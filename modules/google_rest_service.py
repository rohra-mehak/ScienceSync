import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timezone


class GoogleAPI:
    """
    A class for interacting with the Gmail API to read user emails.

    Attributes:
        scopes (list): List of OAuth 2.0 scopes required for accessing Gmail API.
        service (googleapiclient.discovery.Resource): Google API service object.
    """

    def __init__(self, scopes=None):
        """
        Initializes the GoogleAPI object with OAuth 2.0 scopes.

        Args:
            scopes (list, optional): List of OAuth 2.0 scopes required for accessing Gmail API. Defaults to None.
        """
        if scopes is None:
            scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
        self.scopes = scopes

    def authenticate(self):
        """
        Authenticates the user and initializes the Gmail API service.
        """
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", self.scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                path = os.path.join(os.path.dirname(os.path.abspath("ScienceSync")), "secrets", "credentials.json")
                flow = InstalledAppFlow.from_client_secrets_file(path, self.scopes)
                creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        self.service = build("gmail", "v1", credentials=creds)

    def read_messages(self, sender=None, days_ago=4):
        """
        Retrieves email messages from Gmail.

        Args:
            sender (str, optional): Email address of the sender to filter emails. Defaults to None.
            days_ago (int, optional): Number of days ago to filter emails. Defaults to 4.

        Returns:
            list: List of email messages matching the provided filters.
        """
        try:
            query = f"newer_than:{days_ago}d"
            page_token = None  # Initialize the page token
            filtered_messages = []
            while True:
                results = self.service.users().messages().list(userId="me", q=query, pageToken=page_token).execute()

                if 'messages' in results:
                    messages = results['messages']

                    for message in messages:
                        message_id = message['id']
                        message_details = self.service.users().messages().get(userId="me", id=message_id).execute()
                        headers = message_details['payload']['headers']

                        if not sender or any(
                                header['value'] == sender for header in headers if header['name'] == 'From'):
                            filtered_messages.append(message_details)

                    # Check if there are more pages of results
                    page_token = results.get('nextPageToken')
                    if not page_token:
                        break

                else:
                    print("No messages found.")
                    return filtered_messages

            return filtered_messages

        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def get_html_body(self, message_details):
        """
        Retrieves the HTML body of an email message.

        Args:
            message_details (dict): Details of the email message.

        Returns:
            str: HTML content of the email body.
        """
        payload = message_details['payload']
        body_data = payload['body']['data']
        body_text = base64.urlsafe_b64decode(body_data).decode('utf-8')
        return body_text

    def get_json_object(self, message_details):
        """
        Extracts relevant information from an email message and returns it as a JSON object.

        Args:
            message_details (dict): Details of the email message.

        Returns:
            dict: JSON object containing email metadata.
        """
        payload = message_details['payload']
        headers = payload['headers']
        subject = next((header['value'] for header in headers if header['name'] == 'Subject'), None)
        body_text = self.get_html_body(message_details)
        message_json = {
            "Subject": subject,
            "Body": body_text,
            "Received": datetime.fromtimestamp(int(message_details['internalDate']) / 1000,
                                               tz=timezone.utc).date().strftime("%Y-%m-%d")
        }
        return message_json

    def get_user_email_messages(self, sender, days_ago=7):
        """
        Retrieves email messages from a specific sender within the specified number of days.

        Args:
            sender (str): Email address of the sender.
            days_ago (int, optional): Number of days ago. Defaults to 7.

        Returns:
            list: List of email messages.
        """
        messages = []
        email_messages = self.read_messages(sender=sender, days_ago=days_ago)
        for message in email_messages:
            data = self.get_json_object(message)
            messages.append(data)
        return messages


if __name__ == "__main__":
    google_api = GoogleAPI()
    google_api.authenticate()
    m = google_api.get_user_email_messages(sender='Google Scholar Alerts '
                                                  '<scholaralerts-noreply@google.com>')
