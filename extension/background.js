// The name of the native host. Must match the "name" in the host manifest
// that install.py creates.
const HOST = "com.openinbrave.host";

// Only allow YouTube links to be handed to Brave.
const YT = /^https:\/\/((www|m|music)\.)?youtube\.com\/|^https:\/\/youtu\.be\//;

function openInBrave(url) {
  if (!url || !YT.test(url)) {
    console.warn("Not a YouTube URL, ignoring:", url);
    return;
  }
  // Sends {url} to the native host, which launches Brave.
  chrome.runtime.sendNativeMessage(HOST, { url }, (response) => {
    if (chrome.runtime.lastError) {
      console.error("Native host error:", chrome.runtime.lastError.message);
    }
  });
}

// Add the right-click menu entry (on links and on the page itself).
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "open-in-brave",
    title: "Open in Brave",
    contexts: ["link", "page"]
  });
});

// Right-click: prefer the link under the cursor, else the current page.
chrome.contextMenus.onClicked.addListener((info) => {
  openInBrave(info.linkUrl || info.pageUrl);
});

// Toolbar button (and the Alt+B shortcut) opens the current tab's URL.
chrome.action.onClicked.addListener((tab) => openInBrave(tab.url));
