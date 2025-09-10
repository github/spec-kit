#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const https = require('https');
const { execSync } = require('child_process');

// ANSI color codes (no external dependencies)
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m'
};

function colorize(text, color) {
  return `${color}${text}${colors.reset}`;
}

function showBanner() {
  const banner = `
███████╗██████╗ ███████╗ ██████╗██╗███████╗██╗   ██╗
██╔════╝██╔══██╗██╔════╝██╔════╝██║██╔════╝╚██╗ ██╔╝
███████╗██████╔╝█████╗  ██║     ██║█████╗   ╚████╔╝
╚════██║██╔═══╝ ██╔══╝  ██║     ██║██╔══╝    ╚██╔╝
███████║██║     ███████╗╚██████╗██║██║        ██║
╚══════╝╚═╝     ╚══════╝ ╚═════╝╚═╝╚═╝        ╚═╝
`;

  console.log(colorize(banner, colors.cyan));
  console.log(colorize('Spec-Driven Development Toolkit', colors.yellow));
  console.log();
}

// Parse CLI arguments (vanilla Node.js, no external dependencies)
function parseArgs() {
  const args = process.argv.slice(2);
  const parsed = {
    command: null,
    projectName: null,
    here: false,
    help: false,
    ai: null,
    noGit: false,
    ignoreAgentTools: false
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    switch (arg) {
      case 'init':
        parsed.command = 'init';
        if (i + 1 < args.length && !args[i + 1].startsWith('-')) {
          parsed.projectName = args[i + 1];
          i++; // Skip next arg as it's the project name
        }
        break;
      case '--here':
        parsed.here = true;
        break;
      case '--help':
      case '-h':
        parsed.help = true;
        break;
      case '--ai':
        if (i + 1 < args.length) {
          parsed.ai = args[i + 1];
          i++; // Skip next arg as it's the AI value
        }
        break;
      case '--no-git':
        parsed.noGit = true;
        break;
      case '--ignore-agent-tools':
        parsed.ignoreAgentTools = true;
        break;
    }
  }

  return parsed;
}

function showHelp() {
  console.log('Usage: specify init [PROJECT_NAME] [OPTIONS]');
  console.log();
  console.log('Initialize a new Specify project from template');
  console.log();
  console.log('Arguments:');
  console.log('  PROJECT_NAME    Name for your new project directory');
  console.log();
  console.log('Options:');
  console.log('  --here              Initialize project in current directory');
  console.log('  --ai <assistant>    AI assistant: cursor (default)');
  console.log('  --no-git           Skip git repository initialization');
  console.log('  --ignore-agent-tools  Skip AI tool checks');
  console.log('  --help, -h          Show this help message');
  console.log();
  console.log('Examples:');
  console.log('  specify init my-project');
  console.log('  specify init --here');
  console.log('  specify init my-project --ai cursor');
}

function checkPrerequisites() {
  console.log(colorize('Checking prerequisites...', colors.cyan));

  // Check Node.js version
  const nodeVersion = process.versions.node;
  const majorVersion = parseInt(nodeVersion.split('.')[0]);
  if (majorVersion < 16) {
    console.log(colorize(`✗ Node.js ${nodeVersion} detected. Requires Node.js 16+`, colors.red));
    process.exit(1);
  }
  console.log(colorize(`✓ Node.js ${nodeVersion}`, colors.green));

  // Check git
  try {
    execSync('git --version', { stdio: 'pipe' });
    console.log(colorize('✓ Git available', colors.green));
    return true;
  } catch (error) {
    console.log(colorize('✗ Git not found', colors.yellow));
    console.log(colorize('  Install from: https://git-scm.com/downloads', colors.white));
    return false;
  }
}

function selectAIAssistant() {
  console.log();
  console.log('Select your AI assistant:');
  console.log('1. Cursor (recommended)');
  console.log('2. Other (Claude, Gemini, Copilot)');
  process.stdout.write('Enter choice (1-2): ');

  return new Promise((resolve) => {
    process.stdin.once('data', (data) => {
      const choice = data.toString().trim();
      process.stdin.pause();

      if (choice === '1') {
        resolve('cursor');
      } else {
        resolve('other');
      }
    });
  });
}

async function initProject(args) {
  showBanner();

  // Validate arguments
  if (args.here && args.projectName) {
    console.log(colorize('Error: Cannot specify both project name and --here flag', colors.red));
    process.exit(1);
  }

  if (!args.here && !args.projectName) {
    console.log(colorize('Error: Must specify either a project name or use --here flag', colors.red));
    console.log();
    showHelp();
    process.exit(1);
  }

  // Determine project directory
  const projectName = args.here ? path.basename(process.cwd()) : args.projectName;
  const projectPath = args.here ? process.cwd() : path.resolve(args.projectName);

  // Check if project directory already exists (for new projects)
  if (!args.here && fs.existsSync(projectPath)) {
    console.log(colorize(`Error: Directory '${args.projectName}' already exists`, colors.red));
    process.exit(1);
  }

  console.log(colorize(`Initializing project: ${projectName}`, colors.cyan));
  if (args.here) {
    console.log(colorize(`Location: ${projectPath}`, colors.white));
  }
  console.log();

  // Check prerequisites
  const gitAvailable = checkPrerequisites();
  if (!gitAvailable && !args.noGit) {
    console.log(colorize('Git not available. Use --no-git to skip git initialization.', colors.yellow));
    process.exit(1);
  }

  // AI assistant selection
  let aiAssistant = args.ai;
  if (!aiAssistant) {
    aiAssistant = await selectAIAssistant();
  }

  console.log(colorize(`Selected AI assistant: ${aiAssistant}`, colors.green));
  console.log();

  // Run the bash initialization script
  const scriptPath = path.join(__dirname, '..', 'scripts', 'init-project.sh');
  const scriptArgs = [
    projectPath,
    aiAssistant,
    args.here ? 'true' : 'false',
    args.noGit ? 'true' : 'false'
  ];

  try {
    console.log(colorize('Starting project initialization...', colors.cyan));
    execSync(`bash "${scriptPath}" "${scriptArgs.join('" "')}"`, { stdio: 'inherit' });
    console.log();
    console.log(colorize('✓ Project initialized successfully!', colors.green));
    console.log();
    console.log(colorize('Next steps:', colors.cyan));
    if (!args.here) {
      console.log(`1. cd ${args.projectName}`);
    }
    console.log('2. Open in Cursor and use / commands');
    console.log('   - /specify to create specifications');
    console.log('   - /plan to create implementation plans');
    console.log('   - /tasks to generate tasks');
  } catch (error) {
    console.log(colorize('✗ Project initialization failed', colors.red));
    console.error(error.message);
    process.exit(1);
  }
}

async function main() {
  const args = parseArgs();

  if (args.help || process.argv.length === 2) {
    showBanner();
    showHelp();
    return;
  }

  if (args.command === 'init') {
    await initProject(args);
  } else {
    console.log(colorize(`Unknown command: ${args.command}`, colors.red));
    showHelp();
    process.exit(1);
  }
}

main().catch((error) => {
  console.error(colorize(`Error: ${error.message}`, colors.red));
  process.exit(1);
});
