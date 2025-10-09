"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const fs_extra_1 = __importDefault(require("fs-extra"));
const path_1 = require("path");
const bluebird_1 = __importDefault(require("bluebird"));
/**
 * Get the size of a folder or a file.
 *
 * This function returns the actual file size of the folder (size), not the allocated space on disk (size on disk).
 * For more details between the difference, check this link:
 * https://www.howtogeek.com/180369/why-is-there-a-big-difference-between-size-and-size-on-disk/
 *
 * @param {string} path path to the file or the folder.
 */
function getSize(path) {
    return __awaiter(this, void 0, void 0, function* () {
        const stat = yield fs_extra_1.default.lstat(path);
        if (stat.isDirectory()) {
            const list = yield fs_extra_1.default.readdir(path);
            return bluebird_1.default.resolve(list).reduce((prev, curr) => __awaiter(this, void 0, void 0, function* () {
                const currPath = (0, path_1.join)(path, curr);
                const s = yield fs_extra_1.default.lstat(currPath);
                if (s.isDirectory()) {
                    return prev + (yield getSize(currPath));
                }
                return prev + s.size;
            }), 0);
        }
        return stat.size;
    });
}
exports.default = getSize;
