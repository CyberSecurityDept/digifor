import sys
import os
import shutil
import glob
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    print("Cleaning up project...")
    
    os.chdir(project_root)
    

    cleanup_items = [
        "app/__pycache__",
        "app/**/__pycache__",
        "tests/__pycache__",
        "tests/**/__pycache__",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".pytest_cache",
        "htmlcov",
        ".coverage",
        "logs/*.log",
        "*.log",
        ".mypy_cache",
        ".ruff_cache",
        "dist",
        "build",
        "*.egg-info"
    ]
    
    cleaned_count = 0
    
    for item in cleanup_items:
        if "**" in item:
            matches = glob.glob(item, recursive=True)
            for match in matches:
                try:
                    if os.path.isdir(match):
                        shutil.rmtree(match)
                        print(f"Removed directory: {match}")
                    else:
                        os.remove(match)
                        print(f"Removed file: {match}")
                    cleaned_count += 1
                except Exception as e:
                    print(f"Could not remove {match}: {e}")
        else:

            if os.path.exists(item):
                try:
                    if os.path.isdir(item):
                        shutil.rmtree(item)
                        print(f"Removed directory: {item}")
                    else:
                        os.remove(item)
                        print(f"Removed file: {item}")
                    cleaned_count += 1
                except Exception as e:
                    print(f"Could not remove {item}: {e}")
    
    print(f"Cleanup completed! Removed {cleaned_count} items.")

if __name__ == "__main__":
    main()