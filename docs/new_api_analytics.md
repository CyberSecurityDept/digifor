# API Contract Documentation - Analytics Endpoints

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
All endpoints require authentication via Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## 1. Deep Communication Analytics

### Endpoint
```
GET /analytic/deep-communication-analytics
```

### Description
Retrieves deep communication analytics data for a specific analytic. This endpoint requires a minimum of 2 devices linked to the analytic to function properly.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `analytic_id` | integer | Yes | The ID of the analytic to retrieve data for |
| `device_id` | integer | No | Filter results by specific device ID. If not provided, returns data for all devices linked to the analytic |

### Request Example
```http
GET /api/v1/analytic/deep-communication-analytics?analytic_id=1&device_id=2
Authorization: Bearer <access_token>
```

### Response Structure

#### Success Response (200 OK)
```json
{
  "status": 200,
  "message": "Deep Communication Analytics retrieved successfully",
  "data": {
    "analytic_info": {
      "analytic_id": 1,
      "analytic_name": "Test create analyzing untuk deep communication analytics"
    },
    "devices": [
      {
        "device_id": 2,
        "device_name": "Saras",
        "phone_number": "08838943493394",
        "platform_cards": [
          {
            "platform": "Instagram",
            "has_data": true,
            "message_count": 4,
            "intensity_list": [
              {
                "person": "Riko Suloyo",
                "person_id": "riko.suloyo",
                "intensity": 4,
                "direction": "Incoming"
              }
            ]
          },
          {
            "platform": "Telegram",
            "has_data": true,
            "message_count": 650,
            "intensity_list": [
              {
                "person": "CUAN CEPAT",
                "person_id": "1638057280",
                "intensity": 167,
                "direction": "Incoming"
              },
              {
                "person": "Youth Bandung Reborn",
                "person_id": "1692479054",
                "intensity": 143,
                "direction": "Incoming"
              }
            ]
          },
          {
            "platform": "WhatsApp",
            "has_data": false,
            "message_count": 0
          },
          {
            "platform": "Facebook",
            "has_data": false,
            "message_count": 0
          },
          {
            "platform": "X",
            "has_data": true,
            "message_count": 9,
            "intensity_list": [
              {
                "person": "RikoSuloyo69",
                "person_id": null,
                "intensity": 9,
                "direction": "Incoming"
              }
            ]
          },
          {
            "platform": "TikTok",
            "has_data": false,
            "message_count": 0
          }
        ]
      }
    ],
    "summary": "Lorem Ipsum is simply dummy text..."
  }
}
```

#### Response Fields

**Root Level:**
- `status` (integer): HTTP status code
- `message` (string): Response message
- `data` (object): Response data object

**data.analytic_info:**
- `analytic_id` (integer): ID of the analytic
- `analytic_name` (string): Name of the analytic

**data.devices[]:**
- `device_id` (integer): ID of the device
- `device_name` (string): Name of the device
- `phone_number` (string): Phone number associated with the device
- `platform_cards` (array): Array of platform cards

**data.devices[].platform_cards[]:**
- `platform` (string): Platform name (Instagram, Telegram, WhatsApp, Facebook, X, TikTok)
- `has_data` (boolean): Whether the platform has message data
- `message_count` (integer): Total number of messages for this platform
- `intensity_list` (array, optional): List of person/group intensity data (only present if `has_data` is true)

**data.devices[].platform_cards[].intensity_list[]:**
- `person` (string): Person name or group name
- `person_id` (string|null): Person ID or group ID
- `intensity` (integer): Number of messages exchanged
- `direction` (string): Message direction - "Incoming", "Outgoing", or "Unknown"

**data.summary:**
- `summary` (string|null): Summary text for the analytic

### Error Responses

#### 400 Bad Request - Invalid Method
**When:** The analytic method is not "Deep Communication Analytics"

```json
{
  "status": 400,
  "message": "This endpoint is only for Deep Communication Analytics. Current analytic method is 'Social Media Correlation'",
  "data": null
}
```

**Frontend Handling:**
- Display error message to user
- Suggest using the correct endpoint for the analytic method
- Optionally redirect to the appropriate analytics view

---

