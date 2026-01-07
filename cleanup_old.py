import os
import shutil

files_to_delete = ['app.py', 'clp_service.py', 'clp_constants.py', 'models.py']

for f in files_to_delete:
    if os.path.exists(f):
        try:
            os.remove(f)
            print(f"Deleted {f}")
        except Exception as e:
            print(f"Failed to delete {f}: {e}")
    else:
        print(f"{f} does not exist")
