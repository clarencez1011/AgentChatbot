import os
import base64
import asyncio
from email.mime.text import MIMEText
from config import settings
from logger import logger

# Google 官方库
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

class NotificationService:
    def __init__(self):
        self.receiver = settings.ADMIN_EMAIL
        self.scopes = ['https://www.googleapis.com/auth/gmail.send']
        self.creds = None
        self.service = None
        
        # 加载凭据
        self._load_credentials()

    def _load_credentials(self):
        """加载 token.json"""
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', self.scopes)
        else:
            print("⚠️ 未找到 token.json，无法使用 Gmail API。请先运行 setup_gmail.py")

    def _get_service(self):
        """获取 Gmail 服务实例 (带自动刷新)"""
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    logger.error("gmail_refresh_failed", error=str(e))
                    return None
            else:
                return None
        
        if not self.service:
            self.service = build('gmail', 'v1', credentials=self.creds)
        
        return self.service

    def _send_sync(self, subject: str, body: str):
        service = self._get_service()
        if not service:
            return

        try:
            # 1. 构造邮件
            message = MIMEText(body)
            message['to'] = self.receiver
            message['subject'] = f"🚨 [Alert] {subject}"
            
            # 2. 编码 (Gmail API 要求 base64url 编码)
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            body = {'raw': raw_message}

            # 3. 发送 (直接走 HTTPS，稳！)
            service.users().messages().send(userId='me', body=body).execute()
            
            logger.info("email_sent_api", subject=subject, method="Gmail_REST_API")

        except Exception as e:
            logger.error("email_failed_api", error=str(e))

    async def send_alert_async(self, module_name: str, error_msg: str, detail: str = ""):
        subject = f"{module_name} Critical Failure"
        body = f"""
尊敬的管理员：
Mars Agent 触发了自动降级保护 (Via Official Gmail API).

📍 故障模块: {module_name}
❌ 错误信息: {error_msg}
📝 上下文:
{detail}
        """
        asyncio.create_task(asyncio.to_thread(self._send_sync, subject, body))

notification_service = NotificationService()