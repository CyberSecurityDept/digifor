# Analytics API Documentation

## Overview
This document provides comprehensive API documentation for the Analytics system endpoints. The Analytics API handles digital forensics data processing, file uploads, device management, and communication analysis. The API is built with FastAPI and follows RESTful conventions.

## Base URL
```
/api/v1
```

## Authentication
All endpoints require Bearer token authentication:
```
Authorization: Bearer <access_token>
```

---

## API Organization

The Analytics API is organized into four main categories for better structure and maintainability:

### 📁 File Management
- File upload and retrieval operations
- Excel file processing and validation

### 📱 Device Management  
- Device registration and processing
- Upload progress monitoring and cancellation

### 🎯 Analytics Management
- Analytics project creation and management
- Device-analytics linking

### 💬 Communication Analysis
- Deep communication thread analysis
- Message and conversation analysis

---

## Available Endpoints

## 📁 File Management Endpoints

### 1. Get All Files
**Endpoint:** `GET /api/v1/analytics/get-all-file`

**Description:** Retrieve all uploaded files with their metadata.

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Success",
  "data": [
    {
      "id": 1,
      "file_name": "evidence_data.xlsx",
      "file_path": "uploads/data/evidence_data.xlsx",
      "notes": "Phone extraction data from suspect device",
      "type": "Phone Extraction",
      "tools": "Cellebrite UFED",
      "created_at": "2025-01-15T10:30:00.000000+07:00"
    }
  ]
}
```

**Response (500 Internal Server Error):**
```json
{
  "status": 500,
  "message": "Gagal mengambil data file: {error_message}",
  "data": []
}
```

### 2. Upload Data File
**Endpoint:** `POST /api/v1/analytics/upload-data`

**Description:** Upload Excel files (.xlsx, .xls) for digital forensics analysis. Files are stored in the `uploads/data` directory.

**Request Body (multipart/form-data):**
- `file` (file, required): Excel file (.xlsx or .xls, APK)
- `notes` (string, required): Description or notes about the file
- `type` (string, required): Type of data (e.g., "Handphone", "SSD", "Harddisk", "PC", "Laptop", "DVR")
- `tools` (string, required): Tools used for extraction (e.g., "Celebrate", "Oxygen", "Magnet Axiom")

**Request Example:**
```http
POST /api/v1/analytics/upload-data
Content-Type: multipart/form-data

file: evidence_data.xlsx
notes: Phone extraction data from suspect device
type: (e.g., "Handphone", "SSD", "Harddisk", "PC", "Laptop", "DVR")
tools: (e.g., "Celebrate", "Oxygen", "Magnet Axiom")
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "File uploaded successfully",
  "data": {
    "file_id": 1,
    "file_path": "uploads/data/evidence_data.xlsx"
  }
}
```

**Response (400 Bad Request - No File):**
```json
{
  "status": 400,
  "message": "File name is required"
}
```

**Response (400 Bad Request - Invalid File Type):**
```json
{
  "status": 400,
  "message": "Only Excel files (.xlsx, .xls) are allowed"
}
```

**Response (500 Internal Server Error):**
```json
{
  "status": 500,
  "message": "Upload error: {error_message}"
}
```

## 📱 Device Management Endpoints

### 3. Add Device
**Endpoint:** `POST /api/v1/analytics/add-device`

**Description:** Add a device for analysis and start the upload/processing pipeline. This endpoint initiates the data processing workflow.

**Request Body (multipart/form-data):**
- `file_id` (integer, required): ID of the uploaded file
- `owner_name` (string, required): Name of the device owner
- `phone_number` (string, required): Phone number of the device owner
- `upload_id` (string, required): Unique identifier for tracking the upload process

**Request Example:**
```http
POST /api/v1/analytics/add-device
Content-Type: multipart/form-data

