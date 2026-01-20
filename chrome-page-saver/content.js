// sPageSaver - Content Script
// Extract article content from web pages

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'extractArticle') {
    try {
      const articleData = extractArticle();
      articleData.subPath = request.subPath;
      articleData.filenameTemplate = request.filenameTemplate;

      // Send to background for download
      chrome.runtime.sendMessage({
        action: 'downloadArticle',
        data: articleData
      });

      // Show notification
      showNotification('Article saved!');
    } catch (err) {
      console.error('Failed to extract article:', err);
      showNotification('Failed to save article');
    }
  }
});

function extractArticle() {
  const title = document.title || 'Untitled';
  const url = window.location.href;

  // Try multiple methods to extract article content
  let contentElement = null;

  // Method 1: Readability-style article detection
  const article = findArticleNode();
  if (article) {
    contentElement = article;
  }

  // Method 2: Common article containers
  if (!contentElement) {
    const selectors = [
      'article',
      '[role="article"]',
      '.post-content',
      '.article-content',
      '.entry-content',
      '.post-body',
      '.content',
      'main',
      '#content',
      '.markdown-body'
    ];

    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element && element.textContent.trim().length > 200) {
        contentElement = element;
        break;
      }
    }
  }

  // Method 3: Fallback to body
  if (!contentElement) {
    const body = document.body;
    if (body) {
      const clone = body.cloneNode(true);
      removeUnwantedElements(clone);
      contentElement = clone;
    }
  }

  // Convert to Markdown
  const markdown = htmlToMarkdown(contentElement);

  return {
    title,
    url,
    content: markdown
  };
}

// Convert HTML to Markdown
function htmlToMarkdown(element) {
  if (!element) return '';

  let markdown = '';
  const clone = element.cloneNode(true);

  // Process child nodes
  function processNode(node, listLevel = 0) {
    let result = '';

    if (node.nodeType === Node.TEXT_NODE) {
      const text = node.textContent;
      // Preserve text nodes that are not just whitespace
      if (text.trim()) {
        result += text;
      }
    } else if (node.nodeType === Node.ELEMENT_NODE) {
      const tag = node.tagName.toLowerCase();

      // Skip certain elements
      if (['script', 'style', 'noscript', 'iframe'].includes(tag)) {
        return '';
      }

      // Block elements
      switch (tag) {
        case 'h1':
          result += `\n# ${node.textContent.trim()}\n\n`;
          break;
        case 'h2':
          result += `\n## ${node.textContent.trim()}\n\n`;
          break;
        case 'h3':
          result += `\n### ${node.textContent.trim()}\n\n`;
          break;
        case 'h4':
          result += `\n#### ${node.textContent.trim()}\n\n`;
          break;
        case 'h5':
          result += `\n##### ${node.textContent.trim()}\n\n`;
          break;
        case 'h6':
          result += `\n###### ${node.textContent.trim()}\n\n`;
          break;
        case 'p':
          const pContent = Array.from(node.childNodes).map(n => processNode(n, listLevel)).join('');
          if (pContent.trim()) {
            result += `\n${pContent.trim()}\n\n`;
          }
          break;
        case 'br':
          result += '\n';
          break;
        case 'hr':
          result += '\n---\n\n';
          break;
        case 'img':
          const src = node.getAttribute('src') || node.getAttribute('data-src');
          const alt = node.getAttribute('alt') || '';
          if (src) {
            const fullSrc = src.startsWith('http') ? src : new URL(src, window.location.href).href;
            result += `\n![${alt}](${fullSrc})\n\n`;
          }
          break;
        case 'a':
          const href = node.getAttribute('href');
          const linkText = Array.from(node.childNodes).map(n => processNode(n, listLevel)).join('');
          if (href) {
            const fullHref = href.startsWith('http') ? href : new URL(href, window.location.href).href;
            result += `[${linkText}](${fullHref})`;
          } else {
            result += linkText;
          }
          break;
        case 'strong':
        case 'b':
          result += `**${Array.from(node.childNodes).map(n => processNode(n, listLevel)).join('')}**`;
          break;
        case 'em':
        case 'i':
          result += `*${Array.from(node.childNodes).map(n => processNode(n, listLevel)).join('')}*`;
          break;
        case 'code':
          result += `\`${node.textContent.trim()}\``;
          break;
        case 'pre':
          const code = node.querySelector('code');
          const codeText = code ? code.textContent : node.textContent;
          result += `\n\`\`\`\n${codeText.trim()}\n\`\`\`\n\n`;
          break;
        case 'blockquote':
          const quoteContent = Array.from(node.childNodes).map(n => processNode(n, listLevel)).join('');
          const lines = quoteContent.trim().split('\n');
          result += lines.map(line => `> ${line}`).join('\n') + '\n\n';
          break;
        case 'ul':
        case 'ol':
          const isOrdered = tag === 'ol';
          const items = node.querySelectorAll(':scope > li');
          items.forEach((li, idx) => {
            const prefix = isOrdered ? `${idx + 1}. ` : '- ';
            const itemContent = Array.from(li.childNodes).map(n => processNode(n, listLevel + 1)).join('').trim();
            result += `\n${'  '.repeat(listLevel)}${prefix}${itemContent}`;
          });
          result += '\n\n';
          break;
        case 'li':
          // Handled in ul/ol case
          break;
        case 'div':
        case 'section':
        case 'article':
        case 'main':
          // Process children
          result += Array.from(node.childNodes).map(n => processNode(n, listLevel)).join('');
          break;
        case 'table':
          result += convertTableToMarkdown(node);
          break;
        default:
          result += Array.from(node.childNodes).map(n => processNode(n, listLevel)).join('');
      }
    }

    return result;
  }

  markdown = processNode(clone);

  // Clean up extra whitespace
  markdown = markdown
    .replace(/\n{3,}/g, '\n\n')
    .trim();

  return markdown;
}

