#!/usr/bin/env python3
"""
Script to run unit tests for the PDF to HTML server
"""

import subprocess
import sys
import os

def run_tests():
    """Runs all tests"""
    print("🧪 Running unit tests...")
    print("=" * 50)
    
    # Change to Backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    try:
        # Run pytest
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_server.py", 
            "-v", 
            "--tb=short"
        ], capture_output=False)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
            print("\nTests executed:")
            print("- ✅ API Endpoints (/health, /)")
            print("- ✅ Big title detection")
            print("- ✅ Safe OCR function")
            print("- ✅ File validation")
            print("- ✅ PDF to HTML conversion")
            print("- ✅ HTML tag generation")
            print("- ✅ Image processing")
        else:
            print("\n❌ Some tests failed")
            return False
            
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