file_id: 1
owner_name: John Doe
phone_number: +1234567890
upload_id: upload_12345
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Device processing started successfully",
  "data": {
    "upload_id": "upload_12345",
    "device_id": 1,
    "status": "processing"
  }
}
```

**Response (500 Internal Server Error):**
```json
{
  "status": 500,
  "message": "Unexpected error: {error_message}"
}
```

### 4. Get Upload Progress
**Endpoint:** `GET /api/v1/analytics/upload-progress/{upload_id}`

**Description:** Check the progress of file processing and analysis.

**Path Parameters:**
- `upload_id` (string): Unique identifier for the upload process

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Progress retrieved successfully",
  "data": {
    "upload_id": "upload_12345",
    "progress": 75,
    "status": "processing",
    "current_step": "Analyzing messages",
    "estimated_completion": "2025-01-15T11:00:00.000000+07:00"
  }
}
```

**Response (404 Not Found):**
```json
{
  "status": 404,
  "message": "Upload process not found"
}
```

### 5. Cancel Upload
**Endpoint:** `POST /api/v1/analytics/upload-cancel/{upload_id}`

**Description:** Cancel an ongoing upload/analysis process.

**Path Parameters:**
- `upload_id` (string): Unique identifier for the upload process

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Upload process cancelled successfully"
}
```

**Response (404 Not Found):**
```json
{
  "status": 404,
  "message": "Upload process not found"
}
```

## 🎯 Analytics Management Endpoints

### 6. Get All Analytics
**Endpoint:** `GET /api/v1/analytics/get-all-analytic`

**Description:** Retrieve all analytics records with their associated data.

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Success",
  "data": [
    {
      "id": 1,
      "analytic_name": "Phone Analysis Case 001",
      "type": "Digital Forensics",
      "notes": "Analysis of suspect's mobile device",
      "created_at": "2025-01-15T10:30:00.000000+07:00"
    }
  ]
}
```

**Response (500 Internal Server Error):**
```json
{
  "status": 500,
  "message": "Gagal mengambil data: {error_message}",
  "data": []
}
```

### 7. Create Analytic
**Endpoint:** `POST /api/v1/analytics/create-analytic`

**Description:** Create a new analytics record for organizing and tracking analysis projects.

**Request Body:**
```json
{
  "analytic_name": "Phone Analysis Case 001",
  "type": "Digital Forensics",
  "notes": "Analysis of suspect's mobile device for evidence extraction"
}
```

**Request Body Fields:**
- `analytic_name` (string, required): Name of the analytics project
- `type` (string, optional): Type of analysis (e.g., "Digital Forensics", "Network Analysis")
- `notes` (string, optional): Additional notes or description

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Analytics created successfully",
  "data": {
    "id": 1,
    "analytic_name": "Phone Analysis Case 001",
    "type": "Digital Forensics",
    "notes": "Analysis of suspect's mobile device for evidence extraction",
    "created_at": "2025-01-15T10:30:00.000000+07:00"
  }
}
```

**Response (400 Bad Request - Missing Name):**
```json
{
  "status": 400,
  "message": "analytic_name wajib diisi",
  "data": []
}
```

**Response (500 Internal Server Error):**
```json
{
  "status": 500,
  "message": "Gagal membuat analytic: {error_message}",
  "data": []
}
```

### 8. Link Device to Analytic
**Endpoint:** `POST /api/v1/analytics/link-device-analytic`

**Description:** Link a device to an analytics project for organized analysis.

**Request Body:**
```json
{
  "device_id": 1,
  "analytic_id": 1
}
```

**Request Body Fields:**
- `device_id` (integer, required): ID of the device to link
- `analytic_id` (integer, required): ID of the analytics project

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Linked successfully"
}
```

**Response (404 Not Found):**
```json
{
  "status": 404,
  "message": "Device or Analytic not found"
}
```

### 9. Get Analytic Devices
**Endpoint:** `GET /api/v1/analytics/{analytic_id}/devices`

**Description:** Retrieve all devices associated with a specific analytics project.

