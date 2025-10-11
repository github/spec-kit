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
var jestSnapshotSerializer_exports = {};
__export(jestSnapshotSerializer_exports, {
  default: () => jestSnapshotSerializer_default
});
module.exports = __toCommonJS(jestSnapshotSerializer_exports);
var import_chunk_B23KD6U3 = require("../chunk-B23KD6U3.js");
var import_chunk_7MLUNQIZ = require("../chunk-7MLUNQIZ.js");
var import_chunk_2ESYSVXG = require("../chunk-2ESYSVXG.js");
var require_replace_string = (0, import_chunk_2ESYSVXG.__commonJS)({
  "../../node_modules/.pnpm/replace-string@3.1.0/node_modules/replace-string/index.js"(exports, module2) {
    "use strict";
    module2.exports = (string, needle, replacement, options = {}) => {
      if (typeof string !== "string") {
        throw new TypeError(`Expected input to be a string, got ${typeof string}`);
      }
      if (!(typeof needle === "string" && needle.length > 0) || !(typeof replacement === "string" || typeof replacement === "function")) {
        return string;
      }
      let result = "";
      let matchCount = 0;
      let prevIndex = options.fromIndex > 0 ? options.fromIndex : 0;
      if (prevIndex > string.length) {
        return string;
      }
      while (true) {
        const index = options.caseInsensitive ? string.toLowerCase().indexOf(needle.toLowerCase(), prevIndex) : string.indexOf(needle, prevIndex);
        if (index === -1) {
          break;
        }
        matchCount++;
        const replaceStr = typeof replacement === "string" ? replacement : replacement(
          // If `caseInsensitive`` is enabled, the matched substring may be different from the needle.
          string.slice(index, index + needle.length),
          matchCount,
          string,
          index
        );
        const beginSlice = matchCount === 1 ? 0 : prevIndex;
        result += string.slice(beginSlice, index) + replaceStr;
        prevIndex = index + needle.length;
      }
      if (matchCount === 0) {
        return string;
      }
      return result + string.slice(prevIndex);
    };
  }
});
var require_ansi_regex = (0, import_chunk_2ESYSVXG.__commonJS)({
  "../../node_modules/.pnpm/ansi-regex@5.0.1/node_modules/ansi-regex/index.js"(exports, module2) {
    "use strict";
    module2.exports = ({ onlyFirst = false } = {}) => {
      const pattern = [
        "[\\u001B\\u009B][[\\]()#;?]*(?:(?:(?:(?:;[-a-zA-Z\\d\\/#&.:=?%@~_]+)*|[a-zA-Z\\d]+(?:;[-a-zA-Z\\d\\/#&.:=?%@~_]*)*)?\\u0007)",
        "(?:(?:\\d{1,4}(?:;\\d{0,4})*)?[\\dA-PR-TZcf-ntqry=><~]))"
      ].join("|");
      return new RegExp(pattern, onlyFirst ? void 0 : "g");
    };
  }
});
var require_strip_ansi = (0, import_chunk_2ESYSVXG.__commonJS)({
  "../../node_modules/.pnpm/strip-ansi@6.0.1/node_modules/strip-ansi/index.js"(exports, module2) {
    "use strict";
    var ansiRegex = require_ansi_regex();
    module2.exports = (string) => typeof string === "string" ? string.replace(ansiRegex(), "") : string;
  }
});
var require_jestSnapshotSerializer = (0, import_chunk_2ESYSVXG.__commonJS)({
  "src/test-utils/jestSnapshotSerializer.js"(exports, module2) {
    var path = (0, import_chunk_2ESYSVXG.__require)("path");
    var replaceAll = require_replace_string();
    var stripAnsi = require_strip_ansi();
    var { binaryTargetRegex } = ((0, import_chunk_B23KD6U3.init_binaryTargetRegex)(), (0, import_chunk_2ESYSVXG.__toCommonJS)(import_chunk_B23KD6U3.binaryTargetRegex_exports));
    var pipe = (...fns) => (x) => fns.reduce((v, f) => f(v), x);
    function normalizePrismaPaths(str) {
      return str.replace(/prisma\\([\w-]+)\.prisma/g, "prisma/$1.prisma").replace(/prisma\\seed\.ts/g, "prisma/seed.ts").replace(/custom-folder\\seed\.js/g, "custom-folder/seed.js");
    }
    function normalizeLogs(str) {
      return str.replace(
        /Started query engine http server on http:\/\/127\.0\.0\.1:\d{1,5}/g,
        "Started query engine http server on http://127.0.0.1:00000"
      ).replace(/Starting a postgresql pool with \d+ connections./g, "Starting a postgresql pool with XX connections.");
    }
    function normalizeTmpDir(str) {
      return str.replace(/\/tmp\/([a-z0-9]+)\//g, "/tmp/dir/");
    }
    function trimErrorPaths(str) {
      const parentDir = path.dirname(path.dirname(path.dirname(__dirname)));
      return replaceAll(str, parentDir, "");
    }
    function normalizeToUnixPaths(str) {
      return replaceAll(str, path.sep, "/");
    }
    function normalizeGitHubLinks(str) {
      return str.replace(/https:\/\/github.com\/prisma\/prisma(-client-js)?\/issues\/new\S+/, "TEST_GITHUB_LINK");
    }
    function normalizeTsClientStackTrace(str) {
      return str.replace(/([/\\]client[/\\]src[/\\]__tests__[/\\].*test\.ts)(:\d*:\d*)/, "$1:0:0").replace(/([/\\]client[/\\]tests[/\\]functional[/\\].*\.ts)(:\d*:\d*)/, "$1:0:0");
    }
    function removePlatforms(str) {
      return str.replace(binaryTargetRegex, "TEST_PLATFORM");
    }
    function normalizeNodeApiLibFilePath(str) {
      return str.replace(
        /((lib)?query_engine-TEST_PLATFORM\.)(.*)(\.node)/g,
        "libquery_engine-TEST_PLATFORM.LIBRARY_TYPE.node"
      );
    }
    function normalizeBinaryFilePath(str) {
      return str.replace(/\.exe(\s+)?(\W.*)/g, "$1$2").replace(/\.exe$/g, "");
    }
    function normalizeMigrateTimestamps(str) {
      return str.replace(/(?<!\d)\d{14}(?!\d)/g, "20201231000000");
    }
    function normalizeDbUrl(str) {
      return str.replace(/(localhost|postgres|mysql|mssql|mongodb_migrate|cockroachdb):(\d+)/g, "localhost:$2");
    }
    function normalizeRustError(str) {
      return str.replace(/\/rustc\/(.+)\//g, "/rustc/hash/").replace(/(\[.*)(:\d*:\d*)(\])/g, "[/some/rust/path:0:0$3");
    }
    function normalizeRustCodeLocation(str) {
      return str.replace(/(\w+\.rs):(\d+):(\d+)/g, "$1:0:0");
    }
    function normalizeArtificialPanic(str) {
      return str.replace(/(Command failed with exit code 101:) (.+) /g, "$1 prisma-engines-path ");
    }
    function normalizeTime(str) {
      return str.replace(/ \d+ms/g, " XXXms").replace(/ \d+(\.\d+)?s/g, " XXXms");
    }
    function prepareSchemaForSnapshot(str) {
      if (!str.includes("tmp/prisma-tests/integration-test")) return str;
      const urlRegex = /url\s*=\s*.+/;
      const outputRegex = /output\s*=\s*.+/;
      return str.split("\n").map((line) => {
        const urlMatch = urlRegex.exec(line);
        if (urlMatch) {
          return `${line.slice(0, urlMatch.index)}url = "***"`;
        }
        const outputMatch = outputRegex.exec(line);
        if (outputMatch) {
          return `${line.slice(0, outputMatch.index)}output = "***"`;
        }
        return line;
      }).join("\n");
    }
    function wrapWithQuotes(str) {
      return `"${str}"`;
    }
    module2.exports = {
      // Expected by Jest
      test(value) {
        return typeof value === "string" || value instanceof Error;
      },
      serialize(value) {
        const message = typeof value === "string" ? value : value instanceof Error ? value.message : "";
        return pipe(
          stripAnsi,
          // integration-tests pkg
          prepareSchemaForSnapshot,
          // Generic
          normalizeTmpDir,
          normalizeTime,
          // From Client package
          normalizeGitHubLinks,
          removePlatforms,
          normalizeNodeApiLibFilePath,
          normalizeBinaryFilePath,
          normalizeTsClientStackTrace,
          trimErrorPaths,
          normalizePrismaPaths,
          normalizeLogs,
          // remove windows \\
          normalizeToUnixPaths,
          // From Migrate/CLI package
          normalizeDbUrl,
          normalizeRustError,
          normalizeRustCodeLocation,
          normalizeMigrateTimestamps,
          // artificial panic
          normalizeArtificialPanic,
          wrapWithQuotes
        )(message);
      }
    };
  }
});
var jestSnapshotSerializer_default = require_jestSnapshotSerializer();
