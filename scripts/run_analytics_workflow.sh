#!/bin/bash

# Forenlytic Analytics Workflow Script
# Complete workflow from file upload to contact correlation analysis

set -e

# Configuration
BASE_URL="http://172.15.4.26/api/v1"
TIMEOUT=30

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

# Check if server is running
check_server() {
    log_info "Checking server status..."
    if curl -s -f "${BASE_URL%/api/v1}/health" > /dev/null 2>&1; then
        log_success "Server is running and healthy"
        return 0
    else
        log_error "Server is not running or not responding"
        log_info "Please start the server first: ./scripts/start.sh"
        return 1
    fi
}

# Upload file
upload_file() {
    local file_path="$1"
    local file_name="$2"
    local tools="$3"
    
    log_info "Uploading file: $file_name"
    
    if [ ! -f "$file_path" ]; then
        log_error "File not found: $file_path"
        return 1
    fi
    
    local response=$(curl -s -w "\n%{http_code}" -X POST \
        -F "file=@$file_path" \
        -F "file_name=$file_name" \
        -F "tools=$tools" \
        "$BASE_URL/analytics/upload-data")
    
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" -eq 200 ]; then
        local file_id=$(echo "$body" | jq -r '.data.file_id')
        log_success "File uploaded successfully. File ID: $file_id"
        echo "$file_id"
        return 0
    else
        log_error "Upload failed: HTTP $http_code"
        echo "$body" | jq -r '.message // "Unknown error"'
        return 1
    fi
}

# Add device
add_device() {
    local owner_name="$1"
    local phone_number="$2"
    local file_id="$3"
    
    log_info "Adding device for owner: $owner_name"
    
    local response=$(curl -s -w "\n%{http_code}" -X POST \
        -F "owner_name=$owner_name" \
        -F "phone_number=$phone_number" \
        -F "file_id=$file_id" \
        "$BASE_URL/analytics/device/add-device")
    
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" -eq 200 ]; then
        local device_id=$(echo "$body" | jq -r '.data.device_id')
        log_success "Device added successfully. Device ID: $device_id"
        echo "$device_id"
        return 0
    else
        log_error "Add device failed: HTTP $http_code"
        echo "$body" | jq -r '.message // "Unknown error"'
        return 1
    fi
}

# Create analytic
create_analytic() {
    local name="$1"
    local description="$2"
    local method="$3"
    local device_ids="$4"
    
    log_info "Creating analytic: $name"
    
    local json_data=$(jq -n \
        --arg name "$name" \
        --arg description "$description" \
        --arg method "$method" \
        --argjson device_ids "$device_ids" \
        '{name: $name, description: $description, method: $method, device_ids: $device_ids}')
    
    local response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "$json_data" \
        "$BASE_URL/analytics/create-analytic-with-devices")
    
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" -eq 200 ]; then
        local analytic_id=$(echo "$body" | jq -r '.data.analytic_id')
        log_success "Analytic created successfully. Analytic ID: $analytic_id"
        echo "$analytic_id"
        return 0
    else
        log_error "Create analytic failed: HTTP $http_code"
        echo "$body" | jq -r '.message // "Unknown error"'
        return 1
    fi
}

# Run contact correlation
run_contact_correlation() {
    local analytic_id="$1"
    
    log_info "Running contact correlation for analytic ID: $analytic_id"
    
    local json_data=$(jq -n --arg analytic_id "$analytic_id" '{analytic_id: ($analytic_id | tonumber)}')
    
    local response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "$json_data" \
        "$BASE_URL/analytic/$analytic_id/contact-correlation")
    
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" -eq 200 ]; then
        log_success "Contact correlation analysis completed successfully"
        
        # Display results
        local device_count=$(echo "$body" | jq -r '.data.devices | length')
        local correlation_count=$(echo "$body" | jq -r '.data.correlations | length')
        
        log_info "Devices analyzed: $device_count"
        echo "$body" | jq -r '.data.devices[] | "  - \(.device_label): \(.owner_name) (\(.phone_number))"'
        
        log_info "Correlations found: $correlation_count"
        if [ "$correlation_count" -gt 0 ]; then
            echo "$body" | jq -r '.data.correlations[] | "  - \(.contact_name) (\(.phone_number)) found in \(.devices_found_in | length) devices"'
        fi
        
        echo "$body"
        return 0
    else
        log_error "Contact correlation failed: HTTP $http_code"
        echo "$body" | jq -r '.message // "Unknown error"'
        return 1
    fi
}

# Export PDF
export_pdf() {
    local analytic_id="$1"
    local output_path="$2"
    
    log_info "Exporting PDF for analytic ID: $analytic_id"
    
    if [ -z "$output_path" ]; then
        output_path="contact_correlation_report_${analytic_id}.pdf"
    fi
    
    local response=$(curl -s -w "\n%{http_code}" -X GET \
        -o "$output_path" \
        "$BASE_URL/analytic/$analytic_id/export-pdf")
    
    local http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" -eq 200 ]; then
        log_success "PDF exported successfully: $output_path"
        return 0
    else
        log_error "PDF export failed: HTTP $http_code"
        return 1
    fi
}

# Get all files
get_all_files() {
    log_info "Retrieving all files..."
    
    local response=$(curl -s -w "\n%{http_code}" -X GET \
        "$BASE_URL/analytics/files/all")
    
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" -eq 200 ]; then
        local file_count=$(echo "$body" | jq -r '.data | length')
        log_success "Retrieved $file_count files"
        echo "$body" | jq -r '.data[] | "  - ID: \(.id), Name: \(.file_name), Tools: \(.tools)"'
        return 0
    else
        log_error "Get files failed: HTTP $http_code"
        return 1
    fi
}

