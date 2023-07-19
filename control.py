import argparse
import os
import shutil
import subprocess
import sys

EXPORT_PATH = "C:/Linuxize/bin"
EXPORT = """
@echo off
wsl -d linuxize -- {binary} %*
"""
DAEMON_PATH = "C:/Linuxize/Daemon"
LINUXIZE_PATH = "C:/Linuxize"

UPDATE_FILE = "config/.updated"
AUTOEXPORT_FILE = "config/autoexport"
IGNORED_BINARIES_FILE = "config/ignored_binaries"

def export_binary(binary):
    with open(os.path.join(EXPORT_PATH, binary+".bat"), "w") as f:
        f.write(EXPORT.format(binary=binary))

def remove_binary(binary):
    os.remove(os.path.join(EXPORT_PATH, binary+".bat"))

def main():
    parser = argparse.ArgumentParser("linuxize")
    parser.add_argument("-e", "--export-binary", type=str, nargs="*", help="Make the binary available in windows")
    parser.add_argument("-r", "--remove-binary", type=str, nargs="*", help="Make the binary unavailable in windows and stop it from being autoexported")
    parser.add_argument("-k", "--keep-in-autoexport", action="store_true", help="Do not remove the binary from autoexport when unexporting")
    parser.add_argument("-a", "--enable-autoexport", action="store_true", help="Automatically export new binaries in /usr/bin")
    parser.add_argument("-d", "--disable-autoexport", action="store_true", help="Stop autoexporting")
    parser.add_argument("-f", "--ignore-all", action="store_true", help="Remove all installed binaries from autoexport")
    parser.add_argument("-i", "--is-exported", required=False, type=str, help="Check is the binary is exported (returns 255 if it is and 0 if it isn't)")
    parser.add_argument("-l", "--list-exported", action="store_true", help="List all exported binaries (implies -n)")
    parser.add_argument("-u", "--update-config", action="store_true", help="Send config update signal to the daemon")
    parser.add_argument("-n", "--no-banner", action="store_true", help="Do not display the author banner")
    parser.add_argument("--remove", action="store_true", help="Remove linuxize")
    parser.add_argument("command", nargs="?", type=str, help="Directly run a command in linuxize")
    parser.add_argument("args", nargs="*", type=str)
    args = parser.parse_args()

    set_args = {name for name, value in args._get_kwargs() if value != parser.get_default(name)}

    if args.keep_in_autoexport and not args.remove_binary:
        parser.error("keep-in-autoexport could only be used with remove-binary")
    
    if args.enable_autoexport and args.disable_autoexport:
        parser.error("enable-autoexport could not be used with disable-autoexport")
    
    if args.update_config and set_args.difference({"no_banner", "update_config"}):
        parser.error("update-config could not be used with anything else")
    
    if args.list_exported and set_args.difference({"no_banner", "list_exported"}):
        parser.error("list-exported could not be used with anything else")
    
    if args.is_exported and set_args.difference({"no_banner", "is_exported"}):
        parser.error("is-exported could not be used with anything else")
    
    if args.remove and set_args.difference({"no_banner", "remove"}):
        parser.error("remove could not be used with anything else")

    command = None
    
    if not sys.argv[1:]:
        command = ["sh", "-c", "\"${SHELL-bash}\""]
    
    if args.command:
        command = [args.command] + args.args

    binaries = os.listdir("//wsl.localhost/linuxize/usr/bin")
    exported_binaries = os.listdir(EXPORT_PATH)
    config_updated = args.update_config
    if os.path.exists(os.path.join(DAEMON_PATH, IGNORED_BINARIES_FILE)):
        ignored_binaries = open(os.path.join(DAEMON_PATH, IGNORED_BINARIES_FILE)).read().split("\n")
    else:
        ignored_binaries = []
        config_updated = True

    if args.list_exported:
        print(*[i[:-4] for i in exported_binaries], sep="\n")
    elif not args.no_banner:
        print("### Linuxize by highghlow ###")
    
    if args.ignore_all:
        print("adding all binaries to ignore")
        ignored_binaries += binaries
        config_updated = True

    if args.export_binary:
        for binary in args.export_binary:
            which = subprocess.Popen(["wsl", "-d", "linuxize", "--", "which", binary], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if not which.wait():
                if binary+".bat" in exported_binaries:
                    print(binary, "is already exported")
                else:
                    export_binary(binary)
                    print("exported", binary)
            else:
                print(binary, "not found")
            if binary in ignored_binaries:
                ignored_binaries.remove(binary)
                print("added", binary, "to autoexport")
                config_updated = True
    
    if args.remove_binary:
        for binary in args.remove_binary:
            if binary+".bat" in exported_binaries:
                remove_binary(binary)
                print("removed", binary)
            else:
                print(binary, "is not exported")
            if binary not in ignored_binaries and not args.keep_in_autoexport:
                ignored_binaries.append(binary)
                print("removed", binary, "from autoexport")
                config_updated = True
    
    if args.enable_autoexport:
        with open(os.path.join(DAEMON_PATH, AUTOEXPORT_FILE), "w"): pass
        print("enabled autoexport")
        config_updated = True
    elif args.disable_autoexport:
        os.remove(os.path.join(DAEMON_PATH, AUTOEXPORT_FILE))
        print("disabled autoexport")
        config_updated = True
    
    if config_updated:
        with open(os.path.join(DAEMON_PATH, UPDATE_FILE), "w"): pass
        with open(os.path.join(DAEMON_PATH, IGNORED_BINARIES_FILE), "w") as f:
            f.write("\n".join(set(ignored_binaries)))
        print("updated config")
    
    if args.is_exported:
        if args.is_exported+".bat" in exported_binaries:
            print(args.is_exported, "is exported")
            exit(255)
        else:
            print(args.is_exported, "is not exported")
            exit(0)
    
    if args.remove:
        if input("Do you want to PERMANENTLY delete linuxize and it's components? (y/N) ").lower() == "y":
            subprocess.check_call(["wsl", "--unregister", "linuxize"])
            shutil.rmtree(LINUXIZE_PATH)
            print("Removed linuxize")
    
    if command:
        proc = subprocess.Popen(["wsl", "-d", "linuxize", "--"]+command)
        if proc.wait():
            exit(proc.returncode)

if __name__ == "__main__":
    main()