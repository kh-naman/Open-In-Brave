#!/usr/bin/env python3
"""Installer: finds Brave, writes config, registers the native host with Chrome."""
import os, sys, json, shutil, platform, stat

ROOT = os.path.dirname(os.path.abspath(__file__))
HOST_DIR = os.path.join(ROOT, "host")
HOST_NAME = "com.openinbrave.host"
EXT_ID = open(os.path.join(ROOT, "extension_id.txt")).read().strip()
system = platform.system()

def find_brave():
    if system == "Windows":
        cands = [
            os.path.expandvars(r"%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\BraveSoftware\Brave-Browser\Application\brave.exe"),
            os.path.expandvars(r"%LocalAppData%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        ]
        for c in cands:
            if os.path.exists(c):
                return [c]
    elif system == "Darwin":
        p = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
        if os.path.exists(p):
            return [p]
    else:
        for name in ("brave-browser", "brave", "brave-browser-stable"):
            p = shutil.which(name)
            if p:
                return [p]
    return None

brave = find_brave()
if not brave:
    p = input("Couldn't find Brave automatically. Paste the full path to brave.exe / brave: ").strip().strip('"')
    brave = [p]
print("Brave found:", brave[0])

profile = input("Brave profile folder name (e.g. 'Default' or 'Profile 1'; see brave://version -> Profile Path). "
                "Press Enter to use the last-used profile: ").strip()

with open(os.path.join(HOST_DIR, "config.json"), "w") as f:
    json.dump({"brave_cmd": brave, "profile": profile}, f, indent=2)

# Build the launcher Chrome will execute.
if system == "Windows":
    launcher = os.path.join(HOST_DIR, "host.bat")
    with open(launcher, "w") as f:
        f.write('@echo off\r\n"%s" "%s"\r\n' % (sys.executable, os.path.join(HOST_DIR, "host.py")))
else:
    launcher = os.path.join(HOST_DIR, "host.py")
    with open(launcher) as f:
        src = f.read()
    src = src.replace("#!/usr/bin/env python3", "#!" + sys.executable, 1)
    with open(launcher, "w") as f:
        f.write(src)
    os.chmod(launcher, os.stat(launcher).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

manifest = {
    "name": HOST_NAME,
    "description": "Open YouTube URLs in Brave",
    "path": launcher,
    "type": "stdio",
    "allowed_origins": ["chrome-extension://%s/" % EXT_ID],
}
manifest_path = os.path.join(HOST_DIR, HOST_NAME + ".json")
with open(manifest_path, "w") as f:
    json.dump(manifest, f, indent=2)

# Tell Chrome where the host manifest lives.
if system == "Windows":
    import winreg
    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                           r"Software\Google\Chrome\NativeMessagingHosts\%s" % HOST_NAME)
    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, manifest_path)
    print("Registered in Windows registry.")
else:
    if system == "Darwin":
        d = os.path.expanduser("~/Library/Application Support/Google/Chrome/NativeMessagingHosts")
    else:
        d = os.path.expanduser("~/.config/google-chrome/NativeMessagingHosts")
    os.makedirs(d, exist_ok=True)
    shutil.copy(manifest_path, os.path.join(d, HOST_NAME + ".json"))
    print("Copied host manifest to", d)

print("\nDone. Extension ID:", EXT_ID)
print("Now load the 'extension' folder in chrome://extensions (Developer mode -> Load unpacked).")
