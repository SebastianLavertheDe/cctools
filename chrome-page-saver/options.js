// sPageSaver - Options Page Script

const defaultSettings = {
  subPath: 'articles',
  filenameTemplate: '{title}'
};

// Load settings on page load
document.addEventListener('DOMContentLoaded', () => {
  chrome.storage.sync.get(defaultSettings, (items) => {
    document.getElementById('subPath').value = items.subPath;
    document.getElementById('filenameTemplate').value = items.filenameTemplate;
  });
});

// Handle form submission
document.getElementById('settingsForm').addEventListener('submit', (e) => {
  e.preventDefault();

  const settings = {
    subPath: document.getElementById('subPath').value.trim(),
    filenameTemplate: document.getElementById('filenameTemplate').value.trim()
  };

  // Validate
  if (!settings.subPath) {
    showStatus('Please enter a subfolder path', 'error');
    return;
  }

  if (!settings.filenameTemplate) {
    showStatus('Please enter a filename template', 'error');
    return;
  }

  // Save settings
  chrome.storage.sync.set(settings, () => {
    if (chrome.runtime.lastError) {
      showStatus('Error saving settings: ' + chrome.runtime.lastError.message, 'error');
    } else {
      showStatus('Settings saved successfully!', 'success');
    }
  });
});

// Reset to defaults
document.getElementById('resetBtn').addEventListener('click', () => {
  if (confirm('Reset all settings to default values?')) {
    document.getElementById('subPath').value = defaultSettings.subPath;
    document.getElementById('filenameTemplate').value = defaultSettings.filenameTemplate;
    chrome.storage.sync.set(defaultSettings, () => {
      showStatus('Settings reset to defaults', 'success');
    });
  }
});

function showStatus(message, type) {
  const status = document.getElementById('status');
  status.textContent = message;
  status.className = 'status ' + type;
  status.style.display = 'block';

  setTimeout(() => {
    status.style.display = 'none';
  }, 3000);
}
