# 📋 Analisis Form Create Case

## 🎯 **Form Fields pada Gambar vs Schema**

### **✅ Form Fields yang Sesuai:**

#### **1. Case Name → title**
- ✅ **Form Field:** "Case name" input field
- ✅ **Schema Field:** `title: str = Field(..., description="Case title")`
- ✅ **Status:** ✅ **SESUAI**

#### **2. Case Description → description**
- ✅ **Form Field:** "Case Description" textarea
- ✅ **Schema Field:** `description: Optional[str] = Field(None, description="Case description")`
- ✅ **Status:** ✅ **SESUAI**

#### **3. Case ID → case_number**
- ✅ **Form Field:** "Case ID" dengan radio button "Generating" / "Manual input"
- ✅ **Schema Field:** `case_number: str = Field(..., description="Case number")`
- ✅ **Status:** ✅ **SESUAI** (dengan logika conditional)

#### **4. Main Investigator → case_officer**
- ✅ **Form Field:** "Main Investigator" input field
- ✅ **Schema Field:** `case_officer: Optional[str] = Field(None, description="Case officer")`
- ✅ **Status:** ✅ **SESUAI**

#### **5. Agency → agency_id**
- ✅ **Form Field:** "Agency" input field
- ✅ **Schema Field:** `agency_id: Optional[UUID] = Field(None, description="Agency ID")`
- ✅ **Status:** ⚠️ **PERLU PENYESUAIAN** (Form string, Schema UUID)

#### **6. Work Unit → work_unit**
- ✅ **Form Field:** "Work Unit" input field
- ✅ **Schema Field:** `work_unit: Optional[str] = Field(None, description="Work unit")`
- ✅ **Status:** ✅ **SESUAI**

---

## 🔧 **Perbedaan yang Ditemukan**

### **❌ Field yang Tidak Sesuai:**

#### **1. Agency Field Type Mismatch**
- ❌ **Form:** String input field
- ❌ **Schema:** UUID field
- 🔧 **Solusi:** Perlu endpoint untuk lookup agency atau ubah schema

#### **2. Missing Fields di Form**
- ❌ **Schema ada, Form tidak ada:**
  - `case_type` - Case type selection
  - `priority` - Priority selection
  - `incident_date` - Incident date picker
  - `reported_date` - Reported date picker
  - `jurisdiction` - Jurisdiction input
  - `is_confidential` - Confidential checkbox
  - `notes` - Additional notes

#### **3. Missing Fields di Schema**
- ❌ **Form ada, Schema tidak ada:**
  - Tidak ada field yang missing di schema

---

## 🎯 **Rekomendasi Perbaikan**

### **✅ 1. Update Form untuk Menambahkan Missing Fields**

#### **✅ Tambahkan Field yang Missing:**
```html
<!-- Case Type Selection -->
<div class="form-group">
  <label>Case Type</label>
  <select name="case_type">
    <option value="criminal">Criminal</option>
    <option value="civil">Civil</option>
    <option value="corporate">Corporate</option>
  </select>
</div>

<!-- Priority Selection -->
<div class="form-group">
  <label>Priority</label>
  <select name="priority">
    <option value="low">Low</option>
    <option value="medium">Medium</option>
    <option value="high">High</option>
    <option value="critical">Critical</option>
  </select>
</div>

<!-- Incident Date -->
<div class="form-group">
  <label>Incident Date</label>
  <input type="date" name="incident_date">
</div>

<!-- Reported Date -->
<div class="form-group">
  <label>Reported Date</label>
  <input type="date" name="reported_date">
</div>

<!-- Jurisdiction -->
<div class="form-group">
  <label>Jurisdiction</label>
  <input type="text" name="jurisdiction" placeholder="Enter jurisdiction">
</div>

<!-- Confidential Checkbox -->
<div class="form-group">
  <label>
    <input type="checkbox" name="is_confidential">
    Confidential Case
  </label>
</div>

<!-- Additional Notes -->
<div class="form-group">
  <label>Additional Notes</label>
  <textarea name="notes" placeholder="Enter additional notes"></textarea>
</div>
```

