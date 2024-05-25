import requests
from urllib.parse import urlencode
import time


class CrossRefAPI:
    """
    A class to interact with the CrossRef API to retrieve information about referenced works.

    Attributes:
        BASE_URL (str): Base URL of the CrossRef API.
        session (requests.Session): Session object for making HTTP requests.
    """

    BASE_URL = "https://api.crossref.org/works"

    def __init__(self):
        """
        Initializes the CrossRefAPI object with a session.
        """
        self.session = requests.Session()

    def get_referenced_works(self, journal_title):
        """
        Retrieves information about referenced works for a given journal title.

        Args:
            journal_title (str): Title of the journal.

        Returns:
            list: A list containing information about referenced works.
        """
        query_params = {
            'query.bibliographic': journal_title,
            'select': 'title,reference,DOI',
            'rows': 1
        }

        final_url = f"{self.BASE_URL}?{urlencode(query_params)}"

        try:
            response = self.session.get(final_url)
            if response.status_code == 200:
                data = response.json()
                referenced_works = []
                if data.get('message') and data['message'].get('items'):
                    for item in data['message']['items']:
                        reference_info = {
                            'DOI': item.get('DOI'),
                            'references': [ref.get('DOI') for ref in item.get('reference')] if item.get(
                                'reference') else ["N/A"]
                        }
                        referenced_works.append(reference_info)
                    return referenced_works
                else:
                    return [{'DOI': "N/A", 'references': ["N/A"]}]
            else:
                print(f"Request failed with status code: {response.status_code}")
                return [{'DOI': "N/A", 'references': ["N/A"]}]
        except requests.RequestException as e:
            print(f"Request Exception: {e}")
            return [{'DOI': "N/A", 'references': ["N/A"]}]

    def get_multiple_titles_info(self, titles_list):
        """
        Retrieves information about referenced works for multiple journal titles.

        Args:
            titles_list (list): List of journal titles.

        Returns:
            list: A list containing information about referenced works for each journal title.
        """
        titles_info = []
        for index, title in enumerate(titles_list):
            referenced_works = self.get_referenced_works(title)
            if referenced_works:
                titles_info.append({
                    'Title': title,
                    'Journal_Info': referenced_works
                })
            else:
                titles_info.append({
                    'Title': title,
                    'Journal_Info': [{'DOI': "N/A", 'references': ["N/A"]}]
                })
            if index % 40 == 0:
                time.sleep(5)
                print(f"No of requests sent (no of articles processed) : {index}")

        return titles_info


# Example usage:
if __name__ == "__main__":
    # Example Usage
    api = CrossRefAPI()
    journal_titles = [
        "Temporal variability in nutrient transport in a first-order agricultural basin in southern Ontario",
        "Dark and bright autoionizing states in resonant high-order harmonic generation: Simulation via a one-dimensional helium model"
    ]
    titles_info = api.get_multiple_titles_info(journal_titles)
    if titles_info:
        for info in titles_info:
            print(f"Title: {info['Title']}")
            for journal_info in info['Journal_Info']:
                print("Journal Information:")
                print("DOI:", journal_info['DOI'])
                print("References:", journal_info['references'])
                print("-----------------------")
    else:
        print("No information found for the specified journal titles.")
