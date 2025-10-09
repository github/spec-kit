"use strict";
var _a;
Object.defineProperty(exports, "__esModule", { value: true });
const colorette_1 = require("colorette");
exports.default = (0, colorette_1.createColors)({ useColor: ((_a = process.env) === null || _a === void 0 ? void 0 : _a.LISTR_DISABLE_COLOR) !== '1' });
