import os
from os.path import dirname, abspath
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from itertools import combinations
from sklearn_extra.cluster import KMedoids
from sklearn.cluster import (
    AgglomerativeClustering,
KMeans, BisectingKMeans
)
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score,
)
import networkx as nx
import community as community_louvain
from sklearn.manifold import MDS
import matplotlib.cm as cm
from modules.database_services import ArticleDatabase
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import SpectralClustering


class ClusterEngine:
    """
    Class for performing clustering analysis on article data.

    Attributes:
        data (pd.DataFrame): DataFrame containing article data.

    Methods:
        jaccard_similarity(self, set1, set2): Compute Jaccard similarity between two sets.
        calculate_jaccard_similarity(self): Calculate Jaccard similarity between articles based on DOI sets.
        perform_clustering(self, similarity_df, n_clusters=15, method="KMeans"):
            Perform clustering on the articles based on their similarities.
        build_a_louvain_cluster(self, similarity_df): Build a Louvain cluster and visualize the graph.
        analyse_cluster_results(self, clusters, data, method):
            Analyse the results of clustering.
        analyse_optimal_cluster_number_k(self, min_k, max_k, similarity_dataframe, method="KMeans"):
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
        # df["DOI_Set"] = df["ArticleReferences"].apply(lambda x: set(x.split(",")))
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

    def perform_clustering(
            self, similarity_df, n_clusters=8, method="KMeans", preference=None
    ):
        """
        Perform clustering on the articles based on their similarities.

        Args:
            similarity_df (pd.DataFrame): DataFrame containing Jaccard similarities between articles.
            n_clusters (int, optional): Number of clusters. Defaults to 15.
            method (str, optional): Clustering algorithm to use. Defaults to "KMeans".algorithms choices are KMeans, KMeans++, Agglomerative, BisectKMeans, Affinity, KMedoids .

        Returns:
            tuple: Tuple containing cluster results, cluster labels, data, and inertia.

        """
        df = similarity_df
        unique_titles = np.unique(
            df[["ArticleTitle1", "ArticleTitle2"]].values
        )

        # Create an empty similarity matrix
        n_titles = len(unique_titles)
        similarity_matrix = np.zeros((n_titles, n_titles))

        # Populate the similarity matrix
        for i, title1 in enumerate(unique_titles):
            for j, title2 in enumerate(unique_titles):
                if i == j:
                    similarity_matrix[i, j] = 1.0
                else:
                    jaccard_similarity = df[
                        (
                                (df["ArticleTitle1"] == title1)
                                & (df["ArticleTitle2"] == title2)
                        )
                        | (
                                (df["ArticleTitle1"] == title2)
                                & (df["ArticleTitle2"] == title1)
                        )
                        ]["JaccardSimilarity"].values
                    if len(jaccard_similarity) > 0:
                        similarity_matrix[i, j] = jaccard_similarity[0]

        distance_matrix = 1 - similarity_matrix

        # Fit clustering algorithms
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
        agglomerative = AgglomerativeClustering(
            n_clusters=n_clusters, affinity="precomputed", linkage="average"
        )
        kmeansplusplus = KMeans(
            n_clusters=n_clusters, init="k-means++", random_state=42, n_init='auto'
        )
        bisecting_kmeans = BisectingKMeans(
            n_clusters=n_clusters, random_state=42, n_init='auto'
        )
        k_medoids = KMedoids(
            n_clusters=n_clusters, random_state=42, method="pam"
        )

        algorithms = {
            "KMeans": kmeans,
            "KMeans++": kmeansplusplus,
            "Agglomerative": agglomerative,
            "BisectKMeans": bisecting_kmeans,
            "KMedoids": k_medoids,
        }

        algorithm = algorithms[method]

        embedded_points = None
        inertia = None
        X = None
        if method in ["KMeans", "KMeans++", "BisectKMeans"]:
            mds = MDS(
                n_components=2, dissimilarity="precomputed"
            )
            embedded_points = mds.fit_transform(distance_matrix)
            clusters = algorithm.fit_predict(embedded_points)
            inertia = algorithm.inertia_
            X = embedded_points
        elif method == "KMedoids":
            # dissimilarity = pairwise_distances(
            #     distance_matrix, metric="precomputed"
            # )
            clusters = algorithm.fit_predict(distance_matrix)
            X = distance_matrix
        else:
            clusters = algorithm.fit_predict(similarity_matrix)
            X = similarity_matrix

        unique_clusters = np.unique(clusters)
        cluster_results = {}

        for cluster_num in unique_clusters:
            cluster_indices = np.where(clusters == cluster_num)[0]
            cluster_titles = [unique_titles[i] for i in cluster_indices]
            cluster_results[cluster_num] = cluster_titles

        for k, v in cluster_results.items():
            print(k)
            for vv in v:
                print(vv)
        return cluster_results, clusters, X, inertia

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
                # silhouette_avg = silhouette_score(data, clusters)
                dbi_score = davies_bouldin_score(data, clusters)
                chi_score = calinski_harabasz_score(data, clusters)
        else:
            print(f"{method} Analysis Not applicable (only one cluster)")
        return silhouette_avg, dbi_score, chi_score

    def analyse_optimal_cluster_number_k(
            self, min_k, max_k, similarity_dataframe, method="KMeans"
    ):
        """
        Find the optimal number of clusters based on silhouette scores.

        Args:
            min_k (int): Minimum number of clusters to consider.
            max_k (int): Maximum number of clusters to consider.
            similarity_dataframe (pd.DataFrame): DataFrame containing Jaccard similarities between articles.
            method (str, optional): Clustering algorithm to use. Defaults to "KMeans".

        """
        k_values = range(min_k, max_k + 1)
        silhouette_scores = []
        sse = []

        for k in k_values:
            (
                _,
                cluster_labels,
                data,
                inertia,
            ) = self.perform_clustering(
                similarity_dataframe, n_clusters=k, method=method
            )
            silhouette_avg = silhouette_score(data, cluster_labels)
            silhouette_scores.append(silhouette_avg)
            sse.append(inertia)

        # Plot silhouette scores
        plt.plot(k_values, silhouette_scores, marker="o")
        plt.xlabel("Number of clusters (k)")
        plt.ylabel("Silhouette Score")
        plt.title(
            f"Silhouette Score vs. Number of Clusters for {method} algorithm"
        )
        plt.show()

        # plot sse for the elbow method
        plt.plot(k_values, sse)
        plt.xlabel("Number of Clusters")
        plt.ylabel("SSE")
        plt.title(
            f"Elbow Method- SSE Score vs. Number of Clusters for {method} algorithm"
        )
        plt.show()


if __name__ == "__main__":
    table_name = "articles"
    start_date = "2022-05-01"
    end_date = "2022-06-30"

    filepath = os.path.join(dirname(dirname(abspath(__file__))), "database", "articles.db")
    db = ArticleDatabase(db_file=filepath, table_name=table_name)
    data = db.get_all_rows_into_df(table_name, start_date, end_date)
    db.close_connection()

    df = data[["Title", "ArticleReferences"]]

    # Splitting the references into separate DOIs
    df['ArticleReferences'] = df['ArticleReferences'].apply(
        lambda x: [doi for doi in x.split(', ')] if x is not None else [])

    unique_dois = list(set([doi for dois in df['ArticleReferences'] for doi in dois if doi != "N/A"]))

    # Building the feature matrix
    # feature_matrix = pd.DataFrame(index=df['Title'], columns=unique_dois)
    #
    # # Filling the feature matrix with 1s and 0s
    # for idx, dois in enumerate(df['ArticleReferences']):
    #     for doi in dois:
    #         feature_matrix.at[df['Title'].iloc[idx], doi] = 1
    #
    # feature_matrix.fillna(0, inplace=True)

    # feature_matrix.to_csv("feature_matrix.csv")

    binary_vectors = []
    for _, row in df.iterrows():
        binary_vector = [1 if doi in row['ArticleReferences'] else 0 for doi in unique_dois]
        binary_vectors.append(binary_vector)

    binary_array = np.array(binary_vectors)
    jaccard_distances = pdist(binary_array, metric='jaccard')
    print(jaccard_distances.shape)
    s_matrix = squareform(jaccard_distances)
    # print(len(df))
    # print(distance_matrix.shape)
    # s_matrix = np.nan_to_num(s_matrix, nan=0)

    dbi_scores = {}
    sil_scores = {}
    # for linkage in ["complete"]:
    for linkage in ["agglomerative", "k-medoids", "k-means"]:
        print(linkage)
        dbi_scores_per_alg = []
        sil_scores_per_alg = []

        for k in range(3,15):
            cluster = None
            if linkage == "agglomerative":
                cluster = AgglomerativeClustering(n_clusters=k, linkage="average")
                cluster.fit(binary_array)
            elif linkage == "k-medoids":
                 cluster = KMedoids(n_clusters=k, method="pam", random_state=251524)
                 cluster.fit(binary_array)

            else:
                cluster = KMeans(
                    n_clusters=k, init= "k-means++", random_state=42, n_init='auto'
                )
                cluster.fit(binary_array)
            # # cluster = KMedoids(n_clusters=k, method="pam", init="k-medoids++", metric="precomputed",random_state=251524)
            # cluster = KMedoids(n_clusters=k, method="pam", random_state=251524)
            # # cluster = KMeans(
            # #     n_clusters=k, ini"k-means++", random_state=42, n_init='auto'
            # # )
            # # cluster = AgglomerativeClustering(n_clusters=k, linkage=linkage, metric="precomputed")
            # cluster.fit(binary_array)
            # cluster.fit(s_matrix)
            # cluster_titles = {i: [] for i in range(k)}
            s = silhouette_score(binary_array, cluster.labels_)
            # s = silhouette_score(s_matrix, cluster.labels_, metric="precomputed")
            dbi = davies_bouldin_score(binary_array, cluster.labels_)
            chi = calinski_harabasz_score(binary_array, cluster.labels_)
            # cluster_titles = {i: [] for i in np.unique(cluster.labels_)}
            print(k,s, dbi, chi)
            # for i, label in enumerate(cluster.labels_):
            #     cluster_titles[label].append(df['Title'].iloc[i])
            #
            # for cluster_id, titles in cluster_titles.items():
            #     print(f"Cluster {cluster_id}:")
            #     for title in titles:
            #         print(f"- {title}")
            dbi_scores_per_alg.append(dbi)
            sil_scores_per_alg.append(s)
        dbi_scores[linkage] = dbi_scores_per_alg
        sil_scores[linkage]= sil_scores_per_alg


        # for s , v in score_sil_per_alg.items():
        #     plt.plot(k_values, list(v.values()), label=f"{s}")
        #     plt.xlabel('Number of Clusters')
        #     plt.ylabel('Silhouette Score')
        #     plt.title('Silhouette Score for Optimal Clusters')
        #     plt.legend()
        #     plt.show()
        #
    for linkage, values in dbi_scores.items():
        plt.plot(range(3,15),  list(values), label=f"{linkage}", marker="o")
        plt.xlabel('Number of Clusters (k)')
        plt.ylabel('DBI Score')
        plt.title(f'Davies Bouldin Score for {linkage}model')
        plt.legend()
        plt.show()

    for linkage, values in sil_scores.items():
        plt.plot(range(3,15),  list(values), label=f"{linkage}", marker="o")
        plt.xlabel('Number of Clusters (k)')
        plt.ylabel('Silhouette Score')
        plt.title(f'Silhouette scores for {linkage} model')
        plt.legend()
        plt.show()