#### 400 Bad Request - Insufficient Devices
**When:** The analytic has less than 2 devices linked. Deep Communication Analytics requires a minimum of 2 devices to perform cross-device communication analysis.

```json
{
  "status": 400,
  "message": "Deep Communication Analytics requires minimum 2 devices. Current analytic has 1 device(s).",
  "data": {
    "analytic_info": {
      "analytic_id": 1,
      "analytic_name": "Test Analytic"
    },
    "device_count": 1,
    "required_minimum": 2
  }
}
```

**Response Fields:**
- `data.analytic_info.analytic_id` (integer): The analytic ID
- `data.analytic_info.analytic_name` (string): The analytic name
- `data.device_count` (integer): Current number of devices linked to the analytic
- `data.required_minimum` (integer): Minimum required devices (always 2)

**Frontend Handling:**
- Display error message: "Deep Communication Analytics requires at least 2 devices. Currently linked: {device_count} device(s)."
- Show the analytic name from `data.analytic_info.analytic_name`
- Provide action button to "Add More Devices" or "Link Devices"
- Disable the Deep Communication Analytics view until sufficient devices are linked

---

#### 200 OK - No Devices Linked
**When:** The analytic exists but has no devices linked yet

```json
{
  "status": 200,
  "message": "No devices linked to this analytic",
  "data": {
    "analytic_info": {
      "analytic_id": 1,
      "analytic_name": "Test Analytic"
    },
    "devices": [],
    "summary": "Lorem Ipsum..."
  }
}
```

**Frontend Handling:**
- Display empty state with message: "No devices linked to this analytic"
- Show action button to "Link Devices"
- Display the analytic summary if available

---

#### 403 Forbidden
**When:** User does not have permission to access the analytic

```json
{
  "status": 403,
  "message": "You do not have permission to access this analytic"
}
```

**Frontend Handling:**
- Display error message
- Hide or disable access to the analytic
- Optionally redirect to analytics list page

---

#### 404 Not Found - Analytic Not Found
**When:** The analytic ID does not exist

```json
{
  "status": 404,
  "message": "Analytic not found"
}
```

**Frontend Handling:**
- Display error message: "Analytic not found"
- Redirect to analytics list page
- Optionally show "Go Back" button

---

#### 404 Not Found - Device Not Found
**When:** The specified `device_id` is not linked to the analytic

```json
{
  "status": 404,
  "message": "Device not found in this analytic"
}
```

**Frontend Handling:**
- Display error message: "The selected device is not linked to this analytic"
- Refresh device list or allow user to select a different device
- Optionally show list of available devices

---

## 2. Platform Cards Intensity

### Endpoint
```
GET /analytic/platform-cards/intensity
```

### Description
Retrieves intensity list (message count per person/group) for a specific platform within an analytic.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `analytic_id` | integer | Yes | The ID of the analytic to retrieve data for |
| `platform` | string | Yes | Platform name. Supported values: `Instagram`, `Telegram`, `WhatsApp`, `Facebook`, `X`, `TikTok` (case-insensitive) |
| `device_id` | integer | No | Filter results by specific device ID. If not provided, returns data for all devices linked to the analytic |

### Request Example
```http
GET /api/v1/analytic/platform-cards/intensity?analytic_id=1&platform=WhatsApp&device_id=2
Authorization: Bearer <access_token>
```

### Response Structure

#### Success Response (200 OK)
```json
{
  "status": 200,
  "message": "Platform cards intensity retrieved successfully",
  "data": {
    "analytic_id": 1,
    "platform": "WhatsApp",
    "device_id": 2,
    "intensity_list": [
      {
        "person": "Elsa Polban",
        "person_id": "6285179525600",
        "intensity": 17,
        "direction": "Outgoing"
      },
      {
        "person": "0",
        "person_id": "0",
        "intensity": 6,
        "direction": "Incoming"
      },
      {
        "person": "by.U",
        "person_id": "6285155111222",
        "intensity": 1,
        "direction": "Incoming"
      },
      {
        "person": "Gojek Indonesia",
        "person_id": "628118651031",
        "intensity": 1,
        "direction": "Incoming"
      }
    ],
    "summary": null
  }
}
```

