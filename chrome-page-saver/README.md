# sPageSaver Chrome Extension

A Chrome extension that saves web articles (including images) to your local Downloads folder with custom folder structure.

## Features

- Right-click context menu to save any article
- Popup for quick access
- Customizable save path with variables
- Customizable filename templates
- Automatic article content extraction
- Image embedding (up to 2MB per image)

## Installation

### Load as Unpacked Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `chrome-page-saver` directory
5. The extension is now installed!

## Usage

### Save an Article

**Method 1: Right-click menu**
- Right-click anywhere on a page
- Select "Save Article to Local"

**Method 2: Extension popup**
- Click the sPageSaver icon in the toolbar
- Click "Save Current Article"

### Configure Settings

1. Right-click the extension icon and select "Options"
2. Or go to `chrome://extensions/` → Click "Details" → "Extension options"

#### Save Path Variables

Customize where articles are saved using these variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `{domain}` | Website domain | `example.com` |
| `{year}` | Year (4 digits) | `2024` |
| `{month}` | Month (01-12) | `01` |
| `{day}` | Day (01-31) | `15` |
| `{date}` | Full date | `2024-01-15` |

**Default path:** `articles/{domain}/{year}/{month}/`

**Example result:** `Downloads/articles/example.com/2024/01/`

#### Filename Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{title}` | Page title | `My Article` |
| `{domain}` | Website domain | `example.com` |
| `{date}` | Save date | `2024-01-15` |
| `{datetime}` | ISO datetime | `2024-01-15T10-30-00` |

**Default template:** `{title}`

**Example result:** `My-Article.html`

## File Structure

```
chrome-page-saver/
├── manifest.json           # Extension configuration
├── background.js           # Service worker (context menu, downloads)
├── content.js              # Article extraction from pages
├── popup.html / .js        # Extension popup
├── options.html / .js      # Settings page
├── icons/
│   ├── icon.svg            # Source icon
│   ├── generate_icons.py   # Icon generation script
│   ├── icon16.png
│   ├── icon32.png
│   ├── icon48.png
│   └── icon128.png
└── README.md
```

## Permissions

The extension requires these permissions:

- **activeTab**: Access current tab content
- **contextMenus**: Add right-click menu option
- **downloads**: Save files to Downloads folder
- **storage**: Save user preferences
- **<all_urls>**: Fetch images from any website

## How It Works

1. User triggers "Save Article" (context menu or popup)
2. `content.js` scans the page for article content using:
   - Readability-style content detection
   - Common article container selectors
   - Text density scoring
3. Images are converted to base64 data URLs (embedded)
4. HTML is generated with clean styling
5. File is downloaded to configured location

## Troubleshooting

**Article content is incomplete or missing**
- Some sites use complex layouts; try highlighting the article text first, then right-click → Save

**Images not saving**
- Images larger than 2MB are skipped to avoid file bloat
- Some sites block image fetching (CORS)

**Cannot save to specific folder**
- Chrome extensions can only save to the Downloads folder
- Use subfolder variables to organize within Downloads

## Development

### Re-generate Icons

```bash
cd icons
python generate_icons.py
```

Requires: `pip install Pillow`

### Test Changes

1. Make code changes
2. Go to `chrome://extensions/`
3. Click refresh icon on sPageSaver card
4. Test on a webpage

## License

MIT
