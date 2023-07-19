import argparse
import os
import shutil
import subprocess
import math
import sys
import env
try:
    from clint.textui import progress
except ImportError:
    class _fake_progressbar:
        SIZE = 50
        def bar(self, iterable, expected_size):
            iterated = 0
            for i in iterable:
                iterated += 1
                done = min(int(round(iterated / expected_size * self.SIZE)), self.SIZE)
                percent = int(math.ceil(iterated / expected_size * 100))
                print("% 3d%%[%s%s]" % (percent, '=' * done, ' ' * (self.SIZE-done)))
                yield i
    progress = _fake_progressbar()

import requests

WSL_DISTRO_PATH = "C:/Linuxize/WSL"
DAEMON_PATH = "C:/Linuxize/Daemon"
CONTROL_PATH = "C:/Linuxize/Control"
EXPORT_PATH = "C:/Linuxize/bin"

DEFAULT_EXPORT = ["apt", "bash"]

def run(command, ignorecodes=[0]):
    proc = subprocess.Popen(command, shell=isinstance(command, str))
    proc.wait()
    if proc.returncode not in ignorecodes:
        exit(proc.returncode)

def is_success(command):
    try:
        subprocess.check_call(command, shell=isinstance(command, str))
    except subprocess.CalledProcessError:
        return False
    else:
        return True

def enable_wsl():
    run("dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart", [0, 3010])
    run("dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart", [0, 3010])

def is_wsl_limbo():
    out = subprocess.check_output("dism.exe /online /get-featureinfo /featurename:Microsoft-Windows-Subsystem-Linux /English").decode(errors="ignore")
    for line in out.split("\r\n"):
        line = line.strip(" ")
        if line.startswith("State :"):
            return line.endswith("Enabled")
    print("Unable to get component status")
    exit(1)

def get_wsl_distros():
    out = subprocess.check_output("wsl --list -q") \
        .replace(b"\x00", b"") \
        .decode(errors="relace")
    return out.split("\r\n")[:-1]

def get_online_wsl_distros():
    out = subprocess.check_output("wsl --list -o") \
        .replace(b"\x00", b"") \
        .decode(errors="replace") \
        .split("\r\n") \
        [4:-1]
    final = []
    for line in out:
        first_space = line.find(" ")
        name = line[:first_space]
        long_name = line[first_space:].strip(" ")
        final.append((name, long_name))
    return final

def main():
    print("### Linuxize by highghlow ###")
    print("Checking if WSL is enabled...")
    if is_success("wsl --status"):
        print("WSL is enabled")
    else:
        if not is_wsl_limbo():
            print()
            print("WSL (Windows Subsystem Linux) is disabled")
            print("This component is required for linuxize")
            if input("Do you want to enable it? (y/N) ").lower() == "y":
                enable_wsl()
            else:
                print("Canceled.")
                exit(0)
        print()
        print("A restart is required for WSL to work")
        print("After the restart run this program again")
        if input("Do you want to restart now? (y/N) ").lower() == "y":
            run("shutdown /r /t 0")
            exit(0)
        else:
            print("Canceled.")
    print("Checking for linuxize distros...")
    distros = get_wsl_distros()
    new_install = False
    if "linuxize" in distros:
        print("Linuxize distro found")
    else:
        new_install = True
        print()
        print("You have no WSL distros installed")
        if input("Install? (Y/n) ").lower() != "n":
            print()
            os.makedirs(WSL_DISTRO_PATH, exist_ok=True)

            installer_path = None

            for folder in os.listdir("C:/Program Files/WindowsApps"):
                if "Ubuntu" in folder:
                    full_path = os.path.join("C:/Program Files/WindowsApps", folder)
                    if "install.tar.gz" in os.listdir(full_path):
                        installer_path = os.path.join(full_path, "install.tar.gz")
                        print("Found Ubuntu in Microsoft Store")
            
            if not installer_path:
                os.makedirs("temporary", exist_ok=True)

                if not os.path.exists("temporary/ubuntu.zip"):
                    print("Downloading...")
                    url = "https://aka.ms/wslubuntu"
                    r = requests.get(url, stream=True)
                    path = "temporary/ubuntu.zip"
                    with open(path, 'wb') as f:
                        total_length = int(r.headers.get('content-length'))
                        for chunk in progress.bar(r.iter_content(chunk_size=1024), expected_size=(total_length/1024) + 1): 
                            if chunk:
                                f.write(chunk)
                                f.flush()

                print("Extracting...")

                run(["powershell", "Expand-Archive temporary/ubuntu.zip temporary/ubuntu"])

                installer_path = "temporary/ubuntu/install.tar.gz"

            print("Installing...")

            run(["wsl", "--import", "linuxize", WSL_DISTRO_PATH, installer_path])
            run(["wsl", "-s", "linuxize"])
            
            print("Installed!")

    os.makedirs(DAEMON_PATH, exist_ok=True)
    os.makedirs(CONTROL_PATH, exist_ok=True)
    os.makedirs(EXPORT_PATH, exist_ok=True)
    
    print("Copying Linuxize daemon...")
    shutil.copy("daemon.py", DAEMON_PATH)

    print("Copying linuxize control...")

    shutil.copy("control.bat", os.path.join(CONTROL_PATH, "linuxize.bat"))
    shutil.copy("control.py", CONTROL_PATH)

    print("Updating PATH...")

    env.prepend_env("Path", [EXPORT_PATH, CONTROL_PATH])

    print("Initializing config...")

    if new_install:
        subprocess.check_call([sys.executable, os.path.join(CONTROL_PATH, "control.py"), "-f", "-n", "-a"])
        for binary in DEFAULT_EXPORT:
            subprocess.check_call([sys.executable, os.path.join(CONTROL_PATH, "control.py"), "-e", binary, "-n"])
    else:
        subprocess.check_call([sys.executable, os.path.join(CONTROL_PATH, "control.py"), "-u", "-n"])
    
    print("Starting up Linuxize Daemon")

    subprocess.Popen([sys.executable, os.path.join(DAEMON_PATH, "daemon.py")], cwd=DAEMON_PATH).wait()

if __name__ == "__main__":
    main()