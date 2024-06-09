import os
from os.path import dirname, abspath
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from itertools import combinations
from sklearn_extra.cluster import KMedoids
from sklearn.cluster import (
    AgglomerativeClustering,
    KMeans
)
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score,
)
import networkx as nx
import community as community_louvain
import matplotlib.cm as cm
from modules.database_services import ArticleDatabase
from scipy.spatial.distance import pdist, squareform
import warnings

class ClusterEngine:
    """
    Class for performing clustering analysis on article data.

    Attributes:
        articles_data (pd.DataFrame): DataFrame containing article data.

    Methods:
        jaccard_similarity(set1, set2): Compute Jaccard similarity between two sets.
        calculate_jaccard_similarity(): Calculate Jaccard similarity between articles based on DOI sets.
        perform_clustering(data, n_clusters=10, method="Agglomerative", metric="euclidean"):
            Perform clustering on the articles based on their similarities.
        build_a_louvain_cluster(similarity_df): Build a Louvain cluster and visualize the graph.
        analyse_cluster_results(clusters, data, method):
            Analyse the results of clustering.
        analyse_optimal_cluster_number_k(min_k, max_k, similarity_dataframe, method="KMeans"):
            Find the optimal number of clusters based on silhouette scores.
    """

    def __init__(self, data):
        """
        Initialize ClusterEngine with article data.

        Args:
            data (pd.DataFrame): DataFrame containing article data.
        """
        self.articles_data = data

    def jaccard_similarity(self, set1, set2):
        """
        Calculate Jaccard similarity between two sets.

        Args:
            set1 (set): First set.
            set2 (set): Second set.

        Returns:
            float: Jaccard similarity between the sets.
        """
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union

    def calculate_jaccard_similarity(self):
        """
        Calculate Jaccard similarity between articles based on their DOI sets.

        Returns:
            pd.DataFrame: DataFrame containing Jaccard similarities between articles.
        """
        articles_df = self.articles_data
        df = articles_df[articles_df["ArticleReferences"].notnull()]
        df.loc[:, "DOI_Set"] = df["ArticleReferences"].apply(lambda x: set(x.split(",")))

        similarities = []
        for idx1, idx2 in combinations(df.index, 2):
            title1, dois1 = df.loc[idx1, ["Title", "DOI_Set"]]
            title2, dois2 = df.loc[idx2, ["Title", "DOI_Set"]]
            similarity = self.jaccard_similarity(dois1, dois2)
            similarities.append((title1, title2, similarity))

        similarity_df = pd.DataFrame(
            similarities,
            columns=["ArticleTitle1", "ArticleTitle2", "JaccardSimilarity"],
        )
        non_zero_similarity_df = similarity_df[
            similarity_df["JaccardSimilarity"] != 0
        ]
        return non_zero_similarity_df

    def perform_clustering(self, data, n_clusters=10, method="Agglomerative", metric="euclidean"):
        """
        Perform clustering on the articles based on their similarities.

        Args:
            data (pd.DataFrame): DataFrame containing article data.
            n_clusters (int, optional): Number of clusters. Defaults to 10.
            method (str, optional): Clustering algorithm to use. Defaults to "Agglomerative". Options: "KMeans", "KMedoids", "Agglomerative".
            metric (str, optional): Distance metric to use. Defaults to "euclidean". Options: "euclidean", "jaccard".

        Returns:
            dict: Dictionary containing cluster results.
        """
        df = data[["Title", "ArticleReferences"]]

        # Splitting the references into separate DOIs
        df['ArticleReferences'] = df['ArticleReferences'].apply(
            lambda x: [doi for doi in x.split(', ')] if x is not None else [])

        unique_dois = list(set([doi for dois in df['ArticleReferences'] for doi in dois if doi != "N/A"]))

        article_vectors = []
        for _, row in df.iterrows():
            binary_vector = [1 if doi in row['ArticleReferences'] else 0 for doi in unique_dois]
            article_vectors.append(binary_vector)

        X = np.array(article_vectors)

        algorithms = {
            "KMeans": KMeans(n_clusters=n_clusters, init="k-means++", n_init='auto') if metric == "euclidean" else None,
            "KMedoids": KMedoids(n_clusters=n_clusters, method="pam") if metric == "euclidean" else KMedoids(
                n_clusters=n_clusters, method="pam", metric="precomputed"),
            "Agglomerative": AgglomerativeClustering(n_clusters=n_clusters, linkage="average") if metric == "euclidean" else AgglomerativeClustering(
                n_clusters=n_clusters, linkage="complete", metric="precomputed")
        }

        cluster = algorithms[method]
        if metric != "euclidean":
            jaccard_distances = pdist(X, metric='jaccard')
            distance_matrix = squareform(jaccard_distances)
            cluster.fit(distance_matrix)
        else:
            cluster.fit(X)

        cluster_groups = {i: [] for i in np.unique(cluster.labels_)}
        for i, label in enumerate(cluster.labels_):
            cluster_groups[label].append(df['Title'].iloc[i])

        for cluster_id, titles in cluster_groups.items():
            print(f"Cluster {cluster_id}:")
            for title in titles:
                print(f"- {title}")
        return cluster_groups

    def build_a_louvain_cluster(self, similarity_df):
        """
        Build a Louvain cluster and visualize the graph.

        Args:
            similarity_df (pd.DataFrame): DataFrame containing Jaccard similarities between articles.
        """
        G = nx.Graph()
        for _, row in similarity_df.iterrows():
            G.add_edge(
                row["ArticleTitle1"],
                row["ArticleTitle2"],
                weight=row["JaccardSimilarity"],
            )

        partition = community_louvain.best_partition(G)

        num_communities = max(partition.values()) + 1
        colors = cm.get_cmap("tab20", num_communities)

        article_info = {}
        for article, community_id in partition.items():
            article_info[article] = colors(community_id)

        # Visualize the graph with colored nodes
        pos = nx.spring_layout(G)
        node_colors = [colors(partition[node]) for node in G.nodes()]

        nx.draw_networkx_nodes(
            G, pos, node_size=100, node_color=node_colors
        )
        nx.draw_networkx_edges(G, pos, alpha=0.5)
        labels = {node: str(partition[node]) for node in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels, font_size=8)
        plt.show()

    def analyse_cluster_results(self, clusters, data, method):
        """
        Analyse the results of clustering.

        Args:
            clusters (array-like): Cluster labels.
            data (array-like): Data used for clustering.
            method (str): Clustering algorithm used.

        Returns:
            tuple: Tuple containing silhouette score, Davies-Bouldin index, and Calinski-Harabasz index.
        """
        silhouette_avg, dbi_score, chi_score = None, None, None
        if len(np.unique(clusters)) > 1:
            if method in ["KMeans", "KMeans++", "BisectKMeans"]:
                silhouette_avg = silhouette_score(data, clusters)
                dbi_score = davies_bouldin_score(data, clusters)
                chi_score = calinski_harabasz_score(data, clusters)
            else:
                m = 1 - data
                silhouette_avg = silhouette_score(m, clusters, metric='precomputed')
                dbi_score = davies_bouldin_score(data, clusters)
                chi_score = calinski_harabasz_score(data, clusters)
        else:
            print(f"{method} Analysis Not applicable (only one cluster)")
        return silhouette_avg, dbi_score, chi_score


if __name__ == "__main__":
    # example usage
    table_name = "articles"
    start_date , end_date = "2022-02-01",  "2022-06-30"
    filepath = os.path.join(dirname(dirname(abspath(__file__))), "database", "articles.db")
    db = ArticleDatabase(db_file=filepath, table_name=table_name)
    data = db.get_all_rows_into_df(table_name, start_date, end_date)
    db.close_connection()
    cc = ClusterEngine(data)
    cc.perform_clustering(data, n_clusters=8, method="KMedoids", metric="jaccard")