### **✅ 2. Update Schema untuk Agency Field**

#### **✅ Option 1: Ubah Schema ke String**
```python
# app/case_management/schemas.py
class CaseBase(BaseModel):
    # ... other fields ...
    agency: Optional[str] = Field(None, description="Agency name")  # Changed from UUID to str
    # ... other fields ...
```

#### **✅ Option 2: Buat Endpoint untuk Agency Lookup**
```python
# app/api/v1/agency_routes.py
@router.get("/agencies")
async def get_agencies():
    return {
        "status": 200,
        "message": "Agencies retrieved successfully",
        "data": [
            {"id": "uuid-1", "name": "Police Department"},
            {"id": "uuid-2", "name": "FBI"},
            {"id": "uuid-3", "name": "Customs"}
        ]
    }
```

### **✅ 3. Update Form untuk Agency Dropdown**

#### **✅ Agency Dropdown dengan API Integration:**
```html
<div class="form-group">
  <label>Agency</label>
  <select name="agency_id" id="agencySelect">
    <option value="">Select Agency</option>
  </select>
</div>

<script>
// Load agencies from API
async function loadAgencies() {
  try {
    const response = await fetch('/api/v1/agencies');
    const data = await response.json();
    
    const select = document.getElementById('agencySelect');
    data.data.forEach(agency => {
      const option = document.createElement('option');
      option.value = agency.id;
      option.textContent = agency.name;
      select.appendChild(option);
    });
  } catch (error) {
    console.error('Error loading agencies:', error);
  }
}

// Load agencies on page load
document.addEventListener('DOMContentLoaded', loadAgencies);
</script>
```

---

## 🧪 **Testing Form dengan Endpoint**

### **✅ Test Case Creation:**
```bash
curl -X POST "http://localhost:8000/api/v1/cases/create-case" \
  -H "Content-Type: application/json" \
  -d '{
    "case_number": "CASE-001",
    "title": "Test Case",
    "description": "Test case description",
    "case_type": "criminal",
    "priority": "high",
    "case_officer": "John Doe",
    "work_unit": "Digital Forensics Unit",
    "jurisdiction": "Jakarta",
    "is_confidential": false,
    "notes": "Additional notes"
  }'
```

### **✅ Expected Response:**
```json
{
  "status": 201,
  "message": "Case created successfully",
  "data": {
    "case_number": "CASE-001",
    "title": "Test Case",
    "description": "Test case description",
    "case_type": "criminal",
    "priority": "high",
    "case_officer": "John Doe",
    "work_unit": "Digital Forensics Unit",
    "jurisdiction": "Jakarta",
    "is_confidential": false,
    "notes": "Additional notes",
    "status": "Open",
    "id": "uuid-here",
    "created_at": "2025-10-03T00:31:24.986370+07:00"
  }
}
```

---

## 🎉 **Kesimpulan**

### **✅ Status Form vs Schema:**

#### **✅ Sesuai (5 fields):**
- ✅ Case Name → title
- ✅ Case Description → description
- ✅ Case ID → case_number
- ✅ Main Investigator → case_officer
- ✅ Work Unit → work_unit

#### **⚠️ Perlu Penyesuaian (1 field):**
- ⚠️ Agency → agency_id (type mismatch)

#### **❌ Missing di Form (6 fields):**
- ❌ case_type
- ❌ priority
- ❌ incident_date
- ❌ reported_date
- ❌ jurisdiction
- ❌ is_confidential
- ❌ notes

### **🔧 Action Items:**
1. **Update Form** - Tambahkan missing fields
2. **Fix Agency Field** - Ubah ke string atau buat lookup endpoint
3. **Test Integration** - Test form dengan endpoint
4. **Add Validation** - Tambahkan client-side validation

**Form perlu diperbaiki untuk sesuai dengan schema!** 🔧
