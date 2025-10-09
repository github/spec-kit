"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const chalk_1 = __importDefault(require("chalk"));
let logs = [];
const logLevel = () => {
    return (process.env.npm_config_loglevel || 'notice');
};
const error = (...messages) => {
    logs.push(messages.join(' '));
    console.log(chalk_1.default.red(...messages)); // eslint-disable-line no-console
};
const warn = (...messages) => {
    if (logLevel() === 'silent')
        return;
    logs.push(messages.join(' '));
    console.log(chalk_1.default.yellow(...messages)); // eslint-disable-line no-console
};
const log = (...messages) => {
    if (logLevel() === 'silent' || logLevel() === 'warn')
        return;
    logs.push(messages.join(' '));
    console.log(...messages); // eslint-disable-line no-console
};
const always = (...messages) => {
    logs.push(messages.join(' '));
    console.log(...messages); // eslint-disable-line no-console
};
// splits long text into lines and calls log()
// on each one to allow easy unit testing for specific message
const logLines = (text) => {
    const lines = text.split('\n');
    for (const line of lines) {
        log(line);
    }
};
const print = () => {
    return logs.join('\n');
};
const reset = () => {
    logs = [];
};
const loggerModule = {
    log,
    warn,
    error,
    always,
    logLines,
    print,
    reset,
    logLevel,
};
exports.default = loggerModule;
