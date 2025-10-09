"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.parseTaskTime = void 0;
function parseTaskTime(duration) {
    const seconds = Math.floor(duration / 1000);
    const minutes = Math.floor(seconds / 60);
    let parsedTime;
    if (seconds === 0 && minutes === 0) {
        parsedTime = `0.${Math.floor(duration / 100)}s`;
    }
    if (seconds > 0) {
        parsedTime = `${seconds % 60}s`;
    }
    if (minutes > 0) {
        parsedTime = `${minutes}m${parsedTime}`;
    }
    return parsedTime;
}
exports.parseTaskTime = parseTaskTime;
