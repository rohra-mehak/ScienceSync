from modules.ss_welcome_and_preprocessing_app import WelcomePage
from modules.ss_results_app import DisplayResultsPage
from modules.run_workflow import run_science_sync_workflow_phase_2
from modules.run_workflow import run_science_sync_workflow_phase_1

table_name = "articles"
days_ago = 600


def run_science_sync_workflow_p1(service_choice=None, app=None, table_name=table_name, days_ago=days_ago):
    run_science_sync_workflow_phase_1(service_choice, app, table_name=table_name, days_ago=days_ago)


if __name__ == "__main__":
    app = WelcomePage(run_science_sync_workflow_p1, table_name, days_ago)
    app.mainloop()
    grouped_clusters, articles_full = run_science_sync_workflow_phase_2(table_name=table_name, days_ago=days_ago, method="KMedoids",n_clusters=10, metric="jaccard")
    results_app = DisplayResultsPage(grouped_clusters, articles_full)
    results_app.mainloop()
