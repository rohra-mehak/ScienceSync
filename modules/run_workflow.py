import time
import langdetect as ld
from modules.workflows import ScienceSyncWorkflow
import pandas as pd
from datetime import datetime, timedelta


def _get_messages(workflow, service_choice ,days_ago, app):
    """
    Retrieve messages from a specified service.

    Args:
    - workflow (ScienceSyncWorkflow): Instance of ScienceSyncWorkflow.
    - service_choice (str): The service choice for message retrieval.[Google or Outlook]
    - days_ago (int): Number of days back to retrieve messages.

    Returns:
    - List: Messages retrieved from the service.
    """
    return workflow.run_rest_service_workflow(service_choice=service_choice, days_ago=days_ago, app=app)


def _extract_metadata(workflow, messages, service_choice):
    """
    Extract metadata from messages.

    Args:
    - workflow (ScienceSyncWorkflow): Instance of ScienceSyncWorkflow.
    - messages (list): List of messages to extract metadata from.
    - service_choice (str): The service choice for metadata extraction.

    Returns:
    - Tuple: List of titles and DataFrame containing extracted metadata.
    """
    return workflow.run_data_extraction_workflow(messages=messages, domain=service_choice)


def _acquire_references_from_crossref(workflow, titles_not_in_db):
    """
    Acquire references from CrossRef for titles not found in the database.

    Args:
    - workflow (ScienceSyncWorkflow): Instance of ScienceSyncWorkflow.
    - titles_not_in_db (list): List of titles not found in the database.

    Returns:
    - dict: Dictionary containing reference information.
    """

    return workflow.run_crossref_rest_service_workflow(article_titles=titles_not_in_db)


def _update_article_table_with_references(workflow, reference_info, table_name):
    """
    Combine references with metadata and insert into the database.

    Args:
    - workflow (ScienceSyncWorkflow): Instance of ScienceSyncWorkflow.
    - articles_full (DataFrame): DataFrame containing full articles data.
    - titles_not_in_db (list): List of titles not found in the database.
    - reference_info (dict): Dictionary containing reference information.
    - table_name (str): Name of the table in the database.

    Returns:
    - bool: True if insertion is successful, False otherwise.
    """
    return workflow.run_update_article_tables_with_references(retrieved_info=reference_info, table_name=table_name)



def _get_data_from_database(workflow, table_name, start_date, end_date):
    """
    Retrieve data from the database within a specified date range.

    Args:
    - workflow (ScienceSyncWorkflow): Instance of ScienceSyncWorkflow.
    - table_name (str): Name of the table in the database.
    - start_date (str): Start date for data retrieval.
    - end_date (str): End date for data retrieval.

    Returns:
    - DataFrame: DataFrame containing retrieved data.
    """
    return workflow.get_data_between_dates_from_database(table_name=table_name, start_date=start_date,
                                                         end_date=end_date)


def _perform_clustering(workflow, df, method, n_clusters):
    """
    Perform clustering on the provided DataFrame.

    Args:
    - workflow (ScienceSyncWorkflow): Instance of ScienceSyncWorkflow.
    - df (DataFrame): DataFrame containing data for clustering.
    - method (str): Clustering method to use.
    - n_clusters (int): Number of clusters.

    Returns:
    - DataFrame: DataFrame containing clustering results.
    """
    return workflow.run_clustering_workflow(df, method=method, n_clusters=n_clusters)


