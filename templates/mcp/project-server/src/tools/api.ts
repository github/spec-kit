/**
 * API Testing Tools
 *
 * HTTP client for testing REST APIs.
 */

import { config } from "../config.js";

export interface ApiResponse {
  success: boolean;
  status?: number;
  statusText?: string;
  headers?: Record<string, string>;
  body?: unknown;
  duration?: number;
  message?: string;
}

/**
 * Make an HTTP request
 */
export async function request(
  method: string,
  endpoint: string,
  options?: {
    body?: unknown;
    headers?: Record<string, string>;
    timeout?: number;
  }
): Promise<ApiResponse> {
  const startTime = Date.now();

  // Handle relative URLs
  const url = endpoint.startsWith("http")
    ? endpoint
    : `${config.api?.baseUrl || ""}${endpoint}`;

  const headers: Record<string, string> = {
    ...config.api?.defaultHeaders,
    ...options?.headers,
  };

  try {
    const response = await fetch(url, {
      method: method.toUpperCase(),
      headers,
      body: options?.body ? JSON.stringify(options.body) : undefined,
      signal: AbortSignal.timeout(options?.timeout || 30000),
    });

    const duration = Date.now() - startTime;

    // Parse response body
    let body: unknown;
    const contentType = response.headers.get("content-type") || "";

    if (contentType.includes("application/json")) {
      body = await response.json();
    } else if (contentType.includes("text/")) {
      body = await response.text();
    } else {
      body = await response.text();
    }

    // Convert headers to object
    const responseHeaders: Record<string, string> = {};
    response.headers.forEach((value, key) => {
      responseHeaders[key] = value;
    });

    return {
      success: response.ok,
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
      body,
      duration,
    };
  } catch (error) {
    return {
      success: false,
      message: `Request failed: ${error}`,
      duration: Date.now() - startTime,
    };
  }
}

/**
 * GET request
 */
export async function get(
  endpoint: string,
  options?: { headers?: Record<string, string>; timeout?: number }
): Promise<ApiResponse> {
  return request("GET", endpoint, options);
}

/**
 * POST request
 */
export async function post(
  endpoint: string,
  body?: unknown,
  options?: { headers?: Record<string, string>; timeout?: number }
): Promise<ApiResponse> {
  return request("POST", endpoint, { ...options, body });
}

/**
 * PUT request
 */
export async function put(
  endpoint: string,
  body?: unknown,
  options?: { headers?: Record<string, string>; timeout?: number }
): Promise<ApiResponse> {
  return request("PUT", endpoint, { ...options, body });
}

/**
 * PATCH request
 */
export async function patch(
  endpoint: string,
  body?: unknown,
  options?: { headers?: Record<string, string>; timeout?: number }
): Promise<ApiResponse> {
  return request("PATCH", endpoint, { ...options, body });
}

/**
 * DELETE request
 */
export async function del(
  endpoint: string,
  options?: { headers?: Record<string, string>; timeout?: number }
): Promise<ApiResponse> {
  return request("DELETE", endpoint, options);
}

/**
 * Health check - verify an endpoint is reachable
 */
export async function healthCheck(
  url: string,
  expectedStatus: number = 200
): Promise<{ success: boolean; healthy: boolean; status?: number; latency?: number; message?: string }> {
  const startTime = Date.now();

  try {
    const response = await fetch(url, {
      method: "GET",
      signal: AbortSignal.timeout(10000),
    });

    const latency = Date.now() - startTime;
    const healthy = response.status === expectedStatus;

    return {
      success: true,
      healthy,
      status: response.status,
      latency,
      message: healthy ? "Service is healthy" : `Expected ${expectedStatus}, got ${response.status}`,
    };
  } catch (error) {
    return {
      success: false,
      healthy: false,
      latency: Date.now() - startTime,
      message: `Health check failed: ${error}`,
    };
  }
}

/**
 * Test an API endpoint against expected values
 */
export async function testEndpoint(
  method: string,
  endpoint: string,
  options?: {
    body?: unknown;
    headers?: Record<string, string>;
    expectedStatus?: number;
    expectedBody?: unknown;
    expectedHeaders?: Record<string, string>;
  }
): Promise<{
  success: boolean;
  passed: boolean;
  response?: ApiResponse;
  failures?: string[];
}> {
  const response = await request(method, endpoint, {
    body: options?.body,
    headers: options?.headers,
  });

  const failures: string[] = [];

  // Check status
  if (options?.expectedStatus !== undefined) {
    if (response.status !== options.expectedStatus) {
      failures.push(`Status: expected ${options.expectedStatus}, got ${response.status}`);
    }
  }

  // Check headers
  if (options?.expectedHeaders) {
    for (const [key, value] of Object.entries(options.expectedHeaders)) {
      const actual = response.headers?.[key.toLowerCase()];
      if (actual !== value) {
        failures.push(`Header '${key}': expected '${value}', got '${actual}'`);
      }
    }
  }

  // Check body (deep equality for objects)
  if (options?.expectedBody !== undefined) {
    const bodyMatch = JSON.stringify(response.body) === JSON.stringify(options.expectedBody);
    if (!bodyMatch) {
      failures.push(`Body mismatch`);
    }
  }

  return {
    success: true,
    passed: failures.length === 0,
    response,
    failures: failures.length > 0 ? failures : undefined,
  };
}

/**
 * Run multiple API tests
 */
export async function runTests(
  tests: Array<{
    name: string;
    method: string;
    endpoint: string;
    body?: unknown;
    expectedStatus?: number;
  }>
): Promise<{
  success: boolean;
  total: number;
  passed: number;
  failed: number;
  results: Array<{ name: string; passed: boolean; message?: string }>;
}> {
  const results: Array<{ name: string; passed: boolean; message?: string }> = [];

  for (const test of tests) {
    const result = await testEndpoint(test.method, test.endpoint, {
      body: test.body,
      expectedStatus: test.expectedStatus,
    });

    results.push({
      name: test.name,
      passed: result.passed,
      message: result.failures?.join("; "),
    });
  }

  const passed = results.filter((r) => r.passed).length;

  return {
    success: true,
    total: tests.length,
    passed,
    failed: tests.length - passed,
    results,
  };
}