#### Response Fields

**Root Level:**
- `status` (integer): HTTP status code
- `message` (string): Response message
- `data` (object): Response data object

**data:**
- `analytic_id` (integer): ID of the analytic
- `platform` (string): Platform name
- `device_id` (integer|null): Device ID (null if not filtered)
- `intensity_list` (array): Array of intensity data per person/group
- `summary` (string|null): Summary text for the analytic

**data.intensity_list[]:**
- `person` (string): Person name or group name. If person name is empty or whitespace, this will be the same as `person_id`
- `person_id` (string|null): Person ID or group ID. Can be null if not available
- `intensity` (integer): Number of messages exchanged with this person/group
- `direction` (string): Dominant message direction - "Incoming", "Outgoing", or "Unknown"

### Error Responses

#### 400 Bad Request - Missing Platform
```json
{
  "status": 400,
  "message": "Platform parameter is required"
}
```

#### 400 Bad Request - Invalid Platform
```json
{
  "status": 400,
  "message": "Invalid platform. Supported platforms: Instagram, Telegram, WhatsApp, Facebook, X, TikTok"
}
```

#### 403 Forbidden
```json
{
  "status": 403,
  "message": "You do not have permission to access this analytic"
}
```

#### 404 Not Found
```json
{
  "status": 404,
  "message": "Analytic not found"
}
```

#### 404 Not Found - Device Not Found
```json
{
  "status": 404,
  "message": "Device not found in this analytic"
}
```

### Notes
- Platform names are case-insensitive and normalized internally (e.g., "X", "Twitter", "x", "twitter" all map to "x")
- For "One On One" chat types with "Outgoing" direction, `person` and `person_id` are taken from `to_name` and `recipient_number` respectively
- For "Group" or "Broadcast" chat types, `person` and `person_id` are taken from `group_name` and `group_id` respectively
- If `person` is empty or contains only whitespace, it will be replaced with `person_id`

---

## 3. Chat Detail

### Endpoint
```
GET /analytic/chat-detail
```

### Description
Retrieves detailed chat messages for a specific person/group within an analytic. Supports filtering by person name, platform, device, and search text.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `analytic_id` | integer | Yes | The ID of the analytic to retrieve data for |
| `person_name` | string | No* | Person name or group name to filter chat details. *Required if `search` is not provided |
| `platform` | string | No | Platform name. Supported values: `Instagram`, `Telegram`, `WhatsApp`, `Facebook`, `X`, `TikTok` (case-insensitive) |
| `device_id` | integer | No | Filter results by specific device ID |
| `search` | string | No* | Search text to filter messages by content. *Required if `person_name` is not provided |

### Request Example
```http
GET /api/v1/analytic/chat-detail?analytic_id=1&person_name=Elsa%20Polban&platform=WhatsApp&device_id=2&search=
Authorization: Bearer <access_token>
```

### Response Structure

#### Success Response (200 OK)

**For One On One Chat Type:**
```json
{
  "status": 200,
  "message": "Chat detail retrieved successfully",
  "data": {
    "platform": "WhatsApp",
    "intensity": 17,
    "chat_type": "One On One",
    "chat_messages": [
      {
        "message_id": 763,
        "chat_id": "59",
        "timestamp": "2023-10-26T02:06:54+07:00",
        "times": "02:06",
        "direction": "Outgoing",
        "recipient": [
          {
            "recipient_name": "Elsa Polban",
            "recipient_id": "6285179525600"
          }
        ],
        "from": [
          {
            "thread_id": "6285179525600",
            "sender": "Hikari",
            "sender_id": "6285176996014",
            "message_text": "P"
          }
        ]
      },
      {
        "message_id": 764,
        "chat_id": "59",
        "timestamp": "2023-10-26T02:07:10+07:00",
        "times": "02:07",
        "direction": "Outgoing",
        "recipient": [
          {
            "recipient_name": "Elsa Polban",
            "recipient_id": "6285179525600"
          }
        ],
        "from": [
          {
            "thread_id": "6285179525600",
            "sender": "Hikari",
            "sender_id": "6285176996014",
            "message_text": "Elsa ya?"
          }
        ]
      },
      {
        "message_id": 765,
        "chat_id": "59",
        "timestamp": "2023-10-26T02:07:59+07:00",
        "times": "02:07",
        "direction": "Incoming",
        "recipient": [
          {
            "recipient_name": "Hikari",
            "recipient_id": "6285176996014"
          }
        ],
        "from": [
          {
            "thread_id": "6285179525600",
            "sender": "Elsa Polban",
            "sender_id": "6285179525600",
            "message_text": "Iya"
          }
        ]
      }
    ],
    "summary": null
  }
}
```

