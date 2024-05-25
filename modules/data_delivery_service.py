import pandas as pd
import tkinter as tk
from tkinter import filedialog
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle


class DataDeliveryManager:
    """
    A class to manage data delivery in various formats.

    Attributes:
    - preference (str): The preferred format for data delivery (CSV, Excel, PDF, HTML).
    - data (DataFrame): The data to be delivered.
    """

    def __init__(self, preference, data):
        """
        Initializes the DataDeliveryManager with preference and data.

        Args:
        - preference (str): The preferred format for data delivery (CSV, Excel, PDF, HTML).
        - data (DataFrame): The data to be delivered.
        """
        self.preference = preference
        self.data = data
        if preference is None:
            self.preference = "CSV"

    def save_data_to_csv_with_dialog(self):
        """
        Save data to a CSV file using a file dialog.
        """
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.data.to_csv(file_path, index=False)
            print(f"CSV file saved at: {file_path}")
        else:
            print("No file selected. CSV file not saved.")

    def save_data_to_excel_with_dialog(self):
        """
        Save data to an Excel file using a file dialog.
        """
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            self.data.to_excel(file_path, index=False)
            print(f"Excel file saved at: {file_path}")
        else:
            print("No file selected. Excel file not saved.")

    def save_data_to_html_with_dialog(self):
        """
        Save data to an HTML file using a file dialog.
        """
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        file_path = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML files", "*.html")])
        if file_path:
            self.data.to_html(file_path, index=False)
            print(f"HTML file saved at: {file_path}")
        else:
            print("No file selected. HTML file not saved.")

    def save_data_to_pdf_with_dialog(self):
        """
        Save data to a PDF file using a file dialog.
        """
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.generate_pdf(self.data, file_path)
            print(f"PDF file saved at: {file_path}")
        else:
            print("No file selected. PDF file not saved.")

    def generate_pdf(self, data, file_path):
        """
        Generate a PDF file with the given data.

        Args:
        - data (DataFrame): The data to be included in the PDF.
        - file_path (str): The file path to save the PDF.
        """
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        doc = SimpleDocTemplate(file_path, pagesize=letter)
        table_data = [data.columns.values.tolist()] + data.values.tolist()
        table = Table(table_data)
        style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), 'gray'),
                            ('TEXTCOLOR', (0, 0), (-1, 0), (1, 1, 1)),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), (1, 1, 1)),
                            ('GRID', (0, 0), (-1, -1), 1, 'BLACK')])
        table.setStyle(style)
        doc.build([table])

    def make_delivery(self):
        """
        Make the data delivery based on the preference.
        """
        if self.preference == "CSV":
            self.save_data_to_csv_with_dialog()
        elif self.preference == "Excel":
            self.save_data_to_excel_with_dialog()
        elif self.preference == "PDF":
            self.save_data_to_pdf_with_dialog()
        elif self.preference == "HTML":
            self.save_data_to_html_with_dialog()
        else:
            self.save_data_to_csv_with_dialog()


if __name__ == '__main__':
    # Example usage:
    data = {'Name': ['John', 'Anna', 'Peter', 'Linda'],
            'Age': [28, 34, 29, 32],
            'City': ['New York', 'Paris', 'Berlin', 'London']}
    df = pd.DataFrame(data)
    dd = DataDeliveryManager(data=df, preference="HTML")
