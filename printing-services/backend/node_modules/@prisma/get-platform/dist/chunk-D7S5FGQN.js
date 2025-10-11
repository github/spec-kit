"use strict";
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
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
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);
var chunk_D7S5FGQN_exports = {};
__export(chunk_D7S5FGQN_exports, {
  link: () => link
});
module.exports = __toCommonJS(chunk_D7S5FGQN_exports);
var import_chunk_YVXCXD3A = require("./chunk-YVXCXD3A.js");
var import_chunk_2ESYSVXG = require("./chunk-2ESYSVXG.js");
var require_ansi_escapes = (0, import_chunk_2ESYSVXG.__commonJS)({
  "../../node_modules/.pnpm/ansi-escapes@4.3.2/node_modules/ansi-escapes/index.js"(exports, module2) {
    "use strict";
    var ansiEscapes = module2.exports;
    module2.exports.default = ansiEscapes;
    var ESC = "\x1B[";
    var OSC = "\x1B]";
    var BEL = "\x07";
    var SEP = ";";
    var isTerminalApp = process.env.TERM_PROGRAM === "Apple_Terminal";
    ansiEscapes.cursorTo = (x, y) => {
      if (typeof x !== "number") {
        throw new TypeError("The `x` argument is required");
      }
      if (typeof y !== "number") {
        return ESC + (x + 1) + "G";
      }
      return ESC + (y + 1) + ";" + (x + 1) + "H";
    };
    ansiEscapes.cursorMove = (x, y) => {
      if (typeof x !== "number") {
        throw new TypeError("The `x` argument is required");
      }
      let ret = "";
      if (x < 0) {
        ret += ESC + -x + "D";
      } else if (x > 0) {
        ret += ESC + x + "C";
      }
      if (y < 0) {
        ret += ESC + -y + "A";
      } else if (y > 0) {
        ret += ESC + y + "B";
      }
      return ret;
    };
    ansiEscapes.cursorUp = (count = 1) => ESC + count + "A";
    ansiEscapes.cursorDown = (count = 1) => ESC + count + "B";
    ansiEscapes.cursorForward = (count = 1) => ESC + count + "C";
    ansiEscapes.cursorBackward = (count = 1) => ESC + count + "D";
    ansiEscapes.cursorLeft = ESC + "G";
    ansiEscapes.cursorSavePosition = isTerminalApp ? "\x1B7" : ESC + "s";
    ansiEscapes.cursorRestorePosition = isTerminalApp ? "\x1B8" : ESC + "u";
    ansiEscapes.cursorGetPosition = ESC + "6n";
    ansiEscapes.cursorNextLine = ESC + "E";
    ansiEscapes.cursorPrevLine = ESC + "F";
    ansiEscapes.cursorHide = ESC + "?25l";
    ansiEscapes.cursorShow = ESC + "?25h";
    ansiEscapes.eraseLines = (count) => {
      let clear = "";
      for (let i = 0; i < count; i++) {
        clear += ansiEscapes.eraseLine + (i < count - 1 ? ansiEscapes.cursorUp() : "");
      }
      if (count) {
        clear += ansiEscapes.cursorLeft;
      }
      return clear;
    };
    ansiEscapes.eraseEndLine = ESC + "K";
    ansiEscapes.eraseStartLine = ESC + "1K";
    ansiEscapes.eraseLine = ESC + "2K";
    ansiEscapes.eraseDown = ESC + "J";
    ansiEscapes.eraseUp = ESC + "1J";
    ansiEscapes.eraseScreen = ESC + "2J";
    ansiEscapes.scrollUp = ESC + "S";
    ansiEscapes.scrollDown = ESC + "T";
    ansiEscapes.clearScreen = "\x1Bc";
    ansiEscapes.clearTerminal = process.platform === "win32" ? `${ansiEscapes.eraseScreen}${ESC}0f` : (
      // 1. Erases the screen (Only done in case `2` is not supported)
      // 2. Erases the whole screen including scrollback buffer
      // 3. Moves cursor to the top-left position
      // More info: https://www.real-world-systems.com/docs/ANSIcode.html
      `${ansiEscapes.eraseScreen}${ESC}3J${ESC}H`
    );
    ansiEscapes.beep = BEL;
    ansiEscapes.link = (text, url) => {
      return [
        OSC,
        "8",
        SEP,
        SEP,
        url,
        BEL,
        text,
        OSC,
        "8",
        SEP,
        SEP,
        BEL
      ].join("");
    };
    ansiEscapes.image = (buffer, options = {}) => {
      let ret = `${OSC}1337;File=inline=1`;
      if (options.width) {
        ret += `;width=${options.width}`;
      }
      if (options.height) {
        ret += `;height=${options.height}`;
      }
      if (options.preserveAspectRatio === false) {
        ret += ";preserveAspectRatio=0";
      }
      return ret + ":" + buffer.toString("base64") + BEL;
    };
    ansiEscapes.iTerm = {
      setCwd: (cwd = process.cwd()) => `${OSC}50;CurrentDir=${cwd}${BEL}`,
      annotation: (message, options = {}) => {
        let ret = `${OSC}1337;`;
        const hasX = typeof options.x !== "undefined";
        const hasY = typeof options.y !== "undefined";
        if ((hasX || hasY) && !(hasX && hasY && typeof options.length !== "undefined")) {
          throw new Error("`x`, `y` and `length` must be defined when `x` or `y` is defined");
        }
        message = message.replace(/\|/g, "");
        ret += options.isHidden ? "AddHiddenAnnotation=" : "AddAnnotation=";
        if (options.length > 0) {
          ret += (hasX ? [message, options.length, options.x, options.y] : [options.length, message]).join("|");
        } else {
          ret += message;
        }
        return ret + BEL;
      }
    };
  }
});
var require_has_flag = (0, import_chunk_2ESYSVXG.__commonJS)({
  "../../node_modules/.pnpm/has-flag@4.0.0/node_modules/has-flag/index.js"(exports, module2) {
    "use strict";
    module2.exports = (flag, argv = process.argv) => {
      const prefix = flag.startsWith("-") ? "" : flag.length === 1 ? "-" : "--";
      const position = argv.indexOf(prefix + flag);
      const terminatorPosition = argv.indexOf("--");
      return position !== -1 && (terminatorPosition === -1 || position < terminatorPosition);
    };
  }
});
var require_supports_color = (0, import_chunk_2ESYSVXG.__commonJS)({
  "../../node_modules/.pnpm/supports-color@7.2.0/node_modules/supports-color/index.js"(exports, module2) {
    "use strict";
    var os = (0, import_chunk_2ESYSVXG.__require)("os");
    var tty = (0, import_chunk_2ESYSVXG.__require)("tty");
    var hasFlag = require_has_flag();
    var { env } = process;
    var forceColor;
    if (hasFlag("no-color") || hasFlag("no-colors") || hasFlag("color=false") || hasFlag("color=never")) {
      forceColor = 0;
    } else if (hasFlag("color") || hasFlag("colors") || hasFlag("color=true") || hasFlag("color=always")) {
      forceColor = 1;
    }
    if ("FORCE_COLOR" in env) {
      if (env.FORCE_COLOR === "true") {
        forceColor = 1;
      } else if (env.FORCE_COLOR === "false") {
        forceColor = 0;
      } else {
        forceColor = env.FORCE_COLOR.length === 0 ? 1 : Math.min(parseInt(env.FORCE_COLOR, 10), 3);
      }
    }
    function translateLevel(level) {
      if (level === 0) {
        return false;
      }
      return {
        level,
        hasBasic: true,
        has256: level >= 2,
        has16m: level >= 3
      };
    }
    function supportsColor(haveStream, streamIsTTY) {
      if (forceColor === 0) {
        return 0;
      }
      if (hasFlag("color=16m") || hasFlag("color=full") || hasFlag("color=truecolor")) {
        return 3;
      }
      if (hasFlag("color=256")) {
        return 2;
      }
      if (haveStream && !streamIsTTY && forceColor === void 0) {
        return 0;
      }
      const min = forceColor || 0;
      if (env.TERM === "dumb") {
        return min;
      }
      if (process.platform === "win32") {
        const osRelease = os.release().split(".");
        if (Number(osRelease[0]) >= 10 && Number(osRelease[2]) >= 10586) {
          return Number(osRelease[2]) >= 14931 ? 3 : 2;
        }
        return 1;
      }
      if ("CI" in env) {
        if (["TRAVIS", "CIRCLECI", "APPVEYOR", "GITLAB_CI", "GITHUB_ACTIONS", "BUILDKITE"].some((sign) => sign in env) || env.CI_NAME === "codeship") {
          return 1;
        }
        return min;
      }
      if ("TEAMCITY_VERSION" in env) {
        return /^(9\.(0*[1-9]\d*)\.|\d{2,}\.)/.test(env.TEAMCITY_VERSION) ? 1 : 0;
      }
      if (env.COLORTERM === "truecolor") {
        return 3;
      }
      if ("TERM_PROGRAM" in env) {
        const version = parseInt((env.TERM_PROGRAM_VERSION || "").split(".")[0], 10);
        switch (env.TERM_PROGRAM) {
          case "iTerm.app":
            return version >= 3 ? 3 : 2;
          case "Apple_Terminal":
            return 2;
        }
      }
      if (/-256(color)?$/i.test(env.TERM)) {
        return 2;
      }
      if (/^screen|^xterm|^vt100|^vt220|^rxvt|color|ansi|cygwin|linux/i.test(env.TERM)) {
        return 1;
      }
      if ("COLORTERM" in env) {
        return 1;
      }
      return min;
    }
    function getSupportLevel(stream) {
      const level = supportsColor(stream, stream && stream.isTTY);
      return translateLevel(level);
    }
    module2.exports = {
      supportsColor: getSupportLevel,
      stdout: translateLevel(supportsColor(true, tty.isatty(1))),
      stderr: translateLevel(supportsColor(true, tty.isatty(2)))
    };
  }
});
var require_supports_hyperlinks = (0, import_chunk_2ESYSVXG.__commonJS)({
  "../../node_modules/.pnpm/supports-hyperlinks@2.3.0/node_modules/supports-hyperlinks/index.js"(exports, module2) {
    "use strict";
    var supportsColor = require_supports_color();
    var hasFlag = require_has_flag();
    function parseVersion(versionString) {
      if (/^\d{3,4}$/.test(versionString)) {
        const m = /(\d{1,2})(\d{2})/.exec(versionString);
        return {
          major: 0,
          minor: parseInt(m[1], 10),
          patch: parseInt(m[2], 10)
        };
      }
      const versions = (versionString || "").split(".").map((n) => parseInt(n, 10));
      return {
        major: versions[0],
        minor: versions[1],
        patch: versions[2]
      };
    }
    function supportsHyperlink(stream) {
      const { env } = process;
      if ("FORCE_HYPERLINK" in env) {
        return !(env.FORCE_HYPERLINK.length > 0 && parseInt(env.FORCE_HYPERLINK, 10) === 0);
      }
      if (hasFlag("no-hyperlink") || hasFlag("no-hyperlinks") || hasFlag("hyperlink=false") || hasFlag("hyperlink=never")) {
        return false;
      }
      if (hasFlag("hyperlink=true") || hasFlag("hyperlink=always")) {
        return true;
      }
      if ("NETLIFY" in env) {
        return true;
      }
      if (!supportsColor.supportsColor(stream)) {
        return false;
      }
      if (stream && !stream.isTTY) {
        return false;
      }
      if (process.platform === "win32") {
        return false;
      }
      if ("CI" in env) {
        return false;
      }
      if ("TEAMCITY_VERSION" in env) {
        return false;
      }
      if ("TERM_PROGRAM" in env) {
        const version = parseVersion(env.TERM_PROGRAM_VERSION);
        switch (env.TERM_PROGRAM) {
          case "iTerm.app":
            if (version.major === 3) {
              return version.minor >= 1;
            }
            return version.major > 3;
          case "WezTerm":
            return version.major >= 20200620;
          case "vscode":
            return version.major > 1 || version.major === 1 && version.minor >= 72;
        }
      }
      if ("VTE_VERSION" in env) {
        if (env.VTE_VERSION === "0.50.0") {
          return false;
        }
        const version = parseVersion(env.VTE_VERSION);
        return version.major > 0 || version.minor >= 50;
      }
      return false;
    }
    module2.exports = {
      supportsHyperlink,
      stdout: supportsHyperlink(process.stdout),
      stderr: supportsHyperlink(process.stderr)
    };
  }
});
var require_terminal_link = (0, import_chunk_2ESYSVXG.__commonJS)({
  "../../node_modules/.pnpm/terminal-link@2.1.1/node_modules/terminal-link/index.js"(exports, module2) {
    "use strict";
    var ansiEscapes = require_ansi_escapes();
    var supportsHyperlinks = require_supports_hyperlinks();
    var terminalLink2 = (text, url, { target = "stdout", ...options } = {}) => {
      if (!supportsHyperlinks[target]) {
        if (options.fallback === false) {
          return text;
        }
        return typeof options.fallback === "function" ? options.fallback(text, url) : `${text} (\u200B${url}\u200B)`;
      }
      return ansiEscapes.link(text, url);
    };
    module2.exports = (text, url, options = {}) => terminalLink2(text, url, options);
    module2.exports.stderr = (text, url, options = {}) => terminalLink2(text, url, { target: "stderr", ...options });
    module2.exports.isSupported = supportsHyperlinks.stdout;
    module2.exports.stderr.isSupported = supportsHyperlinks.stderr;
  }
});
var import_terminal_link = (0, import_chunk_2ESYSVXG.__toESM)(require_terminal_link());
function link(url) {
  return (0, import_terminal_link.default)(url, url, {
    fallback: import_chunk_YVXCXD3A.underline
  });
}
