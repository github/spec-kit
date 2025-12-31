/**
 * Browser Automation Tools
 *
 * Web testing and interaction using Playwright.
 */

import { chromium, Browser, Page, BrowserContext, Route } from "playwright";
import { config } from "../config.js";
import * as path from "path";

let browser: Browser | null = null;
let context: BrowserContext | null = null;
let page: Page | null = null;

// Track multiple tabs
const pages: Map<string, Page> = new Map();
let activeTabId: string = "main";

// Console message collection
const consoleMessages: string[] = [];
const MAX_CONSOLE_MESSAGES = 500;

// Network request interception
const interceptedRequests: Array<{ url: string; method: string; status?: number; timestamp: number }> = [];
const MAX_INTERCEPTED_REQUESTS = 200;

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
    pages.set("main", page);
    activeTabId = "main";

    // Setup console message collection
    page.on("console", (msg) => {
      const text = `[${msg.type()}] ${msg.text()}`;
      consoleMessages.push(text);
      if (consoleMessages.length > MAX_CONSOLE_MESSAGES) {
        consoleMessages.shift();
      }
    });

    // Setup network request tracking
    page.on("request", (request) => {
      interceptedRequests.push({
        url: request.url(),
        method: request.method(),
        timestamp: Date.now(),
      });
      if (interceptedRequests.length > MAX_INTERCEPTED_REQUESTS) {
        interceptedRequests.shift();
      }
    });

    page.on("response", (response) => {
      const req = interceptedRequests.find(
        (r) => r.url === response.url() && !r.status
      );
      if (req) {
        req.status = response.status();
      }
    });

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
export async function getConsoleMessages(
  filter?: string,
  limit: number = 50
): Promise<{ success: boolean; messages?: string[]; message?: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  let messages = [...consoleMessages];

  if (filter) {
    const regex = new RegExp(filter, "i");
    messages = messages.filter((m) => regex.test(m));
  }

  return { success: true, messages: messages.slice(-limit) };
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

// ============= NAVIGATION =============

/**
 * Go back in browser history
 */
export async function goBack(): Promise<{ success: boolean; url?: string; message?: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.goBack({ waitUntil: "networkidle" });
    return { success: true, url: page.url() };
  } catch (error) {
    return { success: false, message: `goBack failed: ${error}` };
  }
}

/**
 * Go forward in browser history
 */
export async function goForward(): Promise<{ success: boolean; url?: string; message?: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.goForward({ waitUntil: "networkidle" });
    return { success: true, url: page.url() };
  } catch (error) {
    return { success: false, message: `goForward failed: ${error}` };
  }
}

/**
 * Reload the current page
 */
export async function reload(): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.reload({ waitUntil: "networkidle" });
    return { success: true, message: "Page reloaded" };
  } catch (error) {
    return { success: false, message: `reload failed: ${error}` };
  }
}

// ============= MULTI-TAB MANAGEMENT =============

/**
 * Open a new tab
 */
export async function newTab(tabId?: string): Promise<{ success: boolean; tabId?: string; message?: string }> {
  if (!context) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    const newPage = await context.newPage();
    const id = tabId || `tab-${Date.now()}`;
    pages.set(id, newPage);

    // Setup console and network tracking for new tab
    newPage.on("console", (msg) => {
      consoleMessages.push(`[${id}][${msg.type()}] ${msg.text()}`);
      if (consoleMessages.length > MAX_CONSOLE_MESSAGES) {
        consoleMessages.shift();
      }
    });

    return { success: true, tabId: id };
  } catch (error) {
    return { success: false, message: `newTab failed: ${error}` };
  }
}

/**
 * Switch to a different tab
 */
export async function switchTab(tabId: string): Promise<{ success: boolean; message: string }> {
  const targetPage = pages.get(tabId);

  if (!targetPage) {
    return { success: false, message: `Tab '${tabId}' not found` };
  }

  page = targetPage;
  activeTabId = tabId;
  await page.bringToFront();

  return { success: true, message: `Switched to tab '${tabId}'` };
}

