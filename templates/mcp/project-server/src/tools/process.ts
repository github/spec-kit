/**
 * Process Management Tools
 *
 * Start, stop, and monitor services defined in the project configuration.
 */

import { spawn, ChildProcess } from "child_process";
import { promisify } from "util";
import treeKill from "tree-kill";
import { config, ServiceConfig } from "../config.js";

const treeKillAsync = promisify(treeKill);

// Track running processes
const runningProcesses: Map<string, ChildProcess> = new Map();
const processLogs: Map<string, string[]> = new Map();

const MAX_LOG_LINES = 1000;

export interface ProcessStatus {
  name: string;
  running: boolean;
  pid?: number;
  uptime?: number;
  healthStatus?: "healthy" | "unhealthy" | "unknown";
}

/**
 * Start a service by name
 */
export async function startService(serviceName: string): Promise<{ success: boolean; message: string }> {
  const service = config.services.find((s) => s.name === serviceName);

  if (!service) {
    return { success: false, message: `Service '${serviceName}' not found in configuration` };
  }

  if (runningProcesses.has(serviceName)) {
    return { success: false, message: `Service '${serviceName}' is already running` };
  }

  // Check dependencies
  if (service.dependsOn) {
    for (const dep of service.dependsOn) {
      if (!runningProcesses.has(dep)) {
        return { success: false, message: `Dependency '${dep}' is not running. Start it first.` };
      }
    }
  }

  const cwd = service.cwd ? `${config.rootDir}/${service.cwd}` : config.rootDir;

  const child = spawn(service.command, [], {
    cwd,
    shell: true,
    env: { ...process.env, ...service.env },
    stdio: ["ignore", "pipe", "pipe"],
  });

  // Initialize log buffer
  processLogs.set(serviceName, []);

  // Capture stdout
  child.stdout?.on("data", (data) => {
    const lines = data.toString().split("\n").filter(Boolean);
    const logs = processLogs.get(serviceName) || [];
    logs.push(...lines.map((l: string) => `[stdout] ${l}`));
    if (logs.length > MAX_LOG_LINES) {
      logs.splice(0, logs.length - MAX_LOG_LINES);
    }
    processLogs.set(serviceName, logs);
  });

  // Capture stderr
  child.stderr?.on("data", (data) => {
    const lines = data.toString().split("\n").filter(Boolean);
    const logs = processLogs.get(serviceName) || [];
    logs.push(...lines.map((l: string) => `[stderr] ${l}`));
    if (logs.length > MAX_LOG_LINES) {
      logs.splice(0, logs.length - MAX_LOG_LINES);
    }
    processLogs.set(serviceName, logs);
  });

  // Handle process exit
  child.on("exit", (code) => {
    runningProcesses.delete(serviceName);
    const logs = processLogs.get(serviceName) || [];
    logs.push(`[system] Process exited with code ${code}`);
    processLogs.set(serviceName, logs);
  });

  runningProcesses.set(serviceName, child);

  // Wait for health check if configured
  if (service.healthCheck) {
    const healthy = await waitForHealth(service, service.healthCheck.timeout || 30000);
    if (!healthy) {
      return {
        success: true,
        message: `Service '${serviceName}' started (PID: ${child.pid}) but health check failed`,
      };
    }
  }

  return { success: true, message: `Service '${serviceName}' started (PID: ${child.pid})` };
}

/**
 * Stop a service by name
 */
export async function stopService(serviceName: string): Promise<{ success: boolean; message: string }> {
  const child = runningProcesses.get(serviceName);

  if (!child || !child.pid) {
    return { success: false, message: `Service '${serviceName}' is not running` };
  }

  try {
    await treeKillAsync(child.pid, "SIGTERM");
    runningProcesses.delete(serviceName);
    return { success: true, message: `Service '${serviceName}' stopped` };
  } catch (error) {
    return { success: false, message: `Failed to stop '${serviceName}': ${error}` };
  }
}

/**
 * Stop all running services
 */
