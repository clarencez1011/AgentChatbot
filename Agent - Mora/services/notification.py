import os
import base64
import threading
import asyncio
from email.mime.text import MIMEText
from config.settings import Config  # 👈 修正引用

# 尝试导入 logger，如果没有定义则使用 print 代替，防止报错
try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger("Notification")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    logger.addHandler(handler)

# Google 官方库
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

class NotificationService:
    def __init__(self):
        self.receiver = Config.ADMIN_EMAIL
        self.scopes = ['https://www.googleapis.com/auth/gmail.send']
        self.creds = None
        self.service = None
        
        # 加载凭据
        # 使用 os.getcwd() 确保路径正确
        self.token_path = os.path.join(os.getcwd(), 'token.json')
        self._load_credentials()

    def _load_credentials(self):
        """加载 token.json"""
        if os.path.exists(self.token_path):
            self.creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)
        else:
            print(f"⚠️ [Notification] 未找到 {self.token_path}，无法使用 Gmail API。")

    def _get_service(self):
        """获取 Gmail 服务实例 (带自动刷新)"""
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    logger.error(f"gmail_refresh_failed: {str(e)}")
                    return None
            else:
                return None
        
        if not self.service:
            self.service = build('gmail', 'v1', credentials=self.creds)
        
        return self.service

    def _send_sync(self, subject: str, body: str):
        """
        底层的同步发送逻辑
        """
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

            # 3. 发送
            service.users().messages().send(userId='me', body=body).execute()
            
            # 使用 getattr 防止 logger 没有 info 方法
            if hasattr(logger, "info"):
                logger.info(f"email_sent_api: {subject}")
            else:
                print(f"📧 [Mail Sent] {subject}")

        except Exception as e:
            if hasattr(logger, "error"):
                logger.error(f"email_failed_api: {str(e)}")
            else:
                print(f"❌ [Mail Fail] {str(e)}")

    def send_alert(self, module_name: str, error_msg: str, detail: str = ""):
        """
        🚀 [通用方法] 推荐使用这个
        使用线程异步发送，非阻塞。既可以在 async 函数用，也可以在 sync 函数用。
        """
        subject = f"{module_name} Critical Failure"
        body = f"""
尊敬的管理员：
Mars Agent 触发了自动降级保护 (Via Official Gmail API).

📍 故障模块: {module_name}
❌ 错误信息: {error_msg}
📝 上下文:
{detail}
        """
        # Fire-and-forget: 开个线程去发，主程序继续跑
        t = threading.Thread(target=self._send_sync, args=(subject, body))
        t.start()

    # 保留你原本的 async 方法，以防旧代码需要
    async def send_alert_async(self, module_name: str, error_msg: str, detail: str = ""):
        """
        如果你处于 async 上下文中，也可以用这个
        """
        self.send_alert(module_name, error_msg, detail)

notification_service = NotificationService()