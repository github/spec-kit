"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ValidationHalt = exports.contextsKey = void 0;
// Not using Symbol because of #813
exports.contextsKey = 'express-validator#contexts';
class ValidationHalt extends Error {
}
exports.ValidationHalt = ValidationHalt;
