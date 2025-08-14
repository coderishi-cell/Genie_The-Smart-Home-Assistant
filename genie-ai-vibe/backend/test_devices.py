import requests
import json

def test_devices_endpoint():
    url = "http://localhost:8000/api/devices"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nParsed JSON:")
            print(json.dumps(data, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_devices_endpoint() 