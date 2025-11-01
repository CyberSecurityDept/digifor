#!/usr/bin/env python3
"""
Script untuk test endpoint social-media-correlation via HTTP
"""

import requests
import json
import sys

def test_endpoint(analytic_id: int, platform: str = "Instagram", base_url: str = "http://localhost:8000"):
    """Test endpoint via HTTP"""
    
    url = f"{base_url}/api/v1/analytics/{analytic_id}/social-media-correlation"
    params = {"platform": platform}
    
    print("=" * 100)
    print(f"TESTING ENDPOINT: GET {url}")
    print(f"Parameters: {params}")
    print("=" * 100)
    print()
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Response:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if data.get("status") == 200:
                result_data = data.get("data", {})
                total_devices = result_data.get("total_devices", 0)
                correlations = result_data.get("correlations", {})
                
                print()
                print("=" * 100)
                print("ANALISIS HASIL:")
                print("=" * 100)
                print(f"Total Devices: {total_devices}")
                
                if correlations:
                    for platform_name, platform_data in correlations.items():
                        buckets = platform_data.get("buckets", [])
                        print(f"\nPlatform: {platform_name}")
                        print(f"Total Buckets (Correlations): {len(buckets)}")
                        
                        if buckets:
                            print("\nCorrelations ditemukan:")
                            for idx, bucket in enumerate(buckets[:10], 1):  # Show first 10
                                print(f"\n  {idx}. {bucket.get('analyzed_account', 'N/A')}")
                                print(f"     Label: {bucket.get('label', 'N/A')}")
                                print(f"     Total Connections: {bucket.get('total_connections', 0)}")
                                print(f"     Anchor Device: {bucket.get('device_label', 'N/A')} - {bucket.get('device_owner', 'N/A')}")
                                matched = bucket.get('matched_devices', [])
                                if matched:
                                    print(f"     Matched Devices: {len(matched)}")
                                    for m in matched:
                                        print(f"       - {m.get('device_label', 'N/A')}: {m.get('owner_name', 'N/A')}")
                        else:
                            print("Tidak ada correlation ditemukan (buckets kosong)")
                else:
                    print("\nTidak ada correlations data")
        else:
            print(f"❌ Error Response:")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Tidak dapat terhubung ke server di {base_url}")
        print("   Pastikan server FastAPI sedang berjalan")
        print("   Jalankan: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Social Media Correlation Endpoint via HTTP")
    parser.add_argument("--analytic-id", type=int, default=1, help="Analytic ID (default: 1)")
    parser.add_argument("--platform", type=str, default="Instagram", help="Platform filter (default: Instagram)")
    parser.add_argument("--base-url", type=str, default="http://localhost:8000", help="Base URL (default: http://localhost:8000)")
    
    args = parser.parse_args()
    
    test_endpoint(args.analytic_id, args.platform, args.base_url)

