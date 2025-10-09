"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Logger = void 0;
/* eslint-disable no-console */
const figures_1 = require("./figures");
const logger_constants_1 = require("./logger.constants");
const colorette_1 = require("./colorette");
/**
 * A internal logger for using in the verbose renderer mostly.
 */
class Logger {
    constructor(options) {
        this.options = options;
    }
    fail(message) {
        message = this.parseMessage(logger_constants_1.LogLevels.FAILED, message);
        console.error(message);
    }
    skip(message) {
        message = this.parseMessage(logger_constants_1.LogLevels.SKIPPED, message);
        console.info(message);
    }
    success(message) {
        message = this.parseMessage(logger_constants_1.LogLevels.SUCCESS, message);
        console.log(message);
    }
    data(message) {
        message = this.parseMessage(logger_constants_1.LogLevels.DATA, message);
        console.info(message);
    }
    start(message) {
        message = this.parseMessage(logger_constants_1.LogLevels.STARTED, message);
        console.log(message);
    }
    title(message) {
        message = this.parseMessage(logger_constants_1.LogLevels.TITLE, message);
        console.info(message);
    }
    retry(message) {
        message = this.parseMessage(logger_constants_1.LogLevels.RETRY, message);
        console.warn(message);
    }
    rollback(message) {
        message = this.parseMessage(logger_constants_1.LogLevels.ROLLBACK, message);
        console.warn(message);
    }
    parseMessage(level, message) {
        // parse multi line messages
        let multiLineMessage;
        try {
            multiLineMessage = message.split('\n');
        }
        catch /* istanbul ignore next */ {
            multiLineMessage = [message];
        }
        multiLineMessage = multiLineMessage.map((msg) => {
            // format messages
            return this.logColoring({
                level,
                message: msg
            });
        });
        // join back multi line messages
        message = multiLineMessage.join('\n');
        return message;
    }
    logColoring({ level, message }) {
        var _a, _b, _c, _d, _e, _f, _g, _h;
        let icon;
        // do the coloring
        let coloring = (input) => {
            return input;
        };
        switch (level) {
            case logger_constants_1.LogLevels.FAILED:
                /* istanbul ignore if */
                if ((_a = this.options) === null || _a === void 0 ? void 0 : _a.useIcons) {
                    coloring = colorette_1.default.red;
                    icon = figures_1.figures.cross;
                }
                else {
                    icon = this.wrapInBrackets(level);
                }
                break;
            case logger_constants_1.LogLevels.SKIPPED:
                /* istanbul ignore if */
                if ((_b = this.options) === null || _b === void 0 ? void 0 : _b.useIcons) {
                    coloring = colorette_1.default.yellow;
                    icon = figures_1.figures.arrowDown;
                }
                else {
                    icon = this.wrapInBrackets(level);
                }
                break;
            case logger_constants_1.LogLevels.SUCCESS:
                /* istanbul ignore if */
                if ((_c = this.options) === null || _c === void 0 ? void 0 : _c.useIcons) {
                    coloring = colorette_1.default.green;
                    icon = figures_1.figures.tick;
                }
                else {
                    icon = this.wrapInBrackets(level);
                }
                break;
            case logger_constants_1.LogLevels.DATA:
                /* istanbul ignore if */
                if ((_d = this.options) === null || _d === void 0 ? void 0 : _d.useIcons) {
                    icon = figures_1.figures.arrowRight;
                }
                else {
                    icon = this.wrapInBrackets(level);
                }
                break;
            case logger_constants_1.LogLevels.STARTED:
                /* istanbul ignore if */
                if ((_e = this.options) === null || _e === void 0 ? void 0 : _e.useIcons) {
                    icon = figures_1.figures.pointer;
                }
                else {
                    icon = this.wrapInBrackets(level);
                }
                break;
            case logger_constants_1.LogLevels.TITLE:
                /* istanbul ignore if */
                if ((_f = this.options) === null || _f === void 0 ? void 0 : _f.useIcons) {
                    icon = figures_1.figures.checkboxOn;
                }
                else {
                    icon = this.wrapInBrackets(level);
                }
                break;
            case logger_constants_1.LogLevels.RETRY:
                /* istanbul ignore if */
                if ((_g = this.options) === null || _g === void 0 ? void 0 : _g.useIcons) {
                    coloring = colorette_1.default.yellow;
                    icon = figures_1.figures.pointer;
                }
                else {
                    icon = this.wrapInBrackets(level);
                }
                break;
            case logger_constants_1.LogLevels.ROLLBACK:
                /* istanbul ignore if */
                if ((_h = this.options) === null || _h === void 0 ? void 0 : _h.useIcons) {
                    coloring = colorette_1.default.red;
                    icon = figures_1.figures.arrowLeft;
                }
                else {
                    icon = this.wrapInBrackets(level);
                }
                break;
        }
        return coloring(`${icon} ${message}`);
    }
    wrapInBrackets(level) {
        return `[${level}]`;
    }
}
exports.Logger = Logger;
