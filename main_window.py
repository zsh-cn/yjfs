import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox, END as TK_END
from email_client import EmailClient
from config_dialog import ConfigDialog
from config_manager import ConfigManager


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Resend 邮件发送器")
        self.geometry("900x800")
        self.resizable(True, True)

        self.email_client = EmailClient()
        self.config_manager = ConfigManager()
        self.attachments = []
        self.batch_attachments = []
        self.batch_recipients = []

        self._setup_ui()
        self._load_last_input()

    def _setup_ui(self):
        self._create_menu()
        self._create_main_content()

    def _create_menu(self):
        menu_frame = ctk.CTkFrame(self, height=40)
        menu_frame.pack(fill=ctk.X, padx=10, pady=10)

        config_btn = ctk.CTkButton(
            menu_frame, text="⚙️ 配置", command=self._open_config,
            width=100, fg_color="#4f46e5", hover_color="#4338ca"
        )
        config_btn.pack(side=ctk.LEFT, padx=5)

        self.status_label = ctk.CTkLabel(
            menu_frame, text="未连接", font=("Helvetica", 12),
            text_color="red"
        )
        self.status_label.pack(side=ctk.RIGHT, padx=20)

        self._update_status()

    def _update_status(self):
        if self.email_client.api_key:
            self.status_label.configure(text="✓ 已连接", text_color="green")
        else:
            self.status_label.configure(text="✗ 未连接", text_color="red")

    def _open_config(self):
        dialog = ConfigDialog(self, self.email_client)
        self.wait_window(dialog)
        if dialog.result:
            self._update_status()

    def _create_main_content(self):
        tab_view = ctk.CTkTabview(self)
        tab_view.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        tab_view.add("单封发送")
        tab_view.add("批量发送")

        self._setup_single_send_tab(tab_view.tab("单封发送"))
        self._setup_batch_send_tab(tab_view.tab("批量发送"))

    def _setup_single_send_tab(self, parent):
        main_frame = ctk.CTkFrame(parent)
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)

        fields = [
            ("发件人", "from"),
            ("收件人", "to"),
            ("主题", "subject"),
        ]

        self.single_fields = {}
        for label_text, field_name in fields:
            row_frame = ctk.CTkFrame(main_frame)
            row_frame.pack(fill=ctk.X, pady=(0, 10))

            label = ctk.CTkLabel(row_frame, text=label_text, width=80, font=("Helvetica", 12))
            label.pack(side=ctk.LEFT, padx=(0, 10))

            entry = ctk.CTkEntry(row_frame, font=("Helvetica", 12))
            entry.pack(fill=ctk.X, expand=True)
            self.single_fields[field_name] = entry

        content_type_frame = ctk.CTkFrame(main_frame)
        content_type_frame.pack(fill=ctk.X, pady=(0, 5))

        self.single_content_type = ctk.StringVar(value="html")
        html_radio = ctk.CTkRadioButton(
            content_type_frame, text="HTML", variable=self.single_content_type, value="html",
            font=("Helvetica", 11)
        )
        html_radio.pack(side=ctk.LEFT, padx=(0, 15))

        text_radio = ctk.CTkRadioButton(
            content_type_frame, text="纯文本", variable=self.single_content_type, value="text",
            font=("Helvetica", 11)
        )
        text_radio.pack(side=ctk.LEFT)

        template_frame = ctk.CTkFrame(main_frame)
        template_frame.pack(fill=ctk.X, pady=(0, 10))

        template_label = ctk.CTkLabel(template_frame, text="邮件模板", width=80, font=("Helvetica", 12))
        template_label.pack(side=ctk.LEFT, padx=(0, 10))

        self.single_template_var = ctk.StringVar(value="")
        self.single_template_combo = ctk.CTkComboBox(
            template_frame, variable=self.single_template_var,
            values=[""], command=self._apply_single_template,
            font=("Helvetica", 12)
        )
        self.single_template_combo.pack(side=ctk.LEFT, fill=ctk.X, expand=True)

        save_template_btn = ctk.CTkButton(
            template_frame, text="保存模板", command=self._save_single_template,
            width=100, fg_color="#8b5cf6", hover_color="#7c3aed"
        )
        save_template_btn.pack(side=ctk.RIGHT, padx=(10, 0))

        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill=ctk.BOTH, expand=True, pady=(0, 10))

        content_label = ctk.CTkLabel(content_frame, text="邮件内容", width=80, font=("Helvetica", 12))
        content_label.pack(side=ctk.TOP, anchor=ctk.W, padx=(0, 10), pady=(0, 5))

        self.content_text = ctk.CTkTextbox(content_frame, font=("Helvetica", 12))
        self.content_text.pack(fill=ctk.BOTH, expand=True)

        clear_content_btn = ctk.CTkButton(
            content_frame, text="清空内容", command=self._clear_single_content,
            width=80, fg_color="#f59e0b", hover_color="#d97706"
        )
        clear_content_btn.pack(side=ctk.BOTTOM, anchor=ctk.E, pady=(5, 0))

        attachment_frame = ctk.CTkFrame(main_frame)
        attachment_frame.pack(fill=ctk.X, pady=(0, 15))

        attach_btn = ctk.CTkButton(
            attachment_frame, text="添加附件", command=self._add_attachment,
            width=100, fg_color="#6366f1", hover_color="#4f46e5"
        )
        attach_btn.pack(side=ctk.LEFT)

        clear_attach_btn = ctk.CTkButton(
            attachment_frame, text="清空附件", command=self._clear_attachments,
            width=100, fg_color="#ef4444", hover_color="#dc2626"
        )
        clear_attach_btn.pack(side=ctk.LEFT, padx=(10, 0))

        self.attachment_list = ctk.CTkLabel(
            attachment_frame, text="", font=("Helvetica", 11)
        )
        self.attachment_list.pack(side=ctk.LEFT, padx=(15, 0))

        send_btn_frame = ctk.CTkFrame(main_frame)
        send_btn_frame.pack(fill=ctk.X, pady=(10, 0))

        self.single_send_btn = ctk.CTkButton(
            send_btn_frame, text="发送邮件", command=self._send_single_email,
            height=45, font=("Helvetica", 12, "bold"),
            fg_color="#10b981", hover_color="#059669"
        )
        self.single_send_btn.pack(fill=ctk.X, padx=5, pady=5)

    def _add_attachment(self):
        files = filedialog.askopenfilenames(title="选择附件")
        if files:
            self.attachments.extend(files)
            self.attachment_list.configure(text=f"已添加 {len(self.attachments)} 个附件")

    def _clear_attachments(self):
        self.attachments.clear()
        self.attachment_list.configure(text="")

    def _clear_single_content(self):
        self.content_text.delete("1.0", TK_END)

    def _apply_single_template(self, template_name):
        if not template_name:
            return
        template = self.config_manager.get_template(template_name)
        if template:
            self.single_fields["subject"].delete(0, TK_END)
            self.single_fields["subject"].insert(0, template["subject"])
            self.content_text.delete("1.0", TK_END)
            self.content_text.insert("1.0", template["content"])
            self.single_content_type.set(template["content_type"])

    def _save_single_template(self):
        subject = self.single_fields["subject"].get().strip()
        content = self.content_text.get("1.0", TK_END).strip()
        content_type = self.single_content_type.get()

        if not subject or not content:
            messagebox.showerror("错误", "请填写主题和内容")
            return

        dialog = self._create_input_dialog("保存模板", "请输入模板名称:")
        template_name = dialog.result
        if template_name and template_name.strip():
            self.config_manager.save_template(template_name.strip(), subject, content, content_type)
            self._refresh_template_combo(self.single_template_combo)
            messagebox.showinfo("成功", f"模板 '{template_name}' 保存成功")

    def _refresh_template_combo(self, combo=None):
        templates = self.config_manager.list_templates()
        if combo:
            combo.configure(values=[""] + list(templates.keys()))
        if hasattr(self, "single_template_combo"):
            self.single_template_combo.configure(values=[""] + list(templates.keys()))
        if hasattr(self, "batch_template_combo"):
            self.batch_template_combo.configure(values=[""] + list(templates.keys()))

    def _apply_batch_template(self, template_name):
        if not template_name:
            return
        template = self.config_manager.get_template(template_name)
        if template:
            self.batch_subject.delete(0, TK_END)
            self.batch_subject.insert(0, template["subject"])
            self.batch_content.delete("1.0", TK_END)
            self.batch_content.insert("1.0", template["content"])
            self.batch_content_type.set(template["content_type"])

    def _load_last_input(self):
        single_input = self.config_manager.get_last_input("single")
        if single_input:
            for field, value in single_input.get("fields", {}).items():
                if field in self.single_fields:
                    self.single_fields[field].delete(0, TK_END)
                    self.single_fields[field].insert(0, value)
            if "content" in single_input:
                self.content_text.delete("1.0", TK_END)
                self.content_text.insert("1.0", single_input["content"])
            if "content_type" in single_input:
                self.single_content_type.set(single_input["content_type"])

        batch_input = self.config_manager.get_last_input("batch")
        if batch_input:
            for field, value in batch_input.get("fields", {}).items():
                if field in self.batch_fields:
                    self.batch_fields[field].delete(0, TK_END)
                    self.batch_fields[field].insert(0, value)
            if "subject" in batch_input:
                self.batch_subject.delete(0, TK_END)
                self.batch_subject.insert(0, batch_input["subject"])
            if "content" in batch_input:
                self.batch_content.delete("1.0", TK_END)
                self.batch_content.insert("1.0", batch_input["content"])
            if "content_type" in batch_input:
                self.batch_content_type.set(batch_input["content_type"])
            if "recipients" in batch_input:
                self.batch_recipients = batch_input["recipients"]
                self._update_recipient_list()

        self._refresh_template_combo(self.single_template_combo)

    def _save_single_input(self):
        data = {
            "fields": {
                "from": self.single_fields["from"].get().strip(),
                "to": self.single_fields["to"].get().strip(),
                "subject": self.single_fields["subject"].get().strip(),
            },
            "content": self.content_text.get("1.0", TK_END).strip(),
            "content_type": self.single_content_type.get(),
        }
        self.config_manager.save_last_input("single", data)

    def _save_batch_input(self):
        data = {
            "fields": {
                "from": self.batch_fields["from"].get().strip(),
            },
            "subject": self.batch_subject.get().strip(),
            "content": self.batch_content.get("1.0", TK_END).strip(),
            "content_type": self.batch_content_type.get(),
            "recipients": self.batch_recipients,
        }
        self.config_manager.save_last_input("batch", data)

    def _send_single_email(self):
        from_email = self.single_fields["from"].get().strip()
        to_email = self.single_fields["to"].get().strip()
        subject = self.single_fields["subject"].get().strip()
        content = self.content_text.get("1.0", TK_END).strip()
        content_type = self.single_content_type.get()

        if not self.email_client.api_key:
            messagebox.showerror("错误", "请先配置 Resend API Key")
            return

        if not from_email or not to_email or not subject:
            messagebox.showerror("错误", "请填写完整的发件人、收件人和主题")
            return

        to_emails = [e.strip() for e in to_email.split(",")]

        attachments = self.email_client.prepare_attachments(self.attachments)

        self.single_send_btn.configure(state=ctk.DISABLED, text="发送中...")

        def send():
            html_content = content if content_type == "html" else None
            text_content = content if content_type == "text" else None

            success, message, email_id = self.email_client.send_single_email(
                from_email=from_email,
                to_emails=to_emails,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                attachments=attachments
            )

            self.after(0, lambda: self._handle_send_result(success, message, email_id, self.single_send_btn))

        threading.Thread(target=send, daemon=True).start()

    def _handle_send_result(self, success, message, email_id, btn, tab="single"):
        if tab == "single":
            btn.configure(state=ctk.NORMAL, text="发送邮件")
        else:
            btn.configure(state=ctk.NORMAL, text="批量发送")

        if success:
            if tab == "single":
                self._save_single_input()
            else:
                self._save_batch_input()

        messagebox.showinfo(
            "发送结果",
            f"{message}\n邮件ID: {email_id}" if success and email_id else message
        )

    def _setup_batch_send_tab(self, parent):
        main_frame = ctk.CTkFrame(parent)
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)

        fields = [
            ("发件人", "from"),
        ]

        self.batch_fields = {}
        for label_text, field_name in fields:
            row_frame = ctk.CTkFrame(main_frame)
            row_frame.pack(fill=ctk.X, pady=(0, 10))

            label = ctk.CTkLabel(row_frame, text=label_text, width=80, font=("Helvetica", 12))
            label.pack(side=ctk.LEFT, padx=(0, 10))

            entry = ctk.CTkEntry(row_frame, font=("Helvetica", 12))
            entry.pack(fill=ctk.X, expand=True)
            self.batch_fields[field_name] = entry

        recipient_frame = ctk.CTkFrame(main_frame)
        recipient_frame.pack(fill=ctk.X, pady=(0, 15))

        recipient_label = ctk.CTkLabel(recipient_frame, text="收件人列表", width=100, font=("Helvetica", 12))
        recipient_label.pack(side=ctk.LEFT, padx=(0, 10))

        add_recipient_btn = ctk.CTkButton(
            recipient_frame, text="添加收件人", command=self._add_batch_recipient,
            width=120, fg_color="#6366f1", hover_color="#4f46e5"
        )
        add_recipient_btn.pack(side=ctk.RIGHT, padx=(10, 0))

        import_btn = ctk.CTkButton(
            recipient_frame, text="导入CSV", command=self._import_csv,
            width=100, fg_color="#0ea5e9", hover_color="#0284c7"
        )
        import_btn.pack(side=ctk.RIGHT)

        self.recipient_listbox = ctk.CTkTextbox(main_frame, height=100, font=("Helvetica", 11))
        self.recipient_listbox.pack(fill=ctk.X, pady=(0, 15))

        common_frame = ctk.CTkFrame(main_frame)
        common_frame.pack(fill=ctk.X, pady=(0, 15))

        common_label = ctk.CTkLabel(common_frame, text="共同主题", width=100, font=("Helvetica", 12))
        common_label.pack(side=ctk.LEFT, padx=(0, 10))

        self.batch_subject = ctk.CTkEntry(common_frame, font=("Helvetica", 12))
        self.batch_subject.pack(fill=ctk.X, expand=True)

        content_type_frame = ctk.CTkFrame(main_frame)
        content_type_frame.pack(fill=ctk.X, pady=(0, 5))

        self.batch_content_type = ctk.StringVar(value="html")
        html_radio = ctk.CTkRadioButton(
            content_type_frame, text="HTML", variable=self.batch_content_type, value="html",
            font=("Helvetica", 11)
        )
        html_radio.pack(side=ctk.LEFT, padx=(0, 15))

        text_radio = ctk.CTkRadioButton(
            content_type_frame, text="纯文本", variable=self.batch_content_type, value="text",
            font=("Helvetica", 11)
        )
        text_radio.pack(side=ctk.LEFT)

        batch_template_frame = ctk.CTkFrame(main_frame)
        batch_template_frame.pack(fill=ctk.X, pady=(0, 10))

        batch_template_label = ctk.CTkLabel(batch_template_frame, text="邮件模板", width=80, font=("Helvetica", 12))
        batch_template_label.pack(side=ctk.LEFT, padx=(0, 10))

        self.batch_template_var = ctk.StringVar(value="")
        self.batch_template_combo = ctk.CTkComboBox(
            batch_template_frame, variable=self.batch_template_var,
            values=[""], command=self._apply_batch_template,
            font=("Helvetica", 12)
        )
        self.batch_template_combo.pack(side=ctk.LEFT, fill=ctk.X, expand=True)

        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill=ctk.X, pady=(0, 10))

        content_label = ctk.CTkLabel(content_frame, text="邮件内容", width=80, font=("Helvetica", 12))
        content_label.pack(side=ctk.TOP, anchor=ctk.W, padx=(0, 10), pady=(5, 0))

        self.batch_content = ctk.CTkTextbox(content_frame, height=120, font=("Helvetica", 12))
        self.batch_content.pack(fill=ctk.X, pady=(0, 5))

        clear_content_btn = ctk.CTkButton(
            content_frame, text="清空内容", command=self._clear_batch_content,
            width=80, fg_color="#f59e0b", hover_color="#d97706"
        )
        clear_content_btn.pack(side=ctk.RIGHT, pady=(0, 5))

        attachment_frame = ctk.CTkFrame(main_frame)
        attachment_frame.pack(fill=ctk.X, pady=(0, 10))

        attach_btn = ctk.CTkButton(
            attachment_frame, text="添加附件", command=self._add_batch_attachment,
            width=100, fg_color="#6366f1", hover_color="#4f46e5"
        )
        attach_btn.pack(side=ctk.LEFT)

        clear_attach_btn = ctk.CTkButton(
            attachment_frame, text="清空附件", command=self._clear_batch_attachments,
            width=100, fg_color="#ef4444", hover_color="#dc2626"
        )
        clear_attach_btn.pack(side=ctk.LEFT, padx=(10, 0))

        self.batch_attachment_list = ctk.CTkLabel(
            attachment_frame, text="", font=("Helvetica", 11)
        )
        self.batch_attachment_list.pack(side=ctk.LEFT, padx=(15, 0))

        send_btn_frame = ctk.CTkFrame(main_frame)
        send_btn_frame.pack(fill=ctk.X, pady=(5, 0))

        self.batch_send_btn = ctk.CTkButton(
            send_btn_frame, text="批量发送", command=self._send_batch_email,
            height=45, font=("Helvetica", 12, "bold"),
            fg_color="#10b981", hover_color="#059669"
        )
        self.batch_send_btn.pack(fill=ctk.X, padx=5, pady=5)

    def _add_batch_recipient(self):
        dialog = self._create_input_dialog("添加收件人", "请输入收件人邮箱:")
        email = dialog.result
        if email and email.strip():
            email = email.strip().lower()
            if email not in [e.lower() for e in self.batch_recipients]:
                self.batch_recipients.append(email)
                self._update_recipient_list()
            else:
                messagebox.showwarning("警告", f"收件人 {email} 已存在")

    def _create_input_dialog(self, title, message):
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("400x180")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.result = None

        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)

        label = ctk.CTkLabel(main_frame, text=message, font=("Helvetica", 12))
        label.pack(pady=(0, 15))

        entry = ctk.CTkEntry(main_frame, width=350, font=("Helvetica", 12))
        entry.pack(pady=(0, 20))
        entry.focus()

        def on_ok():
            dialog.result = entry.get()
            dialog.destroy()

        def on_cancel():
            dialog.result = None
            dialog.destroy()

        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill=ctk.X)

        ok_btn = ctk.CTkButton(button_frame, text="确定", command=on_ok, width=120, fg_color="#10b981", hover_color="#059669")
        ok_btn.pack(side=ctk.LEFT, padx=(0, 10))

        cancel_btn = ctk.CTkButton(button_frame, text="取消", command=on_cancel, width=120, fg_color="#6b7280", hover_color="#4b5563")
        cancel_btn.pack(side=ctk.RIGHT)

        dialog.bind("<Return>", lambda e: on_ok())
        dialog.bind("<Escape>", lambda e: on_cancel())

        self.wait_window(dialog)
        return dialog

    def _import_csv(self):
        file_path = filedialog.askopenfilename(
            title="选择CSV文件",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                before_count = len(self.batch_recipients)
                existing_emails = {e.lower() for e in self.batch_recipients}
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for line in lines:
                        emails = [e.strip() for e in line.split(",")]
                        for email in emails:
                            if email and "@" in email:
                                email_lower = email.lower()
                                if email_lower not in existing_emails:
                                    self.batch_recipients.append(email)
                                    existing_emails.add(email_lower)
                after_count = len(self.batch_recipients)
                imported_count = after_count - before_count
                self._update_recipient_list()
                messagebox.showinfo("成功", f"成功导入 {imported_count} 个收件人")
            except Exception as e:
                messagebox.showerror("错误", f"导入失败: {e}")

    def _update_recipient_list(self):
        self.recipient_listbox.delete("1.0", TK_END)
        for i, email in enumerate(self.batch_recipients, 1):
            self.recipient_listbox.insert(TK_END, f"{i}. {email}\n")

    def _clear_batch_content(self):
        self.batch_content.delete("1.0", TK_END)

    def _add_batch_attachment(self):
        files = filedialog.askopenfilenames(title="选择附件")
        if files:
            self.batch_attachments.extend(files)
            self.batch_attachment_list.configure(text=f"已添加 {len(self.batch_attachments)} 个附件")

    def _clear_batch_attachments(self):
        self.batch_attachments.clear()
        self.batch_attachment_list.configure(text="")

    def _update_batch_progress(self, current, total, success_count, fail_count):
        progress = (current / total) * 100
        self.batch_send_btn.configure(
            text=f"发送中... {current}/{total} ({progress:.1f}%)"
        )

    def _send_batch_email(self):
        from_email = self.batch_fields["from"].get().strip()
        subject = self.batch_subject.get().strip()
        content = self.batch_content.get("1.0", TK_END).strip()
        content_type = self.batch_content_type.get()

        if not self.email_client.api_key:
            messagebox.showerror("错误", "请先配置 Resend API Key")
            return

        if not from_email:
            messagebox.showerror("错误", "请填写发件人")
            return

        if not self.batch_recipients:
            messagebox.showerror("错误", "请添加收件人")
            return

        if not subject:
            messagebox.showerror("错误", "请填写主题")
            return

        emails = []
        html_content = content if content_type == "html" else None
        text_content = content if content_type == "text" else None
        attachments = self.email_client.prepare_attachments(self.batch_attachments)

        for email in self.batch_recipients:
            emails.append({
                "from": from_email,
                "to": [email],
                "subject": subject,
                "html": html_content,
                "text": text_content,
                "attachments": attachments if attachments else None,
            })

        self.batch_send_btn.configure(state=ctk.DISABLED, text="发送中...")

        def send():
            success, message, data = self.email_client.send_batch_emails(emails, self._update_batch_progress)

            self.after(0, lambda: self._handle_send_result(success, message, None, self.batch_send_btn, tab="batch"))

        threading.Thread(target=send, daemon=True).start()