import os, time, sys
import subprocess

UPDATE_FILE = "config/.updated"
AUTOEXPORT_FILE = "config/autoexport"
IGNORED_BINARIES_FILE = "config/ignored_binaries"
CONTROL_PATH = "C:/Linuxize/Control"
CONTROL_FILE = os.path.join(CONTROL_PATH, "control.py")

def main():
    print("### Linuxize Daemon by highghlow ###")

    os.chdir(os.path.split(__file__)[0])

    load_config = True

    while True:
        time.sleep(0.5)
        # Config
        if load_config or os.path.exists(UPDATE_FILE):
            print("config updated")
            if os.path.exists(UPDATE_FILE):
                os.remove(UPDATE_FILE)
            autoexport = os.path.exists(AUTOEXPORT_FILE)
            ignored_binaries = open(IGNORED_BINARIES_FILE).read().split("\n")
            load_config = False
        # Autoexport
        if not autoexport:
            continue
        installed_binaries = set(os.listdir("//wsl.localhost/linuxize/usr/bin"))
        installed_binaries.discard('')
        to_add = installed_binaries.copy()

        to_add.difference_update(ignored_binaries)

        exported_binaries = set(subprocess.check_output([sys.executable, CONTROL_FILE, "-l"]).decode("utf-8").split("\r\n"))
        exported_binaries.discard('')

        to_add.difference_update(exported_binaries)
        for binary in to_add:
            exported_binaries.add(binary)
            subprocess.check_call([sys.executable, CONTROL_FILE, "-e", binary, "-n"])
        # Autoremove
        to_remove = exported_binaries.copy()
        to_remove.difference_update(installed_binaries)
        to_remove.difference_update(ignored_binaries)
        for binary in to_remove:
            subprocess.check_call([sys.executable, CONTROL_FILE, "-r", binary, "-k", "-n"])

if __name__ == "__main__":
    main()