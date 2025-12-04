import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.analytics.device_management.models import ChatMessage
import warnings, traceback, re


class ChatMessagesParser:
    
    def __init__(self, db: Session):
        self.db = db
    
    def _is_na(self, value: Any) -> bool:

        if value is None:
            return True
        if isinstance(value, (pd.Series, pd.DataFrame)):
            if value.empty:
                return True
            na_result = value.isna().all()
            return bool(na_result) if isinstance(na_result, (pd.Series, pd.DataFrame)) else bool(na_result)
        try:
            na_result = pd.isna(value)
            if isinstance(na_result, (pd.Series, pd.DataFrame)):
                return bool(na_result.all())
            return bool(na_result)
        except (TypeError, ValueError):
            return False
    
    def _not_na(self, value: Any) -> bool:
        return not self._is_na(value)
    
    def _clean(self, text: Any) -> Optional[str]:
        if text is None:
            return None
        if self._is_na(text):
            return None
        text_str = str(text).strip()
        if text_str.lower() in ['nan', 'none', 'null', '', 'n/a']:
            return None
        return text_str
    
    def _generate_message_id(self, platform: str, row: pd.Series, file_id: int, index: int) -> str:
        message_id_fields = ['Message ID', 'Item ID', 'Record', 'message_id', 'id']
        for field in message_id_fields:
            if field in row.index and self._not_na(row.get(field)):
                msg_id = str(row.get(field)).strip()
                if msg_id and msg_id.lower() not in ['nan', 'none', '']:
                    return f"{platform}_{file_id}_{msg_id}"
        
        timestamp = self._clean(row.get('timestamp', '')) or self._clean(row.get('Timestamp', ''))
        if timestamp:
            return f"{platform}_{file_id}_{timestamp}_{index}"
        
        return f"{platform}_{file_id}_{index}"
    
    def _parse_tiktok_messages(self, file_path: str, sheet_name: str, file_id: int, source_tool: str, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
            
            if not df.empty:
                first_col = df.iloc[:, 0].astype(str)
                header_row = None
                for idx, val in enumerate(first_col):
                    if self._not_na(val) and any(keyword in str(val).lower() for keyword in ['sender', 'recipient', 'message', 'record']):
                        header_row = idx
                        break
                
                if header_row and header_row > 0:
                    df.columns = df.iloc[header_row]
                    df = df.iloc[header_row + 1:].reset_index(drop=True)
            
            for idx, row in df.iterrows():
                message_text = self._clean(row.get('Message', ''))
                if not message_text:
                    continue
                
                if str(message_text).lower() in ['message', 'record', 'sender', 'nan']:
                    continue
                
                sender = self._clean(row.get('Sender', ''))
                recipient = self._clean(row.get('Recipient', ''))
                timestamp = self._clean(row.get('Created Date/Time - UTC+00:00 (dd/MM/yyyy)', '')) or \
                           self._clean(row.get('Timestamp', '')) or \
                           self._clean(row.get('Date/Time', ''))
                thread_id = self._clean(row.get('_ThreadID', '')) or \
                           self._clean(row.get('Thread ID', '')) or \
                           self._clean(row.get('Chat ID', ''))
                message_type = self._clean(row.get('Message Type', '')) or \
                             self._clean(row.get('Type', '')) or 'text'
                
                chat_id = self._clean(row.get('Chat ID', ''))
                
                message_data = {
                    "file_id": file_id,
                    "platform": "tiktok",
                    "message_text": message_text,
                    "from_name": sender,
                    "sender_number": self._clean(row.get('Sender ID', '')),
                    "to_name": recipient,
                    "recipient_number": self._clean(row.get('Recipient ID', '')),
                    "timestamp": timestamp,
                    "thread_id": thread_id,
                    "chat_id": chat_id,
                    "message_id": self._generate_message_id("tiktok", row, file_id, idx),
                    "message_type": message_type,
                    "direction": self._clean(row.get('Direction', '')),
                    "source_tool": source_tool,
                    "sheet_name": sheet_name
                }
                
                results.append(message_data)
                
        except Exception as e:
            print(f"Error parsing TikTok messages from {sheet_name}: {e}")
            
            traceback.print_exc()
        
        return results
    
    def _parse_instagram_messages(self, file_path: str, sheet_name: str, file_id: int, source_tool: str, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
            
            if not df.empty:
                first_col = df.iloc[:, 0].astype(str)
                header_row = None
                for idx, val in enumerate(first_col):
                    if self._not_na(val) and any(keyword in str(val).lower() for keyword in ['sender', 'recipient', 'message', 'record']):
                        header_row = idx
                        break
                
                if header_row and header_row > 0:
                    df.columns = df.iloc[header_row]
                    df = df.iloc[header_row + 1:].reset_index(drop=True)
            
            for idx, row in df.iterrows():
                message_text = self._clean(row.get('Message', ''))
                if not message_text:
                    continue
                
                if str(message_text).lower() in ['message', 'record', 'sender', 'nan']:
                    continue
                
                sender = self._clean(row.get('Sender', ''))
                recipient = self._clean(row.get('Recipient', ''))
                timestamp = self._clean(row.get('Message Date/Time - UTC+00:00 (dd/MM/yyyy)', '')) or \
                           self._clean(row.get('Timestamp', '')) or \
                           self._clean(row.get('Date/Time', ''))
                thread_id = self._clean(row.get('_ThreadID', '')) or \
                           self._clean(row.get('Thread ID', '')) or \
                           self._clean(row.get('Chat ID', ''))
                chat_id = self._clean(row.get('Chat ID', ''))
                message_type = self._clean(row.get('Type', '')) or 'text'
                direction = self._clean(row.get('Direction', ''))
                
                message_id = self._clean(row.get('Item ID', '')) or \
                            self._clean(row.get('Message ID', '')) or \
                            self._clean(row.get('Record', ''))
                
                message_data = {
                    "file_id": file_id,
                    "platform": "instagram",
                    "message_text": message_text,
                    "from_name": sender,
                    "sender_number": self._clean(row.get('Sender ID', '')),
                    "to_name": recipient,
                    "recipient_number": self._clean(row.get('Recipient ID', '')),
                    "timestamp": timestamp,
                    "thread_id": thread_id,
                    "chat_id": chat_id,
                    "message_id": self._generate_message_id("instagram", row, file_id, idx) if not message_id else f"instagram_{file_id}_{message_id}",
                    "message_type": message_type,
                    "direction": direction,
                    "source_tool": source_tool,
                    "sheet_name": sheet_name
                }
                
                results.append(message_data)
                
        except Exception as e:
            print(f"Error parsing Instagram messages from {sheet_name}: {e}")
            
            traceback.print_exc()
        
        return results
    
    def _parse_whatsapp_messages(self, file_path: str, sheet_name: str, file_id: int, source_tool: str, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
            
            if not df.empty:
                first_col = df.iloc[:, 0].astype(str)
                header_row = None
                for idx, val in enumerate(first_col):
                    if self._not_na(val) and any(keyword in str(val).lower() for keyword in ['sender', 'from', 'message', 'record', 'timestamp']):
                        header_row = idx
                        break
                
                if header_row and header_row > 0:
                    df.columns = df.iloc[header_row]
                    df = df.iloc[header_row + 1:].reset_index(drop=True)
            
            for idx, row in df.iterrows():
                message_text = self._clean(row.get('Message', '')) or \
                              self._clean(row.get('Text', '')) or \
                              self._clean(row.get('Content', ''))
                if not message_text:
                    continue
                
                msg_lower = str(message_text).lower()
                if msg_lower in ['message', 'record', 'sender', 'nan', 'text', 'content'] or \
                   '\\chats\\' in msg_lower or '\\calls\\' in msg_lower:
                    continue
                
                sender = self._clean(row.get('Sender', '')) or \
                        self._clean(row.get('From', '')) or \
                        self._clean(row.get('Sender Name', ''))
                
                sender_id = None
                if sender and '@s.whatsapp.net' in sender:
                    phone_match = re.search(r'(\+?[0-9]{10,15})', sender)
                    if phone_match:
                        sender_id = phone_match.group(1)
                        sender = sender_id
                
                recipient = self._clean(row.get('Recipient', '')) or \
                           self._clean(row.get('To', '')) or \
                           self._clean(row.get('Recipient Name', ''))
                
                if recipient and '@s.whatsapp.net' in recipient:
                    phone_match = re.search(r'(\+?[0-9]{10,15})', recipient)
                    if phone_match:
                        recipient = phone_match.group(1)
                
                timestamp = self._clean(row.get('Timestamp', '')) or \
                           self._clean(row.get('Message Date/Time - UTC+00:00 (dd/MM/yyyy)', '')) or \
                           self._clean(row.get('Date/Time', '')) or \
                           self._clean(row.get('Created Date/Time - UTC+00:00 (dd/MM/yyyy)', ''))
                
                thread_id = self._clean(row.get('Chat ID', '')) or \
                           self._clean(row.get('_ThreadID', '')) or \
                           self._clean(row.get('Thread ID', '')) or \
                           self._clean(row.get('JID', ''))
                
                direction = self._clean(row.get('Direction', '')) or \
                           self._clean(row.get('Type', ''))
                
                message_type = self._clean(row.get('Message Type', '')) or \
                              self._clean(row.get('Type', '')) or 'text'
                
                message_id = self._clean(row.get('Message ID', '')) or \
                            self._clean(row.get('Item ID', '')) or \
                            self._clean(row.get('Record', ''))
                
                chat_id = self._clean(row.get('Chat ID', '')) or thread_id
                
                message_data = {
                    "file_id": file_id,
                    "platform": "whatsapp",
                    "message_text": message_text,
                    "from_name": sender,
                    "sender_number": sender_id or self._clean(row.get('Sender ID', '')),
                    "to_name": recipient,
                    "recipient_number": self._clean(row.get('Recipient ID', '')),
                    "timestamp": timestamp,
                    "thread_id": thread_id,
                    "chat_id": chat_id,
                    "message_id": self._generate_message_id("whatsapp", row, file_id, idx) if not message_id else f"whatsapp_{file_id}_{message_id}",
                    "message_type": message_type,
                    "direction": direction,
                    "source_tool": source_tool,
                    "sheet_name": sheet_name
                }
                
                results.append(message_data)
                
        except Exception as e:
            print(f"Error parsing WhatsApp messages from {sheet_name}: {e}")
            
            traceback.print_exc()
        
        return results
    
    def _parse_telegram_messages(self, file_path: str, sheet_name: str, file_id: int, source_tool: str, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
            
            if not df.empty:
                first_col = df.iloc[:, 0].astype(str)
                header_row = None
                for idx, val in enumerate(first_col):
                    if self._not_na(val) and any(keyword in str(val).lower() for keyword in ['sender', 'recipient', 'message', 'record']):
                        header_row = idx
                        break
                
                if header_row and header_row > 0:
                    df.columns = df.iloc[header_row]
                    df = df.iloc[header_row + 1:].reset_index(drop=True)
            
            for idx, row in df.iterrows():
                message_text = self._clean(row.get('Message', ''))
                if not message_text:
                    continue
                
                if str(message_text).lower() in ['message', 'record', 'sender', 'nan']:
                    continue
                
                sender_name = self._clean(row.get('Sender Name', '')) or \
                             self._clean(row.get('Sender', ''))
                sender_id = self._clean(row.get('Sender ID', ''))
                recipient_name = self._clean(row.get('Recipient Name', '')) or \
                               self._clean(row.get('Recipient', ''))
                recipient_id = self._clean(row.get('Recipient ID', ''))
                
                timestamp = self._clean(row.get('Message Sent Date/Time - UTC+00:00 (dd/MM/yyyy)', '')) or \
                           self._clean(row.get('Timestamp', '')) or \
                           self._clean(row.get('Date/Time', '')) or \
                           self._clean(row.get('Created Date/Time - UTC+00:00 (dd/MM/yyyy)', ''))
                
                thread_id = self._clean(row.get('_ThreadID', '')) or \
                           self._clean(row.get('Thread ID', ''))
                chat_id = self._clean(row.get('Chat ID', ''))
                
                message_type = self._clean(row.get('Type', '')) or 'text'
                direction = self._clean(row.get('Direction', ''))
                
                message_id = self._clean(row.get('Message ID', '')) or \
                            self._clean(row.get('Item ID', '')) or \
                            self._clean(row.get('Record', ''))
                
                message_data = {
                    "file_id": file_id,
                    "platform": "telegram",
                    "message_text": message_text,
                    "from_name": sender_name,
                    "sender_number": sender_id,
                    "to_name": recipient_name,
                    "recipient_number": recipient_id,
                    "timestamp": timestamp,
                    "thread_id": thread_id,
                    "chat_id": chat_id,
                    "message_id": self._generate_message_id("telegram", row, file_id, idx) if not message_id else f"telegram_{file_id}_{message_id}",
                    "message_type": message_type,
                    "direction": direction,
                    "source_tool": source_tool,
                    "sheet_name": sheet_name
                }
                
                results.append(message_data)
                
        except Exception as e:
            print(f"Error parsing Telegram messages from {sheet_name}: {e}")
            
            traceback.print_exc()
        
        return results
    
    def _parse_x_messages(self, file_path: str, sheet_name: str, file_id: int, source_tool: str, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
            
            if not df.empty:
                first_col = df.iloc[:, 0].astype(str)
                header_row = None
                for idx, val in enumerate(first_col):
                    if self._not_na(val) and any(keyword in str(val).lower() for keyword in ['sender', 'recipient', 'text', 'record']):
                        header_row = idx
                        break
                
                if header_row and header_row > 0:
                    df.columns = df.iloc[header_row]
                    df = df.iloc[header_row + 1:].reset_index(drop=True)
            
            for idx, row in df.iterrows():
                message_text = self._clean(row.get('Text', '')) or \
                              self._clean(row.get('Message', ''))
                if not message_text:
                    continue
                
                if str(message_text).lower() in ['text', 'message', 'record', 'sender', 'nan']:
                    continue
                
                sender_name = self._clean(row.get('Sender Name', '')) or \
                             self._clean(row.get('Sender Screen Name', '')) or \
                             self._clean(row.get('Sender', ''))
                sender_id = self._clean(row.get('Sender ID', ''))
                
                recipient_name = self._clean(row.get('Recipient Name(s)', '')) or \
                               self._clean(row.get('Recipient Screen Name(s)', '')) or \
                               self._clean(row.get('Recipient', ''))
                recipient_id = self._clean(row.get('Recipient ID(s)', ''))
                
                timestamp = self._clean(row.get('Sent/Received Date/Time - UTC+00:00 (dd/MM/yyyy)', '')) or \
                           self._clean(row.get('Timestamp', '')) or \
                           self._clean(row.get('Date/Time', ''))
                
                thread_id = self._clean(row.get('_ThreadID', '')) or \
                           self._clean(row.get('Thread ID', ''))
                
                direction = self._clean(row.get('Direction', ''))
                
                message_id = self._clean(row.get('Item ID', '')) or \
                            self._clean(row.get('Message ID', '')) or \
                            self._clean(row.get('Record', ''))
                
                chat_id = self._clean(row.get('Chat ID', '')) or thread_id
                
                message_data = {
                    "file_id": file_id,
                    "platform": "x",
                    "message_text": message_text,
                    "from_name": sender_name,
                    "sender_number": sender_id,
                    "to_name": recipient_name,
                    "recipient_number": recipient_id,
                    "timestamp": timestamp,
                    "thread_id": thread_id,
                    "chat_id": chat_id,
                    "message_id": self._generate_message_id("x", row, file_id, idx) if not message_id else f"x_{file_id}_{message_id}",
                    "message_type": "text",
                    "direction": direction,
                    "source_tool": source_tool,
                    "sheet_name": sheet_name
                }
                
                results.append(message_data)
                
        except Exception as e:
            print(f"Error parsing X messages from {sheet_name}: {e}")
            
            traceback.print_exc()
        
        return results
    
    def _parse_facebook_messages(self, file_path: str, sheet_name: str, file_id: int, source_tool: str, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
            
            if not df.empty:
                first_col = df.iloc[:, 0].astype(str)
                header_row = None
                for idx, val in enumerate(first_col):
                    if self._not_na(val) and any(keyword in str(val).lower() for keyword in ['sender', 'recipient', 'message', 'record', 'content']):
                        header_row = idx
                        break
                
                if header_row and header_row > 0:
                    df.columns = df.iloc[header_row]
                    df = df.iloc[header_row + 1:].reset_index(drop=True)
            
            for idx, row in df.iterrows():
                message_text = self._clean(row.get('Message', '')) or \
                          self._clean(row.get('Content', '')) or \
                          self._clean(row.get('Text', ''))
                if not message_text:
                    continue
                
                msg_lower = str(message_text).lower()
                if msg_lower in ['message', 'record', 'sender', 'nan', 'content', 'text']:
                    continue
                
                sender_name = self._clean(row.get('Sender Name', '')) or \
                             self._clean(row.get('Sender', '')) or \
                             self._clean(row.get('From', ''))
                sender_id = self._clean(row.get('Sender ID', ''))
                
                recipient_name = self._clean(row.get('Recipient Name', '')) or \
                               self._clean(row.get('Recipient', '')) or \
                               self._clean(row.get('To', ''))
                recipient_id = self._clean(row.get('Recipient ID', ''))
                
                timestamp = self._clean(row.get('Timestamp', '')) or \
                           self._clean(row.get('Message Date/Time - UTC+00:00 (dd/MM/yyyy)', '')) or \
                           self._clean(row.get('Date/Time', '')) or \
                           self._clean(row.get('Sent Date/Time - UTC+00:00 (dd/MM/yyyy)', '')) or \
                           self._clean(row.get('Created Date/Time - UTC+00:00 (dd/MM/yyyy)', ''))
                
                thread_id = self._clean(row.get('Thread ID', '')) or \
                           self._clean(row.get('_ThreadID', '')) or \
                           self._clean(row.get('Chat ID', '')) or \
                           self._clean(row.get('Conversation ID', ''))
                
                message_type = self._clean(row.get('Message Type', '')) or \
                              self._clean(row.get('Type', '')) or 'text'
                direction = self._clean(row.get('Direction', ''))
                
                message_id = self._clean(row.get('Message ID', '')) or \
                            self._clean(row.get('Item ID', '')) or \
                            self._clean(row.get('Record', ''))
                
                chat_id = self._clean(row.get('Chat ID', '')) or \
                          self._clean(row.get('Conversation ID', '')) or \
                          thread_id
                
                message_data = {
                    "file_id": file_id,
                    "platform": "facebook",
                    "message_text": message_text,
                    "from_name": sender_name,
                    "sender_number": sender_id,
                    "to_name": recipient_name,
                    "recipient_number": recipient_id,
                    "timestamp": timestamp,
                    "thread_id": thread_id,
                    "chat_id": chat_id,
                    "message_id": self._generate_message_id("facebook", row, file_id, idx) if not message_id else f"facebook_{file_id}_{message_id}",
                    "message_type": message_type,
                    "direction": direction,
                    "source_tool": source_tool,
                    "sheet_name": sheet_name
                }
                
                results.append(message_data)
                
        except Exception as e:
            print(f"Error parsing Facebook messages from {sheet_name}: {e}")
            
            traceback.print_exc()
        
        return results

