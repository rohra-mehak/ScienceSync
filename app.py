import sys

from modules.initial_interface import WelcomePage
from modules.results_interface import DisplayResultsPage
from modules.run_workflow import run_science_sync_workflow_phase_2
from modules.run_workflow import run_science_sync_workflow_phase_1
import sys

# parameters
table_name = "articles"
days_ago = 14
# possible params for "method"
# KMeans , KMedoids , Agglomerative
method = "KMedoids"
# possible params for "metric"
# jaccard , euclidean
metric = "jaccard"
n_clusters = 10


def run_science_sync_workflow_p1(service_choice=None, app=None, table_name=table_name, days_ago=days_ago):
    run_science_sync_workflow_phase_1(service_choice, app, table_name=table_name, days_ago=days_ago)


if __name__ == "__main__":
    app = WelcomePage(run_science_sync_workflow_p1, table_name, days_ago)
    app.mainloop()

    grouped_clusters, articles_full = run_science_sync_workflow_phase_2(table_name=table_name, days_ago=days_ago,
                                                                        method=method, n_clusters=n_clusters,
                                                                        metric=metric)
    if grouped_clusters or articles_full:
        results_app = DisplayResultsPage(grouped_clusters, articles_full)
        results_app.mainloop()
