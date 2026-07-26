import os
import base64
from typing import List, Dict, Optional, Tuple
import resend
from resend.emails._emails import Emails
from resend.domains._domains import Domains
from logger import Logger


logger = Logger()


class EmailClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("RESEND_API_KEY")
        if self.api_key:
            resend.api_key = self.api_key

    def set_api_key(self, api_key: str):
        self.api_key = api_key
        resend.api_key = api_key

    def send_single_email(
        self,
        from_email: str,
        to_emails: List[str],
        subject: str,
        html_content: str = None,
        text_content: str = None,
        attachments: List[Dict] = None,
    ) -> Tuple[bool, str, Optional[str]]:
        try:
            payload = {
                "from": from_email,
                "to": to_emails,
                "subject": subject,
            }
            if html_content:
                payload["html"] = html_content
            if text_content:
                payload["text"] = text_content
            if attachments:
                payload["attachments"] = attachments

            logger.info(f"发送邮件: from={from_email}, to={to_emails}, subject={subject}")

            result = Emails().send(payload)

            if hasattr(result, "error") and result.error:
                error_msg = str(result.error)
                logger.error(f"邮件发送失败: {error_msg}")
                return False, error_msg, None

            logger.info(f"邮件发送成功: id={result.id}")
            return True, "邮件发送成功", result.id

        except Exception as e:
            error_msg = str(e)
            logger.exception(f"邮件发送异常: {error_msg}")
            return False, error_msg, None

    def send_batch_emails(
        self,
        emails: List[Dict],
        progress_callback=None,
    ) -> Tuple[bool, str, Optional[List[Dict]]]:
        try:
            results = []
            success_count = 0
            fail_count = 0
            total = len(emails)

            for i, email_data in enumerate(emails):
                try:
                    html_content = email_data.get("html")
                    text_content = email_data.get("text")
                    attachments = email_data.get("attachments")

                    success, msg, email_id = self.send_single_email(
                        from_email=email_data["from"],
                        to_emails=email_data["to"],
                        subject=email_data["subject"],
                        html_content=html_content,
                        text_content=text_content,
                        attachments=attachments,
                    )

                    if success:
                        success_count += 1
                        results.append({"email": email_data["to"][0], "id": email_id, "status": "success"})
                    else:
                        fail_count += 1
                        results.append({"email": email_data["to"][0], "error": msg, "status": "failed"})

                    if progress_callback:
                        progress_callback(i + 1, total, success_count, fail_count)

                except Exception as e:
                    fail_count += 1
                    results.append({"email": email_data["to"][0], "error": str(e), "status": "failed"})

                    if progress_callback:
                        progress_callback(i + 1, total, success_count, fail_count)

            if fail_count == 0:
                return True, f"批量发送成功，共发送 {success_count} 封邮件", results
            elif success_count == 0:
                return False, f"批量发送失败，全部 {total} 封邮件发送失败", results
            else:
                return True, f"批量发送完成，成功 {success_count} 封，失败 {fail_count} 封", results

        except Exception as e:
            return False, str(e), None

    @staticmethod
    def prepare_attachments(file_paths: List[str]) -> List[Dict]:
        attachments = []
        for file_path in file_paths:
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "rb") as f:
                        content = f.read()
                    encoded_content = base64.b64encode(content).decode("utf-8")
                    filename = os.path.basename(file_path)
                    attachments.append({
                        "content": encoded_content,
                        "filename": filename,
                    })
                except Exception as e:
                    print(f"无法读取附件 {file_path}: {e}")
        return attachments

    def validate_api_key(self) -> Tuple[bool, str]:
        if not self.api_key:
            return False, "API Key 不能为空"
        try:
            result = Domains().list()
            if result is not None:
                return True, "API Key 有效"
            return False, "API Key 验证失败"
        except Exception as e:
            error_msg = str(e)
            if "API key is invalid" in error_msg:
                return False, "API Key 无效，请检查密钥是否正确"
            if "restricted to only send emails" in error_msg:
                return True, "API Key 有效（仅邮件发送权限）"
            return False, f"验证失败: {error_msg}"