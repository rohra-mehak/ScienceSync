import os
import tkinter as tk
import json
import pandas as pd
from modules.google_rest_service import GoogleAPI
from modules.graph_rest_service import GraphAPI, CodeWindow
from modules.data_preprocessor_for_scholar_messages import DataExtractor
from modules.crossRef_rest_service import CrossRefAPI
from modules.database_services import ArticleDatabase
from modules.clustering import ClusterEngine
from modules.data_delivery_service import DataDeliveryManager
from modules.logger import Log


class ScienceSyncWorkflow:
    """
    Class to encapsulate the ScienceSync workflow.
    """

    def __init__(self):
        self.log = Log.get_logger('logs')
        self.log.info("Initiating WorkFlow...")

    def code_window(self, code):
        """
        Display a window to show the authentication code.

        Args:
            code (str): The authentication code.
        """
        try:
            self.log.info("Running Display user code for Outlook authentication")
            root = tk.Tk()
            app = CodeWindow(root, code=code)
            root.mainloop()
        except Exception as e:
            self.log.error(f"running code window failed with Exception {e}")
            return False

    def run_rest_service_workflow(self, service_choice, days_ago):
        """
        Run the REST service workflow based on the chosen domain.

        Args:
            service_choice (str): The chosen domain ("Google" or "Outlook").
            days_ago (int): no of days to lookback in the email messages

        Returns:
            list: List of email messages.
        """
        try:
            messages = None
            if service_choice == "Google":
                self.log.info("Running google rest services to authenticate user")
                google_client = GoogleAPI()
                google_client.authenticate()
                self.log.info("Getting google scholar email from user mailbox")
                messages = google_client.get_user_email_messages(sender='Google Scholar Alerts '
                                                                        '<scholaralerts-noreply@google.com>',
                                                                 days_ago=days_ago)
            elif service_choice == "Outlook":
                path = os.path.join(os.getcwd(), "secrets", "app-client_ids.json")
                with open(path) as json_file:
                    data = json.load(json_file)
                app_id = data["application_id"]
                self.log.info("Running MS graph rest services to authenticate user")
                graph_client = GraphAPI(app_id)
                app, flow = graph_client.init_flow()
                graph_client.acquire_access_token(app, flow)
                self.log.info("Getting google scholar email from user mailbox")
                messages = graph_client.get_user_email_via_rest_service(sender='scholaralerts-noreply@google.com',
                                                                        days_ago=days_ago)
            else:
                self.log.error("The choice of domain are restricted to Google or Microsoft Outlook")
                return
            return messages
        except Exception as e:
            self.log.error(f"Could not run the rest service workflow to connect to {service_choice}. Exception : {e}")
            return

    def run_data_extraction_workflow(self, messages, domain):
        """
        Run the data extraction workflow.

        Args:
            messages (list): List of email messages.
            domain (str): The chosen domain ("Google" or "Outlook").

        Returns:
            tuple: A tuple containing the extracted titles and article records.
        """
        try:
            self.log.info("Initiating Meta data extraction from email messages")
            extractor = DataExtractor(messages, domain)
            raw_data = extractor.extract_raw_metadata()
            articles_data_list = extractor.create_article_records(raw_data)
            articles_records = extractor.process_extracted_data_into_dataframes(articles_data_list)
            all_titles = []
            all_titles.extend(articles_records['Title'].tolist())
            return all_titles, articles_records
        except Exception as e:
            self.log.error(f"Could not run the data extraction workflow. Exception : {e}")
            return

    def run_crossref_rest_service_workflow(self, article_titles):
        """
        Run the Crossref REST service workflow.

        Args:
            article_titles (list): List of article titles.

        Returns:
            list: List of retrieved information.
        """
        try:
            self.log.info("Running the crossref rest service workflow")
            cross_ref_client = CrossRefAPI()
            ref_info = cross_ref_client.get_multiple_titles_info(article_titles)
            return ref_info
        except Exception as e:
            self.log.error(f"Could not run the crossref rest service workflow {e}")
            return

    def combine_references_with_other_data(self, retrieved_info, articles_data):
        """
        Combine retrieved reference information with other article data.

        Args:
            retrieved_info (list): List of retrieved information.
            articles_data (DataFrame): DataFrame containing article data.

        Returns:
            DataFrame: Combined DataFrame.
        """
        try:
            resultant_articles = articles_data
            self.log.info("Combining references with other meta data")
            for entry in retrieved_info:
                title = entry["Title"]
                doi = entry["Journal_Info"][0]['DOI']
                references = entry["Journal_Info"][0]['references']
                resultant_articles.loc[resultant_articles["Title"] == title, "DOI"] = doi
                resultant_articles.loc[resultant_articles["Title"] == title, "ArticleReferences"] = ", ".join(
                    [x for x in references if x is not None])
            return resultant_articles
        except Exception as e:
            self.log.error(f"Could not combine references. Exception  {e}")
            return

    def run_insert_data_into_database(self, df, table_name):
        """
        Insert data into the database.

        Args:
            df (DataFrame): DataFrame containing data.
            table_name (str): Name of the database table.
        """
        try:
            self.log.info(f"Initiating call to the database table : {table_name}")
            db = ArticleDatabase(table_name=table_name)
            db.insert_dataframe_rows_to_table(table_name, df)
            db.close_connection()
            return True
        except Exception as e:
            self.log.error(f"Could not insert the data into the database. Exception  {e}")
        return False

    def run_database_check_and_get_missing_titles(self, article_titles, table_name):
        """
        Check the database for missing titles and get the titles not present.

        Args:
            article_titles (list): List of article titles.
            table_name (str): Name of the database table.

        Returns:
            list: List of titles not present in the database.
        """
        try:
            self.log.info(f"Initiating call to the database table : {table_name} for checks.")
            db = ArticleDatabase(table_name=table_name)
            titles_not_in_db = db.check_titles_exist(table_name=table_name, title_list=article_titles)
            db.close_connection()
            return titles_not_in_db
        except Exception as e:
            self.log.error(f"Could not run database check and get missing titles. Exception  {e}")
            return

    def get_data_between_dates_from_database(self, table_name, start_date, end_date):
        """
        Retrieve data from the database between specified dates.

        Args:
            table_name (str): Name of the database table.
            start_date (str): Start date (YYYY-MM-DD).
            end_date (str): End date (YYYY-MM-DD).

        Returns:
            DataFrame: DataFrame containing retrieved data.
        """
        try:
            self.log.info(f"Initiating call to the database table : {table_name} for retrieving data.")
            db = ArticleDatabase(table_name=table_name)
            df = db.get_all_rows_into_df(table_name, start_date, end_date)
            db.close_connection()
            return df
        except Exception as e:
            self.log.error(f"Could not get data between dates from the database. Exception  {e}")
            return

    def run_update_titles_date_in_database_workflow(self, table_name, dataframe):
        try:
            self.log.info(f"Initiating call to the database table : {table_name} for updating data.")
            db = ArticleDatabase(table_name=table_name)
            db.update_received_date_in_database(dataframe=dataframe, table_name=table_name)
            db.close_connection()
            return True
        except Exception as e:
            self.log.error(f"Could not update the data with the given dates. Exception  {e}")
            return False

    def run_clustering_workflow(self, data, method="KMeans", n_clusters=10):
        """
        Run the clustering workflow.

        Args:
            data (DataFrame): DataFrame containing data.
            method (str): Clustering method (default is "KMeans").
            n_clusters (int): Number of clusters (default is 15).
        """
        try:
            self.log.info(f"Initiating clustering workflow.")
            cluster_engine = ClusterEngine(data)
            similarity_df = cluster_engine.calculate_jaccard_similarity()
            results, _, _, _ = cluster_engine.perform_clustering(similarity_df=similarity_df, n_clusters=n_clusters,
                                                                 method=method)
            results_dataframe = pd.DataFrame([(key, title) for key, titles in results.items() for title in titles],
                                             columns=["Group", "Title"])
            return results_dataframe
        except Exception as e:
            self.log.error(f"Could not run clustering workflow. Exception  {e}")
            return

    def run_data_delivery_workflow(self, data, preference):
        """
        Run the data delivery workflow.

        Args:
            data (DataFrame): DataFrame containing data.
            preference (str): Delivery preference ("local_storage", "email", or "display").
        """
        try:
            self.log.info(f"Initiating data delivery workflow.")
            delivery_manager = DataDeliveryManager(preference=preference, data=data)
            delivery_manager.make_delivery()
        except Exception as e:
            self.log.error(f"Could not run data delivery workflow. Exception  {e}")
            return


if __name__ == '__main__':
    w = ScienceSyncWorkflow()
    # w.code_window()