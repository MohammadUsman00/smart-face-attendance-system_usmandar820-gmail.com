"""
Quick fix for import issues - Run this first
"""
import os
import sys
from pathlib import Path

def create_missing_init_files():
    """Create missing __init__.py files"""
    directories = [
        "config",
        "database", 
        "auth",
        "face_recognition",
        "services",
        "ui",
        "ui/pages",
        "ui/components",
        "utils"
    ]
    
    for directory in directories:
        init_file = Path(directory) / "__init__.py"
        if not init_file.exists():
            init_file.parent.mkdir(parents=True, exist_ok=True)
            with open(init_file, 'w') as f:
                f.write('"""Package initialization"""\n')
            print(f"Created: {init_file}")

def fix_type_imports():
    """Add proper type imports to files that need them"""
    files_to_fix = [
        "auth/authentication.py",
        "auth/validators.py", 
        "database/user_repository.py",
        "database/student_repository.py",
        "database/attendance_repository.py",
        "services/student_service.py",
        "services/attendance_service.py"
    ]
    
    for file_path in files_to_fix:
        file_path_obj = Path(file_path)
        if file_path_obj.exists():
            with open(file_path_obj, 'r') as f:
                content = f.read()
            
            # Check if typing imports are missing
            if 'from typing import' in content:
                # Already has typing imports
                continue
                
            # Add typing imports after other imports
            lines = content.split('\n')
            insert_index = 0
            
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    insert_index = i + 1
                elif line.strip() == '':
                    continue
                else:
                    break
            
            # Insert typing import
            typing_import = "from typing import List, Dict, Optional, Tuple, Any"
            lines.insert(insert_index, typing_import)
            
            # Write back to file
            with open(file_path_obj, 'w') as f:
                f.write('\n'.join(lines))
            
            print(f"Fixed imports in: {file_path}")

if __name__ == "__main__":
    print("Fixing import issues...")
    create_missing_init_files()
    fix_type_imports()
    print("Import fixes completed!")
