import module from 'module';
const require = module.createRequire(import.meta.url);
const cypress = require('./cypress');
export default cypress;
export const defineConfig = cypress.defineConfig;
export const defineComponentFramework = cypress.defineComponentFramework;
export const run = cypress.run;
export const open = cypress.open;
export const cli = cypress.cli;
