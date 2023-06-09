import os
import time
import json
import requests
import subprocess
from tqdm import tqdm
from datetime import datetime
from version import VERSION

REPO_OWNER = "aedangaming"
REPO_NAME = "DNS-Changer"

is_update_available = False
last_update_check = datetime.min
MIN_CHECK_UPDATE_INTERVAL = 300


# Check if a newer version is available
def check_Update():
    global is_update_available
    global last_update_check

    if is_update_available:
        return True

    if (
        not is_update_available
        and (datetime.now() - last_update_check).total_seconds()
        < MIN_CHECK_UPDATE_INTERVAL
    ):
        return False

    result = check_latest_release()
    last_update_check = datetime.now()

    if not result:
        return None

    if result["version"] != VERSION:
        is_update_available = True
        return True
    else:
        return False


# Get latest available software version
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


# Perfom update
def update(old_exe_filename):
    try:
        result = check_latest_release()
        download_url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases/download/{result['latest_version']}/DNS-Changer_{result['version']}.exe"
        response = requests.get(download_url, stream=True)

        if response.status_code != 200:
            return False

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
        new_exe_filename = f"{REPO_NAME}.exe"
        os.makedirs("updating", exist_ok=True)

        with open("updating\\" + new_exe_filename, "wb") as file:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                file.write(data)

        progress_bar.close()
        time.sleep(0.5)

        command = (
            f'cmd /c "ping -n 3 127.0.0.1 && del /f {old_exe_filename} '
            + f"&& move .\\updating\\{new_exe_filename} .\\{new_exe_filename} "
            + f'&& rmdir updating && start {new_exe_filename}"'
        )
        subprocess.Popen(command, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except:
        return False