# Get all devices
get_all_devices() {
    log_info "Retrieving all devices..."
    
    local response=$(curl -s -w "\n%{http_code}" -X GET \
        "$BASE_URL/analytics/device/get-all-devices")
    
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" -eq 200 ]; then
        local device_count=$(echo "$body" | jq -r '.data | length')
        log_success "Retrieved $device_count devices"
        echo "$body" | jq -r '.data[] | "  - ID: \(.device_id), Owner: \(.owner_name), Phone: \(.phone_number)"'
        return 0
    else
        log_error "Get devices failed: HTTP $http_code"
        return 1
    fi
}

# Get all analytics
get_all_analytics() {
    log_info "Retrieving all analytics..."
    
    local response=$(curl -s -w "\n%{http_code}" -X GET \
        "$BASE_URL/analytics/get-all-analytics")
    
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" -eq 200 ]; then
        local analytic_count=$(echo "$body" | jq -r '.data | length')
        log_success "Retrieved $analytic_count analytics"
        echo "$body" | jq -r '.data[] | "  - ID: \(.analytic_id), Name: \(.name), Method: \(.method)"'
        return 0
    else
        log_error "Get analytics failed: HTTP $http_code"
        return 1
    fi
}

# Main workflow function
main() {
    echo "============================================================"
    echo "FORENLYTIC ANALYTICS WORKFLOW"
    echo "============================================================"
    
    # Check server
    if ! check_server; then
        exit 1
    fi
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        log_error "jq is required but not installed. Please install jq first."
        log_info "On macOS: brew install jq"
        log_info "On Ubuntu: sudo apt-get install jq"
        exit 1
    fi
    
    # Example workflow
    echo ""
    log_info "Starting workflow..."
    
    # 1. Upload file
    echo ""
    log_info "Step 1: Uploading file..."
    local sample_file="sample_dataset/contacts_sample.xlsx"
    local file_id
    
    if [ -f "$sample_file" ]; then
        file_id=$(upload_file "$sample_file" "contacts_sample.xlsx" "oxygen")
    else
        log_warning "Sample file not found: $sample_file"
        read -p "Enter file path: " file_path
        read -p "Enter file name: " file_name
        read -p "Enter tools: " tools
        file_id=$(upload_file "$file_path" "$file_name" "$tools")
    fi
    
    if [ -z "$file_id" ] || [ "$file_id" = "null" ]; then
        log_error "Failed to upload file"
        exit 1
    fi
    
    # 2. Add device
    echo ""
    log_info "Step 2: Adding device..."
    read -p "Owner name (default: John Doe): " owner_name
    owner_name=${owner_name:-"John Doe"}
    
    read -p "Phone number (default: 081234567890): " phone_number
    phone_number=${phone_number:-"081234567890"}
    
    local device_id=$(add_device "$owner_name" "$phone_number" "$file_id")
    
    if [ -z "$device_id" ] || [ "$device_id" = "null" ]; then
        log_error "Failed to add device"
        exit 1
    fi
    
    # 3. Create analytic
    echo ""
    log_info "Step 3: Creating analytic..."
    read -p "Analytic name (default: Contact Correlation Analysis): " analytic_name
    analytic_name=${analytic_name:-"Contact Correlation Analysis"}
    
    read -p "Analytic description (default: Analysis of contact correlations): " analytic_description
    analytic_description=${analytic_description:-"Analysis of contact correlations"}
    
    local device_ids="[$device_id]"
    local analytic_id=$(create_analytic "$analytic_name" "$analytic_description" "Contact Correlation" "$device_ids")
    
    if [ -z "$analytic_id" ] || [ "$analytic_id" = "null" ]; then
        log_error "Failed to create analytic"
        exit 1
    fi
    
    # 4. Run contact correlation
    echo ""
    log_info "Step 4: Running contact correlation..."
    local correlation_result=$(run_contact_correlation "$analytic_id")
    
    if [ $? -ne 0 ]; then
        log_error "Failed to run contact correlation"
        exit 1
    fi
    
    # 5. Export PDF
    echo ""
    log_info "Step 5: Exporting PDF..."
    read -p "Export PDF? (y/n, default: y): " export_pdf
    export_pdf=${export_pdf:-"y"}
    
    if [ "$export_pdf" != "n" ]; then
        if ! export_pdf "$analytic_id"; then
            log_warning "PDF export failed, but analysis completed successfully"
        fi
    fi
    
    echo ""
    echo "============================================================"
    log_success "WORKFLOW COMPLETED SUCCESSFULLY!"
    echo "============================================================"
    
    # Display summary
    echo "Summary:"
    echo "  File ID: $file_id"
    echo "  Device ID: $device_id"
    echo "  Analytic ID: $analytic_id"
    
    # Display correlation summary
    local correlation_count=$(echo "$correlation_result" | jq -r '.data.correlations | length')
    echo "  Correlations found: $correlation_count"
    
    if [ "$correlation_count" -gt 0 ]; then
        echo ""
        echo "Correlation Details:"
        echo "$correlation_result" | jq -r '.data.correlations[] | "  \(.contact_name) (\(.phone_number)) found in:"'
        echo "$correlation_result" | jq -r '.data.correlations[] | .devices_found_in[] | "    - \(.device_label): \(.owner_name)"'
    fi
}

# Run main function
main "$@"
