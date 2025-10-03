# 🏠 Landing Page API Documentation

## 📋 **Overview**

API endpoint untuk halaman landing page yang menampilkan pilihan antara Analytics dan Case Management. Halaman ini akan tampil setelah user berhasil login atau sebagai default user tanpa login.

---

## 🚀 **Base URL**
```
http://localhost:8000/api/v1/dashboard
```

---

## 🔗 **Endpoints**

### **1. Landing Page Data**
```http
GET /api/v1/dashboard/landing
```

**Description:** Mengambil data untuk halaman landing page dengan pilihan Analytics dan Case Management.

**Response:**
```json
{
  "status": 200,
  "message": "Landing page data retrieved successfully",
  "data": {
    "user_type": "default",
    "available_modules": [
      {
        "id": "analytics",
        "name": "Analytics",
        "description": "Digital forensics analytics and reporting",
        "endpoint": "/api/v1/analytics",
        "icon": "analytics",
        "enabled": true
      },
      {
        "id": "case_management",
        "name": "Case Management",
        "description": "Case management and investigation tracking",
        "endpoint": "/api/v1/cases",
        "icon": "case",
        "enabled": true
      }
    ],
    "navigation": {
      "analytics": {
        "title": "Analytics",
        "description": "Access digital forensics analytics",
        "url": "/analytics"
      },
      "case_management": {
        "title": "Case Management",
        "description": "Manage cases and investigations",
        "url": "/cases"
      }
    }
  }
}
```


---

## 🎯 **Frontend Integration**

### **✅ Landing Page Component:**
```javascript
// Fetch landing page data
const response = await fetch('/api/v1/dashboard/landing');
const data = await response.json();

// Render modules
data.data.available_modules.forEach(module => {
  if (module.enabled) {
    // Create module card
    const card = document.createElement('div');
    card.className = 'module-card';
    card.innerHTML = `
      <h3>${module.name}</h3>
      <p>${module.description}</p>
      <button onclick="navigateTo('${module.id}')">
        Access ${module.name}
      </button>
    `;
    document.getElementById('modules-container').appendChild(card);
  }
});
```

### **✅ Navigation Handler:**
```javascript
function navigateTo(moduleId) {
  const navigation = data.data.navigation[moduleId];
  if (navigation) {
    // Navigate to module
    window.location.href = navigation.url;
  }
}
```


---

## 🎨 **UI Mockup Implementation**

### **✅ Landing Page Structure:**
```html
<div class="landing-page">
  <div class="welcome-section">
    <h1>Digital Forensics Platform</h1>
    <p>Choose your module to continue</p>
  </div>
  
  <div class="modules-container">
    <div class="module-card analytics">
      <div class="module-icon">📊</div>
      <h3>Analytics</h3>
      <p>Digital forensics analytics and reporting</p>
      <button onclick="navigateTo('analytics')">Access Analytics</button>
    </div>
    
    <div class="module-card case-management">
      <div class="module-icon">📁</div>
      <h3>Case Management</h3>
      <p>Case management and investigation tracking</p>
      <button onclick="navigateTo('case_management')">Access Cases</button>
    </div>
  </div>
</div>
```

### **✅ CSS Styling:**
```css
.landing-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  min-height: 100vh;
}

.modules-container {
  display: flex;
  gap: 2rem;
  margin-top: 2rem;
}

.module-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: transform 0.2s;
  cursor: pointer;
}

.module-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.module-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}
```

---

## 🧪 **Testing Commands**

### **✅ Test Landing Page:**
```bash
curl -X GET "http://localhost:8000/api/v1/dashboard/landing" \
  -H "accept: application/json" | jq .
```


---

## 🎯 **User Flow**

### **✅ Default User Flow:**
1. **User Access** → Landing Page
2. **Module Selection** → Analytics atau Case Management
3. **Navigation** → Redirect to selected module
4. **Module Access** → Full functionality

### **✅ Authenticated User Flow:**
1. **Login** → Authentication
2. **Landing Page** → Module selection
3. **Module Selection** → Analytics atau Case Management
4. **Navigation** → Redirect to selected module
5. **Module Access** → Full functionality with user context

---

## 🚀 **Ready for Frontend Integration**

### **✅ Status:**
- ✅ **Landing Page Endpoint** - `/api/v1/dashboard/landing`
- ✅ **Response Format** - Consistent API response format
- ✅ **Frontend Ready** - Data structure siap untuk frontend

**Landing page API sudah siap untuk diintegrasikan dengan frontend!** 🎉