def _acquire_data(workflow, service_choice, app, days_ago):
    """
    Acquire data from a specified service.

    Args:
    - workflow (ScienceSyncWorkflow): Instance of ScienceSyncWorkflow.
    - service_choice (str): The service choice for data acquisition.
    - app: The application object.
    - days_ago (int): Number of days back to retrieve data.

    Returns:
    - Tuple: List of titles, DataFrame containing articles data, and a flag indicating success.
    """
    workflow.log.info(f"Domain service for authentication is {service_choice}")
    app.update_info_text("Acquiring E-mail data")
    msgs = _get_messages(workflow, service_choice, days_ago, app)
    if not msgs:
        app.update_info_text("No messages found or retrieved. Please check your e-mails in the given days")
        workflow.log.error(f"no messages retrieved.")
        return None, None, False

    workflow.log.info("Auth workflow complete. Messages from Google scholar received")
    app.update_info_text("Running meta data extraction workflow")

    title_list, articles_full = _extract_metadata(workflow, msgs, service_choice)
    articles_full['lang'] = articles_full['Title'].apply(lambda x: ld.detect(x))
    articles = articles_full[articles_full['lang'] == 'en']
    articles_copy = articles.drop(columns=["lang"]).copy()

    if not title_list or not isinstance(articles_copy, pd.DataFrame):
        workflow.log.error(f"titles or articles were not extracted correctly")
        return None, None, False

    app.update_info_text("Articles MetaData Extraction workflow complete")
    workflow.log.info("Articles MetaData Extraction workflow complete. (_acquire data)")
    return title_list, articles_copy, True


def _check_database_for_existing_titles(workflow, title_list, table_name):
    """
    Check the database for existing titles and return titles not found in the database.

    Args:
    - workflow (ScienceSyncWorkflow): Instance of ScienceSyncWorkflow.
    - title_list (list): List of titles to check in the database.
    - table_name (str): Name of the table in the database.

    Returns:
    - list: List of titles not found in the database.
    """
    titles_not_in_db = workflow.run_database_check_and_get_missing_titles(article_titles=title_list, table_name=table_name)

    if not titles_not_in_db:
        workflow.log.error("titles_not_in_db not returned correctly ")
        return []
    elif len(titles_not_in_db) == 0:
        return []
    else:
        return titles_not_in_db


def _update_titles_date_in_database(workflow, table_name, dataframe):
    """
    Update titles date in the database.

    Args:
    - workflow (ScienceSyncWorkflow): Instance of ScienceSyncWorkflow.
    - table_name (str): Name of the table in the database.
    - dataframe (DataFrame): DataFrame containing titles and date information.

    Returns:
    - bool: True if update is successful, False otherwise.
    """
    return workflow.run_update_titles_date_in_database_workflow(table_name=table_name, dataframe=dataframe)


def _get_additional_information_from_crossref(workflow, titles_not_in_db):
    """
    Get additional information from CrossRef for titles not found in the database.

    Args:
    - workflow (ScienceSyncWorkflow): Instance of ScienceSyncWorkflow.
    - titles_not_in_db (list): List of titles not found in the database.

    Returns:
    - dict: Dictionary containing additional information from CrossRef.
    """
    references_info = _acquire_references_from_crossref(workflow, titles_not_in_db)
    if not references_info:
        workflow.log.error("References were not retrieved")
        return
    workflow.log.info("Data Retrieval from CrossRef is complete.")
    return references_info


def _acquire_data_from_database_and_make_cluster_analysis(workflow, table_name, start_date, end_date, method,
                                                          n_clusters, metric):
    """
    Acquire data from the database and perform cluster analysis.

    Args:
    - workflow (ScienceSyncWorkflow): Instance of ScienceSyncWorkflow.
    - table_name (str): Name of the table in the database.
    - start_date (str): Start date for data retrieval.
    - end_date (str): End date for data retrieval.
    - method (str): Clustering method to use.
    - n_clusters (int): Number of clusters.

    Returns:
    - Tuple: DataFrame containing clustering results and original DataFrame.
    """
    df = _get_data_from_database(workflow, table_name=table_name, start_date=start_date,
                                 end_date=end_date)
    if not isinstance(df, pd.DataFrame):
        workflow.log.error("could not get data from database as a df")
        return None , None
    workflow.log.info("Data from database is acquired.")
    results = workflow.run_clustering_workflow(data=df, method=method, n_clusters=n_clusters, metric=metric)
    if not isinstance(results, pd.DataFrame):
        return None, df
    workflow.log.info("Clustering Workflow is complete.")
    return results, df