**For Group/Broadcast Chat Type:**
```json
{
  "status": 200,
  "message": "Chat detail retrieved successfully",
  "data": {
    "group_name": "Youth Bandung Reborn",
    "group_id": "1692479054",
    "platform": "Telegram",
    "intensity": 65,
    "chat_type": "Group",
    "chat_messages": [
      {
        "message_id": 15,
        "chat_id": "9",
        "timestamp": "2025-10-20T14:35:02+07:00",
        "times": "14:35",
        "direction": "Incoming",
        "recipient": [
          {
            "recipient_name": "Nurcahya Hikari",
            "recipient_id": "8229898490"
          }
        ],
        "from": [
          {
            "thread_id": "1692479054",
            "sender": "tibo",
            "sender_id": "7172473346",
            "message_text": "yu"
          }
        ]
      }
    ],
    "summary": null
  }
}
```

#### Response Fields

**Root Level:**
- `status` (integer): HTTP status code
- `message` (string): Response message
- `data` (object): Response data object

**data (for One On One):**
- `platform` (string): Platform name
- `intensity` (integer): Total number of messages
- `chat_type` (string): Chat type - "One On One", "Group", or "Broadcast"
- `chat_messages` (array): Array of chat messages
- `summary` (string|null): Summary text for the analytic

**data (for Group/Broadcast):**
- `group_name` (string): Group name (only present for Group/Broadcast chat types)
- `group_id` (string): Group ID (only present for Group/Broadcast chat types)
- `platform` (string): Platform name
- `intensity` (integer): Total number of messages
- `chat_type` (string): Chat type - "One On One", "Group", or "Broadcast"
- `chat_messages` (array): Array of chat messages
- `summary` (string|null): Summary text for the analytic

**data.chat_messages[]:**
- `message_id` (integer): Unique message ID
- `chat_id` (string): Chat/thread ID
- `timestamp` (string): Full timestamp in ISO 8601 format with timezone
- `times` (string): Time portion (HH:mm format)
- `direction` (string): Message direction - "Incoming", "Outgoing", or "Unknown"
- `recipient` (array): Array of recipient information
- `from` (array): Array of sender information

**data.chat_messages[].recipient[]:**
- `recipient_name` (string): Name of the recipient
- `recipient_id` (string): ID of the recipient

**data.chat_messages[].from[]:**
- `thread_id` (string): Thread/chat ID
- `sender` (string): Name of the sender
- `sender_id` (string): ID of the sender
- `message_text` (string): Content of the message

### Error Responses

#### 400 Bad Request - Missing Parameters
```json
{
  "status": 400,
  "message": "Either person_name or search parameter must be provided"
}
```

#### 400 Bad Request - Invalid Platform
```json
{
  "status": 400,
  "message": "Invalid platform. Supported platforms: Instagram, Telegram, WhatsApp, Facebook, X, TikTok"
}
```

#### 403 Forbidden
```json
{
  "status": 403,
  "message": "You do not have permission to access this analytic"
}
```

#### 404 Not Found
```json
{
  "status": 404,
  "message": "Analytic not found"
}
```

#### 404 Not Found - Device Not Found
```json
{
  "status": 404,
  "message": "Device not found in this analytic"
}
```

### Notes
- For "One On One" chat types, only messages with `chat_type` "One On One" or `null` are returned. Messages with "Group" or "Broadcast" `chat_type` are excluded.
- For "Group" or "Broadcast" chat types, `group_name` and `group_id` are included in the response. For "One On One" chat types, `person_name` and `person_id` are NOT included in the response.
- Messages are sorted by timestamp in ascending order when `person_name` is provided, and descending order otherwise.
- The `search` parameter filters messages by content (case-insensitive partial match).

