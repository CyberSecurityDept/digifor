# Panduan Insert Chat Messages ke Database

## ✅ Status Saat Ini

**Kesimpulan**: Parsing dan insert Telegram **SUDAH BENAR**. 

Data yang tersimpan di database:
- ✅ `file_id`: Terisi
- ✅ `platform`: "telegram" 
- ✅ `message_text`: Terisi
- ✅ `message_id`: Terisi (dari Details atau generated)
- ✅ `to_name`: Terisi (dari Details → Remote party)
- ✅ `recipient_number`: Terisi (dari Details → Remote party ID)
- ✅ `timestamp`: Terisi
- ✅ `thread_id`: Terisi
- ✅ `chat_id`: Terisi (dari Details → Chat ID)
- ⚠️ `from_name`: Kosong (karena kolom From di Excel kosong - ini NORMAL untuk Telegram)
- ⚠️ `sender_number`: Kosong (karena kolom From di Excel kosong - ini NORMAL untuk Telegram)

**Catatan**: `from_name` kosong adalah **NORMAL** karena:
1. Kolom `From` di Excel untuk Telegram rows = `nan` (kosong)
2. Data pengirim tidak tersedia di kolom `Details` untuk pesan Outgoing
3. Untuk pesan Incoming, `to_name` dan `recipient_number` sudah terisi dari `Remote party`

## 📋 Format Dictionary untuk Insert

```python
message_data = {
    # REQUIRED FIELDS
    "file_id": 1,                          # int - ID file dari tabel files
    "platform": "telegram",               # str - lowercase: telegram, whatsapp, instagram, dll
    "message_text": "Hai",                # str - Teks pesan (REQUIRED, tidak boleh kosong)
    "message_id": "telegram_1_12345",     # str - Unique message ID (REQUIRED)
    
    # OPTIONAL BUT IMPORTANT
    "from_name": "John Doe",              # str - Nama pengirim (bisa None jika tidak ada)
    "sender_number": "123456789",         # str - ID/nomor pengirim (bisa None)
    "to_name": "Jane Doe",                # str - Nama penerima (dari Remote party)
    "recipient_number": "987654321",      # str - ID/nomor penerima (dari Remote party ID)
    "timestamp": "2020-10-22 08:55:14",  # str - Timestamp pesan
    "thread_id": "ee50dd47...",          # str - Thread/chat identifier
    "chat_id": "1313943896",              # str - Chat ID (dari Details)
    "message_type": "text",               # str - Type: text, image, video, dll
    "direction": "Outgoing",              # str - Incoming atau Outgoing
    "source_tool": "oxygen",              # str - Tool source: oxygen, axiom, cellebrite
    "sheet_name": "Messages "             # str - Nama sheet yang di-parse
}
```

## 🔧 Cara Insert Manual

### Method 1: Menggunakan SQLAlchemy ORM (Recommended)

```python
from app.db.session import SessionLocal
from app.analytics.device_management.models import ChatMessage

def insert_chat_message(message_data: dict):
    """
    Insert chat message ke database dengan duplicate checking
    
    Args:
        message_data: Dictionary dengan field sesuai struktur ChatMessage
    """
    db = SessionLocal()
    try:
        # Validasi required fields
        required_fields = ['file_id', 'platform', 'message_text', 'message_id']
        for field in required_fields:
            if not message_data.get(field):
                raise ValueError(f"Required field '{field}' is missing")
        
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
        
        if existing:
            print(f"⚠️  Duplicate message skipped: {message_data['message_id']}")
            return existing.id
        
        # Create new ChatMessage object
        chat_message = ChatMessage(**message_data)
        db.add(chat_message)
        db.commit()
        db.refresh(chat_message)
        
        print(f"✅ Inserted message ID: {chat_message.id}, message_id: {message_data['message_id']}")
        return chat_message.id
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error inserting message: {e}")
        raise
    finally:
        db.close()

# Contoh penggunaan
message_data = {
    "file_id": 1,
    "platform": "telegram",
    "message_text": "Hello, this is a test",
    "message_id": "telegram_1_test_001",
    "to_name": "Jane Doe",
    "recipient_number": "987654321",
    "timestamp": "2020-10-22 08:55:14",
    "thread_id": "ee50dd47e47911e29d245b9711bed3ed",
    "chat_id": "1313943896",
    "message_type": "text",
    "direction": "Outgoing",
    "source_tool": "oxygen",
    "sheet_name": "Messages "
}

insert_chat_message(message_data)
```

### Method 2: Batch Insert