**Path Parameters:**
- `analytic_id` (integer): ID of the analytics project

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Success",
  "data": [
    {
      "device_id": 1,
      "owner_name": "John Doe",
      "phone_number": "+1234567890",
      "created_at": "2025-01-15T10:30:00.000000+07:00"
    }
  ]
}
```

**Response (404 Not Found):**
```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": []
}
```

## 💬 Communication Analysis Endpoints

### 10. Get Device Communication Threads
**Endpoint:** `GET /api/v1/analytics/deep-communication/device/{device_id}`

**Description:** Retrieve communication threads organized by platform (WhatsApp, Telegram, etc.) for a specific device. Each thread represents a conversation with a unique peer.

**Path Parameters:**
- `device_id` (integer): ID of the device to analyze

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "device_id": 1,
    "owner_name": "John Doe",
    "phone_number": "+1234567890",
    "platforms": {
      "whatsapp": [
        {
          "peer": "Jane Smith",
          "thread_id": "thread_001",
          "intensity": 150,
          "first_timestamp": "2025-01-01T08:00:00.000000+07:00",
          "last_timestamp": "2025-01-15T18:30:00.000000+07:00",
          "platform": "WhatsApp"
        }
      ],
      "telegram": [
        {
          "peer": "Anonymous User",
          "thread_id": "thread_002",
          "intensity": 25,
          "first_timestamp": "2025-01-10T12:00:00.000000+07:00",
          "last_timestamp": "2025-01-12T15:45:00.000000+07:00",
          "platform": "Telegram"
        }
      ]
    }
  }
}
```

**Response (404 Not Found):**
```json
{
  "status": 404,
  "message": "Device not found",
  "data": []
}
```

**Response (200 OK - No Messages):**
```json
{
  "status": 200,
  "message": "No messages",
  "data": []
}
```

**Notes:**
- Threads are sorted by intensity (message count) in descending order
- Peer names are determined from incoming messages when possible
- Each thread represents a unique conversation with a specific contact
- Intensity represents the total number of messages in the thread

### 11. Get Thread Messages
**Endpoint:** `GET /api/v1/analytics/deep-communication/thread/{device_id}/{thread_id}`

**Description:** Retrieve all messages from a specific communication thread.

