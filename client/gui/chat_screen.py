import customtkinter as ctk

class ChatScreen(ctk.CTkFrame):
    def __init__(self, parent, controller, my_name):
        super().__init__(parent)
        self.controller = controller
        self.my_name = my_name
        self.current_friend = None

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200)
        self.sidebar.pack(side="left", fill="y")
        ctk.CTkLabel(self.sidebar, text=f"Me: {my_name}").pack(pady=10)
        
        self.friend_entry = ctk.CTkEntry(self.sidebar, placeholder_text="Chat with...")
        self.friend_entry.pack(pady=5, padx=5)
        ctk.CTkButton(self.sidebar, text="Start Chat", command=self.start_chat).pack(pady=5)
        
        # Chat Area
        self.chat_frame = ctk.CTkScrollableFrame(self)
        self.chat_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Input
        self.inp = ctk.CTkEntry(self)
        self.inp.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        self.inp.bind("<Return>", lambda e: self.send())
        ctk.CTkButton(self, text="Send", width=80, command=self.send).pack(side="right", padx=10)

    def start_chat(self):
        f = self.friend_entry.get()
        if f: 
            self.current_friend = f
            self.add_bubble(f"--- Chatting with {f} ---", "gray")

    def send(self):
        txt = self.inp.get()
        if txt and self.current_friend:
            self.controller.send_msg(self.current_friend, txt)
            self.inp.delete(0, 'end')

    def add_bubble(self, text, color):
        lbl = ctk.CTkLabel(self.chat_frame, text=text, fg_color=color, corner_radius=10, text_color="white", padx=10, pady=5)
        lbl.pack(anchor="e" if color=="blue" else "w", pady=2, padx=10)
        
    def on_msg(self, sender, text):
        # Nếu tin nhắn từ người đang chat hoặc chưa chat ai
        if self.current_friend == sender or not self.current_friend:
            self.current_friend = sender # Auto switch (Demo simple)
            self.add_bubble(f"{sender}: {text}", "green")