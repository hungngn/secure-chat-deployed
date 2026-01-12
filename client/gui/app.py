import customtkinter as ctk
from client.core.controller import Controller
from client.gui.login_screen import LoginScreen
from client.gui.chat_screen import ChatScreen

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("900x650")
        self.title("SecretShare")
        self.configure(fg_color="#1A2130")
        
        self.controller = Controller(self)
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        
        self.show_login()

    def show_login(self):
        for w in self.container.winfo_children(): w.destroy()
        LoginScreen(self.container, self.controller).pack(fill="both", expand=True)

    def show_chat(self, username):
        for w in self.container.winfo_children(): w.destroy()
        self.chat_view = ChatScreen(self.container, self.controller, username)
        self.chat_view.pack(fill="both", expand=True)

    def on_new_message(self, friend, text, is_me):
        if hasattr(self, 'chat_view'):
            # is_me=True -> màu blue (Bronze), is_me=False -> màu friend
            color = "blue" if is_me else "green" 
            self.chat_view.add_bubble(text, color)

if __name__ == "__main__":
    app = App()
    app.mainloop()