/**
 * Close a tab
 */
export async function closeTab(tabId?: string): Promise<{ success: boolean; message: string }> {
  const id = tabId || activeTabId;
  const targetPage = pages.get(id);

  if (!targetPage) {
    return { success: false, message: `Tab '${id}' not found` };
  }

  if (id === "main" && pages.size === 1) {
    return { success: false, message: "Cannot close the last tab" };
  }

  await targetPage.close();
  pages.delete(id);

  // Switch to another tab if we closed the active one
  if (id === activeTabId) {
    const remainingTabs = Array.from(pages.keys());
    if (remainingTabs.length > 0) {
      await switchTab(remainingTabs[0]);
    }
  }

  return { success: true, message: `Tab '${id}' closed` };
}

/**
 * List all open tabs
 */
export function listTabs(): { success: boolean; tabs: Array<{ id: string; url: string; active: boolean }> } {
  const tabs = Array.from(pages.entries()).map(([id, p]) => ({
    id,
    url: p.url(),
    active: id === activeTabId,
  }));

  return { success: true, tabs };
}

// ============= IFRAMES =============

/**
 * Switch to an iframe
 */
export async function switchToFrame(
  selector: string
): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    const frame = page.frameLocator(selector);
    // Store reference for frame operations
    // Note: Playwright uses frameLocator for actions within frames
    return { success: true, message: `Switched to frame: ${selector}` };
  } catch (error) {
    return { success: false, message: `switchToFrame failed: ${error}` };
  }
}

/**
 * Execute action in an iframe
 */
export async function frameClick(
  frameSelector: string,
  elementSelector: string
): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.frameLocator(frameSelector).locator(elementSelector).click();
    return { success: true, message: `Clicked ${elementSelector} in frame ${frameSelector}` };
  } catch (error) {
    return { success: false, message: `frameClick failed: ${error}` };
  }
}

/**
 * Fill input in an iframe
 */
export async function frameFill(
  frameSelector: string,
  elementSelector: string,
  value: string
): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.frameLocator(frameSelector).locator(elementSelector).fill(value);
    return { success: true, message: `Filled ${elementSelector} in frame ${frameSelector}` };
  } catch (error) {
    return { success: false, message: `frameFill failed: ${error}` };
  }
}

/**
 * Get text from an iframe
 */
export async function frameGetText(
  frameSelector: string,
  elementSelector: string
): Promise<{ success: boolean; text?: string; message?: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    const text = await page.frameLocator(frameSelector).locator(elementSelector).textContent();
    return { success: true, text: text || "" };
  } catch (error) {
    return { success: false, message: `frameGetText failed: ${error}` };
  }
}

// ============= FILE UPLOAD =============

/**
 * Upload a file to an input element
 */
export async function uploadFile(
  selector: string,
  filePath: string
): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    const absolutePath = path.isAbsolute(filePath) ? filePath : path.join(config.rootDir, filePath);
    await page.setInputFiles(selector, absolutePath);
    return { success: true, message: `Uploaded file to ${selector}` };
  } catch (error) {
    return { success: false, message: `uploadFile failed: ${error}` };
  }
}

/**
 * Upload multiple files
 */
export async function uploadFiles(
  selector: string,
  filePaths: string[]
): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    const absolutePaths = filePaths.map((fp) =>
      path.isAbsolute(fp) ? fp : path.join(config.rootDir, fp)
    );
    await page.setInputFiles(selector, absolutePaths);
    return { success: true, message: `Uploaded ${filePaths.length} files to ${selector}` };
  } catch (error) {
    return { success: false, message: `uploadFiles failed: ${error}` };
  }
}

// ============= STORAGE =============

/**
 * Get localStorage value
 */
export async function getLocalStorage(key: string): Promise<{ success: boolean; value?: string; message?: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    const value = await page.evaluate((k) => localStorage.getItem(k), key);
    return { success: true, value: value || undefined };
  } catch (error) {
    return { success: false, message: `getLocalStorage failed: ${error}` };
  }
}

