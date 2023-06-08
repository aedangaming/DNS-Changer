import requests
import json
import os
import subprocess


REPO_OWNER = "aedangaming"
REPO_NAME = "DNS-Changer"


def check_latest_release():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
    response = requests.get(url)
    if response.status_code == 200:
        data = json.loads(response.content)
        latest_version = data["tag_name"]
        version = latest_version.replace("v", "")
        return {"latest_version": latest_version, "version": version}
    else:
        return None


def updater(file_name):
    try:
        result = check_latest_release()
        download_url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases/download/{result['latest_version']}/DNS-Changer_{result['version']}.exe"
        response = requests.get(download_url)
        if response.status_code == 200:
            # Write new version of file
            exe_filename = f"{REPO_NAME}.exe"
            os.makedirs("New_Update", exist_ok=True)
            with open("New_Update\\" + exe_filename, "wb") as file:
                file.write(response.content)
            command = f'cmd /c "ping -n 3 127.0.0.1 && del /f {file_name} && move .\\New_Update\\DNS-Changer.exe .\\DNS-Changer.exe && rmdir New_Update && start DNS-Changer.exe"'
            subprocess.Popen(command, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return True
        
        else:
            return False
    except:
        return False
