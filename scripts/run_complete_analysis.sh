
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="http://172.15.1.207"
API_BASE="$BASE_URL/api/v1"

# Function to print colored output
print_step() {
    echo -e "${BLUE}[STEP $1]${NC} $2"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to check if server is running
check_server() {
    print_step "0" "Checking if server is running..."
    if curl -s "$BASE_URL/" > /dev/null; then
        print_success "Server is running at $BASE_URL"
    else
        print_error "Server is not running. Please start the server first:"
        echo "  source venv/bin/activate"
        echo "  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
        exit 1
    fi
}

# Function to create analytic
create_analytic() {
    print_step "1" "Creating analytic..."
    
    response=$(curl -s -X POST "$API_BASE/analytics/create-analytic" \
        -H "Content-Type: application/json" \
        -d '{
            "analytic_name": "Multi-Device Forensic Analysis CCC",
            "type": "Contact Correlation",
            "method": "Deep Communication",
            "notes": "Complete analysis of 3 devices with hashfile correlation for CCC case"
        }')
    
    if echo "$response" | grep -q "analytic_id"; then
        ANALYTIC_ID=$(echo "$response" | grep -o '"analytic_id":[0-9]*' | grep -o '[0-9]*')
        print_success "Analytic created with ID: $ANALYTIC_ID"
        echo "Response: $response"
    else
        print_error "Failed to create analytic"
        echo "Response: $response"
        exit 1
    fi
}

# Function to upload device data
upload_device_data() {
    print_step "2" "Uploading device data..."
    
    # Upload Device 1 (iPhone - Oxygen)
    print_step "2.1" "Uploading iPhone data (Oxygen Forensics)..."
    response1=$(curl -s -X POST "$API_BASE/analytics/upload-data" \
        -F "file=@contoh_dataset/Oxygen Forensics - iOS Image CCC.xlsx" \
        -F "file_name=Oxygen Forensics - iOS Image CCC.xlsx" \
        -F "notes=iPhone device extraction from Oxygen Forensics" \
        -F "type=Handphone" \
        -F "tools=Oxygen")
    
    if echo "$response1" | grep -q "file_id"; then
        FILE_ID_1=$(echo "$response1" | grep -o '"file_id":[0-9]*' | grep -o '[0-9]*')
        print_success "iPhone data uploaded with file ID: $FILE_ID_1"
    else
        print_error "Failed to upload iPhone data"
        echo "Response: $response1"
    fi
    
    # Upload Device 2 (Android - Oxygen)
    print_step "2.2" "Uploading Android data (Oxygen Forensics)..."
    response2=$(curl -s -X POST "$API_BASE/analytics/upload-data" \
        -F "file=@contoh_dataset/Oxygen Forensics - Android Image CCC.xlsx" \
        -F "file_name=Oxygen Forensics - Android Image CCC.xlsx" \
        -F "notes=Android device extraction from Oxygen Forensics" \
        -F "type=Handphone" \
        -F "tools=Oxygen")
    
    if echo "$response2" | grep -q "file_id"; then
        FILE_ID_2=$(echo "$response2" | grep -o '"file_id":[0-9]*' | grep -o '[0-9]*')
        print_success "Android data uploaded with file ID: $FILE_ID_2"
    else
        print_error "Failed to upload Android data"
        echo "Response: $response2"
    fi
    
    # Upload Device 3 (Magnet Axiom)
    print_step "2.3" "Uploading Magnet Axiom data..."
    response3=$(curl -s -X POST "$API_BASE/analytics/upload-data" \
        -F "file=@contoh_dataset/Magnet Axiom Report - CCC.xlsx" \
        -F "file_name=Magnet Axiom Report - CCC.xlsx" \
        -F "notes=Device extraction from Magnet Axiom" \
        -F "type=Handphone" \
        -F "tools=Magnet Axiom")
    
    if echo "$response3" | grep -q "file_id"; then
        FILE_ID_3=$(echo "$response3" | grep -o '"file_id":[0-9]*' | grep -o '[0-9]*')
        print_success "Magnet Axiom data uploaded with file ID: $FILE_ID_3"
    else
        print_error "Failed to upload Magnet Axiom data"
        echo "Response: $response3"
    fi
}

# Function to add devices
add_devices() {
    print_step "3" "Adding devices..."
    
    # Add Device 1
    print_step "3.1" "Adding iPhone device..."
    response1=$(curl -s -X POST "$API_BASE/analytics/add-device" \
        -F "file_id=$FILE_ID_1" \
        -F "owner_name=Bambang Ajriman - iPhone" \
        -F "phone_number=+6282121200905")
    
    if echo "$response1" | grep -q "device_id"; then
        DEVICE_ID_1=$(echo "$response1" | grep -o '"device_id":[0-9]*' | grep -o '[0-9]*')
        print_success "iPhone device added with ID: $DEVICE_ID_1"
    else
        print_error "Failed to add iPhone device"
        echo "Response: $response1"
    fi
    
    # Add Device 2
    print_step "3.2" "Adding Android device..."
    response2=$(curl -s -X POST "$API_BASE/analytics/add-device" \
        -F "file_id=$FILE_ID_2" \
        -F "owner_name=Riko Suloyo - Android" \
        -F "phone_number=+6289660149979")
    
    if echo "$response2" | grep -q "device_id"; then
        DEVICE_ID_2=$(echo "$response2" | grep -o '"device_id":[0-9]*' | grep -o '[0-9]*')
        print_success "Android device added with ID: $DEVICE_ID_2"
    else
        print_error "Failed to add Android device"
        echo "Response: $response2"
    fi
    
    # Add Device 3
    print_step "3.3" "Adding Magnet Axiom device..."
    response3=$(curl -s -X POST "$API_BASE/analytics/add-device" \
        -F "file_id=$FILE_ID_3" \
        -F "owner_name=Local User - Android Devices" \
        -F "phone_number=+628112157462")
    
    if echo "$response3" | grep -q "device_id"; then
        DEVICE_ID_3=$(echo "$response3" | grep -o '"device_id":[0-9]*' | grep -o '[0-9]*')
        print_success "Magnet Axiom device added with ID: $DEVICE_ID_3"
    else
        print_error "Failed to add Magnet Axiom device"
        echo "Response: $response3"
    fi
}

# Function to link devices to analytic
link_devices() {
    print_step "4" "Linking devices to analytic..."
    
    response=$(curl -s -X POST "$API_BASE/analytics/$ANALYTIC_ID/link-multiple-devices" \
        -H "Content-Type: application/json" \
        -d "{
            \"device_ids\": [$DEVICE_ID_1, $DEVICE_ID_2, $DEVICE_ID_3]
        }")
    
    if echo "$response" | grep -q "linked successfully"; then
        print_success "Devices linked to analytic successfully"
        echo "Response: $response"
    else
        print_error "Failed to link devices to analytic"
        echo "Response: $response"
    fi
}

# Function to upload hashfiles
upload_hashfiles() {
    print_step "5" "Uploading hashfiles..."
    
    # Upload iPhone Hashfile (Oxygen)
    print_step "5.1" "Uploading iPhone hashfile (Oxygen)..."
    response1=$(curl -s -X POST "$API_BASE/analytic/$ANALYTIC_ID/upload-hashfile" \
        -F "file=@contoh_hashfile/Oxygen iPhone - Hashfile MD5.xls" \
        -F "notes=iPhone hashfile from Oxygen Forensics")
    
    if echo "$response1" | grep -q "uploaded successfully"; then
        print_success "iPhone hashfile uploaded successfully"
    else
        print_warning "iPhone hashfile upload failed or already exists"
        echo "Response: $response1"
    fi
    
    # Upload Android Hashfile (Oxygen)
    print_step "5.2" "Uploading Android hashfile (Oxygen)..."
    response2=$(curl -s -X POST "$API_BASE/analytic/$ANALYTIC_ID/upload-hashfile" \
        -F "file=@contoh_hashfile/Oxygen Android - Hashfile MD5.xls" \
        -F "notes=Android hashfile from Oxygen Forensics")
    
    if echo "$response2" | grep -q "uploaded successfully"; then
        print_success "Android hashfile uploaded successfully"
    else
        print_warning "Android hashfile upload failed or already exists"
        echo "Response: $response2"
    fi
    
    # Upload Cellebrite iPhone Hashfile
    print_step "5.3" "Uploading Cellebrite iPhone hashfile..."
    response3=$(curl -s -X POST "$API_BASE/analytic/$ANALYTIC_ID/upload-hashfile" \
        -F "file=@contoh_hashfile/Cellebrite Inseyets iPhone - MD5.xlsx" \
        -F "notes=iPhone hashfile from Cellebrite")
    
    if echo "$response3" | grep -q "uploaded successfully"; then
        print_success "Cellebrite iPhone hashfile uploaded successfully"
    else
        print_warning "Cellebrite iPhone hashfile upload failed or already exists"
        echo "Response: $response3"
    fi
    
    # Upload Cellebrite Android Hashfile
    print_step "5.4" "Uploading Cellebrite Android hashfile..."
    response4=$(curl -s -X POST "$API_BASE/analytic/$ANALYTIC_ID/upload-hashfile" \
        -F "file=@contoh_hashfile/Cellebrite Inseyets Android - Hashfile MD5.xlsx" \
        -F "notes=Android hashfile from Cellebrite")
    
    if echo "$response4" | grep -q "uploaded successfully"; then
        print_success "Cellebrite Android hashfile uploaded successfully"
    else
        print_warning "Cellebrite Android hashfile upload failed or already exists"
        echo "Response: $response4"
    fi
    
    # Upload Encase Hashfile
    print_step "5.5" "Uploading Encase hashfile..."
    response5=$(curl -s -X POST "$API_BASE/analytic/$ANALYTIC_ID/upload-hashfile" \
        -F "file=@contoh_hashfile/Encase - Hashfile.txt" \
        -F "notes=Hashfile from Encase")
    
    if echo "$response5" | grep -q "uploaded successfully"; then
        print_success "Encase hashfile uploaded successfully"
    else
        print_warning "Encase hashfile upload failed or already exists"
        echo "Response: $response5"
    fi
    
    # Upload Magnet Axiom Hashfile
    print_step "5.6" "Uploading Magnet Axiom hashfile..."
    response6=$(curl -s -X POST "$API_BASE/analytic/$ANALYTIC_ID/upload-hashfile" \
        -F "file=@contoh_hashfile/Magnet Axiom - File Details.csv" \
        -F "notes=File details from Magnet Axiom")
    
    if echo "$response6" | grep -q "uploaded successfully"; then
        print_success "Magnet Axiom hashfile uploaded successfully"
    else
        print_warning "Magnet Axiom hashfile upload failed or already exists"
        echo "Response: $response6"
    fi
}

# Function to run analytics
run_analytics() {
    print_step "6" "Running analytics..."
    
    # Contact Correlation
    print_step "6.1" "Getting contact correlation..."
    response1=$(curl -s -X GET "$API_BASE/analytic/$ANALYTIC_ID/contact-correlation?min_devices=2")
    if echo "$response1" | grep -q "correlation"; then
        print_success "Contact correlation analysis completed"
    else
        print_warning "Contact correlation analysis failed or no data"
        echo "Response: $response1"
    fi
    
    # Contact Analytics
    print_step "6.2" "Getting contact analytics..."
    response2=$(curl -s -X GET "$API_BASE/analytic/$ANALYTIC_ID/contact-analytics")
    if echo "$response2" | grep -q "analytics"; then
        print_success "Contact analytics completed"
    else
        print_warning "Contact analytics failed or no data"
        echo "Response: $response2"
    fi
    
    # Hashfile Analytics
    print_step "6.3" "Getting hashfile analytics..."
    response3=$(curl -s -X GET "$API_BASE/analytic/$ANALYTIC_ID/hashfile-analytics")
    if echo "$response3" | grep -q "analytics"; then
        print_success "Hashfile analytics completed"
    else
        print_warning "Hashfile analytics failed or no data"
        echo "Response: $response3"
    fi
    
    # Social Media Correlation
    print_step "6.4" "Getting social media correlation..."
    response4=$(curl -s -X GET "$API_BASE/analytic/$ANALYTIC_ID/social-media-correlation")
    if echo "$response4" | grep -q "correlation"; then
        print_success "Social media correlation completed"
    else
        print_warning "Social media correlation failed or no data"
        echo "Response: $response4"
    fi
    
    # Deep Communication Analytics
    print_step "6.5" "Getting deep communication analytics..."
    response5=$(curl -s -X GET "$API_BASE/analytic/$ANALYTIC_ID/deep-communication-analytics")
    if echo "$response5" | grep -q "analytics"; then
        print_success "Deep Communication Analytics completed"
    else
        print_warning "Deep Communication Analytics failed or no data"
        echo "Response: $response5"
    fi
}

# Function to export reports
export_reports() {
    print_step "7" "Exporting reports..."
    
    # Create reports directory
    mkdir -p reports
    
    # Export Contact Correlation PDF
    print_step "7.1" "Exporting contact correlation PDF..."
    curl -s -X GET "$API_BASE/analytic/$ANALYTIC_ID/export-contact-correlation-pdf" \
        -o "reports/contact_correlation_report.pdf"
    
    if [ -f "reports/contact_correlation_report.pdf" ]; then
        print_success "Contact correlation PDF exported"
    else
        print_warning "Contact correlation PDF export failed"
    fi
    
    # Export Hashfile Correlation PDF
    print_step "7.2" "Exporting hashfile correlation PDF..."
    curl -s -X GET "$API_BASE/analytic/$ANALYTIC_ID/export-hashfile-correlation-pdf" \
        -o "reports/hashfile_correlation_report.pdf"
    
    if [ -f "reports/hashfile_correlation_report.pdf" ]; then
        print_success "Hashfile correlation PDF exported"
    else
        print_warning "Hashfile correlation PDF export failed"
    fi
    
    # Export Social Media Correlation PDF
    print_step "7.3" "Exporting social media correlation PDF..."
    curl -s -X GET "$API_BASE/analytic/$ANALYTIC_ID/export-social-media-correlation-pdf" \
        -o "reports/social_media_correlation_report.pdf"
    
    if [ -f "reports/social_media_correlation_report.pdf" ]; then
        print_success "Social media correlation PDF exported"
    else
        print_warning "Social media correlation PDF export failed"
    fi
    
    # Export Comprehensive Report PDF
    print_step "7.4" "Exporting comprehensive report PDF..."
    curl -s -X GET "$API_BASE/analytic/$ANALYTIC_ID/export-comprehensive-report-pdf" \
        -o "reports/comprehensive_report.pdf"
    
    if [ -f "reports/comprehensive_report.pdf" ]; then
        print_success "Comprehensive report PDF exported"
    else
        print_warning "Comprehensive report PDF export failed"
    fi
}

# Function to update analytic status
update_status() {
    print_step "8" "Updating analytic status..."
    
    response=$(curl -s -X PUT "$API_BASE/analytics/$ANALYTIC_ID/update-status" \
        -H "Content-Type: application/json" \
        -d '{
            "status": "completed",
            "summary": "Analysis completed successfully with all devices and hashfiles processed"
        }')
    
    if echo "$response" | grep -q "updated successfully"; then
        print_success "Analytic status updated to completed"
        echo "Response: $response"
    else
        print_warning "Failed to update analytic status"
        echo "Response: $response"
    fi
}

# Function to get final summary
get_summary() {
    print_step "9" "Getting final summary..."
    
    # Get All Analytics
    print_step "9.1" "Getting all analytics..."
    response1=$(curl -s -X GET "$API_BASE/analytics/get-all-analytic")
    echo "All Analytics: $response1"
    
    # Get All Files
    print_step "9.2" "Getting all files..."
    response2=$(curl -s -X GET "$API_BASE/analytics/files/all")
    echo "All Files: $response2"
    
    # Get Analytic Detail
    print_step "9.3" "Getting analytic detail..."
    response3=$(curl -s -X GET "$API_BASE/analytics/$ANALYTIC_ID")
    echo "Analytic Detail: $response3"
    
    # Get Analytic Devices
    print_step "9.4" "Getting analytic devices..."
    response4=$(curl -s -X GET "$API_BASE/analytics/$ANALYTIC_ID/devices")
    echo "Analytic Devices: $response4"
}

# Main execution
main() {
    echo "============================================================================="
    echo "FORENLYTIC ANALYTICS - COMPLETE ANALYSIS SCRIPT"
    echo "============================================================================="
    echo "This script will run a complete forensic analysis using sample data"
    echo "from contoh_dataset and contoh_hashfile directories."
    echo "============================================================================="
    echo ""
    
    # Check if required directories exist
    if [ ! -d "contoh_dataset" ]; then
        print_error "contoh_dataset directory not found!"
        exit 1
    fi
    
    if [ ! -d "contoh_hashfile" ]; then
        print_error "contoh_hashfile directory not found!"
        exit 1
    fi
    
    # Run all steps
    check_server
    create_analytic
    upload_device_data
    add_devices
    link_devices
    upload_hashfiles
    run_analytics
    export_reports
    update_status
    get_summary
    
    echo ""
    echo "============================================================================="
    echo " ANALYSIS COMPLETED SUCCESSFULLY!"
    echo "============================================================================="
    echo "Analytic ID: $ANALYTIC_ID"
    echo "Devices: $DEVICE_ID_1, $DEVICE_ID_2, $DEVICE_ID_3"
    echo "Files: $FILE_ID_1, $FILE_ID_2, $FILE_ID_3"
    echo "Reports exported to: reports/"
    echo "============================================================================="
}

# Run main function
main "$@"