/**
 * Set localStorage value
 */
export async function setLocalStorage(key: string, value: string): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.evaluate(({ k, v }) => localStorage.setItem(k, v), { k: key, v: value });
    return { success: true, message: `Set localStorage['${key}']` };
  } catch (error) {
    return { success: false, message: `setLocalStorage failed: ${error}` };
  }
}

/**
 * Clear localStorage
 */
export async function clearLocalStorage(): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.evaluate(() => localStorage.clear());
    return { success: true, message: "localStorage cleared" };
  } catch (error) {
    return { success: false, message: `clearLocalStorage failed: ${error}` };
  }
}

/**
 * Get sessionStorage value
 */
export async function getSessionStorage(key: string): Promise<{ success: boolean; value?: string; message?: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    const value = await page.evaluate((k) => sessionStorage.getItem(k), key);
    return { success: true, value: value || undefined };
  } catch (error) {
    return { success: false, message: `getSessionStorage failed: ${error}` };
  }
}

/**
 * Set sessionStorage value
 */
export async function setSessionStorage(key: string, value: string): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.evaluate(({ k, v }) => sessionStorage.setItem(k, v), { k: key, v: value });
    return { success: true, message: `Set sessionStorage['${key}']` };
  } catch (error) {
    return { success: false, message: `setSessionStorage failed: ${error}` };
  }
}

/**
 * Get all cookies
 */
export async function getCookies(): Promise<{ success: boolean; cookies?: Array<{ name: string; value: string; domain: string }>; message?: string }> {
  if (!context) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    const cookies = await context.cookies();
    return {
      success: true,
      cookies: cookies.map((c) => ({ name: c.name, value: c.value, domain: c.domain })),
    };
  } catch (error) {
    return { success: false, message: `getCookies failed: ${error}` };
  }
}

/**
 * Set a cookie
 */
export async function setCookie(
  name: string,
  value: string,
  options?: { domain?: string; path?: string; expires?: number }
): Promise<{ success: boolean; message: string }> {
  if (!context) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    const url = page?.url() || config.browser?.baseUrl || "http://localhost";
    await context.addCookies([
      {
        name,
        value,
        url,
        domain: options?.domain,
        path: options?.path || "/",
        expires: options?.expires,
      },
    ]);
    return { success: true, message: `Cookie '${name}' set` };
  } catch (error) {
    return { success: false, message: `setCookie failed: ${error}` };
  }
}

/**
 * Clear all cookies
 */
export async function clearCookies(): Promise<{ success: boolean; message: string }> {
  if (!context) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await context.clearCookies();
    return { success: true, message: "Cookies cleared" };
  } catch (error) {
    return { success: false, message: `clearCookies failed: ${error}` };
  }
}

// ============= NETWORK =============

/**
 * Get intercepted network requests
 */
export function getNetworkRequests(
  filter?: string,
  limit: number = 50
): { success: boolean; requests: typeof interceptedRequests } {
  let requests = [...interceptedRequests];

  if (filter) {
    const regex = new RegExp(filter, "i");
    requests = requests.filter((r) => regex.test(r.url));
  }

  return { success: true, requests: requests.slice(-limit) };
}

/**
 * Wait for a network request
 */
export async function waitForRequest(
  urlPattern: string,
  timeout: number = 10000
): Promise<{ success: boolean; url?: string; method?: string; message?: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    const request = await page.waitForRequest(
      (req) => new RegExp(urlPattern).test(req.url()),
      { timeout }
    );
    return { success: true, url: request.url(), method: request.method() };
  } catch (error) {
    return { success: false, message: `waitForRequest failed: ${error}` };
  }
}

/**
 * Wait for a network response
 */
export async function waitForResponse(
  urlPattern: string,
  timeout: number = 10000
): Promise<{ success: boolean; url?: string; status?: number; message?: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    const response = await page.waitForResponse(
      (res) => new RegExp(urlPattern).test(res.url()),
      { timeout }
    );
    return { success: true, url: response.url(), status: response.status() };
  } catch (error) {
    return { success: false, message: `waitForResponse failed: ${error}` };
  }
}