def run_science_sync_workflow_phase_2(table_name, days_ago, method , n_clusters, metric):
    """
    Run phase 2 of the Science Sync workflow.

    Args:
    - table_name (str): Name of the table in the database.
    - days_ago (int): Number of days back to retrieve data (default: 14).
    - method (str): Clustering method to use (default: "KMeans").
    - n_clusters (int): Number of clusters (default: 10).

    Returns:
    - Tuple: Dictionary containing clustered articles and original DataFrame.
    """
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
    workflow = ScienceSyncWorkflow()
    clustering_results, articles_full = _acquire_data_from_database_and_make_cluster_analysis(workflow,
                                                                                              table_name=table_name,
                                                                                              start_date=start_date,
                                                                                              end_date=end_date,
                                                                                              method=method,
                                                                                              n_clusters=n_clusters,
                                                                                              metric=metric)
    return clustering_results, articles_full


def run_science_sync_workflow_phase_1(service_choice, app, table_name, days_ago):
    """
    Run phase 1 of the Science Sync workflow. i.e
    get email service choice , authorise user, retrieve email data , extract article information from alerts
    ,get references if required, save everything to a database.

    Args:
    - service_choice (str): The service choice for data acquisition.
    - app: The application interface object.
    - table_name (str): Name of the table in the database.
    - days_ago (int): Number of days back to retrieve data (default: 14).
    """
    workflow = ScienceSyncWorkflow()
    try:
        title_list, articles_full, acquired = _acquire_data(workflow, service_choice, app, days_ago)
        if not acquired:
           workflow.log.error("Could not acquire data from e-mails")
           app.update_info_text("ERROR: Could not acquire data from e-mails. Please try again. Check logs for more "
                                "details")
           return

        app.update_info_text(f"{len(title_list)} number of articles acquired")
        workflow.log.info(f"{len(title_list)} number of articles acquired")

        titles_not_in_db = _check_database_for_existing_titles(workflow, title_list, table_name=table_name)
        articles_not_in_db = articles_full[articles_full["Title"].isin(titles_not_in_db)]
        if len(titles_not_in_db) > 0:

            inserted_data = workflow.run_insert_data_into_database(articles_not_in_db, table_name)
            if not inserted_data:
                workflow.log.error("Could not insert data into database ")
                app.update_info_text(
                    "ERROR : Could not insert email data. Please try again. Check logs for more details")
                return

            app.update_info_text(f"Need to retrieve references for {len(titles_not_in_db)} articles for similarity analysis out of . \n "
                                 f"Please check the terminal window to provide confirmation")

            # TODO future. to find a way to optimise references retrieval and add different ways to confirm
            confirmation = input(f"Need to retrieve more references for {len(titles_not_in_db)} articles for similarity analysis.\n"
                                 f"This process can take a few hours if a lot of data is required. Additionally,"
                                 f"you can skip this and"
                                 f"proceed to view summarised information with available data. Do you wish to proceed with retrieval ? Y/N?")

            if confirmation == "Y":
                time.sleep(1)
                app.update_info_text("Retrieving references for articles")
                references_info = _get_additional_information_from_crossref(workflow, titles_not_in_db)
                if not references_info:
                   workflow.log.error("There were no references retrieved for the given data")
                else:
                    updated = _update_article_table_with_references(workflow, references_info, table_name=table_name)
                    if not updated:
                        workflow.log.warning("references could not be loaded to the database")
            else:
                app.update_info_text("Inserted data without references")

        else:
            workflow.log.info("Running updates...")
            app.update_info_text("Running updates")
            articles_not_in_db_titles_and_date = articles_not_in_db[["Title", "ReceivedDate"]]
            _update_titles_date_in_database(workflow, table_name, articles_not_in_db_titles_and_date)
        app.update_info_text("full data acquisition is complete. will take a few mins to execute. please close this "
                             "window")
        workflow.log.info("Phase 1 complete.")

    except Exception as e:
        workflow.log.error(f"An error occurred:{e}")
        app.update_info_text(f"An error seems to have occured : {e}. Please close this window and try again after fixes.")