---

## 4. Upload Data

### Endpoint
```
POST /analytics/upload-data
```

### Description
Uploads and processes a data file (encrypted .sdp format) for analytics. The file is processed asynchronously in the background.

### Request Body

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | The encrypted .sdp file to upload (max 100MB) |
| `file_name` | string | Yes | Name of the file |
| `notes` | string | No | Optional notes about the file |
| `type` | string | Yes | Device type. Allowed values: `Handphone`, `SSD`, `Harddisk`, `PC`, `Laptop`, `DVR` |
| `tools` | string | Yes | Forensic tool used. Allowed values: `Magnet Axiom`, `Cellebrite`, `Oxygen`, `Encase` |
| `method` | string | Yes | Analytic method. Allowed values: `Deep Communication Analytics`, `Social Media Correlation`, `Contact Correlation`, `Hashfile Analytics` |

### Request Example
```http
POST /api/v1/analytics/upload-data
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: <binary file data>
file_name: iPhone_7_2025-10-22_Report.sdp
notes: Test upload
type: Handphone
tools: Cellebrite
method: Deep Communication Analytics
```

### Response Structure

#### Success Response (200 OK)
```json
{
  "status": 200,
  "message": "File uploaded, encrypted & parsed successfully",
  "data": {
    "upload_id": "upload_1701234567_a1b2c3d4",
    "status_upload": "Pending",
    "upload_type": "data"
  }
}
```

#### Response Fields

**Root Level:**
- `status` (integer): HTTP status code
- `message` (string): Response message
- `data` (object): Response data object

**data:**
- `upload_id` (string): Unique upload ID for tracking progress
- `status_upload` (string): Initial upload status (usually "Pending")
- `upload_type` (string): Type of upload (always "data" for this endpoint)

### Error Responses

#### 422 Unprocessable Entity - Missing Required Field
**When:** One or more required fields are missing or empty

```json
{
  "status": 422,
  "message": "Field 'file_name' is required and cannot be empty",
  "error_field": "file_name"
}
```

**Response Fields:**
- `status` (integer): HTTP status code (422)
- `message` (string): Error message indicating which field is missing
- `error_field` (string): The name of the field that is missing or empty

**Possible Fields:**
- `file_name`
- `type`
- `tools`
- `method`

**Frontend Handling:**
- Highlight the field specified in `error_field` with error styling
- Display error message near the field
- Prevent form submission until all required fields are filled
- Show validation error: "This field is required"

---

#### 400 Bad Request - Invalid File Extension
**When:** The uploaded file is not a .sdp file

```json
{
  "status": 400,
  "message": "Only .sdp files are accepted. Please upload encrypted .sdp first"
}
```

**Frontend Handling:**
- Display error message: "Only encrypted .sdp files are accepted"
- Show file type validation before upload if possible
- Provide guidance: "Please ensure your file is encrypted and has .sdp extension"
- Clear the file input and allow user to select a different file

---

#### 400 Bad Request - File Size Exceeded
**When:** The uploaded file exceeds 100MB limit

```json
{
  "status": 400,
  "message": "File size exceeds 100MB limit"
}
```

**Frontend Handling:**
- Display error message: "File size exceeds 100MB limit. Maximum allowed size: 100MB"
- Show the actual file size vs. limit
- Validate file size on client-side before upload to prevent unnecessary upload attempts
- Clear the file input

---

#### 400 Bad Request - Invalid Type
**When:** The `type` field value is not in the allowed list

```json
{
  "status": 400,
  "message": "Invalid type. Allowed types: ['Handphone', 'SSD', 'Harddisk', 'PC', 'Laptop', 'DVR']"
}
```

**Response Fields:**
- `message` (string): Error message with list of allowed types

**Allowed Types:**
- `Handphone`
- `SSD`
- `Harddisk`
- `PC`
- `Laptop`
- `DVR`

**Frontend Handling:**
- Display error message with list of allowed types
- Highlight the `type` field with error styling
- Show dropdown/select with only allowed values
- Validate on client-side before submission

