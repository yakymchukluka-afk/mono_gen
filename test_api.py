#!/usr/bin/env python3
"""
Test script for the Latent Walk Video Generator API
"""
import requests
import time
import json

API_BASE = "http://localhost:8888"

def test_health():
    """Test the health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/healthz")
        print(f"Health check: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_generate():
    """Test the video generation endpoint"""
    print("\nTesting video generation...")
    
    # Test request
    request_data = {
        "seconds": 5,  # Short video for testing
        "fps": 10,
        "out_res": 256,
        "anchors": 6,
        "strength": 2.0,
        "sharpen": True
    }
    
    try:
        # Start generation
        response = requests.post(f"{API_BASE}/generate", json=request_data)
        print(f"Generate response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            job_id = data["job_id"]
            print(f"Job started: {job_id}")
            
            # Poll for status
            while True:
                status_response = requests.get(f"{API_BASE}/status/{job_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"Status: {status_data['status']} - {status_data.get('message', '')}")
                    
                    if status_data["status"] == "completed":
                        print(f"Video generated: {status_data['video_path']}")
                        print(f"Download URL: {status_data['download_url']}")
                        return True
                    elif status_data["status"] == "error":
                        print(f"Generation failed: {status_data.get('error', 'Unknown error')}")
                        return False
                    
                    time.sleep(2)
                else:
                    print(f"Status check failed: {status_response.status_code}")
                    return False
        else:
            print(f"Generation failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"Test failed: {e}")
        return False

def main():
    print("Latent Walk Video Generator API Test")
    print("=" * 40)
    
    # Test health
    if not test_health():
        print("Health check failed. Make sure the API server is running.")
        return
    
    # Test generation
    if test_generate():
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Tests failed!")

if __name__ == "__main__":
    main()