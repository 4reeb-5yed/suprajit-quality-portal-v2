import subprocess
import time
import urllib.request
import sys
import os

exe_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'dist', 'SuprajitQualityPortal', 'SuprajitQualityPortal.exe'))

if not os.path.exists(exe_path):
    print(f"ERROR: Executable not found at {exe_path}. Build it first.")
    sys.exit(1)

print(f"==================================================")
print(f"SMOKE TEST: Launching Compiled Executable...")
print(f"Path: {exe_path}")
print(f"==================================================")

# Launch the EXE in the background
process = subprocess.Popen(
    [exe_path],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Give Waitress 5 seconds to fully boot and bind to Port 5000
time.sleep(5)

try:
    # Attempt to hit the web interface
    print("Sending HTTP GET request to http://localhost:5000/login...")
    response = urllib.request.urlopen("http://localhost:5000/login")
    
    if response.getcode() == 200:
        print("\n[SUCCESS] The compiled executable mathematically booted without crashing and returned 200 OK.")
        sys.exit(0)
    else:
        print(f"\n[FAILURE] The server returned an unexpected status code: {response.getcode()}")
        sys.exit(1)
        
except Exception as e:
    print(f"\n[FATAL CRASH DETECTED] The executable failed to respond. Error: {e}")
    # Print the crash logs from the EXE
    stdout, stderr = process.communicate()
    print("EXE STDOUT:", stdout.decode(errors='ignore'))
    print("EXE STDERR:", stderr.decode(errors='ignore'))
    sys.exit(1)
finally:
    # Kill the background EXE process so it doesn't leave a zombie
    process.terminate()
