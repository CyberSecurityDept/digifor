# API Error Response Handling

Dokumentasi ini menjelaskan cara menangani error response dari API, khususnya untuk analytics endpoints yang memiliki informasi redirect untuk membantu frontend melakukan action yang tepat.

## 📋 Daftar Isi

1. [Error Response Structure](#error-response-structure)
2. [Error 400 - Bad Request](#error-400---bad-request)
3. [Error 404 - Not Found](#error-404---not-found)
4. [Frontend Implementation Guide](#frontend-implementation-guide)
5. [Error Response Examples](#error-response-examples)

---

## Error Response Structure

Semua error response mengikuti struktur berikut:

```json
{
  "status": <status_code>,
  "message": "<error_message>",
  "data": {
    // Error-specific data
  }
}
```

---

## Error 400 - Bad Request

### 1. Insufficient Devices

Error ini terjadi ketika jumlah device yang terhubung dengan analytic kurang dari minimum yang dibutuhkan (biasanya 2 devices).

**Endpoints yang Menggunakan Error Ini:**
- `GET /api/v1/analytic/deep-communication-analytics`
- `GET /api/v1/analytic/contact-correlation`
- `GET /api/v1/analytic/hashfile-analytics`
- `GET /api/v1/analytics/social-media-correlation`

**Response Structure:**
```json
{
  "status": 400,
  "message": "<Analytics Method> requires minimum 2 devices. Current analytic has {device_count} device(s).",
  "data": {
    "analytic_info": {
      "analytic_id": <integer>,
      "analytic_name": "<string>"
    },
    "device_count": <integer>,
    "required_minimum": 2,
    "next_action": "add_device",
    "redirect_to": "/analytics/devices",
    "instruction": "Please add at least 2 devices to continue with <Analytics Method>"
  }
}
```

### 2. Invalid Analytic Method

Error ini terjadi ketika method analytic tidak sesuai dengan endpoint yang dipanggil.

**Endpoints yang Menggunakan Error Ini:**
- `GET /api/v1/analytic/deep-communication-analytics`
- `GET /api/v1/analytic/contact-correlation`
- `GET /api/v1/analytic/hashfile-analytics`
- `GET /api/v1/analytics/social-media-correlation`

**Response Structure:**
```json
{
  "status": 400,
  "message": "This endpoint is only for <Expected Method>. Current analytic method is '<Current Method>'",
  "data": {
    "analytic_info": {
      "analytic_id": <integer>,
      "analytic_name": "<string>",
      "current_method": "<string>"
    },
    "next_action": "create_analytic",
    "redirect_to": "/analytics/start-analyzing",
    "instruction": "Please create a new analytic with method '<Expected Method>'"
  }
}
```

---

## Error 404 - Not Found

### 1. Analytic Not Found

Error ini terjadi ketika analytic dengan ID yang diberikan tidak ditemukan.

**Endpoints yang Menggunakan Error Ini:**
- `GET /api/v1/analytic/deep-communication-analytics`
- `GET /api/v1/analytic/contact-correlation`
- `GET /api/v1/analytic/hashfile-analytics`
- `GET /api/v1/analytics/social-media-correlation`
- `GET /api/v1/analytic/platform-cards/intensity`
- `GET /api/v1/analytic/chat-detail`

**Response Structure:**
```json
{
  "status": 404,
  "message": "Analytic with ID {analytic_id} not found",
  "data": {
    "analytic_info": {
      "analytic_id": <integer>,
      "analytic_name": "Unknown"
    },
    "next_action": "create_analytic",
    "redirect_to": "/analytics/start-analyzing",
    "instruction": "Please create a new analytic with method '<Analytics Method>'"
  }
}
```

### 2. No Devices Linked

Error ini terjadi ketika analytic tidak memiliki device yang terhubung.

**Endpoints yang Menggunakan Error Ini:**
- `GET /api/v1/analytic/deep-communication-analytics`
- `GET /api/v1/analytic/contact-correlation`
- `GET /api/v1/analytic/hashfile-analytics`
- `GET /api/v1/analytics/social-media-correlation`

**Response Structure:**
```json
{
  "status": 404,
  "message": "No devices linked to this analytic",
  "data": {
    "analytic_info": {
      "analytic_id": <integer>,
      "analytic_name": "<string>"
    },
    "device_count": 0,
    "required_minimum": 2,
    "next_action": "add_device",
    "redirect_to": "/analytics/devices",
    "instruction": "Please add at least 2 devices to continue with <Analytics Method>"
  }
}
```

### 3. Devices Not Found

Error ini terjadi ketika device yang terhubung dengan analytic tidak ditemukan di database.

**Endpoints yang Menggunakan Error Ini:**
- `GET /api/v1/analytic/deep-communication-analytics`
- `GET /api/v1/analytic/contact-correlation`
- `GET /api/v1/analytic/hashfile-analytics`
- `GET /api/v1/analytics/social-media-correlation`

**Response Structure:**
```json
{
  "status": 404,
  "message": "Devices not found for this analytic",
  "data": {
    "analytic_info": {
      "analytic_id": <integer>,
      "analytic_name": "<string>"
    },
    "device_count": 0,
    "required_minimum": 2,
    "next_action": "add_device",
    "redirect_to": "/analytics/devices",
    "instruction": "Please add at least 2 devices to continue with <Analytics Method>"
  }
}
```

### 4. Device Not Found in Analytic

Error ini terjadi ketika device_id yang diberikan tidak terhubung dengan analytic.

**Endpoints yang Menggunakan Error Ini:**
- `GET /api/v1/analytic/deep-communication-analytics?device_id={device_id}`
- `GET /api/v1/analytic/platform-cards/intensity?device_id={device_id}`
- `GET /api/v1/analytic/chat-detail?device_id={device_id}`

**Response Structure:**
```json
{
  "status": 404,
  "message": "Device not found in this analytic",
  "data": {
    "analytic_info": {
      "analytic_id": <integer>,
      "analytic_name": "<string>"
    },
    "device_id": <integer>,
    "next_action": "add_device",
    "redirect_to": "/analytics/devices",
    "instruction": "The specified device is not linked to this analytic. Please add the device first."
  }
}
```

---

## Frontend Implementation Guide

### 1. Error Handling Pattern

```javascript
try {
  const response = await api.get('/api/v1/analytic/deep-communication-analytics', {
    params: { analytic_id: 1 }
  });
  
  // Handle success
  console.log(response.data);
} catch (error) {
  if (error.response?.status === 400) {
    const errorData = error.response.data;
    
    // Check if error has redirect information
    if (errorData.data?.next_action && errorData.data?.redirect_to) {
      handleRedirectError(errorData);
    } else {
      // Handle other 400 errors
      handleGenericError(errorData);
    }
  } else if (error.response?.status === 404) {
    const errorData = error.response.data;
    
    // Check if error has redirect information
    if (errorData.data?.next_action && errorData.data?.redirect_to) {
      handleRedirectError(errorData);
    } else {
      // Handle other 404 errors
      handleNotFoundError(errorData);
    }
  } else {
    // Handle other errors (401, 403, 500, etc.)
    handleOtherErrors(error);
  }
}
```

### 2. Redirect Handler Function

```javascript
function handleRedirectError(errorData) {
  const { next_action, redirect_to, instruction, analytic_info } = errorData.data;
  
  // Show notification/toast with instruction
  showNotification({
    type: 'warning',
    message: errorData.message,
    description: instruction,
    duration: 5000
  });
  
  // Redirect to specified path
  if (next_action === 'add_device') {
    // Navigate to add device page
    router.push(redirect_to);
    // Optional: Pass analytic_id as query param
    // router.push(`${redirect_to}?analytic_id=${analytic_info.analytic_id}`);
  } else if (next_action === 'create_analytic') {
    // Navigate to create analytic page
    router.push(redirect_to);
  }
}
```

### 3. React Example

```jsx
import { useRouter } from 'next/router';
import { toast } from 'react-toastify';

function useAnalyticsErrorHandler() {
  const router = useRouter();
  
  const handleError = (error) => {
    if (error.response?.status === 400 || error.response?.status === 404) {
      const errorData = error.response.data;
      
      if (errorData.data?.next_action && errorData.data?.redirect_to) {
        // Show toast notification
        toast.warning(errorData.message, {
          description: errorData.data.instruction
        });
        
        // Redirect after short delay
        setTimeout(() => {
          router.push(errorData.data.redirect_to);
        }, 2000);
      } else {
        toast.error(errorData.message);
      }
    } else {
      toast.error('An unexpected error occurred');
    }
  };
  
  return { handleError };
}

// Usage in component
function AnalyticsComponent() {
  const { handleError } = useAnalyticsErrorHandler();
  const router = useRouter();
  
  const fetchAnalytics = async () => {
    try {
      const response = await api.get('/api/v1/analytic/deep-communication-analytics', {
        params: { analytic_id: router.query.id }
      });
      // Handle success
    } catch (error) {
      handleError(error);
    }
  };
  
  return (
    // Component JSX
  );
}
```

### 4. Vue.js Example

```vue
<template>
  <div>
    <!-- Component template -->
  </div>
</template>

<script>
import { useRouter } from 'vue-router';
import { useToast } from 'vue-toastification';

export default {
  setup() {
    const router = useRouter();
    const toast = useToast();
    
    const handleAnalyticsError = (error) => {
      if (error.response?.status === 400 || error.response?.status === 404) {
        const errorData = error.response.data;
        
        if (errorData.data?.next_action && errorData.data?.redirect_to) {
          // Show toast notification
          toast.warning(errorData.message, {
            description: errorData.data.instruction
          });
          
          // Redirect
          setTimeout(() => {
            router.push(errorData.data.redirect_to);
          }, 2000);
        } else {
          toast.error(errorData.message);
        }
      } else {
        toast.error('An unexpected error occurred');
      }
    };
    
    return {
      handleAnalyticsError
    };
  }
};
</script>
```

---

## Error Response Examples

### Example 1: Device Count Insufficient - Deep Communication Analytics

```json
{
  "status": 400,
  "message": "Deep Communication Analytics requires minimum 2 devices. Current analytic has 1 device(s).",
  "data": {
    "analytic_info": {
      "analytic_id": 1,
      "analytic_name": "Communication Analysis Case 1"
    },
    "device_count": 1,
    "required_minimum": 2,
    "next_action": "add_device",
    "redirect_to": "/analytics/devices",
    "instruction": "Please add at least 2 devices to continue with Deep Communication Analytics"
  }
}
```

**Frontend Action:**
```javascript
// Show notification
showNotification({
  type: 'warning',
  message: 'Insufficient devices',
  description: 'Please add at least 2 devices to continue with Deep Communication Analytics'
});

// Redirect to add device page
router.push('/analytics/devices');
```

### Example 2: Invalid Method - Contact Correlation

```json
{
  "status": 400,
  "message": "This endpoint is only for Contact Correlation. Current analytic method is 'Deep Communication Analytics'",
  "data": {
    "analytic_info": {
      "analytic_id": 1,
      "analytic_name": "Communication Analysis Case 1",
      "current_method": "Deep Communication Analytics"
    },
    "next_action": "create_analytic",
    "redirect_to": "/analytics/start-analyzing",
    "instruction": "Please create a new analytic with method 'Contact Correlation'"
  }
}
```

**Frontend Action:**
```javascript
// Show notification
showNotification({
  type: 'warning',
  message: 'Invalid analytic method',
  description: 'Please create a new analytic with method \'Contact Correlation\''
});

// Redirect to create analytic page
router.push('/analytics/start-analyzing');
```

### Example 3: Analytic Not Found - 404

```json
{
  "status": 404,
  "message": "Analytic with ID 999 not found",
  "data": {
    "analytic_info": {
      "analytic_id": 999,
      "analytic_name": "Unknown"
    },
    "next_action": "create_analytic",
    "redirect_to": "/analytics/start-analyzing",
    "instruction": "Please create a new analytic with method 'Deep Communication Analytics'"
  }
}
```

**Frontend Action:**
```javascript
// Show notification
showNotification({
  type: 'error',
  message: 'Analytic not found',
  description: 'Please create a new analytic with method \'Deep Communication Analytics\''
});

// Redirect to create analytic page
router.push('/analytics/start-analyzing');
```

### Example 4: No Devices Linked - 404

```json
{
  "status": 404,
  "message": "No devices linked to this analytic",
  "data": {
    "analytic_info": {
      "analytic_id": 1,
      "analytic_name": "Communication Analysis Case 1"
    },
    "device_count": 0,
    "required_minimum": 2,
    "next_action": "add_device",
    "redirect_to": "/analytics/devices",
    "instruction": "Please add at least 2 devices to continue with Deep Communication Analytics"
  }
}
```

**Frontend Action:**
```javascript
// Show notification
showNotification({
  type: 'warning',
  message: 'No devices linked',
  description: 'Please add at least 2 devices to continue with Deep Communication Analytics'
});

// Redirect to add device page
router.push('/analytics/devices');
```

### Example 5: Device Not Found in Analytic - 404

```json
{
  "status": 404,
  "message": "Device not found in this analytic",
  "data": {
    "analytic_info": {
      "analytic_id": 1,
      "analytic_name": "Communication Analysis Case 1"
    },
    "device_id": 999,
    "next_action": "add_device",
    "redirect_to": "/analytics/devices",
    "instruction": "The specified device is not linked to this analytic. Please add the device first."
  }
}
```

**Frontend Action:**
```javascript
// Show notification
showNotification({
  type: 'warning',
  message: 'Device not found',
  description: 'The specified device is not linked to this analytic. Please add the device first.'
});

// Redirect to add device page
router.push('/analytics/devices');
```

---

## Best Practices

### 1. Always Check for Redirect Information

Selalu periksa apakah error response memiliki `next_action` dan `redirect_to` sebelum melakukan redirect:

```javascript
if (errorData.data?.next_action && errorData.data?.redirect_to) {
  // Safe to redirect
  router.push(errorData.data.redirect_to);
}
```

### 2. Show User-Friendly Messages

Gunakan field `instruction` untuk menampilkan pesan yang user-friendly:

```javascript
toast.warning(errorData.data.instruction);
```

### 3. Preserve Context

Saat redirect, pertimbangkan untuk menyimpan context (seperti `analytic_id`) agar user dapat kembali ke halaman sebelumnya:

```javascript
// Option 1: Query parameter
router.push(`${redirect_to}?analytic_id=${analytic_info.analytic_id}&return_to=${currentPath}`);

// Option 2: State management (Redux, Vuex, etc.)
store.commit('setReturnPath', currentPath);
router.push(redirect_to);
```

### 4. Handle Multiple Errors

Jika ada multiple error conditions, handle secara berurutan:

```javascript
if (error.response?.status === 400) {
  const errorData = error.response.data;
  
  // Check for redirect information first
  if (errorData.data?.next_action === 'add_device') {
    handleAddDeviceRedirect(errorData);
  } else if (errorData.data?.next_action === 'create_analytic') {
    handleCreateAnalyticRedirect(errorData);
  } else {
    // Handle other 400 errors
    handleGeneric400Error(errorData);
  }
} else if (error.response?.status === 404) {
  const errorData = error.response.data;
  
  // Check for redirect information
  if (errorData.data?.next_action === 'add_device') {
    handleAddDeviceRedirect(errorData);
  } else if (errorData.data?.next_action === 'create_analytic') {
    handleCreateAnalyticRedirect(errorData);
  } else {
    // Handle other 404 errors
    handleGeneric404Error(errorData);
  }
} else if (error.response?.status === 403) {
  handleForbiddenError(error);
} else {
  handleUnexpectedError(error);
}
```

### 5. Logging for Debugging

Log error information untuk debugging:

```javascript
console.error('Analytics Error:', {
  status: error.response?.status,
  message: error.response?.data?.message,
  next_action: error.response?.data?.data?.next_action,
  redirect_to: error.response?.data?.data?.redirect_to,
  analytic_info: error.response?.data?.data?.analytic_info
});
```

---

## Summary

Error 400 dan 404 pada analytics endpoints sekarang menyertakan informasi redirect yang membantu frontend untuk:

1. **Mengidentifikasi masalah**: Melalui `message` dan `instruction`
2. **Menentukan action**: Melalui `next_action` (`"add_device"` atau `"create_analytic"`)
3. **Melakukan redirect**: Melalui `redirect_to` (path frontend)
4. **Memberikan context**: Melalui `analytic_info` (informasi analytic yang terkait)

Frontend harus selalu memeriksa keberadaan `next_action` dan `redirect_to` dalam error response sebelum melakukan redirect otomatis.