---

#### 400 Bad Request - Invalid Method
**When:** The `method` field value is not in the allowed list

```json
{
  "status": 400,
  "message": "Invalid method. Must be one of: ['Deep Communication Analytics', 'Social Media Correlation', 'Contact Correlation', 'Hashfile Analytics']"
}
```

**Response Fields:**
- `message` (string): Error message with list of allowed methods

**Allowed Methods:**
- `Deep Communication Analytics`
- `Social Media Correlation`
- `Contact Correlation`
- `Hashfile Analytics`

**Frontend Handling:**
- Display error message with list of allowed methods
- Highlight the `method` field with error styling
- Show dropdown/select with only allowed values
- Validate on client-side before submission

---

#### 400 Bad Request - Invalid Tools
**When:** The `tools` field value is not in the allowed list

```json
{
  "status": 400,
  "message": "Invalid tools. Must be one of: ['Magnet Axiom', 'Cellebrite', 'Oxygen', 'Encase']"
}
```

**Response Fields:**
- `message` (string): Error message with list of allowed tools

**Allowed Tools:**
- `Magnet Axiom`
- `Cellebrite`
- `Oxygen`
- `Encase`

**Frontend Handling:**
- Display error message with list of allowed tools
- Highlight the `tools` field with error styling
- Show dropdown/select with only allowed values
- Validate on client-side before submission

---

#### 409 Conflict - File Already Exists
**When:** A file with the same `file_name`, `tools`, and `method` combination already exists in the system

```json
{
  "status": 409,
  "message": "File already exists",
  "data": {
    "file_id": 123,
    "file_name": "iPhone_7_2025-10-22_Report.sdp",
    "tools": "Cellebrite",
    "method": "Deep Communication Analytics",
    "created_at": "2025-11-19T16:03:29.508227"
  }
}
```

**Response Fields:**
- `status` (integer): HTTP status code (409)
- `message` (string): Error message
- `data` (object): Information about the existing file
  - `file_id` (integer): ID of the existing file
  - `file_name` (string): Name of the existing file
  - `tools` (string): Tools used for the existing file
  - `method` (string): Method used for the existing file
  - `created_at` (string): ISO 8601 timestamp when the file was created

**Frontend Handling:**
- Display error message: "A file with the same name, tools, and method already exists"
- Show details of the existing file:
  - File name: `data.file_name`
  - Tools: `data.tools`
  - Method: `data.method`
  - Created at: Format `data.created_at` as readable date/time
- Provide options:
  - "View Existing File" (navigate to file details using `data.file_id`)
  - "Change File Name" (allow user to rename and retry)
  - "Cancel" (clear form)
- Do not allow duplicate uploads without user confirmation

---

#### 500 Internal Server Error
**When:** An unexpected server error occurs during file upload or processing

```json
{
  "status": 500,
  "message": "Upload error: <error details>"
}
```

**Response Fields:**
- `status` (integer): HTTP status code (500)
- `message` (string): Error message with error details

**Frontend Handling:**
- Display generic error message: "An error occurred while uploading the file. Please try again."
- Log the error details for debugging (do not show technical details to end users)
- Provide "Retry" button to attempt upload again
- If error persists, suggest contacting support
- Clear file input if necessary

### Upload Progress Tracking

After uploading, you can track the progress using the `upload_id`:

```
GET /api/v1/analytics/upload-progress?upload_id=<upload_id>&type=data
```

### Notes
- The file must be encrypted in .sdp format before upload
- Maximum file size is 100MB
- The upload is processed asynchronously. Use the `upload_id` to track progress
- If a file with the same `file_name`, `tools`, and `method` already exists, the upload will be rejected with a 409 Conflict response
- Allowed file extensions vary by device type:
  - **Handphone**: xlsx, xls, csv, txt, xml, apk, ipa
  - **SSD**: xlsx, xls, csv, txt, xml
  - **Harddisk**: xlsx, xls, csv, txt, xml
  - **PC**: xlsx, xls, csv, txt, xml
  - **Laptop**: xlsx, xls, csv, txt, xml
  - **DVR**: xlsx, xls, csv, txt, xml, mp4, avi, mov

