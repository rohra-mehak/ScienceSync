# Science Sync
This system is designed to enhance the management and analysis of scholarly alerts by integrating several automated processes. The core functionalities include:

## Overview 

#### Email Integration:

Gmail and Outlook Connectivity: The system connects to your Gmail or Outlook accounts to retrieve Google Scholar alerts.

 #### Alert Retrieval and Parsing
  Google Scholar alerts are automatically fetched and parsed to extract relevant information such as titles, authors, publication dates, and links.

#### Data Storage: 

The parsed information is stored in a robust database for easy access and further processing. The database is designed to handle large volumes of data efficiently.
Machine Learning-Based Analysis:

#### Clustering: 
The system employs clustering algorithms (such as KMeans, KMedoids, and Agglomerative Clustering) to group similar articles. This helps in identifying trends and patterns in the research data.

#### Similarity Metrics: 
Jaccard similarity / Euclidean can be used to measure the similarity between different articles based on their references.

#### Interfaces: 
interfaces facilitate communication with the system.

Results Display: The system provides intuitive visualization tools to display clustering results and other analytical insights.

## Pre-Requsites
1. Python 3.10 or higher versions
2. pip (for instaling all related dependencies)
3. your preferred IDE: Visual Studio Code or PyCharm

## How To Run

1. Download or clone the repository:

    git clone https://github.com/rohra-mehak/ScienceSync.git
    cd ScienceSync

    you need git installed for this. 

    Alternatively:

    Navigate to: https://github.com/rohra-mehak/ScienceSync

    Click the "Code" button. 

    Select "Download ZIP".

    Extract the ZIP file to your desired location.

2. Navigate to the root folder directory:

   cd yourpath/to/ScienceSync

3. Install all dependencies:

   pip install requirements.txt

4. Configure credentials
   
   You need to obtain your own client id and client secret tokens. You may opt for one depending on 
   where our e-mail account may be located.

   a. For access to Outlook, MS graph is used.
   Process on how to do register and obtain token is described here: https://learn.microsoft.com/en-us/azure/azure-monitor/logs/api/register-app-for-token?tabs=portal

   Once you app application id and client secret
   Navigato to ScienceSync/secrets
   ```bash
   { "application_id" : "your_app_id",
   "client_secret" : "your_client_secret"}
   ```
   and save the credentials as  <i> credentials_msgraph.json </i>


   b. For access to Gmail, Google API is used.
   Process on how to do register and obtain token is described here:
   Section: Environment Setup
   https://developers.google.com/gmail/api/quickstart/python#set_up_your_environment

   credentials as available as a downloadable file, download the json file:

   Navigato to ScienceSync/secrets and save the credentials as <i>credentials.json </i>


5. Navigate to <i> ScienceSync/app.py </i>
and run the file to start the program.

