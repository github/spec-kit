"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SilentRenderer = void 0;
class SilentRenderer {
    constructor(tasks, options) {
        this.tasks = tasks;
        this.options = options;
    }
    render() { }
    end() { }
}
exports.SilentRenderer = SilentRenderer;
/** designates whether this renderer can output to a non-tty console */
SilentRenderer.nonTTY = true;
