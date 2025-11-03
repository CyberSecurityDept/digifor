# Chat Messages Field Mapping Guide

## Struktur Tabel `chat_messages`

```python
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    platform = Column(String, nullable=False)
    message_text = Column(Text, nullable=True)
    from_name = Column(String, nullable=True)          # Nama pengirim
    sender_number = Column(String, nullable=True)      # Nomor/ID pengirim
    to_name = Column(String, nullable=True)           # Nama penerima
    recipient_number = Column(String, nullable=True)  # Nomor/ID penerima
    timestamp = Column(String, nullable=True)
    thread_id = Column(String, nullable=True)
    chat_id = Column(String, nullable=True)
    message_id = Column(String, nullable=True)
    message_type = Column(String, nullable=True)
    direction = Column(String, nullable=True)
    source_tool = Column(String, nullable=True)
    sheet_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)
```

## Mapping dari Excel ke Database

### Untuk Oxygen Forensics - Multi-platform (Messages Sheet)

| Excel Column | Database Field | Contoh Nilai | Catatan |
|--------------|---------------|--------------|---------|
| `Source` | `platform` | "Telegram", "WhatsApp", "Instagram" | Harus mengandung nama platform |
| `Text` atau `Message` | `message_text` | "Hai", "Hello world" | Wajib ada |
| `From` | `from_name` | "John Doe" atau "John <123>" | Parsing format: `Name <ID>` |
| `From` | `sender_number` | "123", "6281234567890" | Extract dari `<ID>` di kolom From |
| `To` | `to_name` | "Jane Doe" atau "Jane <456>" | Parsing format: `Name <ID>` |
| `To` | `recipient_number` | "456", "6289876543210" | Extract dari `<ID>` di kolom To |
| `Time stamp (UTC 0)` | `timestamp` | "2020-10-22 08:55:14" | Format timestamp |
| `Thread ID` atau `Chat ID` | `thread_id` | "ee50dd47..." | ID thread/chat |
| `Details` → Chat ID | `chat_id` | "1313943896" | Extract dari kolom Details |
| `Details` → Message ID | `message_id` | "12345" | Extract dari kolom Details |
| `Message Type` | `message_type` | "text", "image", "video" | Default: "text" |
| `Direction` | `direction` | "Incoming", "Outgoing" | Arah pesan |
| - | `source_tool` | "oxygen" | Hardcoded untuk Oxygen |
| - | `sheet_name` | "Messages " | Nama sheet yang di-parse |
| - | `file_id` | 1 | ID file dari database |

## Format Data yang Benar

### 1. Data Dictionary untuk Insert

```python
message_data = {
    "file_id": file_id,              # int - REQUIRED
    "platform": "telegram",          # str - REQUIRED (lowercase)
    "message_text": "Hai",           # str - REQUIRED
    "from_name": "John Doe",         # str - OPTIONAL
    "sender_number": "123456789",    # str - OPTIONAL
    "to_name": "Jane Doe",           # str - OPTIONAL
    "recipient_number": "987654321", # str - OPTIONAL
    "timestamp": "2020-10-22 08:55:14", # str - OPTIONAL
    "thread_id": "ee50dd47...",      # str - OPTIONAL
    "chat_id": "1313943896",         # str - OPTIONAL
    "message_id": "telegram_1_12345", # str - REQUIRED (unique)
    "message_type": "text",          # str - OPTIONAL (default: "text")
    "direction": "Outgoing",         # str - OPTIONAL
    "source_tool": "oxygen",         # str - OPTIONAL
    "sheet_name": "Messages "       # str - OPTIONAL
}
```

### 2. Cara Insert ke Database

```python
from app.db.session import SessionLocal
from app.analytics.device_management.models import ChatMessage

db = SessionLocal()
try:
    # Check duplicate
    existing = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.file_id == message_data["file_id"],
            ChatMessage.platform == message_data["platform"],
            ChatMessage.message_id == message_data["message_id"]
        )
        .first()
    )
    
    if not existing:
        # Insert new record
        chat_message = ChatMessage(**message_data)
        db.add(chat_message)
        db.commit()
        print(f"✅ Inserted message: {message_data['message_id']}")
    else:
        print(f"⚠️  Duplicate message skipped: {message_data['message_id']}")
        
except Exception as e:
    db.rollback()
    print(f"❌ Error inserting: {e}")
    raise
finally:
    db.close()
```

## Parsing Logic untuk Kolom From/To

### Format yang Didukung

1. **Format: `Name <ID>`**
   - Contoh: `"John Doe <123456789>"`
   - Parsing:
     - `from_name` = "John Doe"
     - `sender_number` = "123456789"

2. **Format: `Name` saja**
   - Contoh: `"John Doe"`
   - Parsing:
     - `from_name` = "John Doe"
     - `sender_number` = None

3. **Format: `<ID>` saja**
   - Contoh: `"<123456789>"`
   - Parsing:
     - `from_name` = None
     - `sender_number` = "123456789"

### Code Parsing