---

## Error Handling Guide

### Error Response Structure

All error responses follow a consistent structure:

```json
{
  "status": <http_status_code>,
  "message": "<error_message>",
  "data": <optional_error_data>
}
```

### Common Error Codes

| Status Code | Description | When to Use |
|-------------|-------------|-------------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid parameters, validation failed, or business logic violation (e.g., insufficient devices) |
| 403 | Forbidden | User does not have permission to access the resource |
| 404 | Not Found | Resource (analytic, device, etc.) does not exist |
| 409 | Conflict | Resource already exists (e.g., duplicate file upload) |
| 422 | Unprocessable Entity | Required fields missing or empty, format validation failed |
| 500 | Internal Server Error | Unexpected server error occurred |

### Error Handling Best Practices

#### 1. Client-Side Validation
Always validate input on the client-side before making API requests:
- **File Upload:**
  - Check file extension is `.sdp`
  - Check file size ≤ 100MB
  - Validate all required fields are filled
  - Validate `type`, `tools`, and `method` against allowed values

- **Query Parameters:**
  - Validate `analytic_id` is a positive integer
  - Validate `device_id` is a positive integer (if provided)
  - Validate `platform` is one of the supported platforms
  - Validate `person_name` or `search` is provided for chat-detail endpoint

#### 2. Error Message Display
- **User-Friendly Messages:** Display user-friendly error messages, not technical details
- **Field-Specific Errors:** Highlight specific form fields that have errors
- **Actionable Guidance:** Provide clear guidance on how to fix the error

#### 3. Error Recovery
- **Retry Logic:** For 500 errors, provide a "Retry" button
- **Form Preservation:** For validation errors, preserve user input (except for invalid fields)
- **Alternative Actions:** For 409 conflicts, offer alternative actions (view existing, rename, etc.)

#### 4. Error Logging
- Log all error responses for debugging purposes
- Include: status code, error message, endpoint, timestamp, user context
- Do not log sensitive information (tokens, passwords, etc.)

### Validation Error Handling Flow

```
1. Client-side validation (before API call)
   ↓ (if validation fails)
   Show inline error, prevent API call
   
2. API call
   ↓ (if validation fails)
   
3. Check status code:
   - 422: Show field-specific error
   - 400: Show general validation error
   - 409: Show conflict resolution options
   - 404: Show not found message, redirect if needed
   - 403: Show permission error, hide/disable resource
   - 500: Show generic error, offer retry
```

### Example Error Handling Implementation

```javascript
// Example: File Upload Error Handling
async function handleFileUpload(file, formData) {
  try {
    // Client-side validation
    if (!file.name.endsWith('.sdp')) {
      showError('Only .sdp files are accepted');
      return;
    }
    
    if (file.size > 100 * 1024 * 1024) {
      showError('File size exceeds 100MB limit');
      return;
    }
    
    // API call
    const response = await uploadFile(formData);
    
    if (response.status === 200) {
      showSuccess('File uploaded successfully');
      trackUploadProgress(response.data.upload_id);
    }
    
  } catch (error) {
    const status = error.response?.status;
    const data = error.response?.data;
    
    switch (status) {
      case 422:
        // Field-specific error
        highlightField(data.error_field);
        showFieldError(data.error_field, data.message);
        break;
        
      case 400:
        // Validation error
        showError(data.message);
        break;
        
      case 409:
        // Duplicate file
        showConflictDialog(data.data);
        break;
        
      case 500:
        // Server error
        showError('An error occurred. Please try again.');
        showRetryButton();
        break;
        
      default:
        showError('An unexpected error occurred');
    }
  }
}
```

### Device Count Validation

For **Deep Communication Analytics**, always check device count before displaying analytics:

```javascript
// Example: Device Count Check
async function loadDeepCommunicationAnalytics(analyticId, deviceId) {
  try {
    const response = await getDeepCommunicationAnalytics(analyticId, deviceId);
    
    if (response.status === 400 && response.data?.device_count !== undefined) {
      // Insufficient devices
      const { device_count, required_minimum } = response.data;
      showDeviceCountError(device_count, required_minimum);
      showAddDeviceButton();
      return;
    }
    
    // Success - display analytics
    displayAnalytics(response.data);
    
  } catch (error) {
    handleError(error);
  }
}
```

