import customtkinter as ctk
from tkinter import filedialog

class ChatScreen(ctk.CTkFrame):
    def __init__(self, parent, controller, my_name):
        super().__init__(parent, fg_color="#1A2130")
        self.controller = controller
        self.my_name = my_name
        self.current_friend = None

        # --- SIDEBAR: Danh sách chat ---
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color="#101720", corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        
        ctk.CTkLabel(self.sidebar, text="SECRET SHARE", font=("Helvetica", 18, "bold"), text_color="#A67C52").pack(pady=30)
        
        # Khu vực danh sách bạn bè (Scrollable)
        self.sidebar_scroll = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.sidebar_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.friend_entry = ctk.CTkEntry(self.sidebar, placeholder_text="Tên bạn bè...", text_color="black")
        self.friend_entry.pack(pady=10, padx=15, fill="x")
        
        ctk.CTkButton(self.sidebar, text="BẮT ĐẦU CHAT", command=self.start_chat, fg_color="#A67C52").pack(pady=5, padx=15, fill="x")
        
        # --- KHUNG CHAT CHÍNH ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        self.header_label = ctk.CTkLabel(self.main_container, text="Chọn một người bạn", font=("Helvetica", 16, "bold"), text_color="white")
        self.header_label.pack(pady=(0, 10), anchor="w")

        self.chat_frame = ctk.CTkScrollableFrame(self.main_container, fg_color="#101720", corner_radius=15)
        self.chat_frame.pack(fill="both", expand=True)
        
        # --- INPUT AREA ---
        self.input_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.input_frame.pack(fill="x", pady=(15, 0))

        self.inp = ctk.CTkEntry(self.input_frame, placeholder_text="Nhập tin nhắn...", text_color="black", height=45)
        self.inp.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.inp.bind("<Return>", lambda e: self.send())

        # Nút chọn File
        self.btn_file = ctk.CTkButton(self.input_frame, text="📎", width=40, height=40, fg_color="#2D3648", command=self.upload_file)
        self.btn_file.pack(side="right", padx=(0, 5))

        self.btn_send = ctk.CTkButton(self.input_frame, text="GỬI", width=80, height=40, fg_color="#A67C52", command=self.send)
        self.btn_send.pack(side="right")

        # Load danh sách chat ban đầu
        self.render_chat_list()

    def render_chat_list(self):
        """Hiển thị danh sách những người đã từng nhắn tin"""
        for child in self.sidebar_scroll.winfo_children():
            child.destroy()
            
        # Lấy danh sách từ các session đã có trong controller
        for friend in self.controller.sessions.keys():
            btn = ctk.CTkButton(
                self.sidebar_scroll, text=f"👤 {friend}", 
                fg_color="transparent", text_color="white", anchor="w",
                command=lambda f=friend: self.switch_chat(f)
            )
            btn.pack(fill="x", padx=5, pady=2)

    def switch_chat(self, friend_name):
        self.current_friend = friend_name
        self.header_label.configure(text=f"Đang chat với: {friend_name}")

    def start_chat(self):
        f = self.friend_entry.get()
        if f: 
            self.switch_chat(f)
            self.render_chat_list()

    def upload_file(self):
        if not self.current_friend:
             return
        # Mở hộp thoại hệ thống chọn file
        file_path = filedialog.askopenfilename()
        if file_path:
            self.controller.send_file(self.current_friend, file_path)

    def send(self):
        txt = self.inp.get()
        if txt and self.current_friend:
            self.controller.send_msg(self.current_friend, txt) #
            self.inp.delete(0, 'end')

    def add_bubble(self, text, color_type):
        # Logic hiển thị bong bóng chat (giữ nguyên từ bản cũ)
        bubble_frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        bubble_frame.pack(fill="x", pady=5)
        
        bg = "#A67C52" if color_type == "blue" else "#2D3648"
        lbl = ctk.CTkLabel(bubble_frame, text=text, fg_color=bg, corner_radius=15, padx=15, pady=8, text_color="white")
        
        if color_type == "blue": lbl.pack(side="right", padx=10)
        else: lbl.pack(side="left", padx=10)
        
        # Cập nhật lại sidebar nếu có người mới nhắn tin
        self.render_chat_list()