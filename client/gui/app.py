# client/gui/app.py
import customtkinter as ctk
from client.core.controller import Controller
from .login_screen import LoginScreen
from .chat_screen import ChatScreen

ctk.set_appearance_mode("Dark")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("800x600")
        self.title("SecureChat")
        
        self.controller = Controller(self)
        self.container = ctk.CTkFrame(self)
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
        # Callback từ Controller đẩy lên GUI
        if hasattr(self, 'chat_view'):
            if is_me:
                self.chat_view.add_bubble(text, "blue")
            else:
                self.chat_view.on_msg(friend, text)

if __name__ == "__main__":
    app = App()
    app.mainloop()