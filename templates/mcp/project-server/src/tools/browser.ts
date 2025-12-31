/**
 * Browser Automation Tools
 *
 * Web testing and interaction using Playwright.
 */

import { chromium, Browser, Page, BrowserContext } from "playwright";
import { config } from "../config.js";

let browser: Browser | null = null;
let context: BrowserContext | null = null;
let page: Page | null = null;

/**
 * Initialize the browser
 */
export async function initBrowser(): Promise<{ success: boolean; message: string }> {
  if (browser) {
    return { success: true, message: "Browser already initialized" };
  }

  try {
    browser = await chromium.launch({
      headless: config.browser?.headless ?? true,
    });
    context = await browser.newContext({
      viewport: { width: 1280, height: 720 },
    });
    page = await context.newPage();

    return { success: true, message: "Browser initialized" };
  } catch (error) {
    return { success: false, message: `Failed to initialize browser: ${error}` };
  }
}

/**
 * Close the browser
 */
export async function closeBrowser(): Promise<{ success: boolean; message: string }> {
  if (!browser) {
    return { success: true, message: "Browser not running" };
  }

  try {
    await browser.close();
    browser = null;
    context = null;
    page = null;
    return { success: true, message: "Browser closed" };
  } catch (error) {
    return { success: false, message: `Failed to close browser: ${error}` };
  }
}

/**
 * Navigate to a URL
 */
export async function navigate(url: string): Promise<{ success: boolean; title?: string; message?: string }> {
  if (!page) {
    const init = await initBrowser();
    if (!init.success) return init;
  }

  try {
    // Handle relative URLs
    const fullUrl = url.startsWith("http") ? url : `${config.browser?.baseUrl || ""}${url}`;

    await page!.goto(fullUrl, { waitUntil: "networkidle" });
    const title = await page!.title();

    return { success: true, title };
  } catch (error) {
    return { success: false, message: `Navigation failed: ${error}` };
  }
}

/**
 * Take a screenshot
 */
export async function screenshot(
  selector?: string
): Promise<{ success: boolean; screenshot?: string; message?: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    let buffer: Buffer;

    if (selector) {
      const element = await page.$(selector);
      if (!element) {
        return { success: false, message: `Element not found: ${selector}` };
      }
      buffer = await element.screenshot();
    } else {
      buffer = await page.screenshot({ fullPage: true });
    }

    return { success: true, screenshot: buffer.toString("base64") };
  } catch (error) {
    return { success: false, message: `Screenshot failed: ${error}` };
  }
}

/**
 * Click an element
 */
export async function click(selector: string): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.click(selector, { timeout: 5000 });
    return { success: true, message: `Clicked: ${selector}` };
  } catch (error) {
    return { success: false, message: `Click failed: ${error}` };
  }
}

/**
 * Fill an input field
 */
export async function fill(selector: string, value: string): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.fill(selector, value, { timeout: 5000 });
    return { success: true, message: `Filled ${selector} with value` };
  } catch (error) {
    return { success: false, message: `Fill failed: ${error}` };
  }
}

/**
 * Type text (character by character, useful for autocomplete)
 */
export async function type(selector: string, text: string): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.type(selector, text, { delay: 50 });
    return { success: true, message: `Typed in ${selector}` };
  } catch (error) {
    return { success: false, message: `Type failed: ${error}` };
  }
}

/**
 * Get text content of an element
 */
export async function getText(selector: string): Promise<{ success: boolean; text?: string; message?: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    const text = await page.textContent(selector, { timeout: 5000 });
    return { success: true, text: text || "" };
  } catch (error) {
    return { success: false, message: `getText failed: ${error}` };
  }
}

/**
 * Wait for an element to appear
 */
export async function waitFor(
  selector: string,
  timeout: number = 10000
): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.waitForSelector(selector, { timeout });
    return { success: true, message: `Element found: ${selector}` };
  } catch (error) {
    return { success: false, message: `Wait failed: ${error}` };
  }
}

/**
 * Check if an element exists
 */
export async function exists(selector: string): Promise<{ success: boolean; exists: boolean }> {
  if (!page) {
    return { success: false, exists: false };
  }

  const element = await page.$(selector);
  return { success: true, exists: !!element };
}

/**
 * Get current URL
 */
export async function getCurrentUrl(): Promise<{ success: boolean; url?: string; message?: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  return { success: true, url: page.url() };
}

/**
 * Get page content (HTML)
 */
export async function getPageContent(): Promise<{ success: boolean; content?: string; message?: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    const content = await page.content();
    return { success: true, content };
  } catch (error) {
    return { success: false, message: `getPageContent failed: ${error}` };
  }
}

/**
 * Execute JavaScript in the page context
 */
export async function evaluate(script: string): Promise<{ success: boolean; result?: unknown; message?: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    const result = await page.evaluate(script);
    return { success: true, result };
  } catch (error) {
    return { success: false, message: `evaluate failed: ${error}` };
  }
}

/**
 * Get console messages from the page
 */
export async function getConsoleMessages(): Promise<{ success: boolean; messages?: string[]; message?: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  // Note: This only works if you set up console message collection beforehand
  // For real use, you'd want to collect these as they come in
  return { success: true, messages: [] };
}

/**
 * Check for JavaScript errors on the page
 */
export async function checkForErrors(): Promise<{
  success: boolean;
  hasErrors: boolean;
  errors?: string[];
  message?: string;
}> {
  if (!page) {
    return { success: false, hasErrors: false, message: "Browser not initialized" };
  }

  // Evaluate for common error indicators
  try {
    const errors = await page.evaluate(() => {
      const errorElements = document.querySelectorAll('[class*="error"], [class*="Error"]');
      return Array.from(errorElements).map((el) => el.textContent?.trim() || "");
    });

    return {
      success: true,
      hasErrors: errors.length > 0,
      errors: errors.filter(Boolean),
    };
  } catch (error) {
    return { success: false, hasErrors: false, message: `checkForErrors failed: ${error}` };
  }
}

/**
 * Select an option from a dropdown
 */
export async function select(
  selector: string,
  value: string
): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.selectOption(selector, value);
    return { success: true, message: `Selected ${value} in ${selector}` };
  } catch (error) {
    return { success: false, message: `select failed: ${error}` };
  }
}

/**
 * Press a keyboard key
 */
export async function press(key: string): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.keyboard.press(key);
    return { success: true, message: `Pressed ${key}` };
  } catch (error) {
    return { success: false, message: `press failed: ${error}` };
  }
}