**Path Parameters:**
- `device_id` (integer): ID of the device
- `thread_id` (string): ID of the specific thread

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Success",
  "data": [
    {
      "id": 1,
      "timestamp": "2025-01-15T10:30:00.000000+07:00",
      "direction": "Incoming",
      "sender": "Jane Smith",
      "receiver": "John Doe",
      "text": "Hello, how are you?",
      "type": "WhatsApp",
      "source": "WhatsApp Chat",
      "details": "Message details",
      "thread_id": "thread_001",
      "attachment": null
    },
    {
      "id": 2,
      "timestamp": "2025-01-15T10:32:00.000000+07:00",
      "direction": "Outgoing",
      "sender": "John Doe",
      "receiver": "Jane Smith",
      "text": "I'm doing well, thank you!",
      "type": "WhatsApp",
      "source": "WhatsApp Chat",
      "details": "Message details",
      "thread_id": "thread_001",
      "attachment": null
    }
  ]
}
```

**Response (404 Not Found):**
```json
{
  "status": 404,
  "message": "Device not found",
  "data": []
}
```

**Response (200 OK - No Messages):**
```json
{
  "status": 200,
  "message": "No messages in this thread",
  "data": []
}
```

---

## Data Models

### Analytic Model
```json
{
  "id": "integer",
  "analytic_name": "string",
  "type": "string (optional)",
  "notes": "string (optional)",
  "created_at": "datetime"
}
```

### File Model
```json
{
  "id": "integer",
  "file_name": "string",
  "file_path": "string",
  "notes": "string (optional)",
  "type": "string",
  "tools": "string",
  "created_at": "datetime"
}
```

### Device Model
```json
{
  "id": "integer",
  "owner_name": "string (optional)",
  "phone_number": "string (optional)",
  "file_id": "integer",
  "created_at": "datetime"
}
```

### Message Model
```json
{
  "id": "integer",
  "device_id": "integer",
  "index_row": "integer",
  "direction": "string (optional)",
  "source": "string (optional)",
  "type": "string (optional)",
  "timestamp": "string (optional)",
  "text": "string (optional)",
  "sender": "string (optional)",
  "receiver": "string (optional)",
  "details": "string (optional)",
  "thread_id": "string (optional)",
  "attachment": "string (optional)",
  "created_at": "datetime"
}
```

### Contact Model
```json
{
  "id": "integer",
  "device_id": "integer",
  "index_row": "integer",
  "type": "string (optional)",
  "source": "string (optional)",
  "contact": "string (optional)",
  "messages": "string (optional)",
  "phones_emails": "string (optional)",
  "internet": "string (optional)",
  "other": "string (optional)",
  "created_at": "datetime"
}
```

### Call Model
```json
{
  "id": "integer",
  "device_id": "integer",
  "index_row": "integer",
  "direction": "string (optional)",
  "source": "string (optional)",
  "type": "string (optional)",
  "timestamp": "string (optional)",
  "duration": "string (optional)",
  "caller": "string (optional)",
  "receiver": "string (optional)",
  "details": "string (optional)",
  "thread_id": "string (optional)",
  "created_at": "datetime"
}
```

### HashFile Model
```json
{
  "id": "integer",
  "device_id": "integer",
  "name": "string (optional)",
  "file_path": "string",
  "created_at": "datetime"
}
```

---

## Workflow Overview

### 1. 📁 File Management Workflow

1. **Upload File**: Use `POST /api/v1/analytics/upload-data` to upload Excel files
2. **Get All Files**: Use `GET /api/v1/analytics/get-all-file` to retrieve uploaded files

### 2. 📱 Device Management Workflow

1. **Add Device**: Use `POST /api/v1/analytics/add-device` to start processing
2. **Monitor Progress**: Use `GET /api/v1/analytics/upload-progress/{upload_id}` to track progress
3. **Cancel if Needed**: Use `POST /api/v1/analytics/upload-cancel/{upload_id}` to cancel processing

### 3. 🎯 Analytics Management Workflow

1. **Create Analytic**: Use `POST /api/v1/analytics/create-analytic` to create analysis project
2. **Get All Analytics**: Use `GET /api/v1/analytics/get-all-analytic` to retrieve all projects
3. **Link Device**: Use `POST /api/v1/analytics/link-device-analytic` to associate devices
4. **View Devices**: Use `GET /api/v1/analytics/{analytic_id}/devices` to see associated devices

### 4. 💬 Communication Analysis Workflow

1. **Get Threads**: Use `GET /api/v1/analytics/deep-communication/device/{device_id}` to see all communication threads
2. **Analyze Messages**: Use `GET /api/v1/analytics/deep-communication/thread/{device_id}/{thread_id}` to examine specific conversations

---

## Error Handling

### Common Error Responses

**400 Bad Request:**
```json
{
  "status": 400,
  "message": "Error description"
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Resource not found"
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Error description"
}
```

---

## Security Features

### File Encryption
- Uploaded files are automatically encrypted using SDP (Secure Data Protocol)
- Encryption keys are generated and stored securely
- Files are stored with `.sdp` extension after encryption

### Data Processing
- Files are processed in temporary directories
- Temporary files are automatically cleaned up after processing
- Original files are preserved for audit purposes

---

## Frontend Integration Examples

### Upload File and Start Processing
```javascript
async function uploadAndProcessFile(file, notes, type, tools, ownerName, phoneNumber) {
  const token = localStorage.getItem('access_token');
  const uploadId = `upload_${Date.now()}`;
  
  // Step 1: Upload file
  const formData = new FormData();
  formData.append('file', file);
  formData.append('notes', notes);
  formData.append('type', type);
  formData.append('tools', tools);
  
  const uploadResponse = await fetch('/api/v1/analytics/upload-data', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });
  
  const uploadResult = await uploadResponse.json();
  
  if (uploadResult.status === 200) {
    // Step 2: Add device and start processing
    const deviceFormData = new FormData();
    deviceFormData.append('file_id', uploadResult.data.file_id);
    deviceFormData.append('owner_name', ownerName);
    deviceFormData.append('phone_number', phoneNumber);
    deviceFormData.append('upload_id', uploadId);
    
    const deviceResponse = await fetch('/api/v1/analytics/add-device', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: deviceFormData
    });
    
    return await deviceResponse.json();
  }
  
  return uploadResult;
}
```

### Monitor Processing Progress
```javascript
async function monitorProgress(uploadId) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(`/api/v1/analytics/upload-progress/${uploadId}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}

// Usage with polling
function startProgressMonitoring(uploadId, onProgress, onComplete) {
  const interval = setInterval(async () => {
    const progress = await monitorProgress(uploadId);
    
    if (progress.status === 200) {
      onProgress(progress.data);
      
      if (progress.data.status === 'completed' || progress.data.status === 'failed') {
        clearInterval(interval);
        onComplete(progress.data);
      }
    }
  }, 2000); // Check every 2 seconds
  
  return interval;
}
```

### Get Communication Analysis
```javascript
async function getCommunicationAnalysis(deviceId) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(`/api/v1/analytics/deep-communication/device/${deviceId}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}

