#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Usage: download-template.sh <ai_assistant> <output_path>
AI_ASSISTANT="$1"
OUTPUT_PATH="$2"

if [ -z "$AI_ASSISTANT" ] || [ -z "$OUTPUT_PATH" ]; then
    echo -e "${RED}Usage: $0 <ai_assistant> <output_path>${NC}" >&2
    exit 1
fi

echo -e "${BLUE}Downloading template for: $AI_ASSISTANT${NC}"

# Use Node.js for HTTP requests (built-in, no external dependencies)
node -e "
const https = require('https');
const fs = require('fs');

const repo = {
  owner: 'github',
  name: 'spec-kit'
};

console.log('Fetching latest release from GitHub...');

const apiOptions = {
  hostname: 'api.github.com',
  path: '/repos/' + repo.owner + '/' + repo.name + '/releases/latest',
  method: 'GET',
  headers: {
    'User-Agent': 'Spec-Kit-Downloader/1.0'
  }
};

https.get(apiOptions, (res) => {
  let data = '';

  res.on('data', (chunk) => {
    data += chunk;
  });

  res.on('end', () => {
    try {
      const release = JSON.parse(data);

      if (res.statusCode !== 200) {
        console.error('GitHub API error:', res.statusCode, release.message);
        process.exit(1);
      }

      console.log('Release:', release.tag_name);
      console.log('Published:', release.published_at);

      // Find the appropriate template asset
      const templatePattern = '$AI_ASSISTANT';
      let asset = null;

      // First try to find the exact assistant template
      for (const a of release.assets) {
        if (a.name.includes(templatePattern) && a.name.endsWith('.zip')) {
          asset = a;
          break;
        }
      }

      // If no exact match and we're looking for cursor, fallback to claude template
      if (!asset && '$AI_ASSISTANT' === 'cursor') {
        console.log('No cursor template found, using claude template as fallback...');
        for (const a of release.assets) {
          if (a.name.includes('claude') && a.name.endsWith('.zip')) {
            asset = a;
            break;
          }
        }
      }

      if (!asset) {
        console.error('No template found for assistant:', '$AI_ASSISTANT');
        console.log('Available assets:');
        release.assets.forEach(a => console.log(' -', a.name));
        process.exit(1);
      }

      console.log('Found template:', asset.name);
      console.log('Size:', (asset.size / 1024 / 1024).toFixed(2), 'MB');

      // Download the template
      console.log('Downloading...');
      const file = fs.createWriteStream('$OUTPUT_PATH');

      https.get(asset.browser_download_url, {
        headers: {
          'User-Agent': 'Spec-Kit-Downloader/1.0'
        }
      }, (downloadRes) => {
        if (downloadRes.statusCode !== 200 && downloadRes.statusCode !== 302) {
          console.error('Download failed:', downloadRes.statusCode);
          process.exit(1);
        }

        // Handle redirects
        if (downloadRes.statusCode === 302) {
          const redirectUrl = downloadRes.headers.location;
          console.log('Following redirect to:', redirectUrl);

          https.get(redirectUrl, {
            headers: {
              'User-Agent': 'Spec-Kit-Downloader/1.0'
            }
          }, (redirectRes) => {
            if (redirectRes.statusCode !== 200) {
              console.error('Redirect download failed:', redirectRes.statusCode);
              process.exit(1);
            }

            redirectRes.pipe(file);
            file.on('finish', () => {
              file.close();
              console.log('Download complete!');
            });
          }).on('error', (err) => {
            console.error('Redirect download error:', err.message);
            fs.unlink('$OUTPUT_PATH');
            process.exit(1);
          });

          return;
        }

        const totalSize = parseInt(downloadRes.headers['content-length'], 10);
        let downloaded = 0;

        downloadRes.on('data', (chunk) => {
          downloaded += chunk.length;
          const progress = ((downloaded / totalSize) * 100).toFixed(1);
          process.stdout.write('\rProgress: ' + progress + '%');
        });

        downloadRes.pipe(file);

        file.on('finish', () => {
          console.log('\nDownload complete!');
          file.close();
        });

        downloadRes.on('error', (err) => {
          console.error('Download error:', err.message);
          fs.unlink('$OUTPUT_PATH');
          process.exit(1);
        });

      }).on('error', (err) => {
        console.error('Connection error:', err.message);
        process.exit(1);
      });

    } catch (e) {
      console.error('Error parsing response:', e.message);
      process.exit(1);
    }
  });

}).on('error', (e) => {
  console.error('Error fetching release:', e.message);
  process.exit(1);
});
"

# Wait for download to complete
while [ ! -f "$OUTPUT_PATH" ]; do
    sleep 1
done

echo -e "${GREEN}Template downloaded successfully: $OUTPUT_PATH${NC}"
