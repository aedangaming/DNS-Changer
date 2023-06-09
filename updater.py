import requests
import json
import os
import subprocess
import time
from tqdm import tqdm

REPO_OWNER = "aedangaming"
REPO_NAME = "DNS-Changer"


def check_latest_release():
    try:
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
        response = requests.get(url)
        if response.status_code == 200:
            data = json.loads(response.content)
            latest_version = data["tag_name"]
            version = latest_version.replace("v", "")
            return {"latest_version": latest_version, "version": version}
        else:
            return None
    except:
        return None


def updater(file_name):
    try:
        result = check_latest_release()
        download_url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases/download/{result['latest_version']}/DNS-Changer_{result['version']}.exe"
        response = requests.get(download_url, stream=True)
        if response.status_code == 200:
            total_size = int(response.headers.get("content-length", 0))
            block_size = 1024
            ascii = " ▒▓"
            progress_bar = tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                desc=f"Downloading {result['latest_version']}",
                bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}",
                ascii=ascii,
                colour="green",
            )

            # Write new version of file
            exe_filename = f"{REPO_NAME}.exe"
            os.makedirs("New_Update", exist_ok=True)

            with open("New_Update\\" + exe_filename, "wb") as file:
                for data in response.iter_content(block_size):
                    progress_bar.update(len(data))
                    file.write(data)

            progress_bar.close()
            time.sleep(0.5)

            command = f'cmd /c "ping -n 3 127.0.0.1 && del /f {file_name} && move .\\New_Update\\DNS-Changer.exe .\\DNS-Changer.exe && rmdir New_Update && start DNS-Changer.exe"'
            subprocess.Popen(
                command, shell=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True

        else:
            return False
    except:
        return False