async function getThreadMessages(deviceId, threadId) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(`/api/v1/analytics/deep-communication/thread/${deviceId}/${threadId}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}
```

### Create Analytics Project
```javascript
async function createAnalyticsProject(name, type, notes) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('/api/v1/analytics/create-analytic', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      analytic_name: name,
      type: type,
      notes: notes
    })
  });
  
  return await response.json();
}
```

---

## Status Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request successful |
| 400 | Bad Request - Invalid request parameters |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error - Server error |

---

## API Summary

This comprehensive Analytics API is organized into four main categories:

### 📁 File Management
- **Upload Files**: `POST /api/v1/analytics/upload-data` - Upload Excel files for analysis
- **Get All Files**: `GET /api/v1/analytics/get-all-file` - Retrieve all uploaded files

### 📱 Device Management
- **Add Device**: `POST /api/v1/analytics/add-device` - Start device analysis workflow
- **Monitor Progress**: `GET /api/v1/analytics/upload-progress/{upload_id}` - Track processing status
- **Cancel Processing**: `POST /api/v1/analytics/upload-cancel/{upload_id}` - Cancel ongoing processes

### 🎯 Analytics Management
- **Create Analytic**: `POST /api/v1/analytics/create-analytic` - Create analysis projects
- **Get All Analytics**: `GET /api/v1/analytics/get-all-analytic` - Retrieve all analytics
- **Link Device**: `POST /api/v1/analytics/link-device-analytic` - Associate devices with projects
- **Get Analytic Devices**: `GET /api/v1/analytics/{analytic_id}/devices` - View project devices

### 💬 Communication Analysis
- **Get Device Threads**: `GET /api/v1/analytics/deep-communication/device/{device_id}` - Analyze communication patterns
- **Get Thread Messages**: `GET /api/v1/analytics/deep-communication/thread/{device_id}/{thread_id}` - Examine specific conversations

### Key Features
- **Secure File Processing**: Automatic encryption and secure storage
- **Real-time Progress Tracking**: Monitor long-running analysis processes
- **Communication Analysis**: Deep analysis of messaging patterns and threads
- **Multi-platform Support**: WhatsApp, Telegram, and other messaging platforms
- **Thread-based Organization**: Messages organized by conversation threads
- **Intensity Analysis**: Message count and communication frequency analysis
- **Peer Identification**: Automatic identification of communication partners
- **Comprehensive Data Models**: Support for messages, contacts, calls, and files
- **Error Handling**: Robust error handling with detailed error messages
- **Audit Trail**: Complete tracking of all processing activities

### Data Processing Pipeline
1. **File Upload**: Excel files uploaded and encrypted
2. **Device Registration**: Device information registered with owner details
3. **Data Extraction**: Messages, contacts, calls extracted from uploaded files
4. **Thread Analysis**: Communication threads identified and organized
5. **Peer Analysis**: Communication partners identified and categorized
6. **Intensity Calculation**: Message frequency and communication patterns analyzed

This API provides a complete digital forensics analytics solution with secure file processing, comprehensive communication analysis, and organized project management capabilities.
