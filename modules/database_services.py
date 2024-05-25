import sqlite3
import pandas as pd
import os


class ArticleDatabase:
    """
    A class to interact with an SQLite database storing article information.

    Attributes:
        db_file (str): Path to the SQLite database file.
        table_name (str): Name of the table storing article information.
        conn (sqlite3.Connection): SQLite database connection object.
        cursor (sqlite3.Cursor): Cursor object to execute SQL commands.
    """

    def __init__(self, db_file=os.path.join(os.getcwd(), "database", "articles.db"), table_name="articles"):
        """
        Initializes the ArticleDatabase object.

        Args:
            db_file (str, optional): Path to the SQLite database file. Defaults to 'database/articles.db'.
            table_name (str, optional): Name of the table storing article information. Defaults to 'articles'.
        """
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()

        # Create the 'articles' table if it doesn't exist
        self.cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY,
                Title TEXT,
                Author TEXT NULL,
                Link TEXT NULL,
                Abstract TEXT NULL,
                CitedAuthor TEXT NULL,
                SaveLink TEXT NULL,
                DOI TEXT NULL,
                ArticleReferences TEXT NULL,
                ReceivedDate TEXT NULL
            );""")
        self.conn.commit()

    def insert_article(self, title_val, authors_val, linktoArticle_val, abstract_val, cited_author_val, linktoSave_val,
                       doi_val, references_val, received_date_val):
        """
        Inserts a new article record into the database.

        Args:
            title_val (str): Title of the article.
            authors_val (str): Authors of the article.
            linktoArticle_val (str): Link to the article.
            abstract_val (str): Abstract of the article.
            cited_author_val (str): Cited author of the article.
            linktoSave_val (str): Link for saving the article.
            doi_val (str): Digital Object Identifier (DOI) of the article.
            references_val (list of str): List of references of the article.
            received_date_val (str) Date of receiving the article in the mail
        """
        self.cursor.execute("""
            INSERT INTO articles (Title, Author, Link, Abstract, CitedAuthor, SaveLink, DOI, ArticleReferences,ReceivedDate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (title_val, authors_val, linktoArticle_val, abstract_val, cited_author_val, linktoSave_val, doi_val,
              ", ".join(references_val), received_date_val))
        self.conn.commit()

    def insert_dataframe_rows_to_table(self, table_name, dataframe: pd.DataFrame):
        """
        Inserts rows from a DataFrame into the specified table in the database.

        Args:
            table_name (str): Name of the table to insert rows into.
            dataframe (pd.DataFrame): DataFrame containing rows to insert.
        """
        dataframe.to_sql(table_name, self.conn, if_exists="append", index=False)
        self.conn.commit()

    def update_doi_references(self, table_name, title_val, doi_val, references_val):
        """
        Updates the DOI and references of an article in the database.

        Args:
            table_name (str): Name of the table to update.
            title_val (str): Title of the article to update.e
            doi_val (str): New DOI value.
            references_val (list of str): Updated list of references.
        """
        self.cursor.execute(f"""
            UPDATE {table_name}
            SET DOI = ?, ArticleReferences = ?
            WHERE Title = ?
        """, (doi_val, ", ".join(references_val), title_val))
        self.conn.commit()

    def get_all_rows_into_df(self, table_name, start_date, end_date):
        """
        Retrieves all rows from the specified table within a given date range and returns them as a DataFrame.

        Args:
            table_name (str): Name of the table to retrieve rows from.
            start_date (str): Start date of the range (format: 'YYYY-MM-DD').
            end_date (str): End date of the range (format: 'YYYY-MM-DD').

        Returns:
            pd.DataFrame: DataFrame containing the retrieved rows.
        """
        query = f"SELECT * FROM {table_name} WHERE ReceivedDate BETWEEN '{start_date}' AND '{end_date}'"
        df = pd.read_sql_query(query, self.conn)
        return df

    def get_all_articles(self, table_name):
        """
        Retrieves all articles from the database and returns them.
        Args:
            table_name (str): Name of the table to retrieve rows from.
        Returns:
            list of tuples: List of tuples containing article information.
        """
        self.cursor.execute(f"SELECT * FROM {table_name}")
        return self.cursor.fetchall()

    def drop_table(self, table_name):
        """
        Drops the specified table from the database.

        Args:
            table_name (str): Name of the table to drop.
        """
        self.cursor.execute(f"""
            DROP TABLE {table_name};
        """)
        self.conn.commit()

    def check_titles_exist(self, table_name, title_list):
        """
        Checks if titles exist in the specified table.

        Args:
            table_name (str): Name of the table to check.
            title_list (list of str): List of titles to check for existence.

        Returns:
            list of str: Titles from title_list that do not exist in the table.
        """
        query = """
            SELECT Title FROM {}
            WHERE Title IN ({})
        """.format(table_name, ", ".join(["?"] * len(title_list)))

        self.cursor.execute(query, title_list)
        existing_titles = [row[0] for row in self.cursor.fetchall()]

        # Return titles that don't exist
        missing_titles = [title for title in title_list if title not in existing_titles]
        return missing_titles

    def update_received_date(self, table_name, title, received_date):
        query = f"UPDATE {table_name} SET ReceivedDate = ? WHERE Title = ?"
        self.cursor.execute(query, (received_date, title))
        self.conn.commit()

    def update_received_date_in_database(self, dataframe, table_name):
        for index, row in dataframe.iterrows():
            title = row['Title']
            received_date = row['ReceivedDate']
            self.update_received_date(table_name, title, received_date)
        self.close_connection()

    def close_connection(self):
        """
        Closes the database connection.
        """
        self.conn.close()


# Example usage:
if __name__ == "__main__":
    db = ArticleDatabase(table_name="articles")
    # Example usage goes here
    # e.g., data = db.get_all_rows_into_df("2022-04-03", '2022-05-03')
    # db.close_connection()
    # print(data)
