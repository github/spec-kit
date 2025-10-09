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
const minimist_1 = __importDefault(require("minimist"));
const debug_1 = __importDefault(require("debug"));
const util_1 = __importDefault(require("./util"));
const cypress_1 = __importDefault(require("./cypress"));
const install_1 = __importDefault(require("./tasks/install"));
const verify_1 = require("./tasks/verify");
const debugCli = (0, debug_1.default)('cypress:cli');
const args = (0, minimist_1.default)(process.argv.slice(2));
// we're being used from the command line
function handleExec() {
    return __awaiter(this, void 0, void 0, function* () {
        switch (args.exec) {
            case 'install': {
                debugCli('installing Cypress from NPM');
                install_1.default.start({ force: args.force })
                    .catch(util_1.default.logErrorExit1);
                break;
            }
            case 'verify': {
                // for simple testing in the monorepo
                debugCli('verifying Cypress');
                (0, verify_1.start)({ force: true }) // always force verification
                    .catch(util_1.default.logErrorExit1);
                break;
            }
            default: {
                break;
            }
        }
    });
}
// Execute the async function
if (args.exec) {
    handleExec().catch(util_1.default.logErrorExit1);
}
else {
    debugCli('exporting Cypress module interface');
}
module.exports = cypress_1.default;