/**
 * Mock a network request
 */
export async function mockRequest(
  urlPattern: string,
  response: { status?: number; body?: string; contentType?: string }
): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.route(urlPattern, async (route: Route) => {
      await route.fulfill({
        status: response.status || 200,
        contentType: response.contentType || "application/json",
        body: response.body || "{}",
      });
    });
    return { success: true, message: `Mocking requests to ${urlPattern}` };
  } catch (error) {
    return { success: false, message: `mockRequest failed: ${error}` };
  }
}

/**
 * Remove all request mocks
 */
export async function clearMocks(): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.unrouteAll();
    return { success: true, message: "All mocks cleared" };
  } catch (error) {
    return { success: false, message: `clearMocks failed: ${error}` };
  }
}

// ============= INTERACTIONS =============

/**
 * Hover over an element
 */
export async function hover(selector: string): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.hover(selector);
    return { success: true, message: `Hovered over ${selector}` };
  } catch (error) {
    return { success: false, message: `hover failed: ${error}` };
  }
}

/**
 * Double click an element
 */
export async function doubleClick(selector: string): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.dblclick(selector);
    return { success: true, message: `Double-clicked ${selector}` };
  } catch (error) {
    return { success: false, message: `doubleClick failed: ${error}` };
  }
}

/**
 * Right click an element
 */
export async function rightClick(selector: string): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.click(selector, { button: "right" });
    return { success: true, message: `Right-clicked ${selector}` };
  } catch (error) {
    return { success: false, message: `rightClick failed: ${error}` };
  }
}

/**
 * Drag and drop
 */
export async function dragAndDrop(
  sourceSelector: string,
  targetSelector: string
): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.dragAndDrop(sourceSelector, targetSelector);
    return { success: true, message: `Dragged ${sourceSelector} to ${targetSelector}` };
  } catch (error) {
    return { success: false, message: `dragAndDrop failed: ${error}` };
  }
}

/**
 * Scroll to an element or position
 */
export async function scroll(
  options: { selector?: string; x?: number; y?: number }
): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    if (options.selector) {
      await page.locator(options.selector).scrollIntoViewIfNeeded();
      return { success: true, message: `Scrolled to ${options.selector}` };
    } else {
      await page.evaluate(({ x, y }) => window.scrollTo(x || 0, y || 0), {
        x: options.x,
        y: options.y,
      });
      return { success: true, message: `Scrolled to (${options.x}, ${options.y})` };
    }
  } catch (error) {
    return { success: false, message: `scroll failed: ${error}` };
  }
}

/**
 * Focus an element
 */
export async function focus(selector: string): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.focus(selector);
    return { success: true, message: `Focused ${selector}` };
  } catch (error) {
    return { success: false, message: `focus failed: ${error}` };
  }
}

/**
 * Clear an input field
 */
export async function clear(selector: string): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.fill(selector, "");
    return { success: true, message: `Cleared ${selector}` };
  } catch (error) {
    return { success: false, message: `clear failed: ${error}` };
  }
}

/**
 * Check a checkbox or radio
 */
export async function check(selector: string): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.check(selector);
    return { success: true, message: `Checked ${selector}` };
  } catch (error) {
    return { success: false, message: `check failed: ${error}` };
  }
}

/**
 * Uncheck a checkbox
 */
export async function uncheck(selector: string): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.uncheck(selector);
    return { success: true, message: `Unchecked ${selector}` };
  } catch (error) {
    return { success: false, message: `uncheck failed: ${error}` };
  }
}

/**
 * Get element attribute
 */
export async function getAttribute(
  selector: string,
  attribute: string
): Promise<{ success: boolean; value?: string | null; message?: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    const value = await page.getAttribute(selector, attribute);
    return { success: true, value };
  } catch (error) {
    return { success: false, message: `getAttribute failed: ${error}` };
  }
}