export async function stopAllServices(): Promise<{ success: boolean; stopped: string[]; failed: string[] }> {
  const stopped: string[] = [];
  const failed: string[] = [];

  for (const [name] of runningProcesses) {
    const result = await stopService(name);
    if (result.success) {
      stopped.push(name);
    } else {
      failed.push(name);
    }
  }

  return { success: failed.length === 0, stopped, failed };
}

/**
 * Get status of all services
 */
export function getServicesStatus(): ProcessStatus[] {
  return config.services.map((service) => {
    const child = runningProcesses.get(service.name);
    return {
      name: service.name,
      running: !!child,
      pid: child?.pid,
      healthStatus: child ? "unknown" : undefined,
    };
  });
}

/**
 * Get logs for a service
 */
export function getServiceLogs(
  serviceName: string,
  lines: number = 50,
  filter?: string
): { success: boolean; logs?: string[]; message?: string } {
  const logs = processLogs.get(serviceName);

  if (!logs) {
    return { success: false, message: `No logs found for '${serviceName}'` };
  }

  let filteredLogs = logs;
  if (filter) {
    const regex = new RegExp(filter, "i");
    filteredLogs = logs.filter((l) => regex.test(l));
  }

  return { success: true, logs: filteredLogs.slice(-lines) };
}

/**
 * Check health of a service
 */
export async function checkHealth(serviceName: string): Promise<{ healthy: boolean; status?: number; message?: string }> {
  const service = config.services.find((s) => s.name === serviceName);

  if (!service?.healthCheck) {
    return { healthy: false, message: "No health check configured for this service" };
  }

  try {
    const response = await fetch(service.healthCheck.url, {
      method: "GET",
      signal: AbortSignal.timeout(5000),
    });

    const expectedStatus = service.healthCheck.expectedStatus || 200;
    const healthy = response.status === expectedStatus;

    return { healthy, status: response.status };
  } catch (error) {
    return { healthy: false, message: String(error) };
  }
}

/**
 * Wait for a service to become healthy
 */
async function waitForHealth(service: ServiceConfig, timeout: number): Promise<boolean> {
  if (!service.healthCheck) return true;

  const startTime = Date.now();
  const interval = 1000;

  while (Date.now() - startTime < timeout) {
    try {
      const response = await fetch(service.healthCheck.url, {
        method: "GET",
        signal: AbortSignal.timeout(5000),
      });

      if (response.status === (service.healthCheck.expectedStatus || 200)) {
        return true;
      }
    } catch {
      // Service not ready yet
    }

    await new Promise((resolve) => setTimeout(resolve, interval));
  }

  return false;
}

/**
 * Start Docker services
 */
export async function startDocker(): Promise<{ success: boolean; message: string }> {
  if (!config.docker) {
    return { success: false, message: "No Docker configuration found" };
  }

  const composeFile = config.docker.composeFile || "docker-compose.yml";
  const services = config.docker.services?.join(" ") || "";

  return new Promise((resolve) => {
    const child = spawn(`docker compose -f ${composeFile} up -d ${services}`, [], {
      cwd: config.rootDir,
      shell: true,
      stdio: ["ignore", "pipe", "pipe"],
    });

    let output = "";
    child.stdout?.on("data", (data) => (output += data.toString()));
    child.stderr?.on("data", (data) => (output += data.toString()));

    child.on("exit", (code) => {
      if (code === 0) {
        resolve({ success: true, message: `Docker services started: ${services || "all"}` });
      } else {
        resolve({ success: false, message: `Docker failed: ${output}` });
      }
    });
  });
}

/**
 * Stop Docker services
 */
export async function stopDocker(): Promise<{ success: boolean; message: string }> {
  if (!config.docker) {
    return { success: false, message: "No Docker configuration found" };
  }

  const composeFile = config.docker.composeFile || "docker-compose.yml";

  return new Promise((resolve) => {
    const child = spawn(`docker compose -f ${composeFile} down`, [], {
      cwd: config.rootDir,
      shell: true,
      stdio: ["ignore", "pipe", "pipe"],
    });

    child.on("exit", (code) => {
      resolve({
        success: code === 0,
        message: code === 0 ? "Docker services stopped" : "Failed to stop Docker services",
      });
    });
  });
}
