# 🧪 Landing Page Testing Guide

## 📋 **HTML Test Files**

### **✅ 1. Complete Test File**
**File:** `landing_page_test.html`
- ✅ Full-featured HTML dengan styling lengkap
- ✅ API integration dengan error handling
- ✅ Responsive design
- ✅ Interactive effects

### **✅ 2. Simple Test File**
**File:** `simple_landing_test.html`
- ✅ HTML sederhana untuk testing cepat
- ✅ Basic API integration
- ✅ Minimal styling
- ✅ Easy to understand

---

## 🚀 **Cara Testing**

### **✅ 1. Buka File HTML**
```bash
# Buka file HTML di browser
open landing_page_test.html
# atau
open simple_landing_test.html
```

### **✅ 2. Pastikan Server Berjalan**
```bash
# Pastikan backend server berjalan
curl -X GET "http://localhost:8000/api/v1/dashboard/landing" | jq .
```

### **✅ 3. Test di Browser**
1. Buka file HTML di browser
2. Periksa console untuk log API
3. Klik module cards untuk test navigation
4. Klik OTA button untuk test functionality

---

## 🎨 **UI Features**

### **✅ Header Bar**
- ✅ Browser-like header dengan controls
- ✅ Title: "Digital Forensics Platform"
- ✅ Close, minimize, maximize buttons

### **✅ Module Cards**
- ✅ **Analytics Card** - Kiri atas
- ✅ **Case Card** - Kanan atas
- ✅ Hover effects
- ✅ Click handlers

### **✅ OTA Button**
- ✅ Bottom right corner
- ✅ Click handler
- ✅ Status messages

### **✅ Status Messages**
- ✅ Success messages (green)
- ✅ Error messages (red)
- ✅ Auto-hide after 3 seconds

---

## 🔧 **API Integration**

### **✅ Endpoint Testing**
```javascript
// Test API endpoint
const response = await fetch('http://localhost:8000/api/v1/dashboard/landing');
const data = await response.json();

// Expected response
{
  "status": 200,
  "message": "Landing page data retrieved successfully",
  "data": {
    "user_type": "default",
    "available_modules": [...],
    "navigation": {...}
  }
}
```

### **✅ Error Handling**
```javascript
try {
  const response = await fetch(`${API_BASE_URL}/dashboard/landing`);
  const data = await response.json();
  
  if (data.status === 200) {
    showStatus('✅ API Test Successful!', 'success');
  } else {
    showStatus('❌ API Error: ' + data.message, 'error');
  }
} catch (error) {
  showStatus('❌ Connection Error: ' + error.message, 'error');
}
```

---

## 🧪 **Testing Scenarios**

### **✅ 1. API Connection Test**
- ✅ **Success Case** - API berhasil diakses
- ✅ **Error Case** - API tidak dapat diakses
- ✅ **Timeout Case** - API timeout

### **✅ 2. Module Navigation Test**
- ✅ **Analytics Click** - Navigate ke analytics
- ✅ **Case Management Click** - Navigate ke case management
- ✅ **Hover Effects** - Visual feedback

### **✅ 3. OTA Functionality Test**
- ✅ **OTA Button Click** - Trigger OTA update
- ✅ **Status Messages** - Success/error feedback

---

## 📱 **Responsive Design**

### **✅ Desktop View**
- ✅ Two-column layout
- ✅ Full-size module cards
- ✅ OTA button bottom right

### **✅ Mobile View**
- ✅ Single-column layout
- ✅ Stacked module cards
- ✅ Responsive sizing

---

## 🎯 **Expected Behavior**

### **✅ Page Load**
1. Header bar appears
2. Module cards render
3. OTA button appears
4. API test runs automatically
5. Status message shows result

### **✅ Module Click**
1. Status message shows navigation
2. Console logs module ID
3. Alert shows destination URL

### **✅ OTA Click**
1. Status message shows OTA trigger
2. Console logs OTA action
3. Alert shows OTA functionality

---

## 🚀 **Quick Start**

### **✅ 1. Start Backend**
```bash
cd /Users/eaglestory/Documents/SIntek-indonesia/Forenlytic/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### **✅ 2. Open HTML File**
```bash
# Buka di browser
open simple_landing_test.html
```

### **✅ 3. Test Functionality**
- ✅ Check status message (should show success)
- ✅ Click Analytics card
- ✅ Click Case card
- ✅ Click OTA button

---

## 🎉 **Success Indicators**

### **✅ API Test Success**
- ✅ Green status message: "✅ API Test Successful!"
- ✅ Console shows API response
- ✅ No error messages

### **✅ Navigation Test Success**
- ✅ Status messages show navigation
- ✅ Console logs module clicks
- ✅ Alerts show destination URLs

### **✅ OTA Test Success**
- ✅ Status messages show OTA trigger
- ✅ Console logs OTA action
- ✅ Alerts show OTA functionality

**Landing page testing siap untuk digunakan!** 🎉
