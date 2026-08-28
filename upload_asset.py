import os
import subprocess
import urllib.request
import urllib.error

def upload():
    print("Fetching GitHub token...")
    token = subprocess.check_output(["gh", "auth", "token"]).decode("utf-8").strip()
    
    release_id = "378097456"
    url = f"https://uploads.github.com/repos/4reeb-5yed/suprajit-quality-portal-v2/releases/{release_id}/assets?name=SuprajitQualityPortal_V2.zip"
    
    file_path = "SuprajitQualityPortal_V2.zip"
    if not os.path.exists(file_path):
        print("Error: ZIP file not found!")
        return
        
    print(f"Uploading {file_path} (Size: {os.path.getsize(file_path)} bytes)...")
    
    with open(file_path, "rb") as f:
        data = f.read()
        
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/zip")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    
    try:
        response = urllib.request.urlopen(req, timeout=120)
        print(f"Status Code: {response.getcode()}")
        print("Upload successful!")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print(e.read().decode('utf-8'))
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    upload()
