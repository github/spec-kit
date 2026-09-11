// @ts-check
import { defineConfig } from 'astro/config';

// Static build — output goes to ./dist and is uploaded to cPanel (public_html).
// Update `site` to your real domain once it is live (used for SEO / canonical URLs).
export default defineConfig({
  site: 'https://www.example.com',
  output: 'static',
  build: {
    format: 'file',
  },
});