```python
import re

def parse_from_to_column(column_value):
    """Parse From/To column yang mungkin berformat 'Name <ID>'"""
    if not column_value:
        return None, None
    
    name_match = re.search(r'^([^<]+)', column_value)
    id_match = re.search(r'<([^>]+)>', column_value)
    
    name = name_match.group(1).strip() if name_match else None
    id_value = id_match.group(1).strip() if id_match else None
    
    # Handle WhatsApp format khusus
    if id_value and '@s.whatsapp.net' in id_value:
        phone_match = re.search(r'(\d+)', id_value)
        id_value = phone_match.group(1) if phone_match else id_value
    
    return name, id_value

# Usage
from_name, sender_id = parse_from_to_column(row['From'])
to_name, recipient_id = parse_from_to_column(row['To'])
```

## Ekstraksi Data dari Kolom Details

Kolom `Details` di Oxygen Forensics sering berisi informasi tambahan yang perlu di-extract:

```python
def extract_from_details(details_text):
    """Extract informasi dari kolom Details"""
    if not details_text:
        return {}
    
    result = {}
    
    # Message ID
    msg_id_match = re.search(r'Message ID:\s*([^\s\n\r]+)', details_text, re.IGNORECASE)
    if msg_id_match:
        result['message_id'] = msg_id_match.group(1).strip()
    
    # Chat ID
    chat_id_match = re.search(r'Chat ID:\s*([^\s\n\r]+)', details_text, re.IGNORECASE)
    if chat_id_match:
        result['chat_id'] = chat_id_match.group(1).strip()
    
    # Remote party phone number
    phone_match = re.search(r'Remote party phone number:\s*([^\s\n\r]+)', details_text, re.IGNORECASE)
    if phone_match:
        result['recipient_number'] = phone_match.group(1).strip()
    
    # Remote party ID
    id_match = re.search(r'Remote party ID:\s*([^\s\n\r]+)', details_text, re.IGNORECASE)
    if id_match:
        result['recipient_number'] = id_match.group(1).strip()
    
    # Remote party name
    name_match = re.search(r'Remote party:\s*([^\n\r]+)', details_text, re.IGNORECASE)
    if name_match:
        result['to_name'] = name_match.group(1).strip()
    
    return result
```

## Masalah yang Sering Terjadi

### 1. `from_name` = None padahal ada data di Excel

**Penyebab:**
- Format kolom `From` tidak sesuai dengan yang diharapkan
- Parsing regex tidak match dengan format sebenarnya
- Kolom `From` kosong atau berisi "N/A"

**Solusi:**
- Periksa format sebenarnya di Excel
- Update parsing logic jika format berbeda
- Gunakan fallback ke nilai mentah jika parsing gagal

### 2. Duplicate Message ID

**Penyebab:**
- Message ID tidak unik
- Generated message ID menggunakan index yang tidak konsisten

**Solusi:**
- Gunakan Message ID dari kolom Details jika ada
- Jika tidak ada, generate dengan format: `{platform}_{file_id}_{unique_id}`
- Pastikan unique_id benar-benar unik (misalnya dari Details atau kombinasi timestamp+row)

### 3. Platform tidak terdeteksi

**Penyebab:**
- Kolom `Source` tidak terdeteksi
- Nilai Source tidak mengandung keyword platform

**Solusi:**
- Pastikan kolom Source terdeteksi dengan benar
- Case-insensitive matching: `'telegram' in source.lower()`
- Tambahkan logging untuk debug

## Contoh Insert Manual

```python
from app.db.session import SessionLocal
from app.analytics.device_management.models import ChatMessage

def insert_telegram_message_example():
    db = SessionLocal()
    try:
        message_data = {
            "file_id": 1,
            "platform": "telegram",
            "message_text": "Hello, this is a test message",
            "from_name": "John Doe",
            "sender_number": "123456789",
            "to_name": "Jane Doe",
            "recipient_number": "987654321",
            "timestamp": "2020-10-22 08:55:14",
            "thread_id": "ee50dd47e47911e29d245b9711bed3ed",
            "chat_id": "1313943896",
            "message_id": "telegram_1_test_001",
            "message_type": "text",
            "direction": "Outgoing",
            "source_tool": "oxygen",
            "sheet_name": "Messages "
        }
        
        # Check duplicate
        existing = db.query(ChatMessage).filter(
            ChatMessage.file_id == message_data["file_id"],
            ChatMessage.platform == message_data["platform"],
            ChatMessage.message_id == message_data["message_id"]
        ).first()
        
        if existing:
            print("Message already exists")
            return existing.id
        
        # Insert
        chat_message = ChatMessage(**message_data)
        db.add(chat_message)
        db.commit()
        db.refresh(chat_message)
        
        print(f"✅ Inserted message with ID: {chat_message.id}")
        return chat_message.id
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()
```

## Validasi Sebelum Insert

```python
def validate_message_data(message_data):
    """Validate message data before inserting"""
    errors = []
    
    # Required fields
    if not message_data.get("file_id"):
        errors.append("file_id is required")
    
    if not message_data.get("platform"):
        errors.append("platform is required")
    
    if not message_data.get("message_text"):
        errors.append("message_text is required")
    
    if not message_data.get("message_id"):
        errors.append("message_id is required")
    
    # Platform validation
    valid_platforms = ["telegram", "whatsapp", "instagram", "facebook", "x", "tiktok"]
    if message_data.get("platform") not in valid_platforms:
        errors.append(f"platform must be one of: {valid_platforms}")
    
    if errors:
        raise ValueError(f"Validation errors: {', '.join(errors)}")
    
    return True
```

