import os
import webbrowser
import customtkinter
import pandas as pd
from modules.data_delivery_service import DataDeliveryManager


def read_clusters():
    clusters_df = pd.read_csv('my_data.csv')
    return clusters_df


def read_titles_metadata():
    titles_metadata_df = pd.read_csv('googlearticles.csv')
    return titles_metadata_df

def callback(url):
    webbrowser.open_new(url)


def build_label(frame, text, wrap_length=400, weight="normal", font_size=14, pad_y=10):
    label = customtkinter.CTkLabel(frame,
                                   text=text,
                                   wraplength=wrap_length,
                                   justify="left",
                                   font=customtkinter.CTkFont(size=font_size, weight=weight))
    label.grid(padx=0, pady=pad_y, sticky="W")
    return label


def build_button(frame, text, sticky, padx, pady):
    button = customtkinter.CTkButton(frame,
                                     text=text)
    button.grid(padx=padx, pady=pady, sticky=sticky)
    return button


def destroy_frame_widgets(frame):
    for widget in frame.winfo_children():
        widget.destroy()


def change_appearance_mode_event(new_appearance_mode: str):
    customtkinter.set_appearance_mode(new_appearance_mode)


def change_scaling_event(new_scaling: str):
    new_scaling_float = int(new_scaling.replace("%", "")) / 100
    customtkinter.set_widget_scaling(new_scaling_float)


def display_appearance_grid(frame):
    appearance_mode_label = customtkinter.CTkLabel(frame, text="Appearance Mode:",
                                                   anchor="w")
    appearance_mode_label.grid(row=1, sticky="w")
    appearance_mode_enumeration = customtkinter.CTkOptionMenu(frame,
                                                              values=["Light", "Dark", "System"],
                                                              command=change_appearance_mode_event)
    appearance_mode_enumeration.grid(row=2, sticky="w")
    scaling_label = customtkinter.CTkLabel(frame, text="UI Scaling:", anchor="w")
    scaling_label.grid(row=1, sticky="e", padx=(0, 80))
    scaling_enumeration = customtkinter.CTkOptionMenu(frame,
                                                      values=["80%", "90%", "100%", "110%", "120%"],
                                                      command=change_scaling_event)
    scaling_enumeration.grid(row=2, sticky="e")


def open_input_dialog_event():
    dialog = customtkinter.CTkInputDialog(text="Type in a number:", title="CTkInputDialog")
    print("CTkInputDialog:", dialog.get_input())


