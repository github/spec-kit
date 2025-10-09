"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BELL_REGEX = exports.CLEAR_LINE_REGEX = void 0;
/* eslint-disable no-control-regex */
exports.CLEAR_LINE_REGEX = '(?:\\u001b|\\u009b)\\[[\\=><~/#&.:=?%@~_-]*[0-9]*[\\a-ln-tqyz=><~/#&.:=?%@~_-]+';
exports.BELL_REGEX = /\u0007/;
