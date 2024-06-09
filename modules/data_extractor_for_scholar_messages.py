import datetime
import re
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np


class DataExtractor:
    """
    A class to extract data from email messages containing HTML content.

    Attributes:
        messages (list): List of email message objects.
        domain (str): Domain of the email service provider (e.g., "Google", "Outlook").
    """

    def __init__(self, messages, domain):
        """
        Initializes the DataExtractor object.

        Args:
            messages (list): List of email message objects.
            domain (str): Domain of the email service provider.
        """
        self.messages = messages
        self.domain = domain

    def extract_data_from_html_body(self, html_content):
        """
        Extracts data from HTML content.

        Args:
            html_content (str): HTML content of the email body.

        Returns:
            tuple: A tuple containing lists of titles, authors, links, abstracts, and save links.
        """
        soup_extractor = BeautifulSoup(html_content, 'html.parser')
        titles = []
        links = []
        authors = []
        abstracts = []
        save_links = []
        try:
            extracted_titles = soup_extractor.find_all("a", {"class": "gse_alrt_title"})
            if self.domain == "Google":
                extracted_authors = soup_extractor.find_all("div", {"style": "color:#006621;line-height:18px"})
            else:
                extracted_authors = soup_extractor.find_all("div", {"style": "color:#006621; line-height:18px"})
                if len(extracted_authors) == 0:
                    extracted_authors = soup_extractor.find_all("div", {"style": "color:#006621"})
            extracted_abstracts = soup_extractor.find_all("div", {"class": "gse_alrt_sni"})
            pattern = re.compile(r"m_-\d{19}gse_alrt_sni")
            if len(extracted_abstracts) == 0:
                extracted_abstracts = soup_extractor.find_all("div", class_=pattern)
            save_button_tags = soup_extractor.find_all('img', alt='Save')

            if extracted_authors or extracted_titles or extracted_abstracts or save_button_tags:
                for title in extracted_titles:
                    titles.append(title.text)
                    links.append(title["href"])

                for abstract in extracted_abstracts:
                    abstracts.append(str(abstract.text).rstrip().strip())

                for tag in save_button_tags:
                    save_links.append(tag.find_previous('a')["href"])

                for author in extracted_authors:
                    authors.append(str(author.text))
        except Exception as e:
            print(f"Could not extract data from this particular journal email: {e}")
            titles.append("")
            authors.append("")
            links.append("")
            abstracts.append("")
            save_links.append("")
        data = titles, authors, links, abstracts, save_links
        return data

    def extract_raw_metadata(self):
        """
        Extracts raw metadata from email messages.

        Returns:
            list: A list containing tuples of extracted metadata.
        """
        extracted_data = []
        for index, msg in enumerate(self.messages):
            if "new citations" in msg["Subject"] or "new citation" in msg["Subject"]:
                message_filter = "by"
                cited_author = None
                if "your" in msg["Subject"]:
                    cited_author = "Yourself"
                elif message_filter in msg["Subject"]:
                    pattern = re.compile(r"(?<=by\s)([^,]+)", re.IGNORECASE | re.UNICODE)
                    match = pattern.search(msg["Subject"])
                    if match:
                        cited_author = match.group(1)
                    else:
                        cited_author = None
                data = self.extract_data_from_html_body(msg["Body"])
                if self.domain == "Outlook":
                    received = datetime.datetime.strptime(msg["Received"], '%Y-%m-%dT%H:%M:%SZ').strftime("%Y-%m-%d")
                else:
                    received = msg["Received"]
                extracted_data.append((cited_author, data, received))

        return extracted_data

    def create_article_records(self, articles_data):
        """
        Creates article records from extracted data.

        Args:
            articles_data (list): A list containing tuples of extracted data.

        Returns:
            list: A list containing article records.
        """
        articles_data_full = []
        for dt in articles_data:
            cited_author = dt[0]
            titles, authors, links, abstracts, save_links = dt[1]
            received_date = dt[2]
            if cited_author is None:
                cited_author_m = ""
            else:
                cited_author_m = cited_author.rstrip().strip()
            if len(titles) == len(authors) == len(links) == len(abstracts) == len(save_links):
                for i in range(len(titles)):
                    title = titles[i].rstrip().strip()
                    author = authors[i].rstrip().strip()
                    link = links[i].rstrip().strip()
                    abstract = abstracts[i].rstrip().strip()
                    save_link = save_links[i].rstrip().strip()
                    journals_list = [title, author, link, abstract, cited_author_m, save_link, received_date]
                    articles_data_full.append(journals_list)
            else:
                print("Data for the following could not be extracted :")
                print(titles, authors, links, abstracts, save_links)
        return articles_data_full

    def process_extracted_data_into_dataframes(self, journal_data):
        """
        Processes extracted data into DataFrame.

        Args:
            journal_data (list): A list containing article records.

        Returns:
            pd.DataFrame: A DataFrame containing processed data.
        """
        title = "Title"
        author = "Author"
        link = "Link"
        abstract = "Abstract"
        cited_author = "CitedAuthor"
        save_link = "SaveLink"
        received_date = "ReceivedDate"

        journal_dataframe = pd.DataFrame(journal_data,
                                         columns=[title, author, link, abstract, cited_author, save_link,
                                                  received_date])
        journal_dataframe.drop_duplicates(subset=[title, cited_author], inplace=True)
        journal_dataframe[link] = journal_dataframe.groupby(title)[link].transform('first')
        journal_dataframe[save_link] = journal_dataframe.groupby(title)[save_link].transform('first')
        journal_dataframe[abstract] = journal_dataframe.groupby(title)[abstract].transform('first')
        updated_journal_dataframe = journal_dataframe.groupby([title, author, link, abstract, save_link,
                                                               received_date])[cited_author].apply(
            ','.join).reset_index()

        return updated_journal_dataframe

    def split_dataframe_into_multiple_dataframes(self, main_dataframe):
        """
        Splits a DataFrame into multiple smaller DataFrames.

        Args:
            main_dataframe (pd.DataFrame): The main DataFrame to split.

        Returns:
            list: A list containing smaller DataFrames.
        """
        split_dfs = None
        if len(main_dataframe) > 10:
            max_split_size = 10
            if len(main_dataframe) > max_split_size:
                num_splits = int(np.ceil(len(main_dataframe) / max_split_size))
                split_dfs = np.array_split(main_dataframe, num_splits)

                for i, split_df in enumerate(split_dfs):
                    print(f"DataFrame {i + 1} (Size: {len(split_df)}):\n{split_df}\n")
            else:
                print("DataFrame size is not greater than 10. No need to split.")
            return split_dfs
        else:
            return [main_dataframe]
