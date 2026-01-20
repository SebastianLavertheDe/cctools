// sPageSaver - Background Service Worker

// Install context menu on extension install
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'savePageArticle',
    title: 'Save Article to Local',
    contexts: ['page', 'selection']
  });
});

// Handle context menu click
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === 'savePageArticle') {
    // Get settings
    const settings = await chrome.storage.sync.get({
      subPath: 'articles',
      filenameTemplate: '{title}'
    });

    try {
      // Send message to content script to extract article
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
  }
});

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Background received message:', request.action);

  if (request.action === 'downloadArticle') {
    downloadArticle(request.data)
      .then(() => {
        console.log('Download started successfully');
        sendResponse({ success: true });
      })
      .catch(err => {
        console.error('Download failed:', err);
        sendResponse({ success: false, error: err.message });
      });
    return true; // Keep message channel open for async response
  }
});

// Download article as Markdown file
async function downloadArticle(data) {
  console.log('downloadArticle called with data:', data);

  const { content, title, url, subPath, filenameTemplate } = data;

  if (!content || content.length === 0) {
    throw new Error('No content to save');
  }

  // Generate filename
  let filename = filenameTemplate
    .replace('{title}', sanitizeFilename(title))
    .replace('{domain}', new URL(url).hostname)
    .replace('{date}', new Date().toISOString().split('T')[0])
    .replace('{datetime}', new Date().toISOString().replace(/[:.]/g, '-').split('T')[0]);

  if (!filename.endsWith('.md')) {
    filename += '.md';
  }

  // Generate sub path
  const urlObj = new URL(url);
  const now = new Date();
  const fullPath = subPath
    .replace('{domain}', urlObj.hostname)
    .replace('{year}', now.getFullYear())
    .replace('{month}', String(now.getMonth() + 1).padStart(2, '0'))
    .replace('{day}', String(now.getDate()).padStart(2, '0'))
    .replace('{date}', now.toISOString().split('T')[0]);

  const finalPath = fullPath ? `${fullPath}/${filename}` : filename;
  console.log('Final path:', finalPath);

  // Create Markdown
  const markdownContent = generateMarkdown(content, title, url);
  console.log('Markdown content length:', markdownContent.length);

  // Download file
  return new Promise((resolve, reject) => {
    chrome.downloads.download({
      url: `data:text/markdown;charset=utf-8,${encodeURIComponent(markdownContent)}`,
      filename: finalPath,
      saveAs: false
    }, (downloadId) => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
      } else {
        console.log('Download started with ID:', downloadId);
        resolve(downloadId);
      }
    });
  });
}

function generateMarkdown(content, title, url) {
  return `# ${title}

> Source: ${url}
> Saved: ${new Date().toLocaleString()}

---

${content}

---

*Saved by sPageSaver Chrome Extension*
`;
}

function escapeHtml(text) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, m => map[m]);
}

function sanitizeFilename(filename) {
  return filename
    .replace(/[<>:"/\\|?*]/g, '-')
    .replace(/\s+/g, '-')
    .substring(0, 200);
}