```python
from app.db.session import SessionLocal
from app.analytics.device_management.models import ChatMessage

def batch_insert_messages(messages_list: list):
    """
    Insert multiple messages sekaligus (lebih efisien)
    
    Args:
        messages_list: List of dictionaries, masing-masing adalah message_data
    """
    db = SessionLocal()
    try:
        saved_count = 0
        skipped_count = 0
        
        for msg_data in messages_list:
            # Validasi
            if not all(msg_data.get(f) for f in ['file_id', 'platform', 'message_text', 'message_id']):
                print(f"⚠️  Skipping invalid message: missing required fields")
                skipped_count += 1
                continue
            
            # Check duplicate
            existing = (
                db.query(ChatMessage)
                .filter(
                    ChatMessage.file_id == msg_data["file_id"],
                    ChatMessage.platform == msg_data["platform"],
                    ChatMessage.message_id == msg_data["message_id"]
                )
                .first()
            )
            
            if not existing:
                chat_message = ChatMessage(**msg_data)
                db.add(chat_message)
                saved_count += 1
            else:
                skipped_count += 1
        
        db.commit()
        print(f"✅ Inserted {saved_count} messages, skipped {skipped_count} duplicates")
        return saved_count
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error batch inserting: {e}")
        raise
    finally:
        db.close()
```

## 🔍 Ekstraksi Data dari Kolom Details (Oxygen Forensics)

Untuk Telegram di Oxygen Forensics, data penting ada di kolom `Details`:

```python
import re

def extract_from_details(details_text: str) -> dict:
    """
    Extract informasi dari kolom Details Oxygen Forensics
    
    Returns:
        Dictionary dengan keys: message_id, chat_id, recipient_number, to_name
    """
    if not details_text or details_text == 'nan':
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
    
    # Remote party ID (fallback jika phone number tidak ada)
    if not result.get('recipient_number'):
        id_match = re.search(r'Remote party ID:\s*([^\s\n\r]+)', details_text, re.IGNORECASE)
        if id_match:
            result['recipient_number'] = id_match.group(1).strip()
    
    # Remote party name
    name_match = re.search(r'Remote party:\s*([^\n\r]+)', details_text, re.IGNORECASE)
    if name_match:
        result['to_name'] = name_match.group(1).strip()
    
    return result

# Contoh penggunaan
details = """Source file: /data/data/org.telegram.messenger/files/cache4.db
Remote party ID: 1313943896
Remote party: Tes
Remote party phone number: 6287822412992
Chat ID: 1313943896
Message ID: 1"""

extracted = extract_from_details(details)
# Result: {
#     'message_id': '1',
#     'chat_id': '1313943896',
#     'recipient_number': '6287822412992',
#     'to_name': 'Tes'
# }
```

## 📊 Validasi Sebelum Insert

```python
def validate_message_data(message_data: dict) -> tuple[bool, list]:
    """
    Validate message data sebelum insert
    
    Returns:
        (is_valid, errors_list)
    """
    errors = []
    
    # Required fields
    required_fields = {
        'file_id': int,
        'platform': str,
        'message_text': str,
        'message_id': str
    }
    
    for field, field_type in required_fields.items():
        if field not in message_data:
            errors.append(f"Required field '{field}' is missing")
        elif message_data[field] is None:
            errors.append(f"Required field '{field}' cannot be None")
        elif not isinstance(message_data[field], field_type):
            errors.append(f"Field '{field}' must be {field_type.__name__}")
    
    # Platform validation
    valid_platforms = ["telegram", "whatsapp", "instagram", "facebook", "x", "tiktok"]
    if message_data.get("platform") and message_data["platform"] not in valid_platforms:
        errors.append(f"platform must be one of: {valid_platforms}")
    
    # Message text validation
    message_text = message_data.get("message_text")
    if message_text:
        if isinstance(message_text, str) and message_text.strip() == "":
            errors.append("message_text cannot be empty string")
        if message_text == "nan":
            errors.append("message_text cannot be 'nan'")
    
    # Direction validation
    if message_data.get("direction"):
        valid_directions = ["Incoming", "Outgoing", "incoming", "outgoing"]
        if message_data["direction"] not in valid_directions:
            errors.append(f"direction must be one of: {valid_directions}")
    
    return len(errors) == 0, errors

# Contoh penggunaan
message_data = {...}
is_valid, errors = validate_message_data(message_data)
if not is_valid:
    print(f"❌ Validation errors: {', '.join(errors)}")
else:
    insert_chat_message(message_data)
```

## 🎯 Best Practices

### 1. Always Check Duplicates
```python
existing = db.query(ChatMessage).filter(
    ChatMessage.file_id == msg_data["file_id"],
    ChatMessage.platform == msg_data["platform"],
    ChatMessage.message_id == msg_data["message_id"]
).first()
```

### 2. Use Transaction (commit/rollback)
```python
try:
    db.add(message)
    db.commit()
except:
    db.rollback()
    raise
```

### 3. Generate Unique Message ID
```python
def generate_message_id(platform: str, file_id: int, unique_id: str) -> str:
    """Generate unique message ID"""
    return f"{platform}_{file_id}_{unique_id}"

# Atau gunakan Message ID dari Details jika ada
message_id = extracted_data.get('message_id') or generate_message_id(...)
```

