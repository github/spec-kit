# Coaching Website

A fast, static personal website for a professional coach, built with [Astro](https://astro.build/).

## Edit your content

All text, contact details, services and testimonials live in **one file**:

```
src/data/site.ts
```

Open it and replace the placeholder values (name, email, WhatsApp number,
social links, services, testimonials). No coding required for content changes.

To replace the two "Add your photo here" placeholders with a real image:
edit `src/pages/index.astro`, put your image in the `public/` folder, and
swap the placeholder block for `<img src="/your-photo.jpg" alt="..." />`.

## Run locally

```bash
npm install
npm run dev      # http://localhost:4321
```

## Build for production

```bash
npm run build
```

This generates a fully static site in the **`dist/`** folder.

## Deploy to cPanel (Tasjeel hosting)

1. Run `npm run build` locally.
2. Open cPanel → **File Manager**.
3. Go into `public_html` (or the subfolder for your domain).
4. Upload **everything inside `dist/`** (not the `dist` folder itself),
   including the hidden `.htaccess` file.
   - Tip: zip the contents of `dist/`, upload the zip, then "Extract" in
     File Manager.
5. Visit your domain — the site is live.

### Notes
- Enable SSL in cPanel (AutoSSL / Let's Encrypt), then uncomment the
  "Force HTTPS" block at the top of `.htaccess` (it is included in `dist/`
  automatically from `public/.htaccess`).
- Update `site:` in `astro.config.mjs` to your real domain for correct
  SEO/social metadata, then rebuild.
- The contact form uses a simple `mailto:` action. For a more reliable
  form, connect it later to a free service like Formspree or your cPanel
  email — ask and this can be wired up.
