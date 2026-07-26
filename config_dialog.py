import os
import threading
import customtkinter as ctk
from tkinter import messagebox
from email_client import EmailClient


class ConfigDialog(ctk.CTkToplevel):
    def __init__(self, parent, email_client: EmailClient):
        super().__init__(parent)
        self.title("Resend 配置")
        self.geometry("450x300")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.email_client = email_client
        self.result = None

        self._setup_ui()

    def _setup_ui(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)

        api_key_label = ctk.CTkLabel(main_frame, text="Resend API Key:", font=("Helvetica", 14, "bold"))
        api_key_label.pack(pady=(0, 10))

        current_key = self.email_client.api_key or ""
        self.api_key_entry = ctk.CTkEntry(main_frame, width=350, show="*", font=("Helvetica", 12))
        self.api_key_entry.insert(0, current_key)
        self.api_key_entry.pack(pady=(0, 15))

        self.show_key_var = ctk.BooleanVar(value=False)
        show_key_checkbox = ctk.CTkCheckBox(
            main_frame, text="显示 API Key", variable=self.show_key_var,
            command=self._toggle_key_visibility, font=("Helvetica", 11)
        )
        show_key_checkbox.pack(pady=(0, 15))

        self.status_label = ctk.CTkLabel(main_frame, text="", font=("Helvetica", 11))
        self.status_label.pack(pady=(0, 15))

        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill=ctk.X)

        validate_btn = ctk.CTkButton(
            button_frame, text="验证", command=self._validate_api_key,
            width=100, fg_color="#0ea5e9", hover_color="#0284c7"
        )
        validate_btn.pack(side=ctk.LEFT)

        save_btn = ctk.CTkButton(
            button_frame, text="保存", command=self._save_config,
            width=120, fg_color="#10b981", hover_color="#059669"
        )
        save_btn.pack(side=ctk.LEFT, padx=(10, 0))

        cancel_btn = ctk.CTkButton(
            button_frame, text="取消", command=self._cancel,
            width=120, fg_color="#6b7280", hover_color="#4b5563"
        )
        cancel_btn.pack(side=ctk.RIGHT)

    def _toggle_key_visibility(self):
        if self.show_key_var.get():
            self.api_key_entry.configure(show="")
        else:
            self.api_key_entry.configure(show="*")

    def _validate_api_key(self):
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            messagebox.showerror("错误", "请输入 API Key")
            return

        self.status_label.configure(text="验证中...", text_color="orange")

        def validate():
            test_client = EmailClient(api_key)
            success, msg = test_client.validate_api_key()
            self.after(0, lambda: self._show_validation_result(success, msg))

        threading.Thread(target=validate, daemon=True).start()

    def _show_validation_result(self, success, message):
        if success:
            self.status_label.configure(text=f"✓ {message}", text_color="green")
        else:
            self.status_label.configure(text=f"✗ {message}", text_color="red")

    def _save_config(self):
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            messagebox.showerror("错误", "请输入 API Key")
            return

        test_client = EmailClient(api_key)
        success, msg = test_client.validate_api_key()

        if not success:
            confirm = messagebox.askyesno("警告", f"API Key 验证失败: {msg}\n确定要保存吗？")
            if not confirm:
                return

        self.email_client.set_api_key(api_key)

        env_path = os.path.join(os.path.dirname(__file__), ".env")
        with open(env_path, "w") as f:
            f.write(f"RESEND_API_KEY={api_key}\n")

        self.result = True
        self.destroy()

    def _cancel(self):
        self.result = False
        self.destroy()