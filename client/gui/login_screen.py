import customtkinter as ctk

class LoginScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        ctk.CTkLabel(self, text="SECURE CHAT", font=("Arial", 30)).pack(pady=40)
        
        self.user = ctk.CTkEntry(self, placeholder_text="Username")
        self.user.pack(pady=10)
        
        self.pwd = ctk.CTkEntry(self, placeholder_text="Password", show="*")
        self.pwd.pack(pady=10)
        
        ctk.CTkButton(self, text="LOGIN", command=self.do_login).pack(pady=10)
        ctk.CTkButton(self, text="REGISTER", fg_color="green", command=self.do_register).pack(pady=10)

    def do_login(self):
        u, p = self.user.get(), self.pwd.get()
        if self.controller.login(u, p, False):
            main_app = self.winfo_toplevel()
            main_app.show_chat(u)

    def do_register(self):
        u, p = self.user.get(), self.pwd.get()
        if self.controller.login(u, p, True):
            print("Registered!")

            main_app = self.winfo_toplevel()
            main_app.show_chat(u)