function convertTableToMarkdown(table) {
  const rows = Array.from(table.querySelectorAll('tr'));
  if (rows.length === 0) return '';

  let result = '\n';

  rows.forEach((row, rowIndex) => {
    const cells = Array.from(row.querySelectorAll('td, th'));
    const rowText = cells.map(cell => cell.textContent.trim()).join(' | ');
    result += `| ${rowText} |\n`;

    // Add separator after header row
    if (rowIndex === 0) {
      const separator = cells.map(() => '---').join(' | ');
      result += `| ${separator} |\n`;
    }
  });

  result += '\n';
  return result;
}

function findArticleNode() {
  // Look for the main content based on text density and structure
  const candidates = [];

  // Check common content containers
  const selectors = [
    'article',
    '[role="article"]',
    '.post-content',
    '.article-content',
    '.entry-content',
    '.post-body',
    '.content article',
    'main article'
  ];

  for (const selector of selectors) {
    const elements = document.querySelectorAll(selector);
    elements.forEach(el => {
      const score = scoreContentNode(el);
      if (score > 0) {
        candidates.push({ node: el, score });
      }
    });
  }

  // Also check divs with high text content
  const allDivs = document.querySelectorAll('div');
  allDivs.forEach(div => {
    if (div.querySelector('p') && div.textContent.trim().length > 500) {
      const score = scoreContentNode(div);
      candidates.push({ node: div, score });
    }
  });

  // Sort by score and return the best match
  candidates.sort((a, b) => b.score - a.score);
  return candidates.length > 0 ? candidates[0].node : null;
}

function scoreContentNode(node) {
  let score = 0;

  // Text content length
  const textLength = node.textContent.trim().length;
  if (textLength > 500) score += 10;
  if (textLength > 1000) score += 10;
  if (textLength > 2000) score += 10;

  // Paragraph count
  const paragraphs = node.querySelectorAll('p').length;
  score += paragraphs * 2;

  // Contains headings
  if (node.querySelector('h1, h2, h3')) score += 5;

  // Penalty for too many links (might be navigation)
  const links = node.querySelectorAll('a').length;
  if (links > textLength / 50) score -= 10;

  // Penalty for forms, inputs (interactive elements)
  if (node.querySelector('form, input, select, textarea, button')) {
    score -= 20;
  }

  return Math.max(0, score);
}

function removeUnwantedElements(container) {
  const unwantedSelectors = [
    'nav',
    'header',
    'footer',
    'aside',
    '.sidebar',
    '.navigation',
    '.menu',
    '.comments',
    '.comment-form',
    '.related-posts',
    '.share-buttons',
    '.social-share',
    'script',
    'style',
    'noscript',
    'iframe',
    '.advertisement',
    '.ad'
  ];

  unwantedSelectors.forEach(selector => {
    const elements = container.querySelectorAll(selector);
    elements.forEach(el => el.remove());
  });
}

function showNotification(message) {
  // Create a simple notification element
  const notification = document.createElement('div');
  notification.textContent = message;
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: #4CAF50;
    color: white;
    padding: 12px 24px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 999999;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 14px;
    animation: slideIn 0.3s ease-out;
  `;

  // Add animation
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
  `;
  document.head.appendChild(style);

  document.body.appendChild(notification);

  setTimeout(() => {
    notification.style.opacity = '0';
    notification.style.transition = 'opacity 0.3s';
    setTimeout(() => notification.remove(), 300);
  }, 2000);
}
