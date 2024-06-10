# Science Sync
This system is designed to enhance the data management, access and analysis of Google Scholar Alerts sent to emails by integrating several automated processes.
The core functionalities are described below.

## Overview 

#### Email Integration:

Gmail and Outlook Connectivity: The system connects to your Gmail or Outlook accounts to retrieve Google Scholar alerts.

 #### Alert Retrieval and Parsing
  Google Scholar alerts are automatically fetched and parsed using <i>Beautiful Soup</i> and regular expressions:<i> regex</i> to extract relevant information such as titles, authors, publication dates, and links.

#### Data Storage: 

The parsed information is stored in an in-memory database using `Sqlite3` for easy access and further processing. 


#### Machine Learning-Based Analysis: 

#### Clustering: 
The system employs clustering algorithms (such as KMeans, KMedoids, and Agglomerative Clustering) to group similar articles. 

#### Similarity Metrics: 
Jaccard similarity / Euclidean can be used to measure the similarity between different articles based on their references.

#### Interfaces: 
Interfaces built using `customtkinter` facilitate communication with the system.

Results Display: The system provides intuitive visualization tools to display clustering results and other analytical insights.

## Pre-Requsites
1. Python 3.10 or higher versions

    Official website for download: https://www.python.org/doc/


2. pip (for instaling all related dependencies)
    
    pip installation guide: https://pip.pypa.io/en/stable/installation/


3. your preferred IDE: Visual Studio Code or others.
    
    VS Code download page: https://code.visualstudio.com/Download
   
    (recommended) Python extension in VS Code Market place: https://code.visualstudio.com/docs/editor/extension-marketplace



## How To Run

1. ### a. Clone the repository: ([git](https://git-scm.com/downloads) is required)

    ```bash
    git clone https://github.com/rohra-mehak/ScienceSync.git
    ```
    ```bash
    cd ScienceSync
    ```

    
    ### b. Alternatively Download the code:

      Navigate to: https://github.com/rohra-mehak/ScienceSync

      Click the `Code` button. 

      Select `Download ZIP`.

      Extract the ZIP file to your desired location.

2. ### Navigate to the root folder directory:
   ```bash
   cd yourpath/to/ScienceSync
   ```
   
   On Linux , macOS or Windows
   Use the `mkdir` command followed by the name of the directory in the terminal of your IDE.
   
   ```bash
   mkdir secrets
   ```
   
   ```bash
   mkdir database
   ```
   
3. ### Configure a virtual environment
   In your IDE, make sure you are in the ScienceSync directory
   go the terminal window and run the following commands
   ```bash
   python -m venv venv
   ```
   
   ```bash
   Set-ExecutionPolicy Unrestricted -Scope Process
   ```
   
   ```bash
   .\venv\Scripts\activate
   ```
   
   Once it is activated, you will see `(venv)` prefix to your command line path,
   
   we can now proceed to install dependencies

4. ### Install all dependencies
   
   run the following command and wait for all dependencies to finshing
   installing.

   ```bash
   pip install -r requirements.txt
   ```


4. ### Configuring Credentials (GoogleAPI or GraphAPI)

To access your email account, you'll need to obtain your own client ID and client secret tokens. Depending on your email service (Outlook or Gmail), follow the appropriate steps below:

#### a. Accessing Outlook (using MS Graph)

1. **Register Your Application:**
   Follow the process outlined in the Microsoft documentation to register your application and obtain the necessary tokens: [Register an app for token](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/api/register-app-for-token?tabs=portal).

2. **Save Credentials:**
   Once you have your application ID and client secret, save them in a file named `credentials_msgraph.json` in the `ScienceSync/secrets` directory. The file should have the following format:

   ```json
   {
     "application_id": "your_app_id",
     "client_secret": "your_client_secret"
   }
   ```

#### b. Accessing Gmail (using Google API)

1. **Set Up Your Environment:**
   Follow the steps mentioned in the Google documentation (Set up your Environment Section only) to register your application and obtain the necessary tokens: [Set up your environment](https://developers.google.com/gmail/api/quickstart/python#set_up_your_environment).

2. **Download and Save Credentials:**
   After registering, download the JSON file containing your credentials. Save this file as `credentials.json` in the `ScienceSync/secrets` directory.

Additional resources and information on working with Google APIs can be found here: [Getting started with Google APIs](https://developers.google.com/workspace/guides/get-started#5_steps_to_get_started).

---

By following the above instructions, you will successfully configure your credentials for accessing your email account using either MS Graph or Google API.


5. Navigate to `ScienceSync/app.py`

   there are various parameters that can be set before running the program. 
   However it is recommended to leave the default values as they are.

* `days_ago` (no of days to look back while going through the mailbox)
* `table_name` (the name of the table in your article database which will be created and referred by the system)
* `n_clusters` (number of groups [for clustering articles together] to divide the articles into)
* `method` (the clustering methodology -> K-Means / KMedoids or Agglomerative)
* `metric` (the similarity metric to use -> euclidean / jaccard)


6. ### Running the main file 
  **After making sure all steps are successfully completed and all dependencies have been installed, 
    Make sure you are in the root Science sync directory.
    To start the program, run the following command on your terminal**

```bash
   python app.py
   ```
## Sample Snapshots

Arrows are simply illustrative indicators.

### Initial Screen

Depending on the service chosen and whether credentials could be located by the program, this part might be different. 

![Initial Screen](https://github.com/rohra-mehak/ScienceSync/blob/master/static/media/step1.png?raw=true)

### Redirection to Authorisation

![Redirection Message Screen](https://github.com/rohra-mehak/ScienceSync/blob/master/static/media/step2.png?raw=true)

The authorisation continues on your browser and this will depend on the service you chose.
The initial screen keeps updating the user about progress of the system and errors encountered if any.

Logs can be used to identify any problem encountered. They provide the exact line, method and file where some exception or error occured.

Wait for the process to finish executing and for the results interface to load.

### After finishing up the process -> Click on All Data to view an itemised list of all extracted articles 
![Initial Results Screen](https://github.com/rohra-mehak/ScienceSync/blob/master/static/media/all_data_view.png?raw=true)

### Viewing the scrollable itemised list of articles. Click on a single article to view more information
![Click article Screen](https://github.com/rohra-mehak/ScienceSync/blob/master/static/media/view_article.png?raw=true)

### Article Information on the Right Hand Tab. This includes additional functionalities to Navigate to Article, Save on Google Scholar.
### Additional Export Options below and also Display settings for UI scaling and Themes 
![Article Information Screen](https://github.com/rohra-mehak/ScienceSync/blob/master/static/media/article%20info.png?raw=true)

### Similarly One can go on to see the article groups and view related articles.