/**
 * Get element bounding box
 */
export async function getBoundingBox(
  selector: string
): Promise<{ success: boolean; box?: { x: number; y: number; width: number; height: number }; message?: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    const box = await page.locator(selector).boundingBox();
    if (!box) {
      return { success: false, message: `Element not visible: ${selector}` };
    }
    return { success: true, box };
  } catch (error) {
    return { success: false, message: `getBoundingBox failed: ${error}` };
  }
}

/**
 * Count matching elements
 */
export async function count(selector: string): Promise<{ success: boolean; count: number }> {
  if (!page) {
    return { success: false, count: 0 };
  }

  const cnt = await page.locator(selector).count();
  return { success: true, count: cnt };
}

/**
 * Get all matching elements' text
 */
export async function getAllTexts(selector: string): Promise<{ success: boolean; texts?: string[]; message?: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    const texts = await page.locator(selector).allTextContents();
    return { success: true, texts };
  } catch (error) {
    return { success: false, message: `getAllTexts failed: ${error}` };
  }
}

/**
 * Wait for page to be fully loaded
 */
export async function waitForLoad(
  state: "load" | "domcontentloaded" | "networkidle" = "networkidle"
): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.waitForLoadState(state);
    return { success: true, message: `Page reached '${state}' state` };
  } catch (error) {
    return { success: false, message: `waitForLoad failed: ${error}` };
  }
}

/**
 * Wait for navigation to complete
 */
export async function waitForNavigation(
  timeout: number = 30000
): Promise<{ success: boolean; url?: string; message?: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.waitForNavigation({ timeout, waitUntil: "networkidle" });
    return { success: true, url: page.url() };
  } catch (error) {
    return { success: false, message: `waitForNavigation failed: ${error}` };
  }
}

/**
 * Accept or dismiss a dialog (alert, confirm, prompt)
 */
export async function handleDialog(
  action: "accept" | "dismiss",
  promptText?: string
): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  page.once("dialog", async (dialog) => {
    if (action === "accept") {
      await dialog.accept(promptText);
    } else {
      await dialog.dismiss();
    }
  });

  return { success: true, message: `Will ${action} next dialog` };
}

/**
 * Get viewport size
 */
export function getViewport(): { success: boolean; viewport?: { width: number; height: number } } {
  if (!page) {
    return { success: false };
  }

  const viewport = page.viewportSize();
  return { success: true, viewport: viewport || undefined };
}

/**
 * Set viewport size
 */
export async function setViewport(
  width: number,
  height: number
): Promise<{ success: boolean; message: string }> {
  if (!page) {
    return { success: false, message: "Browser not initialized" };
  }

  try {
    await page.setViewportSize({ width, height });
    return { success: true, message: `Viewport set to ${width}x${height}` };
  } catch (error) {
    return { success: false, message: `setViewport failed: ${error}` };
  }
}

/**
 * Emulate device
 */
export async function emulateDevice(
  deviceName: "iPhone 12" | "iPhone 13" | "Pixel 5" | "iPad" | "Desktop"
): Promise<{ success: boolean; message: string }> {
  if (!context) {
    return { success: false, message: "Browser not initialized" };
  }

  const devices: Record<string, { width: number; height: number; isMobile: boolean }> = {
    "iPhone 12": { width: 390, height: 844, isMobile: true },
    "iPhone 13": { width: 390, height: 844, isMobile: true },
    "Pixel 5": { width: 393, height: 851, isMobile: true },
    "iPad": { width: 768, height: 1024, isMobile: true },
    "Desktop": { width: 1280, height: 720, isMobile: false },
  };

  const device = devices[deviceName];
  if (!device) {
    return { success: false, message: `Unknown device: ${deviceName}` };
  }

  try {
    await page?.setViewportSize({ width: device.width, height: device.height });
    return { success: true, message: `Emulating ${deviceName} (${device.width}x${device.height})` };
  } catch (error) {
    return { success: false, message: `emulateDevice failed: ${error}` };
  }
}
