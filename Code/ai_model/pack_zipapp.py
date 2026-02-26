import os
import shutil
import zipapp

def main():
    if not os.path.exists("cloud_app"):
        os.makedirs("cloud_app")
    
    if os.path.exists("cloud_app/cloud_ai"):
        shutil.rmtree("cloud_app/cloud_ai")
    
    shutil.copytree("cloud_ai", "cloud_app/cloud_ai", dirs_exist_ok=True)
    shutil.copy("main.py", "cloud_app/__main__.py")
    
    zipapp.create_archive("cloud_app", "cloud_ai_daemon.pyz", main="main:main")
    print("Successfully created cloud_ai_daemon.pyz")

if __name__ == "__main__":
    main()
