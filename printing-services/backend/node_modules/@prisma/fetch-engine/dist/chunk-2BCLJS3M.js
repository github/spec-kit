"use strict";
var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM2 = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);
var chunk_2BCLJS3M_exports = {};
__export(chunk_2BCLJS3M_exports, {
  download: () => download,
  getBinaryName: () => getBinaryName,
  getVersion: () => getVersion,
  maybeCopyToTmp: () => maybeCopyToTmp,
  plusX: () => plusX,
  vercelPkgPathRegex: () => vercelPkgPathRegex
});
module.exports = __toCommonJS(chunk_2BCLJS3M_exports);
var import_chunk_4LX3XBNY = require("./chunk-4LX3XBNY.js");
var import_chunk_MX3HXAU2 = require("./chunk-MX3HXAU2.js");
var import_chunk_QSTZGX47 = require("./chunk-QSTZGX47.js");
var import_chunk_QLWYUM7O = require("./chunk-QLWYUM7O.js");
var import_chunk_FQ2BOR66 = require("./chunk-FQ2BOR66.js");
var import_chunk_PXQVM7NP = require("./chunk-PXQVM7NP.js");
var import_chunk_CWGQAQ3T = require("./chunk-CWGQAQ3T.js");
var import_chunk_AH6QHEOA = require("./chunk-AH6QHEOA.js");
var import_debug = __toESM2(require("@prisma/debug"));
var import_get_platform = require("@prisma/get-platform");
var import_fs = __toESM2(require("fs"));
var import_path = __toESM2(require("path"));
var import_util = require("util");
var require_windows = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/isexe@2.0.0/node_modules/isexe/windows.js"(exports, module2) {
    "use strict";
    module2.exports = isexe;
    isexe.sync = sync;
    var fs2 = (0, import_chunk_AH6QHEOA.__require)("fs");
    function checkPathExt(path2, options2) {
      var pathext = options2.pathExt !== void 0 ? options2.pathExt : process.env.PATHEXT;
      if (!pathext) {
        return true;
      }
      pathext = pathext.split(";");
      if (pathext.indexOf("") !== -1) {
        return true;
      }
      for (var i = 0; i < pathext.length; i++) {
        var p = pathext[i].toLowerCase();
        if (p && path2.substr(-p.length).toLowerCase() === p) {
          return true;
        }
      }
      return false;
    }
    function checkStat(stat, path2, options2) {
      if (!stat.isSymbolicLink() && !stat.isFile()) {
        return false;
      }
      return checkPathExt(path2, options2);
    }
    function isexe(path2, options2, cb) {
      fs2.stat(path2, function(er, stat) {
        cb(er, er ? false : checkStat(stat, path2, options2));
      });
    }
    function sync(path2, options2) {
      return checkStat(fs2.statSync(path2), path2, options2);
    }
  }
});
var require_mode = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/isexe@2.0.0/node_modules/isexe/mode.js"(exports, module2) {
    "use strict";
    module2.exports = isexe;
    isexe.sync = sync;
    var fs2 = (0, import_chunk_AH6QHEOA.__require)("fs");
    function isexe(path2, options2, cb) {
      fs2.stat(path2, function(er, stat) {
        cb(er, er ? false : checkStat(stat, options2));
      });
    }
    function sync(path2, options2) {
      return checkStat(fs2.statSync(path2), options2);
    }
    function checkStat(stat, options2) {
      return stat.isFile() && checkMode(stat, options2);
    }
    function checkMode(stat, options2) {
      var mod = stat.mode;
      var uid = stat.uid;
      var gid = stat.gid;
      var myUid = options2.uid !== void 0 ? options2.uid : process.getuid && process.getuid();
      var myGid = options2.gid !== void 0 ? options2.gid : process.getgid && process.getgid();
      var u = parseInt("100", 8);
      var g = parseInt("010", 8);
      var o = parseInt("001", 8);
      var ug = u | g;
      var ret = mod & o || mod & g && gid === myGid || mod & u && uid === myUid || mod & ug && myUid === 0;
      return ret;
    }
  }
});
var require_isexe = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/isexe@2.0.0/node_modules/isexe/index.js"(exports, module2) {
    "use strict";
    var fs2 = (0, import_chunk_AH6QHEOA.__require)("fs");
    var core;
    if (process.platform === "win32" || global.TESTING_WINDOWS) {
      core = require_windows();
    } else {
      core = require_mode();
    }
    module2.exports = isexe;
    isexe.sync = sync;
    function isexe(path2, options2, cb) {
      if (typeof options2 === "function") {
        cb = options2;
        options2 = {};
      }
      if (!cb) {
        if (typeof Promise !== "function") {
          throw new TypeError("callback not provided");
        }
        return new Promise(function(resolve, reject) {
          isexe(path2, options2 || {}, function(er, is) {
            if (er) {
              reject(er);
            } else {
              resolve(is);
            }
          });
        });
      }
      core(path2, options2 || {}, function(er, is) {
        if (er) {
          if (er.code === "EACCES" || options2 && options2.ignoreErrors) {
            er = null;
            is = false;
          }
        }
        cb(er, is);
      });
    }
    function sync(path2, options2) {
      try {
        return core.sync(path2, options2 || {});
      } catch (er) {
        if (options2 && options2.ignoreErrors || er.code === "EACCES") {
          return false;
        } else {
          throw er;
        }
      }
    }
  }
});
var require_which = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/which@2.0.2/node_modules/which/which.js"(exports, module2) {
    "use strict";
    var isWindows = process.platform === "win32" || process.env.OSTYPE === "cygwin" || process.env.OSTYPE === "msys";
    var path2 = (0, import_chunk_AH6QHEOA.__require)("path");
    var COLON = isWindows ? ";" : ":";
    var isexe = require_isexe();
    var getNotFoundError = (cmd) => Object.assign(new Error(`not found: ${cmd}`), { code: "ENOENT" });
    var getPathInfo = (cmd, opt) => {
      const colon = opt.colon || COLON;
      const pathEnv = cmd.match(/\//) || isWindows && cmd.match(/\\/) ? [""] : [
        // windows always checks the cwd first
        ...isWindows ? [process.cwd()] : [],
        ...(opt.path || process.env.PATH || /* istanbul ignore next: very unusual */
        "").split(colon)
      ];
      const pathExtExe = isWindows ? opt.pathExt || process.env.PATHEXT || ".EXE;.CMD;.BAT;.COM" : "";
      const pathExt = isWindows ? pathExtExe.split(colon) : [""];
      if (isWindows) {
        if (cmd.indexOf(".") !== -1 && pathExt[0] !== "")
          pathExt.unshift("");
      }
      return {
        pathEnv,
        pathExt,
        pathExtExe
      };
    };
    var which = (cmd, opt, cb) => {
      if (typeof opt === "function") {
        cb = opt;
        opt = {};
      }
      if (!opt)
        opt = {};
      const { pathEnv, pathExt, pathExtExe } = getPathInfo(cmd, opt);
      const found = [];
      const step = (i) => new Promise((resolve, reject) => {
        if (i === pathEnv.length)
          return opt.all && found.length ? resolve(found) : reject(getNotFoundError(cmd));
        const ppRaw = pathEnv[i];
        const pathPart = /^".*"$/.test(ppRaw) ? ppRaw.slice(1, -1) : ppRaw;
        const pCmd = path2.join(pathPart, cmd);
        const p = !pathPart && /^\.[\\\/]/.test(cmd) ? cmd.slice(0, 2) + pCmd : pCmd;
        resolve(subStep(p, i, 0));
      });
      const subStep = (p, i, ii) => new Promise((resolve, reject) => {
        if (ii === pathExt.length)
          return resolve(step(i + 1));
        const ext = pathExt[ii];
        isexe(p + ext, { pathExt: pathExtExe }, (er, is) => {
          if (!er && is) {
            if (opt.all)
              found.push(p + ext);
            else
              return resolve(p + ext);
          }
          return resolve(subStep(p, i, ii + 1));
        });
      });
      return cb ? step(0).then((res) => cb(null, res), cb) : step(0);
    };
    var whichSync = (cmd, opt) => {
      opt = opt || {};
      const { pathEnv, pathExt, pathExtExe } = getPathInfo(cmd, opt);
      const found = [];
      for (let i = 0; i < pathEnv.length; i++) {
        const ppRaw = pathEnv[i];
        const pathPart = /^".*"$/.test(ppRaw) ? ppRaw.slice(1, -1) : ppRaw;
        const pCmd = path2.join(pathPart, cmd);
        const p = !pathPart && /^\.[\\\/]/.test(cmd) ? cmd.slice(0, 2) + pCmd : pCmd;
        for (let j = 0; j < pathExt.length; j++) {
          const cur = p + pathExt[j];
          try {
            const is = isexe.sync(cur, { pathExt: pathExtExe });
            if (is) {
              if (opt.all)
                found.push(cur);
              else
                return cur;
            }
          } catch (ex) {
          }
        }
      }
      if (opt.all && found.length)
        return found;
      if (opt.nothrow)
        return null;
      throw getNotFoundError(cmd);
    };
    module2.exports = which;
    which.sync = whichSync;
  }
});
var require_path_key = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/path-key@3.1.1/node_modules/path-key/index.js"(exports, module2) {
    "use strict";
    var pathKey = (options2 = {}) => {
      const environment = options2.env || process.env;
      const platform = options2.platform || process.platform;
      if (platform !== "win32") {
        return "PATH";
      }
      return Object.keys(environment).reverse().find((key) => key.toUpperCase() === "PATH") || "Path";
    };
    module2.exports = pathKey;
    module2.exports.default = pathKey;
  }
});
var require_resolveCommand = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/cross-spawn@7.0.3/node_modules/cross-spawn/lib/util/resolveCommand.js"(exports, module2) {
    "use strict";
    var path2 = (0, import_chunk_AH6QHEOA.__require)("path");
    var which = require_which();
    var getPathKey = require_path_key();
    function resolveCommandAttempt(parsed, withoutPathExt) {
      const env = parsed.options.env || process.env;
      const cwd = process.cwd();
      const hasCustomCwd = parsed.options.cwd != null;
      const shouldSwitchCwd = hasCustomCwd && process.chdir !== void 0 && !process.chdir.disabled;
      if (shouldSwitchCwd) {
        try {
          process.chdir(parsed.options.cwd);
        } catch (err) {
        }
      }
      let resolved;
      try {
        resolved = which.sync(parsed.command, {
          path: env[getPathKey({ env })],
          pathExt: withoutPathExt ? path2.delimiter : void 0
        });
      } catch (e) {
      } finally {
        if (shouldSwitchCwd) {
          process.chdir(cwd);
        }
      }
      if (resolved) {
        resolved = path2.resolve(hasCustomCwd ? parsed.options.cwd : "", resolved);
      }
      return resolved;
    }
    function resolveCommand(parsed) {
      return resolveCommandAttempt(parsed) || resolveCommandAttempt(parsed, true);
    }
    module2.exports = resolveCommand;
  }
});
var require_escape = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/cross-spawn@7.0.3/node_modules/cross-spawn/lib/util/escape.js"(exports, module2) {
    "use strict";
    var metaCharsRegExp = /([()\][%!^"`<>&|;, *?])/g;
    function escapeCommand(arg) {
      arg = arg.replace(metaCharsRegExp, "^$1");
      return arg;
    }
    function escapeArgument(arg, doubleEscapeMetaChars) {
      arg = `${arg}`;
      arg = arg.replace(/(\\*)"/g, '$1$1\\"');
      arg = arg.replace(/(\\*)$/, "$1$1");
      arg = `"${arg}"`;
      arg = arg.replace(metaCharsRegExp, "^$1");
      if (doubleEscapeMetaChars) {
        arg = arg.replace(metaCharsRegExp, "^$1");
      }
      return arg;
    }
    module2.exports.command = escapeCommand;
    module2.exports.argument = escapeArgument;
  }
});
var require_shebang_regex = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/shebang-regex@3.0.0/node_modules/shebang-regex/index.js"(exports, module2) {
    "use strict";
    module2.exports = /^#!(.*)/;
  }
});
var require_shebang_command = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/shebang-command@2.0.0/node_modules/shebang-command/index.js"(exports, module2) {
    "use strict";
    var shebangRegex = require_shebang_regex();
    module2.exports = (string = "") => {
      const match = string.match(shebangRegex);
      if (!match) {
        return null;
      }
      const [path2, argument] = match[0].replace(/#! ?/, "").split(" ");
      const binary = path2.split("/").pop();
      if (binary === "env") {
        return argument;
      }
      return argument ? `${binary} ${argument}` : binary;
    };
  }
});
var require_readShebang = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/cross-spawn@7.0.3/node_modules/cross-spawn/lib/util/readShebang.js"(exports, module2) {
    "use strict";
    var fs2 = (0, import_chunk_AH6QHEOA.__require)("fs");
    var shebangCommand = require_shebang_command();
    function readShebang(command) {
      const size = 150;
      const buffer = Buffer.alloc(size);
      let fd;
      try {
        fd = fs2.openSync(command, "r");
        fs2.readSync(fd, buffer, 0, size, 0);
        fs2.closeSync(fd);
      } catch (e) {
      }
      return shebangCommand(buffer.toString());
    }
    module2.exports = readShebang;
  }
});
var require_parse = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/cross-spawn@7.0.3/node_modules/cross-spawn/lib/parse.js"(exports, module2) {
    "use strict";
    var path2 = (0, import_chunk_AH6QHEOA.__require)("path");
    var resolveCommand = require_resolveCommand();
    var escape = require_escape();
    var readShebang = require_readShebang();
    var isWin = process.platform === "win32";
    var isExecutableRegExp = /\.(?:com|exe)$/i;
    var isCmdShimRegExp = /node_modules[\\/].bin[\\/][^\\/]+\.cmd$/i;
    function detectShebang(parsed) {
      parsed.file = resolveCommand(parsed);
      const shebang = parsed.file && readShebang(parsed.file);
      if (shebang) {
        parsed.args.unshift(parsed.file);
        parsed.command = shebang;
        return resolveCommand(parsed);
      }
      return parsed.file;
    }
    function parseNonShell(parsed) {
      if (!isWin) {
        return parsed;
      }
      const commandFile = detectShebang(parsed);
      const needsShell = !isExecutableRegExp.test(commandFile);
      if (parsed.options.forceShell || needsShell) {
        const needsDoubleEscapeMetaChars = isCmdShimRegExp.test(commandFile);
        parsed.command = path2.normalize(parsed.command);
        parsed.command = escape.command(parsed.command);
        parsed.args = parsed.args.map((arg) => escape.argument(arg, needsDoubleEscapeMetaChars));
        const shellCommand = [parsed.command].concat(parsed.args).join(" ");
        parsed.args = ["/d", "/s", "/c", `"${shellCommand}"`];
        parsed.command = process.env.comspec || "cmd.exe";
        parsed.options.windowsVerbatimArguments = true;
      }
      return parsed;
    }
    function parse(command, args, options2) {
      if (args && !Array.isArray(args)) {
        options2 = args;
        args = null;
      }
      args = args ? args.slice(0) : [];
      options2 = Object.assign({}, options2);
      const parsed = {
        command,
        args,
        options: options2,
        file: void 0,
        original: {
          command,
          args
        }
      };
      return options2.shell ? parsed : parseNonShell(parsed);
    }
    module2.exports = parse;
  }
});
var require_enoent = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/cross-spawn@7.0.3/node_modules/cross-spawn/lib/enoent.js"(exports, module2) {
    "use strict";
    var isWin = process.platform === "win32";
    function notFoundError(original, syscall) {
      return Object.assign(new Error(`${syscall} ${original.command} ENOENT`), {
        code: "ENOENT",
        errno: "ENOENT",
        syscall: `${syscall} ${original.command}`,
        path: original.command,
        spawnargs: original.args
      });
    }
    function hookChildProcess(cp, parsed) {
      if (!isWin) {
        return;
      }
      const originalEmit = cp.emit;
      cp.emit = function(name, arg1) {
        if (name === "exit") {
          const err = verifyENOENT(arg1, parsed, "spawn");
          if (err) {
            return originalEmit.call(cp, "error", err);
          }
        }
        return originalEmit.apply(cp, arguments);
      };
    }
    function verifyENOENT(status, parsed) {
      if (isWin && status === 1 && !parsed.file) {
        return notFoundError(parsed.original, "spawn");
      }
      return null;
    }
    function verifyENOENTSync(status, parsed) {
      if (isWin && status === 1 && !parsed.file) {
        return notFoundError(parsed.original, "spawnSync");
      }
      return null;
    }
    module2.exports = {
      hookChildProcess,
      verifyENOENT,
      verifyENOENTSync,
      notFoundError
    };
  }
});
var require_cross_spawn = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/cross-spawn@7.0.3/node_modules/cross-spawn/index.js"(exports, module2) {
    "use strict";
    var cp = (0, import_chunk_AH6QHEOA.__require)("child_process");
    var parse = require_parse();
    var enoent = require_enoent();
    function spawn(command, args, options2) {
      const parsed = parse(command, args, options2);
      const spawned = cp.spawn(parsed.command, parsed.args, parsed.options);
      enoent.hookChildProcess(spawned, parsed);
      return spawned;
    }
    function spawnSync(command, args, options2) {
      const parsed = parse(command, args, options2);
      const result = cp.spawnSync(parsed.command, parsed.args, parsed.options);
      result.error = result.error || enoent.verifyENOENTSync(result.status, parsed);
      return result;
    }
    module2.exports = spawn;
    module2.exports.spawn = spawn;
    module2.exports.sync = spawnSync;
    module2.exports._parse = parse;
    module2.exports._enoent = enoent;
  }
});
var require_strip_final_newline = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/strip-final-newline@2.0.0/node_modules/strip-final-newline/index.js"(exports, module2) {
    "use strict";
    module2.exports = (input) => {
      const LF = typeof input === "string" ? "\n" : "\n".charCodeAt();
      const CR = typeof input === "string" ? "\r" : "\r".charCodeAt();
      if (input[input.length - 1] === LF) {
        input = input.slice(0, input.length - 1);
      }
      if (input[input.length - 1] === CR) {
        input = input.slice(0, input.length - 1);
      }
      return input;
    };
  }
});
var require_npm_run_path = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/npm-run-path@4.0.1/node_modules/npm-run-path/index.js"(exports, module2) {
    "use strict";
    var path2 = (0, import_chunk_AH6QHEOA.__require)("path");
    var pathKey = require_path_key();
    var npmRunPath = (options2) => {
      options2 = {
        cwd: process.cwd(),
        path: process.env[pathKey()],
        execPath: process.execPath,
        ...options2
      };
      let previous;
      let cwdPath = path2.resolve(options2.cwd);
      const result = [];
      while (previous !== cwdPath) {
        result.push(path2.join(cwdPath, "node_modules/.bin"));
        previous = cwdPath;
        cwdPath = path2.resolve(cwdPath, "..");
      }
      const execPathDir = path2.resolve(options2.cwd, options2.execPath, "..");
      result.push(execPathDir);
      return result.concat(options2.path).join(path2.delimiter);
    };
    module2.exports = npmRunPath;
    module2.exports.default = npmRunPath;
    module2.exports.env = (options2) => {
      options2 = {
        env: process.env,
        ...options2
      };
      const env = { ...options2.env };
      const path3 = pathKey({ env });
      options2.path = env[path3];
      env[path3] = module2.exports(options2);
      return env;
    };
  }
});
var require_mimic_fn = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/mimic-fn@2.1.0/node_modules/mimic-fn/index.js"(exports, module2) {
    "use strict";
    var mimicFn = (to, from) => {
      for (const prop of Reflect.ownKeys(from)) {
        Object.defineProperty(to, prop, Object.getOwnPropertyDescriptor(from, prop));
      }
      return to;
    };
    module2.exports = mimicFn;
    module2.exports.default = mimicFn;
  }
});
var require_onetime = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/onetime@5.1.2/node_modules/onetime/index.js"(exports, module2) {
    "use strict";
    var mimicFn = require_mimic_fn();
    var calledFunctions = /* @__PURE__ */ new WeakMap();
    var onetime = (function_, options2 = {}) => {
      if (typeof function_ !== "function") {
        throw new TypeError("Expected a function");
      }
      let returnValue;
      let callCount = 0;
      const functionName = function_.displayName || function_.name || "<anonymous>";
      const onetime2 = function(...arguments_) {
        calledFunctions.set(onetime2, ++callCount);
        if (callCount === 1) {
          returnValue = function_.apply(this, arguments_);
          function_ = null;
        } else if (options2.throw === true) {
          throw new Error(`Function \`${functionName}\` can only be called once`);
        }
        return returnValue;
      };
      mimicFn(onetime2, function_);
      calledFunctions.set(onetime2, callCount);
      return onetime2;
    };
    module2.exports = onetime;
    module2.exports.default = onetime;
    module2.exports.callCount = (function_) => {
      if (!calledFunctions.has(function_)) {
        throw new Error(`The given function \`${function_.name}\` is not wrapped by the \`onetime\` package`);
      }
      return calledFunctions.get(function_);
    };
  }
});
var require_core = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/human-signals@2.1.0/node_modules/human-signals/build/src/core.js"(exports) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    exports.SIGNALS = void 0;
    var SIGNALS = [
      {
        name: "SIGHUP",
        number: 1,
        action: "terminate",
        description: "Terminal closed",
        standard: "posix"
      },
      {
        name: "SIGINT",
        number: 2,
        action: "terminate",
        description: "User interruption with CTRL-C",
        standard: "ansi"
      },
      {
        name: "SIGQUIT",
        number: 3,
        action: "core",
        description: "User interruption with CTRL-\\",
        standard: "posix"
      },
      {
        name: "SIGILL",
        number: 4,
        action: "core",
        description: "Invalid machine instruction",
        standard: "ansi"
      },
      {
        name: "SIGTRAP",
        number: 5,
        action: "core",
        description: "Debugger breakpoint",
        standard: "posix"
      },
      {
        name: "SIGABRT",
        number: 6,
        action: "core",
        description: "Aborted",
        standard: "ansi"
      },
      {
        name: "SIGIOT",
        number: 6,
        action: "core",
        description: "Aborted",
        standard: "bsd"
      },
      {
        name: "SIGBUS",
        number: 7,
        action: "core",
        description: "Bus error due to misaligned, non-existing address or paging error",
        standard: "bsd"
      },
      {
        name: "SIGEMT",
        number: 7,
        action: "terminate",
        description: "Command should be emulated but is not implemented",
        standard: "other"
      },
      {
        name: "SIGFPE",
        number: 8,
        action: "core",
        description: "Floating point arithmetic error",
        standard: "ansi"
      },
      {
        name: "SIGKILL",
        number: 9,
        action: "terminate",
        description: "Forced termination",
        standard: "posix",
        forced: true
      },
      {
        name: "SIGUSR1",
        number: 10,
        action: "terminate",
        description: "Application-specific signal",
        standard: "posix"
      },
      {
        name: "SIGSEGV",
        number: 11,
        action: "core",
        description: "Segmentation fault",
        standard: "ansi"
      },
      {
        name: "SIGUSR2",
        number: 12,
        action: "terminate",
        description: "Application-specific signal",
        standard: "posix"
      },
      {
        name: "SIGPIPE",
        number: 13,
        action: "terminate",
        description: "Broken pipe or socket",
        standard: "posix"
      },
      {
        name: "SIGALRM",
        number: 14,
        action: "terminate",
        description: "Timeout or timer",
        standard: "posix"
      },
      {
        name: "SIGTERM",
        number: 15,
        action: "terminate",
        description: "Termination",
        standard: "ansi"
      },
      {
        name: "SIGSTKFLT",
        number: 16,
        action: "terminate",
        description: "Stack is empty or overflowed",
        standard: "other"
      },
      {
        name: "SIGCHLD",
        number: 17,
        action: "ignore",
        description: "Child process terminated, paused or unpaused",
        standard: "posix"
      },
      {
        name: "SIGCLD",
        number: 17,
        action: "ignore",
        description: "Child process terminated, paused or unpaused",
        standard: "other"
      },
      {
        name: "SIGCONT",
        number: 18,
        action: "unpause",
        description: "Unpaused",
        standard: "posix",
        forced: true
      },
      {
        name: "SIGSTOP",
        number: 19,
        action: "pause",
        description: "Paused",
        standard: "posix",
        forced: true
      },
      {
        name: "SIGTSTP",
        number: 20,
        action: "pause",
        description: 'Paused using CTRL-Z or "suspend"',
        standard: "posix"
      },
      {
        name: "SIGTTIN",
        number: 21,
        action: "pause",
        description: "Background process cannot read terminal input",
        standard: "posix"
      },
      {
        name: "SIGBREAK",
        number: 21,
        action: "terminate",
        description: "User interruption with CTRL-BREAK",
        standard: "other"
      },
      {
        name: "SIGTTOU",
        number: 22,
        action: "pause",
        description: "Background process cannot write to terminal output",
        standard: "posix"
      },
      {
        name: "SIGURG",
        number: 23,
        action: "ignore",
        description: "Socket received out-of-band data",
        standard: "bsd"
      },
      {
        name: "SIGXCPU",
        number: 24,
        action: "core",
        description: "Process timed out",
        standard: "bsd"
      },
      {
        name: "SIGXFSZ",
        number: 25,
        action: "core",
        description: "File too big",
        standard: "bsd"
      },
      {
        name: "SIGVTALRM",
        number: 26,
        action: "terminate",
        description: "Timeout or timer",
        standard: "bsd"
      },
      {
        name: "SIGPROF",
        number: 27,
        action: "terminate",
        description: "Timeout or timer",
        standard: "bsd"
      },
      {
        name: "SIGWINCH",
        number: 28,
        action: "ignore",
        description: "Terminal window size changed",
        standard: "bsd"
      },
      {
        name: "SIGIO",
        number: 29,
        action: "terminate",
        description: "I/O is available",
        standard: "other"
      },
      {
        name: "SIGPOLL",
        number: 29,
        action: "terminate",
        description: "Watched event",
        standard: "other"
      },
      {
        name: "SIGINFO",
        number: 29,
        action: "ignore",
        description: "Request for process information",
        standard: "other"
      },
      {
        name: "SIGPWR",
        number: 30,
        action: "terminate",
        description: "Device running out of power",
        standard: "systemv"
      },
      {
        name: "SIGSYS",
        number: 31,
        action: "core",
        description: "Invalid system call",
        standard: "other"
      },
      {
        name: "SIGUNUSED",
        number: 31,
        action: "terminate",
        description: "Invalid system call",
        standard: "other"
      }
    ];
    exports.SIGNALS = SIGNALS;
  }
});
var require_realtime = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/human-signals@2.1.0/node_modules/human-signals/build/src/realtime.js"(exports) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    exports.SIGRTMAX = exports.getRealtimeSignals = void 0;
    var getRealtimeSignals = function() {
      const length = SIGRTMAX - SIGRTMIN + 1;
      return Array.from({ length }, getRealtimeSignal);
    };
    exports.getRealtimeSignals = getRealtimeSignals;
    var getRealtimeSignal = function(value, index) {
      return {
        name: `SIGRT${index + 1}`,
        number: SIGRTMIN + index,
        action: "terminate",
        description: "Application-specific signal (realtime)",
        standard: "posix"
      };
    };
    var SIGRTMIN = 34;
    var SIGRTMAX = 64;
    exports.SIGRTMAX = SIGRTMAX;
  }
});
var require_signals = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/human-signals@2.1.0/node_modules/human-signals/build/src/signals.js"(exports) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    exports.getSignals = void 0;
    var _os = (0, import_chunk_AH6QHEOA.__require)("os");
    var _core = require_core();
    var _realtime = require_realtime();
    var getSignals = function() {
      const realtimeSignals = (0, _realtime.getRealtimeSignals)();
      const signals = [..._core.SIGNALS, ...realtimeSignals].map(normalizeSignal);
      return signals;
    };
    exports.getSignals = getSignals;
    var normalizeSignal = function({
      name,
      number: defaultNumber,
      description,
      action,
      forced = false,
      standard
    }) {
      const {
        signals: { [name]: constantSignal }
      } = _os.constants;
      const supported = constantSignal !== void 0;
      const number = supported ? constantSignal : defaultNumber;
      return { name, number, description, supported, action, forced, standard };
    };
  }
});
var require_main = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/human-signals@2.1.0/node_modules/human-signals/build/src/main.js"(exports) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    exports.signalsByNumber = exports.signalsByName = void 0;
    var _os = (0, import_chunk_AH6QHEOA.__require)("os");
    var _signals = require_signals();
    var _realtime = require_realtime();
    var getSignalsByName = function() {
      const signals = (0, _signals.getSignals)();
      return signals.reduce(getSignalByName, {});
    };
    var getSignalByName = function(signalByNameMemo, { name, number, description, supported, action, forced, standard }) {
      return {
        ...signalByNameMemo,
        [name]: { name, number, description, supported, action, forced, standard }
      };
    };
    var signalsByName = getSignalsByName();
    exports.signalsByName = signalsByName;
    var getSignalsByNumber = function() {
      const signals = (0, _signals.getSignals)();
      const length = _realtime.SIGRTMAX + 1;
      const signalsA = Array.from({ length }, (value, number) => getSignalByNumber(number, signals));
      return Object.assign({}, ...signalsA);
    };
    var getSignalByNumber = function(number, signals) {
      const signal = findSignalByNumber(number, signals);
      if (signal === void 0) {
        return {};
      }
      const { name, description, supported, action, forced, standard } = signal;
      return {
        [number]: {
          name,
          number,
          description,
          supported,
          action,
          forced,
          standard
        }
      };
    };
    var findSignalByNumber = function(number, signals) {
      const signal = signals.find(({ name }) => _os.constants.signals[name] === number);
      if (signal !== void 0) {
        return signal;
      }
      return signals.find((signalA) => signalA.number === number);
    };
    var signalsByNumber = getSignalsByNumber();
    exports.signalsByNumber = signalsByNumber;
  }
});
var require_error = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/execa@5.1.1/node_modules/execa/lib/error.js"(exports, module2) {
    "use strict";
    var { signalsByName } = require_main();
    var getErrorPrefix = ({ timedOut, timeout, errorCode, signal, signalDescription, exitCode, isCanceled }) => {
      if (timedOut) {
        return `timed out after ${timeout} milliseconds`;
      }
      if (isCanceled) {
        return "was canceled";
      }
      if (errorCode !== void 0) {
        return `failed with ${errorCode}`;
      }
      if (signal !== void 0) {
        return `was killed with ${signal} (${signalDescription})`;
      }
      if (exitCode !== void 0) {
        return `failed with exit code ${exitCode}`;
      }
      return "failed";
    };
    var makeError = ({
      stdout,
      stderr,
      all,
      error,
      signal,
      exitCode,
      command,
      escapedCommand,
      timedOut,
      isCanceled,
      killed,
      parsed: { options: { timeout } }
    }) => {
      exitCode = exitCode === null ? void 0 : exitCode;
      signal = signal === null ? void 0 : signal;
      const signalDescription = signal === void 0 ? void 0 : signalsByName[signal].description;
      const errorCode = error && error.code;
      const prefix = getErrorPrefix({ timedOut, timeout, errorCode, signal, signalDescription, exitCode, isCanceled });
      const execaMessage = `Command ${prefix}: ${command}`;
      const isError = Object.prototype.toString.call(error) === "[object Error]";
      const shortMessage = isError ? `${execaMessage}
${error.message}` : execaMessage;
      const message = [shortMessage, stderr, stdout].filter(Boolean).join("\n");
      if (isError) {
        error.originalMessage = error.message;
        error.message = message;
      } else {
        error = new Error(message);
      }
      error.shortMessage = shortMessage;
      error.command = command;
      error.escapedCommand = escapedCommand;
      error.exitCode = exitCode;
      error.signal = signal;
      error.signalDescription = signalDescription;
      error.stdout = stdout;
      error.stderr = stderr;
      if (all !== void 0) {
        error.all = all;
      }
      if ("bufferedData" in error) {
        delete error.bufferedData;
      }
      error.failed = true;
      error.timedOut = Boolean(timedOut);
      error.isCanceled = isCanceled;
      error.killed = killed && !timedOut;
      return error;
    };
    module2.exports = makeError;
  }
});
var require_stdio = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/execa@5.1.1/node_modules/execa/lib/stdio.js"(exports, module2) {
    "use strict";
    var aliases = ["stdin", "stdout", "stderr"];
    var hasAlias = (options2) => aliases.some((alias) => options2[alias] !== void 0);
    var normalizeStdio = (options2) => {
      if (!options2) {
        return;
      }
      const { stdio } = options2;
      if (stdio === void 0) {
        return aliases.map((alias) => options2[alias]);
      }
      if (hasAlias(options2)) {
        throw new Error(`It's not possible to provide \`stdio\` in combination with one of ${aliases.map((alias) => `\`${alias}\``).join(", ")}`);
      }
      if (typeof stdio === "string") {
        return stdio;
      }
      if (!Array.isArray(stdio)) {
        throw new TypeError(`Expected \`stdio\` to be of type \`string\` or \`Array\`, got \`${typeof stdio}\``);
      }
      const length = Math.max(stdio.length, aliases.length);
      return Array.from({ length }, (value, index) => stdio[index]);
    };
    module2.exports = normalizeStdio;
    module2.exports.node = (options2) => {
      const stdio = normalizeStdio(options2);
      if (stdio === "ipc") {
        return "ipc";
      }
      if (stdio === void 0 || typeof stdio === "string") {
        return [stdio, stdio, stdio, "ipc"];
      }
      if (stdio.includes("ipc")) {
        return stdio;
      }
      return [...stdio, "ipc"];
    };
  }
});
var require_signals2 = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/signal-exit@3.0.7/node_modules/signal-exit/signals.js"(exports, module2) {
    "use strict";
    module2.exports = [
      "SIGABRT",
      "SIGALRM",
      "SIGHUP",
      "SIGINT",
      "SIGTERM"
    ];
    if (process.platform !== "win32") {
      module2.exports.push(
        "SIGVTALRM",
        "SIGXCPU",
        "SIGXFSZ",
        "SIGUSR2",
        "SIGTRAP",
        "SIGSYS",
        "SIGQUIT",
        "SIGIOT"
        // should detect profiler and enable/disable accordingly.
        // see #21
        // 'SIGPROF'
      );
    }
    if (process.platform === "linux") {
      module2.exports.push(
        "SIGIO",
        "SIGPOLL",
        "SIGPWR",
        "SIGSTKFLT",
        "SIGUNUSED"
      );
    }
  }
});
var require_signal_exit = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/signal-exit@3.0.7/node_modules/signal-exit/index.js"(exports, module2) {
    "use strict";
    var process2 = global.process;
    var processOk = function(process3) {
      return process3 && typeof process3 === "object" && typeof process3.removeListener === "function" && typeof process3.emit === "function" && typeof process3.reallyExit === "function" && typeof process3.listeners === "function" && typeof process3.kill === "function" && typeof process3.pid === "number" && typeof process3.on === "function";
    };
    if (!processOk(process2)) {
      module2.exports = function() {
        return function() {
        };
      };
    } else {
      assert = (0, import_chunk_AH6QHEOA.__require)("assert");
      signals = require_signals2();
      isWin = /^win/i.test(process2.platform);
      EE = (0, import_chunk_AH6QHEOA.__require)("events");
      if (typeof EE !== "function") {
        EE = EE.EventEmitter;
      }
      if (process2.__signal_exit_emitter__) {
        emitter = process2.__signal_exit_emitter__;
      } else {
        emitter = process2.__signal_exit_emitter__ = new EE();
        emitter.count = 0;
        emitter.emitted = {};
      }
      if (!emitter.infinite) {
        emitter.setMaxListeners(Infinity);
        emitter.infinite = true;
      }
      module2.exports = function(cb, opts2) {
        if (!processOk(global.process)) {
          return function() {
          };
        }
        assert.equal(typeof cb, "function", "a callback must be provided for exit handler");
        if (loaded === false) {
          load();
        }
        var ev = "exit";
        if (opts2 && opts2.alwaysLast) {
          ev = "afterexit";
        }
        var remove = function() {
          emitter.removeListener(ev, cb);
          if (emitter.listeners("exit").length === 0 && emitter.listeners("afterexit").length === 0) {
            unload();
          }
        };
        emitter.on(ev, cb);
        return remove;
      };
      unload = function unload2() {
        if (!loaded || !processOk(global.process)) {
          return;
        }
        loaded = false;
        signals.forEach(function(sig) {
          try {
            process2.removeListener(sig, sigListeners[sig]);
          } catch (er) {
          }
        });
        process2.emit = originalProcessEmit;
        process2.reallyExit = originalProcessReallyExit;
        emitter.count -= 1;
      };
      module2.exports.unload = unload;
      emit = function emit2(event, code, signal) {
        if (emitter.emitted[event]) {
          return;
        }
        emitter.emitted[event] = true;
        emitter.emit(event, code, signal);
      };
      sigListeners = {};
      signals.forEach(function(sig) {
        sigListeners[sig] = function listener() {
          if (!processOk(global.process)) {
            return;
          }
          var listeners = process2.listeners(sig);
          if (listeners.length === emitter.count) {
            unload();
            emit("exit", null, sig);
            emit("afterexit", null, sig);
            if (isWin && sig === "SIGHUP") {
              sig = "SIGINT";
            }
            process2.kill(process2.pid, sig);
          }
        };
      });
      module2.exports.signals = function() {
        return signals;
      };
      loaded = false;
      load = function load2() {
        if (loaded || !processOk(global.process)) {
          return;
        }
        loaded = true;
        emitter.count += 1;
        signals = signals.filter(function(sig) {
          try {
            process2.on(sig, sigListeners[sig]);
            return true;
          } catch (er) {
            return false;
          }
        });
        process2.emit = processEmit;
        process2.reallyExit = processReallyExit;
      };
      module2.exports.load = load;
      originalProcessReallyExit = process2.reallyExit;
      processReallyExit = function processReallyExit2(code) {
        if (!processOk(global.process)) {
          return;
        }
        process2.exitCode = code || /* istanbul ignore next */
        0;
        emit("exit", process2.exitCode, null);
        emit("afterexit", process2.exitCode, null);
        originalProcessReallyExit.call(process2, process2.exitCode);
      };
      originalProcessEmit = process2.emit;
      processEmit = function processEmit2(ev, arg) {
        if (ev === "exit" && processOk(global.process)) {
          if (arg !== void 0) {
            process2.exitCode = arg;
          }
          var ret = originalProcessEmit.apply(this, arguments);
          emit("exit", process2.exitCode, null);
          emit("afterexit", process2.exitCode, null);
          return ret;
        } else {
          return originalProcessEmit.apply(this, arguments);
        }
      };
    }
    var assert;
    var signals;
    var isWin;
    var EE;
    var emitter;
    var unload;
    var emit;
    var sigListeners;
    var loaded;
    var load;
    var originalProcessReallyExit;
    var processReallyExit;
    var originalProcessEmit;
    var processEmit;
  }
});
var require_kill = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/execa@5.1.1/node_modules/execa/lib/kill.js"(exports, module2) {
    "use strict";
    var os2 = (0, import_chunk_AH6QHEOA.__require)("os");
    var onExit = require_signal_exit();
    var DEFAULT_FORCE_KILL_TIMEOUT = 1e3 * 5;
    var spawnedKill = (kill, signal = "SIGTERM", options2 = {}) => {
      const killResult = kill(signal);
      setKillTimeout(kill, signal, options2, killResult);
      return killResult;
    };
    var setKillTimeout = (kill, signal, options2, killResult) => {
      if (!shouldForceKill(signal, options2, killResult)) {
        return;
      }
      const timeout = getForceKillAfterTimeout(options2);
      const t = setTimeout(() => {
        kill("SIGKILL");
      }, timeout);
      if (t.unref) {
        t.unref();
      }
    };
    var shouldForceKill = (signal, { forceKillAfterTimeout }, killResult) => {
      return isSigterm(signal) && forceKillAfterTimeout !== false && killResult;
    };
    var isSigterm = (signal) => {
      return signal === os2.constants.signals.SIGTERM || typeof signal === "string" && signal.toUpperCase() === "SIGTERM";
    };
    var getForceKillAfterTimeout = ({ forceKillAfterTimeout = true }) => {
      if (forceKillAfterTimeout === true) {
        return DEFAULT_FORCE_KILL_TIMEOUT;
      }
      if (!Number.isFinite(forceKillAfterTimeout) || forceKillAfterTimeout < 0) {
        throw new TypeError(`Expected the \`forceKillAfterTimeout\` option to be a non-negative integer, got \`${forceKillAfterTimeout}\` (${typeof forceKillAfterTimeout})`);
      }
      return forceKillAfterTimeout;
    };
    var spawnedCancel = (spawned, context) => {
      const killResult = spawned.kill();
      if (killResult) {
        context.isCanceled = true;
      }
    };
    var timeoutKill = (spawned, signal, reject) => {
      spawned.kill(signal);
      reject(Object.assign(new Error("Timed out"), { timedOut: true, signal }));
    };
    var setupTimeout = (spawned, { timeout, killSignal = "SIGTERM" }, spawnedPromise) => {
      if (timeout === 0 || timeout === void 0) {
        return spawnedPromise;
      }
      let timeoutId;
      const timeoutPromise = new Promise((resolve, reject) => {
        timeoutId = setTimeout(() => {
          timeoutKill(spawned, killSignal, reject);
        }, timeout);
      });
      const safeSpawnedPromise = spawnedPromise.finally(() => {
        clearTimeout(timeoutId);
      });
      return Promise.race([timeoutPromise, safeSpawnedPromise]);
    };
    var validateTimeout = ({ timeout }) => {
      if (timeout !== void 0 && (!Number.isFinite(timeout) || timeout < 0)) {
        throw new TypeError(`Expected the \`timeout\` option to be a non-negative integer, got \`${timeout}\` (${typeof timeout})`);
      }
    };
    var setExitHandler = async (spawned, { cleanup, detached }, timedPromise) => {
      if (!cleanup || detached) {
        return timedPromise;
      }
      const removeExitHandler = onExit(() => {
        spawned.kill();
      });
      return timedPromise.finally(() => {
        removeExitHandler();
      });
    };
    module2.exports = {
      spawnedKill,
      spawnedCancel,
      setupTimeout,
      validateTimeout,
      setExitHandler
    };
  }
});
var require_buffer_stream = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/get-stream@6.0.1/node_modules/get-stream/buffer-stream.js"(exports, module2) {
    "use strict";
    var { PassThrough: PassThroughStream } = (0, import_chunk_AH6QHEOA.__require)("stream");
    module2.exports = (options2) => {
      options2 = { ...options2 };
      const { array } = options2;
      let { encoding } = options2;
      const isBuffer = encoding === "buffer";
      let objectMode = false;
      if (array) {
        objectMode = !(encoding || isBuffer);
      } else {
        encoding = encoding || "utf8";
      }
      if (isBuffer) {
        encoding = null;
      }
      const stream = new PassThroughStream({ objectMode });
      if (encoding) {
        stream.setEncoding(encoding);
      }
      let length = 0;
      const chunks = [];
      stream.on("data", (chunk) => {
        chunks.push(chunk);
        if (objectMode) {
          length = chunks.length;
        } else {
          length += chunk.length;
        }
      });
      stream.getBufferedValue = () => {
        if (array) {
          return chunks;
        }
        return isBuffer ? Buffer.concat(chunks, length) : chunks.join("");
      };
      stream.getBufferedLength = () => length;
      return stream;
    };
  }
});
var require_get_stream = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/get-stream@6.0.1/node_modules/get-stream/index.js"(exports, module2) {
    "use strict";
    var { constants: BufferConstants } = (0, import_chunk_AH6QHEOA.__require)("buffer");
    var stream = (0, import_chunk_AH6QHEOA.__require)("stream");
    var { promisify: promisify2 } = (0, import_chunk_AH6QHEOA.__require)("util");
    var bufferStream = require_buffer_stream();
    var streamPipelinePromisified = promisify2(stream.pipeline);
    var MaxBufferError = class extends Error {
      constructor() {
        super("maxBuffer exceeded");
        this.name = "MaxBufferError";
      }
    };
    async function getStream(inputStream, options2) {
      if (!inputStream) {
        throw new Error("Expected a stream");
      }
      options2 = {
        maxBuffer: Infinity,
        ...options2
      };
      const { maxBuffer } = options2;
      const stream2 = bufferStream(options2);
      await new Promise((resolve, reject) => {
        const rejectPromise = (error) => {
          if (error && stream2.getBufferedLength() <= BufferConstants.MAX_LENGTH) {
            error.bufferedData = stream2.getBufferedValue();
          }
          reject(error);
        };
        (async () => {
          try {
            await streamPipelinePromisified(inputStream, stream2);
            resolve();
          } catch (error) {
            rejectPromise(error);
          }
        })();
        stream2.on("data", () => {
          if (stream2.getBufferedLength() > maxBuffer) {
            rejectPromise(new MaxBufferError());
          }
        });
      });
      return stream2.getBufferedValue();
    }
    module2.exports = getStream;
    module2.exports.buffer = (stream2, options2) => getStream(stream2, { ...options2, encoding: "buffer" });
    module2.exports.array = (stream2, options2) => getStream(stream2, { ...options2, array: true });
    module2.exports.MaxBufferError = MaxBufferError;
  }
});
var require_merge_stream = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/merge-stream@2.0.0/node_modules/merge-stream/index.js"(exports, module2) {
    "use strict";
    var { PassThrough } = (0, import_chunk_AH6QHEOA.__require)("stream");
    module2.exports = function() {
      var sources = [];
      var output = new PassThrough({ objectMode: true });
      output.setMaxListeners(0);
      output.add = add;
      output.isEmpty = isEmpty;
      output.on("unpipe", remove);
      Array.prototype.slice.call(arguments).forEach(add);
      return output;
      function add(source) {
        if (Array.isArray(source)) {
          source.forEach(add);
          return this;
        }
        sources.push(source);
        source.once("end", remove.bind(null, source));
        source.once("error", output.emit.bind(output, "error"));
        source.pipe(output, { end: false });
        return this;
      }
      function isEmpty() {
        return sources.length == 0;
      }
      function remove(source) {
        sources = sources.filter(function(it) {
          return it !== source;
        });
        if (!sources.length && output.readable) {
          output.end();
        }
      }
    };
  }
});
var require_stream = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/execa@5.1.1/node_modules/execa/lib/stream.js"(exports, module2) {
    "use strict";
    var isStream = (0, import_chunk_QLWYUM7O.require_is_stream)();
    var getStream = require_get_stream();
    var mergeStream = require_merge_stream();
    var handleInput = (spawned, input) => {
      if (input === void 0 || spawned.stdin === void 0) {
        return;
      }
      if (isStream(input)) {
        input.pipe(spawned.stdin);
      } else {
        spawned.stdin.end(input);
      }
    };
    var makeAllStream = (spawned, { all }) => {
      if (!all || !spawned.stdout && !spawned.stderr) {
        return;
      }
      const mixed = mergeStream();
      if (spawned.stdout) {
        mixed.add(spawned.stdout);
      }
      if (spawned.stderr) {
        mixed.add(spawned.stderr);
      }
      return mixed;
    };
    var getBufferedData = async (stream, streamPromise) => {
      if (!stream) {
        return;
      }
      stream.destroy();
      try {
        return await streamPromise;
      } catch (error) {
        return error.bufferedData;
      }
    };
    var getStreamPromise = (stream, { encoding, buffer, maxBuffer }) => {
      if (!stream || !buffer) {
        return;
      }
      if (encoding) {
        return getStream(stream, { encoding, maxBuffer });
      }
      return getStream.buffer(stream, { maxBuffer });
    };
    var getSpawnedResult = async ({ stdout, stderr, all }, { encoding, buffer, maxBuffer }, processDone) => {
      const stdoutPromise = getStreamPromise(stdout, { encoding, buffer, maxBuffer });
      const stderrPromise = getStreamPromise(stderr, { encoding, buffer, maxBuffer });
      const allPromise = getStreamPromise(all, { encoding, buffer, maxBuffer: maxBuffer * 2 });
      try {
        return await Promise.all([processDone, stdoutPromise, stderrPromise, allPromise]);
      } catch (error) {
        return Promise.all([
          { error, signal: error.signal, timedOut: error.timedOut },
          getBufferedData(stdout, stdoutPromise),
          getBufferedData(stderr, stderrPromise),
          getBufferedData(all, allPromise)
        ]);
      }
    };
    var validateInputSync = ({ input }) => {
      if (isStream(input)) {
        throw new TypeError("The `input` option cannot be a stream in sync mode");
      }
    };
    module2.exports = {
      handleInput,
      makeAllStream,
      getSpawnedResult,
      validateInputSync
    };
  }
});
var require_promise = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/execa@5.1.1/node_modules/execa/lib/promise.js"(exports, module2) {
    "use strict";
    var nativePromisePrototype = (async () => {
    })().constructor.prototype;
    var descriptors = ["then", "catch", "finally"].map((property) => [
      property,
      Reflect.getOwnPropertyDescriptor(nativePromisePrototype, property)
    ]);
    var mergePromise = (spawned, promise) => {
      for (const [property, descriptor] of descriptors) {
        const value = typeof promise === "function" ? (...args) => Reflect.apply(descriptor.value, promise(), args) : descriptor.value.bind(promise);
        Reflect.defineProperty(spawned, property, { ...descriptor, value });
      }
      return spawned;
    };
    var getSpawnedPromise = (spawned) => {
      return new Promise((resolve, reject) => {
        spawned.on("exit", (exitCode, signal) => {
          resolve({ exitCode, signal });
        });
        spawned.on("error", (error) => {
          reject(error);
        });
        if (spawned.stdin) {
          spawned.stdin.on("error", (error) => {
            reject(error);
          });
        }
      });
    };
    module2.exports = {
      mergePromise,
      getSpawnedPromise
    };
  }
});
var require_command = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/execa@5.1.1/node_modules/execa/lib/command.js"(exports, module2) {
    "use strict";
    var normalizeArgs = (file2, args = []) => {
      if (!Array.isArray(args)) {
        return [file2];
      }
      return [file2, ...args];
    };
    var NO_ESCAPE_REGEXP = /^[\w.-]+$/;
    var DOUBLE_QUOTES_REGEXP = /"/g;
    var escapeArg = (arg) => {
      if (typeof arg !== "string" || NO_ESCAPE_REGEXP.test(arg)) {
        return arg;
      }
      return `"${arg.replace(DOUBLE_QUOTES_REGEXP, '\\"')}"`;
    };
    var joinCommand = (file2, args) => {
      return normalizeArgs(file2, args).join(" ");
    };
    var getEscapedCommand = (file2, args) => {
      return normalizeArgs(file2, args).map((arg) => escapeArg(arg)).join(" ");
    };
    var SPACES_REGEXP = / +/g;
    var parseCommand = (command) => {
      const tokens = [];
      for (const token of command.trim().split(SPACES_REGEXP)) {
        const previousToken = tokens[tokens.length - 1];
        if (previousToken && previousToken.endsWith("\\")) {
          tokens[tokens.length - 1] = `${previousToken.slice(0, -1)} ${token}`;
        } else {
          tokens.push(token);
        }
      }
      return tokens;
    };
    module2.exports = {
      joinCommand,
      getEscapedCommand,
      parseCommand
    };
  }
});
var require_execa = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/execa@5.1.1/node_modules/execa/index.js"(exports, module2) {
    "use strict";
    var path2 = (0, import_chunk_AH6QHEOA.__require)("path");
    var childProcess = (0, import_chunk_AH6QHEOA.__require)("child_process");
    var crossSpawn = require_cross_spawn();
    var stripFinalNewline = require_strip_final_newline();
    var npmRunPath = require_npm_run_path();
    var onetime = require_onetime();
    var makeError = require_error();
    var normalizeStdio = require_stdio();
    var { spawnedKill, spawnedCancel, setupTimeout, validateTimeout, setExitHandler } = require_kill();
    var { handleInput, getSpawnedResult, makeAllStream, validateInputSync } = require_stream();
    var { mergePromise, getSpawnedPromise } = require_promise();
    var { joinCommand, parseCommand, getEscapedCommand } = require_command();
    var DEFAULT_MAX_BUFFER = 1e3 * 1e3 * 100;
    var getEnv = ({ env: envOption, extendEnv, preferLocal, localDir, execPath }) => {
      const env = extendEnv ? { ...process.env, ...envOption } : envOption;
      if (preferLocal) {
        return npmRunPath.env({ env, cwd: localDir, execPath });
      }
      return env;
    };
    var handleArguments = (file2, args, options2 = {}) => {
      const parsed = crossSpawn._parse(file2, args, options2);
      file2 = parsed.command;
      args = parsed.args;
      options2 = parsed.options;
      options2 = {
        maxBuffer: DEFAULT_MAX_BUFFER,
        buffer: true,
        stripFinalNewline: true,
        extendEnv: true,
        preferLocal: false,
        localDir: options2.cwd || process.cwd(),
        execPath: process.execPath,
        encoding: "utf8",
        reject: true,
        cleanup: true,
        all: false,
        windowsHide: true,
        ...options2
      };
      options2.env = getEnv(options2);
      options2.stdio = normalizeStdio(options2);
      if (process.platform === "win32" && path2.basename(file2, ".exe") === "cmd") {
        args.unshift("/q");
      }
      return { file: file2, args, options: options2, parsed };
    };
    var handleOutput = (options2, value, error) => {
      if (typeof value !== "string" && !Buffer.isBuffer(value)) {
        return error === void 0 ? void 0 : "";
      }
      if (options2.stripFinalNewline) {
        return stripFinalNewline(value);
      }
      return value;
    };
    var execa2 = (file2, args, options2) => {
      const parsed = handleArguments(file2, args, options2);
      const command = joinCommand(file2, args);
      const escapedCommand = getEscapedCommand(file2, args);
      validateTimeout(parsed.options);
      let spawned;
      try {
        spawned = childProcess.spawn(parsed.file, parsed.args, parsed.options);
      } catch (error) {
        const dummySpawned = new childProcess.ChildProcess();
        const errorPromise = Promise.reject(makeError({
          error,
          stdout: "",
          stderr: "",
          all: "",
          command,
          escapedCommand,
          parsed,
          timedOut: false,
          isCanceled: false,
          killed: false
        }));
        return mergePromise(dummySpawned, errorPromise);
      }
      const spawnedPromise = getSpawnedPromise(spawned);
      const timedPromise = setupTimeout(spawned, parsed.options, spawnedPromise);
      const processDone = setExitHandler(spawned, parsed.options, timedPromise);
      const context = { isCanceled: false };
      spawned.kill = spawnedKill.bind(null, spawned.kill.bind(spawned));
      spawned.cancel = spawnedCancel.bind(null, spawned, context);
      const handlePromise = async () => {
        const [{ error, exitCode, signal, timedOut }, stdoutResult, stderrResult, allResult] = await getSpawnedResult(spawned, parsed.options, processDone);
        const stdout = handleOutput(parsed.options, stdoutResult);
        const stderr = handleOutput(parsed.options, stderrResult);
        const all = handleOutput(parsed.options, allResult);
        if (error || exitCode !== 0 || signal !== null) {
          const returnedError = makeError({
            error,
            exitCode,
            signal,
            stdout,
            stderr,
            all,
            command,
            escapedCommand,
            parsed,
            timedOut,
            isCanceled: context.isCanceled,
            killed: spawned.killed
          });
          if (!parsed.options.reject) {
            return returnedError;
          }
          throw returnedError;
        }
        return {
          command,
          escapedCommand,
          exitCode: 0,
          stdout,
          stderr,
          all,
          failed: false,
          timedOut: false,
          isCanceled: false,
          killed: false
        };
      };
      const handlePromiseOnce = onetime(handlePromise);
      handleInput(spawned, parsed.options.input);
      spawned.all = makeAllStream(spawned, parsed.options);
      return mergePromise(spawned, handlePromiseOnce);
    };
    module2.exports = execa2;
    module2.exports.sync = (file2, args, options2) => {
      const parsed = handleArguments(file2, args, options2);
      const command = joinCommand(file2, args);
      const escapedCommand = getEscapedCommand(file2, args);
      validateInputSync(parsed.options);
      let result;
      try {
        result = childProcess.spawnSync(parsed.file, parsed.args, parsed.options);
      } catch (error) {
        throw makeError({
          error,
          stdout: "",
          stderr: "",
          all: "",
          command,
          escapedCommand,
          parsed,
          timedOut: false,
          isCanceled: false,
          killed: false
        });
      }
      const stdout = handleOutput(parsed.options, result.stdout, result.error);
      const stderr = handleOutput(parsed.options, result.stderr, result.error);
      if (result.error || result.status !== 0 || result.signal !== null) {
        const error = makeError({
          stdout,
          stderr,
          error: result.error,
          signal: result.signal,
          exitCode: result.status,
          command,
          escapedCommand,
          parsed,
          timedOut: result.error && result.error.code === "ETIMEDOUT",
          isCanceled: false,
          killed: result.signal !== null
        });
        if (!parsed.options.reject) {
          return error;
        }
        throw error;
      }
      return {
        command,
        escapedCommand,
        exitCode: 0,
        stdout,
        stderr,
        failed: false,
        timedOut: false,
        isCanceled: false,
        killed: false
      };
    };
    module2.exports.command = (command, options2) => {
      const [file2, ...args] = parseCommand(command);
      return execa2(file2, args, options2);
    };
    module2.exports.commandSync = (command, options2) => {
      const [file2, ...args] = parseCommand(command);
      return execa2.sync(file2, args, options2);
    };
    module2.exports.node = (scriptPath, args, options2 = {}) => {
      if (args && !Array.isArray(args) && typeof args === "object") {
        options2 = args;
        args = [];
      }
      const stdio = normalizeStdio.node(options2);
      const defaultExecArgv = process.execArgv.filter((arg) => !arg.startsWith("--inspect"));
      const {
        nodePath = process.execPath,
        nodeOptions = defaultExecArgv
      } = options2;
      return execa2(
        nodePath,
        [
          ...nodeOptions,
          scriptPath,
          ...Array.isArray(args) ? args : []
        ],
        {
          ...options2,
          stdin: void 0,
          stdout: void 0,
          stderr: void 0,
          stdio,
          shell: false
        }
      );
    };
  }
});
var require_p_map = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/p-map@2.1.0/node_modules/p-map/index.js"(exports, module2) {
    "use strict";
    var pMap = (iterable, mapper, options2) => new Promise((resolve, reject) => {
      options2 = Object.assign({
        concurrency: Infinity
      }, options2);
      if (typeof mapper !== "function") {
        throw new TypeError("Mapper function is required");
      }
      const { concurrency } = options2;
      if (!(typeof concurrency === "number" && concurrency >= 1)) {
        throw new TypeError(`Expected \`concurrency\` to be a number from 1 and up, got \`${concurrency}\` (${typeof concurrency})`);
      }
      const ret = [];
      const iterator = iterable[Symbol.iterator]();
      let isRejected = false;
      let isIterableDone = false;
      let resolvingCount = 0;
      let currentIndex = 0;
      const next = () => {
        if (isRejected) {
          return;
        }
        const nextItem = iterator.next();
        const i = currentIndex;
        currentIndex++;
        if (nextItem.done) {
          isIterableDone = true;
          if (resolvingCount === 0) {
            resolve(ret);
          }
          return;
        }
        resolvingCount++;
        Promise.resolve(nextItem.value).then((element) => mapper(element, i)).then(
          (value) => {
            ret[i] = value;
            resolvingCount--;
            next();
          },
          (error) => {
            isRejected = true;
            reject(error);
          }
        );
      };
      for (let i = 0; i < concurrency; i++) {
        next();
        if (isIterableDone) {
          break;
        }
      }
    });
    module2.exports = pMap;
    module2.exports.default = pMap;
  }
});
var require_p_filter = (0, import_chunk_AH6QHEOA.__commonJS)({
  "../../node_modules/.pnpm/p-filter@2.1.0/node_modules/p-filter/index.js"(exports, module2) {
    "use strict";
    var pMap = require_p_map();
    var pFilter2 = async (iterable, filterer, options2) => {
      const values = await pMap(
        iterable,
        (element, index) => Promise.all([filterer(element, index), element]),
        options2
      );
      return values.filter((value) => Boolean(value[0])).map((value) => value[1]);
    };
    module2.exports = pFilter2;
    module2.exports.default = pFilter2;
  }
});
var require_package = (0, import_chunk_AH6QHEOA.__commonJS)({
  "package.json"(exports, module2) {
    module2.exports = {
      name: "@prisma/fetch-engine",
      version: "5.22.0",
      description: "This package is intended for Prisma's internal use",
      main: "dist/index.js",
      types: "dist/index.d.ts",
      license: "Apache-2.0",
      author: "Tim Suchanek <suchanek@prisma.io>",
      homepage: "https://www.prisma.io",
      repository: {
        type: "git",
        url: "https://github.com/prisma/prisma.git",
        directory: "packages/fetch-engine"
      },
      bugs: "https://github.com/prisma/prisma/issues",
      enginesOverride: {},
      devDependencies: {
        "@swc/core": "1.6.13",
        "@swc/jest": "0.2.36",
        "@types/jest": "29.5.12",
        "@types/node": "18.19.31",
        "@types/progress": "2.0.7",
        del: "6.1.1",
        execa: "5.1.1",
        "find-cache-dir": "5.0.0",
        "fs-extra": "11.1.1",
        hasha: "5.2.2",
        "http-proxy-agent": "7.0.2",
        "https-proxy-agent": "7.0.5",
        jest: "29.7.0",
        kleur: "4.1.5",
        "node-fetch": "3.3.2",
        "p-filter": "2.1.0",
        "p-map": "4.0.0",
        "p-retry": "4.6.2",
        progress: "2.0.3",
        rimraf: "3.0.2",
        "strip-ansi": "6.0.1",
        "temp-dir": "2.0.0",
        tempy: "1.0.1",
        "timeout-signal": "2.0.0",
        typescript: "5.4.5"
      },
      dependencies: {
        "@prisma/debug": "workspace:*",
        "@prisma/engines-version": "5.22.0-44.605197351a3c8bdd595af2d2a9bc3025bca48ea2",
        "@prisma/get-platform": "workspace:*"
      },
      scripts: {
        dev: "DEV=true tsx helpers/build.ts",
        build: "tsx helpers/build.ts",
        test: "jest",
        prepublishOnly: "pnpm run build"
      },
      files: [
        "README.md",
        "dist"
      ],
      sideEffects: false
    };
  }
});
var import_execa = (0, import_chunk_AH6QHEOA.__toESM)(require_execa());
var import_fs_extra = (0, import_chunk_AH6QHEOA.__toESM)((0, import_chunk_FQ2BOR66.require_lib)());
var import_p_filter = (0, import_chunk_AH6QHEOA.__toESM)(require_p_filter());
var import_temp_dir = (0, import_chunk_AH6QHEOA.__toESM)((0, import_chunk_QLWYUM7O.require_temp_dir)());
var { enginesOverride } = require_package();
var debug = (0, import_debug.default)("prisma:fetch-engine:download");
var exists = (0, import_util.promisify)(import_fs.default.exists);
var channel = "master";
var vercelPkgPathRegex = /^((\w:[\\\/])|\/)snapshot[\/\\]/;
async function download(options) {
  if (enginesOverride?.["branch"] || enginesOverride?.["folder"]) {
    options.version = "_local_";
    options.skipCacheIntegrityCheck = true;
  }
  const { binaryTarget, ...os } = await (0, import_get_platform.getPlatformInfo)();
  if (os.targetDistro && ["nixos"].includes(os.targetDistro) && !(0, import_chunk_PXQVM7NP.allEngineEnvVarsSet)(Object.keys(options.binaries))) {
    console.error(
      `${(0, import_chunk_PXQVM7NP.yellow)("Warning")} Precompiled engine files are not available for ${os.targetDistro}, please provide the paths via environment variables, see https://pris.ly/d/custom-engines`
    );
  } else if (["freebsd11", "freebsd12", "freebsd13", "freebsd14", "freebsd15", "openbsd", "netbsd"].includes(binaryTarget)) {
    console.error(
      `${(0, import_chunk_PXQVM7NP.yellow)(
        "Warning"
      )} Precompiled engine files are not available for ${binaryTarget}. Read more about building your own engines at https://pris.ly/d/build-engines`
    );
  } else if ("libquery-engine" in options.binaries) {
    (0, import_get_platform.assertNodeAPISupported)();
  }
  if (!options.binaries || Object.values(options.binaries).length === 0) {
    return {};
  }
  const opts = {
    ...options,
    binaryTargets: options.binaryTargets ?? [binaryTarget],
    version: options.version ?? "latest",
    binaries: options.binaries
  };
  const binaryJobs = Object.entries(opts.binaries).flatMap(
    ([binaryName, targetFolder]) => opts.binaryTargets.map((binaryTarget2) => {
      const fileName = getBinaryName(binaryName, binaryTarget2);
      const targetFilePath = import_path.default.join(targetFolder, fileName);
      return {
        binaryName,
        targetFolder,
        binaryTarget: binaryTarget2,
        fileName,
        targetFilePath,
        envVarPath: (0, import_chunk_PXQVM7NP.getBinaryEnvVarPath)(binaryName)?.path,
        skipCacheIntegrityCheck: !!opts.skipCacheIntegrityCheck
      };
    })
  );
  if (process.env.BINARY_DOWNLOAD_VERSION) {
    debug(`process.env.BINARY_DOWNLOAD_VERSION is set to "${process.env.BINARY_DOWNLOAD_VERSION}"`);
    opts.version = process.env.BINARY_DOWNLOAD_VERSION;
  }
  if (opts.printVersion) {
    console.log(`version: ${opts.version}`);
  }
  const binariesToDownload = await (0, import_p_filter.default)(binaryJobs, async (job) => {
    const needsToBeDownloaded = await binaryNeedsToBeDownloaded(job, binaryTarget, opts.version);
    const isSupported = import_get_platform.binaryTargets.includes(job.binaryTarget);
    const shouldDownload = isSupported && !job.envVarPath && // this is for custom binaries
    needsToBeDownloaded;
    if (needsToBeDownloaded && !isSupported) {
      throw new Error(`Unknown binaryTarget ${job.binaryTarget} and no custom engine files were provided`);
    }
    return shouldDownload;
  });
  if (binariesToDownload.length > 0) {
    const cleanupPromise = (0, import_chunk_QSTZGX47.cleanupCache)();
    let finishBar;
    let setProgress;
    if (opts.showProgress) {
      const collectiveBar = getCollectiveBar(opts);
      finishBar = collectiveBar.finishBar;
      setProgress = collectiveBar.setProgress;
    }
    const promises = binariesToDownload.map((job) => {
      const downloadUrl = (0, import_chunk_FQ2BOR66.getDownloadUrl)({
        channel: "all_commits",
        version: opts.version,
        binaryTarget: job.binaryTarget,
        binaryName: job.binaryName
      });
      debug(`${downloadUrl} will be downloaded to ${job.targetFilePath}`);
      return downloadBinary({
        ...job,
        downloadUrl,
        version: opts.version,
        failSilent: opts.failSilent,
        progressCb: setProgress ? setProgress(job.targetFilePath) : void 0
      });
    });
    await Promise.all(promises);
    await cleanupPromise;
    if (finishBar) {
      finishBar();
    }
  }
  const binaryPaths = binaryJobsToBinaryPaths(binaryJobs);
  const dir = eval("__dirname");
  if (dir.match(vercelPkgPathRegex)) {
    for (const engineType in binaryPaths) {
      const binaryTargets2 = binaryPaths[engineType];
      for (const binaryTarget2 in binaryTargets2) {
        const binaryPath = binaryTargets2[binaryTarget2];
        binaryTargets2[binaryTarget2] = await maybeCopyToTmp(binaryPath);
      }
    }
  }
  return binaryPaths;
}
function getCollectiveBar(options2) {
  const hasNodeAPI = "libquery-engine" in options2.binaries;
  const bar = (0, import_chunk_4LX3XBNY.getBar)(
    `Downloading Prisma engines${hasNodeAPI ? " for Node-API" : ""} for ${options2.binaryTargets?.map((p) => (0, import_chunk_PXQVM7NP.bold)(p)).join(" and ")}`
  );
  const progressMap = {};
  const numDownloads = Object.values(options2.binaries).length * Object.values(options2?.binaryTargets ?? []).length;
  const setProgress = (sourcePath) => (progress) => {
    progressMap[sourcePath] = progress;
    const progressValues = Object.values(progressMap);
    const totalProgress = progressValues.reduce((acc, curr) => {
      return acc + curr;
    }, 0) / numDownloads;
    if (options2.progressCb) {
      options2.progressCb(totalProgress);
    }
    if (bar) {
      bar.update(totalProgress);
    }
  };
  return {
    setProgress,
    finishBar: () => {
      bar.update(1);
      bar.terminate();
    }
  };
}
function binaryJobsToBinaryPaths(jobs) {
  return jobs.reduce((acc, job) => {
    if (!acc[job.binaryName]) {
      acc[job.binaryName] = {};
    }
    acc[job.binaryName][job.binaryTarget] = job.envVarPath || job.targetFilePath;
    return acc;
  }, {});
}
async function binaryNeedsToBeDownloaded(job, nativePlatform, version) {
  if (job.envVarPath && import_fs.default.existsSync(job.envVarPath)) {
    return false;
  }
  const targetExists = await exists(job.targetFilePath);
  const cachedFile = await getCachedBinaryPath({
    ...job,
    version
  });
  if (cachedFile) {
    if (job.skipCacheIntegrityCheck === true) {
      await (0, import_chunk_FQ2BOR66.overwriteFile)(cachedFile, job.targetFilePath);
      return false;
    }
    const sha256FilePath = cachedFile + ".sha256";
    if (await exists(sha256FilePath)) {
      const sha256File = await import_fs.default.promises.readFile(sha256FilePath, "utf-8");
      const sha256Cache = await (0, import_chunk_CWGQAQ3T.getHash)(cachedFile);
      if (sha256File === sha256Cache) {
        if (!targetExists) {
          debug(`copying ${cachedFile} to ${job.targetFilePath}`);
          await import_fs.default.promises.utimes(cachedFile, /* @__PURE__ */ new Date(), /* @__PURE__ */ new Date());
          await (0, import_chunk_FQ2BOR66.overwriteFile)(cachedFile, job.targetFilePath);
        }
        const targetSha256 = await (0, import_chunk_CWGQAQ3T.getHash)(job.targetFilePath);
        if (sha256File !== targetSha256) {
          debug(`overwriting ${job.targetFilePath} with ${cachedFile} as hashes do not match`);
          await (0, import_chunk_FQ2BOR66.overwriteFile)(cachedFile, job.targetFilePath);
        }
        return false;
      } else {
        return true;
      }
    } else if (process.env.PRISMA_ENGINES_CHECKSUM_IGNORE_MISSING) {
      debug(
        `The checksum file: ${sha256FilePath} is missing but this was ignored as the PRISMA_ENGINES_CHECKSUM_IGNORE_MISSING environment variable is truthy.`
      );
      return false;
    } else {
      return true;
    }
  }
  if (!targetExists) {
    debug(`file ${job.targetFilePath} does not exist and must be downloaded`);
    return true;
  }
  if (job.binaryTarget === nativePlatform) {
    const currentVersion = await getVersion(job.targetFilePath, job.binaryName);
    if (currentVersion?.includes(version) !== true) {
      debug(`file ${job.targetFilePath} exists but its version is ${currentVersion} and we expect ${version}`);
      return true;
    }
  }
  return false;
}
async function getVersion(enginePath, binaryName) {
  try {
    if (binaryName === "libquery-engine") {
      (0, import_get_platform.assertNodeAPISupported)();
      const commitHash = (0, import_chunk_AH6QHEOA.__require)(enginePath).version().commit;
      return `${"libquery-engine"} ${commitHash}`;
    } else {
      const result = await (0, import_execa.default)(enginePath, ["--version"]);
      return result.stdout;
    }
  } catch {
  }
  return void 0;
}
function getBinaryName(binaryName, binaryTarget2) {
  if (binaryName === "libquery-engine") {
    return `${(0, import_get_platform.getNodeAPIName)(binaryTarget2, "fs")}`;
  }
  const extension = binaryTarget2 === "windows" ? ".exe" : "";
  return `${binaryName}-${binaryTarget2}${extension}`;
}
async function getCachedBinaryPath({
  version,
  binaryTarget: binaryTarget2,
  binaryName
}) {
  const cacheDir = await (0, import_chunk_FQ2BOR66.getCacheDir)(channel, version, binaryTarget2);
  if (!cacheDir) {
    return null;
  }
  const cachedTargetPath = import_path.default.join(cacheDir, binaryName);
  if (!import_fs.default.existsSync(cachedTargetPath)) {
    return null;
  }
  if (version !== "latest") {
    return cachedTargetPath;
  }
  if (await exists(cachedTargetPath)) {
    return cachedTargetPath;
  }
  return null;
}
async function downloadBinary(options2) {
  const { version, progressCb, targetFilePath, downloadUrl } = options2;
  const targetDir = import_path.default.dirname(targetFilePath);
  try {
    import_fs.default.accessSync(targetDir, import_fs.default.constants.W_OK);
    await (0, import_fs_extra.ensureDir)(targetDir);
  } catch (e) {
    if (options2.failSilent || e.code !== "EACCES") {
      return;
    } else {
      throw new Error(`Can't write to ${targetDir} please make sure you install "prisma" with the right permissions.`);
    }
  }
  debug(`Downloading ${downloadUrl} to ${targetFilePath} ...`);
  if (progressCb) {
    progressCb(0);
  }
  const { sha256, zippedSha256 } = await (0, import_chunk_QLWYUM7O.downloadZip)(downloadUrl, targetFilePath, progressCb);
  if (progressCb) {
    progressCb(1);
  }
  (0, import_chunk_MX3HXAU2.chmodPlusX)(targetFilePath);
  await saveFileToCache(options2, version, sha256, zippedSha256);
}
async function saveFileToCache(job, version, sha256, zippedSha256) {
  const cacheDir = await (0, import_chunk_FQ2BOR66.getCacheDir)(channel, version, job.binaryTarget);
  if (!cacheDir) {
    return;
  }
  const cachedTargetPath = import_path.default.join(cacheDir, job.binaryName);
  const cachedSha256Path = import_path.default.join(cacheDir, job.binaryName + ".sha256");
  const cachedSha256ZippedPath = import_path.default.join(cacheDir, job.binaryName + ".gz.sha256");
  try {
    await (0, import_chunk_FQ2BOR66.overwriteFile)(job.targetFilePath, cachedTargetPath);
    if (sha256 != null) {
      await import_fs.default.promises.writeFile(cachedSha256Path, sha256);
    }
    if (zippedSha256 != null) {
      await import_fs.default.promises.writeFile(cachedSha256ZippedPath, zippedSha256);
    }
  } catch (e) {
    debug(e);
  }
}
async function maybeCopyToTmp(file) {
  const dir = eval("__dirname");
  if (dir.match(vercelPkgPathRegex)) {
    const targetDir = import_path.default.join(import_temp_dir.default, "prisma-binaries");
    await (0, import_fs_extra.ensureDir)(targetDir);
    const target = import_path.default.join(targetDir, import_path.default.basename(file));
    const data = await import_fs.default.promises.readFile(file);
    await import_fs.default.promises.writeFile(target, data);
    plusX(target);
    return target;
  }
  return file;
}
function plusX(file2) {
  const s = import_fs.default.statSync(file2);
  const newMode = s.mode | 64 | 8 | 1;
  if (s.mode === newMode) {
    return;
  }
  const base8 = newMode.toString(8).slice(-3);
  import_fs.default.chmodSync(file2, base8);
}
