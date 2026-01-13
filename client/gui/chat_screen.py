import customtkinter as ctk
from tkinter import filedialog, messagebox
import base64
import os

class ChatScreen(ctk.CTkFrame):
    def __init__(self, parent, controller, my_name):
        super().__init__(parent, fg_color="#1A2130")
        self.controller = controller
        self.my_name = my_name
        self.current_friend = None

        self.sidebar = ctk.CTkFrame(self, width=220, fg_color="#101720", corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        ctk.CTkLabel(self.sidebar, text="SECRET SHARE", font=("Helvetica", 18, "bold"), text_color="#A67C52").pack(pady=30)
        self.sidebar_scroll = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.sidebar_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.friend_entry = ctk.CTkEntry(self.sidebar, placeholder_text="Tên bạn bè...", text_color="white", fg_color="#1A2130", border_color="#A67C52")
        self.friend_entry.pack(pady=10, padx=15, fill="x")
        ctk.CTkButton(self.sidebar, text="CHAT NGAY", command=self.start_chat, fg_color="#A67C52").pack(pady=5, padx=15, fill="x")

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        self.header_label = ctk.CTkLabel(self.main_container, text="Chọn bạn bè", font=("Helvetica", 16, "bold"), text_color="white")
        self.header_label.pack(pady=(0, 10), anchor="w")

        self.chat_frame = ctk.CTkScrollableFrame(self.main_container, fg_color="#101720", corner_radius=15, border_width=1, border_color="#2D3648")
        self.chat_frame.pack(fill="both", expand=True)

        self.input_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.input_frame.pack(fill="x", pady=(15, 0))
        self.inp = ctk.CTkEntry(self.input_frame, placeholder_text="Nhập tin nhắn...", text_color="white", fg_color="#1A2130", height=45, corner_radius=20)
        self.inp.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.inp.bind("<Return>", lambda e: self.send())
        ctk.CTkButton(self.input_frame, text="📎", width=40, height=40, corner_radius=20, fg_color="#2D3648", command=self.upload_file).pack(side="right", padx=(0, 5))
        ctk.CTkButton(self.input_frame, text="GỬI", width=80, height=40, corner_radius=20, fg_color="#A67C52", command=self.send).pack(side="right")
        self.render_chat_list()

    def render_chat_list(self):
        for child in self.sidebar_scroll.winfo_children(): child.destroy()
        try:
            cursor = self.controller.vault.conn.execute("SELECT DISTINCT friend_id FROM chat_history")
            for (f,) in cursor.fetchall():
                ctk.CTkButton(self.sidebar_scroll, text=f"👤 {f}", fg_color="transparent", text_color="white", anchor="w", command=lambda name=f: self.switch_chat(name)).pack(fill="x", padx=5, pady=2)
        except: pass

    def switch_chat(self, friend_name):
        self.current_friend = friend_name
        self.header_label.configure(text=f"Đang chat với: {friend_name}")
        for child in self.chat_frame.winfo_children(): child.destroy()
        history = self.controller.vault.get_chat_history(friend_name)
        for msg, is_me in history: self.add_bubble(msg, "blue" if is_me else "green", False)

    def start_chat(self):
        f = self.friend_entry.get()
        if f: self.switch_chat(f); self.render_chat_list()

    def upload_file(self):
        if not self.current_friend: return
        p = filedialog.askopenfilename()
        if p: self.controller.send_file(self.current_friend, p)

    def send(self):
        t = self.inp.get()
        if t and self.current_friend: self.controller.send_msg(self.current_friend, t); self.inp.delete(0, 'end')

    def add_bubble(self, text, color_type, update_sidebar=True):
        is_file = text.startswith("FILE_SHARE|")
        disp = f"📄 FILE: {text.split('|')[1]}" if is_file else text
        f = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        f.pack(fill="x", pady=5)
        bg = "#A67C52" if color_type == "blue" else "#2D3648"
        
        if is_file:
            ctk.CTkButton(f, text=disp, fg_color=bg, text_color="white", corner_radius=15, command=lambda: self.download_file(text)).pack(side="right" if color_type=="blue" else "left", padx=10)
        else:
            ctk.CTkLabel(f, text=disp, fg_color=bg, text_color="white", corner_radius=15, padx=15, pady=8).pack(side="right" if color_type=="blue" else "left", padx=10)
        if update_sidebar: self.render_chat_list()

    def download_file(self, raw):
        try:
            _, name, content = raw.split("|")
            p = filedialog.asksaveasfilename(initialfile=name)
            if p: 
                with open(p, "wb") as f: f.write(base64.b64decode(content))
                messagebox.showinfo("OK", "Lưu file thành công!")
        except: pass