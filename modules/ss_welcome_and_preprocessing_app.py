import time
import threading
import customtkinter


class WelcomePage(customtkinter.CTk):
    def __init__(self, thread_target_task=None, database_table_name=None, number_of_days_ago= None):
        super().__init__()
        self.geometry("630X625")
        self.title("Science Sync")
        self.after(0, lambda: self.state('zoomed'))
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)
        self.display_welcome_text()
        self.display_authorization_services("Google", 0.5)
        self.display_authorization_services("Outlook", 0.6)
        self.authorization_in_progress_label = customtkinter.CTkLabel(self,
                                                                      text='',
                                                                      fg_color="transparent")
        self.thread_target_task = thread_target_task
        self.thread_target_task_arg_table = database_table_name
        self.thread_target_task_arg_days = number_of_days_ago

    def display_welcome_text(self):
        welcome_text = customtkinter.CTkLabel(self, text="Welcome to Science Sync", fg_color="transparent",
                                              font=customtkinter.CTkFont(size=32, weight="bold"))
        welcome_text.place(relx=0.5, rely=0.1, anchor='center')
        self.select_service_choice = customtkinter.CTkLabel(self, text="Please select a service to continue", fg_color="transparent",
                                              font=customtkinter.CTkFont(size=16))
        self.select_service_choice.place(relx=0.5, rely=0.4, anchor='center')


    def display_authorization_services(self, service, rely):
        service_button = customtkinter.CTkButton(self, text=service, corner_radius=32)
        service_button.place(relx=0.5, rely=rely, anchor='center')
        service_button.bind('<Button-1>',
                            lambda e, b=service_button: self.handle_service_button(e, service_button))

    def handle_service_button(self, event, service_button):
        if service_button.cget('state') == 'disabled':
            return
        self.update_info_text("Processes are complete. Please close this window to proceed")
        service_choice = service_button.cget("text")
        self.disable_authorization_options()
        self.select_service_choice.destroy()
        self.display_progress_bar()
        # time.sleep(3)
        if self.thread_target_task is not None:
            t = threading.Thread(target=self.thread_target_task, args=(service_choice, self, self.thread_target_task_arg_table, self.thread_target_task_arg_days))
            t.start()

    def disable_authorization_options(self):
        for widget in self.winfo_children():
            if widget.cget('text') in ['Google', 'Outlook']:
                widget.configure(state="disabled")

    def display_progress_bar(self):
        progressbar = customtkinter.CTkProgressBar(self)
        progressbar.grid(sticky="ew")
        progressbar.place(relx=0.5, rely=0.8, anchor='center')
        progressbar.configure(mode="indeterminate")
        progressbar.start()

    def update_info_text(self, text):
        self.authorization_in_progress_label.configure(text=text)
        self.authorization_in_progress_label.place(relx=0.5, rely=0.7, anchor='center')

    def quit_window(self):
        self.destroy()


if __name__ == "__main__":
    app = WelcomePage(thread_target_task=None)
    app.mainloop()

