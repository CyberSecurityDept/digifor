#!/usr/bin/env python3
"""
Script untuk testing Deep Communication Analytics endpoints
"""
import sys
import os
import json
from pprint import pprint

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.db.session import SessionLocal
from app.api.v1.analytics_communication_enhanced_routes import (
    get_deep_communication_analytics,
    get_interaction_intensity,
    get_chat_detail,
    search_chat_messages
)
from app.analytics.shared.models import Analytic, AnalyticDevice
from fastapi import Query

def test_endpoints():
    """Test semua endpoint deep communication analytics"""
    db = SessionLocal()
    
    try:
        # Get analytic yang punya devices
        analytic = db.query(Analytic).filter(Analytic.id == 1).first()
        if not analytic:
            print("❌ Analytic ID 1 tidak ditemukan")
            return
        
        device_links = db.query(AnalyticDevice).filter(
            AnalyticDevice.analytic_id == 1
        ).first()
        
        if not device_links:
            print("❌ Analytic ID 1 tidak punya devices")
            return
        
        print("=" * 80)
        print("TESTING DEEP COMMUNICATION ANALYTICS ENDPOINTS")
        print("=" * 80)
        print(f"Analytic ID: {analytic.id}")
        print(f"Analytic Name: {analytic.analytic_name}")
        print()
        
        # Test 1: Deep Communication Analytics (Main Endpoint)
        print("=" * 80)
        print("TEST 1: GET /api/v1/analytic/1/deep-communication-analytics")
        print("=" * 80)
        try:
            response = get_deep_communication_analytics(
                analytic_id=1,
                device_id=None,
                platform=None,
                db=db
            )
            
            data = json.loads(response.body)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Endpoint berhasil")
                response_data = data.get('data', {})
                print(f"  Total Devices: {len(response_data.get('device_tabs', []))}")
                
                device_tabs = response_data.get('device_tabs', [])
                if device_tabs:
                    print(f"\n  Device Tabs:")
                    for tab in device_tabs:
                        print(f"    - {tab.get('device_name')} ({tab.get('phone_number')})")
                
                platform_analysis = response_data.get('platform_analysis', {})
                print(f"\n  Platforms Analyzed: {list(platform_analysis.keys())}")
                
                for platform, persons in platform_analysis.items():
                    print(f"\n  Platform: {platform.upper()}")
                    print(f"    Total Persons: {len(persons)}")
                    if persons:
                        print(f"    Top 5 Persons:")
                        for i, person in enumerate(persons[:5], 1):
                            print(f"      {i}. {person.get('person')}: {person.get('intensity')} messages")
            else:
                print(f"❌ Error: {data}")
        except Exception as e:
            print(f"❌ Error testing endpoint: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n")
        
        # Test 2: Interaction Intensity
        print("=" * 80)
        print("TEST 2: GET /api/v1/analytic/1/interaction-intensity?platform=WhatsApp")
        print("=" * 80)
        try:
            response = get_interaction_intensity(
                analytic_id=1,
                platform="WhatsApp",
                device_id=None,
                db=db
            )
            
            data = json.loads(response.body)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Endpoint berhasil")
                response_data = data.get('data', {})
                intensity_list = response_data.get('intensity_list', [])
                print(f"  Platform: {response_data.get('platform')}")
                print(f"  Total Persons: {len(intensity_list)}")
                
                if intensity_list:
                    print(f"\n  Top 10 Persons:")
                    for i, person in enumerate(intensity_list[:10], 1):
                        print(f"    {i}. {person.get('person')} (ID: {person.get('person_id')}): {person.get('intensity')} messages")
            else:
                print(f"❌ Error: {data}")
        except Exception as e:
            print(f"❌ Error testing endpoint: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n")
        
        # Test 3: Chat Detail
        print("=" * 80)
        print("TEST 3: GET /api/v1/analytic/1/chat-detail?person_name=<person>&platform=WhatsApp")
        print("=" * 80)
        try:
            # Get first person from WhatsApp intensity list
            intensity_response = get_interaction_intensity(
                analytic_id=1,
                platform="WhatsApp",
                device_id=None,
                db=db
            )
            
            if intensity_response.status_code == 200:
                intensity_data = json.loads(intensity_response.body)
                persons = intensity_data.get('data', {}).get('intensity_list', [])
                
                if persons:
                    first_person = persons[0].get('person')
                    print(f"Testing with person: {first_person}")
                    
                    response = get_chat_detail(
                        analytic_id=1,
                        person_name=first_person,
                        platform="WhatsApp",
                        device_id=None,
                        search=None,
                        db=db
                    )
                    
                    data = json.loads(response.body)
                    print(f"Status Code: {response.status_code}")
                    
                    if response.status_code == 200:
                        print("✅ Endpoint berhasil")
                        chat_data = data.get('data', {})
                        print(f"  Person: {chat_data.get('person_name')}")
                        print(f"  Person ID: {chat_data.get('person_id')}")
                        print(f"  Platform: {chat_data.get('platform')}")
                        print(f"  Intensity: {chat_data.get('intensity')}")
                        
                        chat_messages = chat_data.get('chat_messages', [])
                        print(f"  Total Messages: {len(chat_messages)}")
                        
                        if chat_messages:
                            print(f"\n  Sample Messages (first 5):")
                            for i, msg in enumerate(chat_messages[:5], 1):
                                direction = msg.get('direction', 'Unknown')
                                text = msg.get('message_text', '')[:60]
                                timestamp = msg.get('timestamp', 'N/A')
                                print(f"    {i}. [{direction}] ({timestamp[:19] if timestamp else 'N/A'}) {text}...")
                            
                            # Count direction
                            outgoing = len([m for m in chat_messages if m.get('direction') == 'Outgoing'])
                            incoming = len([m for m in chat_messages if m.get('direction') == 'Incoming'])
                            print(f"\n  Message Direction:")
                            print(f"    Outgoing: {outgoing}")
                            print(f"    Incoming: {incoming}")
                    else:
                        print(f"❌ Error: {data}")
                else:
                    print("⚠️  Tidak ada person untuk testing")
            else:
                print("⚠️  Tidak bisa mendapatkan person list")
        except Exception as e:
            print(f"❌ Error testing endpoint: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n")
        
        # Test 4: Chat Search
        print("=" * 80)
        print("TEST 4: GET /api/v1/analytic/1/chat-search?query=test&platform=WhatsApp")
        print("=" * 80)
        try:
            response = search_chat_messages(
                analytic_id=1,
                query="test",
                platform="WhatsApp",
                device_id=None,
                person_name=None,
                db=db
            )
            
            data = json.loads(response.body)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Endpoint berhasil")
                response_data = data.get('data', {})
                results = response_data.get('results', [])
                print(f"  Query: {response_data.get('query')}")
                print(f"  Platform: {response_data.get('platform')}")
                print(f"  Total Results: {len(results)}")
                
                if results:
                    print(f"\n  Sample Results (first 5):")
                    for i, result in enumerate(results[:5], 1):
                        direction = result.get('direction', 'Unknown')
                        text = result.get('message_text', '')[:60]
                        sender = result.get('sender', 'Unknown')
                        print(f"    {i}. [{direction}] From: {sender}")
                        print(f"       {text}...")
            else:
                print(f"❌ Error: {data}")
        except Exception as e:
            print(f"❌ Error testing endpoint: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n")
        print("=" * 80)
        print("TESTING COMPLETED")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_endpoints()
