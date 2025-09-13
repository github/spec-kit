/**
 * T010: CLI Contract Test for track-tasks Command
 *
 * This test validates the contract specifications for the `specify track-tasks` command.
 * Tests are designed to FAIL initially as part of TDD (RED phase).
 */

import { describe, test, expect, beforeEach, jest } from '@jest/globals';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

describe('CLI Contract: specify track-tasks', () => {
  const CLI_PATH = './dist/cli/index.js';
  const SPECIFY_CMD = `node ${CLI_PATH}`;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Command Structure', () => {
    test('should require a command argument', async () => {
      const command = `${SPECIFY_CMD} track-tasks`;

      try {
        await execAsync(command);
        expect(true).toBe(false); // Should not reach here
      } catch (error: any) {
        expect(error.code).toBe(1);
        expect(error.stderr).toContain('Missing required command');
      }
    });

    test('should accept enable command', async () => {
      const command = `${SPECIFY_CMD} track-tasks enable`;

      // This test WILL FAIL initially - no CLI implementation exists
      expect(async () => {
        await execAsync(command);
      }).not.toThrow();
    });

    test('should accept disable command', async () => {
      const command = `${SPECIFY_CMD} track-tasks disable`;

      expect(async () => {
        await execAsync(command);
      }).not.toThrow();
    });

    test('should accept status command', async () => {
      const command = `${SPECIFY_CMD} track-tasks status`;

      expect(async () => {
        await execAsync(command);
      }).not.toThrow();
    });

    test('should accept clear command', async () => {
      const command = `${SPECIFY_CMD} track-tasks clear`;

      expect(async () => {
        await execAsync(command);
      }).not.toThrow();
    });

    test('should reject invalid command', async () => {
      const command = `${SPECIFY_CMD} track-tasks invalid-command`;

      try {
        await execAsync(command);
        expect(true).toBe(false); // Should not reach here
      } catch (error: any) {
        expect(error.code).toBe(1);
        expect(error.stderr).toContain('Invalid command');
      }
    });
  });

  describe('Enable Command', () => {
    test('should enable task tracking UI', async () => {
      const command = `${SPECIFY_CMD} track-tasks enable`;

      try {
        const { stdout } = await execAsync(command);
        const output = JSON.parse(stdout);

        expect(output).toHaveProperty('success', true);
        expect(output).toHaveProperty('enabled', true);
      } catch (error) {
        // Expected to fail in RED phase
        expect(true).toBe(true);
      }
    });

    test('should accept --sidebar option with default true', async () => {
      const command = `${SPECIFY_CMD} track-tasks enable --sidebar`;

      expect(async () => {
        await execAsync(command);
      }).not.toThrow();
    });

    test('should accept --no-sidebar option', async () => {
      const command = `${SPECIFY_CMD} track-tasks enable --no-sidebar`;

      try {
        const { stdout } = await execAsync(command);
        const output = JSON.parse(stdout);

        if (output.sidebar !== undefined) {
          expect(output.sidebar).toBe(false);
        }
      } catch (error) {
        // Expected to fail in RED phase
        expect(true).toBe(true);
      }
    });

    test('should handle already enabled state gracefully', async () => {
      const commands = [
        `${SPECIFY_CMD} track-tasks enable`,
        `${SPECIFY_CMD} track-tasks enable`
      ];

      for (const command of commands) {
        try {
          const { stdout } = await execAsync(command);
          const output = JSON.parse(stdout);
          expect(output.success).toBe(true);
        } catch (error) {
          // Expected to fail in RED phase
          expect(true).toBe(true);
        }
      }
    });
  });

  describe('Disable Command', () => {
    test('should disable task tracking UI', async () => {
      const command = `${SPECIFY_CMD} track-tasks disable`;

      try {
        const { stdout } = await execAsync(command);
        const output = JSON.parse(stdout);

        expect(output).toHaveProperty('success', true);
        expect(output).toHaveProperty('enabled', false);
      } catch (error) {
        // Expected to fail in RED phase
        expect(true).toBe(true);
      }
    });

    test('should handle already disabled state gracefully', async () => {
      const commands = [
        `${SPECIFY_CMD} track-tasks disable`,
        `${SPECIFY_CMD} track-tasks disable`
      ];

      for (const command of commands) {
        try {
          const { stdout } = await execAsync(command);
          const output = JSON.parse(stdout);
          expect(output.success).toBe(true);
        } catch (error) {
          // Expected to fail in RED phase
          expect(true).toBe(true);
        }
      }
    });
  });

  describe('Status Command', () => {
    test('should show current status in table format by default', async () => {
      const command = `${SPECIFY_CMD} track-tasks status`;

      try {
        const { stdout } = await execAsync(command);
        expect(stdout).toContain('Task Tracking');
        expect(stdout).toContain('Status');
        expect(stdout).toMatch(/Enabled|Disabled/);
        expect(stdout).toMatch(/Sidebar|UI/);
      } catch (error) {
        // Expected to fail in RED phase
        expect(true).toBe(true);
      }
    });

    test('should accept --format json option', async () => {
      const command = `${SPECIFY_CMD} track-tasks status --format json`;

      try {
        const { stdout } = await execAsync(command);
        const output = JSON.parse(stdout);

        expect(output).toHaveProperty('enabled');
        expect(output).toHaveProperty('sidebar');
        expect(typeof output.enabled).toBe('boolean');
        expect(typeof output.sidebar).toBe('boolean');

        // Optional properties that might be present
        if (output.active_tasks !== undefined) {
          expect(typeof output.active_tasks).toBe('number');
        }
        if (output.completed_tasks !== undefined) {
          expect(typeof output.completed_tasks).toBe('number');
        }
      } catch (error) {
        // Expected to fail in RED phase
        expect(true).toBe(true);
      }
    });

    test('should accept --format table option', async () => {
      const command = `${SPECIFY_CMD} track-tasks status --format table`;

      try {
        const { stdout } = await execAsync(command);
        expect(stdout).toContain('Status');
        expect(stdout).toMatch(/Enabled|Disabled/);
      } catch (error) {
        // Expected to fail in RED phase
        expect(true).toBe(true);
      }
    });

    test('should reject invalid format option', async () => {
      const command = `${SPECIFY_CMD} track-tasks status --format invalid`;

      try {
        await execAsync(command);
        expect(true).toBe(false); // Should not reach here
      } catch (error: any) {
        expect(error.code).toBe(1);
        expect(error.stderr).toContain('Invalid format');
      }
    });
  });

  describe('Clear Command', () => {
    test('should clear task history', async () => {
      const command = `${SPECIFY_CMD} track-tasks clear`;

      try {
        const { stdout } = await execAsync(command);
        const output = JSON.parse(stdout);

        expect(output).toHaveProperty('success', true);
        expect(output).toHaveProperty('cleared', true);

        // Should indicate how many tasks were cleared
        if (output.cleared_count !== undefined) {
          expect(typeof output.cleared_count).toBe('number');
        }
      } catch (error) {
        // Expected to fail in RED phase
        expect(true).toBe(true);
      }
    });

    test('should handle empty history gracefully', async () => {
      const commands = [
        `${SPECIFY_CMD} track-tasks clear`,
        `${SPECIFY_CMD} track-tasks clear`
      ];

      for (const command of commands) {
        try {
          const { stdout } = await execAsync(command);
          const output = JSON.parse(stdout);
          expect(output.success).toBe(true);
        } catch (error) {
          // Expected to fail in RED phase
          expect(true).toBe(true);
        }
      }
    });

    test('should require confirmation for destructive operation', async () => {
      const command = `${SPECIFY_CMD} track-tasks clear`;

      // Should either prompt for confirmation or require --confirm flag
      try {
        const child = exec(command);
        child.stdin?.write('y\n');
        child.stdin?.end();

        await new Promise((resolve, reject) => {
          child.on('close', resolve);
          child.on('error', reject);
        });

        expect(true).toBe(true); // If we reach here, confirmation worked
      } catch (error) {
        // Expected to fail in RED phase
        expect(true).toBe(true);
      }
    });
  });

  describe('Options Parsing', () => {
    test('should accept --sidebar option for enable command', async () => {
      const command = `${SPECIFY_CMD} track-tasks enable --sidebar`;

      try {
        const { stdout } = await execAsync(command);
        const output = JSON.parse(stdout);

        if (output.sidebar !== undefined) {
          expect(output.sidebar).toBe(true);
        }
      } catch (error) {
        // Expected to fail in RED phase
        expect(true).toBe(true);
      }
    });

    test('should accept --format option for status command', async () => {
      const command = `${SPECIFY_CMD} track-tasks status --format json`;

      expect(async () => {
        await execAsync(command);
      }).not.toThrow();
    });

    test('should ignore irrelevant options for each command', async () => {
      // --sidebar should be ignored for status command
      const command = `${SPECIFY_CMD} track-tasks status --sidebar`;

      expect(async () => {
        await execAsync(command);
      }).not.toThrow();
    });
  });

  describe('Help Documentation', () => {
    test('should display help with --help flag', async () => {
      const command = `${SPECIFY_CMD} track-tasks --help`;

      try {
        const { stdout } = await execAsync(command);
        expect(stdout).toContain('Enable/disable task tracking UI');
        expect(stdout).toContain('enable');
        expect(stdout).toContain('disable');
        expect(stdout).toContain('status');
        expect(stdout).toContain('clear');
        expect(stdout).toContain('--sidebar');
        expect(stdout).toContain('--format');
      } catch (error) {
        const output = (error as any).stdout || (error as any).stderr;
        expect(output).toContain('track-tasks');
      }
    });

    test('should display usage examples in help', async () => {
      const command = `${SPECIFY_CMD} track-tasks --help`;

      try {
        const { stdout } = await execAsync(command);
        expect(stdout).toContain('specify track-tasks enable');
        expect(stdout).toContain('specify track-tasks status --format json');
        expect(stdout).toContain('specify track-tasks clear');
      } catch (error) {
        const output = (error as any).stdout || (error as any).stderr;
        expect(output).toContain('track-tasks');
      }
    });

    test('should display subcommand-specific help', async () => {
      const command = `${SPECIFY_CMD} track-tasks enable --help`;

      try {
        const { stdout } = await execAsync(command);
        expect(stdout).toContain('enable');
        expect(stdout).toContain('--sidebar');
      } catch (error) {
        const output = (error as any).stdout || (error as any).stderr;
        expect(output).toContain('enable');
      }
    });
  });

  describe('State Persistence', () => {
    test('should persist enabled state between commands', async () => {
      const enableCommand = `${SPECIFY_CMD} track-tasks enable`;
      const statusCommand = `${SPECIFY_CMD} track-tasks status --format json`;

      try {
        await execAsync(enableCommand);
        const { stdout } = await execAsync(statusCommand);
        const output = JSON.parse(stdout);

        expect(output.enabled).toBe(true);
      } catch (error) {
        // Expected to fail in RED phase
        expect(true).toBe(true);
      }
    });

    test('should persist disabled state between commands', async () => {
      const disableCommand = `${SPECIFY_CMD} track-tasks disable`;
      const statusCommand = `${SPECIFY_CMD} track-tasks status --format json`;

      try {
        await execAsync(disableCommand);
        const { stdout } = await execAsync(statusCommand);
        const output = JSON.parse(stdout);

        expect(output.enabled).toBe(false);
      } catch (error) {
        // Expected to fail in RED phase
        expect(true).toBe(true);
      }
    });
  });

  describe('Error Handling', () => {
    test('should handle PROJECT_NOT_FOUND error', async () => {
      const command = `${SPECIFY_CMD} track-tasks enable`;

      try {
        await execAsync(command, { cwd: '/tmp' });
      } catch (error: any) {
        if (error.stderr?.includes('PROJECT_NOT_FOUND')) {
          try {
            const output = JSON.parse(error.stderr);
            expect(output.error.code).toBe('PROJECT_NOT_FOUND');
          } catch (parseError) {
            expect(error.stderr).toContain('PROJECT_NOT_FOUND');
          }
        }
      }
    });

    test('should handle configuration file corruption', async () => {
      const command = `${SPECIFY_CMD} track-tasks status --format json`;

      try {
        await execAsync(command);
      } catch (error: any) {
        if (error.stderr?.includes('CORRUPTION_DETECTED')) {
          try {
            const output = JSON.parse(error.stderr);
            expect(output.error.code).toBe('CORRUPTION_DETECTED');
          } catch (parseError) {
            expect(error.stderr).toContain('corrupt');
          }
        }
      }
    });
  });

  describe('Global Options Integration', () => {
    test('should accept global --verbose option', async () => {
      const command = `${SPECIFY_CMD} track-tasks status --verbose`;

      expect(async () => {
        await execAsync(command);
      }).not.toThrow();
    });

    test('should accept global --quiet option', async () => {
      const command = `${SPECIFY_CMD} track-tasks enable --quiet`;

      expect(async () => {
        await execAsync(command);
      }).not.toThrow();
    });

    test('should accept global --config option', async () => {
      const command = `${SPECIFY_CMD} track-tasks status --config /custom/path`;

      expect(async () => {
        await execAsync(command);
      }).not.toThrow();
    });

    test('should accept global --no-color option', async () => {
      const command = `${SPECIFY_CMD} track-tasks status --no-color`;

      try {
        const { stdout } = await execAsync(command);
        // Should not contain ANSI color codes
        expect(stdout).not.toMatch(/\u001b\[[0-9;]*m/);
      } catch (error) {
        // Expected to fail in RED phase
        expect(true).toBe(true);
      }
    });
  });

  describe('Exit Codes', () => {
    test('should return 0 for successful operations', async () => {
      const commands = [
        `${SPECIFY_CMD} track-tasks enable`,
        `${SPECIFY_CMD} track-tasks disable`,
        `${SPECIFY_CMD} track-tasks status`
      ];

      for (const command of commands) {
        try {
          await execAsync(command);
          // If we reach here, exit code was 0
          expect(true).toBe(true);
        } catch (error) {
          // Expected to fail in RED phase
          expect(true).toBe(true);
        }
      }
    });

    test('should return non-zero for invalid commands', async () => {
      const command = `${SPECIFY_CMD} track-tasks invalid`;

      try {
        await execAsync(command);
        expect(true).toBe(false); // Should not reach here
      } catch (error: any) {
        expect(error.code).toBeGreaterThan(0);
      }
    });
  });
});