### 4. Handle Empty Values
```python
# Jangan insert 'nan' atau empty string, gunakan None
def clean_value(value):
    if value in ['nan', 'NaN', '', None]:
        return None
    return str(value).strip()

message_data["from_name"] = clean_value(row.get("From"))
```

## 🔄 Update Existing Records

```python
def update_chat_message(message_id: str, file_id: int, platform: str, updates: dict):
    """Update existing chat message"""
    db = SessionLocal()
    try:
        message = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.message_id == message_id,
                ChatMessage.file_id == file_id,
                ChatMessage.platform == platform
            )
            .first()
        )
        
        if not message:
            print(f"⚠️  Message not found: {message_id}")
            return None
        
        # Update fields
        for key, value in updates.items():
            if hasattr(message, key):
                setattr(message, key, value)
        
        db.commit()
        db.refresh(message)
        print(f"✅ Updated message: {message_id}")
        return message.id
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error updating: {e}")
        raise
    finally:
        db.close()
```

## 📝 Contoh Lengkap: Parse dan Insert Telegram

```python
import pandas as pd
import re
from app.db.session import SessionLocal
from app.analytics.device_management.models import ChatMessage

def parse_and_insert_telegram(file_path: str, file_id: int):
    """Parse Telegram dari Excel dan insert ke database"""
    db = SessionLocal()
    try:
        df = pd.read_excel(file_path, sheet_name='Messages ', engine='openpyxl', dtype=str)
        
        # Filter Telegram rows
        telegram_rows = df[df['Source'].str.contains('Telegram', case=False, na=False)]
        
        messages_to_insert = []
        
        for idx, row in telegram_rows.iterrows():
            # Extract dari Details
            details = str(row.get('Details', ''))
            extracted = extract_from_details(details)
            
            # Build message_data
            message_data = {
                "file_id": file_id,
                "platform": "telegram",
                "message_text": clean_value(row.get('Text', '')),
                "message_id": extracted.get('message_id') or f"telegram_{file_id}_{idx}",
                "to_name": extracted.get('to_name'),
                "recipient_number": extracted.get('recipient_number'),
                "timestamp": clean_value(row.get('Time stamp (UTC 0)')),
                "thread_id": clean_value(row.get('Thread ID')),
                "chat_id": extracted.get('chat_id'),
                "message_type": clean_value(row.get('Message Type')) or "text",
                "direction": clean_value(row.get('Direction')),
                "source_tool": "oxygen",
                "sheet_name": "Messages "
            }
            
            # Validate
            is_valid, errors = validate_message_data(message_data)
            if not is_valid:
                print(f"⚠️  Row {idx} skipped: {', '.join(errors)}")
                continue
            
            messages_to_insert.append(message_data)
        
        # Batch insert
        saved_count = 0
        for msg_data in messages_to_insert:
            existing = db.query(ChatMessage).filter(
                ChatMessage.file_id == msg_data["file_id"],
                ChatMessage.platform == msg_data["platform"],
                ChatMessage.message_id == msg_data["message_id"]
            ).first()
            
            if not existing:
                db.add(ChatMessage(**msg_data))
                saved_count += 1
        
        db.commit()
        print(f"✅ Inserted {saved_count} Telegram messages")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()
```

## 🚨 Common Issues & Solutions

### Issue 1: `from_name` selalu None untuk Telegram
**Penyebab**: Kolom From di Excel kosong untuk Telegram rows
**Solusi**: Ini normal, data pengirim tidak tersedia di Oxygen Forensics untuk Telegram. Jika diperlukan, bisa di-extract dari informasi device/user.

### Issue 2: Duplicate Message ID
**Penyebab**: Message ID tidak unik
**Solusi**: 
- Gunakan Message ID dari Details jika ada
- Jika tidak, generate dengan format yang benar: `{platform}_{file_id}_{unique_id}`
- Pastikan unique_id benar-benar unik

### Issue 3: Message text = 'nan'
**Penyebab**: Value dari pandas adalah 'nan' string
**Solusi**: 
```python
def clean_value(value):
    if pd.isna(value) or value == 'nan' or value == '':
        return None
    return str(value).strip()
```

### Issue 4: Timestamp format tidak konsisten
**Penyebab**: Format timestamp berbeda-beda
**Solusi**: Normalize timestamp sebelum insert:
```python
def normalize_timestamp(ts_str):
    # Convert berbagai format ke format standar
    # Implement sesuai kebutuhan
    return ts_str  # atau format ulang
```

## ✅ Checklist Sebelum Insert

- [ ] `file_id` sudah valid (ada di tabel files)
- [ ] `platform` adalah lowercase dan valid
- [ ] `message_text` tidak kosong dan bukan 'nan'
- [ ] `message_id` unik (check duplicate dulu)
- [ ] Data sudah di-clean (no 'nan', no empty string)
- [ ] Timestamp format konsisten
- [ ] Transaction handling (try/except dengan rollback)
- [ ] Logging untuk debugging

