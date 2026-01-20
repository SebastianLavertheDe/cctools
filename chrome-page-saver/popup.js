// sPageSaver - Popup Script

document.addEventListener('DOMContentLoaded', () => {
  // Quick save button
  document.getElementById('saveBtn').addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    // Get settings
    const settings = await chrome.storage.sync.get({
      subPath: 'articles',
      filenameTemplate: '{title}'
    });

    try {
      // Try sending message to content script
      await chrome.tabs.sendMessage(tab.id, {
        action: 'extractArticle',
        subPath: settings.subPath,
        filenameTemplate: settings.filenameTemplate
      });
    } catch (error) {
      // Content script not loaded, inject it first
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ['content.js']
      });

      // Retry sending message
      await chrome.tabs.sendMessage(tab.id, {
        action: 'extractArticle',
        subPath: settings.subPath,
        filenameTemplate: settings.filenameTemplate
      });
    }

    window.close();
  });

  // Options link
  document.getElementById('optionsLink').addEventListener('click', (e) => {
    e.preventDefault();
    chrome.runtime.openOptionsPage();
  });
});
