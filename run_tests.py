#!/usr/bin/env python3
"""
Script to run unit tests for the server_enhanced.py module.
"""

import subprocess
import sys
import os

def run_tests():
    """Run the unit tests."""
    # Change to project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    # Run pytest
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "src/Backend/test_server_enhanced.py",
            "-v",
            "--tb=short"
        ], check=True)
        
        print("\n✅ All tests passed!")
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with return code {e.returncode}")
        return e.returncode
    except FileNotFoundError:
        print("❌ pytest not found. Please install testing dependencies:")
        print("pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())
