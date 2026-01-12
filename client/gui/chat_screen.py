# client/gui/chat_screen.py
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

        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color="#101720", corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        
        ctk.CTkLabel(self.sidebar, text="SECRET SHARE", font=("Helvetica", 18, "bold"), text_color="#A67C52").pack(pady=30)
        
        self.sidebar_scroll = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.sidebar_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.friend_entry = ctk.CTkEntry(self.sidebar, placeholder_text="Tên bạn bè...", text_color="white", fg_color="#1A2130", border_color="#A67C52")
        self.friend_entry.pack(pady=10, padx=15, fill="x")
        
        ctk.CTkButton(self.sidebar, text="BẮT ĐẦU CHAT", command=self.start_chat, fg_color="#A67C52", hover_color="#8B6845").pack(pady=5, padx=15, fill="x")
        
        # --- MAIN CHAT ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        self.header_label = ctk.CTkLabel(self.main_container, text="Chọn một người bạn", font=("Helvetica", 16, "bold"), text_color="white")
        self.header_label.pack(pady=(0, 10), anchor="w")

        self.chat_frame = ctk.CTkScrollableFrame(self.main_container, fg_color="#101720", corner_radius=15, border_width=1, border_color="#2D3648")
        self.chat_frame.pack(fill="both", expand=True)
        
        # --- INPUT AREA ---
        self.input_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.input_frame.pack(fill="x", pady=(15, 0))

        self.inp = ctk.CTkEntry(self.input_frame, placeholder_text="Nhập tin nhắn...", text_color="white", fg_color="#1A2130", height=45, corner_radius=20)
        self.inp.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.inp.bind("<Return>", lambda e: self.send())

        self.btn_file = ctk.CTkButton(self.input_frame, text="📎", width=40, height=40, corner_radius=20, fg_color="#2D3648", hover_color="#3D495C", command=self.upload_file)
        self.btn_file.pack(side="right", padx=(0, 5))

        self.btn_send = ctk.CTkButton(self.input_frame, text="GỬI", width=80, height=40, corner_radius=20, fg_color="#A67C52", hover_color="#8B6845", command=self.send)
        self.btn_send.pack(side="right")

        self.render_chat_list()

    def render_chat_list(self):
        for child in self.sidebar_scroll.winfo_children():
            child.destroy()
        for friend in self.controller.sessions.keys():
            btn = ctk.CTkButton(self.sidebar_scroll, text=f"👤 {friend}", fg_color="transparent", text_color="white", anchor="w", command=lambda f=friend: self.switch_chat(f))
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
        if not self.current_friend: return
        file_path = filedialog.askopenfilename()
        if file_path:
            self.controller.send_file(self.current_friend, file_path)

    def send(self):
        txt = self.inp.get()
        if txt and self.current_friend:
            self.controller.send_msg(self.current_friend, txt)
            self.inp.delete(0, 'end')

    def add_bubble(self, text, color_type):
        bubble_frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        bubble_frame.pack(fill="x", pady=5)
        
        is_file = text.startswith("FILE_SHARE|")
        display_text = text
        bg = "#A67C52" if color_type == "blue" else "#2D3648"

        if is_file:
            try:
                parts = text.split("|")
                file_name = parts[1]
                display_text = f"📄 FILE: {file_name}\n(Nhấp để tải)"
                # SỬA LỖI: Bỏ padx, pady trong CTkButton
                lbl = ctk.CTkButton(
                    bubble_frame, text=display_text, fg_color=bg, 
                    hover_color="#3D495C", corner_radius=15, 
                    text_color="white", command=lambda t=text: self.download_file(t)
                )
            except:
                display_text = "Lỗi định dạng file"
                lbl = ctk.CTkLabel(bubble_frame, text=display_text, fg_color=bg, corner_radius=15, text_color="white", padx=15, pady=8)
        else:
            # CTkLabel vẫn dùng padx, pady được
            lbl = ctk.CTkLabel(bubble_frame, text=display_text, fg_color=bg, corner_radius=15, text_color="white", padx=15, pady=8)
        
        if color_type == "blue": lbl.pack(side="right", padx=10)
        else: lbl.pack(side="left", padx=10)
        self.render_chat_list()

    def download_file(self, raw_file_data):
        try:
            parts = raw_file_data.split("|")
            if len(parts) < 3: return
            
            file_name = parts[1]
            content_b64 = parts[2]
            
            save_path = filedialog.asksaveasfilename(
                initialfile=file_name,
                title="Lưu file",
                defaultextension=os.path.splitext(file_name)[1]
            )
            
            if save_path:
                file_bytes = base64.b64decode(content_b64)
                with open(save_path, "wb") as f:
                    f.write(file_bytes)
                messagebox.showinfo("Secret Share", f"Đã lưu file thành công!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu file: {e}")