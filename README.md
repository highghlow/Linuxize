# Linuxize
Integrate linux into windows seamlessly
## Installation
Clone this repository and then run
```
python -m pip install -r requirements.txt
python main.py
```
## Usage
```
usage: linuxize [-h] [-e [EXPORT_BINARY ...]] [-r [REMOVE_BINARY ...]] [-a] [-d] [-i IS_EXPORTED] [-l] [-u] [-n] [-k] [-f] [--remove] [command] [args ...]
```
You can use linux packages in windows by exporting them:
```
linuxize -e <package>
```
by default packages `apt` and `bash` are exported

NOTE: All new packages in /usr/bin are exported automatically

If you want to run a command without exporting it use:
```
linuxize <command> [<args> ...]
```
