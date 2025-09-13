/**
 * Contract Test: Hello CLI Command
 * Tests the CLI command interface contract for hello command
 * This test MUST fail initially (RED phase of TDD)
 */

import { execSync } from 'child_process';

describe('Hello Command Contract', () => {
  const CLI_PATH = './dist/cli.js'; // Adjust based on build output
  const TIMEOUT = 5000; // 5 second timeout for CLI execution

  describe('specify hello command', () => {
    it('should execute successfully with exit code 0', () => {
      // This will fail initially as hello command doesn't exist yet
      expect(() => {
        execSync(`node ${CLI_PATH} hello`, {
          timeout: TIMEOUT,
          encoding: 'utf8'
        });
      }).not.toThrow();
    });

    it('should output greeting message to stdout', () => {
      const output = execSync(`node ${CLI_PATH} hello`, {
        timeout: TIMEOUT,
        encoding: 'utf8'
      });

      // Contract: Must output non-empty greeting message
      expect(output).toBeDefined();
      expect(typeof output).toBe('string');
      expect(output.trim().length).toBeGreaterThan(0);
      expect(output.toLowerCase()).toContain('hello');
    });

    it('should complete execution within performance constraint', () => {
      const startTime = Date.now();
      execSync(`node ${CLI_PATH} hello`, {
        timeout: TIMEOUT,
        encoding: 'utf8'
      });
      const endTime = Date.now();

      // Contract: CLI execution should be fast (<1000ms total)
      expect(endTime - startTime).toBeLessThan(1000);
    });

    it('should support --help flag', () => {
      const output = execSync(`node ${CLI_PATH} hello --help`, {
        timeout: TIMEOUT,
        encoding: 'utf8'
      });

      // Contract: Must provide help information
      expect(output).toContain('hello');
      expect(output.toLowerCase()).toMatch(/help|usage|description/);
    });

    it('should be consistent across multiple executions', () => {
      const output1 = execSync(`node ${CLI_PATH} hello`, {
        timeout: TIMEOUT,
        encoding: 'utf8'
      });
      const output2 = execSync(`node ${CLI_PATH} hello`, {
        timeout: TIMEOUT,
        encoding: 'utf8'
      });

      // Contract: Should produce consistent output structure
      expect(typeof output1).toBe(typeof output2);
      expect(output1.length).toBeGreaterThan(0);
      expect(output2.length).toBeGreaterThan(0);
    });

    it('should handle no additional arguments gracefully', () => {
      // Contract: Command should work with no args beyond "hello"
      expect(() => {
        execSync(`node ${CLI_PATH} hello`, {
          timeout: TIMEOUT,
          encoding: 'utf8'
        });
      }).not.toThrow();
    });
  });
});