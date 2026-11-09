#!/opt/homebrew/opt/python@3.14/bin/python3.14
"""Native messaging host: receives {"url": ...} from Chrome and opens it in Brave."""
import sys, os, json, struct, subprocess, re

HERE = os.path.dirname(os.path.abspath(__file__))
YT = re.compile(r"^https://((www|m|music)\.)?youtube\.com/|^https://youtu\.be/")

def read_message():
    raw = sys.stdin.buffer.read(4)          # Chrome sends a 4-byte length first
    if len(raw) < 4:
        return None
    length = struct.unpack("<I", raw)[0]
    return json.loads(sys.stdin.buffer.read(length).decode("utf-8"))

def send_message(obj):
    data = json.dumps(obj).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("<I", len(data)) + data)
    sys.stdout.buffer.flush()

def main():
    with open(os.path.join(HERE, "config.json")) as f:
        cfg = json.load(f)

    msg = read_message() or {}
    url = msg.get("url", "")

    # Safety: never launch anything except a YouTube URL.
    if not YT.match(url):
        send_message({"ok": False, "error": "not a youtube url"})
        return

    cmd = list(cfg["brave_cmd"])            # e.g. ["C:\\...\\brave.exe"]
    if cfg.get("profile"):
        cmd.append("--profile-directory=" + cfg["profile"])
    cmd.append(url)

    kwargs = {}
    if os.name == "nt":
        kwargs["creationflags"] = 0x00000008 | 0x08000000  # DETACHED | NO_WINDOW
    subprocess.Popen(cmd, **kwargs)
    send_message({"ok": True})

if __name__ == "__main__":
    main()