---

## Platform Support

All endpoints support the following platforms:
- **Instagram**
- **Telegram**
- **WhatsApp**
- **Facebook**
- **X** (formerly Twitter) - Note: "X" and "Twitter" are treated as the same platform

---

## Data Types

### Chat Type
- `One On One`: Direct message between two individuals
- `Group`: Group chat with multiple participants
- `Broadcast`: Broadcast message to multiple recipients

### Direction
- `Incoming`: Message received by the device owner
- `Outgoing`: Message sent by the device owner
- `Unknown`: Direction could not be determined

---

## Best Practices

1. **Authentication**: Always include the Bearer token in the Authorization header
2. **Error Handling**: Check the `status` field in the response and handle errors appropriately
3. **Pagination**: For large datasets, consider implementing client-side pagination
4. **Upload Progress**: For file uploads, poll the upload progress endpoint to track processing status
5. **Platform Names**: Platform names are case-insensitive, but use the standard names (Instagram, Telegram, WhatsApp, Facebook, X, TikTok) for consistency
6. **Device Filtering**: Use `device_id` parameter to filter results when working with analytics that have multiple devices

---

## Error Handling Summary

### Quick Reference: Error Scenarios

#### File Upload Validation Errors

| Error Scenario | Status Code | Key Field | Frontend Action |
|----------------|-------------|-----------|----------------|
| Missing required field | 422 | `error_field` | Highlight field, show error message |
| Invalid file extension | 400 | - | Show error, clear file input |
| File size exceeded | 400 | - | Show size limit message, clear file input |
| Invalid device type | 400 | `type` | Show allowed types, highlight field |
| Invalid method | 400 | `method` | Show allowed methods, highlight field |
| Invalid tools | 400 | `tools` | Show allowed tools, highlight field |
| Duplicate file | 409 | `data.file_id` | Show existing file info, offer actions |

#### Device Count Validation Errors

| Error Scenario | Status Code | Key Fields | Frontend Action |
|---------------|-------------|------------|----------------|
| Insufficient devices (< 2) | 400 | `device_count`, `required_minimum` | Show error, disable analytics, show "Add Device" button |
| No devices linked | 200 | `devices: []` | Show empty state, show "Link Devices" button |
| Device not found | 404 | - | Show error, refresh device list |

#### Access Control Errors

| Error Scenario | Status Code | Frontend Action |
|---------------|-------------|----------------|
| No permission | 403 | Hide/disable resource, show error |
| Analytic not found | 404 | Redirect to list, show error |
| Device not found | 404 | Refresh device list, show error |

### Validation Checklist for Frontend

#### Before File Upload
- [ ] File extension is `.sdp`
- [ ] File size ≤ 100MB
- [ ] `file_name` is not empty
- [ ] `type` is one of: Handphone, SSD, Harddisk, PC, Laptop, DVR
- [ ] `tools` is one of: Magnet Axiom, Cellebrite, Oxygen, Encase
- [ ] `method` is one of: Deep Communication Analytics, Social Media Correlation, Contact Correlation, Hashfile Analytics

#### Before Deep Communication Analytics Request
- [ ] `analytic_id` is a valid positive integer
- [ ] Analytic method is "Deep Communication Analytics"
- [ ] At least 2 devices are linked to the analytic (check via API or previous response)
- [ ] User has permission to access the analytic

#### Before Platform Cards Intensity Request
- [ ] `analytic_id` is a valid positive integer
- [ ] `platform` is one of: Instagram, Telegram, WhatsApp, Facebook, X, TikTok
- [ ] `device_id` is a valid positive integer (if provided)

#### Before Chat Detail Request
- [ ] `analytic_id` is a valid positive integer
- [ ] Either `person_name` or `search` is provided
- [ ] `platform` is one of: Instagram, Telegram, WhatsApp, Facebook, X, TikTok (if provided)
- [ ] `device_id` is a valid positive integer (if provided)

---

## Version
**API Version:** v1  
**Last Updated:** 2025-11-19