class DisplayResultsPage(customtkinter.CTk):

    def __init__(self, clusters_df, titles_metadata_df):
        super().__init__()

        self.clusters_df = clusters_df
        self.title_metadata_df = titles_metadata_df

        self.title("Science Sync")
        self.after(0, lambda: self.state('zoomed'))

        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=1)
        self.grid_rowconfigure((1, 2), weight=1)

        self.clusters_frame = self.setup_frame(0, 1, frame_title='Related Groups / All Data')
        self.titles_frame = self.setup_frame(1, 1, column_span=2, frame_title='Articles From Google Scholar')
        self.title_metadata_frame = self.setup_frame(3, 1, column_span=1, frame_title='Article Information')
        self.window_metadata_frame = self.setup_frame(3, 1, row=5, frame_title='Settings')
        self.config_settings_tabs()
        self.display_all_data_grid()
        if clusters_df is not None:
            self.display_clusters_grid()
        self.export_all_data = None
        self.export_groups = None
        self.titles_lists = []

    def setup_frame(self, column, column_weight, row=0, column_span=1, frame_title=''):
        frame = customtkinter.CTkScrollableFrame(self, corner_radius=0,
                                                 label_text=frame_title,
                                                 label_font=customtkinter.CTkFont(size=18, weight='bold')
                                                 )
        frame.grid(row=row, column=column, rowspan=8, columnspan=column_span, sticky="nsew")
        frame.columnconfigure(0, weight=column_weight)
        frame.grid_rowconfigure(4, weight=1)
        return frame

    def setup_not_scrollable_frame(self, column, column_weight, row=0, column_span=1, frame_title=''):
        frame = customtkinter.CTkFrame(self, corner_radius=0
                                       )
        frame.grid(row=row, column=column, rowspan=8, columnspan=column_span, sticky="nsew")
        frame.columnconfigure(0, weight=column_weight)
        frame.grid_rowconfigure(4, weight=1)
        return frame


    def display_all_data_grid(self):
        all_cluster_button = customtkinter.CTkButton(self.clusters_frame, text="All")
        all_cluster_button.bind('<Button-1>',
                                lambda e, b=all_cluster_button: self.handle_cluster_button_click(b.cget('text')))
        all_cluster_button.grid(padx=20, pady=20)
    def display_clusters_grid(self):
        for cluster in self.clusters_df["Group"].unique().tolist():
            cluster_button = customtkinter.CTkButton(self.clusters_frame, text=f'Group {cluster}')
            cluster_button.bind('<Button-1>',
                                lambda e, b=cluster_button: self.handle_cluster_button_click(b.cget('text')))
            cluster_button.grid(padx=20, pady=20)

    def handle_cluster_button_click(self, button_text):
        if button_text == "All":
            cluster_titles = self.title_metadata_df["Title"].tolist()
        else:
            cluster = button_text.replace('Group ', '')
            # cluster_titles = self.clusters_df.get(int(cluster))
            cluster_titles = self.clusters_df.loc[self.clusters_df['Group'] == int(cluster), 'Title'].tolist()
        destroy_frame_widgets(self.titles_frame)
        self.titles_lists = divide_list_into_chunks(cluster_titles, 20)
        self.display_page_titles(0)

    def handle_export_as_event(self, file_format: str):
        if self.export_all_data_checkbox.get() == 1:
            delivery_manager = DataDeliveryManager(preference=file_format, data=self.title_metadata_df)
            delivery_manager.make_delivery()
        if self.export_groups_checkbox.get() == 1:
            delivery_manager = DataDeliveryManager(preference=file_format, data=self.clusters_df)
            delivery_manager.make_delivery()

    def display_save_options(self, frame):
        self.export_all_data_checkbox = customtkinter.CTkCheckBox(frame, text="Export all Articles")
        self.export_all_data_checkbox.grid(row=1, sticky="w")
        self.export_groups_checkbox = customtkinter.CTkCheckBox(frame, text="Export Cluster Groupings")
        self.export_groups_checkbox.grid(row=2, sticky="w", pady=10)
        export_as_label = build_label(frame, "Export As: ", pad_y=0, weight="bold")
        export_as_label.grid(row=3, sticky="w")
        export_as_option_menu = customtkinter.CTkOptionMenu(frame,
                                                            values=["Excel", "CSV", "HTML", "PDF"],
                                                            command=self.handle_export_as_event)
        export_as_option_menu.grid(row=3, sticky="e")

    def display_page_titles(self, page_number):
        for index, title in enumerate(self.titles_lists[page_number]):
            title_label = build_label(self.titles_frame, title, wrap_length=700, pad_y=20)
            title_label.configure(cursor="hand2")
            title_label.bind('<Button-1>',
                             lambda e, label=title_label: self.handle_title_label_click(label.cget('text')))
        previous_page_button = customtkinter.CTkButton(self.titles_frame, text="Previous Page")
        previous_page_button.grid(row=21, sticky="w")
        previous_page_button.bind('<Button-1>',
                                  lambda e, b=previous_page_button: self.hande_page_navigation_event(page_number, b))
        next_page_button = customtkinter.CTkButton(self.titles_frame, text="Next Page")
        next_page_button.grid(row=21, sticky="e")
        next_page_button.bind('<Button-1>',
                              lambda e, b=next_page_button: self.hande_page_navigation_event(page_number, b))
        if page_number == 0:
            previous_page_button.configure(state='disabled')
        if page_number == len(self.titles_lists) - 1:
            next_page_button.configure(state='disabled')

    def hande_page_navigation_event(self, current_page_number, button):
        if button.cget('state') == 'disabled':
            return
        new_page_number = current_page_number - 1 if 'Previous' in button.cget('text') else current_page_number + 1
        self.delete_current_page_titles()
        self.display_page_titles(new_page_number)

    def delete_current_page_titles(self):
        for widget in self.titles_frame.winfo_children():
            widget.destroy()

    def handle_title_label_click(self, title):
        destroy_frame_widgets(self.title_metadata_frame)
        title_metadata = self.title_metadata_df.loc[self.title_metadata_df['Title'] == title]
        if not title_metadata.empty:
            build_label(self.title_metadata_frame, title, weight="bold", wrap_length=350)
            build_label(self.title_metadata_frame, f"Authors: {title_metadata.iloc[0]['Author']}")
            build_label(self.title_metadata_frame, f"Abstract:\n{title_metadata.iloc[0]['Abstract']}", wrap_length=400)
            build_label(self.title_metadata_frame, f"Cited Authors:\n{title_metadata.iloc[0]['CitedAuthor']}")
            title_link = customtkinter.CTkButton(self.title_metadata_frame, text="Navigate To Article")
            title_link.grid(row=5, sticky="w", pady=10)
            title_link.bind("<Button-1>", lambda e: callback(title_metadata.iloc[0]['Link']))
            title_save_link = customtkinter.CTkButton(self.title_metadata_frame, text="Save On Google Scholar")
            title_save_link.grid(row=5, sticky="e", pady=10)
            title_save_link.bind("<Button-1>", lambda e: callback(title_metadata.iloc[0]['SaveLink']))

    def config_settings_tabs(self):
        tabview = customtkinter.CTkTabview(self.window_metadata_frame)
        tabview.grid(sticky="nsew")
        tabview.add("Saving Options")
        tabview.add("Display Settings")
        tabview.tab("Saving Options").grid_columnconfigure(0, weight=1)
        tabview.tab("Display Settings").grid_columnconfigure(0, weight=1)
        display_appearance_grid(tabview.tab('Display Settings'))
        self.display_save_options(tabview.tab('Saving Options'))


def divide_list_into_chunks(lst, chunk_size):
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


if __name__ == "__main__":
    # Example usage
    app = DisplayResultsPage(None, read_titles_metadata())
    app.mainloop()
