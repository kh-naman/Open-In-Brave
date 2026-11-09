# Open in Brave

I wanted a way to jump from a YouTube video in Chrome to the same video in Brave, without copying the link and pasting it into another browser. This is a small Chrome extension that does that. Click a button, press a shortcut, or right-click a link, and Brave opens it in the profile you pick.

It's not affiliated with Google or Brave.

## Why there are two parts

Chrome extensions are sandboxed, so they can't start other programs. An extension can't launch Brave on its own.

The way around it is native messaging. The extension sends the URL to Chrome, Chrome starts a small Python script on your computer, and that script opens Brave. So the project is:

- `extension/`, the Chrome extension. It notices your click and hands over the URL.
- `host/`, the Python script. It receives the URL and launches Brave.
- `install.py`, which tells Chrome the script exists and is allowed to be used by this extension.

You run the installer once and load the extension once. After that you shouldn't need to touch anything.

## What you need

Chrome, Brave, and Python 3. On a Mac, run `python3 --version` in Terminal. If it prints a version you're fine. If it offers to install developer tools, say yes. On Windows, install Python from python.org and tick "Add Python to PATH". Windows, macOS and Linux all work, though I've mostly tested on a Mac.

## Installing

Put the folder somewhere permanent before you do anything else. Chrome will keep pointing at it, so if you move it later you have to run the installer again. On a Mac, don't use Downloads, Desktop or Documents. macOS can stop programs started by Chrome from reading files in those places. Something like `~/open-in-brave` is fine.

If you're setting this up on a second computer, unzip a fresh copy there. Don't copy over a folder that's already been installed, because the files the installer generates contain paths from the first machine.

Run the installer from inside the folder:

```
python3 install.py
```

(`python install.py` on Windows.)

It looks for Brave and asks which profile to use. To find the profile name, open `brave://version` in Brave and look at the end of the Profile Path, which will be something like `Default` or `Profile 1`. If you just press Enter, Brave uses whichever profile you used last.

Then in Chrome:

1. Go to `chrome://extensions` and turn on Developer mode.
2. Click Load unpacked and choose the `extension` folder.
3. The extension's ID should be `lanpecpfhmjcpdngpnjgkoegloefenok`. If it's different, you've loaded some other copy.

Chrome will probably nag you about developer mode extensions every time it starts. That's expected for extensions loaded this way.

## Using it

On a YouTube page you can click the toolbar icon, press Alt+B (Option+B on a Mac), or right-click a link or thumbnail and pick "Open in Brave". Right-clicking the page itself opens the current page.

If you don't like the shortcut, change it at `chrome://extensions/shortcuts`.

Only YouTube links get through (youtube.com, m.youtube.com, music.youtube.com and youtu.be). If you want other sites, the pattern lives in two places, `extension/background.js` and `host/host.py`. Change both. The host checks the URL again on purpose, so it doesn't have to trust whatever sent it.

## Changing the profile later

Open `host/config.json` and edit the `profile` value. No need to reinstall.

## If it doesn't work

Start by finding out what Chrome is complaining about. Go to `chrome://extensions`, click "service worker" on the extension, and press the button on a YouTube page. The error shows up in that console.

"Specified native messaging host not found" means Chrome can't find the registration. Run `install.py` again and reload the extension. Also check that you moved nothing and that you're on regular Chrome, not Chromium or Edge.

"Access to the specified native messaging host is forbidden" means the extension ID doesn't match. Check it against the one above.

"Native host has exited" means the script started and then crashed. If it crashed from a Python error, the details are in `host/error.log`. The usual reasons are a wrong Brave path in `config.json`, a folder in one of the protected macOS locations, a folder copied from another computer, or a `python3` that's just a placeholder with no real Python behind it. Fixing the cause and running `install.py` again clears most of these.

If you get nothing at all in the console, the click isn't reaching the extension. Check the shortcut, and make sure the page really is a YouTube one.

You can also test the script without Chrome involved. From the project folder on a Mac or Linux:

```
python3 -c "
import subprocess, struct, json
m = json.dumps({'url':'https://www.youtube.com/watch?v=dQw4w9WgXcQ'}).encode()
p = subprocess.run(['./host/launcher.sh'], input=struct.pack('<I', len(m)) + m, capture_output=True)
print(p.returncode, p.stdout, p.stderr.decode())
"
```

On Windows, use `python` and `host\host.bat`. If Brave opens and you see `{"ok": true}` in the output, the script is fine and the problem is on the Chrome side. If you see a Python error, that's your answer.

## How the pieces talk

When you click, `background.js` checks the URL and calls `chrome.runtime.sendNativeMessage`. Chrome looks up `com.openinbrave.host`, confirms the extension is on the allow list, and starts the host. It writes the URL to the host's stdin as a 4-byte length followed by JSON, which is how Chrome frames every native message. The host reads it, checks the URL again, reads `config.json`, and starts Brave with the profile flag and the URL. It replies `{"ok": true}` and exits. Chrome starts a new copy for every click.

If Brave is already open, the new Brave process hands the URL to the running one and quits, so you just get a new tab. Otherwise it becomes the browser. The host starts Brave detached so it doesn't get closed when the host exits.

The installer registers the host in different places per system. On Windows that's a registry key under `HKCU\Software\Google\Chrome\NativeMessagingHosts`. On macOS it's `~/Library/Application Support/Google/Chrome/NativeMessagingHosts/`, and on Linux `~/.config/google-chrome/NativeMessagingHosts/`. It also writes a small launcher (`launcher.sh` or `host.bat`) with the full path of the Python it ran under, so Chrome doesn't have to guess.

The extension ID is fixed by the `key` field in `manifest.json`. Without it, Chrome would generate a different ID for every folder location and the allow list would never match.

## Files

```
extension/manifest.json     permissions, shortcut, fixed ID
extension/background.js     listens for clicks, sends the URL
host/host.py                the script that launches Brave
install.py                  setup and registration
extension_id.txt            the ID, read by install.py
```

The installer also creates `host/config.json`, `host/launcher.sh` (or `host.bat`) and `host/com.openinbrave.host.json`. `host/error.log` appears only if the script crashes. None of those are in the repo.

## Is it safe

It does very little. The host only accepts the one extension's ID, checks every URL against an anchored pattern (so `youtube.com.evil.com` doesn't pass), and never uses a shell. The worst it can do is open a YouTube link in Brave. Nothing goes over the network.

## Uninstalling

Remove the extension from `chrome://extensions`, then delete the registration:

- Windows: `reg delete "HKCU\Software\Google\Chrome\NativeMessagingHosts\com.openinbrave.host" /f`
- macOS: `rm ~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts/com.openinbrave.host.json`
- Linux: `rm ~/.config/google-chrome/NativeMessagingHosts/com.openinbrave.host.json`

Then delete the folder.

## Things people ask

Why not a local web server instead? Because it would have to be running all the time and any website could try to talk to it. Native messaging only starts the script when needed, and Chrome only lets the listed extension use it.

Does it work in Edge or Firefox? Not as is. The installer only registers with Chrome, and other browsers look for the registration somewhere else.

Can it go on the Chrome Web Store? The extension could, but the store can't install the Python host, so users would still need to install that themselves. The store would also give the extension a different ID, which means updating the allow list.

## License

MIT, see LICENSE.
