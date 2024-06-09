import json
import os
import webbrowser
import requests
from msal import PublicClientApplication
from datetime import datetime, timedelta
import tkinter as tk
from customtkinter import CTkLabel, CTkButton


class GraphAPI:
    """
    A class for interacting with the Microsoft Graph API to access user emails and initiate device flow authentication.

    Attributes:
        client_id (str): The client ID for the application registered with Azure Active Directory.
        scopes (list): List of scopes required for accessing user emails.
        access_token (str): Access token obtained after authentication.
        user_code (str): User code obtained during device flow authentication.
    """

    def __init__(self, client_id, scopes=None):
        """
        Initializes the GraphAPI object with client ID and scopes.

        Args:
            client_id (str): The client ID for the application registered with Azure Active Directory.
            scopes (list, optional): List of scopes required for accessing user emails. Defaults to None.
        """
        if scopes is None:
            scopes = ['Mail.Read', 'Mail.ReadWrite']
        self.client_id = client_id
        self.scopes = scopes
        self.access_token = None
        self.user_code = None

    def init_flow(self):
        """
        Initiates the device flow authentication process.

        Returns:
            tuple: A tuple containing the PublicClientApplication object and device flow response.
        """
        app = PublicClientApplication(client_id=self.client_id)
        flow = app.initiate_device_flow(scopes=self.scopes)
        self.user_code = flow['user_code']
        return app, flow

    def acquire_access_token(self, app, flow):
        """
        Acquires an access token using device flow authentication.

        Args:
            app (PublicClientApplication): PublicClientApplication object.
            flow (dict): Device flow response containing user code and verification URI.

        Returns:
            str: Access token obtained after authentication.
        """
        print('USER CODE ' + flow['user_code'])
        webbrowser.open(flow['verification_uri'])
        response = app.acquire_token_by_device_flow(flow)
        self.access_token = str(response.get('access_token'))

    def get_user_email_via_rest_service(self, days_ago, sender):
        """
        Retrieves user emails via Microsoft Graph REST services.

        Args:
            sender (str, optional): Email address of the sender to filter emails. Defaults to None.
            days_ago (int, optional): Number of days ago to filter emails. Defaults to None.

        Returns:
            list: List of dictionaries containing email metadata.
        """
        messages = []
        token = self.access_token
        headers = {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }

        url = "https://graph.microsoft.com/v1.0/me/messages"

        if days_ago is not None:
            received_date_filter = (datetime.utcnow() - timedelta(days=days_ago)).strftime('%Y-%m-%dT%H:%M:%SZ')
            # Add the received date filter to the query parameters
            params = {
                '$filter': f"(from/emailAddress/address eq '{sender}') and (receivedDateTime ge {received_date_filter})",
                '$select': 'subject,body,receivedDateTime',
                '$top': 100  # Adjust this value as needed
            }
        else:
            params = {
                '$filter': f"(from/emailAddress/address eq '{sender}')",
                '$select': 'subject,body,receivedDateTime',
                '$top': 100  # Adjust this value as needed
            }

        while url:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                for email in data['value']:
                    messages.append({"Subject": email['subject'], "Body": str(email['body']['content']),
                                     "Received": email['receivedDateTime']})
                url = data.get('@odata.nextLink', None)
                params = None
            else:
                print('Error:', response.status_code)
                print('Message:', response.text)
                break
        return messages



if __name__ == "__main__":
    # example usage
    path = os.path.join(os.getcwd(), "secrets", "app-client_ids.json")
    with open(path) as json_file:
        data = json.load(json_file)
    app_id = data["application_id"]
    graph_client = GraphAPI(app_id)
    app, flow = graph_client.init_flow()
    graph_client.acquire_access_token(app, flow)
    messages = graph_client.get_user_email_via_rest_service(sender='scholaralerts-noreply@google.com', days_ago=505)
    for msg in messages:
        print(msg["Subject"], msg["Received"])
