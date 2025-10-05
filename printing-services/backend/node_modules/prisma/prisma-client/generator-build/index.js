"use strict";
var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __esm = (fn, res) => function __init() {
  return fn && (res = (0, fn[__getOwnPropNames(fn)[0]])(fn = 0)), res;
};
var __commonJS = (cb, mod) => function __require() {
  return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
};
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
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// ../../node_modules/.pnpm/@prisma+engines-version@5.22.0-44.605197351a3c8bdd595af2d2a9bc3025bca48ea2/node_modules/@prisma/engines-version/package.json
var require_package = __commonJS({
  "../../node_modules/.pnpm/@prisma+engines-version@5.22.0-44.605197351a3c8bdd595af2d2a9bc3025bca48ea2/node_modules/@prisma/engines-version/package.json"(exports2, module2) {
    module2.exports = {
      name: "@prisma/engines-version",
      version: "5.22.0-44.605197351a3c8bdd595af2d2a9bc3025bca48ea2",
      main: "index.js",
      types: "index.d.ts",
      license: "Apache-2.0",
      author: "Tim Suchanek <suchanek@prisma.io>",
      prisma: {
        enginesVersion: "605197351a3c8bdd595af2d2a9bc3025bca48ea2"
      },
      repository: {
        type: "git",
        url: "https://github.com/prisma/engines-wrapper.git",
        directory: "packages/engines-version"
      },
      devDependencies: {
        "@types/node": "18.19.34",
        typescript: "4.9.5"
      },
      files: [
        "index.js",
        "index.d.ts"
      ],
      scripts: {
        build: "tsc -d"
      }
    };
  }
});

// ../../node_modules/.pnpm/@prisma+engines-version@5.22.0-44.605197351a3c8bdd595af2d2a9bc3025bca48ea2/node_modules/@prisma/engines-version/index.js
var require_engines_version = __commonJS({
  "../../node_modules/.pnpm/@prisma+engines-version@5.22.0-44.605197351a3c8bdd595af2d2a9bc3025bca48ea2/node_modules/@prisma/engines-version/index.js"(exports2) {
    "use strict";
    Object.defineProperty(exports2, "__esModule", { value: true });
    exports2.enginesVersion = void 0;
    exports2.enginesVersion = require_package().prisma.enginesVersion;
  }
});

// ../../node_modules/.pnpm/universalify@2.0.0/node_modules/universalify/index.js
var require_universalify = __commonJS({
  "../../node_modules/.pnpm/universalify@2.0.0/node_modules/universalify/index.js"(exports2) {
    "use strict";
    exports2.fromCallback = function(fn) {
      return Object.defineProperty(function(...args) {
        if (typeof args[args.length - 1] === "function") fn.apply(this, args);
        else {
          return new Promise((resolve, reject) => {
            fn.call(
              this,
              ...args,
              (err, res) => err != null ? reject(err) : resolve(res)
            );
          });
        }
      }, "name", { value: fn.name });
    };
    exports2.fromPromise = function(fn) {
      return Object.defineProperty(function(...args) {
        const cb = args[args.length - 1];
        if (typeof cb !== "function") return fn.apply(this, args);
        else fn.apply(this, args.slice(0, -1)).then((r) => cb(null, r), cb);
      }, "name", { value: fn.name });
    };
  }
});

// ../../node_modules/.pnpm/graceful-fs@4.2.10/node_modules/graceful-fs/polyfills.js
var require_polyfills = __commonJS({
  "../../node_modules/.pnpm/graceful-fs@4.2.10/node_modules/graceful-fs/polyfills.js"(exports2, module2) {
    "use strict";
    var constants = require("constants");
    var origCwd = process.cwd;
    var cwd2 = null;
    var platform = process.env.GRACEFUL_FS_PLATFORM || process.platform;
    process.cwd = function() {
      if (!cwd2)
        cwd2 = origCwd.call(process);
      return cwd2;
    };
    try {
      process.cwd();
    } catch (er) {
    }
    if (typeof process.chdir === "function") {
      chdir = process.chdir;
      process.chdir = function(d) {
        cwd2 = null;
        chdir.call(process, d);
      };
      if (Object.setPrototypeOf) Object.setPrototypeOf(process.chdir, chdir);
    }
    var chdir;
    module2.exports = patch;
    function patch(fs3) {
      if (constants.hasOwnProperty("O_SYMLINK") && process.version.match(/^v0\.6\.[0-2]|^v0\.5\./)) {
        patchLchmod(fs3);
      }
      if (!fs3.lutimes) {
        patchLutimes(fs3);
      }
      fs3.chown = chownFix(fs3.chown);
      fs3.fchown = chownFix(fs3.fchown);
      fs3.lchown = chownFix(fs3.lchown);
      fs3.chmod = chmodFix(fs3.chmod);
      fs3.fchmod = chmodFix(fs3.fchmod);
      fs3.lchmod = chmodFix(fs3.lchmod);
      fs3.chownSync = chownFixSync(fs3.chownSync);
      fs3.fchownSync = chownFixSync(fs3.fchownSync);
      fs3.lchownSync = chownFixSync(fs3.lchownSync);
      fs3.chmodSync = chmodFixSync(fs3.chmodSync);
      fs3.fchmodSync = chmodFixSync(fs3.fchmodSync);
      fs3.lchmodSync = chmodFixSync(fs3.lchmodSync);
      fs3.stat = statFix(fs3.stat);
      fs3.fstat = statFix(fs3.fstat);
      fs3.lstat = statFix(fs3.lstat);
      fs3.statSync = statFixSync(fs3.statSync);
      fs3.fstatSync = statFixSync(fs3.fstatSync);
      fs3.lstatSync = statFixSync(fs3.lstatSync);
      if (fs3.chmod && !fs3.lchmod) {
        fs3.lchmod = function(path5, mode, cb) {
          if (cb) process.nextTick(cb);
        };
        fs3.lchmodSync = function() {
        };
      }
      if (fs3.chown && !fs3.lchown) {
        fs3.lchown = function(path5, uid, gid, cb) {
          if (cb) process.nextTick(cb);
        };
        fs3.lchownSync = function() {
        };
      }
      if (platform === "win32") {
        fs3.rename = typeof fs3.rename !== "function" ? fs3.rename : function(fs$rename) {
          function rename(from, to, cb) {
            var start = Date.now();
            var backoff = 0;
            fs$rename(from, to, function CB(er) {
              if (er && (er.code === "EACCES" || er.code === "EPERM") && Date.now() - start < 6e4) {
                setTimeout(function() {
                  fs3.stat(to, function(stater, st) {
                    if (stater && stater.code === "ENOENT")
                      fs$rename(from, to, CB);
                    else
                      cb(er);
                  });
                }, backoff);
                if (backoff < 100)
                  backoff += 10;
                return;
              }
              if (cb) cb(er);
            });
          }
          if (Object.setPrototypeOf) Object.setPrototypeOf(rename, fs$rename);
          return rename;
        }(fs3.rename);
      }
      fs3.read = typeof fs3.read !== "function" ? fs3.read : function(fs$read) {
        function read(fd, buffer2, offset, length, position, callback_) {
          var callback;
          if (callback_ && typeof callback_ === "function") {
            var eagCounter = 0;
            callback = function(er, _, __) {
              if (er && er.code === "EAGAIN" && eagCounter < 10) {
                eagCounter++;
                return fs$read.call(fs3, fd, buffer2, offset, length, position, callback);
              }
              callback_.apply(this, arguments);
            };
          }
          return fs$read.call(fs3, fd, buffer2, offset, length, position, callback);
        }
        if (Object.setPrototypeOf) Object.setPrototypeOf(read, fs$read);
        return read;
      }(fs3.read);
      fs3.readSync = typeof fs3.readSync !== "function" ? fs3.readSync : /* @__PURE__ */ function(fs$readSync) {
        return function(fd, buffer2, offset, length, position) {
          var eagCounter = 0;
          while (true) {
            try {
              return fs$readSync.call(fs3, fd, buffer2, offset, length, position);
            } catch (er) {
              if (er.code === "EAGAIN" && eagCounter < 10) {
                eagCounter++;
                continue;
              }
              throw er;
            }
          }
        };
      }(fs3.readSync);
      function patchLchmod(fs4) {
        fs4.lchmod = function(path5, mode, callback) {
          fs4.open(
            path5,
            constants.O_WRONLY | constants.O_SYMLINK,
            mode,
            function(err, fd) {
              if (err) {
                if (callback) callback(err);
                return;
              }
              fs4.fchmod(fd, mode, function(err2) {
                fs4.close(fd, function(err22) {
                  if (callback) callback(err2 || err22);
                });
              });
            }
          );
        };
        fs4.lchmodSync = function(path5, mode) {
          var fd = fs4.openSync(path5, constants.O_WRONLY | constants.O_SYMLINK, mode);
          var threw = true;
          var ret;
          try {
            ret = fs4.fchmodSync(fd, mode);
            threw = false;
          } finally {
            if (threw) {
              try {
                fs4.closeSync(fd);
              } catch (er) {
              }
            } else {
              fs4.closeSync(fd);
            }
          }
          return ret;
        };
      }
      function patchLutimes(fs4) {
        if (constants.hasOwnProperty("O_SYMLINK") && fs4.futimes) {
          fs4.lutimes = function(path5, at, mt, cb) {
            fs4.open(path5, constants.O_SYMLINK, function(er, fd) {
              if (er) {
                if (cb) cb(er);
                return;
              }
              fs4.futimes(fd, at, mt, function(er2) {
                fs4.close(fd, function(er22) {
                  if (cb) cb(er2 || er22);
                });
              });
            });
          };
          fs4.lutimesSync = function(path5, at, mt) {
            var fd = fs4.openSync(path5, constants.O_SYMLINK);
            var ret;
            var threw = true;
            try {
              ret = fs4.futimesSync(fd, at, mt);
              threw = false;
            } finally {
              if (threw) {
                try {
                  fs4.closeSync(fd);
                } catch (er) {
                }
              } else {
                fs4.closeSync(fd);
              }
            }
            return ret;
          };
        } else if (fs4.futimes) {
          fs4.lutimes = function(_a, _b, _c, cb) {
            if (cb) process.nextTick(cb);
          };
          fs4.lutimesSync = function() {
          };
        }
      }
      function chmodFix(orig) {
        if (!orig) return orig;
        return function(target, mode, cb) {
          return orig.call(fs3, target, mode, function(er) {
            if (chownErOk(er)) er = null;
            if (cb) cb.apply(this, arguments);
          });
        };
      }
      function chmodFixSync(orig) {
        if (!orig) return orig;
        return function(target, mode) {
          try {
            return orig.call(fs3, target, mode);
          } catch (er) {
            if (!chownErOk(er)) throw er;
          }
        };
      }
      function chownFix(orig) {
        if (!orig) return orig;
        return function(target, uid, gid, cb) {
          return orig.call(fs3, target, uid, gid, function(er) {
            if (chownErOk(er)) er = null;
            if (cb) cb.apply(this, arguments);
          });
        };
      }
      function chownFixSync(orig) {
        if (!orig) return orig;
        return function(target, uid, gid) {
          try {
            return orig.call(fs3, target, uid, gid);
          } catch (er) {
            if (!chownErOk(er)) throw er;
          }
        };
      }
      function statFix(orig) {
        if (!orig) return orig;
        return function(target, options, cb) {
          if (typeof options === "function") {
            cb = options;
            options = null;
          }
          function callback(er, stats) {
            if (stats) {
              if (stats.uid < 0) stats.uid += 4294967296;
              if (stats.gid < 0) stats.gid += 4294967296;
            }
            if (cb) cb.apply(this, arguments);
          }
          return options ? orig.call(fs3, target, options, callback) : orig.call(fs3, target, callback);
        };
      }
      function statFixSync(orig) {
        if (!orig) return orig;
        return function(target, options) {
          var stats = options ? orig.call(fs3, target, options) : orig.call(fs3, target);
          if (stats) {
            if (stats.uid < 0) stats.uid += 4294967296;
            if (stats.gid < 0) stats.gid += 4294967296;
          }
          return stats;
        };
      }
      function chownErOk(er) {
        if (!er)
          return true;
        if (er.code === "ENOSYS")
          return true;
        var nonroot = !process.getuid || process.getuid() !== 0;
        if (nonroot) {
          if (er.code === "EINVAL" || er.code === "EPERM")
            return true;
        }
        return false;
      }
    }
  }
});

// ../../node_modules/.pnpm/graceful-fs@4.2.10/node_modules/graceful-fs/legacy-streams.js
var require_legacy_streams = __commonJS({
  "../../node_modules/.pnpm/graceful-fs@4.2.10/node_modules/graceful-fs/legacy-streams.js"(exports2, module2) {
    "use strict";
    var Stream = require("stream").Stream;
    module2.exports = legacy;
    function legacy(fs3) {
      return {
        ReadStream,
        WriteStream
      };
      function ReadStream(path5, options) {
        if (!(this instanceof ReadStream)) return new ReadStream(path5, options);
        Stream.call(this);
        var self = this;
        this.path = path5;
        this.fd = null;
        this.readable = true;
        this.paused = false;
        this.flags = "r";
        this.mode = 438;
        this.bufferSize = 64 * 1024;
        options = options || {};
        var keys = Object.keys(options);
        for (var index = 0, length = keys.length; index < length; index++) {
          var key = keys[index];
          this[key] = options[key];
        }
        if (this.encoding) this.setEncoding(this.encoding);
        if (this.start !== void 0) {
          if ("number" !== typeof this.start) {
            throw TypeError("start must be a Number");
          }
          if (this.end === void 0) {
            this.end = Infinity;
          } else if ("number" !== typeof this.end) {
            throw TypeError("end must be a Number");
          }
          if (this.start > this.end) {
            throw new Error("start must be <= end");
          }
          this.pos = this.start;
        }
        if (this.fd !== null) {
          process.nextTick(function() {
            self._read();
          });
          return;
        }
        fs3.open(this.path, this.flags, this.mode, function(err, fd) {
          if (err) {
            self.emit("error", err);
            self.readable = false;
            return;
          }
          self.fd = fd;
          self.emit("open", fd);
          self._read();
        });
      }
      function WriteStream(path5, options) {
        if (!(this instanceof WriteStream)) return new WriteStream(path5, options);
        Stream.call(this);
        this.path = path5;
        this.fd = null;
        this.writable = true;
        this.flags = "w";
        this.encoding = "binary";
        this.mode = 438;
        this.bytesWritten = 0;
        options = options || {};
        var keys = Object.keys(options);
        for (var index = 0, length = keys.length; index < length; index++) {
          var key = keys[index];
          this[key] = options[key];
        }
        if (this.start !== void 0) {
          if ("number" !== typeof this.start) {
            throw TypeError("start must be a Number");
          }
          if (this.start < 0) {
            throw new Error("start must be >= zero");
          }
          this.pos = this.start;
        }
        this.busy = false;
        this._queue = [];
        if (this.fd === null) {
          this._open = fs3.open;
          this._queue.push([this._open, this.path, this.flags, this.mode, void 0]);
          this.flush();
        }
      }
    }
  }
});

// ../../node_modules/.pnpm/graceful-fs@4.2.10/node_modules/graceful-fs/clone.js
var require_clone = __commonJS({
  "../../node_modules/.pnpm/graceful-fs@4.2.10/node_modules/graceful-fs/clone.js"(exports2, module2) {
    "use strict";
    module2.exports = clone;
    var getPrototypeOf = Object.getPrototypeOf || function(obj) {
      return obj.__proto__;
    };
    function clone(obj) {
      if (obj === null || typeof obj !== "object")
        return obj;
      if (obj instanceof Object)
        var copy = { __proto__: getPrototypeOf(obj) };
      else
        var copy = /* @__PURE__ */ Object.create(null);
      Object.getOwnPropertyNames(obj).forEach(function(key) {
        Object.defineProperty(copy, key, Object.getOwnPropertyDescriptor(obj, key));
      });
      return copy;
    }
  }
});

// ../../node_modules/.pnpm/graceful-fs@4.2.10/node_modules/graceful-fs/graceful-fs.js
var require_graceful_fs = __commonJS({
  "../../node_modules/.pnpm/graceful-fs@4.2.10/node_modules/graceful-fs/graceful-fs.js"(exports2, module2) {
    "use strict";
    var fs3 = require("fs");
    var polyfills = require_polyfills();
    var legacy = require_legacy_streams();
    var clone = require_clone();
    var util2 = require("util");
    var gracefulQueue;
    var previousSymbol;
    if (typeof Symbol === "function" && typeof Symbol.for === "function") {
      gracefulQueue = Symbol.for("graceful-fs.queue");
      previousSymbol = Symbol.for("graceful-fs.previous");
    } else {
      gracefulQueue = "___graceful-fs.queue";
      previousSymbol = "___graceful-fs.previous";
    }
    function noop() {
    }
    function publishQueue(context, queue2) {
      Object.defineProperty(context, gracefulQueue, {
        get: function() {
          return queue2;
        }
      });
    }
    var debug4 = noop;
    if (util2.debuglog)
      debug4 = util2.debuglog("gfs4");
    else if (/\bgfs4\b/i.test(process.env.NODE_DEBUG || ""))
      debug4 = function() {
        var m = util2.format.apply(util2, arguments);
        m = "GFS4: " + m.split(/\n/).join("\nGFS4: ");
        console.error(m);
      };
    if (!fs3[gracefulQueue]) {
      queue = global[gracefulQueue] || [];
      publishQueue(fs3, queue);
      fs3.close = function(fs$close) {
        function close(fd, cb) {
          return fs$close.call(fs3, fd, function(err) {
            if (!err) {
              resetQueue();
            }
            if (typeof cb === "function")
              cb.apply(this, arguments);
          });
        }
        Object.defineProperty(close, previousSymbol, {
          value: fs$close
        });
        return close;
      }(fs3.close);
      fs3.closeSync = function(fs$closeSync) {
        function closeSync(fd) {
          fs$closeSync.apply(fs3, arguments);
          resetQueue();
        }
        Object.defineProperty(closeSync, previousSymbol, {
          value: fs$closeSync
        });
        return closeSync;
      }(fs3.closeSync);
      if (/\bgfs4\b/i.test(process.env.NODE_DEBUG || "")) {
        process.on("exit", function() {
          debug4(fs3[gracefulQueue]);
          require("assert").equal(fs3[gracefulQueue].length, 0);
        });
      }
    }
    var queue;
    if (!global[gracefulQueue]) {
      publishQueue(global, fs3[gracefulQueue]);
    }
    module2.exports = patch(clone(fs3));
    if (process.env.TEST_GRACEFUL_FS_GLOBAL_PATCH && !fs3.__patched) {
      module2.exports = patch(fs3);
      fs3.__patched = true;
    }
    function patch(fs4) {
      polyfills(fs4);
      fs4.gracefulify = patch;
      fs4.createReadStream = createReadStream;
      fs4.createWriteStream = createWriteStream;
      var fs$readFile = fs4.readFile;
      fs4.readFile = readFile;
      function readFile(path5, options, cb) {
        if (typeof options === "function")
          cb = options, options = null;
        return go$readFile(path5, options, cb);
        function go$readFile(path6, options2, cb2, startTime) {
          return fs$readFile(path6, options2, function(err) {
            if (err && (err.code === "EMFILE" || err.code === "ENFILE"))
              enqueue([go$readFile, [path6, options2, cb2], err, startTime || Date.now(), Date.now()]);
            else {
              if (typeof cb2 === "function")
                cb2.apply(this, arguments);
            }
          });
        }
      }
      var fs$writeFile = fs4.writeFile;
      fs4.writeFile = writeFile;
      function writeFile(path5, data, options, cb) {
        if (typeof options === "function")
          cb = options, options = null;
        return go$writeFile(path5, data, options, cb);
        function go$writeFile(path6, data2, options2, cb2, startTime) {
          return fs$writeFile(path6, data2, options2, function(err) {
            if (err && (err.code === "EMFILE" || err.code === "ENFILE"))
              enqueue([go$writeFile, [path6, data2, options2, cb2], err, startTime || Date.now(), Date.now()]);
            else {
              if (typeof cb2 === "function")
                cb2.apply(this, arguments);
            }
          });
        }
      }
      var fs$appendFile = fs4.appendFile;
      if (fs$appendFile)
        fs4.appendFile = appendFile;
      function appendFile(path5, data, options, cb) {
        if (typeof options === "function")
          cb = options, options = null;
        return go$appendFile(path5, data, options, cb);
        function go$appendFile(path6, data2, options2, cb2, startTime) {
          return fs$appendFile(path6, data2, options2, function(err) {
            if (err && (err.code === "EMFILE" || err.code === "ENFILE"))
              enqueue([go$appendFile, [path6, data2, options2, cb2], err, startTime || Date.now(), Date.now()]);
            else {
              if (typeof cb2 === "function")
                cb2.apply(this, arguments);
            }
          });
        }
      }
      var fs$copyFile = fs4.copyFile;
      if (fs$copyFile)
        fs4.copyFile = copyFile;
      function copyFile(src, dest, flags, cb) {
        if (typeof flags === "function") {
          cb = flags;
          flags = 0;
        }
        return go$copyFile(src, dest, flags, cb);
        function go$copyFile(src2, dest2, flags2, cb2, startTime) {
          return fs$copyFile(src2, dest2, flags2, function(err) {
            if (err && (err.code === "EMFILE" || err.code === "ENFILE"))
              enqueue([go$copyFile, [src2, dest2, flags2, cb2], err, startTime || Date.now(), Date.now()]);
            else {
              if (typeof cb2 === "function")
                cb2.apply(this, arguments);
            }
          });
        }
      }
      var fs$readdir = fs4.readdir;
      fs4.readdir = readdir;
      var noReaddirOptionVersions = /^v[0-5]\./;
      function readdir(path5, options, cb) {
        if (typeof options === "function")
          cb = options, options = null;
        var go$readdir = noReaddirOptionVersions.test(process.version) ? function go$readdir2(path6, options2, cb2, startTime) {
          return fs$readdir(path6, fs$readdirCallback(
            path6,
            options2,
            cb2,
            startTime
          ));
        } : function go$readdir2(path6, options2, cb2, startTime) {
          return fs$readdir(path6, options2, fs$readdirCallback(
            path6,
            options2,
            cb2,
            startTime
          ));
        };
        return go$readdir(path5, options, cb);
        function fs$readdirCallback(path6, options2, cb2, startTime) {
          return function(err, files) {
            if (err && (err.code === "EMFILE" || err.code === "ENFILE"))
              enqueue([
                go$readdir,
                [path6, options2, cb2],
                err,
                startTime || Date.now(),
                Date.now()
              ]);
            else {
              if (files && files.sort)
                files.sort();
              if (typeof cb2 === "function")
                cb2.call(this, err, files);
            }
          };
        }
      }
      if (process.version.substr(0, 4) === "v0.8") {
        var legStreams = legacy(fs4);
        ReadStream = legStreams.ReadStream;
        WriteStream = legStreams.WriteStream;
      }
      var fs$ReadStream = fs4.ReadStream;
      if (fs$ReadStream) {
        ReadStream.prototype = Object.create(fs$ReadStream.prototype);
        ReadStream.prototype.open = ReadStream$open;
      }
      var fs$WriteStream = fs4.WriteStream;
      if (fs$WriteStream) {
        WriteStream.prototype = Object.create(fs$WriteStream.prototype);
        WriteStream.prototype.open = WriteStream$open;
      }
      Object.defineProperty(fs4, "ReadStream", {
        get: function() {
          return ReadStream;
        },
        set: function(val) {
          ReadStream = val;
        },
        enumerable: true,
        configurable: true
      });
      Object.defineProperty(fs4, "WriteStream", {
        get: function() {
          return WriteStream;
        },
        set: function(val) {
          WriteStream = val;
        },
        enumerable: true,
        configurable: true
      });
      var FileReadStream = ReadStream;
      Object.defineProperty(fs4, "FileReadStream", {
        get: function() {
          return FileReadStream;
        },
        set: function(val) {
          FileReadStream = val;
        },
        enumerable: true,
        configurable: true
      });
      var FileWriteStream = WriteStream;
      Object.defineProperty(fs4, "FileWriteStream", {
        get: function() {
          return FileWriteStream;
        },
        set: function(val) {
          FileWriteStream = val;
        },
        enumerable: true,
        configurable: true
      });
      function ReadStream(path5, options) {
        if (this instanceof ReadStream)
          return fs$ReadStream.apply(this, arguments), this;
        else
          return ReadStream.apply(Object.create(ReadStream.prototype), arguments);
      }
      function ReadStream$open() {
        var that = this;
        open(that.path, that.flags, that.mode, function(err, fd) {
          if (err) {
            if (that.autoClose)
              that.destroy();
            that.emit("error", err);
          } else {
            that.fd = fd;
            that.emit("open", fd);
            that.read();
          }
        });
      }
      function WriteStream(path5, options) {
        if (this instanceof WriteStream)
          return fs$WriteStream.apply(this, arguments), this;
        else
          return WriteStream.apply(Object.create(WriteStream.prototype), arguments);
      }
      function WriteStream$open() {
        var that = this;
        open(that.path, that.flags, that.mode, function(err, fd) {
          if (err) {
            that.destroy();
            that.emit("error", err);
          } else {
            that.fd = fd;
            that.emit("open", fd);
          }
        });
      }
      function createReadStream(path5, options) {
        return new fs4.ReadStream(path5, options);
      }
      function createWriteStream(path5, options) {
        return new fs4.WriteStream(path5, options);
      }
      var fs$open = fs4.open;
      fs4.open = open;
      function open(path5, flags, mode, cb) {
        if (typeof mode === "function")
          cb = mode, mode = null;
        return go$open(path5, flags, mode, cb);
        function go$open(path6, flags2, mode2, cb2, startTime) {
          return fs$open(path6, flags2, mode2, function(err, fd) {
            if (err && (err.code === "EMFILE" || err.code === "ENFILE"))
              enqueue([go$open, [path6, flags2, mode2, cb2], err, startTime || Date.now(), Date.now()]);
            else {
              if (typeof cb2 === "function")
                cb2.apply(this, arguments);
            }
          });
        }
      }
      return fs4;
    }
    function enqueue(elem) {
      debug4("ENQUEUE", elem[0].name, elem[1]);
      fs3[gracefulQueue].push(elem);
      retry();
    }
    var retryTimer;
    function resetQueue() {
      var now = Date.now();
      for (var i = 0; i < fs3[gracefulQueue].length; ++i) {
        if (fs3[gracefulQueue][i].length > 2) {
          fs3[gracefulQueue][i][3] = now;
          fs3[gracefulQueue][i][4] = now;
        }
      }
      retry();
    }
    function retry() {
      clearTimeout(retryTimer);
      retryTimer = void 0;
      if (fs3[gracefulQueue].length === 0)
        return;
      var elem = fs3[gracefulQueue].shift();
      var fn = elem[0];
      var args = elem[1];
      var err = elem[2];
      var startTime = elem[3];
      var lastTime = elem[4];
      if (startTime === void 0) {
        debug4("RETRY", fn.name, args);
        fn.apply(null, args);
      } else if (Date.now() - startTime >= 6e4) {
        debug4("TIMEOUT", fn.name, args);
        var cb = args.pop();
        if (typeof cb === "function")
          cb.call(null, err);
      } else {
        var sinceAttempt = Date.now() - lastTime;
        var sinceStart = Math.max(lastTime - startTime, 1);
        var desiredDelay = Math.min(sinceStart * 1.2, 100);
        if (sinceAttempt >= desiredDelay) {
          debug4("RETRY", fn.name, args);
          fn.apply(null, args.concat([startTime]));
        } else {
          fs3[gracefulQueue].push(elem);
        }
      }
      if (retryTimer === void 0) {
        retryTimer = setTimeout(retry, 0);
      }
    }
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/fs/index.js
var require_fs = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/fs/index.js"(exports2) {
    "use strict";
    var u = require_universalify().fromCallback;
    var fs3 = require_graceful_fs();
    var api = [
      "access",
      "appendFile",
      "chmod",
      "chown",
      "close",
      "copyFile",
      "fchmod",
      "fchown",
      "fdatasync",
      "fstat",
      "fsync",
      "ftruncate",
      "futimes",
      "lchmod",
      "lchown",
      "link",
      "lstat",
      "mkdir",
      "mkdtemp",
      "open",
      "opendir",
      "readdir",
      "readFile",
      "readlink",
      "realpath",
      "rename",
      "rm",
      "rmdir",
      "stat",
      "symlink",
      "truncate",
      "unlink",
      "utimes",
      "writeFile"
    ].filter((key) => {
      return typeof fs3[key] === "function";
    });
    Object.assign(exports2, fs3);
    api.forEach((method2) => {
      exports2[method2] = u(fs3[method2]);
    });
    exports2.exists = function(filename, callback) {
      if (typeof callback === "function") {
        return fs3.exists(filename, callback);
      }
      return new Promise((resolve) => {
        return fs3.exists(filename, resolve);
      });
    };
    exports2.read = function(fd, buffer2, offset, length, position, callback) {
      if (typeof callback === "function") {
        return fs3.read(fd, buffer2, offset, length, position, callback);
      }
      return new Promise((resolve, reject) => {
        fs3.read(fd, buffer2, offset, length, position, (err, bytesRead, buffer3) => {
          if (err) return reject(err);
          resolve({ bytesRead, buffer: buffer3 });
        });
      });
    };
    exports2.write = function(fd, buffer2, ...args) {
      if (typeof args[args.length - 1] === "function") {
        return fs3.write(fd, buffer2, ...args);
      }
      return new Promise((resolve, reject) => {
        fs3.write(fd, buffer2, ...args, (err, bytesWritten, buffer3) => {
          if (err) return reject(err);
          resolve({ bytesWritten, buffer: buffer3 });
        });
      });
    };
    exports2.readv = function(fd, buffers, ...args) {
      if (typeof args[args.length - 1] === "function") {
        return fs3.readv(fd, buffers, ...args);
      }
      return new Promise((resolve, reject) => {
        fs3.readv(fd, buffers, ...args, (err, bytesRead, buffers2) => {
          if (err) return reject(err);
          resolve({ bytesRead, buffers: buffers2 });
        });
      });
    };
    exports2.writev = function(fd, buffers, ...args) {
      if (typeof args[args.length - 1] === "function") {
        return fs3.writev(fd, buffers, ...args);
      }
      return new Promise((resolve, reject) => {
        fs3.writev(fd, buffers, ...args, (err, bytesWritten, buffers2) => {
          if (err) return reject(err);
          resolve({ bytesWritten, buffers: buffers2 });
        });
      });
    };
    if (typeof fs3.realpath.native === "function") {
      exports2.realpath.native = u(fs3.realpath.native);
    } else {
      process.emitWarning(
        "fs.realpath.native is not a function. Is fs being monkey-patched?",
        "Warning",
        "fs-extra-WARN0003"
      );
    }
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/mkdirs/utils.js
var require_utils = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/mkdirs/utils.js"(exports2, module2) {
    "use strict";
    var path5 = require("path");
    module2.exports.checkPath = function checkPath(pth) {
      if (process.platform === "win32") {
        const pathHasInvalidWinCharacters = /[<>:"|?*]/.test(pth.replace(path5.parse(pth).root, ""));
        if (pathHasInvalidWinCharacters) {
          const error = new Error(`Path contains invalid characters: ${pth}`);
          error.code = "EINVAL";
          throw error;
        }
      }
    };
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/mkdirs/make-dir.js
var require_make_dir = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/mkdirs/make-dir.js"(exports2, module2) {
    "use strict";
    var fs3 = require_fs();
    var { checkPath } = require_utils();
    var getMode = (options) => {
      const defaults = { mode: 511 };
      if (typeof options === "number") return options;
      return { ...defaults, ...options }.mode;
    };
    module2.exports.makeDir = async (dir, options) => {
      checkPath(dir);
      return fs3.mkdir(dir, {
        mode: getMode(options),
        recursive: true
      });
    };
    module2.exports.makeDirSync = (dir, options) => {
      checkPath(dir);
      return fs3.mkdirSync(dir, {
        mode: getMode(options),
        recursive: true
      });
    };
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/mkdirs/index.js
var require_mkdirs = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/mkdirs/index.js"(exports2, module2) {
    "use strict";
    var u = require_universalify().fromPromise;
    var { makeDir: _makeDir, makeDirSync } = require_make_dir();
    var makeDir = u(_makeDir);
    module2.exports = {
      mkdirs: makeDir,
      mkdirsSync: makeDirSync,
      // alias
      mkdirp: makeDir,
      mkdirpSync: makeDirSync,
      ensureDir: makeDir,
      ensureDirSync: makeDirSync
    };
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/path-exists/index.js
var require_path_exists = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/path-exists/index.js"(exports2, module2) {
    "use strict";
    var u = require_universalify().fromPromise;
    var fs3 = require_fs();
    function pathExists2(path5) {
      return fs3.access(path5).then(() => true).catch(() => false);
    }
    module2.exports = {
      pathExists: u(pathExists2),
      pathExistsSync: fs3.existsSync
    };
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/util/utimes.js
var require_utimes = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/util/utimes.js"(exports2, module2) {
    "use strict";
    var fs3 = require_graceful_fs();
    function utimesMillis(path5, atime, mtime, callback) {
      fs3.open(path5, "r+", (err, fd) => {
        if (err) return callback(err);
        fs3.futimes(fd, atime, mtime, (futimesErr) => {
          fs3.close(fd, (closeErr) => {
            if (callback) callback(futimesErr || closeErr);
          });
        });
      });
    }
    function utimesMillisSync(path5, atime, mtime) {
      const fd = fs3.openSync(path5, "r+");
      fs3.futimesSync(fd, atime, mtime);
      return fs3.closeSync(fd);
    }
    module2.exports = {
      utimesMillis,
      utimesMillisSync
    };
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/util/stat.js
var require_stat = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/util/stat.js"(exports2, module2) {
    "use strict";
    var fs3 = require_fs();
    var path5 = require("path");
    var util2 = require("util");
    function getStats(src, dest, opts) {
      const statFunc = opts.dereference ? (file2) => fs3.stat(file2, { bigint: true }) : (file2) => fs3.lstat(file2, { bigint: true });
      return Promise.all([
        statFunc(src),
        statFunc(dest).catch((err) => {
          if (err.code === "ENOENT") return null;
          throw err;
        })
      ]).then(([srcStat, destStat]) => ({ srcStat, destStat }));
    }
    function getStatsSync(src, dest, opts) {
      let destStat;
      const statFunc = opts.dereference ? (file2) => fs3.statSync(file2, { bigint: true }) : (file2) => fs3.lstatSync(file2, { bigint: true });
      const srcStat = statFunc(src);
      try {
        destStat = statFunc(dest);
      } catch (err) {
        if (err.code === "ENOENT") return { srcStat, destStat: null };
        throw err;
      }
      return { srcStat, destStat };
    }
    function checkPaths(src, dest, funcName, opts, cb) {
      util2.callbackify(getStats)(src, dest, opts, (err, stats) => {
        if (err) return cb(err);
        const { srcStat, destStat } = stats;
        if (destStat) {
          if (areIdentical(srcStat, destStat)) {
            const srcBaseName = path5.basename(src);
            const destBaseName = path5.basename(dest);
            if (funcName === "move" && srcBaseName !== destBaseName && srcBaseName.toLowerCase() === destBaseName.toLowerCase()) {
              return cb(null, { srcStat, destStat, isChangingCase: true });
            }
            return cb(new Error("Source and destination must not be the same."));
          }
          if (srcStat.isDirectory() && !destStat.isDirectory()) {
            return cb(new Error(`Cannot overwrite non-directory '${dest}' with directory '${src}'.`));
          }
          if (!srcStat.isDirectory() && destStat.isDirectory()) {
            return cb(new Error(`Cannot overwrite directory '${dest}' with non-directory '${src}'.`));
          }
        }
        if (srcStat.isDirectory() && isSrcSubdir(src, dest)) {
          return cb(new Error(errMsg(src, dest, funcName)));
        }
        return cb(null, { srcStat, destStat });
      });
    }
    function checkPathsSync(src, dest, funcName, opts) {
      const { srcStat, destStat } = getStatsSync(src, dest, opts);
      if (destStat) {
        if (areIdentical(srcStat, destStat)) {
          const srcBaseName = path5.basename(src);
          const destBaseName = path5.basename(dest);
          if (funcName === "move" && srcBaseName !== destBaseName && srcBaseName.toLowerCase() === destBaseName.toLowerCase()) {
            return { srcStat, destStat, isChangingCase: true };
          }
          throw new Error("Source and destination must not be the same.");
        }
        if (srcStat.isDirectory() && !destStat.isDirectory()) {
          throw new Error(`Cannot overwrite non-directory '${dest}' with directory '${src}'.`);
        }
        if (!srcStat.isDirectory() && destStat.isDirectory()) {
          throw new Error(`Cannot overwrite directory '${dest}' with non-directory '${src}'.`);
        }
      }
      if (srcStat.isDirectory() && isSrcSubdir(src, dest)) {
        throw new Error(errMsg(src, dest, funcName));
      }
      return { srcStat, destStat };
    }
    function checkParentPaths(src, srcStat, dest, funcName, cb) {
      const srcParent = path5.resolve(path5.dirname(src));
      const destParent = path5.resolve(path5.dirname(dest));
      if (destParent === srcParent || destParent === path5.parse(destParent).root) return cb();
      fs3.stat(destParent, { bigint: true }, (err, destStat) => {
        if (err) {
          if (err.code === "ENOENT") return cb();
          return cb(err);
        }
        if (areIdentical(srcStat, destStat)) {
          return cb(new Error(errMsg(src, dest, funcName)));
        }
        return checkParentPaths(src, srcStat, destParent, funcName, cb);
      });
    }
    function checkParentPathsSync(src, srcStat, dest, funcName) {
      const srcParent = path5.resolve(path5.dirname(src));
      const destParent = path5.resolve(path5.dirname(dest));
      if (destParent === srcParent || destParent === path5.parse(destParent).root) return;
      let destStat;
      try {
        destStat = fs3.statSync(destParent, { bigint: true });
      } catch (err) {
        if (err.code === "ENOENT") return;
        throw err;
      }
      if (areIdentical(srcStat, destStat)) {
        throw new Error(errMsg(src, dest, funcName));
      }
      return checkParentPathsSync(src, srcStat, destParent, funcName);
    }
    function areIdentical(srcStat, destStat) {
      return destStat.ino && destStat.dev && destStat.ino === srcStat.ino && destStat.dev === srcStat.dev;
    }
    function isSrcSubdir(src, dest) {
      const srcArr = path5.resolve(src).split(path5.sep).filter((i) => i);
      const destArr = path5.resolve(dest).split(path5.sep).filter((i) => i);
      return srcArr.reduce((acc, cur, i) => acc && destArr[i] === cur, true);
    }
    function errMsg(src, dest, funcName) {
      return `Cannot ${funcName} '${src}' to a subdirectory of itself, '${dest}'.`;
    }
    module2.exports = {
      checkPaths,
      checkPathsSync,
      checkParentPaths,
      checkParentPathsSync,
      isSrcSubdir,
      areIdentical
    };
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/copy/copy.js
var require_copy = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/copy/copy.js"(exports2, module2) {
    "use strict";
    var fs3 = require_graceful_fs();
    var path5 = require("path");
    var mkdirs = require_mkdirs().mkdirs;
    var pathExists2 = require_path_exists().pathExists;
    var utimesMillis = require_utimes().utimesMillis;
    var stat = require_stat();
    function copy(src, dest, opts, cb) {
      if (typeof opts === "function" && !cb) {
        cb = opts;
        opts = {};
      } else if (typeof opts === "function") {
        opts = { filter: opts };
      }
      cb = cb || function() {
      };
      opts = opts || {};
      opts.clobber = "clobber" in opts ? !!opts.clobber : true;
      opts.overwrite = "overwrite" in opts ? !!opts.overwrite : opts.clobber;
      if (opts.preserveTimestamps && process.arch === "ia32") {
        process.emitWarning(
          "Using the preserveTimestamps option in 32-bit node is not recommended;\n\n	see https://github.com/jprichardson/node-fs-extra/issues/269",
          "Warning",
          "fs-extra-WARN0001"
        );
      }
      stat.checkPaths(src, dest, "copy", opts, (err, stats) => {
        if (err) return cb(err);
        const { srcStat, destStat } = stats;
        stat.checkParentPaths(src, srcStat, dest, "copy", (err2) => {
          if (err2) return cb(err2);
          runFilter(src, dest, opts, (err3, include) => {
            if (err3) return cb(err3);
            if (!include) return cb();
            checkParentDir(destStat, src, dest, opts, cb);
          });
        });
      });
    }
    function checkParentDir(destStat, src, dest, opts, cb) {
      const destParent = path5.dirname(dest);
      pathExists2(destParent, (err, dirExists) => {
        if (err) return cb(err);
        if (dirExists) return getStats(destStat, src, dest, opts, cb);
        mkdirs(destParent, (err2) => {
          if (err2) return cb(err2);
          return getStats(destStat, src, dest, opts, cb);
        });
      });
    }
    function runFilter(src, dest, opts, cb) {
      if (!opts.filter) return cb(null, true);
      Promise.resolve(opts.filter(src, dest)).then((include) => cb(null, include), (error) => cb(error));
    }
    function getStats(destStat, src, dest, opts, cb) {
      const stat2 = opts.dereference ? fs3.stat : fs3.lstat;
      stat2(src, (err, srcStat) => {
        if (err) return cb(err);
        if (srcStat.isDirectory()) return onDir(srcStat, destStat, src, dest, opts, cb);
        else if (srcStat.isFile() || srcStat.isCharacterDevice() || srcStat.isBlockDevice()) return onFile(srcStat, destStat, src, dest, opts, cb);
        else if (srcStat.isSymbolicLink()) return onLink(destStat, src, dest, opts, cb);
        else if (srcStat.isSocket()) return cb(new Error(`Cannot copy a socket file: ${src}`));
        else if (srcStat.isFIFO()) return cb(new Error(`Cannot copy a FIFO pipe: ${src}`));
        return cb(new Error(`Unknown file: ${src}`));
      });
    }
    function onFile(srcStat, destStat, src, dest, opts, cb) {
      if (!destStat) return copyFile(srcStat, src, dest, opts, cb);
      return mayCopyFile(srcStat, src, dest, opts, cb);
    }
    function mayCopyFile(srcStat, src, dest, opts, cb) {
      if (opts.overwrite) {
        fs3.unlink(dest, (err) => {
          if (err) return cb(err);
          return copyFile(srcStat, src, dest, opts, cb);
        });
      } else if (opts.errorOnExist) {
        return cb(new Error(`'${dest}' already exists`));
      } else return cb();
    }
    function copyFile(srcStat, src, dest, opts, cb) {
      fs3.copyFile(src, dest, (err) => {
        if (err) return cb(err);
        if (opts.preserveTimestamps) return handleTimestampsAndMode(srcStat.mode, src, dest, cb);
        return setDestMode(dest, srcStat.mode, cb);
      });
    }
    function handleTimestampsAndMode(srcMode, src, dest, cb) {
      if (fileIsNotWritable(srcMode)) {
        return makeFileWritable(dest, srcMode, (err) => {
          if (err) return cb(err);
          return setDestTimestampsAndMode(srcMode, src, dest, cb);
        });
      }
      return setDestTimestampsAndMode(srcMode, src, dest, cb);
    }
    function fileIsNotWritable(srcMode) {
      return (srcMode & 128) === 0;
    }
    function makeFileWritable(dest, srcMode, cb) {
      return setDestMode(dest, srcMode | 128, cb);
    }
    function setDestTimestampsAndMode(srcMode, src, dest, cb) {
      setDestTimestamps(src, dest, (err) => {
        if (err) return cb(err);
        return setDestMode(dest, srcMode, cb);
      });
    }
    function setDestMode(dest, srcMode, cb) {
      return fs3.chmod(dest, srcMode, cb);
    }
    function setDestTimestamps(src, dest, cb) {
      fs3.stat(src, (err, updatedSrcStat) => {
        if (err) return cb(err);
        return utimesMillis(dest, updatedSrcStat.atime, updatedSrcStat.mtime, cb);
      });
    }
    function onDir(srcStat, destStat, src, dest, opts, cb) {
      if (!destStat) return mkDirAndCopy(srcStat.mode, src, dest, opts, cb);
      return copyDir(src, dest, opts, cb);
    }
    function mkDirAndCopy(srcMode, src, dest, opts, cb) {
      fs3.mkdir(dest, (err) => {
        if (err) return cb(err);
        copyDir(src, dest, opts, (err2) => {
          if (err2) return cb(err2);
          return setDestMode(dest, srcMode, cb);
        });
      });
    }
    function copyDir(src, dest, opts, cb) {
      fs3.readdir(src, (err, items) => {
        if (err) return cb(err);
        return copyDirItems(items, src, dest, opts, cb);
      });
    }
    function copyDirItems(items, src, dest, opts, cb) {
      const item = items.pop();
      if (!item) return cb();
      return copyDirItem(items, item, src, dest, opts, cb);
    }
    function copyDirItem(items, item, src, dest, opts, cb) {
      const srcItem = path5.join(src, item);
      const destItem = path5.join(dest, item);
      runFilter(srcItem, destItem, opts, (err, include) => {
        if (err) return cb(err);
        if (!include) return copyDirItems(items, src, dest, opts, cb);
        stat.checkPaths(srcItem, destItem, "copy", opts, (err2, stats) => {
          if (err2) return cb(err2);
          const { destStat } = stats;
          getStats(destStat, srcItem, destItem, opts, (err3) => {
            if (err3) return cb(err3);
            return copyDirItems(items, src, dest, opts, cb);
          });
        });
      });
    }
    function onLink(destStat, src, dest, opts, cb) {
      fs3.readlink(src, (err, resolvedSrc) => {
        if (err) return cb(err);
        if (opts.dereference) {
          resolvedSrc = path5.resolve(process.cwd(), resolvedSrc);
        }
        if (!destStat) {
          return fs3.symlink(resolvedSrc, dest, cb);
        } else {
          fs3.readlink(dest, (err2, resolvedDest) => {
            if (err2) {
              if (err2.code === "EINVAL" || err2.code === "UNKNOWN") return fs3.symlink(resolvedSrc, dest, cb);
              return cb(err2);
            }
            if (opts.dereference) {
              resolvedDest = path5.resolve(process.cwd(), resolvedDest);
            }
            if (stat.isSrcSubdir(resolvedSrc, resolvedDest)) {
              return cb(new Error(`Cannot copy '${resolvedSrc}' to a subdirectory of itself, '${resolvedDest}'.`));
            }
            if (stat.isSrcSubdir(resolvedDest, resolvedSrc)) {
              return cb(new Error(`Cannot overwrite '${resolvedDest}' with '${resolvedSrc}'.`));
            }
            return copyLink(resolvedSrc, dest, cb);
          });
        }
      });
    }
    function copyLink(resolvedSrc, dest, cb) {
      fs3.unlink(dest, (err) => {
        if (err) return cb(err);
        return fs3.symlink(resolvedSrc, dest, cb);
      });
    }
    module2.exports = copy;
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/copy/copy-sync.js
var require_copy_sync = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/copy/copy-sync.js"(exports2, module2) {
    "use strict";
    var fs3 = require_graceful_fs();
    var path5 = require("path");
    var mkdirsSync = require_mkdirs().mkdirsSync;
    var utimesMillisSync = require_utimes().utimesMillisSync;
    var stat = require_stat();
    function copySync(src, dest, opts) {
      if (typeof opts === "function") {
        opts = { filter: opts };
      }
      opts = opts || {};
      opts.clobber = "clobber" in opts ? !!opts.clobber : true;
      opts.overwrite = "overwrite" in opts ? !!opts.overwrite : opts.clobber;
      if (opts.preserveTimestamps && process.arch === "ia32") {
        process.emitWarning(
          "Using the preserveTimestamps option in 32-bit node is not recommended;\n\n	see https://github.com/jprichardson/node-fs-extra/issues/269",
          "Warning",
          "fs-extra-WARN0002"
        );
      }
      const { srcStat, destStat } = stat.checkPathsSync(src, dest, "copy", opts);
      stat.checkParentPathsSync(src, srcStat, dest, "copy");
      if (opts.filter && !opts.filter(src, dest)) return;
      const destParent = path5.dirname(dest);
      if (!fs3.existsSync(destParent)) mkdirsSync(destParent);
      return getStats(destStat, src, dest, opts);
    }
    function getStats(destStat, src, dest, opts) {
      const statSync = opts.dereference ? fs3.statSync : fs3.lstatSync;
      const srcStat = statSync(src);
      if (srcStat.isDirectory()) return onDir(srcStat, destStat, src, dest, opts);
      else if (srcStat.isFile() || srcStat.isCharacterDevice() || srcStat.isBlockDevice()) return onFile(srcStat, destStat, src, dest, opts);
      else if (srcStat.isSymbolicLink()) return onLink(destStat, src, dest, opts);
      else if (srcStat.isSocket()) throw new Error(`Cannot copy a socket file: ${src}`);
      else if (srcStat.isFIFO()) throw new Error(`Cannot copy a FIFO pipe: ${src}`);
      throw new Error(`Unknown file: ${src}`);
    }
    function onFile(srcStat, destStat, src, dest, opts) {
      if (!destStat) return copyFile(srcStat, src, dest, opts);
      return mayCopyFile(srcStat, src, dest, opts);
    }
    function mayCopyFile(srcStat, src, dest, opts) {
      if (opts.overwrite) {
        fs3.unlinkSync(dest);
        return copyFile(srcStat, src, dest, opts);
      } else if (opts.errorOnExist) {
        throw new Error(`'${dest}' already exists`);
      }
    }
    function copyFile(srcStat, src, dest, opts) {
      fs3.copyFileSync(src, dest);
      if (opts.preserveTimestamps) handleTimestamps(srcStat.mode, src, dest);
      return setDestMode(dest, srcStat.mode);
    }
    function handleTimestamps(srcMode, src, dest) {
      if (fileIsNotWritable(srcMode)) makeFileWritable(dest, srcMode);
      return setDestTimestamps(src, dest);
    }
    function fileIsNotWritable(srcMode) {
      return (srcMode & 128) === 0;
    }
    function makeFileWritable(dest, srcMode) {
      return setDestMode(dest, srcMode | 128);
    }
    function setDestMode(dest, srcMode) {
      return fs3.chmodSync(dest, srcMode);
    }
    function setDestTimestamps(src, dest) {
      const updatedSrcStat = fs3.statSync(src);
      return utimesMillisSync(dest, updatedSrcStat.atime, updatedSrcStat.mtime);
    }
    function onDir(srcStat, destStat, src, dest, opts) {
      if (!destStat) return mkDirAndCopy(srcStat.mode, src, dest, opts);
      return copyDir(src, dest, opts);
    }
    function mkDirAndCopy(srcMode, src, dest, opts) {
      fs3.mkdirSync(dest);
      copyDir(src, dest, opts);
      return setDestMode(dest, srcMode);
    }
    function copyDir(src, dest, opts) {
      fs3.readdirSync(src).forEach((item) => copyDirItem(item, src, dest, opts));
    }
    function copyDirItem(item, src, dest, opts) {
      const srcItem = path5.join(src, item);
      const destItem = path5.join(dest, item);
      if (opts.filter && !opts.filter(srcItem, destItem)) return;
      const { destStat } = stat.checkPathsSync(srcItem, destItem, "copy", opts);
      return getStats(destStat, srcItem, destItem, opts);
    }
    function onLink(destStat, src, dest, opts) {
      let resolvedSrc = fs3.readlinkSync(src);
      if (opts.dereference) {
        resolvedSrc = path5.resolve(process.cwd(), resolvedSrc);
      }
      if (!destStat) {
        return fs3.symlinkSync(resolvedSrc, dest);
      } else {
        let resolvedDest;
        try {
          resolvedDest = fs3.readlinkSync(dest);
        } catch (err) {
          if (err.code === "EINVAL" || err.code === "UNKNOWN") return fs3.symlinkSync(resolvedSrc, dest);
          throw err;
        }
        if (opts.dereference) {
          resolvedDest = path5.resolve(process.cwd(), resolvedDest);
        }
        if (stat.isSrcSubdir(resolvedSrc, resolvedDest)) {
          throw new Error(`Cannot copy '${resolvedSrc}' to a subdirectory of itself, '${resolvedDest}'.`);
        }
        if (stat.isSrcSubdir(resolvedDest, resolvedSrc)) {
          throw new Error(`Cannot overwrite '${resolvedDest}' with '${resolvedSrc}'.`);
        }
        return copyLink(resolvedSrc, dest);
      }
    }
    function copyLink(resolvedSrc, dest) {
      fs3.unlinkSync(dest);
      return fs3.symlinkSync(resolvedSrc, dest);
    }
    module2.exports = copySync;
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/copy/index.js
var require_copy2 = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/copy/index.js"(exports2, module2) {
    "use strict";
    var u = require_universalify().fromCallback;
    module2.exports = {
      copy: u(require_copy()),
      copySync: require_copy_sync()
    };
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/remove/index.js
var require_remove = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/remove/index.js"(exports2, module2) {
    "use strict";
    var fs3 = require_graceful_fs();
    var u = require_universalify().fromCallback;
    function remove(path5, callback) {
      fs3.rm(path5, { recursive: true, force: true }, callback);
    }
    function removeSync(path5) {
      fs3.rmSync(path5, { recursive: true, force: true });
    }
    module2.exports = {
      remove: u(remove),
      removeSync
    };
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/empty/index.js
var require_empty = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/empty/index.js"(exports2, module2) {
    "use strict";
    var u = require_universalify().fromPromise;
    var fs3 = require_fs();
    var path5 = require("path");
    var mkdir = require_mkdirs();
    var remove = require_remove();
    var emptyDir = u(async function emptyDir2(dir) {
      let items;
      try {
        items = await fs3.readdir(dir);
      } catch {
        return mkdir.mkdirs(dir);
      }
      return Promise.all(items.map((item) => remove.remove(path5.join(dir, item))));
    });
    function emptyDirSync(dir) {
      let items;
      try {
        items = fs3.readdirSync(dir);
      } catch {
        return mkdir.mkdirsSync(dir);
      }
      items.forEach((item) => {
        item = path5.join(dir, item);
        remove.removeSync(item);
      });
    }
    module2.exports = {
      emptyDirSync,
      emptydirSync: emptyDirSync,
      emptyDir,
      emptydir: emptyDir
    };
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/ensure/file.js
var require_file = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/ensure/file.js"(exports2, module2) {
    "use strict";
    var u = require_universalify().fromCallback;
    var path5 = require("path");
    var fs3 = require_graceful_fs();
    var mkdir = require_mkdirs();
    function createFile(file2, callback) {
      function makeFile() {
        fs3.writeFile(file2, "", (err) => {
          if (err) return callback(err);
          callback();
        });
      }
      fs3.stat(file2, (err, stats) => {
        if (!err && stats.isFile()) return callback();
        const dir = path5.dirname(file2);
        fs3.stat(dir, (err2, stats2) => {
          if (err2) {
            if (err2.code === "ENOENT") {
              return mkdir.mkdirs(dir, (err3) => {
                if (err3) return callback(err3);
                makeFile();
              });
            }
            return callback(err2);
          }
          if (stats2.isDirectory()) makeFile();
          else {
            fs3.readdir(dir, (err3) => {
              if (err3) return callback(err3);
            });
          }
        });
      });
    }
    function createFileSync(file2) {
      let stats;
      try {
        stats = fs3.statSync(file2);
      } catch {
      }
      if (stats && stats.isFile()) return;
      const dir = path5.dirname(file2);
      try {
        if (!fs3.statSync(dir).isDirectory()) {
          fs3.readdirSync(dir);
        }
      } catch (err) {
        if (err && err.code === "ENOENT") mkdir.mkdirsSync(dir);
        else throw err;
      }
      fs3.writeFileSync(file2, "");
    }
    module2.exports = {
      createFile: u(createFile),
      createFileSync
    };
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/ensure/link.js
var require_link = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/ensure/link.js"(exports2, module2) {
    "use strict";
    var u = require_universalify().fromCallback;
    var path5 = require("path");
    var fs3 = require_graceful_fs();
    var mkdir = require_mkdirs();
    var pathExists2 = require_path_exists().pathExists;
    var { areIdentical } = require_stat();
    function createLink(srcpath, dstpath, callback) {
      function makeLink(srcpath2, dstpath2) {
        fs3.link(srcpath2, dstpath2, (err) => {
          if (err) return callback(err);
          callback(null);
        });
      }
      fs3.lstat(dstpath, (_, dstStat) => {
        fs3.lstat(srcpath, (err, srcStat) => {
          if (err) {
            err.message = err.message.replace("lstat", "ensureLink");
            return callback(err);
          }
          if (dstStat && areIdentical(srcStat, dstStat)) return callback(null);
          const dir = path5.dirname(dstpath);
          pathExists2(dir, (err2, dirExists) => {
            if (err2) return callback(err2);
            if (dirExists) return makeLink(srcpath, dstpath);
            mkdir.mkdirs(dir, (err3) => {
              if (err3) return callback(err3);
              makeLink(srcpath, dstpath);
            });
          });
        });
      });
    }
    function createLinkSync(srcpath, dstpath) {
      let dstStat;
      try {
        dstStat = fs3.lstatSync(dstpath);
      } catch {
      }
      try {
        const srcStat = fs3.lstatSync(srcpath);
        if (dstStat && areIdentical(srcStat, dstStat)) return;
      } catch (err) {
        err.message = err.message.replace("lstat", "ensureLink");
        throw err;
      }
      const dir = path5.dirname(dstpath);
      const dirExists = fs3.existsSync(dir);
      if (dirExists) return fs3.linkSync(srcpath, dstpath);
      mkdir.mkdirsSync(dir);
      return fs3.linkSync(srcpath, dstpath);
    }
    module2.exports = {
      createLink: u(createLink),
      createLinkSync
    };
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/ensure/symlink-paths.js
var require_symlink_paths = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/ensure/symlink-paths.js"(exports2, module2) {
    "use strict";
    var path5 = require("path");
    var fs3 = require_graceful_fs();
    var pathExists2 = require_path_exists().pathExists;
    function symlinkPaths(srcpath, dstpath, callback) {
      if (path5.isAbsolute(srcpath)) {
        return fs3.lstat(srcpath, (err) => {
          if (err) {
            err.message = err.message.replace("lstat", "ensureSymlink");
            return callback(err);
          }
          return callback(null, {
            toCwd: srcpath,
            toDst: srcpath
          });
        });
      } else {
        const dstdir = path5.dirname(dstpath);
        const relativeToDst = path5.join(dstdir, srcpath);
        return pathExists2(relativeToDst, (err, exists) => {
          if (err) return callback(err);
          if (exists) {
            return callback(null, {
              toCwd: relativeToDst,
              toDst: srcpath
            });
          } else {
            return fs3.lstat(srcpath, (err2) => {
              if (err2) {
                err2.message = err2.message.replace("lstat", "ensureSymlink");
                return callback(err2);
              }
              return callback(null, {
                toCwd: srcpath,
                toDst: path5.relative(dstdir, srcpath)
              });
            });
          }
        });
      }
    }
    function symlinkPathsSync(srcpath, dstpath) {
      let exists;
      if (path5.isAbsolute(srcpath)) {
        exists = fs3.existsSync(srcpath);
        if (!exists) throw new Error("absolute srcpath does not exist");
        return {
          toCwd: srcpath,
          toDst: srcpath
        };
      } else {
        const dstdir = path5.dirname(dstpath);
        const relativeToDst = path5.join(dstdir, srcpath);
        exists = fs3.existsSync(relativeToDst);
        if (exists) {
          return {
            toCwd: relativeToDst,
            toDst: srcpath
          };
        } else {
          exists = fs3.existsSync(srcpath);
          if (!exists) throw new Error("relative srcpath does not exist");
          return {
            toCwd: srcpath,
            toDst: path5.relative(dstdir, srcpath)
          };
        }
      }
    }
    module2.exports = {
      symlinkPaths,
      symlinkPathsSync
    };
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/ensure/symlink-type.js
var require_symlink_type = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/ensure/symlink-type.js"(exports2, module2) {
    "use strict";
    var fs3 = require_graceful_fs();
    function symlinkType(srcpath, type, callback) {
      callback = typeof type === "function" ? type : callback;
      type = typeof type === "function" ? false : type;
      if (type) return callback(null, type);
      fs3.lstat(srcpath, (err, stats) => {
        if (err) return callback(null, "file");
        type = stats && stats.isDirectory() ? "dir" : "file";
        callback(null, type);
      });
    }
    function symlinkTypeSync(srcpath, type) {
      let stats;
      if (type) return type;
      try {
        stats = fs3.lstatSync(srcpath);
      } catch {
        return "file";
      }
      return stats && stats.isDirectory() ? "dir" : "file";
    }
    module2.exports = {
      symlinkType,
      symlinkTypeSync
    };
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/ensure/symlink.js
var require_symlink = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/ensure/symlink.js"(exports2, module2) {
    "use strict";
    var u = require_universalify().fromCallback;
    var path5 = require("path");
    var fs3 = require_fs();
    var _mkdirs = require_mkdirs();
    var mkdirs = _mkdirs.mkdirs;
    var mkdirsSync = _mkdirs.mkdirsSync;
    var _symlinkPaths = require_symlink_paths();
    var symlinkPaths = _symlinkPaths.symlinkPaths;
    var symlinkPathsSync = _symlinkPaths.symlinkPathsSync;
    var _symlinkType = require_symlink_type();
    var symlinkType = _symlinkType.symlinkType;
    var symlinkTypeSync = _symlinkType.symlinkTypeSync;
    var pathExists2 = require_path_exists().pathExists;
    var { areIdentical } = require_stat();
    function createSymlink(srcpath, dstpath, type, callback) {
      callback = typeof type === "function" ? type : callback;
      type = typeof type === "function" ? false : type;
      fs3.lstat(dstpath, (err, stats) => {
        if (!err && stats.isSymbolicLink()) {
          Promise.all([
            fs3.stat(srcpath),
            fs3.stat(dstpath)
          ]).then(([srcStat, dstStat]) => {
            if (areIdentical(srcStat, dstStat)) return callback(null);
            _createSymlink(srcpath, dstpath, type, callback);
          });
        } else _createSymlink(srcpath, dstpath, type, callback);
      });
    }
    function _createSymlink(srcpath, dstpath, type, callback) {
      symlinkPaths(srcpath, dstpath, (err, relative) => {
        if (err) return callback(err);
        srcpath = relative.toDst;
        symlinkType(relative.toCwd, type, (err2, type2) => {
          if (err2) return callback(err2);
          const dir = path5.dirname(dstpath);
          pathExists2(dir, (err3, dirExists) => {
            if (err3) return callback(err3);
            if (dirExists) return fs3.symlink(srcpath, dstpath, type2, callback);
            mkdirs(dir, (err4) => {
              if (err4) return callback(err4);
              fs3.symlink(srcpath, dstpath, type2, callback);
            });
          });
        });
      });
    }
    function createSymlinkSync(srcpath, dstpath, type) {
      let stats;
      try {
        stats = fs3.lstatSync(dstpath);
      } catch {
      }
      if (stats && stats.isSymbolicLink()) {
        const srcStat = fs3.statSync(srcpath);
        const dstStat = fs3.statSync(dstpath);
        if (areIdentical(srcStat, dstStat)) return;
      }
      const relative = symlinkPathsSync(srcpath, dstpath);
      srcpath = relative.toDst;
      type = symlinkTypeSync(relative.toCwd, type);
      const dir = path5.dirname(dstpath);
      const exists = fs3.existsSync(dir);
      if (exists) return fs3.symlinkSync(srcpath, dstpath, type);
      mkdirsSync(dir);
      return fs3.symlinkSync(srcpath, dstpath, type);
    }
    module2.exports = {
      createSymlink: u(createSymlink),
      createSymlinkSync
    };
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/ensure/index.js
var require_ensure = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/ensure/index.js"(exports2, module2) {
    "use strict";
    var { createFile, createFileSync } = require_file();
    var { createLink, createLinkSync } = require_link();
    var { createSymlink, createSymlinkSync } = require_symlink();
    module2.exports = {
      // file
      createFile,
      createFileSync,
      ensureFile: createFile,
      ensureFileSync: createFileSync,
      // link
      createLink,
      createLinkSync,
      ensureLink: createLink,
      ensureLinkSync: createLinkSync,
      // symlink
      createSymlink,
      createSymlinkSync,
      ensureSymlink: createSymlink,
      ensureSymlinkSync: createSymlinkSync
    };
  }
});

// ../../node_modules/.pnpm/jsonfile@6.1.0/node_modules/jsonfile/utils.js
var require_utils2 = __commonJS({
  "../../node_modules/.pnpm/jsonfile@6.1.0/node_modules/jsonfile/utils.js"(exports2, module2) {
    "use strict";
    function stringify2(obj, { EOL = "\n", finalEOL = true, replacer = null, spaces } = {}) {
      const EOF = finalEOL ? EOL : "";
      const str = JSON.stringify(obj, replacer, spaces);
      return str.replace(/\n/g, EOL) + EOF;
    }
    function stripBom(content) {
      if (Buffer.isBuffer(content)) content = content.toString("utf8");
      return content.replace(/^\uFEFF/, "");
    }
    module2.exports = { stringify: stringify2, stripBom };
  }
});

// ../../node_modules/.pnpm/jsonfile@6.1.0/node_modules/jsonfile/index.js
var require_jsonfile = __commonJS({
  "../../node_modules/.pnpm/jsonfile@6.1.0/node_modules/jsonfile/index.js"(exports2, module2) {
    "use strict";
    var _fs;
    try {
      _fs = require_graceful_fs();
    } catch (_) {
      _fs = require("fs");
    }
    var universalify = require_universalify();
    var { stringify: stringify2, stripBom } = require_utils2();
    async function _readFile(file2, options = {}) {
      if (typeof options === "string") {
        options = { encoding: options };
      }
      const fs3 = options.fs || _fs;
      const shouldThrow = "throws" in options ? options.throws : true;
      let data = await universalify.fromCallback(fs3.readFile)(file2, options);
      data = stripBom(data);
      let obj;
      try {
        obj = JSON.parse(data, options ? options.reviver : null);
      } catch (err) {
        if (shouldThrow) {
          err.message = `${file2}: ${err.message}`;
          throw err;
        } else {
          return null;
        }
      }
      return obj;
    }
    var readFile = universalify.fromPromise(_readFile);
    function readFileSync(file2, options = {}) {
      if (typeof options === "string") {
        options = { encoding: options };
      }
      const fs3 = options.fs || _fs;
      const shouldThrow = "throws" in options ? options.throws : true;
      try {
        let content = fs3.readFileSync(file2, options);
        content = stripBom(content);
        return JSON.parse(content, options.reviver);
      } catch (err) {
        if (shouldThrow) {
          err.message = `${file2}: ${err.message}`;
          throw err;
        } else {
          return null;
        }
      }
    }
    async function _writeFile(file2, obj, options = {}) {
      const fs3 = options.fs || _fs;
      const str = stringify2(obj, options);
      await universalify.fromCallback(fs3.writeFile)(file2, str, options);
    }
    var writeFile = universalify.fromPromise(_writeFile);
    function writeFileSync(file2, obj, options = {}) {
      const fs3 = options.fs || _fs;
      const str = stringify2(obj, options);
      return fs3.writeFileSync(file2, str, options);
    }
    var jsonfile = {
      readFile,
      readFileSync,
      writeFile,
      writeFileSync
    };
    module2.exports = jsonfile;
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/json/jsonfile.js
var require_jsonfile2 = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/json/jsonfile.js"(exports2, module2) {
    "use strict";
    var jsonFile = require_jsonfile();
    module2.exports = {
      // jsonfile exports
      readJson: jsonFile.readFile,
      readJsonSync: jsonFile.readFileSync,
      writeJson: jsonFile.writeFile,
      writeJsonSync: jsonFile.writeFileSync
    };
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/output-file/index.js
var require_output_file = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/output-file/index.js"(exports2, module2) {
    "use strict";
    var u = require_universalify().fromCallback;
    var fs3 = require_graceful_fs();
    var path5 = require("path");
    var mkdir = require_mkdirs();
    var pathExists2 = require_path_exists().pathExists;
    function outputFile(file2, data, encoding, callback) {
      if (typeof encoding === "function") {
        callback = encoding;
        encoding = "utf8";
      }
      const dir = path5.dirname(file2);
      pathExists2(dir, (err, itDoes) => {
        if (err) return callback(err);
        if (itDoes) return fs3.writeFile(file2, data, encoding, callback);
        mkdir.mkdirs(dir, (err2) => {
          if (err2) return callback(err2);
          fs3.writeFile(file2, data, encoding, callback);
        });
      });
    }
    function outputFileSync(file2, ...args) {
      const dir = path5.dirname(file2);
      if (fs3.existsSync(dir)) {
        return fs3.writeFileSync(file2, ...args);
      }
      mkdir.mkdirsSync(dir);
      fs3.writeFileSync(file2, ...args);
    }
    module2.exports = {
      outputFile: u(outputFile),
      outputFileSync
    };
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/json/output-json.js
var require_output_json = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/json/output-json.js"(exports2, module2) {
    "use strict";
    var { stringify: stringify2 } = require_utils2();
    var { outputFile } = require_output_file();
    async function outputJson(file2, data, options = {}) {
      const str = stringify2(data, options);
      await outputFile(file2, str, options);
    }
    module2.exports = outputJson;
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/json/output-json-sync.js
var require_output_json_sync = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/json/output-json-sync.js"(exports2, module2) {
    "use strict";
    var { stringify: stringify2 } = require_utils2();
    var { outputFileSync } = require_output_file();
    function outputJsonSync(file2, data, options) {
      const str = stringify2(data, options);
      outputFileSync(file2, str, options);
    }
    module2.exports = outputJsonSync;
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/json/index.js
var require_json = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/json/index.js"(exports2, module2) {
    "use strict";
    var u = require_universalify().fromPromise;
    var jsonFile = require_jsonfile2();
    jsonFile.outputJson = u(require_output_json());
    jsonFile.outputJsonSync = require_output_json_sync();
    jsonFile.outputJSON = jsonFile.outputJson;
    jsonFile.outputJSONSync = jsonFile.outputJsonSync;
    jsonFile.writeJSON = jsonFile.writeJson;
    jsonFile.writeJSONSync = jsonFile.writeJsonSync;
    jsonFile.readJSON = jsonFile.readJson;
    jsonFile.readJSONSync = jsonFile.readJsonSync;
    module2.exports = jsonFile;
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/move/move.js
var require_move = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/move/move.js"(exports2, module2) {
    "use strict";
    var fs3 = require_graceful_fs();
    var path5 = require("path");
    var copy = require_copy2().copy;
    var remove = require_remove().remove;
    var mkdirp = require_mkdirs().mkdirp;
    var pathExists2 = require_path_exists().pathExists;
    var stat = require_stat();
    function move(src, dest, opts, cb) {
      if (typeof opts === "function") {
        cb = opts;
        opts = {};
      }
      opts = opts || {};
      const overwrite = opts.overwrite || opts.clobber || false;
      stat.checkPaths(src, dest, "move", opts, (err, stats) => {
        if (err) return cb(err);
        const { srcStat, isChangingCase = false } = stats;
        stat.checkParentPaths(src, srcStat, dest, "move", (err2) => {
          if (err2) return cb(err2);
          if (isParentRoot(dest)) return doRename(src, dest, overwrite, isChangingCase, cb);
          mkdirp(path5.dirname(dest), (err3) => {
            if (err3) return cb(err3);
            return doRename(src, dest, overwrite, isChangingCase, cb);
          });
        });
      });
    }
    function isParentRoot(dest) {
      const parent = path5.dirname(dest);
      const parsedPath = path5.parse(parent);
      return parsedPath.root === parent;
    }
    function doRename(src, dest, overwrite, isChangingCase, cb) {
      if (isChangingCase) return rename(src, dest, overwrite, cb);
      if (overwrite) {
        return remove(dest, (err) => {
          if (err) return cb(err);
          return rename(src, dest, overwrite, cb);
        });
      }
      pathExists2(dest, (err, destExists) => {
        if (err) return cb(err);
        if (destExists) return cb(new Error("dest already exists."));
        return rename(src, dest, overwrite, cb);
      });
    }
    function rename(src, dest, overwrite, cb) {
      fs3.rename(src, dest, (err) => {
        if (!err) return cb();
        if (err.code !== "EXDEV") return cb(err);
        return moveAcrossDevice(src, dest, overwrite, cb);
      });
    }
    function moveAcrossDevice(src, dest, overwrite, cb) {
      const opts = {
        overwrite,
        errorOnExist: true,
        preserveTimestamps: true
      };
      copy(src, dest, opts, (err) => {
        if (err) return cb(err);
        return remove(src, cb);
      });
    }
    module2.exports = move;
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/move/move-sync.js
var require_move_sync = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/move/move-sync.js"(exports2, module2) {
    "use strict";
    var fs3 = require_graceful_fs();
    var path5 = require("path");
    var copySync = require_copy2().copySync;
    var removeSync = require_remove().removeSync;
    var mkdirpSync = require_mkdirs().mkdirpSync;
    var stat = require_stat();
    function moveSync(src, dest, opts) {
      opts = opts || {};
      const overwrite = opts.overwrite || opts.clobber || false;
      const { srcStat, isChangingCase = false } = stat.checkPathsSync(src, dest, "move", opts);
      stat.checkParentPathsSync(src, srcStat, dest, "move");
      if (!isParentRoot(dest)) mkdirpSync(path5.dirname(dest));
      return doRename(src, dest, overwrite, isChangingCase);
    }
    function isParentRoot(dest) {
      const parent = path5.dirname(dest);
      const parsedPath = path5.parse(parent);
      return parsedPath.root === parent;
    }
    function doRename(src, dest, overwrite, isChangingCase) {
      if (isChangingCase) return rename(src, dest, overwrite);
      if (overwrite) {
        removeSync(dest);
        return rename(src, dest, overwrite);
      }
      if (fs3.existsSync(dest)) throw new Error("dest already exists.");
      return rename(src, dest, overwrite);
    }
    function rename(src, dest, overwrite) {
      try {
        fs3.renameSync(src, dest);
      } catch (err) {
        if (err.code !== "EXDEV") throw err;
        return moveAcrossDevice(src, dest, overwrite);
      }
    }
    function moveAcrossDevice(src, dest, overwrite) {
      const opts = {
        overwrite,
        errorOnExist: true,
        preserveTimestamps: true
      };
      copySync(src, dest, opts);
      return removeSync(src);
    }
    module2.exports = moveSync;
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/move/index.js
var require_move2 = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/move/index.js"(exports2, module2) {
    "use strict";
    var u = require_universalify().fromCallback;
    module2.exports = {
      move: u(require_move()),
      moveSync: require_move_sync()
    };
  }
});

// ../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/index.js
var require_lib = __commonJS({
  "../../node_modules/.pnpm/fs-extra@11.1.1/node_modules/fs-extra/lib/index.js"(exports2, module2) {
    "use strict";
    module2.exports = {
      // Export promiseified graceful-fs:
      ...require_fs(),
      // Export extra methods:
      ...require_copy2(),
      ...require_empty(),
      ...require_ensure(),
      ...require_json(),
      ...require_mkdirs(),
      ...require_move2(),
      ...require_output_file(),
      ...require_path_exists(),
      ...require_remove()
    };
  }
});

// ../../node_modules/.pnpm/common-path-prefix@3.0.0/node_modules/common-path-prefix/index.js
var require_common_path_prefix = __commonJS({
  "../../node_modules/.pnpm/common-path-prefix@3.0.0/node_modules/common-path-prefix/index.js"(exports2, module2) {
    "use strict";
    var { sep: DEFAULT_SEPARATOR } = require("path");
    var determineSeparator = (paths2) => {
      for (const path5 of paths2) {
        const match = /(\/|\\)/.exec(path5);
        if (match !== null) return match[0];
      }
      return DEFAULT_SEPARATOR;
    };
    module2.exports = function commonPathPrefix2(paths2, sep = determineSeparator(paths2)) {
      const [first = "", ...remaining] = paths2;
      if (first === "" || remaining.length === 0) return "";
      const parts = first.split(sep);
      let endOfPrefix = parts.length;
      for (const path5 of remaining) {
        const compare = path5.split(sep);
        for (let i = 0; i < endOfPrefix; i++) {
          if (compare[i] !== parts[i]) {
            endOfPrefix = i;
          }
        }
        if (endOfPrefix === 0) return "";
      }
      const prefix = parts.slice(0, endOfPrefix).join(sep);
      return prefix.endsWith(sep) ? prefix : prefix + sep;
    };
  }
});

// ../../node_modules/.pnpm/indent-string@4.0.0/node_modules/indent-string/index.js
var require_indent_string = __commonJS({
  "../../node_modules/.pnpm/indent-string@4.0.0/node_modules/indent-string/index.js"(exports2, module2) {
    "use strict";
    module2.exports = (string, count = 1, options) => {
      options = {
        indent: " ",
        includeEmptyLines: false,
        ...options
      };
      if (typeof string !== "string") {
        throw new TypeError(
          `Expected \`input\` to be a \`string\`, got \`${typeof string}\``
        );
      }
      if (typeof count !== "number") {
        throw new TypeError(
          `Expected \`count\` to be a \`number\`, got \`${typeof count}\``
        );
      }
      if (typeof options.indent !== "string") {
        throw new TypeError(
          `Expected \`options.indent\` to be a \`string\`, got \`${typeof options.indent}\``
        );
      }
      if (count === 0) {
        return string;
      }
      const regex = options.includeEmptyLines ? /^/gm : /^(?!\s*$)/gm;
      return string.replace(regex, options.indent.repeat(count));
    };
  }
});

// ../../node_modules/.pnpm/@babel+helper-validator-identifier@7.24.7/node_modules/@babel/helper-validator-identifier/lib/identifier.js
var require_identifier = __commonJS({
  "../../node_modules/.pnpm/@babel+helper-validator-identifier@7.24.7/node_modules/@babel/helper-validator-identifier/lib/identifier.js"(exports2) {
    "use strict";
    Object.defineProperty(exports2, "__esModule", {
      value: true
    });
    exports2.isIdentifierChar = isIdentifierChar;
    exports2.isIdentifierName = isIdentifierName2;
    exports2.isIdentifierStart = isIdentifierStart;
    var nonASCIIidentifierStartChars = "\xAA\xB5\xBA\xC0-\xD6\xD8-\xF6\xF8-\u02C1\u02C6-\u02D1\u02E0-\u02E4\u02EC\u02EE\u0370-\u0374\u0376\u0377\u037A-\u037D\u037F\u0386\u0388-\u038A\u038C\u038E-\u03A1\u03A3-\u03F5\u03F7-\u0481\u048A-\u052F\u0531-\u0556\u0559\u0560-\u0588\u05D0-\u05EA\u05EF-\u05F2\u0620-\u064A\u066E\u066F\u0671-\u06D3\u06D5\u06E5\u06E6\u06EE\u06EF\u06FA-\u06FC\u06FF\u0710\u0712-\u072F\u074D-\u07A5\u07B1\u07CA-\u07EA\u07F4\u07F5\u07FA\u0800-\u0815\u081A\u0824\u0828\u0840-\u0858\u0860-\u086A\u0870-\u0887\u0889-\u088E\u08A0-\u08C9\u0904-\u0939\u093D\u0950\u0958-\u0961\u0971-\u0980\u0985-\u098C\u098F\u0990\u0993-\u09A8\u09AA-\u09B0\u09B2\u09B6-\u09B9\u09BD\u09CE\u09DC\u09DD\u09DF-\u09E1\u09F0\u09F1\u09FC\u0A05-\u0A0A\u0A0F\u0A10\u0A13-\u0A28\u0A2A-\u0A30\u0A32\u0A33\u0A35\u0A36\u0A38\u0A39\u0A59-\u0A5C\u0A5E\u0A72-\u0A74\u0A85-\u0A8D\u0A8F-\u0A91\u0A93-\u0AA8\u0AAA-\u0AB0\u0AB2\u0AB3\u0AB5-\u0AB9\u0ABD\u0AD0\u0AE0\u0AE1\u0AF9\u0B05-\u0B0C\u0B0F\u0B10\u0B13-\u0B28\u0B2A-\u0B30\u0B32\u0B33\u0B35-\u0B39\u0B3D\u0B5C\u0B5D\u0B5F-\u0B61\u0B71\u0B83\u0B85-\u0B8A\u0B8E-\u0B90\u0B92-\u0B95\u0B99\u0B9A\u0B9C\u0B9E\u0B9F\u0BA3\u0BA4\u0BA8-\u0BAA\u0BAE-\u0BB9\u0BD0\u0C05-\u0C0C\u0C0E-\u0C10\u0C12-\u0C28\u0C2A-\u0C39\u0C3D\u0C58-\u0C5A\u0C5D\u0C60\u0C61\u0C80\u0C85-\u0C8C\u0C8E-\u0C90\u0C92-\u0CA8\u0CAA-\u0CB3\u0CB5-\u0CB9\u0CBD\u0CDD\u0CDE\u0CE0\u0CE1\u0CF1\u0CF2\u0D04-\u0D0C\u0D0E-\u0D10\u0D12-\u0D3A\u0D3D\u0D4E\u0D54-\u0D56\u0D5F-\u0D61\u0D7A-\u0D7F\u0D85-\u0D96\u0D9A-\u0DB1\u0DB3-\u0DBB\u0DBD\u0DC0-\u0DC6\u0E01-\u0E30\u0E32\u0E33\u0E40-\u0E46\u0E81\u0E82\u0E84\u0E86-\u0E8A\u0E8C-\u0EA3\u0EA5\u0EA7-\u0EB0\u0EB2\u0EB3\u0EBD\u0EC0-\u0EC4\u0EC6\u0EDC-\u0EDF\u0F00\u0F40-\u0F47\u0F49-\u0F6C\u0F88-\u0F8C\u1000-\u102A\u103F\u1050-\u1055\u105A-\u105D\u1061\u1065\u1066\u106E-\u1070\u1075-\u1081\u108E\u10A0-\u10C5\u10C7\u10CD\u10D0-\u10FA\u10FC-\u1248\u124A-\u124D\u1250-\u1256\u1258\u125A-\u125D\u1260-\u1288\u128A-\u128D\u1290-\u12B0\u12B2-\u12B5\u12B8-\u12BE\u12C0\u12C2-\u12C5\u12C8-\u12D6\u12D8-\u1310\u1312-\u1315\u1318-\u135A\u1380-\u138F\u13A0-\u13F5\u13F8-\u13FD\u1401-\u166C\u166F-\u167F\u1681-\u169A\u16A0-\u16EA\u16EE-\u16F8\u1700-\u1711\u171F-\u1731\u1740-\u1751\u1760-\u176C\u176E-\u1770\u1780-\u17B3\u17D7\u17DC\u1820-\u1878\u1880-\u18A8\u18AA\u18B0-\u18F5\u1900-\u191E\u1950-\u196D\u1970-\u1974\u1980-\u19AB\u19B0-\u19C9\u1A00-\u1A16\u1A20-\u1A54\u1AA7\u1B05-\u1B33\u1B45-\u1B4C\u1B83-\u1BA0\u1BAE\u1BAF\u1BBA-\u1BE5\u1C00-\u1C23\u1C4D-\u1C4F\u1C5A-\u1C7D\u1C80-\u1C88\u1C90-\u1CBA\u1CBD-\u1CBF\u1CE9-\u1CEC\u1CEE-\u1CF3\u1CF5\u1CF6\u1CFA\u1D00-\u1DBF\u1E00-\u1F15\u1F18-\u1F1D\u1F20-\u1F45\u1F48-\u1F4D\u1F50-\u1F57\u1F59\u1F5B\u1F5D\u1F5F-\u1F7D\u1F80-\u1FB4\u1FB6-\u1FBC\u1FBE\u1FC2-\u1FC4\u1FC6-\u1FCC\u1FD0-\u1FD3\u1FD6-\u1FDB\u1FE0-\u1FEC\u1FF2-\u1FF4\u1FF6-\u1FFC\u2071\u207F\u2090-\u209C\u2102\u2107\u210A-\u2113\u2115\u2118-\u211D\u2124\u2126\u2128\u212A-\u2139\u213C-\u213F\u2145-\u2149\u214E\u2160-\u2188\u2C00-\u2CE4\u2CEB-\u2CEE\u2CF2\u2CF3\u2D00-\u2D25\u2D27\u2D2D\u2D30-\u2D67\u2D6F\u2D80-\u2D96\u2DA0-\u2DA6\u2DA8-\u2DAE\u2DB0-\u2DB6\u2DB8-\u2DBE\u2DC0-\u2DC6\u2DC8-\u2DCE\u2DD0-\u2DD6\u2DD8-\u2DDE\u3005-\u3007\u3021-\u3029\u3031-\u3035\u3038-\u303C\u3041-\u3096\u309B-\u309F\u30A1-\u30FA\u30FC-\u30FF\u3105-\u312F\u3131-\u318E\u31A0-\u31BF\u31F0-\u31FF\u3400-\u4DBF\u4E00-\uA48C\uA4D0-\uA4FD\uA500-\uA60C\uA610-\uA61F\uA62A\uA62B\uA640-\uA66E\uA67F-\uA69D\uA6A0-\uA6EF\uA717-\uA71F\uA722-\uA788\uA78B-\uA7CA\uA7D0\uA7D1\uA7D3\uA7D5-\uA7D9\uA7F2-\uA801\uA803-\uA805\uA807-\uA80A\uA80C-\uA822\uA840-\uA873\uA882-\uA8B3\uA8F2-\uA8F7\uA8FB\uA8FD\uA8FE\uA90A-\uA925\uA930-\uA946\uA960-\uA97C\uA984-\uA9B2\uA9CF\uA9E0-\uA9E4\uA9E6-\uA9EF\uA9FA-\uA9FE\uAA00-\uAA28\uAA40-\uAA42\uAA44-\uAA4B\uAA60-\uAA76\uAA7A\uAA7E-\uAAAF\uAAB1\uAAB5\uAAB6\uAAB9-\uAABD\uAAC0\uAAC2\uAADB-\uAADD\uAAE0-\uAAEA\uAAF2-\uAAF4\uAB01-\uAB06\uAB09-\uAB0E\uAB11-\uAB16\uAB20-\uAB26\uAB28-\uAB2E\uAB30-\uAB5A\uAB5C-\uAB69\uAB70-\uABE2\uAC00-\uD7A3\uD7B0-\uD7C6\uD7CB-\uD7FB\uF900-\uFA6D\uFA70-\uFAD9\uFB00-\uFB06\uFB13-\uFB17\uFB1D\uFB1F-\uFB28\uFB2A-\uFB36\uFB38-\uFB3C\uFB3E\uFB40\uFB41\uFB43\uFB44\uFB46-\uFBB1\uFBD3-\uFD3D\uFD50-\uFD8F\uFD92-\uFDC7\uFDF0-\uFDFB\uFE70-\uFE74\uFE76-\uFEFC\uFF21-\uFF3A\uFF41-\uFF5A\uFF66-\uFFBE\uFFC2-\uFFC7\uFFCA-\uFFCF\uFFD2-\uFFD7\uFFDA-\uFFDC";
    var nonASCIIidentifierChars = "\u200C\u200D\xB7\u0300-\u036F\u0387\u0483-\u0487\u0591-\u05BD\u05BF\u05C1\u05C2\u05C4\u05C5\u05C7\u0610-\u061A\u064B-\u0669\u0670\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED\u06F0-\u06F9\u0711\u0730-\u074A\u07A6-\u07B0\u07C0-\u07C9\u07EB-\u07F3\u07FD\u0816-\u0819\u081B-\u0823\u0825-\u0827\u0829-\u082D\u0859-\u085B\u0898-\u089F\u08CA-\u08E1\u08E3-\u0903\u093A-\u093C\u093E-\u094F\u0951-\u0957\u0962\u0963\u0966-\u096F\u0981-\u0983\u09BC\u09BE-\u09C4\u09C7\u09C8\u09CB-\u09CD\u09D7\u09E2\u09E3\u09E6-\u09EF\u09FE\u0A01-\u0A03\u0A3C\u0A3E-\u0A42\u0A47\u0A48\u0A4B-\u0A4D\u0A51\u0A66-\u0A71\u0A75\u0A81-\u0A83\u0ABC\u0ABE-\u0AC5\u0AC7-\u0AC9\u0ACB-\u0ACD\u0AE2\u0AE3\u0AE6-\u0AEF\u0AFA-\u0AFF\u0B01-\u0B03\u0B3C\u0B3E-\u0B44\u0B47\u0B48\u0B4B-\u0B4D\u0B55-\u0B57\u0B62\u0B63\u0B66-\u0B6F\u0B82\u0BBE-\u0BC2\u0BC6-\u0BC8\u0BCA-\u0BCD\u0BD7\u0BE6-\u0BEF\u0C00-\u0C04\u0C3C\u0C3E-\u0C44\u0C46-\u0C48\u0C4A-\u0C4D\u0C55\u0C56\u0C62\u0C63\u0C66-\u0C6F\u0C81-\u0C83\u0CBC\u0CBE-\u0CC4\u0CC6-\u0CC8\u0CCA-\u0CCD\u0CD5\u0CD6\u0CE2\u0CE3\u0CE6-\u0CEF\u0CF3\u0D00-\u0D03\u0D3B\u0D3C\u0D3E-\u0D44\u0D46-\u0D48\u0D4A-\u0D4D\u0D57\u0D62\u0D63\u0D66-\u0D6F\u0D81-\u0D83\u0DCA\u0DCF-\u0DD4\u0DD6\u0DD8-\u0DDF\u0DE6-\u0DEF\u0DF2\u0DF3\u0E31\u0E34-\u0E3A\u0E47-\u0E4E\u0E50-\u0E59\u0EB1\u0EB4-\u0EBC\u0EC8-\u0ECE\u0ED0-\u0ED9\u0F18\u0F19\u0F20-\u0F29\u0F35\u0F37\u0F39\u0F3E\u0F3F\u0F71-\u0F84\u0F86\u0F87\u0F8D-\u0F97\u0F99-\u0FBC\u0FC6\u102B-\u103E\u1040-\u1049\u1056-\u1059\u105E-\u1060\u1062-\u1064\u1067-\u106D\u1071-\u1074\u1082-\u108D\u108F-\u109D\u135D-\u135F\u1369-\u1371\u1712-\u1715\u1732-\u1734\u1752\u1753\u1772\u1773\u17B4-\u17D3\u17DD\u17E0-\u17E9\u180B-\u180D\u180F-\u1819\u18A9\u1920-\u192B\u1930-\u193B\u1946-\u194F\u19D0-\u19DA\u1A17-\u1A1B\u1A55-\u1A5E\u1A60-\u1A7C\u1A7F-\u1A89\u1A90-\u1A99\u1AB0-\u1ABD\u1ABF-\u1ACE\u1B00-\u1B04\u1B34-\u1B44\u1B50-\u1B59\u1B6B-\u1B73\u1B80-\u1B82\u1BA1-\u1BAD\u1BB0-\u1BB9\u1BE6-\u1BF3\u1C24-\u1C37\u1C40-\u1C49\u1C50-\u1C59\u1CD0-\u1CD2\u1CD4-\u1CE8\u1CED\u1CF4\u1CF7-\u1CF9\u1DC0-\u1DFF\u200C\u200D\u203F\u2040\u2054\u20D0-\u20DC\u20E1\u20E5-\u20F0\u2CEF-\u2CF1\u2D7F\u2DE0-\u2DFF\u302A-\u302F\u3099\u309A\u30FB\uA620-\uA629\uA66F\uA674-\uA67D\uA69E\uA69F\uA6F0\uA6F1\uA802\uA806\uA80B\uA823-\uA827\uA82C\uA880\uA881\uA8B4-\uA8C5\uA8D0-\uA8D9\uA8E0-\uA8F1\uA8FF-\uA909\uA926-\uA92D\uA947-\uA953\uA980-\uA983\uA9B3-\uA9C0\uA9D0-\uA9D9\uA9E5\uA9F0-\uA9F9\uAA29-\uAA36\uAA43\uAA4C\uAA4D\uAA50-\uAA59\uAA7B-\uAA7D\uAAB0\uAAB2-\uAAB4\uAAB7\uAAB8\uAABE\uAABF\uAAC1\uAAEB-\uAAEF\uAAF5\uAAF6\uABE3-\uABEA\uABEC\uABED\uABF0-\uABF9\uFB1E\uFE00-\uFE0F\uFE20-\uFE2F\uFE33\uFE34\uFE4D-\uFE4F\uFF10-\uFF19\uFF3F\uFF65";
    var nonASCIIidentifierStart = new RegExp("[" + nonASCIIidentifierStartChars + "]");
    var nonASCIIidentifier = new RegExp("[" + nonASCIIidentifierStartChars + nonASCIIidentifierChars + "]");
    nonASCIIidentifierStartChars = nonASCIIidentifierChars = null;
    var astralIdentifierStartCodes = [0, 11, 2, 25, 2, 18, 2, 1, 2, 14, 3, 13, 35, 122, 70, 52, 268, 28, 4, 48, 48, 31, 14, 29, 6, 37, 11, 29, 3, 35, 5, 7, 2, 4, 43, 157, 19, 35, 5, 35, 5, 39, 9, 51, 13, 10, 2, 14, 2, 6, 2, 1, 2, 10, 2, 14, 2, 6, 2, 1, 68, 310, 10, 21, 11, 7, 25, 5, 2, 41, 2, 8, 70, 5, 3, 0, 2, 43, 2, 1, 4, 0, 3, 22, 11, 22, 10, 30, 66, 18, 2, 1, 11, 21, 11, 25, 71, 55, 7, 1, 65, 0, 16, 3, 2, 2, 2, 28, 43, 28, 4, 28, 36, 7, 2, 27, 28, 53, 11, 21, 11, 18, 14, 17, 111, 72, 56, 50, 14, 50, 14, 35, 349, 41, 7, 1, 79, 28, 11, 0, 9, 21, 43, 17, 47, 20, 28, 22, 13, 52, 58, 1, 3, 0, 14, 44, 33, 24, 27, 35, 30, 0, 3, 0, 9, 34, 4, 0, 13, 47, 15, 3, 22, 0, 2, 0, 36, 17, 2, 24, 20, 1, 64, 6, 2, 0, 2, 3, 2, 14, 2, 9, 8, 46, 39, 7, 3, 1, 3, 21, 2, 6, 2, 1, 2, 4, 4, 0, 19, 0, 13, 4, 159, 52, 19, 3, 21, 2, 31, 47, 21, 1, 2, 0, 185, 46, 42, 3, 37, 47, 21, 0, 60, 42, 14, 0, 72, 26, 38, 6, 186, 43, 117, 63, 32, 7, 3, 0, 3, 7, 2, 1, 2, 23, 16, 0, 2, 0, 95, 7, 3, 38, 17, 0, 2, 0, 29, 0, 11, 39, 8, 0, 22, 0, 12, 45, 20, 0, 19, 72, 264, 8, 2, 36, 18, 0, 50, 29, 113, 6, 2, 1, 2, 37, 22, 0, 26, 5, 2, 1, 2, 31, 15, 0, 328, 18, 16, 0, 2, 12, 2, 33, 125, 0, 80, 921, 103, 110, 18, 195, 2637, 96, 16, 1071, 18, 5, 4026, 582, 8634, 568, 8, 30, 18, 78, 18, 29, 19, 47, 17, 3, 32, 20, 6, 18, 689, 63, 129, 74, 6, 0, 67, 12, 65, 1, 2, 0, 29, 6135, 9, 1237, 43, 8, 8936, 3, 2, 6, 2, 1, 2, 290, 16, 0, 30, 2, 3, 0, 15, 3, 9, 395, 2309, 106, 6, 12, 4, 8, 8, 9, 5991, 84, 2, 70, 2, 1, 3, 0, 3, 1, 3, 3, 2, 11, 2, 0, 2, 6, 2, 64, 2, 3, 3, 7, 2, 6, 2, 27, 2, 3, 2, 4, 2, 0, 4, 6, 2, 339, 3, 24, 2, 24, 2, 30, 2, 24, 2, 30, 2, 24, 2, 30, 2, 24, 2, 30, 2, 24, 2, 7, 1845, 30, 7, 5, 262, 61, 147, 44, 11, 6, 17, 0, 322, 29, 19, 43, 485, 27, 757, 6, 2, 3, 2, 1, 2, 14, 2, 196, 60, 67, 8, 0, 1205, 3, 2, 26, 2, 1, 2, 0, 3, 0, 2, 9, 2, 3, 2, 0, 2, 0, 7, 0, 5, 0, 2, 0, 2, 0, 2, 2, 2, 1, 2, 0, 3, 0, 2, 0, 2, 0, 2, 0, 2, 0, 2, 1, 2, 0, 3, 3, 2, 6, 2, 3, 2, 3, 2, 0, 2, 9, 2, 16, 6, 2, 2, 4, 2, 16, 4421, 42719, 33, 4153, 7, 221, 3, 5761, 15, 7472, 16, 621, 2467, 541, 1507, 4938, 6, 4191];
    var astralIdentifierCodes = [509, 0, 227, 0, 150, 4, 294, 9, 1368, 2, 2, 1, 6, 3, 41, 2, 5, 0, 166, 1, 574, 3, 9, 9, 370, 1, 81, 2, 71, 10, 50, 3, 123, 2, 54, 14, 32, 10, 3, 1, 11, 3, 46, 10, 8, 0, 46, 9, 7, 2, 37, 13, 2, 9, 6, 1, 45, 0, 13, 2, 49, 13, 9, 3, 2, 11, 83, 11, 7, 0, 3, 0, 158, 11, 6, 9, 7, 3, 56, 1, 2, 6, 3, 1, 3, 2, 10, 0, 11, 1, 3, 6, 4, 4, 193, 17, 10, 9, 5, 0, 82, 19, 13, 9, 214, 6, 3, 8, 28, 1, 83, 16, 16, 9, 82, 12, 9, 9, 84, 14, 5, 9, 243, 14, 166, 9, 71, 5, 2, 1, 3, 3, 2, 0, 2, 1, 13, 9, 120, 6, 3, 6, 4, 0, 29, 9, 41, 6, 2, 3, 9, 0, 10, 10, 47, 15, 406, 7, 2, 7, 17, 9, 57, 21, 2, 13, 123, 5, 4, 0, 2, 1, 2, 6, 2, 0, 9, 9, 49, 4, 2, 1, 2, 4, 9, 9, 330, 3, 10, 1, 2, 0, 49, 6, 4, 4, 14, 9, 5351, 0, 7, 14, 13835, 9, 87, 9, 39, 4, 60, 6, 26, 9, 1014, 0, 2, 54, 8, 3, 82, 0, 12, 1, 19628, 1, 4706, 45, 3, 22, 543, 4, 4, 5, 9, 7, 3, 6, 31, 3, 149, 2, 1418, 49, 513, 54, 5, 49, 9, 0, 15, 0, 23, 4, 2, 14, 1361, 6, 2, 16, 3, 6, 2, 1, 2, 4, 101, 0, 161, 6, 10, 9, 357, 0, 62, 13, 499, 13, 983, 6, 110, 6, 6, 9, 4759, 9, 787719, 239];
    function isInAstralSet(code, set) {
      let pos = 65536;
      for (let i = 0, length = set.length; i < length; i += 2) {
        pos += set[i];
        if (pos > code) return false;
        pos += set[i + 1];
        if (pos >= code) return true;
      }
      return false;
    }
    function isIdentifierStart(code) {
      if (code < 65) return code === 36;
      if (code <= 90) return true;
      if (code < 97) return code === 95;
      if (code <= 122) return true;
      if (code <= 65535) {
        return code >= 170 && nonASCIIidentifierStart.test(String.fromCharCode(code));
      }
      return isInAstralSet(code, astralIdentifierStartCodes);
    }
    function isIdentifierChar(code) {
      if (code < 48) return code === 36;
      if (code < 58) return true;
      if (code < 65) return false;
      if (code <= 90) return true;
      if (code < 97) return code === 95;
      if (code <= 122) return true;
      if (code <= 65535) {
        return code >= 170 && nonASCIIidentifier.test(String.fromCharCode(code));
      }
      return isInAstralSet(code, astralIdentifierStartCodes) || isInAstralSet(code, astralIdentifierCodes);
    }
    function isIdentifierName2(name) {
      let isFirst = true;
      for (let i = 0; i < name.length; i++) {
        let cp = name.charCodeAt(i);
        if ((cp & 64512) === 55296 && i + 1 < name.length) {
          const trail = name.charCodeAt(++i);
          if ((trail & 64512) === 56320) {
            cp = 65536 + ((cp & 1023) << 10) + (trail & 1023);
          }
        }
        if (isFirst) {
          isFirst = false;
          if (!isIdentifierStart(cp)) {
            return false;
          }
        } else if (!isIdentifierChar(cp)) {
          return false;
        }
      }
      return !isFirst;
    }
  }
});

// ../../node_modules/.pnpm/@babel+helper-validator-identifier@7.24.7/node_modules/@babel/helper-validator-identifier/lib/keyword.js
var require_keyword = __commonJS({
  "../../node_modules/.pnpm/@babel+helper-validator-identifier@7.24.7/node_modules/@babel/helper-validator-identifier/lib/keyword.js"(exports2) {
    "use strict";
    Object.defineProperty(exports2, "__esModule", {
      value: true
    });
    exports2.isKeyword = isKeyword;
    exports2.isReservedWord = isReservedWord;
    exports2.isStrictBindOnlyReservedWord = isStrictBindOnlyReservedWord;
    exports2.isStrictBindReservedWord = isStrictBindReservedWord;
    exports2.isStrictReservedWord = isStrictReservedWord;
    var reservedWords = {
      keyword: ["break", "case", "catch", "continue", "debugger", "default", "do", "else", "finally", "for", "function", "if", "return", "switch", "throw", "try", "var", "const", "while", "with", "new", "this", "super", "class", "extends", "export", "import", "null", "true", "false", "in", "instanceof", "typeof", "void", "delete"],
      strict: ["implements", "interface", "let", "package", "private", "protected", "public", "static", "yield"],
      strictBind: ["eval", "arguments"]
    };
    var keywords = new Set(reservedWords.keyword);
    var reservedWordsStrictSet = new Set(reservedWords.strict);
    var reservedWordsStrictBindSet = new Set(reservedWords.strictBind);
    function isReservedWord(word, inModule) {
      return inModule && word === "await" || word === "enum";
    }
    function isStrictReservedWord(word, inModule) {
      return isReservedWord(word, inModule) || reservedWordsStrictSet.has(word);
    }
    function isStrictBindOnlyReservedWord(word) {
      return reservedWordsStrictBindSet.has(word);
    }
    function isStrictBindReservedWord(word, inModule) {
      return isStrictReservedWord(word, inModule) || isStrictBindOnlyReservedWord(word);
    }
    function isKeyword(word) {
      return keywords.has(word);
    }
  }
});

// ../../node_modules/.pnpm/@babel+helper-validator-identifier@7.24.7/node_modules/@babel/helper-validator-identifier/lib/index.js
var require_lib2 = __commonJS({
  "../../node_modules/.pnpm/@babel+helper-validator-identifier@7.24.7/node_modules/@babel/helper-validator-identifier/lib/index.js"(exports2) {
    "use strict";
    Object.defineProperty(exports2, "__esModule", {
      value: true
    });
    Object.defineProperty(exports2, "isIdentifierChar", {
      enumerable: true,
      get: function() {
        return _identifier.isIdentifierChar;
      }
    });
    Object.defineProperty(exports2, "isIdentifierName", {
      enumerable: true,
      get: function() {
        return _identifier.isIdentifierName;
      }
    });
    Object.defineProperty(exports2, "isIdentifierStart", {
      enumerable: true,
      get: function() {
        return _identifier.isIdentifierStart;
      }
    });
    Object.defineProperty(exports2, "isKeyword", {
      enumerable: true,
      get: function() {
        return _keyword.isKeyword;
      }
    });
    Object.defineProperty(exports2, "isReservedWord", {
      enumerable: true,
      get: function() {
        return _keyword.isReservedWord;
      }
    });
    Object.defineProperty(exports2, "isStrictBindOnlyReservedWord", {
      enumerable: true,
      get: function() {
        return _keyword.isStrictBindOnlyReservedWord;
      }
    });
    Object.defineProperty(exports2, "isStrictBindReservedWord", {
      enumerable: true,
      get: function() {
        return _keyword.isStrictBindReservedWord;
      }
    });
    Object.defineProperty(exports2, "isStrictReservedWord", {
      enumerable: true,
      get: function() {
        return _keyword.isStrictReservedWord;
      }
    });
    var _identifier = require_identifier();
    var _keyword = require_keyword();
  }
});

// ../../node_modules/.pnpm/pluralize@8.0.0/node_modules/pluralize/pluralize.js
var require_pluralize = __commonJS({
  "../../node_modules/.pnpm/pluralize@8.0.0/node_modules/pluralize/pluralize.js"(exports2, module2) {
    "use strict";
    (function(root, pluralize3) {
      if (typeof require === "function" && typeof exports2 === "object" && typeof module2 === "object") {
        module2.exports = pluralize3();
      } else if (typeof define === "function" && define.amd) {
        define(function() {
          return pluralize3();
        });
      } else {
        root.pluralize = pluralize3();
      }
    })(exports2, function() {
      var pluralRules = [];
      var singularRules = [];
      var uncountables = {};
      var irregularPlurals = {};
      var irregularSingles = {};
      function sanitizeRule(rule) {
        if (typeof rule === "string") {
          return new RegExp("^" + rule + "$", "i");
        }
        return rule;
      }
      function restoreCase(word, token) {
        if (word === token) return token;
        if (word === word.toLowerCase()) return token.toLowerCase();
        if (word === word.toUpperCase()) return token.toUpperCase();
        if (word[0] === word[0].toUpperCase()) {
          return token.charAt(0).toUpperCase() + token.substr(1).toLowerCase();
        }
        return token.toLowerCase();
      }
      function interpolate(str, args) {
        return str.replace(/\$(\d{1,2})/g, function(match, index) {
          return args[index] || "";
        });
      }
      function replace(word, rule) {
        return word.replace(rule[0], function(match, index) {
          var result = interpolate(rule[1], arguments);
          if (match === "") {
            return restoreCase(word[index - 1], result);
          }
          return restoreCase(match, result);
        });
      }
      function sanitizeWord(token, word, rules) {
        if (!token.length || uncountables.hasOwnProperty(token)) {
          return word;
        }
        var len = rules.length;
        while (len--) {
          var rule = rules[len];
          if (rule[0].test(word)) return replace(word, rule);
        }
        return word;
      }
      function replaceWord(replaceMap, keepMap, rules) {
        return function(word) {
          var token = word.toLowerCase();
          if (keepMap.hasOwnProperty(token)) {
            return restoreCase(word, token);
          }
          if (replaceMap.hasOwnProperty(token)) {
            return restoreCase(word, replaceMap[token]);
          }
          return sanitizeWord(token, word, rules);
        };
      }
      function checkWord(replaceMap, keepMap, rules, bool) {
        return function(word) {
          var token = word.toLowerCase();
          if (keepMap.hasOwnProperty(token)) return true;
          if (replaceMap.hasOwnProperty(token)) return false;
          return sanitizeWord(token, token, rules) === token;
        };
      }
      function pluralize3(word, count, inclusive) {
        var pluralized = count === 1 ? pluralize3.singular(word) : pluralize3.plural(word);
        return (inclusive ? count + " " : "") + pluralized;
      }
      pluralize3.plural = replaceWord(
        irregularSingles,
        irregularPlurals,
        pluralRules
      );
      pluralize3.isPlural = checkWord(
        irregularSingles,
        irregularPlurals,
        pluralRules
      );
      pluralize3.singular = replaceWord(
        irregularPlurals,
        irregularSingles,
        singularRules
      );
      pluralize3.isSingular = checkWord(
        irregularPlurals,
        irregularSingles,
        singularRules
      );
      pluralize3.addPluralRule = function(rule, replacement) {
        pluralRules.push([sanitizeRule(rule), replacement]);
      };
      pluralize3.addSingularRule = function(rule, replacement) {
        singularRules.push([sanitizeRule(rule), replacement]);
      };
      pluralize3.addUncountableRule = function(word) {
        if (typeof word === "string") {
          uncountables[word.toLowerCase()] = true;
          return;
        }
        pluralize3.addPluralRule(word, "$0");
        pluralize3.addSingularRule(word, "$0");
      };
      pluralize3.addIrregularRule = function(single, plural) {
        plural = plural.toLowerCase();
        single = single.toLowerCase();
        irregularSingles[single] = plural;
        irregularPlurals[plural] = single;
      };
      [
        // Pronouns.
        ["I", "we"],
        ["me", "us"],
        ["he", "they"],
        ["she", "they"],
        ["them", "them"],
        ["myself", "ourselves"],
        ["yourself", "yourselves"],
        ["itself", "themselves"],
        ["herself", "themselves"],
        ["himself", "themselves"],
        ["themself", "themselves"],
        ["is", "are"],
        ["was", "were"],
        ["has", "have"],
        ["this", "these"],
        ["that", "those"],
        // Words ending in with a consonant and `o`.
        ["echo", "echoes"],
        ["dingo", "dingoes"],
        ["volcano", "volcanoes"],
        ["tornado", "tornadoes"],
        ["torpedo", "torpedoes"],
        // Ends with `us`.
        ["genus", "genera"],
        ["viscus", "viscera"],
        // Ends with `ma`.
        ["stigma", "stigmata"],
        ["stoma", "stomata"],
        ["dogma", "dogmata"],
        ["lemma", "lemmata"],
        ["schema", "schemata"],
        ["anathema", "anathemata"],
        // Other irregular rules.
        ["ox", "oxen"],
        ["axe", "axes"],
        ["die", "dice"],
        ["yes", "yeses"],
        ["foot", "feet"],
        ["eave", "eaves"],
        ["goose", "geese"],
        ["tooth", "teeth"],
        ["quiz", "quizzes"],
        ["human", "humans"],
        ["proof", "proofs"],
        ["carve", "carves"],
        ["valve", "valves"],
        ["looey", "looies"],
        ["thief", "thieves"],
        ["groove", "grooves"],
        ["pickaxe", "pickaxes"],
        ["passerby", "passersby"]
      ].forEach(function(rule) {
        return pluralize3.addIrregularRule(rule[0], rule[1]);
      });
      [
        [/s?$/i, "s"],
        [/[^\u0000-\u007F]$/i, "$0"],
        [/([^aeiou]ese)$/i, "$1"],
        [/(ax|test)is$/i, "$1es"],
        [/(alias|[^aou]us|t[lm]as|gas|ris)$/i, "$1es"],
        [/(e[mn]u)s?$/i, "$1s"],
        [/([^l]ias|[aeiou]las|[ejzr]as|[iu]am)$/i, "$1"],
        [/(alumn|syllab|vir|radi|nucle|fung|cact|stimul|termin|bacill|foc|uter|loc|strat)(?:us|i)$/i, "$1i"],
        [/(alumn|alg|vertebr)(?:a|ae)$/i, "$1ae"],
        [/(seraph|cherub)(?:im)?$/i, "$1im"],
        [/(her|at|gr)o$/i, "$1oes"],
        [/(agend|addend|millenni|dat|extrem|bacteri|desiderat|strat|candelabr|errat|ov|symposi|curricul|automat|quor)(?:a|um)$/i, "$1a"],
        [/(apheli|hyperbat|periheli|asyndet|noumen|phenomen|criteri|organ|prolegomen|hedr|automat)(?:a|on)$/i, "$1a"],
        [/sis$/i, "ses"],
        [/(?:(kni|wi|li)fe|(ar|l|ea|eo|oa|hoo)f)$/i, "$1$2ves"],
        [/([^aeiouy]|qu)y$/i, "$1ies"],
        [/([^ch][ieo][ln])ey$/i, "$1ies"],
        [/(x|ch|ss|sh|zz)$/i, "$1es"],
        [/(matr|cod|mur|sil|vert|ind|append)(?:ix|ex)$/i, "$1ices"],
        [/\b((?:tit)?m|l)(?:ice|ouse)$/i, "$1ice"],
        [/(pe)(?:rson|ople)$/i, "$1ople"],
        [/(child)(?:ren)?$/i, "$1ren"],
        [/eaux$/i, "$0"],
        [/m[ae]n$/i, "men"],
        ["thou", "you"]
      ].forEach(function(rule) {
        return pluralize3.addPluralRule(rule[0], rule[1]);
      });
      [
        [/s$/i, ""],
        [/(ss)$/i, "$1"],
        [/(wi|kni|(?:after|half|high|low|mid|non|night|[^\w]|^)li)ves$/i, "$1fe"],
        [/(ar|(?:wo|[ae])l|[eo][ao])ves$/i, "$1f"],
        [/ies$/i, "y"],
        [/\b([pl]|zomb|(?:neck|cross)?t|coll|faer|food|gen|goon|group|lass|talk|goal|cut)ies$/i, "$1ie"],
        [/\b(mon|smil)ies$/i, "$1ey"],
        [/\b((?:tit)?m|l)ice$/i, "$1ouse"],
        [/(seraph|cherub)im$/i, "$1"],
        [/(x|ch|ss|sh|zz|tto|go|cho|alias|[^aou]us|t[lm]as|gas|(?:her|at|gr)o|[aeiou]ris)(?:es)?$/i, "$1"],
        [/(analy|diagno|parenthe|progno|synop|the|empha|cri|ne)(?:sis|ses)$/i, "$1sis"],
        [/(movie|twelve|abuse|e[mn]u)s$/i, "$1"],
        [/(test)(?:is|es)$/i, "$1is"],
        [/(alumn|syllab|vir|radi|nucle|fung|cact|stimul|termin|bacill|foc|uter|loc|strat)(?:us|i)$/i, "$1us"],
        [/(agend|addend|millenni|dat|extrem|bacteri|desiderat|strat|candelabr|errat|ov|symposi|curricul|quor)a$/i, "$1um"],
        [/(apheli|hyperbat|periheli|asyndet|noumen|phenomen|criteri|organ|prolegomen|hedr|automat)a$/i, "$1on"],
        [/(alumn|alg|vertebr)ae$/i, "$1a"],
        [/(cod|mur|sil|vert|ind)ices$/i, "$1ex"],
        [/(matr|append)ices$/i, "$1ix"],
        [/(pe)(rson|ople)$/i, "$1rson"],
        [/(child)ren$/i, "$1"],
        [/(eau)x?$/i, "$1"],
        [/men$/i, "man"]
      ].forEach(function(rule) {
        return pluralize3.addSingularRule(rule[0], rule[1]);
      });
      [
        // Singular words with no plurals.
        "adulthood",
        "advice",
        "agenda",
        "aid",
        "aircraft",
        "alcohol",
        "ammo",
        "analytics",
        "anime",
        "athletics",
        "audio",
        "bison",
        "blood",
        "bream",
        "buffalo",
        "butter",
        "carp",
        "cash",
        "chassis",
        "chess",
        "clothing",
        "cod",
        "commerce",
        "cooperation",
        "corps",
        "debris",
        "diabetes",
        "digestion",
        "elk",
        "energy",
        "equipment",
        "excretion",
        "expertise",
        "firmware",
        "flounder",
        "fun",
        "gallows",
        "garbage",
        "graffiti",
        "hardware",
        "headquarters",
        "health",
        "herpes",
        "highjinks",
        "homework",
        "housework",
        "information",
        "jeans",
        "justice",
        "kudos",
        "labour",
        "literature",
        "machinery",
        "mackerel",
        "mail",
        "media",
        "mews",
        "moose",
        "music",
        "mud",
        "manga",
        "news",
        "only",
        "personnel",
        "pike",
        "plankton",
        "pliers",
        "police",
        "pollution",
        "premises",
        "rain",
        "research",
        "rice",
        "salmon",
        "scissors",
        "series",
        "sewage",
        "shambles",
        "shrimp",
        "software",
        "species",
        "staff",
        "swine",
        "tennis",
        "traffic",
        "transportation",
        "trout",
        "tuna",
        "wealth",
        "welfare",
        "whiting",
        "wildebeest",
        "wildlife",
        "you",
        /pok[eé]mon$/i,
        // Regexes.
        /[^aeiou]ese$/i,
        // "chinese", "japanese"
        /deer$/i,
        // "deer", "reindeer"
        /fish$/i,
        // "fish", "blowfish", "angelfish"
        /measles$/i,
        /o[iu]s$/i,
        // "carnivorous"
        /pox$/i,
        // "chickpox", "smallpox"
        /sheep$/i
      ].forEach(pluralize3.addUncountableRule);
      return pluralize3;
    });
  }
});

// ../../node_modules/.pnpm/env-paths@2.2.1/node_modules/env-paths/index.js
var require_env_paths = __commonJS({
  "../../node_modules/.pnpm/env-paths@2.2.1/node_modules/env-paths/index.js"(exports2, module2) {
    "use strict";
    var path5 = require("path");
    var os2 = require("os");
    var homedir = os2.homedir();
    var tmpdir = os2.tmpdir();
    var { env: env2 } = process;
    var macos = (name) => {
      const library = path5.join(homedir, "Library");
      return {
        data: path5.join(library, "Application Support", name),
        config: path5.join(library, "Preferences", name),
        cache: path5.join(library, "Caches", name),
        log: path5.join(library, "Logs", name),
        temp: path5.join(tmpdir, name)
      };
    };
    var windows = (name) => {
      const appData = env2.APPDATA || path5.join(homedir, "AppData", "Roaming");
      const localAppData = env2.LOCALAPPDATA || path5.join(homedir, "AppData", "Local");
      return {
        // Data/config/cache/log are invented by me as Windows isn't opinionated about this
        data: path5.join(localAppData, name, "Data"),
        config: path5.join(appData, name, "Config"),
        cache: path5.join(localAppData, name, "Cache"),
        log: path5.join(localAppData, name, "Log"),
        temp: path5.join(tmpdir, name)
      };
    };
    var linux = (name) => {
      const username = path5.basename(homedir);
      return {
        data: path5.join(env2.XDG_DATA_HOME || path5.join(homedir, ".local", "share"), name),
        config: path5.join(env2.XDG_CONFIG_HOME || path5.join(homedir, ".config"), name),
        cache: path5.join(env2.XDG_CACHE_HOME || path5.join(homedir, ".cache"), name),
        // https://wiki.debian.org/XDGBaseDirectorySpecification#state
        log: path5.join(env2.XDG_STATE_HOME || path5.join(homedir, ".local", "state"), name),
        temp: path5.join(tmpdir, username, name)
      };
    };
    var envPaths = (name, options) => {
      if (typeof name !== "string") {
        throw new TypeError(`Expected string, got ${typeof name}`);
      }
      options = Object.assign({ suffix: "nodejs" }, options);
      if (options.suffix) {
        name += `-${options.suffix}`;
      }
      if (process.platform === "darwin") {
        return macos(name);
      }
      if (process.platform === "win32") {
        return windows(name);
      }
      return linux(name);
    };
    module2.exports = envPaths;
    module2.exports.default = envPaths;
  }
});

// ../../node_modules/.pnpm/path-exists@3.0.0/node_modules/path-exists/index.js
var require_path_exists2 = __commonJS({
  "../../node_modules/.pnpm/path-exists@3.0.0/node_modules/path-exists/index.js"(exports2, module2) {
    "use strict";
    var fs3 = require("fs");
    module2.exports = (fp) => new Promise((resolve) => {
      fs3.access(fp, (err) => {
        resolve(!err);
      });
    });
    module2.exports.sync = (fp) => {
      try {
        fs3.accessSync(fp);
        return true;
      } catch (err) {
        return false;
      }
    };
  }
});

// ../../node_modules/.pnpm/p-try@2.2.0/node_modules/p-try/index.js
var require_p_try = __commonJS({
  "../../node_modules/.pnpm/p-try@2.2.0/node_modules/p-try/index.js"(exports2, module2) {
    "use strict";
    var pTry = (fn, ...arguments_) => new Promise((resolve) => {
      resolve(fn(...arguments_));
    });
    module2.exports = pTry;
    module2.exports.default = pTry;
  }
});

// ../../node_modules/.pnpm/p-limit@2.3.0/node_modules/p-limit/index.js
var require_p_limit = __commonJS({
  "../../node_modules/.pnpm/p-limit@2.3.0/node_modules/p-limit/index.js"(exports2, module2) {
    "use strict";
    var pTry = require_p_try();
    var pLimit2 = (concurrency) => {
      if (!((Number.isInteger(concurrency) || concurrency === Infinity) && concurrency > 0)) {
        return Promise.reject(new TypeError("Expected `concurrency` to be a number from 1 and up"));
      }
      const queue = [];
      let activeCount = 0;
      const next = () => {
        activeCount--;
        if (queue.length > 0) {
          queue.shift()();
        }
      };
      const run = (fn, resolve, ...args) => {
        activeCount++;
        const result = pTry(fn, ...args);
        resolve(result);
        result.then(next, next);
      };
      const enqueue = (fn, resolve, ...args) => {
        if (activeCount < concurrency) {
          run(fn, resolve, ...args);
        } else {
          queue.push(run.bind(null, fn, resolve, ...args));
        }
      };
      const generator = (fn, ...args) => new Promise((resolve) => enqueue(fn, resolve, ...args));
      Object.defineProperties(generator, {
        activeCount: {
          get: () => activeCount
        },
        pendingCount: {
          get: () => queue.length
        },
        clearQueue: {
          value: () => {
            queue.length = 0;
          }
        }
      });
      return generator;
    };
    module2.exports = pLimit2;
    module2.exports.default = pLimit2;
  }
});

// ../../node_modules/.pnpm/p-locate@3.0.0/node_modules/p-locate/index.js
var require_p_locate = __commonJS({
  "../../node_modules/.pnpm/p-locate@3.0.0/node_modules/p-locate/index.js"(exports2, module2) {
    "use strict";
    var pLimit2 = require_p_limit();
    var EndError = class extends Error {
      constructor(value) {
        super();
        this.value = value;
      }
    };
    var testElement = (el, tester) => Promise.resolve(el).then(tester);
    var finder = (el) => Promise.all(el).then((val) => val[1] === true && Promise.reject(new EndError(val[0])));
    module2.exports = (iterable, tester, opts) => {
      opts = Object.assign({
        concurrency: Infinity,
        preserveOrder: true
      }, opts);
      const limit = pLimit2(opts.concurrency);
      const items = [...iterable].map((el) => [el, limit(testElement, el, tester)]);
      const checkLimit = pLimit2(opts.preserveOrder ? 1 : Infinity);
      return Promise.all(items.map((el) => checkLimit(finder, el))).then(() => {
      }).catch((err) => err instanceof EndError ? err.value : Promise.reject(err));
    };
  }
});

// ../../node_modules/.pnpm/locate-path@3.0.0/node_modules/locate-path/index.js
var require_locate_path = __commonJS({
  "../../node_modules/.pnpm/locate-path@3.0.0/node_modules/locate-path/index.js"(exports2, module2) {
    "use strict";
    var path5 = require("path");
    var pathExists2 = require_path_exists2();
    var pLocate2 = require_p_locate();
    module2.exports = (iterable, options) => {
      options = Object.assign({
        cwd: process.cwd()
      }, options);
      return pLocate2(iterable, (el) => pathExists2(path5.resolve(options.cwd, el)), options);
    };
    module2.exports.sync = (iterable, options) => {
      options = Object.assign({
        cwd: process.cwd()
      }, options);
      for (const el of iterable) {
        if (pathExists2.sync(path5.resolve(options.cwd, el))) {
          return el;
        }
      }
    };
  }
});

// ../../node_modules/.pnpm/find-up@3.0.0/node_modules/find-up/index.js
var require_find_up = __commonJS({
  "../../node_modules/.pnpm/find-up@3.0.0/node_modules/find-up/index.js"(exports2, module2) {
    "use strict";
    var path5 = require("path");
    var locatePath2 = require_locate_path();
    module2.exports = (filename, opts = {}) => {
      const startDir = path5.resolve(opts.cwd || "");
      const { root } = path5.parse(startDir);
      const filenames = [].concat(filename);
      return new Promise((resolve) => {
        (function find(dir) {
          locatePath2(filenames, { cwd: dir }).then((file2) => {
            if (file2) {
              resolve(path5.join(dir, file2));
            } else if (dir === root) {
              resolve(null);
            } else {
              find(path5.dirname(dir));
            }
          });
        })(startDir);
      });
    };
    module2.exports.sync = (filename, opts = {}) => {
      let dir = path5.resolve(opts.cwd || "");
      const { root } = path5.parse(dir);
      const filenames = [].concat(filename);
      while (true) {
        const file2 = locatePath2.sync(filenames, { cwd: dir });
        if (file2) {
          return path5.join(dir, file2);
        }
        if (dir === root) {
          return null;
        }
        dir = path5.dirname(dir);
      }
    };
  }
});

// ../../node_modules/.pnpm/pkg-up@3.1.0/node_modules/pkg-up/index.js
var require_pkg_up = __commonJS({
  "../../node_modules/.pnpm/pkg-up@3.1.0/node_modules/pkg-up/index.js"(exports2, module2) {
    "use strict";
    var findUp2 = require_find_up();
    module2.exports = async ({ cwd: cwd2 } = {}) => findUp2("package.json", { cwd: cwd2 });
    module2.exports.sync = ({ cwd: cwd2 } = {}) => findUp2.sync("package.json", { cwd: cwd2 });
  }
});

// package.json
var require_package2 = __commonJS({
  "package.json"(exports2, module2) {
    module2.exports = {
      name: "@prisma/client",
      version: "5.22.0",
      description: "Prisma Client is an auto-generated, type-safe and modern JavaScript/TypeScript ORM for Node.js that's tailored to your data. Supports PostgreSQL, CockroachDB, MySQL, MariaDB, SQL Server, SQLite & MongoDB databases.",
      keywords: [
        "ORM",
        "Prisma",
        "prisma2",
        "Prisma Client",
        "client",
        "query",
        "query-builder",
        "database",
        "db",
        "JavaScript",
        "JS",
        "TypeScript",
        "TS",
        "SQL",
        "SQLite",
        "pg",
        "Postgres",
        "PostgreSQL",
        "CockroachDB",
        "MySQL",
        "MariaDB",
        "MSSQL",
        "SQL Server",
        "SQLServer",
        "MongoDB",
        "react-native"
      ],
      main: "default.js",
      types: "default.d.ts",
      browser: "index-browser.js",
      exports: {
        "./package.json": "./package.json",
        ".": {
          require: {
            types: "./default.d.ts",
            node: "./default.js",
            "edge-light": "./default.js",
            workerd: "./default.js",
            worker: "./default.js",
            browser: "./index-browser.js"
          },
          import: {
            types: "./default.d.ts",
            node: "./default.js",
            "edge-light": "./default.js",
            workerd: "./default.js",
            worker: "./default.js",
            browser: "./index-browser.js"
          },
          default: "./default.js"
        },
        "./edge": {
          types: "./edge.d.ts",
          require: "./edge.js",
          import: "./edge.js",
          default: "./edge.js"
        },
        "./react-native": {
          types: "./react-native.d.ts",
          require: "./react-native.js",
          import: "./react-native.js",
          default: "./react-native.js"
        },
        "./extension": {
          types: "./extension.d.ts",
          require: "./extension.js",
          import: "./extension.js",
          default: "./extension.js"
        },
        "./index-browser": {
          types: "./index.d.ts",
          require: "./index-browser.js",
          import: "./index-browser.js",
          default: "./index-browser.js"
        },
        "./index": {
          types: "./index.d.ts",
          require: "./index.js",
          import: "./index.js",
          default: "./index.js"
        },
        "./wasm": {
          types: "./wasm.d.ts",
          require: "./wasm.js",
          import: "./wasm.js",
          default: "./wasm.js"
        },
        "./runtime/library": {
          types: "./runtime/library.d.ts",
          require: "./runtime/library.js",
          import: "./runtime/library.js",
          default: "./runtime/library.js"
        },
        "./runtime/binary": {
          types: "./runtime/binary.d.ts",
          require: "./runtime/binary.js",
          import: "./runtime/binary.js",
          default: "./runtime/binary.js"
        },
        "./generator-build": {
          require: "./generator-build/index.js",
          import: "./generator-build/index.js",
          default: "./generator-build/index.js"
        },
        "./sql": {
          require: {
            types: "./sql.d.ts",
            node: "./sql.js",
            default: "./sql.js"
          },
          import: {
            types: "./sql.d.ts",
            node: "./sql.mjs",
            default: "./sql.mjs"
          },
          default: "./sql.js"
        },
        "./*": "./*"
      },
      license: "Apache-2.0",
      engines: {
        node: ">=16.13"
      },
      homepage: "https://www.prisma.io",
      repository: {
        type: "git",
        url: "https://github.com/prisma/prisma.git",
        directory: "packages/client"
      },
      author: "Tim Suchanek <suchanek@prisma.io>",
      bugs: "https://github.com/prisma/prisma/issues",
      scripts: {
        dev: "DEV=true tsx helpers/build.ts",
        build: "tsx helpers/build.ts",
        test: "dotenv -e ../../.db.env -- jest --silent",
        "test:e2e": "dotenv -e ../../.db.env -- tsx tests/e2e/_utils/run.ts",
        "test:functional": "dotenv -e ../../.db.env -- tsx helpers/functional-test/run-tests.ts",
        "test:memory": "dotenv -e ../../.db.env -- tsx helpers/memory-tests.ts",
        "test:functional:code": "dotenv -e ../../.db.env -- tsx helpers/functional-test/run-tests.ts --no-types",
        "test:functional:types": "dotenv -e ../../.db.env -- tsx helpers/functional-test/run-tests.ts --types-only",
        "test-notypes": "dotenv -e ../../.db.env -- jest --testPathIgnorePatterns src/__tests__/types/types.test.ts",
        generate: "node scripts/postinstall.js",
        postinstall: "node scripts/postinstall.js",
        prepublishOnly: "pnpm run build",
        "new-test": "tsx ./helpers/new-test/new-test.ts"
      },
      files: [
        "README.md",
        "runtime",
        "!runtime/*.map",
        "scripts",
        "generator-build",
        "edge.js",
        "edge.d.ts",
        "wasm.js",
        "wasm.d.ts",
        "index.js",
        "index.d.ts",
        "react-native.js",
        "react-native.d.ts",
        "default.js",
        "default.d.ts",
        "index-browser.js",
        "extension.js",
        "extension.d.ts",
        "sql.d.ts",
        "sql.js",
        "sql.mjs"
      ],
      devDependencies: {
        "@cloudflare/workers-types": "4.20240614.0",
        "@codspeed/benchmark.js-plugin": "3.1.1",
        "@faker-js/faker": "8.4.1",
        "@fast-check/jest": "1.8.2",
        "@inquirer/prompts": "5.0.5",
        "@jest/create-cache-key-function": "29.7.0",
        "@jest/globals": "29.7.0",
        "@jest/test-sequencer": "29.7.0",
        "@libsql/client": "0.8.0",
        "@neondatabase/serverless": "0.9.3",
        "@opentelemetry/api": "1.9.0",
        "@opentelemetry/context-async-hooks": "1.25.1",
        "@opentelemetry/instrumentation": "0.52.1",
        "@opentelemetry/resources": "1.25.1",
        "@opentelemetry/sdk-trace-base": "1.25.1",
        "@opentelemetry/semantic-conventions": "1.25.1",
        "@planetscale/database": "1.18.0",
        "@prisma/adapter-d1": "workspace:*",
        "@prisma/adapter-libsql": "workspace:*",
        "@prisma/adapter-neon": "workspace:*",
        "@prisma/adapter-pg": "workspace:*",
        "@prisma/adapter-pg-worker": "workspace:*",
        "@prisma/adapter-planetscale": "workspace:*",
        "@prisma/debug": "workspace:*",
        "@prisma/driver-adapter-utils": "workspace:*",
        "@prisma/engines": "workspace:*",
        "@prisma/engines-version": "5.22.0-44.605197351a3c8bdd595af2d2a9bc3025bca48ea2",
        "@prisma/fetch-engine": "workspace:*",
        "@prisma/generator-helper": "workspace:*",
        "@prisma/get-platform": "workspace:*",
        "@prisma/instrumentation": "workspace:*",
        "@prisma/internals": "workspace:*",
        "@prisma/migrate": "workspace:*",
        "@prisma/mini-proxy": "0.9.5",
        "@prisma/pg-worker": "workspace:*",
        "@prisma/query-engine-wasm": "5.22.0-44.605197351a3c8bdd595af2d2a9bc3025bca48ea2",
        "@snaplet/copycat": "0.17.3",
        "@swc-node/register": "1.10.9",
        "@swc/core": "1.6.13",
        "@swc/jest": "0.2.36",
        "@timsuchanek/copy": "1.4.5",
        "@types/debug": "4.1.12",
        "@types/fs-extra": "9.0.13",
        "@types/jest": "29.5.12",
        "@types/js-levenshtein": "1.1.3",
        "@types/mssql": "9.1.5",
        "@types/node": "18.19.31",
        "@types/pg": "8.11.6",
        arg: "5.0.2",
        benchmark: "2.1.4",
        "ci-info": "4.0.0",
        "decimal.js": "10.4.3",
        "detect-runtime": "1.0.4",
        "env-paths": "2.2.1",
        esbuild: "0.23.0",
        execa: "5.1.1",
        "expect-type": "0.19.0",
        "flat-map-polyfill": "0.3.8",
        "fs-extra": "11.1.1",
        "get-stream": "6.0.1",
        globby: "11.1.0",
        "indent-string": "4.0.0",
        jest: "29.7.0",
        "jest-extended": "4.0.2",
        "jest-junit": "16.0.0",
        "jest-serializer-ansi-escapes": "3.0.0",
        "jest-snapshot": "29.7.0",
        "js-levenshtein": "1.1.6",
        kleur: "4.1.5",
        klona: "2.0.6",
        mariadb: "3.3.1",
        memfs: "4.9.3",
        mssql: "11.0.1",
        "new-github-issue-url": "0.2.1",
        "node-fetch": "3.3.2",
        "p-retry": "4.6.2",
        pg: "8.11.5",
        "pkg-up": "3.1.0",
        pluralize: "8.0.0",
        resolve: "1.22.8",
        rimraf: "3.0.2",
        "simple-statistics": "7.8.5",
        "sort-keys": "4.2.0",
        "source-map-support": "0.5.21",
        "sql-template-tag": "5.2.1",
        "stacktrace-parser": "0.1.10",
        "strip-ansi": "6.0.1",
        "strip-indent": "3.0.0",
        "ts-node": "10.9.2",
        "ts-pattern": "5.2.0",
        tsd: "0.31.1",
        typescript: "5.4.5",
        undici: "5.28.4",
        wrangler: "3.62.0",
        zx: "7.2.3"
      },
      peerDependencies: {
        prisma: "*"
      },
      peerDependenciesMeta: {
        prisma: {
          optional: true
        }
      },
      sideEffects: false
    };
  }
});

// ../../node_modules/.pnpm/flat-map-polyfill@0.3.8/node_modules/flat-map-polyfill/dist/cjs/array-species-create.js
var require_array_species_create = __commonJS({
  "../../node_modules/.pnpm/flat-map-polyfill@0.3.8/node_modules/flat-map-polyfill/dist/cjs/array-species-create.js"(exports2) {
    "use strict";
    Object.defineProperty(exports2, "__esModule", {
      value: true
    });
    var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function(obj) {
      return typeof obj;
    } : function(obj) {
      return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj;
    };
    exports2.default = arraySpeciesCreate;
    function arraySpeciesCreate(originalArray, length) {
      var isArray = Array.isArray(originalArray);
      if (!isArray) {
        return Array(length);
      }
      var C = Object.getPrototypeOf(originalArray).constructor;
      if (C) {
        if ((typeof C === "undefined" ? "undefined" : _typeof(C)) === "object" || typeof C === "function") {
          C = C[Symbol.species.toString()];
          C = C !== null ? C : void 0;
        }
        if (C === void 0) {
          return Array(length);
        }
        if (typeof C !== "function") {
          throw TypeError("invalid constructor");
        }
        var result = new C(length);
        return result;
      }
    }
  }
});

// ../../node_modules/.pnpm/flat-map-polyfill@0.3.8/node_modules/flat-map-polyfill/dist/cjs/flatten-into-array.js
var require_flatten_into_array = __commonJS({
  "../../node_modules/.pnpm/flat-map-polyfill@0.3.8/node_modules/flat-map-polyfill/dist/cjs/flatten-into-array.js"(exports2) {
    "use strict";
    Object.defineProperty(exports2, "__esModule", {
      value: true
    });
    exports2.default = flattenIntoArray;
    function flattenIntoArray(target, source, start, depth, mapperFunction, thisArg) {
      var mapperFunctionProvied = mapperFunction !== void 0;
      var targetIndex = start;
      var sourceIndex = 0;
      var sourceLen = source.length;
      while (sourceIndex < sourceLen) {
        var p = sourceIndex;
        var exists = !!source[p];
        if (exists === true) {
          var element = source[p];
          if (element) {
            if (mapperFunctionProvied) {
              element = mapperFunction.call(thisArg, element, sourceIndex, target);
            }
            var spreadable = Object.getOwnPropertySymbols(element).includes(Symbol.isConcatSpreadable) || Array.isArray(element);
            if (spreadable === true && depth > 0) {
              var nextIndex = flattenIntoArray(target, element, targetIndex, depth - 1);
              targetIndex = nextIndex;
            } else {
              if (!Number.isSafeInteger(targetIndex)) {
                throw TypeError();
              }
              target[targetIndex] = element;
            }
          }
        }
        targetIndex += 1;
        sourceIndex += 1;
      }
      return targetIndex;
    }
  }
});

// ../../node_modules/.pnpm/flat-map-polyfill@0.3.8/node_modules/flat-map-polyfill/dist/cjs/flatten.js
var require_flatten = __commonJS({
  "../../node_modules/.pnpm/flat-map-polyfill@0.3.8/node_modules/flat-map-polyfill/dist/cjs/flatten.js"() {
    "use strict";
    var _arraySpeciesCreate = require_array_species_create();
    var _arraySpeciesCreate2 = _interopRequireDefault(_arraySpeciesCreate);
    var _flattenIntoArray = require_flatten_into_array();
    var _flattenIntoArray2 = _interopRequireDefault(_flattenIntoArray);
    function _interopRequireDefault(obj) {
      return obj && obj.__esModule ? obj : { default: obj };
    }
    if (!Object.prototype.hasOwnProperty.call(Array.prototype, "flatten")) {
      Array.prototype.flatten = function flatten(depth) {
        var o = Object(this);
        var a = (0, _arraySpeciesCreate2.default)(o, this.length);
        var depthNum = depth !== void 0 ? Number(depth) : Infinity;
        (0, _flattenIntoArray2.default)(a, o, 0, depthNum);
        return a.filter(function(e) {
          return e !== void 0;
        });
      };
    }
  }
});

// ../../node_modules/.pnpm/flat-map-polyfill@0.3.8/node_modules/flat-map-polyfill/dist/cjs/flat-map.js
var require_flat_map = __commonJS({
  "../../node_modules/.pnpm/flat-map-polyfill@0.3.8/node_modules/flat-map-polyfill/dist/cjs/flat-map.js"() {
    "use strict";
    var _flattenIntoArray = require_flatten_into_array();
    var _flattenIntoArray2 = _interopRequireDefault(_flattenIntoArray);
    var _arraySpeciesCreate = require_array_species_create();
    var _arraySpeciesCreate2 = _interopRequireDefault(_arraySpeciesCreate);
    function _interopRequireDefault(obj) {
      return obj && obj.__esModule ? obj : { default: obj };
    }
    if (!Object.prototype.hasOwnProperty.call(Array.prototype, "flatMap")) {
      Array.prototype.flatMap = function flatMap(callbackFn, thisArg) {
        var o = Object(this);
        if (!callbackFn || typeof callbackFn.call !== "function") {
          throw TypeError("callbackFn must be callable.");
        }
        var t = thisArg !== void 0 ? thisArg : void 0;
        var a = (0, _arraySpeciesCreate2.default)(o, o.length);
        (0, _flattenIntoArray2.default)(
          a,
          o,
          /*start*/
          0,
          /*depth*/
          1,
          callbackFn,
          t
        );
        return a.filter(function(x) {
          return x !== void 0;
        }, a);
      };
    }
  }
});

// src/generation/ts-builders/KeyType.ts
var KeyType_exports = {};
__export(KeyType_exports, {
  KeyType: () => KeyType,
  keyType: () => keyType
});
function keyType(baseType, key) {
  return new KeyType(baseType, key);
}
var KeyType;
var init_KeyType = __esm({
  "src/generation/ts-builders/KeyType.ts"() {
    "use strict";
    init_TypeBuilder();
    KeyType = class extends TypeBuilder {
      constructor(baseType, key) {
        super();
        this.baseType = baseType;
        this.key = key;
      }
      write(writer) {
        this.baseType.writeIndexed(writer);
        writer.write("[").write(`"${this.key}"`).write("]");
      }
    };
  }
});

// src/generation/ts-builders/TypeBuilder.ts
var TypeBuilder;
var init_TypeBuilder = __esm({
  "src/generation/ts-builders/TypeBuilder.ts"() {
    "use strict";
    TypeBuilder = class {
      constructor() {
        // TODO(@SevInf): this should be replaced with precedence system that would
        // automatically add parenthesis where they are needed
        this.needsParenthesisWhenIndexed = false;
        this.needsParenthesisInKeyof = false;
        this.needsParenthesisInUnion = false;
      }
      subKey(key) {
        const { KeyType: KeyType2 } = (init_KeyType(), __toCommonJS(KeyType_exports));
        return new KeyType2(this, key);
      }
      writeIndexed(writer) {
        if (this.needsParenthesisWhenIndexed) {
          writer.write("(");
        }
        writer.write(this);
        if (this.needsParenthesisWhenIndexed) {
          writer.write(")");
        }
      }
    };
  }
});

// ../../node_modules/.pnpm/ci-info@4.0.0/node_modules/ci-info/vendors.json
var require_vendors = __commonJS({
  "../../node_modules/.pnpm/ci-info@4.0.0/node_modules/ci-info/vendors.json"(exports2, module2) {
    module2.exports = [
      {
        name: "Agola CI",
        constant: "AGOLA",
        env: "AGOLA_GIT_REF",
        pr: "AGOLA_PULL_REQUEST_ID"
      },
      {
        name: "Appcircle",
        constant: "APPCIRCLE",
        env: "AC_APPCIRCLE"
      },
      {
        name: "AppVeyor",
        constant: "APPVEYOR",
        env: "APPVEYOR",
        pr: "APPVEYOR_PULL_REQUEST_NUMBER"
      },
      {
        name: "AWS CodeBuild",
        constant: "CODEBUILD",
        env: "CODEBUILD_BUILD_ARN"
      },
      {
        name: "Azure Pipelines",
        constant: "AZURE_PIPELINES",
        env: "TF_BUILD",
        pr: {
          BUILD_REASON: "PullRequest"
        }
      },
      {
        name: "Bamboo",
        constant: "BAMBOO",
        env: "bamboo_planKey"
      },
      {
        name: "Bitbucket Pipelines",
        constant: "BITBUCKET",
        env: "BITBUCKET_COMMIT",
        pr: "BITBUCKET_PR_ID"
      },
      {
        name: "Bitrise",
        constant: "BITRISE",
        env: "BITRISE_IO",
        pr: "BITRISE_PULL_REQUEST"
      },
      {
        name: "Buddy",
        constant: "BUDDY",
        env: "BUDDY_WORKSPACE_ID",
        pr: "BUDDY_EXECUTION_PULL_REQUEST_ID"
      },
      {
        name: "Buildkite",
        constant: "BUILDKITE",
        env: "BUILDKITE",
        pr: {
          env: "BUILDKITE_PULL_REQUEST",
          ne: "false"
        }
      },
      {
        name: "CircleCI",
        constant: "CIRCLE",
        env: "CIRCLECI",
        pr: "CIRCLE_PULL_REQUEST"
      },
      {
        name: "Cirrus CI",
        constant: "CIRRUS",
        env: "CIRRUS_CI",
        pr: "CIRRUS_PR"
      },
      {
        name: "Codefresh",
        constant: "CODEFRESH",
        env: "CF_BUILD_ID",
        pr: {
          any: [
            "CF_PULL_REQUEST_NUMBER",
            "CF_PULL_REQUEST_ID"
          ]
        }
      },
      {
        name: "Codemagic",
        constant: "CODEMAGIC",
        env: "CM_BUILD_ID",
        pr: "CM_PULL_REQUEST"
      },
      {
        name: "Codeship",
        constant: "CODESHIP",
        env: {
          CI_NAME: "codeship"
        }
      },
      {
        name: "Drone",
        constant: "DRONE",
        env: "DRONE",
        pr: {
          DRONE_BUILD_EVENT: "pull_request"
        }
      },
      {
        name: "dsari",
        constant: "DSARI",
        env: "DSARI"
      },
      {
        name: "Earthly",
        constant: "EARTHLY",
        env: "EARTHLY_CI"
      },
      {
        name: "Expo Application Services",
        constant: "EAS",
        env: "EAS_BUILD"
      },
      {
        name: "Gerrit",
        constant: "GERRIT",
        env: "GERRIT_PROJECT"
      },
      {
        name: "Gitea Actions",
        constant: "GITEA_ACTIONS",
        env: "GITEA_ACTIONS"
      },
      {
        name: "GitHub Actions",
        constant: "GITHUB_ACTIONS",
        env: "GITHUB_ACTIONS",
        pr: {
          GITHUB_EVENT_NAME: "pull_request"
        }
      },
      {
        name: "GitLab CI",
        constant: "GITLAB",
        env: "GITLAB_CI",
        pr: "CI_MERGE_REQUEST_ID"
      },
      {
        name: "GoCD",
        constant: "GOCD",
        env: "GO_PIPELINE_LABEL"
      },
      {
        name: "Google Cloud Build",
        constant: "GOOGLE_CLOUD_BUILD",
        env: "BUILDER_OUTPUT"
      },
      {
        name: "Harness CI",
        constant: "HARNESS",
        env: "HARNESS_BUILD_ID"
      },
      {
        name: "Heroku",
        constant: "HEROKU",
        env: {
          env: "NODE",
          includes: "/app/.heroku/node/bin/node"
        }
      },
      {
        name: "Hudson",
        constant: "HUDSON",
        env: "HUDSON_URL"
      },
      {
        name: "Jenkins",
        constant: "JENKINS",
        env: [
          "JENKINS_URL",
          "BUILD_ID"
        ],
        pr: {
          any: [
            "ghprbPullId",
            "CHANGE_ID"
          ]
        }
      },
      {
        name: "LayerCI",
        constant: "LAYERCI",
        env: "LAYERCI",
        pr: "LAYERCI_PULL_REQUEST"
      },
      {
        name: "Magnum CI",
        constant: "MAGNUM",
        env: "MAGNUM"
      },
      {
        name: "Netlify CI",
        constant: "NETLIFY",
        env: "NETLIFY",
        pr: {
          env: "PULL_REQUEST",
          ne: "false"
        }
      },
      {
        name: "Nevercode",
        constant: "NEVERCODE",
        env: "NEVERCODE",
        pr: {
          env: "NEVERCODE_PULL_REQUEST",
          ne: "false"
        }
      },
      {
        name: "Prow",
        constant: "PROW",
        env: "PROW_JOB_ID"
      },
      {
        name: "ReleaseHub",
        constant: "RELEASEHUB",
        env: "RELEASE_BUILD_ID"
      },
      {
        name: "Render",
        constant: "RENDER",
        env: "RENDER",
        pr: {
          IS_PULL_REQUEST: "true"
        }
      },
      {
        name: "Sail CI",
        constant: "SAIL",
        env: "SAILCI",
        pr: "SAIL_PULL_REQUEST_NUMBER"
      },
      {
        name: "Screwdriver",
        constant: "SCREWDRIVER",
        env: "SCREWDRIVER",
        pr: {
          env: "SD_PULL_REQUEST",
          ne: "false"
        }
      },
      {
        name: "Semaphore",
        constant: "SEMAPHORE",
        env: "SEMAPHORE",
        pr: "PULL_REQUEST_NUMBER"
      },
      {
        name: "Sourcehut",
        constant: "SOURCEHUT",
        env: {
          CI_NAME: "sourcehut"
        }
      },
      {
        name: "Strider CD",
        constant: "STRIDER",
        env: "STRIDER"
      },
      {
        name: "TaskCluster",
        constant: "TASKCLUSTER",
        env: [
          "TASK_ID",
          "RUN_ID"
        ]
      },
      {
        name: "TeamCity",
        constant: "TEAMCITY",
        env: "TEAMCITY_VERSION"
      },
      {
        name: "Travis CI",
        constant: "TRAVIS",
        env: "TRAVIS",
        pr: {
          env: "TRAVIS_PULL_REQUEST",
          ne: "false"
        }
      },
      {
        name: "Vela",
        constant: "VELA",
        env: "VELA",
        pr: {
          VELA_PULL_REQUEST: "1"
        }
      },
      {
        name: "Vercel",
        constant: "VERCEL",
        env: {
          any: [
            "NOW_BUILDER",
            "VERCEL"
          ]
        },
        pr: "VERCEL_GIT_PULL_REQUEST_ID"
      },
      {
        name: "Visual Studio App Center",
        constant: "APPCENTER",
        env: "APPCENTER_BUILD_ID"
      },
      {
        name: "Woodpecker",
        constant: "WOODPECKER",
        env: {
          CI: "woodpecker"
        },
        pr: {
          CI_BUILD_EVENT: "pull_request"
        }
      },
      {
        name: "Xcode Cloud",
        constant: "XCODE_CLOUD",
        env: "CI_XCODE_PROJECT",
        pr: "CI_PULL_REQUEST_NUMBER"
      },
      {
        name: "Xcode Server",
        constant: "XCODE_SERVER",
        env: "XCS"
      }
    ];
  }
});

// ../../node_modules/.pnpm/ci-info@4.0.0/node_modules/ci-info/index.js
var require_ci_info = __commonJS({
  "../../node_modules/.pnpm/ci-info@4.0.0/node_modules/ci-info/index.js"(exports2) {
    "use strict";
    var vendors = require_vendors();
    var env2 = process.env;
    Object.defineProperty(exports2, "_vendors", {
      value: vendors.map(function(v) {
        return v.constant;
      })
    });
    exports2.name = null;
    exports2.isPR = null;
    vendors.forEach(function(vendor) {
      const envs = Array.isArray(vendor.env) ? vendor.env : [vendor.env];
      const isCI = envs.every(function(obj) {
        return checkEnv(obj);
      });
      exports2[vendor.constant] = isCI;
      if (!isCI) {
        return;
      }
      exports2.name = vendor.name;
      switch (typeof vendor.pr) {
        case "string":
          exports2.isPR = !!env2[vendor.pr];
          break;
        case "object":
          if ("env" in vendor.pr) {
            exports2.isPR = vendor.pr.env in env2 && env2[vendor.pr.env] !== vendor.pr.ne;
          } else if ("any" in vendor.pr) {
            exports2.isPR = vendor.pr.any.some(function(key) {
              return !!env2[key];
            });
          } else {
            exports2.isPR = checkEnv(vendor.pr);
          }
          break;
        default:
          exports2.isPR = null;
      }
    });
    exports2.isCI = !!(env2.CI !== "false" && // Bypass all checks if CI env is explicitly set to 'false'
    (env2.BUILD_ID || // Jenkins, Cloudbees
    env2.BUILD_NUMBER || // Jenkins, TeamCity
    env2.CI || // Travis CI, CircleCI, Cirrus CI, Gitlab CI, Appveyor, CodeShip, dsari
    env2.CI_APP_ID || // Appflow
    env2.CI_BUILD_ID || // Appflow
    env2.CI_BUILD_NUMBER || // Appflow
    env2.CI_NAME || // Codeship and others
    env2.CONTINUOUS_INTEGRATION || // Travis CI, Cirrus CI
    env2.RUN_ID || // TaskCluster, dsari
    exports2.name || false));
    function checkEnv(obj) {
      if (typeof obj === "string") return !!env2[obj];
      if ("env" in obj) {
        return env2[obj.env] && env2[obj.env].includes(obj.includes);
      }
      if ("any" in obj) {
        return obj.any.some(function(k) {
          return !!env2[k];
        });
      }
      return Object.keys(obj).every(function(k) {
        return env2[k] === obj[k];
      });
    }
  }
});

// src/generation/generator.ts
var generator_exports = {};
__export(generator_exports, {
  dmmfToTypes: () => dmmfToTypes,
  externalToInternalDmmf: () => externalToInternalDmmf
});
module.exports = __toCommonJS(generator_exports);

// ../../node_modules/.pnpm/kleur@4.1.5/node_modules/kleur/colors.mjs
var colors_exports = {};
__export(colors_exports, {
  $: () => $,
  bgBlack: () => bgBlack,
  bgBlue: () => bgBlue,
  bgCyan: () => bgCyan,
  bgGreen: () => bgGreen,
  bgMagenta: () => bgMagenta,
  bgRed: () => bgRed,
  bgWhite: () => bgWhite,
  bgYellow: () => bgYellow,
  black: () => black,
  blue: () => blue,
  bold: () => bold,
  cyan: () => cyan,
  dim: () => dim,
  gray: () => gray,
  green: () => green,
  grey: () => grey,
  hidden: () => hidden,
  inverse: () => inverse,
  italic: () => italic,
  magenta: () => magenta,
  red: () => red,
  reset: () => reset,
  strikethrough: () => strikethrough,
  underline: () => underline,
  white: () => white,
  yellow: () => yellow
});
var FORCE_COLOR;
var NODE_DISABLE_COLORS;
var NO_COLOR;
var TERM;
var isTTY = true;
if (typeof process !== "undefined") {
  ({ FORCE_COLOR, NODE_DISABLE_COLORS, NO_COLOR, TERM } = process.env || {});
  isTTY = process.stdout && process.stdout.isTTY;
}
var $ = {
  enabled: !NODE_DISABLE_COLORS && NO_COLOR == null && TERM !== "dumb" && (FORCE_COLOR != null && FORCE_COLOR !== "0" || isTTY)
};
function init(x, y) {
  let rgx = new RegExp(`\\x1b\\[${y}m`, "g");
  let open = `\x1B[${x}m`, close = `\x1B[${y}m`;
  return function(txt) {
    if (!$.enabled || txt == null) return txt;
    return open + (!!~("" + txt).indexOf(close) ? txt.replace(rgx, close + open) : txt) + close;
  };
}
var reset = init(0, 0);
var bold = init(1, 22);
var dim = init(2, 22);
var italic = init(3, 23);
var underline = init(4, 24);
var inverse = init(7, 27);
var hidden = init(8, 28);
var strikethrough = init(9, 29);
var black = init(30, 39);
var red = init(31, 39);
var green = init(32, 39);
var yellow = init(33, 39);
var blue = init(34, 39);
var magenta = init(35, 39);
var cyan = init(36, 39);
var white = init(37, 39);
var gray = init(90, 39);
var grey = init(90, 39);
var bgBlack = init(40, 49);
var bgRed = init(41, 49);
var bgGreen = init(42, 49);
var bgYellow = init(43, 49);
var bgBlue = init(44, 49);
var bgMagenta = init(45, 49);
var bgCyan = init(46, 49);
var bgWhite = init(47, 49);

// ../debug/src/index.ts
var MAX_ARGS_HISTORY = 100;
var COLORS = ["green", "yellow", "blue", "magenta", "cyan", "red"];
var argsHistory = [];
var lastTimestamp = Date.now();
var lastColor = 0;
var processEnv = typeof process !== "undefined" ? process.env : {};
globalThis.DEBUG ??= processEnv.DEBUG ?? "";
globalThis.DEBUG_COLORS ??= processEnv.DEBUG_COLORS ? processEnv.DEBUG_COLORS === "true" : true;
var topProps = {
  enable(namespace2) {
    if (typeof namespace2 === "string") {
      globalThis.DEBUG = namespace2;
    }
  },
  disable() {
    const prev = globalThis.DEBUG;
    globalThis.DEBUG = "";
    return prev;
  },
  // this is the core logic to check if logging should happen or not
  enabled(namespace2) {
    const listenedNamespaces = globalThis.DEBUG.split(",").map((s) => {
      return s.replace(/[.+?^${}()|[\]\\]/g, "\\$&");
    });
    const isListened = listenedNamespaces.some((listenedNamespace) => {
      if (listenedNamespace === "" || listenedNamespace[0] === "-") return false;
      return namespace2.match(RegExp(listenedNamespace.split("*").join(".*") + "$"));
    });
    const isExcluded = listenedNamespaces.some((listenedNamespace) => {
      if (listenedNamespace === "" || listenedNamespace[0] !== "-") return false;
      return namespace2.match(RegExp(listenedNamespace.slice(1).split("*").join(".*") + "$"));
    });
    return isListened && !isExcluded;
  },
  log: (...args) => {
    const [namespace2, format, ...rest] = args;
    const logWithFormatting = console.warn ?? console.log;
    logWithFormatting(`${namespace2} ${format}`, ...rest);
  },
  formatters: {}
  // not implemented
};
function debugCreate(namespace2) {
  const instanceProps = {
    color: COLORS[lastColor++ % COLORS.length],
    enabled: topProps.enabled(namespace2),
    namespace: namespace2,
    log: topProps.log,
    extend: () => {
    }
    // not implemented
  };
  const debugCall = (...args) => {
    const { enabled, namespace: namespace3, color, log } = instanceProps;
    if (args.length !== 0) {
      argsHistory.push([namespace3, ...args]);
    }
    if (argsHistory.length > MAX_ARGS_HISTORY) {
      argsHistory.shift();
    }
    if (topProps.enabled(namespace3) || enabled) {
      const stringArgs = args.map((arg) => {
        if (typeof arg === "string") {
          return arg;
        }
        return safeStringify(arg);
      });
      const ms = `+${Date.now() - lastTimestamp}ms`;
      lastTimestamp = Date.now();
      if (globalThis.DEBUG_COLORS) {
        log(colors_exports[color](bold(namespace3)), ...stringArgs, colors_exports[color](ms));
      } else {
        log(namespace3, ...stringArgs, ms);
      }
    }
  };
  return new Proxy(debugCall, {
    get: (_, prop) => instanceProps[prop],
    set: (_, prop, value) => instanceProps[prop] = value
  });
}
var Debug = new Proxy(debugCreate, {
  get: (_, prop) => topProps[prop],
  set: (_, prop, value) => topProps[prop] = value
});
function safeStringify(value, indent9 = 2) {
  const cache = /* @__PURE__ */ new Set();
  return JSON.stringify(
    value,
    (key, value2) => {
      if (typeof value2 === "object" && value2 !== null) {
        if (cache.has(value2)) {
          return `[Circular *]`;
        }
        cache.add(value2);
      } else if (typeof value2 === "bigint") {
        return value2.toString();
      }
      return value2;
    },
    indent9
  );
}
var src_default = Debug;

// src/generation/generator.ts
var import_engines_version = __toESM(require_engines_version());

// ../generator-helper/src/dmmf.ts
var DMMF;
((DMMF2) => {
  let ModelAction;
  ((ModelAction2) => {
    ModelAction2["findUnique"] = "findUnique";
    ModelAction2["findUniqueOrThrow"] = "findUniqueOrThrow";
    ModelAction2["findFirst"] = "findFirst";
    ModelAction2["findFirstOrThrow"] = "findFirstOrThrow";
    ModelAction2["findMany"] = "findMany";
    ModelAction2["create"] = "create";
    ModelAction2["createMany"] = "createMany";
    ModelAction2["createManyAndReturn"] = "createManyAndReturn";
    ModelAction2["update"] = "update";
    ModelAction2["updateMany"] = "updateMany";
    ModelAction2["upsert"] = "upsert";
    ModelAction2["delete"] = "delete";
    ModelAction2["deleteMany"] = "deleteMany";
    ModelAction2["groupBy"] = "groupBy";
    ModelAction2["count"] = "count";
    ModelAction2["aggregate"] = "aggregate";
    ModelAction2["findRaw"] = "findRaw";
    ModelAction2["aggregateRaw"] = "aggregateRaw";
  })(ModelAction = DMMF2.ModelAction || (DMMF2.ModelAction = {}));
})(DMMF || (DMMF = {}));

// ../generator-helper/src/byline.ts
var import_stream = __toESM(require("stream"));
var import_util = __toESM(require("util"));
function byline(readStream, options) {
  return createStream(readStream, options);
}
function createStream(readStream, options) {
  if (readStream) {
    return createLineStream(readStream, options);
  } else {
    return new LineStream(options);
  }
}
function createLineStream(readStream, options) {
  if (!readStream) {
    throw new Error("expected readStream");
  }
  if (!readStream.readable) {
    throw new Error("readStream must be readable");
  }
  const ls = new LineStream(options);
  readStream.pipe(ls);
  return ls;
}
function LineStream(options) {
  import_stream.default.Transform.call(this, options);
  options = options || {};
  this._readableState.objectMode = true;
  this._lineBuffer = [];
  this._keepEmptyLines = options.keepEmptyLines || false;
  this._lastChunkEndedWithCR = false;
  this.on("pipe", function(src) {
    if (!this.encoding) {
      if (src instanceof import_stream.default.Readable) {
        this.encoding = src._readableState.encoding;
      }
    }
  });
}
import_util.default.inherits(LineStream, import_stream.default.Transform);
LineStream.prototype._transform = function(chunk, encoding, done) {
  encoding = encoding || "utf8";
  if (Buffer.isBuffer(chunk)) {
    if (encoding == "buffer") {
      chunk = chunk.toString();
      encoding = "utf8";
    } else {
      chunk = chunk.toString(encoding);
    }
  }
  this._chunkEncoding = encoding;
  const lines = chunk.split(/\r\n|\r|\n/g);
  if (this._lastChunkEndedWithCR && chunk[0] == "\n") {
    lines.shift();
  }
  if (this._lineBuffer.length > 0) {
    this._lineBuffer[this._lineBuffer.length - 1] += lines[0];
    lines.shift();
  }
  this._lastChunkEndedWithCR = chunk[chunk.length - 1] == "\r";
  this._lineBuffer = this._lineBuffer.concat(lines);
  this._pushBuffer(encoding, 1, done);
};
LineStream.prototype._pushBuffer = function(encoding, keep, done) {
  while (this._lineBuffer.length > keep) {
    const line = this._lineBuffer.shift();
    if (this._keepEmptyLines || line.length > 0) {
      if (!this.push(this._reencode(line, encoding))) {
        const self = this;
        setImmediate(function() {
          self._pushBuffer(encoding, keep, done);
        });
        return;
      }
    }
  }
  done();
};
LineStream.prototype._flush = function(done) {
  this._pushBuffer(this._chunkEncoding, 0, done);
};
LineStream.prototype._reencode = function(line, chunkEncoding) {
  if (this.encoding && this.encoding != chunkEncoding) {
    return Buffer.from(line, chunkEncoding).toString(this.encoding);
  } else if (this.encoding) {
    return line;
  } else {
    return Buffer.from(line, chunkEncoding);
  }
};

// ../generator-helper/src/generatorHandler.ts
function generatorHandler(handler) {
  byline(process.stdin).on("data", async (line) => {
    const json = JSON.parse(String(line));
    if (json.method === "generate" && json.params) {
      try {
        const result = await handler.onGenerate(json.params);
        respond({
          jsonrpc: "2.0",
          result,
          id: json.id
        });
      } catch (_e) {
        const e = _e;
        respond({
          jsonrpc: "2.0",
          error: {
            code: -32e3,
            message: e.message,
            data: {
              stack: e.stack
            }
          },
          id: json.id
        });
      }
    }
    if (json.method === "getManifest") {
      if (handler.onManifest) {
        try {
          const manifest = handler.onManifest(json.params);
          respond({
            jsonrpc: "2.0",
            result: {
              manifest
            },
            id: json.id
          });
        } catch (_e) {
          const e = _e;
          respond({
            jsonrpc: "2.0",
            error: {
              code: -32e3,
              message: e.message,
              data: {
                stack: e.stack
              }
            },
            id: json.id
          });
        }
      } else {
        respond({
          jsonrpc: "2.0",
          result: {
            manifest: null
          },
          id: json.id
        });
      }
    }
  });
  process.stdin.resume();
}
function respond(response) {
  console.error(JSON.stringify(response));
}

// ../get-platform/src/getNodeAPIName.ts
var NODE_API_QUERY_ENGINE_URL_BASE = "libquery_engine";
function getNodeAPIName(binaryTarget, type) {
  const isUrl = type === "url";
  if (binaryTarget.includes("windows")) {
    return isUrl ? `query_engine.dll.node` : `query_engine-${binaryTarget}.dll.node`;
  } else if (binaryTarget.includes("darwin")) {
    return isUrl ? `${NODE_API_QUERY_ENGINE_URL_BASE}.dylib.node` : `${NODE_API_QUERY_ENGINE_URL_BASE}-${binaryTarget}.dylib.node`;
  } else {
    return isUrl ? `${NODE_API_QUERY_ENGINE_URL_BASE}.so.node` : `${NODE_API_QUERY_ENGINE_URL_BASE}-${binaryTarget}.so.node`;
  }
}

// ../../node_modules/.pnpm/find-cache-dir@5.0.0/node_modules/find-cache-dir/index.js
var import_node_process = __toESM(require("process"), 1);
var import_common_path_prefix = __toESM(require_common_path_prefix(), 1);

// ../../node_modules/.pnpm/find-up@6.3.0/node_modules/find-up/index.js
var findUpStop = Symbol("findUpStop");

// ../../node_modules/.pnpm/find-cache-dir@5.0.0/node_modules/find-cache-dir/index.js
var { env, cwd } = import_node_process.default;

// ../fetch-engine/src/utils.ts
var import_fs = __toESM(require("fs"));
var import_os = __toESM(require("os"));
var debug = src_default("prisma:fetch-engine:cache-dir");
async function overwriteFile(sourcePath, targetPath) {
  if (import_os.default.platform() === "darwin") {
    await removeFileIfExists(targetPath);
    await import_fs.default.promises.copyFile(sourcePath, targetPath);
  } else {
    let tempPath = `${targetPath}.tmp${process.pid}`;
    await import_fs.default.promises.copyFile(sourcePath, tempPath);
    await import_fs.default.promises.rename(tempPath, targetPath);
  }
}
async function removeFileIfExists(filePath) {
  try {
    await import_fs.default.promises.unlink(filePath);
  } catch (e) {
    if (e.code !== "ENOENT") {
      throw e;
    }
  }
}

// ../internals/src/client/getClientEngineType.ts
var DEFAULT_CLIENT_ENGINE_TYPE = "library" /* Library */;
function getClientEngineType(generatorConfig) {
  const engineTypeFromEnvVar = getEngineTypeFromEnvVar();
  if (engineTypeFromEnvVar) return engineTypeFromEnvVar;
  if (generatorConfig?.config.engineType === "library" /* Library */) {
    return "library" /* Library */;
  } else if (generatorConfig?.config.engineType === "binary" /* Binary */) {
    return "binary" /* Binary */;
  } else {
    return DEFAULT_CLIENT_ENGINE_TYPE;
  }
}
function getEngineTypeFromEnvVar() {
  const engineType = process.env.PRISMA_CLIENT_ENGINE_TYPE;
  if (engineType === "library" /* Library */) {
    return "library" /* Library */;
  } else if (engineType === "binary" /* Binary */) {
    return "binary" /* Binary */;
  } else {
    return void 0;
  }
}

// ../internals/src/utils/parseEnvValue.ts
function parseEnvValue(object) {
  if (object.fromEnvVar && object.fromEnvVar != "null") {
    const value = process.env[object.fromEnvVar];
    if (!value) {
      throw new Error(
        `Attempted to load provider value using \`env(${object.fromEnvVar})\` but it was not present. Please ensure that ${dim(
          object.fromEnvVar
        )} is present in your Environment Variables`
      );
    }
    return value;
  }
  return object.value;
}

// ../internals/src/utils/path.ts
var import_path = __toESM(require("path"));
function pathToPosix(filePath) {
  if (import_path.default.sep === import_path.default.posix.sep) {
    return filePath;
  }
  return filePath.split(import_path.default.sep).join(import_path.default.posix.sep);
}

// ../internals/src/utils/parseAWSNodejsRuntimeEnvVarVersion.ts
function parseAWSNodejsRuntimeEnvVarVersion() {
  const runtimeEnvVar = process.env.AWS_LAMBDA_JS_RUNTIME;
  if (!runtimeEnvVar || runtimeEnvVar === "") return null;
  try {
    const runtimeRegex = /^nodejs(\d+).x$/;
    const match = runtimeRegex.exec(runtimeEnvVar);
    if (match) {
      return parseInt(match[1]);
    }
  } catch (e) {
    console.error(
      `We could not parse the AWS_LAMBDA_JS_RUNTIME env var with the following value: ${runtimeEnvVar}. This was silently ignored.`
    );
  }
  return null;
}

// ../internals/src/utils/assertNever.ts
function assertNever(arg, errorMessage) {
  throw new Error(errorMessage);
}

// ../internals/src/utils/hasOwnProperty.ts
function hasOwnProperty(object, key) {
  return Object.prototype.hasOwnProperty.call(object, key);
}

// ../internals/src/utils/isValidJsIdentifier.ts
var import_helper_validator_identifier = __toESM(require_lib2());
function isValidJsIdentifier(str) {
  return (0, import_helper_validator_identifier.isIdentifierName)(str);
}

// ../internals/src/utils/setClassName.ts
function setClassName(classObject, name) {
  Object.defineProperty(classObject, "name", {
    value: name,
    configurable: true
  });
}

// src/runtime/externalToInternalDmmf.ts
var import_pluralize = __toESM(require_pluralize());

// src/generation/utils/common.ts
var keyBy = (collection, prop) => {
  const acc = {};
  for (const obj of collection) {
    const key = obj[prop];
    acc[key] = obj;
  }
  return acc;
};
function needsNamespace(field) {
  if (field.kind === "object") {
    return true;
  }
  if (field.kind === "scalar") {
    return field.type === "Json" || field.type === "Decimal";
  }
  return false;
}
var GraphQLScalarToJSTypeTable = {
  String: "string",
  Int: "number",
  Float: "number",
  Boolean: "boolean",
  Long: "number",
  DateTime: ["Date", "string"],
  ID: "string",
  UUID: "string",
  Json: "JsonValue",
  Bytes: "Buffer",
  Decimal: ["Decimal", "DecimalJsLike", "number", "string"],
  BigInt: ["bigint", "number"]
};
var JSOutputTypeToInputType = {
  JsonValue: "InputJsonValue"
};
function capitalize(str) {
  return str[0].toUpperCase() + str.slice(1);
}
function lowerCase(name) {
  return name.substring(0, 1).toLowerCase() + name.substring(1);
}

// src/runtime/externalToInternalDmmf.ts
function externalToInternalDmmf(document) {
  return {
    ...document,
    mappings: getMappings(document.mappings, document.datamodel)
  };
}
function getMappings(mappings, datamodel) {
  const modelOperations = mappings.modelOperations.filter((mapping) => {
    const model = datamodel.models.find((m) => m.name === mapping.model);
    if (!model) {
      throw new Error(`Mapping without model ${mapping.model}`);
    }
    return model.fields.some((f) => f.kind !== "object");
  }).map((mapping) => ({
    model: mapping.model,
    plural: (0, import_pluralize.default)(lowerCase(mapping.model)),
    // TODO not needed anymore
    findUnique: mapping.findUnique || mapping.findSingle,
    findUniqueOrThrow: mapping.findUniqueOrThrow,
    findFirst: mapping.findFirst,
    findFirstOrThrow: mapping.findFirstOrThrow,
    findMany: mapping.findMany,
    create: mapping.createOne || mapping.createSingle || mapping.create,
    createMany: mapping.createMany,
    createManyAndReturn: mapping.createManyAndReturn,
    delete: mapping.deleteOne || mapping.deleteSingle || mapping.delete,
    update: mapping.updateOne || mapping.updateSingle || mapping.update,
    deleteMany: mapping.deleteMany,
    updateMany: mapping.updateMany,
    upsert: mapping.upsertOne || mapping.upsertSingle || mapping.upsert,
    aggregate: mapping.aggregate,
    groupBy: mapping.groupBy,
    findRaw: mapping.findRaw,
    aggregateRaw: mapping.aggregateRaw
  }));
  return {
    modelOperations,
    otherOperations: mappings.otherOperations
  };
}

// src/generation/generateClient.ts
var import_crypto2 = require("crypto");
var import_env_paths = __toESM(require_env_paths());
var import_fs2 = require("fs");
var import_promises = __toESM(require("fs/promises"));
var import_fs_extra = __toESM(require_lib());
var import_path5 = __toESM(require("path"));
var import_pkg_up = __toESM(require_pkg_up());
var import_package = __toESM(require_package2());

// src/generation/getDMMF.ts
function getPrismaClientDMMF(dmmf) {
  return externalToInternalDmmf(dmmf);
}

// ../../node_modules/.pnpm/flat-map-polyfill@0.3.8/node_modules/flat-map-polyfill/dist/cjs/index.js
require_flatten();
require_flat_map();

// src/generation/TSClient/Enum.ts
var import_indent_string = __toESM(require_indent_string());

// src/runtime/core/types/exported/ObjectEnums.ts
var objectEnumNames = ["JsonNullValueInput", "NullableJsonNullValueInput", "JsonNullValueFilter"];
var secret = Symbol();
var representations = /* @__PURE__ */ new WeakMap();
var ObjectEnumValue = class {
  constructor(arg) {
    if (arg === secret) {
      representations.set(this, `Prisma.${this._getName()}`);
    } else {
      representations.set(this, `new Prisma.${this._getNamespace()}.${this._getName()}()`);
    }
  }
  _getName() {
    return this.constructor.name;
  }
  toString() {
    return representations.get(this);
  }
};
var NullTypesEnumValue = class extends ObjectEnumValue {
  _getNamespace() {
    return "NullTypes";
  }
};
var DbNull = class extends NullTypesEnumValue {
};
setClassName2(DbNull, "DbNull");
var JsonNull = class extends NullTypesEnumValue {
};
setClassName2(JsonNull, "JsonNull");
var AnyNull = class extends NullTypesEnumValue {
};
setClassName2(AnyNull, "AnyNull");
var objectEnumValues = {
  classes: {
    DbNull,
    JsonNull,
    AnyNull
  },
  instances: {
    DbNull: new DbNull(secret),
    JsonNull: new JsonNull(secret),
    AnyNull: new AnyNull(secret)
  }
};
function setClassName2(classObject, name) {
  Object.defineProperty(classObject, "name", {
    value: name,
    configurable: true
  });
}

// src/runtime/strictEnum.ts
var strictEnumNames = ["TransactionIsolationLevel"];

// src/generation/TSClient/constants.ts
var TAB_SIZE = 2;

// src/generation/TSClient/Enum.ts
var Enum = class {
  constructor(type, useNamespace) {
    this.type = type;
    this.useNamespace = useNamespace;
  }
  isObjectEnum() {
    return this.useNamespace && objectEnumNames.includes(this.type.name);
  }
  isStrictEnum() {
    return this.useNamespace && strictEnumNames.includes(this.type.name);
  }
  toJS() {
    const { type } = this;
    const enumVariants = `{
${(0, import_indent_string.default)(type.values.map((v) => `${v}: ${this.getValueJS(v)}`).join(",\n"), TAB_SIZE)}
}`;
    const enumBody = this.isStrictEnum() ? `makeStrictEnum(${enumVariants})` : enumVariants;
    return this.useNamespace ? `exports.Prisma.${type.name} = ${enumBody};` : `exports.${type.name} = exports.$Enums.${type.name} = ${enumBody};`;
  }
  getValueJS(value) {
    return this.isObjectEnum() ? `Prisma.${value}` : `'${value}'`;
  }
  toTS() {
    const { type } = this;
    return `export const ${type.name}: {
${(0, import_indent_string.default)(type.values.map((v) => `${v}: ${this.getValueTS(v)}`).join(",\n"), TAB_SIZE)}
};

export type ${type.name} = (typeof ${type.name})[keyof typeof ${type.name}]
`;
  }
  getValueTS(value) {
    return this.isObjectEnum() ? `typeof ${value}` : `'${value}'`;
  }
};

// src/generation/TSClient/Generable.ts
function JS(gen) {
  return gen.toJS?.() ?? "";
}
function BrowserJS(gen) {
  return gen.toBrowserJS?.() ?? "";
}
function TS(gen) {
  return gen.toTS();
}

// src/generation/TSClient/Input.ts
var import_indent_string2 = __toESM(require_indent_string());

// src/runtime/utils/uniqueBy.ts
function uniqueBy(arr, callee) {
  const result = {};
  for (const value of arr) {
    const hash = callee(value);
    if (!result[hash]) {
      result[hash] = value;
    }
  }
  return Object.values(result);
}

// src/generation/ts-builders/ArraySpread.ts
init_TypeBuilder();
var ArraySpread = class extends TypeBuilder {
  constructor(innerType) {
    super();
    this.innerType = innerType;
  }
  write(writer) {
    writer.write("[...").write(this.innerType).write("]");
  }
};
function arraySpread(innerType) {
  return new ArraySpread(innerType);
}

// src/generation/ts-builders/ArrayType.ts
init_TypeBuilder();
var ArrayType = class extends TypeBuilder {
  constructor(elementType) {
    super();
    this.elementType = elementType;
  }
  write(writer) {
    this.elementType.writeIndexed(writer);
    writer.write("[]");
  }
};
function array(elementType) {
  return new ArrayType(elementType);
}

// src/generation/ts-builders/ConstDeclaration.ts
var ConstDeclaration = class {
  constructor(name, type) {
    this.name = name;
    this.type = type;
  }
  setDocComment(docComment2) {
    this.docComment = docComment2;
    return this;
  }
  write(writer) {
    if (this.docComment) {
      writer.write(this.docComment);
    }
    writer.write("const ").write(this.name).write(": ").write(this.type);
  }
};
function constDeclaration(name, type) {
  return new ConstDeclaration(name, type);
}

// src/generation/ts-builders/DocComment.ts
var DocComment = class {
  constructor(startingText) {
    this.lines = [];
    if (startingText) {
      this.addText(startingText);
    }
  }
  addText(text) {
    this.lines.push(...text.split("\n"));
    return this;
  }
  write(writer) {
    writer.writeLine("/**");
    for (const line of this.lines) {
      writer.writeLine(` * ${line}`);
    }
    writer.writeLine(" */");
    return writer;
  }
};
function docComment(firstParameter, ...args) {
  if (typeof firstParameter === "string" || typeof firstParameter === "undefined") {
    return new DocComment(firstParameter);
  }
  return docCommentTag(firstParameter, args);
}
function docCommentTag(strings, args) {
  const docComment2 = new DocComment();
  const fullText = strings.flatMap((str, i) => {
    if (i < args.length) {
      return [str, args[i]];
    }
    return [str];
  }).join("");
  const lines = trimEmptyLines(fullText.split("\n"));
  if (lines.length === 0) {
    return docComment2;
  }
  const indent9 = getIndent(lines[0]);
  for (const line of lines) {
    docComment2.addText(line.slice(indent9));
  }
  return docComment2;
}
function trimEmptyLines(lines) {
  const firstLine = findFirstNonEmptyLine(lines);
  const lastLine = findLastNonEmptyLine(lines);
  if (firstLine === -1 || lastLine === -1) {
    return [];
  }
  return lines.slice(firstLine, lastLine + 1);
}
function findFirstNonEmptyLine(lines) {
  return lines.findIndex((line) => !isEmptyLine(line));
}
function findLastNonEmptyLine(lines) {
  let i = lines.length - 1;
  while (i > 0 && isEmptyLine(lines[i])) {
    i--;
  }
  return i;
}
function isEmptyLine(line) {
  return line.trim().length === 0;
}
function getIndent(line) {
  let indent9 = 0;
  while (line[indent9] === " ") {
    indent9++;
  }
  return indent9;
}

// src/generation/ts-builders/Export.ts
var Export = class {
  constructor(declaration) {
    this.declaration = declaration;
  }
  setDocComment(docComment2) {
    this.docComment = docComment2;
    return this;
  }
  write(writer) {
    if (this.docComment) {
      writer.write(this.docComment);
    }
    writer.write("export ").write(this.declaration);
  }
};
function moduleExport(declaration) {
  return new Export(declaration);
}

// src/generation/ts-builders/ExportFrom.ts
var NamespaceExport = class {
  constructor(from, namespace2) {
    this.from = from;
    this.namespace = namespace2;
  }
  write(writer) {
    writer.write(`export * as ${this.namespace} from '${this.from}'`);
  }
};
var BindingsExport = class {
  constructor(from) {
    this.from = from;
    this.namedExports = [];
  }
  named(namedExport) {
    if (typeof namedExport === "string") {
      namedExport = new NamedExport(namedExport);
    }
    this.namedExports.push(namedExport);
    return this;
  }
  write(writer) {
    writer.write("export ").write("{ ").writeJoined(", ", this.namedExports).write(" }").write(` from "${this.from}"`);
  }
};
var NamedExport = class {
  constructor(name) {
    this.name = name;
  }
  as(alias) {
    this.alias = alias;
    return this;
  }
  write(writer) {
    writer.write(this.name);
    if (this.alias) {
      writer.write(" as ").write(this.alias);
    }
  }
};
var ExportAllFrom = class {
  constructor(from) {
    this.from = from;
  }
  asNamespace(namespace2) {
    return new NamespaceExport(this.from, namespace2);
  }
  named(binding) {
    return new BindingsExport(this.from).named(binding);
  }
  write(writer) {
    writer.write(`export * from "${this.from}"`);
  }
};
function moduleExportFrom(from) {
  return new ExportAllFrom(from);
}

// src/generation/ts-builders/File.ts
var File = class {
  constructor() {
    this.imports = [];
    this.declarations = [];
  }
  addImport(moduleImport2) {
    this.imports.push(moduleImport2);
    return this;
  }
  add(declaration) {
    this.declarations.push(declaration);
  }
  write(writer) {
    for (const moduleImport2 of this.imports) {
      writer.writeLine(moduleImport2);
    }
    if (this.imports.length > 0) {
      writer.newLine();
    }
    for (const [i, declaration] of this.declarations.entries()) {
      writer.writeLine(declaration);
      if (i < this.declarations.length - 1) {
        writer.newLine();
      }
    }
  }
};
function file() {
  return new File();
}

// src/generation/ts-builders/PrimitiveType.ts
init_TypeBuilder();
var PrimitiveType = class extends TypeBuilder {
  constructor(name) {
    super();
    this.name = name;
  }
  write(writer) {
    writer.write(this.name);
  }
};
var stringType = new PrimitiveType("string");
var numberType = new PrimitiveType("number");
var booleanType = new PrimitiveType("boolean");
var nullType = new PrimitiveType("null");
var undefinedType = new PrimitiveType("undefined");
var bigintType = new PrimitiveType("bigint");
var unknownType = new PrimitiveType("unknown");
var anyType = new PrimitiveType("any");
var voidType = new PrimitiveType("void");
var thisType = new PrimitiveType("this");
var neverType = new PrimitiveType("never");

// src/generation/ts-builders/FunctionType.ts
init_TypeBuilder();
var FunctionType = class extends TypeBuilder {
  constructor() {
    super(...arguments);
    this.needsParenthesisWhenIndexed = true;
    this.needsParenthesisInKeyof = true;
    this.needsParenthesisInUnion = true;
    this.returnType = voidType;
    this.parameters = [];
    this.genericParameters = [];
  }
  setReturnType(returnType) {
    this.returnType = returnType;
    return this;
  }
  addParameter(param) {
    this.parameters.push(param);
    return this;
  }
  addGenericParameter(param) {
    this.genericParameters.push(param);
    return this;
  }
  write(writer) {
    if (this.genericParameters.length > 0) {
      writer.write("<").writeJoined(", ", this.genericParameters).write(">");
    }
    writer.write("(").writeJoined(", ", this.parameters).write(") => ").write(this.returnType);
  }
};
function functionType() {
  return new FunctionType();
}

// src/generation/ts-builders/NamedType.ts
init_TypeBuilder();
var NamedType = class extends TypeBuilder {
  constructor(name) {
    super();
    this.name = name;
    this.genericArguments = [];
  }
  addGenericArgument(type) {
    this.genericArguments.push(type);
    return this;
  }
  write(writer) {
    writer.write(this.name);
    if (this.genericArguments.length > 0) {
      writer.write("<").writeJoined(", ", this.genericArguments).write(">");
    }
  }
};
function namedType(name) {
  return new NamedType(name);
}

// src/generation/ts-builders/GenericParameter.ts
var GenericParameter = class {
  constructor(name) {
    this.name = name;
  }
  extends(type) {
    this.extendedType = type;
    return this;
  }
  default(type) {
    this.defaultType = type;
    return this;
  }
  toArgument() {
    return new NamedType(this.name);
  }
  write(writer) {
    writer.write(this.name);
    if (this.extendedType) {
      writer.write(" extends ").write(this.extendedType);
    }
    if (this.defaultType) {
      writer.write(" = ").write(this.defaultType);
    }
  }
};
function genericParameter(name) {
  return new GenericParameter(name);
}

// src/generation/ts-builders/helpers.ts
function omit(type, keyType2) {
  return namedType("Omit").addGenericArgument(type).addGenericArgument(keyType2);
}
function promise(resultType) {
  return new NamedType("$Utils.JsPromise").addGenericArgument(resultType);
}
function prismaPromise(resultType) {
  return new NamedType("Prisma.PrismaPromise").addGenericArgument(resultType);
}
function optional(innerType) {
  return new NamedType("$Utils.Optional").addGenericArgument(innerType);
}

// src/generation/ts-builders/Import.ts
var NamespaceImport = class {
  constructor(alias, from) {
    this.alias = alias;
    this.from = from;
  }
  write(writer) {
    writer.write("import * as ").write(this.alias).write(` from "${this.from}"`);
  }
};
var BindingsImport = class {
  constructor(from) {
    this.from = from;
    this.namedImports = [];
  }
  default(name) {
    this.defaultImport = name;
    return this;
  }
  named(namedImport) {
    if (typeof namedImport === "string") {
      namedImport = new NamedImport(namedImport);
    }
    this.namedImports.push(namedImport);
    return this;
  }
  write(writer) {
    writer.write("import ");
    if (this.defaultImport) {
      writer.write(this.defaultImport);
      if (this.hasNamedImports()) {
        writer.write(", ");
      }
    }
    if (this.hasNamedImports()) {
      writer.write("{ ").writeJoined(", ", this.namedImports).write(" }");
    }
    writer.write(` from "${this.from}"`);
  }
  hasNamedImports() {
    return this.namedImports.length > 0;
  }
};
var NamedImport = class {
  constructor(name) {
    this.name = name;
  }
  as(alias) {
    this.alias = alias;
    return this;
  }
  write(writer) {
    writer.write(this.name);
    if (this.alias) {
      writer.write(" as ").write(this.alias);
    }
  }
};
var ModuleImport = class {
  constructor(from) {
    this.from = from;
  }
  asNamespace(alias) {
    return new NamespaceImport(alias, this.from);
  }
  default(alias) {
    return new BindingsImport(this.from).default(alias);
  }
  named(namedImport) {
    return new BindingsImport(this.from).named(namedImport);
  }
  write(writer) {
    writer.write("import ").write(`"${this.from}"`);
  }
};
function moduleImport(from) {
  return new ModuleImport(from);
}

// src/generation/ts-builders/Interface.ts
init_TypeBuilder();
var InterfaceDeclaration = class extends TypeBuilder {
  constructor(name) {
    super();
    this.name = name;
    this.needsParenthesisWhenIndexed = true;
    this.items = [];
    this.genericParameters = [];
    this.extendedTypes = [];
  }
  add(item) {
    this.items.push(item);
    return this;
  }
  addMultiple(items) {
    for (const item of items) {
      this.add(item);
    }
    return this;
  }
  addGenericParameter(param) {
    this.genericParameters.push(param);
    return this;
  }
  extends(type) {
    this.extendedTypes.push(type);
    return this;
  }
  write(writer) {
    writer.write("interface ").write(this.name);
    if (this.genericParameters.length > 0) {
      writer.write("<").writeJoined(", ", this.genericParameters).write(">");
    }
    if (this.extendedTypes.length > 0) {
      writer.write(" extends ").writeJoined(", ", this.extendedTypes);
    }
    if (this.items.length === 0) {
      writer.writeLine(" {}");
      return;
    }
    writer.writeLine(" {").withIndent(() => {
      for (const item of this.items) {
        writer.writeLine(item);
      }
    }).write("}");
  }
};
function interfaceDeclaration(name) {
  return new InterfaceDeclaration(name);
}

// src/generation/ts-builders/Method.ts
var Method = class {
  constructor(name) {
    this.name = name;
    this.returnType = voidType;
    this.parameters = [];
    this.genericParameters = [];
  }
  setDocComment(docComment2) {
    this.docComment = docComment2;
    return this;
  }
  setReturnType(returnType) {
    this.returnType = returnType;
    return this;
  }
  addParameter(param) {
    this.parameters.push(param);
    return this;
  }
  addGenericParameter(param) {
    this.genericParameters.push(param);
    return this;
  }
  write(writer) {
    if (this.docComment) {
      writer.write(this.docComment);
    }
    writer.write(this.name);
    if (this.genericParameters.length > 0) {
      writer.write("<").writeJoined(", ", this.genericParameters).write(">");
    }
    writer.write("(");
    if (this.parameters.length > 0) {
      writer.writeJoined(", ", this.parameters);
    }
    writer.write(")");
    if (this.name !== "constructor") {
      writer.write(": ").write(this.returnType);
    }
  }
};
function method(name) {
  return new Method(name);
}

// src/generation/ts-builders/NamespaceDeclaration.ts
var NamespaceDeclaration = class {
  constructor(name) {
    this.name = name;
    this.items = [];
  }
  add(declaration) {
    this.items.push(declaration);
  }
  write(writer) {
    writer.writeLine(`namespace ${this.name} {`).withIndent(() => {
      for (const item of this.items) {
        writer.writeLine(item);
      }
    }).write("}");
  }
};
function namespace(name) {
  return new NamespaceDeclaration(name);
}

// src/generation/ts-builders/ObjectType.ts
init_TypeBuilder();
var ObjectType = class extends TypeBuilder {
  constructor() {
    super(...arguments);
    this.needsParenthesisWhenIndexed = true;
    this.items = [];
    this.inline = false;
  }
  add(item) {
    this.items.push(item);
    return this;
  }
  addMultiple(items) {
    for (const item of items) {
      this.add(item);
    }
    return this;
  }
  formatInline() {
    this.inline = true;
    return this;
  }
  write(writer) {
    if (this.items.length === 0) {
      writer.write("{}");
    } else if (this.inline) {
      this.writeInline(writer);
    } else {
      this.writeMultiline(writer);
    }
  }
  writeMultiline(writer) {
    writer.writeLine("{").withIndent(() => {
      for (const item of this.items) {
        writer.writeLine(item);
      }
    }).write("}");
  }
  writeInline(writer) {
    writer.write("{ ").writeJoined(", ", this.items).write(" }");
  }
};
function objectType() {
  return new ObjectType();
}

// src/generation/ts-builders/Parameter.ts
var Parameter = class {
  constructor(name, type) {
    this.name = name;
    this.type = type;
    this.isOptional = false;
  }
  optional() {
    this.isOptional = true;
    return this;
  }
  write(writer) {
    writer.write(this.name);
    if (this.isOptional) {
      writer.write("?");
    }
    writer.write(": ").write(this.type);
  }
};
function parameter(name, type) {
  return new Parameter(name, type);
}

// src/generation/ts-builders/Property.ts
var Property = class {
  constructor(name, type) {
    this.name = name;
    this.type = type;
    this.isOptional = false;
    this.isReadonly = false;
  }
  optional() {
    this.isOptional = true;
    return this;
  }
  readonly() {
    this.isReadonly = true;
    return this;
  }
  setDocComment(docComment2) {
    this.docComment = docComment2;
    return this;
  }
  write(writer) {
    if (this.docComment) {
      writer.write(this.docComment);
    }
    if (this.isReadonly) {
      writer.write("readonly ");
    }
    if (typeof this.name === "string") {
      if (isValidJsIdentifier(this.name)) {
        writer.write(this.name);
      } else {
        writer.write("[").write(JSON.stringify(this.name)).write("]");
      }
    } else {
      writer.write("[").write(this.name).write("]");
    }
    if (this.isOptional) {
      writer.write("?");
    }
    writer.write(": ").write(this.type);
  }
};
function property(name, type) {
  return new Property(name, type);
}

// src/generation/ts-builders/Writer.ts
var INDENT_SIZE = 2;
var Writer = class {
  constructor(startingIndent = 0, context) {
    this.context = context;
    this.lines = [];
    this.currentLine = "";
    this.currentIndent = 0;
    this.currentIndent = startingIndent;
  }
  /**
   * Adds provided value to the current line. Does not end the line.
   *
   * @param value
   * @returns
   */
  write(value) {
    if (typeof value === "string") {
      this.currentLine += value;
    } else {
      value.write(this);
    }
    return this;
  }
  /**
   * Adds several `values` to the current line, separated by `separator`. Both values and separator
   * can also be `Builder` instances for more advanced formatting.
   *
   * @param separator
   * @param values
   * @param writeItem allow to customize how individual item is written
   * @returns
   */
  writeJoined(separator, values, writeItem = (item, w) => w.write(item)) {
    const last = values.length - 1;
    for (let i = 0; i < values.length; i++) {
      writeItem(values[i], this);
      if (i !== last) {
        this.write(separator);
      }
    }
    return this;
  }
  /**
   * Adds a string to current line, flushes current line and starts a new line.
   * @param line
   * @returns
   */
  writeLine(line) {
    return this.write(line).newLine();
  }
  /**
   * Flushes current line and starts a new line. New line starts at previously configured indentation level
   * @returns
   */
  newLine() {
    this.lines.push(this.indentedCurrentLine());
    this.currentLine = "";
    this.marginSymbol = void 0;
    const afterNextNewLineCallback = this.afterNextNewLineCallback;
    this.afterNextNewLineCallback = void 0;
    afterNextNewLineCallback?.();
    return this;
  }
  /**
   * Increases indentation level by 1, calls provided callback and then decreases indentation again.
   * Could be used for writing indented blocks of text:
   *
   * @example
   * ```ts
   * writer
   *   .writeLine('{')
   *   .withIndent(() => {
   *      writer.writeLine('foo: 123');
   *      writer.writeLine('bar: 456');
   *   })
   *   .writeLine('}')
   * ```
   * @param callback
   * @returns
   */
  withIndent(callback) {
    this.indent();
    callback(this);
    this.unindent();
    return this;
  }
  /**
   * Calls provided callback next time when new line is started.
   * Callback is called after old line have already been flushed and a new
   * line have been started. Can be used for adding "between the lines" decorations,
   * such as underlines.
   *
   * @param callback
   * @returns
   */
  afterNextNewline(callback) {
    this.afterNextNewLineCallback = callback;
    return this;
  }
  /**
   * Increases indentation level of the current line by 1
   * @returns
   */
  indent() {
    this.currentIndent++;
    return this;
  }
  /**
   * Decreases indentation level of the current line by 1, if it is possible
   * @returns
   */
  unindent() {
    if (this.currentIndent > 0) {
      this.currentIndent--;
    }
    return this;
  }
  /**
   * Adds a symbol, that will replace the first character of the current line (including indentation)
   * when it is flushed. Can be used for adding markers to the line.
   *
   * Note: if indentation level of the line is 0, it will replace the first actually printed character
   * of the line. Use with caution.
   * @param symbol
   * @returns
   */
  addMarginSymbol(symbol) {
    this.marginSymbol = symbol;
    return this;
  }
  toString() {
    return this.lines.concat(this.indentedCurrentLine()).join("\n");
  }
  getCurrentLineLength() {
    return this.currentLine.length;
  }
  indentedCurrentLine() {
    const line = this.currentLine.padStart(this.currentLine.length + INDENT_SIZE * this.currentIndent);
    if (this.marginSymbol) {
      return this.marginSymbol + line.slice(1);
    }
    return line;
  }
};

// src/generation/ts-builders/stringify.ts
function stringify(builder, { indentLevel = 0, newLine = "none" } = {}) {
  const str = new Writer(indentLevel, void 0).write(builder).toString();
  switch (newLine) {
    case "none":
      return str;
    case "leading":
      return "\n" + str;
    case "trailing":
      return str + "\n";
    case "both":
      return "\n" + str + "\n";
    default:
      assertNever(newLine, "Unexpected value");
  }
}

// src/generation/ts-builders/StringLiteralType.ts
init_TypeBuilder();
var StringLiteralType = class extends TypeBuilder {
  constructor(content) {
    super();
    this.content = content;
  }
  write(writer) {
    writer.write(JSON.stringify(this.content));
  }
};
function stringLiteral(content) {
  return new StringLiteralType(content);
}

// src/generation/ts-builders/TupleType.ts
init_TypeBuilder();
var TupleItem = class {
  constructor(type) {
    this.type = type;
  }
  setName(name) {
    this.name = name;
    return this;
  }
  write(writer) {
    if (this.name) {
      writer.write(this.name).write(": ");
    }
    writer.write(this.type);
  }
};
var TupleType = class extends TypeBuilder {
  constructor() {
    super(...arguments);
    this.items = [];
  }
  add(item) {
    if (item instanceof TypeBuilder) {
      item = new TupleItem(item);
    }
    this.items.push(item);
    return this;
  }
  write(writer) {
    writer.write("[").writeJoined(", ", this.items).write("]");
  }
};
function tupleType() {
  return new TupleType();
}
function tupleItem(type) {
  return new TupleItem(type);
}

// src/generation/ts-builders/TypeDeclaration.ts
var TypeDeclaration = class {
  constructor(name, type) {
    this.name = name;
    this.type = type;
    this.genericParameters = [];
  }
  addGenericParameter(param) {
    this.genericParameters.push(param);
    return this;
  }
  setName(name) {
    this.name = name;
    return this;
  }
  setDocComment(docComment2) {
    this.docComment = docComment2;
    return this;
  }
  write(writer) {
    if (this.docComment) {
      writer.write(this.docComment);
    }
    writer.write("type ").write(this.name);
    if (this.genericParameters.length > 0) {
      writer.write("<").writeJoined(", ", this.genericParameters).write(">");
    }
    writer.write(" = ").write(this.type);
  }
};
function typeDeclaration(name, type) {
  return new TypeDeclaration(name, type);
}

// src/generation/ts-builders/UnionType.ts
init_TypeBuilder();
var UnionType = class extends TypeBuilder {
  constructor(firstType) {
    super();
    this.needsParenthesisWhenIndexed = true;
    this.needsParenthesisInKeyof = true;
    this.variants = [firstType];
  }
  addVariant(variant) {
    this.variants.push(variant);
    return this;
  }
  addVariants(variants) {
    for (const variant of variants) {
      this.addVariant(variant);
    }
    return this;
  }
  write(writer) {
    writer.writeJoined(" | ", this.variants, (variant, writer2) => {
      if (variant.needsParenthesisInUnion) {
        writer2.write("(").write(variant).write(")");
      } else {
        writer2.write(variant);
      }
    });
  }
  mapVariants(callback) {
    return unionType(this.variants.map((v) => callback(v)));
  }
};
function unionType(types) {
  if (Array.isArray(types)) {
    if (types.length === 0) {
      throw new TypeError("Union types array can not be empty");
    }
    const union = new UnionType(types[0]);
    for (let i = 1; i < types.length; i++) {
      union.addVariant(types[i]);
    }
    return union;
  }
  return new UnionType(types);
}

// src/generation/ts-builders/WellKnownSymbol.ts
var WellKnownSymbol = class {
  constructor(name) {
    this.name = name;
  }
  write(writer) {
    writer.write("Symbol.").write(this.name);
  }
};
function wellKnownSymbol(name) {
  return new WellKnownSymbol(name);
}
var toStringTag = wellKnownSymbol("toStringTag");

// src/generation/utils.ts
function getSelectName(modelName) {
  return `${modelName}Select`;
}
function getSelectCreateManyAndReturnName(modelName) {
  return `${modelName}SelectCreateManyAndReturn`;
}
function getIncludeName(modelName) {
  return `${modelName}Include`;
}
function getIncludeCreateManyAndReturnName(modelName) {
  return `${modelName}IncludeCreateManyAndReturn`;
}
function getCreateManyAndReturnOutputType(modelName) {
  return `CreateMany${modelName}AndReturnOutputType`;
}
function getOmitName(modelName) {
  return `${modelName}Omit`;
}
function getAggregateName(modelName) {
  return `Aggregate${capitalize2(modelName)}`;
}
function getGroupByName(modelName) {
  return `${capitalize2(modelName)}GroupByOutputType`;
}
function getAvgAggregateName(modelName) {
  return `${capitalize2(modelName)}AvgAggregateOutputType`;
}
function getSumAggregateName(modelName) {
  return `${capitalize2(modelName)}SumAggregateOutputType`;
}
function getMinAggregateName(modelName) {
  return `${capitalize2(modelName)}MinAggregateOutputType`;
}
function getMaxAggregateName(modelName) {
  return `${capitalize2(modelName)}MaxAggregateOutputType`;
}
function getCountAggregateInputName(modelName) {
  return `${capitalize2(modelName)}CountAggregateInputType`;
}
function getCountAggregateOutputName(modelName) {
  return `${capitalize2(modelName)}CountAggregateOutputType`;
}
function getAggregateInputType(aggregateOutputType) {
  return aggregateOutputType.replace(/OutputType$/, "InputType");
}
function getGroupByArgsName(modelName) {
  return `${modelName}GroupByArgs`;
}
function getGroupByPayloadName(modelName) {
  return `Get${capitalize2(modelName)}GroupByPayload`;
}
function getAggregateArgsName(modelName) {
  return `${capitalize2(modelName)}AggregateArgs`;
}
function getAggregateGetName(modelName) {
  return `Get${capitalize2(modelName)}AggregateType`;
}
function getFieldArgName(field, modelName) {
  if (field.args.length) {
    return getModelFieldArgsName(field, modelName);
  }
  return getModelArgName(field.outputType.type);
}
function getModelFieldArgsName(field, modelName) {
  return `${modelName}$${field.name}Args`;
}
function getLegacyModelArgName(modelName) {
  return `${modelName}Args`;
}
function getModelArgName(modelName, action) {
  if (!action) {
    return `${modelName}DefaultArgs`;
  }
  switch (action) {
    case DMMF.ModelAction.findMany:
      return `${modelName}FindManyArgs`;
    case DMMF.ModelAction.findUnique:
      return `${modelName}FindUniqueArgs`;
    case DMMF.ModelAction.findUniqueOrThrow:
      return `${modelName}FindUniqueOrThrowArgs`;
    case DMMF.ModelAction.findFirst:
      return `${modelName}FindFirstArgs`;
    case DMMF.ModelAction.findFirstOrThrow:
      return `${modelName}FindFirstOrThrowArgs`;
    case DMMF.ModelAction.upsert:
      return `${modelName}UpsertArgs`;
    case DMMF.ModelAction.update:
      return `${modelName}UpdateArgs`;
    case DMMF.ModelAction.updateMany:
      return `${modelName}UpdateManyArgs`;
    case DMMF.ModelAction.delete:
      return `${modelName}DeleteArgs`;
    case DMMF.ModelAction.create:
      return `${modelName}CreateArgs`;
    case DMMF.ModelAction.createMany:
      return `${modelName}CreateManyArgs`;
    case DMMF.ModelAction.createManyAndReturn:
      return `${modelName}CreateManyAndReturnArgs`;
    case DMMF.ModelAction.deleteMany:
      return `${modelName}DeleteManyArgs`;
    case DMMF.ModelAction.groupBy:
      return getGroupByArgsName(modelName);
    case DMMF.ModelAction.aggregate:
      return getAggregateArgsName(modelName);
    case DMMF.ModelAction.count:
      return `${modelName}CountArgs`;
    case DMMF.ModelAction.findRaw:
      return `${modelName}FindRawArgs`;
    case DMMF.ModelAction.aggregateRaw:
      return `${modelName}AggregateRawArgs`;
    default:
      assertNever(action, `Unknown action: ${action}`);
  }
}
function getPayloadName(modelName, namespace2 = true) {
  if (namespace2) {
    return `Prisma.${getPayloadName(modelName, false)}`;
  }
  return `$${modelName}Payload`;
}
function getFieldRefsTypeName(name) {
  return `${name}FieldRefs`;
}
function capitalize2(str) {
  return str[0].toUpperCase() + str.slice(1);
}
function getRefAllowedTypeName(type) {
  let typeName = type.type;
  if (type.isList) {
    typeName += "[]";
  }
  return `'${typeName}'`;
}
function appendSkipType(context, type) {
  if (context.isPreviewFeatureOn("strictUndefinedChecks")) {
    return unionType([type, namedType("$Types.Skip")]);
  }
  return type;
}
var extArgsParam = genericParameter("ExtArgs").extends(namedType("$Extensions.InternalArgs")).default(namedType("$Extensions.DefaultArgs"));

// src/generation/TSClient/Input.ts
var InputField = class {
  constructor(field, context, source) {
    this.field = field;
    this.context = context;
    this.source = source;
  }
  toTS() {
    const property2 = buildInputField(this.field, this.context, this.source);
    return stringify(property2);
  }
};
function buildInputField(field, context, source) {
  const tsType = buildAllFieldTypes(field.inputTypes, context, source);
  const tsProperty = property(field.name, field.isRequired ? tsType : appendSkipType(context, tsType));
  if (!field.isRequired) {
    tsProperty.optional();
  }
  const docComment2 = docComment();
  if (field.comment) {
    docComment2.addText(field.comment);
  }
  if (field.deprecation) {
    docComment2.addText(`@deprecated since ${field.deprecation.sinceVersion}: ${field.deprecation.reason}`);
  }
  if (docComment2.lines.length > 0) {
    tsProperty.setDocComment(docComment2);
  }
  return tsProperty;
}
function buildSingleFieldType(t, genericsInfo, source) {
  let type;
  const scalarType = GraphQLScalarToJSTypeTable[t.type];
  if (t.location === "enumTypes" && t.namespace === "model") {
    type = namedType(`$Enums.${t.type}`);
  } else if (t.type === "Null") {
    return nullType;
  } else if (Array.isArray(scalarType)) {
    const union = unionType(scalarType.map(namedInputType));
    if (t.isList) {
      return union.mapVariants((variant) => array(variant));
    }
    return union;
  } else {
    type = namedInputType(scalarType ?? t.type);
  }
  if (genericsInfo.typeRefNeedsGenericModelArg(t)) {
    if (source) {
      type.addGenericArgument(stringLiteral(source));
    } else {
      type.addGenericArgument(namedType("$PrismaModel"));
    }
  }
  if (t.isList) {
    return array(type);
  }
  return type;
}
function namedInputType(typeName) {
  return namedType(JSOutputTypeToInputType[typeName] ?? typeName);
}
function buildAllFieldTypes(inputTypes, context, source) {
  const inputObjectTypes = inputTypes.filter((t) => t.location === "inputObjectTypes" && !t.isList);
  const otherTypes = inputTypes.filter((t) => t.location !== "inputObjectTypes" || t.isList);
  const tsInputObjectTypes = inputObjectTypes.map((type) => buildSingleFieldType(type, context.genericArgsInfo, source));
  const tsOtherTypes = otherTypes.map((type) => buildSingleFieldType(type, context.genericArgsInfo, source));
  if (tsOtherTypes.length === 0) {
    return xorTypes(tsInputObjectTypes);
  }
  if (tsInputObjectTypes.length === 0) {
    return unionType(tsOtherTypes);
  }
  return unionType(xorTypes(tsInputObjectTypes)).addVariants(tsOtherTypes);
}
function xorTypes(types) {
  return types.reduce((prev, curr) => namedType("XOR").addGenericArgument(prev).addGenericArgument(curr));
}
var InputType = class {
  constructor(type, context) {
    this.type = type;
    this.context = context;
    this.generatedName = type.name;
  }
  toTS() {
    const { type } = this;
    const source = type.meta?.source;
    const fields = uniqueBy(type.fields, (f) => f.name);
    const body = `{
${(0, import_indent_string2.default)(
      fields.map((arg) => {
        return new InputField(arg, this.context, source).toTS();
      }).join("\n"),
      TAB_SIZE
    )}
}`;
    return `
export type ${this.getTypeName()} = ${wrapWithAtLeast(body, type)}`;
  }
  overrideName(name) {
    this.generatedName = name;
    return this;
  }
  getTypeName() {
    if (this.context.genericArgsInfo.typeNeedsGenericModelArg(this.type)) {
      return `${this.generatedName}<$PrismaModel = never>`;
    }
    return this.generatedName;
  }
};
function wrapWithAtLeast(body, input) {
  if (input.constraints?.fields && input.constraints.fields.length > 0) {
    const fields = input.constraints.fields.map((f) => `"${f}"`).join(" | ");
    return `Prisma.AtLeast<${body}, ${fields}>`;
  }
  return body;
}

// src/generation/TSClient/Model.ts
var import_indent_string3 = __toESM(require_indent_string());

// ../../node_modules/.pnpm/klona@2.0.6/node_modules/klona/dist/index.mjs
function klona(x) {
  if (typeof x !== "object") return x;
  var k, tmp, str = Object.prototype.toString.call(x);
  if (str === "[object Object]") {
    if (x.constructor !== Object && typeof x.constructor === "function") {
      tmp = new x.constructor();
      for (k in x) {
        if (x.hasOwnProperty(k) && tmp[k] !== x[k]) {
          tmp[k] = klona(x[k]);
        }
      }
    } else {
      tmp = {};
      for (k in x) {
        if (k === "__proto__") {
          Object.defineProperty(tmp, k, {
            value: klona(x[k]),
            configurable: true,
            enumerable: true,
            writable: true
          });
        } else {
          tmp[k] = klona(x[k]);
        }
      }
    }
    return tmp;
  }
  if (str === "[object Array]") {
    k = x.length;
    for (tmp = Array(k); k--; ) {
      tmp[k] = klona(x[k]);
    }
    return tmp;
  }
  if (str === "[object Set]") {
    tmp = /* @__PURE__ */ new Set();
    x.forEach(function(val) {
      tmp.add(klona(val));
    });
    return tmp;
  }
  if (str === "[object Map]") {
    tmp = /* @__PURE__ */ new Map();
    x.forEach(function(val, key) {
      tmp.set(klona(key), klona(val));
    });
    return tmp;
  }
  if (str === "[object Date]") {
    return /* @__PURE__ */ new Date(+x);
  }
  if (str === "[object RegExp]") {
    tmp = new RegExp(x.source, x.flags);
    tmp.lastIndex = x.lastIndex;
    return tmp;
  }
  if (str === "[object DataView]") {
    return new x.constructor(klona(x.buffer));
  }
  if (str === "[object ArrayBuffer]") {
    return x.slice(0);
  }
  if (str.slice(-6) === "Array]") {
    return new x.constructor(x);
  }
  return x;
}

// src/generation/TSClient/helpers.ts
var import_pluralize2 = __toESM(require_pluralize());

// src/generation/TSClient/jsdoc.ts
var Docs = {
  cursor: `{@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}`,
  pagination: `{@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}`,
  aggregations: `{@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}`,
  distinct: `{@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}`,
  sorting: `{@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}`
};
function addLinkToDocs(comment, docs) {
  return `${Docs[docs]}

${comment}`;
}
function getDeprecationString(since, replacement) {
  return `@deprecated since ${since} please use \`${replacement}\``;
}
var undefinedNote = `Note, that providing \`undefined\` is treated as the value not being there.
Read more here: https://pris.ly/d/null-undefined`;
var JSDocFields = {
  take: (singular, plural) => addLinkToDocs(`Take \`\xB1n\` ${plural} from the position of the cursor.`, "pagination"),
  skip: (singular, plural) => addLinkToDocs(`Skip the first \`n\` ${plural}.`, "pagination"),
  _count: (singular, plural) => addLinkToDocs(`Count returned ${plural}`, "aggregations"),
  _avg: () => addLinkToDocs(`Select which fields to average`, "aggregations"),
  _sum: () => addLinkToDocs(`Select which fields to sum`, "aggregations"),
  _min: () => addLinkToDocs(`Select which fields to find the minimum value`, "aggregations"),
  _max: () => addLinkToDocs(`Select which fields to find the maximum value`, "aggregations"),
  count: () => getDeprecationString("2.23.0", "_count"),
  avg: () => getDeprecationString("2.23.0", "_avg"),
  sum: () => getDeprecationString("2.23.0", "_sum"),
  min: () => getDeprecationString("2.23.0", "_min"),
  max: () => getDeprecationString("2.23.0", "_max"),
  distinct: (singular, plural) => addLinkToDocs(`Filter by unique combinations of ${plural}.`, "distinct"),
  orderBy: (singular, plural) => addLinkToDocs(`Determine the order of ${plural} to fetch.`, "sorting")
};
var JSDocs = {
  groupBy: {
    body: (ctx) => `Group by ${ctx.singular}.
${undefinedNote}
@param {${getGroupByArgsName(ctx.model.name)}} args - Group by arguments.
@example
// Group by city, order by createdAt, get count
const result = await prisma.user.groupBy({
  by: ['city', 'createdAt'],
  orderBy: {
    createdAt: true
  },
  _count: {
    _all: true
  },
})
`,
    fields: {}
  },
  create: {
    body: (ctx) => `Create a ${ctx.singular}.
@param {${getModelArgName(ctx.model.name, ctx.action)}} args - Arguments to create a ${ctx.singular}.
@example
// Create one ${ctx.singular}
const ${ctx.singular} = await ${ctx.method}({
  data: {
    // ... data to create a ${ctx.singular}
  }
})
`,
    fields: {
      data: (singular) => `The data needed to create a ${singular}.`
    }
  },
  createMany: {
    body: (ctx) => `Create many ${ctx.plural}.
@param {${getModelArgName(ctx.model.name, ctx.action)}} args - Arguments to create many ${ctx.plural}.
@example
// Create many ${ctx.plural}
const ${lowerCase(ctx.mapping.model)} = await ${ctx.method}({
  data: [
    // ... provide data here
  ]
})
    `,
    fields: {
      data: (singular, plural) => `The data used to create many ${plural}.`
    }
  },
  createManyAndReturn: {
    body: (ctx) => {
      const onlySelect = ctx.firstScalar ? `
// Create many ${ctx.plural} and only return the \`${ctx.firstScalar.name}\`
const ${lowerCase(ctx.mapping.model)}With${capitalize(ctx.firstScalar.name)}Only = await ${ctx.method}({ 
  select: { ${ctx.firstScalar.name}: true },
  data: [
    // ... provide data here
  ]
})` : "";
      return `Create many ${ctx.plural} and returns the data saved in the database.
@param {${getModelArgName(ctx.model.name, ctx.action)}} args - Arguments to create many ${ctx.plural}.
@example
// Create many ${ctx.plural}
const ${lowerCase(ctx.mapping.model)} = await ${ctx.method}({
  data: [
    // ... provide data here
  ]
})
${onlySelect}
${undefinedNote}
`;
    },
    fields: {
      data: (singular, plural) => `The data used to create many ${plural}.`
    }
  },
  findUnique: {
    body: (ctx) => `Find zero or one ${ctx.singular} that matches the filter.
@param {${getModelArgName(ctx.model.name, ctx.action)}} args - Arguments to find a ${ctx.singular}
@example
// Get one ${ctx.singular}
const ${lowerCase(ctx.mapping.model)} = await ${ctx.method}({
  where: {
    // ... provide filter here
  }
})`,
    fields: {
      where: (singular) => `Filter, which ${singular} to fetch.`
    }
  },
  findUniqueOrThrow: {
    body: (ctx) => `Find one ${ctx.singular} that matches the filter or throw an error with \`error.code='P2025'\` 
if no matches were found.
@param {${getModelArgName(ctx.model.name, ctx.action)}} args - Arguments to find a ${ctx.singular}
@example
// Get one ${ctx.singular}
const ${lowerCase(ctx.mapping.model)} = await ${ctx.method}({
  where: {
    // ... provide filter here
  }
})`,
    fields: {
      where: (singular) => `Filter, which ${singular} to fetch.`
    }
  },
  findFirst: {
    body: (ctx) => `Find the first ${ctx.singular} that matches the filter.
${undefinedNote}
@param {${getModelArgName(ctx.model.name, ctx.action)}} args - Arguments to find a ${ctx.singular}
@example
// Get one ${ctx.singular}
const ${lowerCase(ctx.mapping.model)} = await ${ctx.method}({
  where: {
    // ... provide filter here
  }
})`,
    fields: {
      where: (singular) => `Filter, which ${singular} to fetch.`,
      orderBy: JSDocFields.orderBy,
      cursor: (singular, plural) => addLinkToDocs(`Sets the position for searching for ${plural}.`, "cursor"),
      take: JSDocFields.take,
      skip: JSDocFields.skip,
      distinct: JSDocFields.distinct
    }
  },
  findFirstOrThrow: {
    body: (ctx) => `Find the first ${ctx.singular} that matches the filter or
throw \`PrismaKnownClientError\` with \`P2025\` code if no matches were found.
${undefinedNote}
@param {${getModelArgName(ctx.model.name, ctx.action)}} args - Arguments to find a ${ctx.singular}
@example
// Get one ${ctx.singular}
const ${lowerCase(ctx.mapping.model)} = await ${ctx.method}({
  where: {
    // ... provide filter here
  }
})`,
    fields: {
      where: (singular) => `Filter, which ${singular} to fetch.`,
      orderBy: JSDocFields.orderBy,
      cursor: (singular, plural) => addLinkToDocs(`Sets the position for searching for ${plural}.`, "cursor"),
      take: JSDocFields.take,
      skip: JSDocFields.skip,
      distinct: JSDocFields.distinct
    }
  },
  findMany: {
    body: (ctx) => {
      const onlySelect = ctx.firstScalar ? `
// Only select the \`${ctx.firstScalar.name}\`
const ${lowerCase(ctx.mapping.model)}With${capitalize(ctx.firstScalar.name)}Only = await ${ctx.method}({ select: { ${ctx.firstScalar.name}: true } })` : "";
      return `Find zero or more ${ctx.plural} that matches the filter.
${undefinedNote}
@param {${getModelArgName(ctx.model.name, ctx.action)}} args - Arguments to filter and select certain fields only.
@example
// Get all ${ctx.plural}
const ${ctx.mapping.plural} = await ${ctx.method}()

// Get first 10 ${ctx.plural}
const ${ctx.mapping.plural} = await ${ctx.method}({ take: 10 })
${onlySelect}
`;
    },
    fields: {
      where: (singular, plural) => `Filter, which ${plural} to fetch.`,
      orderBy: JSDocFields.orderBy,
      skip: JSDocFields.skip,
      cursor: (singular, plural) => addLinkToDocs(`Sets the position for listing ${plural}.`, "cursor"),
      take: JSDocFields.take
    }
  },
  update: {
    body: (ctx) => `Update one ${ctx.singular}.
@param {${getModelArgName(ctx.model.name, ctx.action)}} args - Arguments to update one ${ctx.singular}.
@example
// Update one ${ctx.singular}
const ${lowerCase(ctx.mapping.model)} = await ${ctx.method}({
  where: {
    // ... provide filter here
  },
  data: {
    // ... provide data here
  }
})
`,
    fields: {
      data: (singular) => `The data needed to update a ${singular}.`,
      where: (singular) => `Choose, which ${singular} to update.`
    }
  },
  upsert: {
    body: (ctx) => `Create or update one ${ctx.singular}.
@param {${getModelArgName(ctx.model.name, ctx.action)}} args - Arguments to update or create a ${ctx.singular}.
@example
// Update or create a ${ctx.singular}
const ${lowerCase(ctx.mapping.model)} = await ${ctx.method}({
  create: {
    // ... data to create a ${ctx.singular}
  },
  update: {
    // ... in case it already exists, update
  },
  where: {
    // ... the filter for the ${ctx.singular} we want to update
  }
})`,
    fields: {
      where: (singular) => `The filter to search for the ${singular} to update in case it exists.`,
      create: (singular) => `In case the ${singular} found by the \`where\` argument doesn't exist, create a new ${singular} with this data.`,
      update: (singular) => `In case the ${singular} was found with the provided \`where\` argument, update it with this data.`
    }
  },
  delete: {
    body: (ctx) => `Delete a ${ctx.singular}.
@param {${getModelArgName(ctx.model.name, ctx.action)}} args - Arguments to delete one ${ctx.singular}.
@example
// Delete one ${ctx.singular}
const ${ctx.singular} = await ${ctx.method}({
  where: {
    // ... filter to delete one ${ctx.singular}
  }
})
`,
    fields: {
      where: (singular) => `Filter which ${singular} to delete.`
    }
  },
  aggregate: {
    body: (ctx) => `Allows you to perform aggregations operations on a ${ctx.singular}.
${undefinedNote}
@param {${getModelArgName(
      ctx.model.name,
      ctx.action
    )}} args - Select which aggregations you would like to apply and on what fields.
@example
// Ordered by age ascending
// Where email contains prisma.io
// Limited to the 10 users
const aggregations = await prisma.user.aggregate({
  _avg: {
    age: true,
  },
  where: {
    email: {
      contains: "prisma.io",
    },
  },
  orderBy: {
    age: "asc",
  },
  take: 10,
})`,
    fields: {
      where: (singular) => `Filter which ${singular} to aggregate.`,
      orderBy: JSDocFields.orderBy,
      cursor: () => addLinkToDocs(`Sets the start position`, "cursor"),
      take: JSDocFields.take,
      skip: JSDocFields.skip,
      _count: JSDocFields._count,
      _avg: JSDocFields._avg,
      _sum: JSDocFields._sum,
      _min: JSDocFields._min,
      _max: JSDocFields._max,
      count: JSDocFields.count,
      avg: JSDocFields.avg,
      sum: JSDocFields.sum,
      min: JSDocFields.min,
      max: JSDocFields.max
    }
  },
  count: {
    body: (ctx) => `Count the number of ${ctx.plural}.
${undefinedNote}
@param {${getModelArgName(ctx.model.name, ctx.action)}} args - Arguments to filter ${ctx.plural} to count.
@example
// Count the number of ${ctx.plural}
const count = await ${ctx.method}({
  where: {
    // ... the filter for the ${ctx.plural} we want to count
  }
})`,
    fields: {}
  },
  updateMany: {
    body: (ctx) => `Update zero or more ${ctx.plural}.
${undefinedNote}
@param {${getModelArgName(ctx.model.name, ctx.action)}} args - Arguments to update one or more rows.
@example
// Update many ${ctx.plural}
const ${lowerCase(ctx.mapping.model)} = await ${ctx.method}({
  where: {
    // ... provide filter here
  },
  data: {
    // ... provide data here
  }
})
`,
    fields: {
      data: (singular, plural) => `The data used to update ${plural}.`,
      where: (singular, plural) => `Filter which ${plural} to update`
    }
  },
  deleteMany: {
    body: (ctx) => `Delete zero or more ${ctx.plural}.
@param {${getModelArgName(ctx.model.name, ctx.action)}} args - Arguments to filter ${ctx.plural} to delete.
@example
// Delete a few ${ctx.plural}
const { count } = await ${ctx.method}({
  where: {
    // ... provide filter here
  }
})
`,
    fields: {
      where: (singular, plural) => `Filter which ${plural} to delete`
    }
  },
  aggregateRaw: {
    body: (ctx) => `Perform aggregation operations on a ${ctx.singular}.
@param {${getModelArgName(ctx.model.name, ctx.action)}} args - Select which aggregations you would like to apply.
@example
const ${lowerCase(ctx.mapping.model)} = await ${ctx.method}({
  pipeline: [
    { $match: { status: "registered" } },
    { $group: { _id: "$country", total: { $sum: 1 } } }
  ]
})`,
    fields: {
      pipeline: () => "An array of aggregation stages to process and transform the document stream via the aggregation pipeline. ${@link https://docs.mongodb.com/manual/reference/operator/aggregation-pipeline MongoDB Docs}.",
      options: () => "Additional options to pass to the `aggregate` command ${@link https://docs.mongodb.com/manual/reference/command/aggregate/#command-fields MongoDB Docs}."
    }
  },
  findRaw: {
    body: (ctx) => `Find zero or more ${ctx.plural} that matches the filter.
@param {${getModelArgName(ctx.model.name, ctx.action)}} args - Select which filters you would like to apply.
@example
const ${lowerCase(ctx.mapping.model)} = await ${ctx.method}({
  filter: { age: { $gt: 25 } } 
})`,
    fields: {
      filter: () => "The query predicate filter. If unspecified, then all documents in the collection will match the predicate. ${@link https://docs.mongodb.com/manual/reference/operator/query MongoDB Docs}.",
      options: () => "Additional options to pass to the `find` command ${@link https://docs.mongodb.com/manual/reference/command/find/#command-fields MongoDB Docs}."
    }
  }
};

// src/generation/TSClient/helpers.ts
function getMethodJSDocBody(action, mapping, model) {
  const ctx = {
    singular: capitalize(mapping.model),
    plural: capitalize(mapping.plural),
    firstScalar: model.fields.find((f) => f.kind === "scalar"),
    method: `prisma.${lowerCase(mapping.model)}.${action}`,
    action,
    mapping,
    model
  };
  const jsdoc = JSDocs[action]?.body(ctx);
  return jsdoc ? jsdoc : "";
}
function getMethodJSDoc(action, mapping, model) {
  return wrapComment(getMethodJSDocBody(action, mapping, model));
}
function wrapComment(str) {
  return `/**
${str.split("\n").map((l) => " * " + l).join("\n")}
**/`;
}
function getArgFieldJSDoc(type, action, field) {
  if (!field || !action || !type) return;
  const fieldName = typeof field === "string" ? field : field.name;
  if (JSDocs[action] && JSDocs[action]?.fields[fieldName]) {
    const singular = type.name;
    const plural = (0, import_pluralize2.default)(type.name);
    const comment = JSDocs[action]?.fields[fieldName](singular, plural);
    return comment;
  }
  return void 0;
}
function escapeJson(str) {
  return str.replace(/\\n/g, "\\\\n").replace(/\\r/g, "\\\\r").replace(/\\t/g, "\\\\t");
}

// src/generation/TSClient/Args.ts
var ArgsTypeBuilder = class {
  constructor(type, context, action) {
    this.type = type;
    this.context = context;
    this.action = action;
    this.hasDefaultName = true;
    this.moduleExport = moduleExport(
      typeDeclaration(getModelArgName(type.name, action), objectType()).addGenericParameter(extArgsParam)
    ).setDocComment(docComment(`${type.name} ${action ?? "without action"}`));
  }
  addProperty(prop) {
    this.moduleExport.declaration.type.add(prop);
  }
  addSchemaArgs(args) {
    for (const arg of args) {
      const inputField = buildInputField(arg, this.context);
      const docComment2 = getArgFieldJSDoc(this.type, this.action, arg);
      if (docComment2) {
        inputField.setDocComment(docComment(docComment2));
      }
      this.addProperty(inputField);
    }
    return this;
  }
  addSelectArg(selectTypeName = getSelectName(this.type.name)) {
    this.addProperty(
      property(
        "select",
        unionType([namedType(selectTypeName).addGenericArgument(extArgsParam.toArgument()), nullType])
      ).optional().setDocComment(docComment(`Select specific fields to fetch from the ${this.type.name}`))
    );
    return this;
  }
  addIncludeArgIfHasRelations(includeTypeName = getIncludeName(this.type.name), type = this.type) {
    const hasRelationField = type.fields.some((f) => f.outputType.location === "outputObjectTypes");
    if (!hasRelationField) {
      return this;
    }
    this.addProperty(
      property(
        "include",
        unionType([namedType(includeTypeName).addGenericArgument(extArgsParam.toArgument()), nullType])
      ).optional().setDocComment(docComment("Choose, which related nodes to fetch as well"))
    );
    return this;
  }
  addOmitArg() {
    if (!this.context.isPreviewFeatureOn("omitApi")) {
      return this;
    }
    this.addProperty(
      property(
        "omit",
        unionType([
          namedType(getOmitName(this.type.name)).addGenericArgument(extArgsParam.toArgument()),
          nullType
        ])
      ).optional().setDocComment(docComment(`Omit specific fields from the ${this.type.name}`))
    );
    return this;
  }
  setGeneratedName(name) {
    this.hasDefaultName = false;
    this.moduleExport.declaration.setName(name);
    return this;
  }
  setComment(comment) {
    this.moduleExport.setDocComment(docComment(comment));
    return this;
  }
  createExport() {
    if (!this.action && this.hasDefaultName) {
      this.context.defaultArgsAliases.addPossibleAlias(
        getModelArgName(this.type.name),
        getLegacyModelArgName(this.type.name)
      );
    }
    this.context.defaultArgsAliases.registerArgName(this.moduleExport.declaration.name);
    return this.moduleExport;
  }
};

// src/generation/TSClient/ModelFieldRefs.ts
var ModelFieldRefs = class {
  constructor(outputType) {
    this.outputType = outputType;
  }
  toTS() {
    const { name } = this.outputType;
    return `

/**
 * Fields of the ${name} model
 */ 
interface ${getFieldRefsTypeName(name)} {
${this.stringifyFields()}
}
    `;
  }
  stringifyFields() {
    const { name } = this.outputType;
    return this.outputType.fields.filter((field) => field.outputType.location !== "outputObjectTypes").map((field) => {
      const fieldOutput = field.outputType;
      const refTypeName = getRefAllowedTypeName(fieldOutput);
      return `  readonly ${field.name}: FieldRef<"${name}", ${refTypeName}>`;
    }).join("\n");
  }
};

// src/generation/TSClient/Output.ts
function buildModelOutputProperty(field, dmmf) {
  let fieldTypeName = hasOwnProperty(GraphQLScalarToJSTypeTable, field.type) ? GraphQLScalarToJSTypeTable[field.type] : field.type;
  if (Array.isArray(fieldTypeName)) {
    fieldTypeName = fieldTypeName[0];
  }
  if (needsNamespace(field)) {
    fieldTypeName = `Prisma.${fieldTypeName}`;
  }
  let fieldType;
  if (field.kind === "object") {
    const payloadType = namedType(getPayloadName(field.type));
    if (!dmmf.isComposite(field.type)) {
      payloadType.addGenericArgument(namedType("ExtArgs"));
    }
    fieldType = payloadType;
  } else if (field.kind === "enum") {
    fieldType = namedType(`$Enums.${fieldTypeName}`);
  } else {
    fieldType = namedType(fieldTypeName);
  }
  if (field.isList) {
    fieldType = array(fieldType);
  } else if (!field.isRequired) {
    fieldType = unionType(fieldType).addVariant(nullType);
  }
  const property2 = property(field.name, fieldType);
  if (field.documentation) {
    property2.setDocComment(docComment(field.documentation));
  }
  return property2;
}
function buildOutputType(type) {
  return moduleExport(typeDeclaration(type.name, objectType().addMultiple(type.fields.map(buildOutputField))));
}
function buildOutputField(field) {
  let fieldType;
  if (field.outputType.location === "enumTypes" && field.outputType.namespace === "model") {
    fieldType = namedType(enumTypeName(field.outputType));
  } else {
    const typeNames = GraphQLScalarToJSTypeTable[field.outputType.type] ?? field.outputType.type;
    fieldType = Array.isArray(typeNames) ? namedType(typeNames[0]) : namedType(typeNames);
  }
  if (field.outputType.isList) {
    fieldType = array(fieldType);
  } else if (field.isNullable) {
    fieldType = unionType(fieldType).addVariant(nullType);
  }
  const property2 = property(field.name, fieldType);
  if (field.deprecation) {
    property2.setDocComment(
      docComment(`@deprecated since ${field.deprecation.sinceVersion} because ${field.deprecation.reason}`)
    );
  }
  return property2;
}
function enumTypeName(ref) {
  const name = ref.type;
  const namespace2 = ref.namespace === "model" ? "$Enums" : "Prisma";
  return `${namespace2}.${name}`;
}

// src/generation/TSClient/Payload.ts
function buildModelPayload(model, context) {
  const isComposite = context.dmmf.isComposite(model.name);
  const objects = objectType();
  const scalars = objectType();
  const composites = objectType();
  for (const field of model.fields) {
    if (field.kind === "object") {
      if (context.dmmf.isComposite(field.type)) {
        composites.add(buildModelOutputProperty(field, context.dmmf));
      } else {
        objects.add(buildModelOutputProperty(field, context.dmmf));
      }
    } else if (field.kind === "enum" || field.kind === "scalar") {
      scalars.add(buildModelOutputProperty(field, context.dmmf));
    }
  }
  const scalarsType = isComposite ? scalars : namedType("$Extensions.GetPayloadResult").addGenericArgument(scalars).addGenericArgument(namedType("ExtArgs").subKey("result").subKey(lowerCase(model.name)));
  const payloadTypeDeclaration = typeDeclaration(
    getPayloadName(model.name, false),
    objectType().add(property("name", stringLiteral(model.name))).add(property("objects", objects)).add(property("scalars", scalarsType)).add(property("composites", composites))
  );
  if (!isComposite) {
    payloadTypeDeclaration.addGenericParameter(extArgsParam);
  }
  return moduleExport(payloadTypeDeclaration);
}

// src/generation/TSClient/SelectIncludeOmit.ts
function buildIncludeType({
  modelName,
  typeName = getIncludeName(modelName),
  context,
  fields
}) {
  const type = buildSelectOrIncludeObject(modelName, getIncludeFields(fields, context.dmmf), context);
  return buildExport(typeName, type);
}
function buildOmitType({ modelName, fields, context }) {
  const keysType = unionType(
    fields.filter(
      (field) => field.outputType.location === "scalar" || field.outputType.location === "enumTypes" || context.dmmf.isComposite(field.outputType.type)
    ).map((field) => stringLiteral(field.name))
  );
  const omitType = namedType("$Extensions.GetOmit").addGenericArgument(keysType).addGenericArgument(modelResultExtensionsType(modelName));
  if (context.isPreviewFeatureOn("strictUndefinedChecks")) {
    omitType.addGenericArgument(namedType("$Types.Skip"));
  }
  return buildExport(getOmitName(modelName), omitType);
}
function buildSelectType({
  modelName,
  typeName = getSelectName(modelName),
  fields,
  context
}) {
  const objectType2 = buildSelectOrIncludeObject(modelName, fields, context);
  const selectType = namedType("$Extensions.GetSelect").addGenericArgument(objectType2).addGenericArgument(modelResultExtensionsType(modelName));
  return buildExport(typeName, selectType);
}
function modelResultExtensionsType(modelName) {
  return extArgsParam.toArgument().subKey("result").subKey(lowerCase(modelName));
}
function buildScalarSelectType({ modelName, fields, context }) {
  const object = buildSelectOrIncludeObject(
    modelName,
    fields.filter((field) => field.outputType.location === "scalar" || field.outputType.location === "enumTypes"),
    context
  );
  return moduleExport(typeDeclaration(`${getSelectName(modelName)}Scalar`, object));
}
function buildSelectOrIncludeObject(modelName, fields, context) {
  const objectType2 = objectType();
  for (const field of fields) {
    const fieldType = unionType(booleanType);
    if (field.outputType.location === "outputObjectTypes") {
      const subSelectType = namedType(getFieldArgName(field, modelName));
      subSelectType.addGenericArgument(extArgsParam.toArgument());
      fieldType.addVariant(subSelectType);
    }
    objectType2.add(property(field.name, appendSkipType(context, fieldType)).optional());
  }
  return objectType2;
}
function buildExport(typeName, type) {
  const declaration = typeDeclaration(typeName, type);
  return moduleExport(declaration.addGenericParameter(extArgsParam));
}
function getIncludeFields(fields, dmmf) {
  return fields.filter((field) => {
    if (field.outputType.location !== "outputObjectTypes") {
      return false;
    }
    return !dmmf.isComposite(field.outputType.type);
  });
}

// src/generation/TSClient/utils/getModelActions.ts
function getModelActions(dmmf, name) {
  const mapping = dmmf.mappingsMap[name] ?? { model: name, plural: `${name}s` };
  const mappingKeys = Object.keys(mapping).filter(
    (key) => key !== "model" && key !== "plural" && mapping[key]
  );
  if ("aggregate" in mapping) {
    mappingKeys.push("count");
  }
  return mappingKeys;
}

// src/generation/TSClient/Model.ts
var Model = class {
  constructor(model, context) {
    this.model = model;
    this.context = context;
    this.dmmf = context.dmmf;
    this.type = this.context.dmmf.outputTypeMap.model[model.name];
    this.createManyAndReturnType = this.context.dmmf.outputTypeMap.model[getCreateManyAndReturnOutputType(model.name)];
    this.mapping = this.context.dmmf.mappings.modelOperations.find((m) => m.model === model.name);
  }
  get argsTypes() {
    const argsTypes = [];
    for (const action of Object.keys(DMMF.ModelAction)) {
      const fieldName = this.rootFieldNameForAction(action);
      if (!fieldName) {
        continue;
      }
      const field = this.dmmf.rootFieldMap[fieldName];
      if (!field) {
        throw new Error(`Oops this must not happen. Could not find field ${fieldName} on either Query or Mutation`);
      }
      if (action === "updateMany" || action === "deleteMany" || action === "createMany" || action === "findRaw" || action === "aggregateRaw") {
        argsTypes.push(
          new ArgsTypeBuilder(this.type, this.context, action).addSchemaArgs(field.args).createExport()
        );
      } else if (action === "createManyAndReturn") {
        const args = new ArgsTypeBuilder(this.type, this.context, action).addSelectArg(getSelectCreateManyAndReturnName(this.type.name)).addOmitArg().addSchemaArgs(field.args);
        if (this.createManyAndReturnType) {
          args.addIncludeArgIfHasRelations(
            getIncludeCreateManyAndReturnName(this.model.name),
            this.createManyAndReturnType
          );
        }
        argsTypes.push(args.createExport());
      } else if (action !== "groupBy" && action !== "aggregate") {
        argsTypes.push(
          new ArgsTypeBuilder(this.type, this.context, action).addSelectArg().addOmitArg().addIncludeArgIfHasRelations().addSchemaArgs(field.args).createExport()
        );
      }
    }
    for (const field of this.type.fields) {
      if (!field.args.length) {
        continue;
      }
      const fieldOutput = this.dmmf.resolveOutputObjectType(field.outputType);
      if (!fieldOutput) {
        continue;
      }
      argsTypes.push(
        new ArgsTypeBuilder(fieldOutput, this.context).addSelectArg().addOmitArg().addIncludeArgIfHasRelations().addSchemaArgs(field.args).setGeneratedName(getModelFieldArgsName(field, this.model.name)).setComment(`${this.model.name}.${field.name}`).createExport()
      );
    }
    argsTypes.push(
      new ArgsTypeBuilder(this.type, this.context).addSelectArg().addOmitArg().addIncludeArgIfHasRelations().createExport()
    );
    return argsTypes;
  }
  rootFieldNameForAction(action) {
    return this.mapping?.[action];
  }
  getGroupByTypes() {
    const { model, mapping } = this;
    const groupByType = this.dmmf.outputTypeMap.prisma[getGroupByName(model.name)];
    if (!groupByType) {
      throw new Error(`Could not get group by type for model ${model.name}`);
    }
    const groupByRootField = this.dmmf.rootFieldMap[mapping.groupBy];
    if (!groupByRootField) {
      throw new Error(`Could not find groupBy root field for model ${model.name}. Mapping: ${mapping?.groupBy}`);
    }
    const groupByArgsName = getGroupByArgsName(model.name);
    this.context.defaultArgsAliases.registerArgName(groupByArgsName);
    return `


export type ${groupByArgsName}<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
${(0, import_indent_string3.default)(
      groupByRootField.args.map((arg) => {
        const updatedArg = { ...arg, comment: getArgFieldJSDoc(this.type, DMMF.ModelAction.groupBy, arg) };
        return new InputField(updatedArg, this.context).toTS();
      }).concat(
        groupByType.fields.filter((f) => f.outputType.location === "outputObjectTypes").map((f) => {
          if (f.outputType.location === "outputObjectTypes") {
            return `${f.name}?: ${getAggregateInputType(f.outputType.type)}${f.name === "_count" ? " | true" : ""}`;
          }
          return "";
        })
      ).join("\n"),
      TAB_SIZE
    )}
}

${stringify(buildOutputType(groupByType))}

type ${getGroupByPayloadName(model.name)}<T extends ${groupByArgsName}> = Prisma.PrismaPromise<
  Array<
    PickEnumerable<${groupByType.name}, T['by']> &
      {
        [P in ((keyof T) & (keyof ${groupByType.name}))]: P extends '_count'
          ? T[P] extends boolean
            ? number
            : GetScalarType<T[P], ${groupByType.name}[P]>
          : GetScalarType<T[P], ${groupByType.name}[P]>
      }
    >
  >
`;
  }
  getAggregationTypes() {
    const { model, mapping } = this;
    let aggregateType = this.dmmf.outputTypeMap.prisma[getAggregateName(model.name)];
    if (!aggregateType) {
      throw new Error(`Could not get aggregate type "${getAggregateName(model.name)}" for "${model.name}"`);
    }
    aggregateType = klona(aggregateType);
    const aggregateRootField = this.dmmf.rootFieldMap[mapping.aggregate];
    if (!aggregateRootField) {
      throw new Error(`Could not find aggregate root field for model ${model.name}. Mapping: ${mapping?.aggregate}`);
    }
    const aggregateTypes = [aggregateType];
    const avgType = this.dmmf.outputTypeMap.prisma[getAvgAggregateName(model.name)];
    const sumType = this.dmmf.outputTypeMap.prisma[getSumAggregateName(model.name)];
    const minType = this.dmmf.outputTypeMap.prisma[getMinAggregateName(model.name)];
    const maxType = this.dmmf.outputTypeMap.prisma[getMaxAggregateName(model.name)];
    const countType = this.dmmf.outputTypeMap.prisma[getCountAggregateOutputName(model.name)];
    if (avgType) {
      aggregateTypes.push(avgType);
    }
    if (sumType) {
      aggregateTypes.push(sumType);
    }
    if (minType) {
      aggregateTypes.push(minType);
    }
    if (maxType) {
      aggregateTypes.push(maxType);
    }
    if (countType) {
      aggregateTypes.push(countType);
    }
    const aggregateArgsName = getAggregateArgsName(model.name);
    this.context.defaultArgsAliases.registerArgName(aggregateArgsName);
    const aggregateName = getAggregateName(model.name);
    return `${aggregateTypes.map(buildOutputType).map((type) => stringify(type)).join("\n\n")}

${aggregateTypes.length > 1 ? aggregateTypes.slice(1).map((type) => {
      const newType = {
        name: getAggregateInputType(type.name),
        constraints: {
          maxNumFields: null,
          minNumFields: null
        },
        fields: type.fields.map((field) => ({
          ...field,
          name: field.name,
          isNullable: false,
          isRequired: false,
          inputTypes: [
            {
              isList: false,
              location: "scalar",
              type: "true"
            }
          ]
        }))
      };
      return new InputType(newType, this.context).toTS();
    }).join("\n") : ""}

export type ${aggregateArgsName}<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
${(0, import_indent_string3.default)(
      aggregateRootField.args.map((arg) => {
        const updatedArg = { ...arg, comment: getArgFieldJSDoc(this.type, DMMF.ModelAction.aggregate, arg) };
        return new InputField(updatedArg, this.context).toTS();
      }).concat(
        aggregateType.fields.map((f) => {
          let data = "";
          const comment = getArgFieldJSDoc(this.type, DMMF.ModelAction.aggregate, f.name);
          data += comment ? wrapComment(comment) + "\n" : "";
          if (f.name === "_count" || f.name === "count") {
            data += `${f.name}?: true | ${getCountAggregateInputName(model.name)}`;
          } else {
            data += `${f.name}?: ${getAggregateInputType(f.outputType.type)}`;
          }
          return data;
        })
      ).join("\n"),
      TAB_SIZE
    )}
}

export type ${getAggregateGetName(model.name)}<T extends ${getAggregateArgsName(model.name)}> = {
      [P in keyof T & keyof ${aggregateName}]: P extends '_count' | 'count'
    ? T[P] extends true
      ? number
      : GetScalarType<T[P], ${aggregateName}[P]>
    : GetScalarType<T[P], ${aggregateName}[P]>
}`;
  }
  toTSWithoutNamespace() {
    const { model } = this;
    const docLines = model.documentation ?? "";
    const modelLine = `Model ${model.name}
`;
    const docs = `${modelLine}${docLines}`;
    const modelTypeExport = moduleExport(
      typeDeclaration(
        model.name,
        namedType(`$Result.DefaultSelection`).addGenericArgument(namedType(getPayloadName(model.name)))
      )
    ).setDocComment(docComment(docs));
    return stringify(modelTypeExport);
  }
  toTS() {
    const { model } = this;
    const isComposite = this.dmmf.isComposite(model.name);
    const omitType = this.context.isPreviewFeatureOn("omitApi") ? stringify(buildOmitType({ modelName: this.model.name, context: this.context, fields: this.type.fields }), {
      newLine: "leading"
    }) : "";
    const hasRelationField = model.fields.some((f) => f.kind === "object");
    const includeType = hasRelationField ? stringify(
      buildIncludeType({ modelName: this.model.name, context: this.context, fields: this.type.fields }),
      {
        newLine: "leading"
      }
    ) : "";
    const createManyAndReturnIncludeType = hasRelationField && this.createManyAndReturnType ? stringify(
      buildIncludeType({
        typeName: getIncludeCreateManyAndReturnName(this.model.name),
        modelName: this.model.name,
        context: this.context,
        fields: this.createManyAndReturnType.fields
      }),
      {
        newLine: "leading"
      }
    ) : "";
    return `
/**
 * Model ${model.name}
 */

${!isComposite ? this.getAggregationTypes() : ""}

${!isComposite ? this.getGroupByTypes() : ""}

${stringify(buildSelectType({ modelName: this.model.name, fields: this.type.fields, context: this.context }))}
${this.createManyAndReturnType ? stringify(
      buildSelectType({
        modelName: this.model.name,
        fields: this.createManyAndReturnType.fields,
        context: this.context,
        typeName: getSelectCreateManyAndReturnName(this.model.name)
      }),
      { newLine: "leading" }
    ) : ""}
${stringify(buildScalarSelectType({ modelName: this.model.name, fields: this.type.fields, context: this.context }), {
      newLine: "leading"
    })}
${omitType}${includeType}${createManyAndReturnIncludeType}

${stringify(buildModelPayload(this.model, this.context), { newLine: "none" })}

type ${model.name}GetPayload<S extends boolean | null | undefined | ${getModelArgName(
      model.name
    )}> = $Result.GetResult<${getPayloadName(model.name)}, S>

${isComposite ? "" : new ModelDelegate(this.type, this.context).toTS()}

${new ModelFieldRefs(this.type).toTS()}

// Custom InputTypes
${this.argsTypes.map((type) => stringify(type)).join("\n\n")}
`;
  }
};
var ModelDelegate = class {
  constructor(outputType, context) {
    this.outputType = outputType;
    this.context = context;
  }
  /**
   * Returns all available non-aggregate or group actions
   * Includes both dmmf and client-only actions
   *
   * @param availableActions
   * @returns
   */
  getNonAggregateActions(availableActions) {
    const actions = availableActions.filter(
      (key) => key !== DMMF.ModelAction.aggregate && key !== DMMF.ModelAction.groupBy && key !== DMMF.ModelAction.count
    );
    return actions;
  }
  toTS() {
    const { name } = this.outputType;
    const { dmmf } = this.context;
    const mapping = dmmf.mappingsMap[name] ?? { model: name, plural: `${name}s` };
    const modelOrType = dmmf.typeAndModelMap[name];
    const availableActions = getModelActions(dmmf, name);
    const nonAggregateActions = this.getNonAggregateActions(availableActions);
    const groupByArgsName = getGroupByArgsName(name);
    const countArgsName = getModelArgName(name, DMMF.ModelAction.count);
    this.context.defaultArgsAliases.registerArgName(countArgsName);
    const genericDelegateParams = [extArgsParam];
    const excludedArgsForCount = ["select", "include", "distinct"];
    if (this.context.isPreviewFeatureOn("omitApi")) {
      excludedArgsForCount.push("omit");
      genericDelegateParams.push(genericParameter("ClientOptions").default(objectType()));
    }
    if (this.context.isPreviewFeatureOn("relationJoins")) {
      excludedArgsForCount.push("relationLoadStrategy");
    }
    const excludedArgsForCountType = excludedArgsForCount.map((name2) => `'${name2}'`).join(" | ");
    return `${availableActions.includes(DMMF.ModelAction.aggregate) ? `type ${countArgsName}<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = 
  Omit<${getModelArgName(name, DMMF.ModelAction.findMany)}, ${excludedArgsForCountType}> & {
    select?: ${getCountAggregateInputName(name)} | true
  }
` : ""}
export interface ${name}Delegate<${genericDelegateParams.map((param) => stringify(param)).join(", ")}> {
${(0, import_indent_string3.default)(`[K: symbol]: { types: Prisma.TypeMap<ExtArgs>['model']['${name}'], meta: { name: '${name}' } }`, TAB_SIZE)}
${nonAggregateActions.map((action) => {
      const method2 = buildModelDelegateMethod(name, action, this.context);
      return stringify(method2, { indentLevel: 1, newLine: "trailing" });
    }).join("\n")}

${availableActions.includes(DMMF.ModelAction.aggregate) ? `${(0, import_indent_string3.default)(getMethodJSDoc(DMMF.ModelAction.count, mapping, modelOrType), TAB_SIZE)}
  count<T extends ${countArgsName}>(
    args?: Subset<T, ${countArgsName}>,
  ): Prisma.PrismaPromise<
    T extends $Utils.Record<'select', any>
      ? T['select'] extends true
        ? number
        : GetScalarType<T['select'], ${getCountAggregateOutputName(name)}>
      : number
  >
` : ""}
${availableActions.includes(DMMF.ModelAction.aggregate) ? `${(0, import_indent_string3.default)(getMethodJSDoc(DMMF.ModelAction.aggregate, mapping, modelOrType), TAB_SIZE)}
  aggregate<T extends ${getAggregateArgsName(name)}>(args: Subset<T, ${getAggregateArgsName(
      name
    )}>): Prisma.PrismaPromise<${getAggregateGetName(name)}<T>>
` : ""}
${availableActions.includes(DMMF.ModelAction.groupBy) ? `${(0, import_indent_string3.default)(getMethodJSDoc(DMMF.ModelAction.groupBy, mapping, modelOrType), TAB_SIZE)}
  groupBy<
    T extends ${groupByArgsName},
    HasSelectOrTake extends Or<
      Extends<'skip', Keys<T>>,
      Extends<'take', Keys<T>>
    >,
    OrderByArg extends True extends HasSelectOrTake
      ? { orderBy: ${groupByArgsName}['orderBy'] }
      : { orderBy?: ${groupByArgsName}['orderBy'] },
    OrderFields extends ExcludeUnderscoreKeys<Keys<MaybeTupleToUnion<T['orderBy']>>>,
    ByFields extends MaybeTupleToUnion<T['by']>,
    ByValid extends Has<ByFields, OrderFields>,
    HavingFields extends GetHavingFields<T['having']>,
    HavingValid extends Has<ByFields, HavingFields>,
    ByEmpty extends T['by'] extends never[] ? True : False,
    InputErrors extends ByEmpty extends True
    ? \`Error: "by" must not be empty.\`
    : HavingValid extends False
    ? {
        [P in HavingFields]: P extends ByFields
          ? never
          : P extends string
          ? \`Error: Field "\${P}" used in "having" needs to be provided in "by".\`
          : [
              Error,
              'Field ',
              P,
              \` in "having" needs to be provided in "by"\`,
            ]
      }[HavingFields]
    : 'take' extends Keys<T>
    ? 'orderBy' extends Keys<T>
      ? ByValid extends True
        ? {}
        : {
            [P in OrderFields]: P extends ByFields
              ? never
              : \`Error: Field "\${P}" in "orderBy" needs to be provided in "by"\`
          }[OrderFields]
      : 'Error: If you provide "take", you also need to provide "orderBy"'
    : 'skip' extends Keys<T>
    ? 'orderBy' extends Keys<T>
      ? ByValid extends True
        ? {}
        : {
            [P in OrderFields]: P extends ByFields
              ? never
              : \`Error: Field "\${P}" in "orderBy" needs to be provided in "by"\`
          }[OrderFields]
      : 'Error: If you provide "skip", you also need to provide "orderBy"'
    : ByValid extends True
    ? {}
    : {
        [P in OrderFields]: P extends ByFields
          ? never
          : \`Error: Field "\${P}" in "orderBy" needs to be provided in "by"\`
      }[OrderFields]
  >(args: SubsetIntersection<T, ${groupByArgsName}, OrderByArg> & InputErrors): {} extends InputErrors ? ${getGroupByPayloadName(
      name
    )}<T> : Prisma.PrismaPromise<InputErrors>` : ""}
/**
 * Fields of the ${name} model
 */
readonly fields: ${getFieldRefsTypeName(name)};
}

${stringify(buildFluentWrapperDefinition(name, this.outputType, this.context))}
`;
  }
};
function buildModelDelegateMethod(modelName, actionName, context) {
  const mapping = context.dmmf.mappingsMap[modelName] ?? { model: modelName, plural: `${modelName}s` };
  const modelOrType = context.dmmf.typeAndModelMap[modelName];
  const method2 = method(actionName).setDocComment(docComment(getMethodJSDocBody(actionName, mapping, modelOrType))).addParameter(getNonAggregateMethodArgs(modelName, actionName)).setReturnType(getReturnType({ modelName, actionName, context }));
  const generic = getNonAggregateMethodGenericParam(modelName, actionName);
  if (generic) {
    method2.addGenericParameter(generic);
  }
  return method2;
}
function getNonAggregateMethodArgs(modelName, actionName) {
  getReturnType;
  const makeParameter = (type2) => parameter("args", type2);
  if (actionName === DMMF.ModelAction.count) {
    const type2 = omit(
      namedType(getModelArgName(modelName, DMMF.ModelAction.findMany)),
      unionType(stringLiteral("select")).addVariant(stringLiteral("include")).addVariant(stringLiteral("distinct"))
    );
    return makeParameter(type2).optional();
  }
  if (actionName === DMMF.ModelAction.findRaw || actionName === DMMF.ModelAction.aggregateRaw) {
    return makeParameter(namedType(getModelArgName(modelName, actionName))).optional();
  }
  const type = namedType("SelectSubset").addGenericArgument(namedType("T")).addGenericArgument(
    namedType(getModelArgName(modelName, actionName)).addGenericArgument(extArgsParam.toArgument())
  );
  const param = makeParameter(type);
  if (actionName === DMMF.ModelAction.findMany || actionName === DMMF.ModelAction.findFirst || actionName === DMMF.ModelAction.deleteMany || actionName === DMMF.ModelAction.createMany || actionName === DMMF.ModelAction.createManyAndReturn || actionName === DMMF.ModelAction.findFirstOrThrow) {
    param.optional();
  }
  return param;
}
function getNonAggregateMethodGenericParam(modelName, actionName) {
  if (actionName === DMMF.ModelAction.count || actionName === DMMF.ModelAction.findRaw || actionName === DMMF.ModelAction.aggregateRaw) {
    return null;
  }
  const arg = genericParameter("T");
  if (actionName === DMMF.ModelAction.aggregate) {
    return arg.extends(namedType(getAggregateArgsName(modelName)));
  }
  return arg.extends(namedType(getModelArgName(modelName, actionName)));
}
function getReturnType({
  modelName,
  actionName,
  context,
  isChaining = false,
  isNullable = false
}) {
  if (actionName === DMMF.ModelAction.count) {
    return promise(numberType);
  }
  if (actionName === DMMF.ModelAction.aggregate) {
    return promise(namedType(getAggregateGetName(modelName)).addGenericArgument(namedType("T")));
  }
  if (actionName === DMMF.ModelAction.findRaw || actionName === DMMF.ModelAction.aggregateRaw) {
    return prismaPromise(namedType("JsonObject"));
  }
  if (actionName === DMMF.ModelAction.deleteMany || actionName === DMMF.ModelAction.updateMany || actionName === DMMF.ModelAction.createMany) {
    return prismaPromise(namedType("BatchPayload"));
  }
  const isList = actionName === DMMF.ModelAction.findMany || actionName === DMMF.ModelAction.createManyAndReturn;
  if (isList) {
    let result = getResultType(modelName, actionName, context);
    if (isChaining) {
      result = unionType(result).addVariant(namedType("Null"));
    }
    return prismaPromise(result);
  }
  if (isChaining && actionName === DMMF.ModelAction.findUniqueOrThrow) {
    const nullType2 = isNullable ? nullType : namedType("Null");
    const result = unionType(getResultType(modelName, actionName, context)).addVariant(nullType2);
    return getFluentWrapper(modelName, context, result, nullType2);
  }
  if (actionName === DMMF.ModelAction.findFirst || actionName === DMMF.ModelAction.findUnique) {
    const result = unionType(getResultType(modelName, actionName, context)).addVariant(nullType);
    return getFluentWrapper(modelName, context, result, nullType);
  }
  return getFluentWrapper(modelName, context, getResultType(modelName, actionName, context));
}
function getFluentWrapper(modelName, context, resultType, nullType2 = neverType) {
  const result = namedType(fluentWrapperName(modelName)).addGenericArgument(resultType).addGenericArgument(nullType2).addGenericArgument(extArgsParam.toArgument());
  if (context.isPreviewFeatureOn("omitApi")) {
    result.addGenericArgument(namedType("ClientOptions"));
  }
  return result;
}
function getResultType(modelName, actionName, context) {
  const result = namedType("$Result.GetResult").addGenericArgument(namedType(getPayloadName(modelName)).addGenericArgument(extArgsParam.toArgument())).addGenericArgument(namedType("T")).addGenericArgument(stringLiteral(actionName));
  if (context.isPreviewFeatureOn("omitApi")) {
    result.addGenericArgument(namedType("ClientOptions"));
  }
  return result;
}
function buildFluentWrapperDefinition(modelName, outputType, context) {
  const definition = interfaceDeclaration(fluentWrapperName(modelName));
  definition.addGenericParameter(genericParameter("T")).addGenericParameter(genericParameter("Null").default(neverType)).addGenericParameter(extArgsParam).extends(prismaPromise(namedType("T")));
  if (context.isPreviewFeatureOn("omitApi")) {
    definition.addGenericParameter(genericParameter("ClientOptions").default(objectType()));
  }
  definition.add(property(toStringTag, stringLiteral("PrismaPromise")).readonly());
  definition.addMultiple(
    outputType.fields.filter(
      (field) => field.outputType.location === "outputObjectTypes" && !context.dmmf.isComposite(field.outputType.type) && field.name !== "_count"
    ).map((field) => {
      const fieldArgType = namedType(getFieldArgName(field, modelName)).addGenericArgument(extArgsParam.toArgument());
      const argsParam = genericParameter("T").extends(fieldArgType).default(objectType());
      return method(field.name).addGenericParameter(argsParam).addParameter(parameter("args", subset(argsParam.toArgument(), fieldArgType)).optional()).setReturnType(
        getReturnType({
          modelName: field.outputType.type,
          actionName: field.outputType.isList ? DMMF.ModelAction.findMany : DMMF.ModelAction.findUniqueOrThrow,
          isChaining: true,
          context,
          isNullable: field.isNullable
        })
      );
    })
  );
  definition.add(
    method("then").setDocComment(
      docComment`
          Attaches callbacks for the resolution and/or rejection of the Promise.
          @param onfulfilled The callback to execute when the Promise is resolved.
          @param onrejected The callback to execute when the Promise is rejected.
          @returns A Promise for the completion of which ever callback is executed.
        `
    ).addGenericParameter(genericParameter("TResult1").default(namedType("T"))).addGenericParameter(genericParameter("TResult2").default(neverType)).addParameter(promiseCallback("onfulfilled", parameter("value", namedType("T")), namedType("TResult1"))).addParameter(promiseCallback("onrejected", parameter("reason", anyType), namedType("TResult2"))).setReturnType(promise(unionType([namedType("TResult1"), namedType("TResult2")])))
  );
  definition.add(
    method("catch").setDocComment(
      docComment`
          Attaches a callback for only the rejection of the Promise.
          @param onrejected The callback to execute when the Promise is rejected.
          @returns A Promise for the completion of the callback.
        `
    ).addGenericParameter(genericParameter("TResult").default(neverType)).addParameter(promiseCallback("onrejected", parameter("reason", anyType), namedType("TResult"))).setReturnType(promise(unionType([namedType("T"), namedType("TResult")])))
  );
  definition.add(
    method("finally").setDocComment(
      docComment`
          Attaches a callback that is invoked when the Promise is settled (fulfilled or rejected). The
          resolved value cannot be modified from the callback.
          @param onfinally The callback to execute when the Promise is settled (fulfilled or rejected).
          @returns A Promise for the completion of the callback.
      `
    ).addParameter(
      parameter("onfinally", unionType([functionType(), undefinedType, nullType])).optional()
    ).setReturnType(promise(namedType("T")))
  );
  return moduleExport(definition).setDocComment(docComment`
      The delegate class that acts as a "Promise-like" for ${modelName}.
      Why is this prefixed with \`Prisma__\`?
      Because we want to prevent naming conflicts as mentioned in
      https://github.com/prisma/prisma-client-js/issues/707
    `);
}
function promiseCallback(name, callbackParam, returnType) {
  return parameter(
    name,
    unionType([
      functionType().addParameter(callbackParam).setReturnType(typeOrPromiseLike(returnType)),
      undefinedType,
      nullType
    ])
  ).optional();
}
function typeOrPromiseLike(type) {
  return unionType([type, namedType("PromiseLike").addGenericArgument(type)]);
}
function subset(arg, baseType) {
  return namedType("Subset").addGenericArgument(arg).addGenericArgument(baseType);
}
function fluentWrapperName(modelName) {
  return `Prisma__${modelName}Client`;
}

// src/generation/TSClient/TSClient.ts
var import_ci_info = __toESM(require_ci_info());
var import_crypto = __toESM(require("crypto"));
var import_indent_string8 = __toESM(require_indent_string());
var import_path4 = __toESM(require("path"));

// src/generation/dmmf.ts
var DMMFHelper = class {
  constructor(document) {
    this.document = document;
  }
  get compositeNames() {
    return this._compositeNames ??= new Set(this.datamodel.types.map((t) => t.name));
  }
  get inputTypesByName() {
    return this._inputTypesByName ??= this.buildInputTypesMap();
  }
  get typeAndModelMap() {
    return this._typeAndModelMap ??= this.buildTypeModelMap();
  }
  get mappingsMap() {
    return this._mappingsMap ??= this.buildMappingsMap();
  }
  get outputTypeMap() {
    return this._outputTypeMap ??= this.buildMergedOutputTypeMap();
  }
  get rootFieldMap() {
    return this._rootFieldMap ??= this.buildRootFieldMap();
  }
  get datamodel() {
    return this.document.datamodel;
  }
  get mappings() {
    return this.document.mappings;
  }
  get schema() {
    return this.document.schema;
  }
  get inputObjectTypes() {
    return this.schema.inputObjectTypes;
  }
  get outputObjectTypes() {
    return this.schema.outputObjectTypes;
  }
  isComposite(modelOrTypeName) {
    return this.compositeNames.has(modelOrTypeName);
  }
  getOtherOperationNames() {
    return [
      Object.values(this.mappings.otherOperations.write),
      Object.values(this.mappings.otherOperations.read)
    ].flat();
  }
  hasEnumInNamespace(enumName, namespace2) {
    return this.schema.enumTypes[namespace2]?.find((schemaEnum) => schemaEnum.name === enumName) !== void 0;
  }
  resolveInputObjectType(ref) {
    return this.inputTypesByName.get(fullyQualifiedName(ref.type, ref.namespace));
  }
  resolveOutputObjectType(ref) {
    if (ref.location !== "outputObjectTypes") {
      return void 0;
    }
    return this.outputObjectTypes[ref.namespace ?? "prisma"].find((outputObject) => outputObject.name === ref.type);
  }
  buildModelMap() {
    return keyBy(this.datamodel.models, "name");
  }
  buildTypeMap() {
    return keyBy(this.datamodel.types, "name");
  }
  buildTypeModelMap() {
    return { ...this.buildTypeMap(), ...this.buildModelMap() };
  }
  buildMappingsMap() {
    return keyBy(this.mappings.modelOperations, "model");
  }
  buildMergedOutputTypeMap() {
    if (!this.schema.outputObjectTypes.prisma) {
      return {
        model: keyBy(this.schema.outputObjectTypes.model, "name"),
        prisma: keyBy([], "name")
      };
    }
    return {
      model: keyBy(this.schema.outputObjectTypes.model, "name"),
      prisma: keyBy(this.schema.outputObjectTypes.prisma, "name")
    };
  }
  buildRootFieldMap() {
    return {
      ...keyBy(this.outputTypeMap.prisma.Query.fields, "name"),
      ...keyBy(this.outputTypeMap.prisma.Mutation.fields, "name")
    };
  }
  buildInputTypesMap() {
    const result = /* @__PURE__ */ new Map();
    for (const type of this.inputObjectTypes.prisma) {
      result.set(fullyQualifiedName(type.name, "prisma"), type);
    }
    if (!this.inputObjectTypes.model) {
      return result;
    }
    for (const type of this.inputObjectTypes.model) {
      result.set(fullyQualifiedName(type.name, "model"), type);
    }
    return result;
  }
};
function fullyQualifiedName(typeName, namespace2) {
  if (namespace2) {
    return `${namespace2}.${typeName}`;
  }
  return typeName;
}

// src/generation/Cache.ts
var Cache = class {
  constructor() {
    this._map = /* @__PURE__ */ new Map();
  }
  get(key) {
    return this._map.get(key)?.value;
  }
  set(key, value) {
    this._map.set(key, { value });
  }
  getOrCreate(key, create) {
    const cached = this._map.get(key);
    if (cached) {
      return cached.value;
    }
    const value = create();
    this.set(key, value);
    return value;
  }
};

// src/generation/GenericsArgsInfo.ts
var GenericArgsInfo = class {
  constructor(_dmmf) {
    this._dmmf = _dmmf;
    this._cache = new Cache();
  }
  /**
   * Determines if arg types need generic <$PrismaModel> argument added.
   * Essentially, performs breadth-first search for any fieldRefTypes that
   * do not have corresponding `meta.source` defined.
   *
   * @param type
   * @returns
   */
  typeNeedsGenericModelArg(topLevelType) {
    return this._cache.getOrCreate(topLevelType, () => {
      const toVisit = [{ type: topLevelType }];
      const visited = /* @__PURE__ */ new Set();
      let item;
      while (item = toVisit.shift()) {
        const { type: currentType } = item;
        const cached = this._cache.get(currentType);
        if (cached === true) {
          this._cacheResultsForTree(item);
          return true;
        }
        if (cached === false) {
          continue;
        }
        if (visited.has(currentType)) {
          continue;
        }
        if (currentType.meta?.source) {
          this._cache.set(currentType, false);
          continue;
        }
        visited.add(currentType);
        for (const field of currentType.fields) {
          for (const fieldType of field.inputTypes) {
            if (fieldType.location === "fieldRefTypes") {
              this._cacheResultsForTree(item);
              return true;
            }
            const inputObject = this._dmmf.resolveInputObjectType(fieldType);
            if (inputObject) {
              toVisit.push({ type: inputObject, parent: item });
            }
          }
        }
      }
      for (const visitedType of visited) {
        this._cache.set(visitedType, false);
      }
      return false;
    });
  }
  typeRefNeedsGenericModelArg(ref) {
    if (ref.location === "fieldRefTypes") {
      return true;
    }
    const inputType = this._dmmf.resolveInputObjectType(ref);
    if (!inputType) {
      return false;
    }
    return this.typeNeedsGenericModelArg(inputType);
  }
  _cacheResultsForTree(item) {
    let currentItem = item;
    while (currentItem) {
      this._cache.set(currentItem.type, true);
      currentItem = currentItem.parent;
    }
  }
};

// src/generation/utils/buildInjectableEdgeEnv.ts
function buildInjectableEdgeEnv(edge, datasources) {
  if (edge === true) {
    return declareInjectableEdgeEnv(datasources);
  }
  return ``;
}
function declareInjectableEdgeEnv(datasources) {
  const injectableEdgeEnv = { parsed: {} };
  const envVarNames = getSelectedEnvVarNames(datasources);
  for (const envVarName of envVarNames) {
    injectableEdgeEnv.parsed[envVarName] = getRuntimeEdgeEnvVar(envVarName);
  }
  const injectableEdgeEnvJson = JSON.stringify(injectableEdgeEnv, null, 2);
  const injectableEdgeEnvCode = injectableEdgeEnvJson.replace(/"/g, "");
  return `
config.injectableEdgeEnv = () => (${injectableEdgeEnvCode})`;
}
function getSelectedEnvVarNames(datasources) {
  return datasources.reduce((acc, datasource) => {
    if (datasource.url.fromEnvVar) {
      return [...acc, datasource.url.fromEnvVar];
    }
    return acc;
  }, []);
}
function getRuntimeEdgeEnvVar(envVarName) {
  const cfwEnv = `typeof globalThis !== 'undefined' && globalThis['${envVarName}']`;
  const nodeOrVercelEnv = `typeof process !== 'undefined' && process.env && process.env.${envVarName}`;
  return `${cfwEnv} || ${nodeOrVercelEnv} || undefined`;
}

// src/generation/utils/buildDebugInitialization.ts
function buildDebugInitialization(edge) {
  if (!edge) {
    return "";
  }
  const debugVar = getRuntimeEdgeEnvVar("DEBUG");
  return `if (${debugVar}) {
  Debug.enable(${debugVar})
}
`;
}

// src/generation/utils/buildDirname.ts
function buildDirname(edge, relativeOutdir) {
  if (edge === true) {
    return buildDirnameDefault();
  }
  return buildDirnameFind(relativeOutdir);
}
function buildDirnameFind(relativeOutdir) {
  return `
const fs = require('fs')

config.dirname = __dirname
if (!fs.existsSync(path.join(__dirname, 'schema.prisma'))) {
  const alternativePaths = [
    ${JSON.stringify(pathToPosix(relativeOutdir))},
    ${JSON.stringify(pathToPosix(relativeOutdir).split("/").slice(1).join("/"))},
  ]
  
  const alternativePath = alternativePaths.find((altPath) => {
    return fs.existsSync(path.join(process.cwd(), altPath, 'schema.prisma'))
  }) ?? alternativePaths[0]

  config.dirname = path.join(process.cwd(), alternativePath)
  config.isBundled = true
}`;
}
function buildDirnameDefault() {
  return `config.dirname = '/'`;
}

// src/runtime/core/runtimeDataModel.ts
function dmmfToRuntimeDataModel(dmmfDataModel) {
  return {
    models: buildMapForRuntime(dmmfDataModel.models),
    enums: buildMapForRuntime(dmmfDataModel.enums),
    types: buildMapForRuntime(dmmfDataModel.types)
  };
}
function pruneRuntimeDataModel({ models }) {
  const prunedModels = {};
  for (const modelName of Object.keys(models)) {
    prunedModels[modelName] = { fields: [], dbName: models[modelName].dbName };
    for (const { name, kind, type, relationName, dbName } of models[modelName].fields) {
      prunedModels[modelName].fields.push({ name, kind, type, relationName, dbName });
    }
  }
  return { models: prunedModels, enums: {}, types: {} };
}
function buildMapForRuntime(list) {
  const result = {};
  for (const { name, ...rest } of list) {
    result[name] = rest;
  }
  return result;
}

// src/generation/utils/buildDMMF.ts
function buildRuntimeDataModel(datamodel, runtimeNameJs) {
  const runtimeDataModel = dmmfToRuntimeDataModel(datamodel);
  let prunedDataModel;
  if (runtimeNameJs === "wasm") {
    prunedDataModel = pruneRuntimeDataModel(runtimeDataModel);
  } else {
    prunedDataModel = runtimeDataModel;
  }
  const datamodelString = escapeJson(JSON.stringify(prunedDataModel));
  return `
config.runtimeDataModel = JSON.parse(${JSON.stringify(datamodelString)})
defineDmmfProperty(exports.Prisma, config.runtimeDataModel)`;
}

// src/generation/utils/buildGetQueryEngineWasmModule.ts
function buildQueryEngineWasmModule(wasm, copyEngine, runtimeNameJs) {
  if (copyEngine && runtimeNameJs === "library" && process.env.PRISMA_CLIENT_FORCE_WASM) {
    return `config.engineWasm = {
      getRuntime: () => require('./query_engine_bg.js'),
      getQueryEngineWasmModule: async () => {
        const queryEngineWasmFilePath = require('path').join(config.dirname, 'query_engine_bg.wasm')
        const queryEngineWasmFileBytes = require('fs').readFileSync(queryEngineWasmFilePath)
      
        return new WebAssembly.Module(queryEngineWasmFileBytes)
      }
    }`;
  }
  if (copyEngine && wasm === true) {
    return `config.engineWasm = {
  getRuntime: () => require('./query_engine_bg.js'),
  getQueryEngineWasmModule: async () => {
    const loader = (await import('#wasm-engine-loader')).default
    const engine = (await loader).default
    return engine 
  }
}`;
  }
  return `config.engineWasm = undefined`;
}

// src/generation/utils/buildNFTAnnotations.ts
var import_path3 = __toESM(require("path"));

// ../../helpers/blaze/map.ts
function mapList(object, mapper) {
  const mapped = new Array(object.length);
  for (let i = 0; i < object.length; ++i) {
    mapped[i] = mapper(object[i], i);
  }
  return mapped;
}
function mapObject(object, mapper) {
  const mapped = {};
  const keys = Object.keys(object);
  for (let i = 0; i < keys.length; ++i) {
    mapped[i] = mapper(object[keys[i]], keys[i]);
  }
  return mapped;
}
var map = (object, mapper) => {
  return Array.isArray(object) ? mapList(object, mapper) : mapObject(object, mapper);
};

// src/generation/utils/buildNFTAnnotations.ts
function buildNFTAnnotations(noEngine, engineType, binaryTargets, relativeOutdir) {
  if (noEngine === true) return "";
  if (binaryTargets === void 0) {
    return "";
  }
  if (process.env.NETLIFY) {
    const isNodeMajor20OrUp = parseInt(process.versions.node.split(".")[0]) >= 20;
    const awsRuntimeVersion = parseAWSNodejsRuntimeEnvVarVersion();
    const isRuntimeEnvVar20OrUp = awsRuntimeVersion && awsRuntimeVersion >= 20;
    const isRuntimeEnvVar18OrDown = awsRuntimeVersion && awsRuntimeVersion <= 18;
    if ((isNodeMajor20OrUp || isRuntimeEnvVar20OrUp) && !isRuntimeEnvVar18OrDown) {
      binaryTargets = ["rhel-openssl-3.0.x"];
    } else {
      binaryTargets = ["rhel-openssl-1.0.x"];
    }
  }
  const engineAnnotations = map(binaryTargets, (binaryTarget) => {
    const engineFilename = getQueryEngineFilename(engineType, binaryTarget);
    return engineFilename ? buildNFTAnnotation(engineFilename, relativeOutdir) : "";
  }).join("\n");
  const schemaAnnotations = buildNFTAnnotation("schema.prisma", relativeOutdir);
  return `${engineAnnotations}${schemaAnnotations}`;
}
function getQueryEngineFilename(engineType, binaryTarget) {
  if (engineType === "library" /* Library */) {
    return getNodeAPIName(binaryTarget, "fs");
  }
  if (engineType === "binary" /* Binary */) {
    return `query-engine-${binaryTarget}`;
  }
  return void 0;
}
function buildNFTAnnotation(fileName, relativeOutdir) {
  const relativeFilePath = import_path3.default.join(relativeOutdir, fileName);
  return `
// file annotations for bundling tools to include these files
path.join(__dirname, ${JSON.stringify(pathToPosix(fileName))});
path.join(process.cwd(), ${JSON.stringify(pathToPosix(relativeFilePath))})`;
}

// src/generation/utils/buildRequirePath.ts
function buildRequirePath(edge) {
  if (edge === true) return "";
  return `
  const path = require('path')`;
}

// src/generation/utils/buildWarnEnvConflicts.ts
function buildWarnEnvConflicts(edge, runtimeBase, runtimeNameJs) {
  if (edge === true) return "";
  return `
const { warnEnvConflicts } = require('${runtimeBase}/${runtimeNameJs}.js')

warnEnvConflicts({
    rootEnvPath: config.relativeEnvPaths.rootEnvPath && path.resolve(config.dirname, config.relativeEnvPaths.rootEnvPath),
    schemaEnvPath: config.relativeEnvPaths.schemaEnvPath && path.resolve(config.dirname, config.relativeEnvPaths.schemaEnvPath)
})`;
}

// src/generation/TSClient/common.ts
var import_indent_string4 = __toESM(require_indent_string());
var commonCodeJS = ({
  runtimeBase,
  runtimeNameJs,
  browser,
  clientVersion: clientVersion2,
  engineVersion,
  generator,
  deno
}) => `${deno ? "const exports = {}" : ""}
Object.defineProperty(exports, "__esModule", { value: true });
${deno ? `
import {
  PrismaClientKnownRequestError,
  PrismaClientUnknownRequestError,
  PrismaClientRustPanicError,
  PrismaClientInitializationError,
  PrismaClientValidationError,
  NotFoundError,
  getPrismaClient,
  sqltag,
  empty,
  join,
  raw,
  Decimal,
  Debug,
  objectEnumValues,
  makeStrictEnum,
  Extensions,
  defineDmmfProperty,
  Public,
  getRuntime,
  skip
} from '${runtimeBase}/${runtimeNameJs}.js'` : browser ? `
const {
  Decimal,
  objectEnumValues,
  makeStrictEnum,
  Public,
  getRuntime,
  skip
} = require('${runtimeBase}/${runtimeNameJs}.js')
` : `
const {
  PrismaClientKnownRequestError,
  PrismaClientUnknownRequestError,
  PrismaClientRustPanicError,
  PrismaClientInitializationError,
  PrismaClientValidationError,
  NotFoundError,
  getPrismaClient,
  sqltag,
  empty,
  join,
  raw,
  skip,
  Decimal,
  Debug,
  objectEnumValues,
  makeStrictEnum,
  Extensions,
  warnOnce,
  defineDmmfProperty,
  Public,
  getRuntime
} = require('${runtimeBase}/${runtimeNameJs}.js')
`}

const Prisma = {}

exports.Prisma = Prisma
exports.$Enums = {}

/**
 * Prisma Client JS version: ${clientVersion2}
 * Query Engine version: ${engineVersion}
 */
Prisma.prismaVersion = {
  client: "${clientVersion2}",
  engine: "${engineVersion}"
}

Prisma.PrismaClientKnownRequestError = ${notSupportOnBrowser("PrismaClientKnownRequestError", browser)};
Prisma.PrismaClientUnknownRequestError = ${notSupportOnBrowser("PrismaClientUnknownRequestError", browser)}
Prisma.PrismaClientRustPanicError = ${notSupportOnBrowser("PrismaClientRustPanicError", browser)}
Prisma.PrismaClientInitializationError = ${notSupportOnBrowser("PrismaClientInitializationError", browser)}
Prisma.PrismaClientValidationError = ${notSupportOnBrowser("PrismaClientValidationError", browser)}
Prisma.NotFoundError = ${notSupportOnBrowser("NotFoundError", browser)}
Prisma.Decimal = Decimal

/**
 * Re-export of sql-template-tag
 */
Prisma.sql = ${notSupportOnBrowser("sqltag", browser)}
Prisma.empty = ${notSupportOnBrowser("empty", browser)}
Prisma.join = ${notSupportOnBrowser("join", browser)}
Prisma.raw = ${notSupportOnBrowser("raw", browser)}
Prisma.validator = Public.validator

/**
* Extensions
*/
Prisma.getExtensionContext = ${notSupportOnBrowser("Extensions.getExtensionContext", browser)}
Prisma.defineExtension = ${notSupportOnBrowser("Extensions.defineExtension", browser)}

/**
 * Shorthand utilities for JSON filtering
 */
Prisma.DbNull = objectEnumValues.instances.DbNull
Prisma.JsonNull = objectEnumValues.instances.JsonNull
Prisma.AnyNull = objectEnumValues.instances.AnyNull

Prisma.NullTypes = {
  DbNull: objectEnumValues.classes.DbNull,
  JsonNull: objectEnumValues.classes.JsonNull,
  AnyNull: objectEnumValues.classes.AnyNull
}

${buildPrismaSkipJs(generator.previewFeatures)}
`;
var notSupportOnBrowser = (fnc, browser) => {
  if (browser) {
    return `() => {
  const runtimeName = getRuntime().prettyName;
  throw new Error(\`${fnc} is unable to run in this browser environment, or has been bundled for the browser (running in \${runtimeName}).
In case this error is unexpected for you, please report it in https://pris.ly/prisma-prisma-bug-report\`,
)}`;
  }
  return fnc;
};
var commonCodeTS = ({
  runtimeBase,
  runtimeNameTs,
  clientVersion: clientVersion2,
  engineVersion,
  generator
}) => ({
  tsWithoutNamespace: () => `import * as runtime from '${runtimeBase}/${runtimeNameTs}';
import $Types = runtime.Types // general types
import $Public = runtime.Types.Public
import $Utils = runtime.Types.Utils
import $Extensions = runtime.Types.Extensions
import $Result = runtime.Types.Result

export type PrismaPromise<T> = $Public.PrismaPromise<T>
`,
  ts: () => `export import DMMF = runtime.DMMF

export type PrismaPromise<T> = $Public.PrismaPromise<T>

/**
 * Validator
 */
export import validator = runtime.Public.validator

/**
 * Prisma Errors
 */
export import PrismaClientKnownRequestError = runtime.PrismaClientKnownRequestError
export import PrismaClientUnknownRequestError = runtime.PrismaClientUnknownRequestError
export import PrismaClientRustPanicError = runtime.PrismaClientRustPanicError
export import PrismaClientInitializationError = runtime.PrismaClientInitializationError
export import PrismaClientValidationError = runtime.PrismaClientValidationError
export import NotFoundError = runtime.NotFoundError

/**
 * Re-export of sql-template-tag
 */
export import sql = runtime.sqltag
export import empty = runtime.empty
export import join = runtime.join
export import raw = runtime.raw
export import Sql = runtime.Sql

${buildPrismaSkipTs(generator.previewFeatures)}

/**
 * Decimal.js
 */
export import Decimal = runtime.Decimal

export type DecimalJsLike = runtime.DecimalJsLike

/**
 * Metrics 
 */
export type Metrics = runtime.Metrics
export type Metric<T> = runtime.Metric<T>
export type MetricHistogram = runtime.MetricHistogram
export type MetricHistogramBucket = runtime.MetricHistogramBucket

/**
* Extensions
*/
export import Extension = $Extensions.UserArgs
export import getExtensionContext = runtime.Extensions.getExtensionContext
export import Args = $Public.Args
export import Payload = $Public.Payload
export import Result = $Public.Result
export import Exact = $Public.Exact

/**
 * Prisma Client JS version: ${clientVersion2}
 * Query Engine version: ${engineVersion}
 */
export type PrismaVersion = {
  client: string
}

export const prismaVersion: PrismaVersion 

/**
 * Utility Types
 */


export import JsonObject = runtime.JsonObject
export import JsonArray = runtime.JsonArray
export import JsonValue = runtime.JsonValue
export import InputJsonObject = runtime.InputJsonObject
export import InputJsonArray = runtime.InputJsonArray
export import InputJsonValue = runtime.InputJsonValue

/**
 * Types of the values used to represent different kinds of \`null\` values when working with JSON fields.
 * 
 * @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
 */
namespace NullTypes {
${buildNullClass("DbNull")}

${buildNullClass("JsonNull")}

${buildNullClass("AnyNull")}
}

/**
 * Helper for filtering JSON entries that have \`null\` on the database (empty on the db)
 * 
 * @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
 */
export const DbNull: NullTypes.DbNull

/**
 * Helper for filtering JSON entries that have JSON \`null\` values (not empty on the db)
 * 
 * @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
 */
export const JsonNull: NullTypes.JsonNull

/**
 * Helper for filtering JSON entries that are \`Prisma.DbNull\` or \`Prisma.JsonNull\`
 * 
 * @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
 */
export const AnyNull: NullTypes.AnyNull

type SelectAndInclude = {
  select: any
  include: any
}

type SelectAndOmit = {
  select: any
  omit: any
}

/**
 * Get the type of the value, that the Promise holds.
 */
export type PromiseType<T extends PromiseLike<any>> = T extends PromiseLike<infer U> ? U : T;

/**
 * Get the return type of a function which returns a Promise.
 */
export type PromiseReturnType<T extends (...args: any) => $Utils.JsPromise<any>> = PromiseType<ReturnType<T>>

/**
 * From T, pick a set of properties whose keys are in the union K
 */
type Prisma__Pick<T, K extends keyof T> = {
    [P in K]: T[P];
};


export type Enumerable<T> = T | Array<T>;

export type RequiredKeys<T> = {
  [K in keyof T]-?: {} extends Prisma__Pick<T, K> ? never : K
}[keyof T]

export type TruthyKeys<T> = keyof {
  [K in keyof T as T[K] extends false | undefined | null ? never : K]: K
}

export type TrueKeys<T> = TruthyKeys<Prisma__Pick<T, RequiredKeys<T>>>

/**
 * Subset
 * @desc From \`T\` pick properties that exist in \`U\`. Simple version of Intersection
 */
export type Subset<T, U> = {
  [key in keyof T]: key extends keyof U ? T[key] : never;
};

/**
 * SelectSubset
 * @desc From \`T\` pick properties that exist in \`U\`. Simple version of Intersection.
 * Additionally, it validates, if both select and include are present. If the case, it errors.
 */
export type SelectSubset<T, U> = {
  [key in keyof T]: key extends keyof U ? T[key] : never
} &
  (T extends SelectAndInclude
    ? 'Please either choose \`select\` or \`include\`.'
    : T extends SelectAndOmit
      ? 'Please either choose \`select\` or \`omit\`.'
      : {})

/**
 * Subset + Intersection
 * @desc From \`T\` pick properties that exist in \`U\` and intersect \`K\`
 */
export type SubsetIntersection<T, U, K> = {
  [key in keyof T]: key extends keyof U ? T[key] : never
} &
  K

type Without<T, U> = { [P in Exclude<keyof T, keyof U>]?: never };

/**
 * XOR is needed to have a real mutually exclusive union type
 * https://stackoverflow.com/questions/42123407/does-typescript-support-mutually-exclusive-types
 */
type XOR<T, U> =
  T extends object ?
  U extends object ?
    (Without<T, U> & U) | (Without<U, T> & T)
  : U : T


/**
 * Is T a Record?
 */
type IsObject<T extends any> = T extends Array<any>
? False
: T extends Date
? False
: T extends Uint8Array
? False
: T extends BigInt
? False
: T extends object
? True
: False


/**
 * If it's T[], return T
 */
export type UnEnumerate<T extends unknown> = T extends Array<infer U> ? U : T

/**
 * From ts-toolbelt
 */

type __Either<O extends object, K extends Key> = Omit<O, K> &
  {
    // Merge all but K
    [P in K]: Prisma__Pick<O, P & keyof O> // With K possibilities
  }[K]

type EitherStrict<O extends object, K extends Key> = Strict<__Either<O, K>>

type EitherLoose<O extends object, K extends Key> = ComputeRaw<__Either<O, K>>

type _Either<
  O extends object,
  K extends Key,
  strict extends Boolean
> = {
  1: EitherStrict<O, K>
  0: EitherLoose<O, K>
}[strict]

type Either<
  O extends object,
  K extends Key,
  strict extends Boolean = 1
> = O extends unknown ? _Either<O, K, strict> : never

export type Union = any

type PatchUndefined<O extends object, O1 extends object> = {
  [K in keyof O]: O[K] extends undefined ? At<O1, K> : O[K]
} & {}

/** Helper Types for "Merge" **/
export type IntersectOf<U extends Union> = (
  U extends unknown ? (k: U) => void : never
) extends (k: infer I) => void
  ? I
  : never

export type Overwrite<O extends object, O1 extends object> = {
    [K in keyof O]: K extends keyof O1 ? O1[K] : O[K];
} & {};

type _Merge<U extends object> = IntersectOf<Overwrite<U, {
    [K in keyof U]-?: At<U, K>;
}>>;

type Key = string | number | symbol;
type AtBasic<O extends object, K extends Key> = K extends keyof O ? O[K] : never;
type AtStrict<O extends object, K extends Key> = O[K & keyof O];
type AtLoose<O extends object, K extends Key> = O extends unknown ? AtStrict<O, K> : never;
export type At<O extends object, K extends Key, strict extends Boolean = 1> = {
    1: AtStrict<O, K>;
    0: AtLoose<O, K>;
}[strict];

export type ComputeRaw<A extends any> = A extends Function ? A : {
  [K in keyof A]: A[K];
} & {};

export type OptionalFlat<O> = {
  [K in keyof O]?: O[K];
} & {};

type _Record<K extends keyof any, T> = {
  [P in K]: T;
};

// cause typescript not to expand types and preserve names
type NoExpand<T> = T extends unknown ? T : never;

// this type assumes the passed object is entirely optional
type AtLeast<O extends object, K extends string> = NoExpand<
  O extends unknown
  ? | (K extends keyof O ? { [P in K]: O[P] } & O : O)
    | {[P in keyof O as P extends K ? K : never]-?: O[P]} & O
  : never>;

type _Strict<U, _U = U> = U extends unknown ? U & OptionalFlat<_Record<Exclude<Keys<_U>, keyof U>, never>> : never;

export type Strict<U extends object> = ComputeRaw<_Strict<U>>;
/** End Helper Types for "Merge" **/

export type Merge<U extends object> = ComputeRaw<_Merge<Strict<U>>>;

/**
A [[Boolean]]
*/
export type Boolean = True | False

// /**
// 1
// */
export type True = 1

/**
0
*/
export type False = 0

export type Not<B extends Boolean> = {
  0: 1
  1: 0
}[B]

export type Extends<A1 extends any, A2 extends any> = [A1] extends [never]
  ? 0 // anything \`never\` is false
  : A1 extends A2
  ? 1
  : 0

export type Has<U extends Union, U1 extends Union> = Not<
  Extends<Exclude<U1, U>, U1>
>

export type Or<B1 extends Boolean, B2 extends Boolean> = {
  0: {
    0: 0
    1: 1
  }
  1: {
    0: 1
    1: 1
  }
}[B1][B2]

export type Keys<U extends Union> = U extends unknown ? keyof U : never

type Cast<A, B> = A extends B ? A : B;

export const type: unique symbol;



/**
 * Used by group by
 */

export type GetScalarType<T, O> = O extends object ? {
  [P in keyof T]: P extends keyof O
    ? O[P]
    : never
} : never

type FieldPaths<
  T,
  U = Omit<T, '_avg' | '_sum' | '_count' | '_min' | '_max'>
> = IsObject<T> extends True ? U : T

type GetHavingFields<T> = {
  [K in keyof T]: Or<
    Or<Extends<'OR', K>, Extends<'AND', K>>,
    Extends<'NOT', K>
  > extends True
    ? // infer is only needed to not hit TS limit
      // based on the brilliant idea of Pierre-Antoine Mills
      // https://github.com/microsoft/TypeScript/issues/30188#issuecomment-478938437
      T[K] extends infer TK
      ? GetHavingFields<UnEnumerate<TK> extends object ? Merge<UnEnumerate<TK>> : never>
      : never
    : {} extends FieldPaths<T[K]>
    ? never
    : K
}[keyof T]

/**
 * Convert tuple to union
 */
type _TupleToUnion<T> = T extends (infer E)[] ? E : never
type TupleToUnion<K extends readonly any[]> = _TupleToUnion<K>
type MaybeTupleToUnion<T> = T extends any[] ? TupleToUnion<T> : T

/**
 * Like \`Pick\`, but additionally can also accept an array of keys
 */
type PickEnumerable<T, K extends Enumerable<keyof T> | keyof T> = Prisma__Pick<T, MaybeTupleToUnion<K>>

/**
 * Exclude all keys with underscores
 */
type ExcludeUnderscoreKeys<T extends string> = T extends \`_\${string}\` ? never : T


export type FieldRef<Model, FieldType> = runtime.FieldRef<Model, FieldType>

type FieldRefInputType<Model, FieldType> = Model extends never ? never : FieldRef<Model, FieldType>

`
});
function buildNullClass(name) {
  const source = `/**
* Type of \`Prisma.${name}\`.
* 
* You cannot use other instances of this class. Please use the \`Prisma.${name}\` value.
* 
* @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
*/
class ${name} {
  private ${name}: never
  private constructor()
}`;
  return (0, import_indent_string4.default)(source, TAB_SIZE);
}
function buildPrismaSkipTs(previewFeatures) {
  if (previewFeatures.includes("strictUndefinedChecks")) {
    return `
/**
 * Prisma.skip
 */
export import skip = runtime.skip
`;
  }
  return "";
}
function buildPrismaSkipJs(previewFeatures) {
  if (previewFeatures.includes("strictUndefinedChecks")) {
    return `
Prisma.skip = skip
`;
  }
  return "";
}

// src/generation/TSClient/Count.ts
var import_indent_string5 = __toESM(require_indent_string());
var Count = class {
  constructor(type, context) {
    this.type = type;
    this.context = context;
  }
  get argsTypes() {
    const argsTypes = [];
    argsTypes.push(
      new ArgsTypeBuilder(this.type, this.context).addSelectArg().addIncludeArgIfHasRelations().createExport()
    );
    for (const field of this.type.fields) {
      if (field.args.length > 0) {
        argsTypes.push(
          new ArgsTypeBuilder(this.type, this.context).addSchemaArgs(field.args).setGeneratedName(getCountArgsType(this.type.name, field.name)).createExport()
        );
      }
    }
    return argsTypes;
  }
  toTS() {
    const { type } = this;
    const { name } = type;
    const outputType = buildOutputType(type);
    return `
/**
 * Count Type ${name}
 */

${stringify(outputType)}

export type ${getSelectName(name)}<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
${(0, import_indent_string5.default)(
      type.fields.map((field) => {
        const types = ["boolean"];
        if (field.outputType.location === "outputObjectTypes") {
          types.push(getFieldArgName(field, this.type.name));
        }
        if (field.args.length > 0) {
          types.push(getCountArgsType(name, field.name));
        }
        return `${field.name}?: ${types.join(" | ")}`;
      }).join("\n"),
      TAB_SIZE
    )}
}

// Custom InputTypes
${this.argsTypes.map((typeExport) => stringify(typeExport)).join("\n\n")}
`;
  }
};
function getCountArgsType(typeName, fieldName) {
  return `${typeName}Count${capitalize2(fieldName)}Args`;
}

// src/generation/TSClient/DefaultArgsAliases.ts
var DefaultArgsAliases = class {
  constructor() {
    this.existingArgTypes = /* @__PURE__ */ new Set();
    this.possibleAliases = [];
  }
  addPossibleAlias(newName, legacyName) {
    this.possibleAliases.push({ newName, legacyName });
  }
  registerArgName(name) {
    this.existingArgTypes.add(name);
  }
  generateAliases() {
    const aliases = [];
    for (const { newName, legacyName } of this.possibleAliases) {
      if (this.existingArgTypes.has(legacyName)) {
        continue;
      }
      aliases.push(
        stringify(
          moduleExport(
            typeDeclaration(legacyName, namedType(newName).addGenericArgument(extArgsParam.toArgument())).addGenericParameter(extArgsParam)
          ).setDocComment(docComment(`@deprecated Use ${newName} instead`)),
          { indentLevel: 1 }
        )
      );
    }
    return aliases.join("\n");
  }
};

// src/generation/TSClient/FieldRefInput.ts
var FieldRefInput = class {
  constructor(type) {
    this.type = type;
  }
  toTS() {
    const allowedTypes = this.getAllowedTypes();
    return `
/**
 * Reference to a field of type ${allowedTypes}
 */
export type ${this.type.name}<$PrismaModel> = FieldRefInputType<$PrismaModel, ${allowedTypes}>
    `;
  }
  getAllowedTypes() {
    return this.type.allowTypes.map(getRefAllowedTypeName).join(" | ");
  }
};

// src/generation/TSClient/GenerateContext.ts
var GenerateContext = class {
  constructor({ dmmf, genericArgsInfo, defaultArgsAliases, generator }) {
    this.dmmf = dmmf;
    this.genericArgsInfo = genericArgsInfo;
    this.defaultArgsAliases = defaultArgsAliases;
    this.generator = generator;
  }
  isPreviewFeatureOn(previewFeature) {
    return this.generator?.previewFeatures?.includes(previewFeature) ?? false;
  }
};

// src/generation/TSClient/PrismaClient.ts
var import_indent_string7 = __toESM(require_indent_string());

// src/generation/utils/runtimeImport.ts
function runtimeImport(name) {
  return name;
}
function runtimeImportedType(name) {
  return namedType(`runtime.${name}`);
}

// src/generation/TSClient/Datasources.ts
var import_indent_string6 = __toESM(require_indent_string());
var Datasources = class {
  constructor(internalDatasources) {
    this.internalDatasources = internalDatasources;
  }
  toTS() {
    const sources = this.internalDatasources;
    return `export type Datasources = {
${(0, import_indent_string6.default)(sources.map((s) => `${s.name}?: Datasource`).join("\n"), 2)}
}`;
  }
};

// src/generation/TSClient/globalOmit.ts
function globalOmitConfig(dmmf) {
  const objectType2 = objectType().addMultiple(
    dmmf.datamodel.models.map((model) => {
      const type = namedType(getOmitName(model.name));
      return property(lowerCase(model.name), type).optional();
    })
  );
  return moduleExport(typeDeclaration("GlobalOmitConfig", objectType2));
}

// src/generation/TSClient/PrismaClient.ts
function clientTypeMapModelsDefinition(context) {
  const meta = objectType();
  const modelNames = context.dmmf.datamodel.models.map((m) => m.name);
  if (modelNames.length === 0) {
    meta.add(property("modelProps", neverType));
  } else {
    meta.add(property("modelProps", unionType(modelNames.map((name) => stringLiteral(lowerCase(name))))));
  }
  const isolationLevel = context.dmmf.hasEnumInNamespace("TransactionIsolationLevel", "prisma") ? namedType("Prisma.TransactionIsolationLevel") : neverType;
  meta.add(property("txIsolationLevel", isolationLevel));
  const model = objectType();
  model.addMultiple(
    modelNames.map((modelName) => {
      const entry = objectType();
      entry.add(
        property("payload", namedType(getPayloadName(modelName)).addGenericArgument(extArgsParam.toArgument()))
      );
      entry.add(property("fields", namedType(`Prisma.${getFieldRefsTypeName(modelName)}`)));
      const actions = getModelActions(context.dmmf, modelName);
      const operations = objectType();
      operations.addMultiple(
        actions.map((action) => {
          const operationType = objectType();
          const argsType = `Prisma.${getModelArgName(modelName, action)}`;
          operationType.add(property("args", namedType(argsType).addGenericArgument(extArgsParam.toArgument())));
          operationType.add(property("result", clientTypeMapModelsResultDefinition(modelName, action)));
          return property(action, operationType);
        })
      );
      entry.add(property("operations", operations));
      return property(modelName, entry);
    })
  );
  return objectType().add(property("meta", meta)).add(property("model", model));
}
function clientTypeMapModelsResultDefinition(modelName, action) {
  if (action === "count")
    return unionType([optional(namedType(getCountAggregateOutputName(modelName))), numberType]);
  if (action === "groupBy") return array(optional(namedType(getGroupByName(modelName))));
  if (action === "aggregate") return optional(namedType(getAggregateName(modelName)));
  if (action === "findRaw") return namedType("JsonObject");
  if (action === "aggregateRaw") return namedType("JsonObject");
  if (action === "deleteMany") return namedType("BatchPayload");
  if (action === "createMany") return namedType("BatchPayload");
  if (action === "createManyAndReturn") return array(payloadToResult(modelName));
  if (action === "updateMany") return namedType("BatchPayload");
  if (action === "findMany") return array(payloadToResult(modelName));
  if (action === "findFirst") return unionType([payloadToResult(modelName), nullType]);
  if (action === "findUnique") return unionType([payloadToResult(modelName), nullType]);
  if (action === "findFirstOrThrow") return payloadToResult(modelName);
  if (action === "findUniqueOrThrow") return payloadToResult(modelName);
  if (action === "create") return payloadToResult(modelName);
  if (action === "update") return payloadToResult(modelName);
  if (action === "upsert") return payloadToResult(modelName);
  if (action === "delete") return payloadToResult(modelName);
  assertNever(action, `Unknown action: ${action}`);
}
function payloadToResult(modelName) {
  return namedType("$Utils.PayloadToResult").addGenericArgument(namedType(getPayloadName(modelName)));
}
function clientTypeMapOthersDefinition(context) {
  const otherOperationsNames = context.dmmf.getOtherOperationNames().flatMap((name) => {
    const results = [`$${name}`];
    if (name === "executeRaw" || name === "queryRaw") {
      results.push(`$${name}Unsafe`);
    }
    if (name === "queryRaw" && context.isPreviewFeatureOn("typedSql")) {
      results.push(`$queryRawTyped`);
    }
    return results;
  });
  const argsResultMap = {
    $executeRaw: { args: "[query: TemplateStringsArray | Prisma.Sql, ...values: any[]]", result: "any" },
    $queryRaw: { args: "[query: TemplateStringsArray | Prisma.Sql, ...values: any[]]", result: "any" },
    $executeRawUnsafe: { args: "[query: string, ...values: any[]]", result: "any" },
    $queryRawUnsafe: { args: "[query: string, ...values: any[]]", result: "any" },
    $runCommandRaw: { args: "Prisma.InputJsonObject", result: "Prisma.JsonObject" },
    $queryRawTyped: { args: "runtime.UnknownTypedSql", result: "Prisma.JsonObject" }
  };
  return `{
  other: {
    payload: any
    operations: {${otherOperationsNames.reduce((acc, action) => {
    return `${acc}
      ${action}: {
        args: ${argsResultMap[action].args},
        result: ${argsResultMap[action].result}
      }`;
  }, "")}
    }
  }
}`;
}
function clientTypeMapDefinition(context) {
  const typeMap = `${stringify(clientTypeMapModelsDefinition(context))} & ${clientTypeMapOthersDefinition(context)}`;
  return `
interface TypeMapCb extends $Utils.Fn<{extArgs: $Extensions.InternalArgs, clientOptions: PrismaClientOptions }, $Utils.Record<string, any>> {
  returns: Prisma.TypeMap<this['params']['extArgs'], this['params']['clientOptions']>
}

export type TypeMap<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, ClientOptions = {}> = ${typeMap}`;
}
function clientExtensionsDefinitions(context) {
  const typeMap = clientTypeMapDefinition(context);
  const define2 = moduleExport(
    constDeclaration(
      "defineExtension",
      namedType("$Extensions.ExtendsHook").addGenericArgument(stringLiteral("define")).addGenericArgument(namedType("Prisma.TypeMapCb")).addGenericArgument(namedType("$Extensions.DefaultArgs"))
    )
  );
  return [typeMap, stringify(define2)].join("\n");
}
function extendsPropertyDefinition(context) {
  const extendsDefinition = namedType("$Extensions.ExtendsHook").addGenericArgument(stringLiteral("extends")).addGenericArgument(namedType("Prisma.TypeMapCb")).addGenericArgument(namedType("ExtArgs"));
  if (context.isPreviewFeatureOn("omitApi")) {
    extendsDefinition.addGenericArgument(
      namedType("$Utils.Call").addGenericArgument(namedType("Prisma.TypeMapCb")).addGenericArgument(objectType().add(property("extArgs", namedType("ExtArgs"))))
    ).addGenericArgument(namedType("ClientOptions"));
  }
  return stringify(property("$extends", extendsDefinition), { indentLevel: 1 });
}
function batchingTransactionDefinition(context) {
  const method2 = method("$transaction").setDocComment(
    docComment`
        Allows the running of a sequence of read/write operations that are guaranteed to either succeed or fail as a whole.
        @example
        \`\`\`
        const [george, bob, alice] = await prisma.$transaction([
          prisma.user.create({ data: { name: 'George' } }),
          prisma.user.create({ data: { name: 'Bob' } }),
          prisma.user.create({ data: { name: 'Alice' } }),
        ])
        \`\`\`

        Read more in our [docs](https://www.prisma.io/docs/concepts/components/prisma-client/transactions).
      `
  ).addGenericParameter(genericParameter("P").extends(array(prismaPromise(anyType)))).addParameter(parameter("arg", arraySpread(namedType("P")))).setReturnType(promise(namedType("runtime.Types.Utils.UnwrapTuple").addGenericArgument(namedType("P"))));
  if (context.dmmf.hasEnumInNamespace("TransactionIsolationLevel", "prisma")) {
    const options = objectType().formatInline().add(property("isolationLevel", namedType("Prisma.TransactionIsolationLevel")).optional());
    method2.addParameter(parameter("options", options).optional());
  }
  return stringify(method2, { indentLevel: 1, newLine: "leading" });
}
function interactiveTransactionDefinition(context) {
  const options = objectType().formatInline().add(property("maxWait", numberType).optional()).add(property("timeout", numberType).optional());
  if (context.dmmf.hasEnumInNamespace("TransactionIsolationLevel", "prisma")) {
    const isolationLevel = property("isolationLevel", namedType("Prisma.TransactionIsolationLevel")).optional();
    options.add(isolationLevel);
  }
  const returnType = promise(namedType("R"));
  const callbackType = functionType().addParameter(
    parameter("prisma", omit(namedType("PrismaClient"), namedType("runtime.ITXClientDenyList")))
  ).setReturnType(returnType);
  const method2 = method("$transaction").addGenericParameter(genericParameter("R")).addParameter(parameter("fn", callbackType)).addParameter(parameter("options", options).optional()).setReturnType(returnType);
  return stringify(method2, { indentLevel: 1, newLine: "leading" });
}
function queryRawDefinition(context) {
  if (!context.dmmf.mappings.otherOperations.write.includes("queryRaw")) {
    return "";
  }
  return `
  /**
   * Performs a prepared raw query and returns the \`SELECT\` data.
   * @example
   * \`\`\`
   * const result = await prisma.$queryRaw\`SELECT * FROM User WHERE id = \${1} OR email = \${'user@email.com'};\`
   * \`\`\`
   * 
   * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client/raw-database-access).
   */
  $queryRaw<T = unknown>(query: TemplateStringsArray | Prisma.Sql, ...values: any[]): Prisma.PrismaPromise<T>;

  /**
   * Performs a raw query and returns the \`SELECT\` data.
   * Susceptible to SQL injections, see documentation.
   * @example
   * \`\`\`
   * const result = await prisma.$queryRawUnsafe('SELECT * FROM User WHERE id = $1 OR email = $2;', 1, 'user@email.com')
   * \`\`\`
   * 
   * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client/raw-database-access).
   */
  $queryRawUnsafe<T = unknown>(query: string, ...values: any[]): Prisma.PrismaPromise<T>;`;
}
function executeRawDefinition(context) {
  if (!context.dmmf.mappings.otherOperations.write.includes("executeRaw")) {
    return "";
  }
  return `
  /**
   * Executes a prepared raw query and returns the number of affected rows.
   * @example
   * \`\`\`
   * const result = await prisma.$executeRaw\`UPDATE User SET cool = \${true} WHERE email = \${'user@email.com'};\`
   * \`\`\`
   * 
   * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client/raw-database-access).
   */
  $executeRaw<T = unknown>(query: TemplateStringsArray | Prisma.Sql, ...values: any[]): Prisma.PrismaPromise<number>;

  /**
   * Executes a raw query and returns the number of affected rows.
   * Susceptible to SQL injections, see documentation.
   * @example
   * \`\`\`
   * const result = await prisma.$executeRawUnsafe('UPDATE User SET cool = $1 WHERE email = $2 ;', true, 'user@email.com')
   * \`\`\`
   * 
   * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client/raw-database-access).
   */
  $executeRawUnsafe<T = unknown>(query: string, ...values: any[]): Prisma.PrismaPromise<number>;`;
}
function queryRawTypedDefinition(context) {
  if (!context.isPreviewFeatureOn("typedSql")) {
    return "";
  }
  if (!context.dmmf.mappings.otherOperations.write.includes("queryRaw")) {
    return "";
  }
  const param = genericParameter("T");
  const method2 = method("$queryRawTyped").setDocComment(
    docComment`
        Executes a typed SQL query and returns a typed result
        @example
        \`\`\`
        import { myQuery } from '@prisma/client/sql'

        const result = await prisma.$queryRawTyped(myQuery())
        \`\`\`
      `
  ).addGenericParameter(param).addParameter(
    parameter(
      "typedSql",
      runtimeImportedType("TypedSql").addGenericArgument(array(unknownType)).addGenericArgument(param.toArgument())
    )
  ).setReturnType(prismaPromise(array(param.toArgument())));
  return stringify(method2, { indentLevel: 1, newLine: "leading" });
}
function metricDefinition(context) {
  if (!context.isPreviewFeatureOn("metrics")) {
    return "";
  }
  const property2 = property("$metrics", namedType(`runtime.${runtimeImport("MetricsClient")}`)).setDocComment(
    docComment`
        Gives access to the client metrics in json or prometheus format.
        
        @example
        \`\`\`
        const metrics = await prisma.$metrics.json()
        // or
        const metrics = await prisma.$metrics.prometheus()
        \`\`\`
    `
  ).readonly();
  return stringify(property2, { indentLevel: 1, newLine: "leading" });
}
function runCommandRawDefinition(context) {
  if (!context.dmmf.mappings.otherOperations.write.includes("runCommandRaw")) {
    return "";
  }
  const method2 = method("$runCommandRaw").addParameter(parameter("command", namedType("Prisma.InputJsonObject"))).setReturnType(prismaPromise(namedType("Prisma.JsonObject"))).setDocComment(docComment`
      Executes a raw MongoDB command and returns the result of it.
      @example
      \`\`\`
      const user = await prisma.$runCommandRaw({
        aggregate: 'User',
        pipeline: [{ $match: { name: 'Bob' } }, { $project: { email: true, _id: false } }],
        explain: false,
      })
      \`\`\`
   
      Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client/raw-database-access).
    `);
  return stringify(method2, { indentLevel: 1, newLine: "leading" });
}
function applyPendingMigrationsDefinition() {
  if (this.runtimeNameTs !== "react-native") {
    return null;
  }
  const method2 = method("$applyPendingMigrations").setReturnType(promise(voidType)).setDocComment(
    docComment`Tries to apply pending migrations one by one. If a migration fails to apply, the function will stop and throw an error. You are responsible for informing the user and possibly blocking the app as we cannot guarantee the state of the database.`
  );
  return stringify(method2, { indentLevel: 1, newLine: "leading" });
}
function eventRegistrationMethodDeclaration(runtimeNameTs) {
  if (runtimeNameTs === "binary.js") {
    return `$on<V extends (U | 'beforeExit')>(eventType: V, callback: (event: V extends 'query' ? Prisma.QueryEvent : V extends 'beforeExit' ? () => $Utils.JsPromise<void> : Prisma.LogEvent) => void): void;`;
  } else {
    return `$on<V extends U>(eventType: V, callback: (event: V extends 'query' ? Prisma.QueryEvent : Prisma.LogEvent) => void): void;`;
  }
}
var PrismaClientClass = class {
  constructor(context, internalDatasources, outputDir, runtimeNameTs, browser) {
    this.context = context;
    this.internalDatasources = internalDatasources;
    this.outputDir = outputDir;
    this.runtimeNameTs = runtimeNameTs;
    this.browser = browser;
  }
  get jsDoc() {
    const { dmmf } = this.context;
    let example;
    if (dmmf.mappings.modelOperations.length) {
      example = dmmf.mappings.modelOperations[0];
    } else {
      example = {
        model: "User",
        plural: "users"
      };
    }
    return `/**
 * ##  Prisma Client \u02B2\u02E2
 * 
 * Type-safe database client for TypeScript & Node.js
 * @example
 * \`\`\`
 * const prisma = new PrismaClient()
 * // Fetch zero or more ${capitalize2(example.plural)}
 * const ${lowerCase(example.plural)} = await prisma.${lowerCase(example.model)}.findMany()
 * \`\`\`
 *
 * 
 * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client).
 */`;
  }
  toTSWithoutNamespace() {
    const { dmmf } = this.context;
    return `${this.jsDoc}
export class PrismaClient<
  ClientOptions extends Prisma.PrismaClientOptions = Prisma.PrismaClientOptions,
  U = 'log' extends keyof ClientOptions ? ClientOptions['log'] extends Array<Prisma.LogLevel | Prisma.LogDefinition> ? Prisma.GetEvents<ClientOptions['log']> : never : never,
  ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs
> {
  [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['other'] }

  ${(0, import_indent_string7.default)(this.jsDoc, TAB_SIZE)}

  constructor(optionsArg ?: Prisma.Subset<ClientOptions, Prisma.PrismaClientOptions>);
  ${eventRegistrationMethodDeclaration(this.runtimeNameTs)}

  /**
   * Connect with the database
   */
  $connect(): $Utils.JsPromise<void>;

  /**
   * Disconnect from the database
   */
  $disconnect(): $Utils.JsPromise<void>;

  /**
   * Add a middleware
   * @deprecated since 4.16.0. For new code, prefer client extensions instead.
   * @see https://pris.ly/d/extensions
   */
  $use(cb: Prisma.Middleware): void

${[
      executeRawDefinition(this.context),
      queryRawDefinition(this.context),
      queryRawTypedDefinition(this.context),
      batchingTransactionDefinition(this.context),
      interactiveTransactionDefinition(this.context),
      runCommandRawDefinition(this.context),
      metricDefinition(this.context),
      applyPendingMigrationsDefinition.bind(this)(),
      extendsPropertyDefinition(this.context)
    ].filter((d) => d !== null).join("\n").trim()}

    ${(0, import_indent_string7.default)(
      dmmf.mappings.modelOperations.filter((m) => m.findMany).map((m) => {
        let methodName = lowerCase(m.model);
        if (methodName === "constructor") {
          methodName = '["constructor"]';
        }
        const generics = ["ExtArgs"];
        if (this.context.isPreviewFeatureOn("omitApi")) {
          generics.push("ClientOptions");
        }
        return `/**
 * \`prisma.${methodName}\`: Exposes CRUD operations for the **${m.model}** model.
  * Example usage:
  * \`\`\`ts
  * // Fetch zero or more ${capitalize2(m.plural)}
  * const ${lowerCase(m.plural)} = await prisma.${methodName}.findMany()
  * \`\`\`
  */
get ${methodName}(): Prisma.${m.model}Delegate<${generics.join(", ")}>;`;
      }).join("\n\n"),
      2
    )}
}`;
  }
  toTS() {
    const clientOptions = this.buildClientOptions();
    const isOmitEnabled = this.context.isPreviewFeatureOn("omitApi");
    return `${new Datasources(this.internalDatasources).toTS()}
${clientExtensionsDefinitions(this.context)}
export type DefaultPrismaClient = PrismaClient
export type ErrorFormat = 'pretty' | 'colorless' | 'minimal'
${stringify(moduleExport(clientOptions))}
${isOmitEnabled ? stringify(globalOmitConfig(this.context.dmmf)) : ""}

/* Types for Logging */
export type LogLevel = 'info' | 'query' | 'warn' | 'error'
export type LogDefinition = {
  level: LogLevel
  emit: 'stdout' | 'event'
}

export type GetLogType<T extends LogLevel | LogDefinition> = T extends LogDefinition ? T['emit'] extends 'event' ? T['level'] : never : never
export type GetEvents<T extends any> = T extends Array<LogLevel | LogDefinition> ?
  GetLogType<T[0]> | GetLogType<T[1]> | GetLogType<T[2]> | GetLogType<T[3]>
  : never

export type QueryEvent = {
  timestamp: Date
  query: string
  params: string
  duration: number
  target: string
}

export type LogEvent = {
  timestamp: Date
  message: string
  target: string
}
/* End Types for Logging */


export type PrismaAction =
  | 'findUnique'
  | 'findUniqueOrThrow'
  | 'findMany'
  | 'findFirst'
  | 'findFirstOrThrow'
  | 'create'
  | 'createMany'
  | 'createManyAndReturn'
  | 'update'
  | 'updateMany'
  | 'upsert'
  | 'delete'
  | 'deleteMany'
  | 'executeRaw'
  | 'queryRaw'
  | 'aggregate'
  | 'count'
  | 'runCommandRaw'
  | 'findRaw'
  | 'groupBy'

/**
 * These options are being passed into the middleware as "params"
 */
export type MiddlewareParams = {
  model?: ModelName
  action: PrismaAction
  args: any
  dataPath: string[]
  runInTransaction: boolean
}

/**
 * The \`T\` type makes sure, that the \`return proceed\` is not forgotten in the middleware implementation
 */
export type Middleware<T = any> = (
  params: MiddlewareParams,
  next: (params: MiddlewareParams) => $Utils.JsPromise<T>,
) => $Utils.JsPromise<T>

// tested in getLogLevel.test.ts
export function getLogLevel(log: Array<LogLevel | LogDefinition>): LogLevel | undefined;

/**
 * \`PrismaClient\` proxy available in interactive transactions.
 */
export type TransactionClient = Omit<Prisma.DefaultPrismaClient, runtime.ITXClientDenyList>
`;
  }
  buildClientOptions() {
    const clientOptions = interfaceDeclaration("PrismaClientOptions").add(
      property("datasources", namedType("Datasources")).optional().setDocComment(docComment("Overwrites the datasource url from your schema.prisma file"))
    ).add(
      property("datasourceUrl", stringType).optional().setDocComment(docComment("Overwrites the datasource url from your schema.prisma file"))
    ).add(
      property("errorFormat", namedType("ErrorFormat")).optional().setDocComment(docComment('@default "colorless"'))
    ).add(
      property("log", array(unionType([namedType("LogLevel"), namedType("LogDefinition")]))).optional().setDocComment(docComment`
             @example
             \`\`\`
             // Defaults to stdout
             log: ['query', 'info', 'warn', 'error']
            
             // Emit as events
             log: [
               { emit: 'stdout', level: 'query' },
               { emit: 'stdout', level: 'info' },
               { emit: 'stdout', level: 'warn' }
               { emit: 'stdout', level: 'error' }
             ]
             \`\`\`
             Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client/logging#the-log-option).
          `)
    );
    const transactionOptions = objectType().add(property("maxWait", numberType).optional()).add(property("timeout", numberType).optional());
    if (this.context.dmmf.hasEnumInNamespace("TransactionIsolationLevel", "prisma")) {
      transactionOptions.add(property("isolationLevel", namedType("Prisma.TransactionIsolationLevel")).optional());
    }
    clientOptions.add(
      property("transactionOptions", transactionOptions).optional().setDocComment(docComment`
             The default values for transactionOptions
             maxWait ?= 2000
             timeout ?= 5000
          `)
    );
    if (this.runtimeNameTs === "library.js" && this.context.isPreviewFeatureOn("driverAdapters")) {
      clientOptions.add(
        property("adapter", unionType([namedType("runtime.DriverAdapter"), namedType("null")])).optional().setDocComment(
          docComment("Instance of a Driver Adapter, e.g., like one provided by `@prisma/adapter-planetscale`")
        )
      );
    }
    if (this.context.isPreviewFeatureOn("omitApi")) {
      clientOptions.add(
        property("omit", namedType("Prisma.GlobalOmitConfig")).optional().setDocComment(docComment`
            Global configuration for omitting model fields by default.

            @example
            \`\`\`
            const prisma = new PrismaClient({
              omit: {
                user: {
                  password: true
                }
              }
            })
            \`\`\`
          `)
      );
    }
    return clientOptions;
  }
};

// src/generation/TSClient/TSClient.ts
var TSClient = class {
  constructor(options) {
    this.options = options;
    this.dmmf = new DMMFHelper(options.dmmf);
    this.genericsInfo = new GenericArgsInfo(this.dmmf);
  }
  toJS() {
    const {
      edge,
      wasm,
      binaryPaths,
      generator,
      outputDir,
      datamodel: inlineSchema,
      runtimeBase,
      runtimeNameJs,
      datasources,
      deno,
      copyEngine = true,
      reusedJs,
      envPaths
    } = this.options;
    if (reusedJs) {
      return `module.exports = { ...require('${reusedJs}') }`;
    }
    const relativeEnvPaths = {
      rootEnvPath: envPaths.rootEnvPath && pathToPosix(import_path4.default.relative(outputDir, envPaths.rootEnvPath)),
      schemaEnvPath: envPaths.schemaEnvPath && pathToPosix(import_path4.default.relative(outputDir, envPaths.schemaEnvPath))
    };
    const clientEngineType = getClientEngineType(generator);
    generator.config.engineType = clientEngineType;
    const binaryTargets = clientEngineType === "library" /* Library */ ? Object.keys(binaryPaths.libqueryEngine ?? {}) : Object.keys(binaryPaths.queryEngine ?? {});
    const inlineSchemaHash = import_crypto.default.createHash("sha256").update(Buffer.from(inlineSchema, "utf8").toString("base64")).digest("hex");
    const datasourceFilePath = datasources[0].sourceFilePath;
    const config = {
      generator,
      relativeEnvPaths,
      relativePath: pathToPosix(import_path4.default.relative(outputDir, import_path4.default.dirname(datasourceFilePath))),
      clientVersion: this.options.clientVersion,
      engineVersion: this.options.engineVersion,
      datasourceNames: datasources.map((d) => d.name),
      activeProvider: this.options.activeProvider,
      postinstall: this.options.postinstall,
      ciName: import_ci_info.default.name ?? void 0,
      inlineDatasources: datasources.reduce((acc, ds) => {
        return acc[ds.name] = { url: ds.url }, acc;
      }, {}),
      inlineSchema,
      inlineSchemaHash,
      copyEngine
    };
    const relativeOutdir = import_path4.default.relative(process.cwd(), outputDir);
    const code = `${commonCodeJS({ ...this.options, browser: false })}
${buildRequirePath(edge)}

/**
 * Enums
 */
${this.dmmf.schema.enumTypes.prisma?.map((type) => new Enum(type, true).toJS()).join("\n\n")}
${this.dmmf.schema.enumTypes.model?.map((type) => new Enum(type, false).toJS()).join("\n\n") ?? ""}

${new Enum(
      {
        name: "ModelName",
        values: this.dmmf.mappings.modelOperations.map((m) => m.model)
      },
      true
    ).toJS()}
/**
 * Create the Client
 */
const config = ${JSON.stringify(config, null, 2)}
${buildDirname(edge, relativeOutdir)}
${buildRuntimeDataModel(this.dmmf.datamodel, runtimeNameJs)}
${buildQueryEngineWasmModule(wasm, copyEngine, runtimeNameJs)}
${buildInjectableEdgeEnv(edge, datasources)}
${buildWarnEnvConflicts(edge, runtimeBase, runtimeNameJs)}
${buildDebugInitialization(edge)}
const PrismaClient = getPrismaClient(config)
exports.PrismaClient = PrismaClient
Object.assign(exports, Prisma)${deno ? "\nexport { exports as default, Prisma, PrismaClient }" : ""}
${buildNFTAnnotations(edge || !copyEngine, clientEngineType, binaryTargets, relativeOutdir)}
`;
    return code;
  }
  toTS() {
    const { reusedTs } = this.options;
    if (reusedTs) {
      const topExports = moduleExportFrom(`./${reusedTs}`);
      return stringify(topExports);
    }
    const context = new GenerateContext({
      dmmf: this.dmmf,
      genericArgsInfo: this.genericsInfo,
      generator: this.options.generator,
      defaultArgsAliases: new DefaultArgsAliases()
    });
    const prismaClientClass = new PrismaClientClass(
      context,
      this.options.datasources,
      this.options.outputDir,
      this.options.runtimeNameTs,
      this.options.browser
    );
    const commonCode = commonCodeTS(this.options);
    const modelAndTypes = Object.values(this.dmmf.typeAndModelMap).reduce((acc, modelOrType) => {
      if (this.dmmf.outputTypeMap.model[modelOrType.name]) {
        acc.push(new Model(modelOrType, context));
      }
      return acc;
    }, []);
    const prismaEnums = this.dmmf.schema.enumTypes.prisma?.map((type) => new Enum(type, true).toTS());
    const modelEnums = [];
    const modelEnumsAliases = [];
    for (const enumType of this.dmmf.schema.enumTypes.model ?? []) {
      modelEnums.push(new Enum(enumType, false).toTS());
      modelEnumsAliases.push(
        stringify(moduleExport(typeDeclaration(enumType.name, namedType(`$Enums.${enumType.name}`)))),
        stringify(
          moduleExport(constDeclaration(enumType.name, namedType(`typeof $Enums.${enumType.name}`)))
        )
      );
    }
    const fieldRefs = this.dmmf.schema.fieldRefTypes.prisma?.map((type) => new FieldRefInput(type).toTS()) ?? [];
    const countTypes = this.dmmf.schema.outputObjectTypes.prisma?.filter((t) => t.name.endsWith("CountOutputType")).map((t) => new Count(t, context));
    const code = `
/**
 * Client
**/

${commonCode.tsWithoutNamespace()}

${modelAndTypes.map((m) => m.toTSWithoutNamespace()).join("\n")}
${modelEnums.length > 0 ? `
/**
 * Enums
 */
export namespace $Enums {
  ${modelEnums.join("\n\n")}
}

${modelEnumsAliases.join("\n\n")}
` : ""}
${prismaClientClass.toTSWithoutNamespace()}

export namespace Prisma {
${(0, import_indent_string8.default)(
      `${commonCode.ts()}
${new Enum(
        {
          name: "ModelName",
          values: this.dmmf.mappings.modelOperations.map((m) => m.model)
        },
        true
      ).toTS()}

${prismaClientClass.toTS()}
export type Datasource = {
  url?: string
}

/**
 * Count Types
 */

${countTypes.map((t) => t.toTS()).join("\n")}

/**
 * Models
 */
${modelAndTypes.map((model) => model.toTS()).join("\n")}

/**
 * Enums
 */

${prismaEnums?.join("\n\n")}
${fieldRefs.length > 0 ? `
/**
 * Field references 
 */

${fieldRefs.join("\n\n")}` : ""}
/**
 * Deep Input Types
 */

${this.dmmf.inputObjectTypes.prisma?.reduce((acc, inputType) => {
        if (inputType.name.includes("Json") && inputType.name.includes("Filter")) {
          const needsGeneric = this.genericsInfo.typeNeedsGenericModelArg(inputType);
          const innerName = needsGeneric ? `${inputType.name}Base<$PrismaModel>` : `${inputType.name}Base`;
          const typeName = needsGeneric ? `${inputType.name}<$PrismaModel = never>` : inputType.name;
          const baseName = `Required<${innerName}>`;
          acc.push(`export type ${typeName} = 
  | PatchUndefined<
      Either<${baseName}, Exclude<keyof ${baseName}, 'path'>>,
      ${baseName}
    >
  | OptionalFlat<Omit<${baseName}, 'path'>>`);
          acc.push(new InputType(inputType, context).overrideName(`${inputType.name}Base`).toTS());
        } else {
          acc.push(new InputType(inputType, context).toTS());
        }
        return acc;
      }, []).join("\n")}

${this.dmmf.inputObjectTypes.model?.map((inputType) => new InputType(inputType, context).toTS()).join("\n") ?? ""}

/**
 * Aliases for legacy arg types
 */
${context.defaultArgsAliases.generateAliases()}

/**
 * Batch Payload for updateMany & deleteMany & createMany
 */

export type BatchPayload = {
  count: number
}

/**
 * DMMF
 */
export const dmmf: runtime.BaseDMMF
`,
      2
    )}}`;
    return code;
  }
  toBrowserJS() {
    const code = `${commonCodeJS({
      ...this.options,
      runtimeNameJs: "index-browser",
      browser: true
    })}
/**
 * Enums
 */

${this.dmmf.schema.enumTypes.prisma?.map((type) => new Enum(type, true).toJS()).join("\n\n")}
${this.dmmf.schema.enumTypes.model?.map((type) => new Enum(type, false).toJS()).join("\n\n") ?? ""}

${new Enum(
      {
        name: "ModelName",
        values: this.dmmf.mappings.modelOperations.map((m) => m.model)
      },
      true
    ).toJS()}

/**
 * This is a stub Prisma Client that will error at runtime if called.
 */
class PrismaClient {
  constructor() {
    return new Proxy(this, {
      get(target, prop) {
        let message
        const runtime = getRuntime()
        if (runtime.isEdge) {
          message = \`PrismaClient is not configured to run in \${runtime.prettyName}. In order to run Prisma Client on edge runtime, either:
- Use Prisma Accelerate: https://pris.ly/d/accelerate
- Use Driver Adapters: https://pris.ly/d/driver-adapters
\`;
        } else {
          message = 'PrismaClient is unable to run in this browser environment, or has been bundled for the browser (running in \`' + runtime.prettyName + '\`).'
        }
        
        message += \`
If this is unexpected, please open an issue: https://pris.ly/prisma-prisma-bug-report\`

        throw new Error(message)
      }
    })
  }
}

exports.PrismaClient = PrismaClient

Object.assign(exports, Prisma)
`;
    return code;
  }
};

// src/generation/typedSql/buildDbEnums.ts
var DbEnumsList = class {
  constructor(enums) {
    this.enums = enums.map((dmmfEnum) => ({
      name: dmmfEnum.dbName ?? dmmfEnum.name,
      values: dmmfEnum.values.map((dmmfValue) => dmmfValue.dbName ?? dmmfValue.name)
    }));
  }
  isEmpty() {
    return this.enums.length === 0;
  }
  hasEnum(name) {
    return Boolean(this.enums.find((dbEnum) => dbEnum.name === name));
  }
  *validJsIdentifiers() {
    for (const dbEnum of this.enums) {
      if (isValidJsIdentifier(dbEnum.name)) {
        yield dbEnum;
      }
    }
  }
  *invalidJsIdentifiers() {
    for (const dbEnum of this.enums) {
      if (!isValidJsIdentifier(dbEnum.name)) {
        yield dbEnum;
      }
    }
  }
};
function buildDbEnums(list) {
  const file2 = file();
  file2.add(buildInvalidIdentifierEnums(list));
  file2.add(buildValidIdentifierEnums(list));
  return stringify(file2);
}
function buildValidIdentifierEnums(list) {
  const namespace2 = namespace("$DbEnums");
  for (const dbEnum of list.validJsIdentifiers()) {
    namespace2.add(typeDeclaration(dbEnum.name, enumToUnion(dbEnum)));
  }
  return moduleExport(namespace2);
}
function buildInvalidIdentifierEnums(list) {
  const iface = interfaceDeclaration("$DbEnums");
  for (const dbEnum of list.invalidJsIdentifiers()) {
    iface.add(property(dbEnum.name, enumToUnion(dbEnum)));
  }
  return moduleExport(iface);
}
function enumToUnion(dbEnum) {
  return unionType(dbEnum.values.map(stringLiteral));
}
function queryUsesEnums(query, enums) {
  if (enums.isEmpty()) {
    return false;
  }
  return query.parameters.some((param) => enums.hasEnum(param.typ)) || query.resultColumns.some((column) => enums.hasEnum(column.typ));
}

// src/generation/typedSql/buildIndex.ts
function buildIndexTs(queries, enums) {
  const file2 = file();
  if (!enums.isEmpty()) {
    file2.add(moduleExportFrom("./$DbEnums").named("$DbEnums"));
  }
  for (const query of queries) {
    file2.add(moduleExportFrom(`./${query.name}`));
  }
  return stringify(file2);
}
function buildIndexCjs(queries, edgeRuntimeSuffix) {
  const writer = new Writer(0, void 0);
  writer.writeLine('"use strict"');
  for (const { name } of queries) {
    const fileName = edgeRuntimeSuffix ? `${name}.${edgeRuntimeSuffix}` : name;
    writer.writeLine(`exports.${name} = require("./${fileName}.js").${name}`);
  }
  return writer.toString();
}
function buildIndexEsm(queries, edgeRuntimeSuffix) {
  const writer = new Writer(0, void 0);
  for (const { name } of queries) {
    const fileName = edgeRuntimeSuffix ? `${name}.${edgeRuntimeSuffix}` : name;
    writer.writeLine(`export * from "./${fileName}.mjs"`);
  }
  return writer.toString();
}

// src/generation/typedSql/mapTypes.ts
var decimal = namedType("$runtime.Decimal");
var buffer = namedType("Buffer");
var date = namedType("Date");
var inputJsonValue = namedType("$runtime.InputJsonObject");
var jsonValue = namedType("$runtime.JsonValue");
var bigintIn = unionType([numberType, bigintType]);
var decimalIn = unionType([numberType, decimal]);
var typeMappings = {
  unknown: unknownType,
  string: stringType,
  int: numberType,
  bigint: {
    in: bigintIn,
    out: bigintType
  },
  decimal: {
    in: decimalIn,
    out: decimal
  },
  float: numberType,
  double: numberType,
  enum: stringType,
  // TODO:
  bytes: buffer,
  bool: booleanType,
  char: stringType,
  json: {
    in: inputJsonValue,
    out: jsonValue
  },
  xml: stringType,
  uuid: stringType,
  date,
  datetime: date,
  time: date,
  null: nullType,
  "int-array": array(numberType),
  "string-array": array(stringType),
  "json-array": {
    in: array(inputJsonValue),
    out: array(jsonValue)
  },
  "uuid-array": array(stringType),
  "xml-array": array(stringType),
  "bigint-array": {
    in: array(bigintIn),
    out: array(bigintType)
  },
  "float-array": array(numberType),
  "double-array": array(numberType),
  "char-array": array(stringType),
  "bytes-array": array(buffer),
  "bool-array": array(booleanType),
  "date-array": array(date),
  "time-array": array(date),
  "datetime-array": array(date),
  "decimal-array": {
    in: array(decimalIn),
    out: array(decimal)
  }
};
function getInputType(introspectionType, nullable, enums) {
  const inn = getMappingConfig(introspectionType, enums).in;
  if (!nullable) {
    return inn;
  } else {
    return new UnionType(inn).addVariant(nullType);
  }
}
function getOutputType(introspectionType, nullable, enums) {
  const out = getMappingConfig(introspectionType, enums).out;
  if (!nullable) {
    return out;
  } else {
    return new UnionType(out).addVariant(nullType);
  }
}
function getMappingConfig(introspectionType, enums) {
  const config = typeMappings[introspectionType];
  if (!config) {
    if (enums.hasEnum(introspectionType)) {
      const type = getEnumType(introspectionType);
      return { in: type, out: type };
    }
    throw new Error("Unknown type");
  }
  if (config instanceof TypeBuilder) {
    return { in: config, out: config };
  }
  return config;
}
function getEnumType(name) {
  if (isValidJsIdentifier(name)) {
    return namedType(`$DbEnums.${name}`);
  }
  return namedType("$DbEnums").subKey(name);
}

// src/generation/typedSql/buildTypedQuery.ts
function buildTypedQueryTs({ query, runtimeBase, runtimeName, enums }) {
  const file2 = file();
  file2.addImport(moduleImport(`${runtimeBase}/${runtimeName}`).asNamespace("$runtime"));
  if (queryUsesEnums(query, enums)) {
    file2.addImport(moduleImport("./$DbEnums").named("$DbEnums"));
  }
  const doc = docComment(query.documentation ?? void 0);
  const factoryType = functionType();
  const parametersType = tupleType();
  for (const param of query.parameters) {
    const paramType = getInputType(param.typ, param.nullable, enums);
    factoryType.addParameter(parameter(param.name, paramType));
    parametersType.add(tupleItem(paramType).setName(param.name));
    if (param.documentation) {
      doc.addText(`@param ${param.name} ${param.documentation}`);
    } else {
      doc.addText(`@param ${param.name}`);
    }
  }
  factoryType.setReturnType(
    namedType("$runtime.TypedSql").addGenericArgument(namedType(`${query.name}.Parameters`)).addGenericArgument(namedType(`${query.name}.Result`))
  );
  file2.add(moduleExport(constDeclaration(query.name, factoryType)).setDocComment(doc));
  const namespace2 = namespace(query.name);
  namespace2.add(moduleExport(typeDeclaration("Parameters", parametersType)));
  namespace2.add(buildResultType(query, enums));
  file2.add(moduleExport(namespace2));
  return stringify(file2);
}
function buildResultType(query, enums) {
  const type = objectType().addMultiple(
    query.resultColumns.map((column) => property(column.name, getOutputType(column.typ, column.nullable, enums)))
  );
  return moduleExport(typeDeclaration("Result", type));
}
function buildTypedQueryCjs({ query, runtimeBase, runtimeName }) {
  const writer = new Writer(0, void 0);
  writer.writeLine('"use strict"');
  writer.writeLine(`const { makeTypedQueryFactory: $mkFactory } = require("${runtimeBase}/${runtimeName}")`);
  writer.writeLine(`exports.${query.name} = /*#__PURE__*/ $mkFactory(${JSON.stringify(query.source)})`);
  return writer.toString();
}
function buildTypedQueryEsm({ query, runtimeBase, runtimeName }) {
  const writer = new Writer(0, void 0);
  writer.writeLine(`import { makeTypedQueryFactory as $mkFactory } from "${runtimeBase}/${runtimeName}"`);
  writer.writeLine(`export const ${query.name} = /*#__PURE__*/ $mkFactory(${JSON.stringify(query.source)})`);
  return writer.toString();
}

// src/generation/typedSql/typedSql.ts
function buildTypedSql({
  queries,
  runtimeBase,
  edgeRuntimeName,
  mainRuntimeName,
  dmmf
}) {
  const fileMap = {};
  const enums = new DbEnumsList(dmmf.datamodel.enums);
  if (!enums.isEmpty()) {
    fileMap["$DbEnums.d.ts"] = buildDbEnums(enums);
  }
  for (const query of queries) {
    const options = { query, runtimeBase, runtimeName: mainRuntimeName, enums };
    const edgeOptions = { ...options, runtimeName: `${edgeRuntimeName}.js` };
    fileMap[`${query.name}.d.ts`] = buildTypedQueryTs(options);
    fileMap[`${query.name}.js`] = buildTypedQueryCjs(options);
    fileMap[`${query.name}.${edgeRuntimeName}.js`] = buildTypedQueryCjs(edgeOptions);
    fileMap[`${query.name}.mjs`] = buildTypedQueryEsm(options);
    fileMap[`${query.name}.edge.mjs`] = buildTypedQueryEsm(edgeOptions);
  }
  fileMap["index.d.ts"] = buildIndexTs(queries, enums);
  fileMap["index.js"] = buildIndexCjs(queries);
  fileMap["index.mjs"] = buildIndexEsm(queries);
  fileMap[`index.${edgeRuntimeName}.mjs`] = buildIndexEsm(queries, edgeRuntimeName);
  fileMap[`index.${edgeRuntimeName}.js`] = buildIndexCjs(queries, edgeRuntimeName);
  return fileMap;
}

// src/generation/generateClient.ts
var debug2 = src_default("prisma:client:generateClient");
var DenylistError = class extends Error {
  constructor(message) {
    super(message);
    this.stack = void 0;
  }
};
setClassName(DenylistError, "DenylistError");
async function buildClient({
  schemaPath,
  runtimeBase,
  datamodel,
  binaryPaths,
  outputDir,
  generator,
  dmmf,
  datasources,
  engineVersion,
  clientVersion: clientVersion2,
  activeProvider,
  postinstall,
  copyEngine,
  envPaths,
  typedSql
}) {
  const clientEngineType = getClientEngineType(generator);
  const baseClientOptions = {
    dmmf: getPrismaClientDMMF(dmmf),
    envPaths: envPaths ?? { rootEnvPath: null, schemaEnvPath: void 0 },
    datasources,
    generator,
    binaryPaths,
    schemaPath,
    outputDir,
    runtimeBase,
    clientVersion: clientVersion2,
    engineVersion,
    activeProvider,
    postinstall,
    copyEngine,
    datamodel,
    browser: false,
    deno: false,
    edge: false,
    wasm: false
  };
  const nodeClientOptions = {
    ...baseClientOptions,
    runtimeNameJs: getNodeRuntimeName(clientEngineType),
    runtimeNameTs: `${getNodeRuntimeName(clientEngineType)}.js`
  };
  const nodeClient = new TSClient(nodeClientOptions);
  const defaultClient = new TSClient({
    ...nodeClientOptions,
    reusedTs: "index",
    reusedJs: "."
  });
  const edgeClient = new TSClient({
    ...baseClientOptions,
    runtimeNameJs: "edge",
    runtimeNameTs: "library.js",
    reusedTs: "default",
    edge: true
  });
  const rnTsClient = new TSClient({
    ...baseClientOptions,
    runtimeNameJs: "react-native",
    runtimeNameTs: "react-native",
    edge: true
  });
  const trampolineTsClient = new TSClient({
    ...nodeClientOptions,
    reusedTs: "index",
    reusedJs: "#main-entry-point"
  });
  const exportsMapBase = {
    node: "./index.js",
    "edge-light": "./wasm.js",
    workerd: "./wasm.js",
    worker: "./wasm.js",
    browser: "./index-browser.js",
    default: "./index.js"
  };
  const exportsMapDefault = {
    require: exportsMapBase,
    import: exportsMapBase,
    default: exportsMapBase.default
  };
  const pkgJson = {
    name: getUniquePackageName(datamodel),
    main: "index.js",
    types: "index.d.ts",
    browser: "index-browser.js",
    exports: {
      ...import_package.default.exports,
      // TODO: remove on DA ga
      ...{ ".": exportsMapDefault }
    },
    version: clientVersion2,
    sideEffects: false
  };
  const fileMap = {};
  fileMap["index.js"] = JS(nodeClient);
  fileMap["index.d.ts"] = TS(nodeClient);
  fileMap["default.js"] = JS(defaultClient);
  fileMap["default.d.ts"] = TS(defaultClient);
  fileMap["index-browser.js"] = BrowserJS(nodeClient);
  fileMap["edge.js"] = JS(edgeClient);
  fileMap["edge.d.ts"] = TS(edgeClient);
  if (generator.previewFeatures.includes("reactNative")) {
    fileMap["react-native.js"] = JS(rnTsClient);
    fileMap["react-native.d.ts"] = TS(rnTsClient);
  }
  const usesWasmRuntime = generator.previewFeatures.includes("driverAdapters");
  if (usesWasmRuntime) {
    fileMap["default.js"] = JS(trampolineTsClient);
    fileMap["default.d.ts"] = TS(trampolineTsClient);
    fileMap["wasm-worker-loader.mjs"] = `export default import('./query_engine_bg.wasm')`;
    fileMap["wasm-edge-light-loader.mjs"] = `export default import('./query_engine_bg.wasm?module')`;
    pkgJson["browser"] = "default.js";
    pkgJson["imports"] = {
      // when `import('#wasm-engine-loader')` is called, it will be resolved to the correct file
      "#wasm-engine-loader": {
        // Keys reference: https://runtime-keys.proposal.wintercg.org/#keys
        /**
         * Vercel Edge Functions / Next.js Middlewares
         */
        "edge-light": "./wasm-edge-light-loader.mjs",
        /**
         * Cloudflare Workers, Cloudflare Pages
         */
        workerd: "./wasm-worker-loader.mjs",
        /**
         * (Old) Cloudflare Workers
         * @millsp It's a fallback, in case both other keys didn't work because we could be on a different edge platform. It's a hypothetical case rather than anything actually tested.
         */
        worker: "./wasm-worker-loader.mjs",
        /**
         * Fallback for every other JavaScript runtime
         */
        default: "./wasm-worker-loader.mjs"
      },
      // when `require('#main-entry-point')` is called, it will be resolved to the correct file
      "#main-entry-point": exportsMapDefault
    };
    const wasmClient = new TSClient({
      ...baseClientOptions,
      runtimeNameJs: "wasm",
      runtimeNameTs: "library.js",
      reusedTs: "default",
      edge: true,
      wasm: true
    });
    fileMap["wasm.js"] = JS(wasmClient);
    fileMap["wasm.d.ts"] = TS(wasmClient);
  } else {
    fileMap["wasm.js"] = fileMap["index-browser.js"];
    fileMap["wasm.d.ts"] = fileMap["default.d.ts"];
  }
  if (generator.previewFeatures.includes("deno") && !!globalThis.Deno) {
    const denoEdgeClient = new TSClient({
      ...baseClientOptions,
      runtimeBase: `../${runtimeBase}`,
      runtimeNameJs: "edge-esm",
      runtimeNameTs: "library.d.ts",
      deno: true,
      edge: true
    });
    fileMap["deno/edge.js"] = JS(denoEdgeClient);
    fileMap["deno/index.d.ts"] = TS(denoEdgeClient);
    fileMap["deno/edge.ts"] = `
import './polyfill.js'
// @deno-types="./index.d.ts"
export * from './edge.js'`;
    fileMap["deno/polyfill.js"] = "globalThis.process = { env: Deno.env.toObject() }; globalThis.global = globalThis";
  }
  if (typedSql && typedSql.length > 0) {
    const edgeRuntimeName = usesWasmRuntime ? "wasm" : "edge";
    const cjsEdgeIndex = `./sql/index.${edgeRuntimeName}.js`;
    const esmEdgeIndex = `./sql/index.${edgeRuntimeName}.mjs`;
    pkgJson.exports["./sql"] = {
      require: {
        types: "./sql/index.d.ts",
        "edge-light": cjsEdgeIndex,
        workerd: cjsEdgeIndex,
        worker: cjsEdgeIndex,
        node: "./sql/index.js",
        default: "./sql/index.js"
      },
      import: {
        types: "./sql/index.d.ts",
        "edge-light": esmEdgeIndex,
        workerd: esmEdgeIndex,
        worker: esmEdgeIndex,
        node: "./sql/index.mjs",
        default: "./sql/index.mjs"
      },
      default: "./sql/index.js"
    };
    fileMap["sql"] = buildTypedSql({
      dmmf,
      runtimeBase: getTypedSqlRuntimeBase(runtimeBase),
      mainRuntimeName: getNodeRuntimeName(clientEngineType),
      queries: typedSql,
      edgeRuntimeName
    });
  }
  fileMap["package.json"] = JSON.stringify(pkgJson, null, 2);
  return {
    fileMap,
    // a map of file names to their contents
    prismaClientDmmf: dmmf
    // the DMMF document
  };
}
function getTypedSqlRuntimeBase(runtimeBase) {
  if (!runtimeBase.startsWith(".")) {
    return runtimeBase;
  }
  if (runtimeBase.startsWith("./")) {
    return `.${runtimeBase}`;
  }
  return `../${runtimeBase}`;
}
async function getDefaultOutdir(outputDir) {
  if (outputDir.endsWith("node_modules/@prisma/client")) {
    return import_path5.default.join(outputDir, "../../.prisma/client");
  }
  if (process.env.INIT_CWD && process.env.npm_lifecycle_event === "postinstall" && !process.env.PWD?.includes(".pnpm")) {
    if ((0, import_fs2.existsSync)(import_path5.default.join(process.env.INIT_CWD, "package.json"))) {
      return import_path5.default.join(process.env.INIT_CWD, "node_modules/.prisma/client");
    }
    const packagePath = await (0, import_pkg_up.default)({ cwd: process.env.INIT_CWD });
    if (packagePath) {
      return import_path5.default.join(import_path5.default.dirname(packagePath), "node_modules/.prisma/client");
    }
  }
  return import_path5.default.join(outputDir, "../../.prisma/client");
}
async function generateClient(options) {
  const {
    datamodel,
    schemaPath,
    generator,
    dmmf,
    datasources,
    binaryPaths,
    testMode,
    copyRuntime,
    copyRuntimeSourceMaps = false,
    clientVersion: clientVersion2,
    engineVersion,
    activeProvider,
    postinstall,
    envPaths,
    copyEngine = true,
    typedSql
  } = options;
  const clientEngineType = getClientEngineType(generator);
  const { runtimeBase, outputDir } = await getGenerationDirs(options);
  const { prismaClientDmmf, fileMap } = await buildClient({
    datamodel,
    schemaPath,
    runtimeBase,
    outputDir,
    generator,
    dmmf,
    datasources,
    binaryPaths,
    clientVersion: clientVersion2,
    engineVersion,
    activeProvider,
    postinstall,
    copyEngine,
    testMode,
    envPaths,
    typedSql
  });
  const provider = datasources[0].provider;
  const denylistsErrors = validateDmmfAgainstDenylists(prismaClientDmmf);
  if (denylistsErrors) {
    let message = `${bold(
      red("Error: ")
    )}The schema at "${schemaPath}" contains reserved keywords.
       Rename the following items:`;
    for (const error of denylistsErrors) {
      message += "\n         - " + error.message;
    }
    message += `
To learn more about how to rename models, check out https://pris.ly/d/naming-models`;
    throw new DenylistError(message);
  }
  if (!copyEngine) {
    await deleteOutputDir(outputDir);
  }
  await (0, import_fs_extra.ensureDir)(outputDir);
  if (generator.previewFeatures.includes("deno") && !!globalThis.Deno) {
    await (0, import_fs_extra.ensureDir)(import_path5.default.join(outputDir, "deno"));
  }
  await writeFileMap(outputDir, fileMap);
  const runtimeDir = import_path5.default.join(__dirname, `${testMode ? "../" : ""}../runtime`);
  if (copyRuntime || generator.isCustomOutput === true) {
    const copiedRuntimeDir = import_path5.default.join(outputDir, "runtime");
    await (0, import_fs_extra.ensureDir)(copiedRuntimeDir);
    await copyRuntimeFiles({
      from: runtimeDir,
      to: copiedRuntimeDir,
      sourceMaps: copyRuntimeSourceMaps,
      runtimeName: getNodeRuntimeName(clientEngineType)
    });
  }
  const enginePath = clientEngineType === "library" /* Library */ ? binaryPaths.libqueryEngine : binaryPaths.queryEngine;
  if (!enginePath) {
    throw new Error(
      `Prisma Client needs \`${clientEngineType === "library" /* Library */ ? "libqueryEngine" : "queryEngine"}\` in the \`binaryPaths\` object.`
    );
  }
  if (copyEngine) {
    if (process.env.NETLIFY) {
      await (0, import_fs_extra.ensureDir)("/tmp/prisma-engines");
    }
    for (const [binaryTarget, filePath] of Object.entries(enginePath)) {
      const fileName = import_path5.default.basename(filePath);
      let target;
      if (process.env.NETLIFY && !["rhel-openssl-1.0.x", "rhel-openssl-3.0.x"].includes(binaryTarget)) {
        target = import_path5.default.join("/tmp/prisma-engines", fileName);
      } else {
        target = import_path5.default.join(outputDir, fileName);
      }
      await overwriteFile(filePath, target);
    }
  }
  const schemaTargetPath = import_path5.default.join(outputDir, "schema.prisma");
  await import_promises.default.writeFile(schemaTargetPath, datamodel, { encoding: "utf-8" });
  if (generator.previewFeatures.includes("driverAdapters") && isWasmEngineSupported(provider) && copyEngine && !testMode) {
    const suffix = provider === "postgres" ? "postgresql" : provider;
    await import_promises.default.copyFile(
      import_path5.default.join(runtimeDir, `query_engine_bg.${suffix}.wasm`),
      import_path5.default.join(outputDir, `query_engine_bg.wasm`)
    );
    await import_promises.default.copyFile(import_path5.default.join(runtimeDir, `query_engine_bg.${suffix}.js`), import_path5.default.join(outputDir, `query_engine_bg.js`));
  }
  try {
    const prismaCache = (0, import_env_paths.default)("prisma").cache;
    const signalsPath = import_path5.default.join(prismaCache, "last-generate");
    await import_promises.default.mkdir(prismaCache, { recursive: true });
    await import_promises.default.writeFile(signalsPath, Date.now().toString());
  } catch {
  }
}
function writeFileMap(outputDir, fileMap) {
  return Promise.all(
    Object.entries(fileMap).map(async ([fileName, content]) => {
      const absolutePath = import_path5.default.join(outputDir, fileName);
      await import_promises.default.rm(absolutePath, { recursive: true, force: true });
      if (typeof content === "string") {
        await import_promises.default.writeFile(absolutePath, content);
      } else {
        await import_promises.default.mkdir(absolutePath);
        await writeFileMap(absolutePath, content);
      }
    })
  );
}
function isWasmEngineSupported(provider) {
  return provider === "postgresql" || provider === "postgres" || provider === "mysql" || provider === "sqlite";
}
function validateDmmfAgainstDenylists(prismaClientDmmf) {
  const errorArray = [];
  const denylists = {
    // A copy of this list is also in prisma-engines. Any edit should be done in both places.
    // https://github.com/prisma/prisma-engines/blob/main/psl/parser-database/src/names/reserved_model_names.rs
    models: [
      // Reserved Prisma keywords
      "PrismaClient",
      "Prisma",
      // JavaScript keywords
      "break",
      "case",
      "catch",
      "class",
      "const",
      "continue",
      "debugger",
      "default",
      "delete",
      "do",
      "else",
      "enum",
      "export",
      "extends",
      "false",
      "finally",
      "for",
      "function",
      "if",
      "implements",
      "import",
      "in",
      "instanceof",
      "interface",
      "let",
      "new",
      "null",
      "package",
      "private",
      "protected",
      "public",
      "return",
      "super",
      "switch",
      "this",
      "throw",
      "true",
      "try",
      "typeof",
      "var",
      "void",
      "while",
      "with",
      "yield"
    ],
    fields: ["AND", "OR", "NOT"],
    dynamic: []
  };
  if (prismaClientDmmf.datamodel.enums) {
    for (const it of prismaClientDmmf.datamodel.enums) {
      if (denylists.models.includes(it.name) || denylists.fields.includes(it.name)) {
        errorArray.push(Error(`"enum ${it.name}"`));
      }
    }
  }
  if (prismaClientDmmf.datamodel.models) {
    for (const it of prismaClientDmmf.datamodel.models) {
      if (denylists.models.includes(it.name) || denylists.fields.includes(it.name)) {
        errorArray.push(Error(`"model ${it.name}"`));
      }
    }
  }
  return errorArray.length > 0 ? errorArray : null;
}
async function getGenerationDirs({
  runtimeBase,
  generator,
  outputDir,
  datamodel,
  schemaPath,
  testMode
}) {
  const isCustomOutput = generator.isCustomOutput === true;
  let userRuntimeImport = isCustomOutput ? "./runtime" : "@prisma/client/runtime";
  let userOutputDir = isCustomOutput ? outputDir : await getDefaultOutdir(outputDir);
  if (testMode && runtimeBase) {
    userOutputDir = outputDir;
    userRuntimeImport = pathToPosix(runtimeBase);
  }
  if (isCustomOutput) {
    await verifyOutputDirectory(userOutputDir, datamodel, schemaPath);
  }
  const userPackageRoot = await (0, import_pkg_up.default)({ cwd: import_path5.default.dirname(userOutputDir) });
  const userProjectRoot = userPackageRoot ? import_path5.default.dirname(userPackageRoot) : process.cwd();
  return {
    runtimeBase: userRuntimeImport,
    outputDir: userOutputDir,
    projectRoot: userProjectRoot
  };
}
async function verifyOutputDirectory(directory, datamodel, schemaPath) {
  let content;
  try {
    content = await import_promises.default.readFile(import_path5.default.join(directory, "package.json"), "utf8");
  } catch (e) {
    if (e.code === "ENOENT") {
      return;
    }
    throw e;
  }
  const { name } = JSON.parse(content);
  if (name === import_package.default.name) {
    const message = [`Generating client into ${bold(directory)} is not allowed.`];
    message.push("This package is used by `prisma generate` and overwriting its content is dangerous.");
    message.push("");
    message.push("Suggestion:");
    const outputDeclaration = findOutputPathDeclaration(datamodel);
    if (outputDeclaration && outputDeclaration.content.includes(import_package.default.name)) {
      const outputLine = outputDeclaration.content;
      message.push(`In ${bold(schemaPath)} replace:`);
      message.push("");
      message.push(`${dim(outputDeclaration.lineNumber)} ${replacePackageName(outputLine, red(import_package.default.name))}`);
      message.push("with");
      message.push(`${dim(outputDeclaration.lineNumber)} ${replacePackageName(outputLine, green(".prisma/client"))}`);
    } else {
      message.push(`Generate client into ${bold(replacePackageName(directory, green(".prisma/client")))} instead`);
    }
    message.push("");
    message.push("You won't need to change your imports.");
    message.push("Imports from `@prisma/client` will be automatically forwarded to `.prisma/client`");
    const error = new Error(message.join("\n"));
    throw error;
  }
}
function replacePackageName(directoryPath, replacement) {
  return directoryPath.replace(import_package.default.name, replacement);
}
function findOutputPathDeclaration(datamodel) {
  const lines = datamodel.split(/\r?\n/);
  for (const [i, line] of lines.entries()) {
    if (/output\s*=/.test(line)) {
      return { lineNumber: i + 1, content: line.trim() };
    }
  }
  return null;
}
function getNodeRuntimeName(engineType) {
  if (engineType === "binary" /* Binary */) {
    return "binary";
  }
  if (engineType === "library" /* Library */) {
    return "library";
  }
  assertNever(engineType, "Unknown engine type");
}
async function copyRuntimeFiles({ from, to, runtimeName, sourceMaps }) {
  const files = [
    // library.d.ts is always included, as it contains the actual runtime type
    // definitions. Rest of the `runtime.d.ts` files just re-export everything
    // from `library.d.ts`
    "library.d.ts",
    "index-browser.js",
    "index-browser.d.ts",
    "edge.js",
    "edge-esm.js",
    "react-native.js",
    "wasm.js"
  ];
  files.push(`${runtimeName}.js`);
  if (runtimeName !== "library") {
    files.push(`${runtimeName}.d.ts`);
  }
  if (sourceMaps) {
    files.push(...files.filter((file2) => file2.endsWith(".js")).map((file2) => `${file2}.map`));
  }
  await Promise.all(files.map((file2) => import_promises.default.copyFile(import_path5.default.join(from, file2), import_path5.default.join(to, file2))));
}
async function deleteOutputDir(outputDir) {
  try {
    debug2(`attempting to delete ${outputDir} recursively`);
    if (require(`${outputDir}/package.json`).name?.startsWith(GENERATED_PACKAGE_NAME_PREFIX)) {
      await import_promises.default.rmdir(outputDir, { recursive: true }).catch(() => {
        debug2(`failed to delete ${outputDir} recursively`);
      });
    }
  } catch {
    debug2(`failed to delete ${outputDir} recursively, not found`);
  }
}
function getUniquePackageName(datamodel) {
  const hash = (0, import_crypto2.createHash)("sha256");
  hash.write(datamodel);
  return `${GENERATED_PACKAGE_NAME_PREFIX}${hash.digest().toString("hex")}`;
}
var GENERATED_PACKAGE_NAME_PREFIX = "prisma-client-";

// src/generation/utils/types/dmmfToTypes.ts
function dmmfToTypes(dmmf) {
  return new TSClient({
    dmmf,
    datasources: [],
    clientVersion: "",
    engineVersion: "",
    runtimeBase: "@prisma/client",
    runtimeNameJs: "library",
    runtimeNameTs: "library",
    schemaPath: "",
    outputDir: "",
    activeProvider: "",
    binaryPaths: {},
    generator: {
      binaryTargets: [],
      config: {},
      name: "prisma-client-js",
      output: null,
      provider: { value: "prisma-client-js", fromEnvVar: null },
      previewFeatures: [],
      isCustomOutput: false,
      sourceFilePath: "schema.prisma"
    },
    datamodel: "",
    browser: false,
    deno: false,
    edge: false,
    wasm: false,
    envPaths: {
      rootEnvPath: null,
      schemaEnvPath: void 0
    }
  }).toTS();
}

// src/generation/generator.ts
var debug3 = src_default("prisma:client:generator");
var pkg = require_package2();
var clientVersion = pkg.version;
if (process.argv[1] === __filename) {
  generatorHandler({
    onManifest(config) {
      const requiredEngine = getClientEngineType(config) === "library" /* Library */ ? "libqueryEngine" : "queryEngine";
      debug3(`requiredEngine: ${requiredEngine}`);
      return {
        defaultOutput: ".prisma/client",
        // the value here doesn't matter, as it's resolved in https://github.com/prisma/prisma/blob/88fe98a09092d8e53e51f11b730c7672c19d1bd4/packages/sdk/src/get-generators/getGenerators.ts
        prettyName: "Prisma Client",
        requiresEngines: [requiredEngine],
        version: clientVersion,
        requiresEngineVersion: import_engines_version.enginesVersion
      };
    },
    async onGenerate(options) {
      const outputDir = parseEnvValue(options.generator.output);
      return generateClient({
        datamodel: options.datamodel,
        schemaPath: options.schemaPath,
        binaryPaths: options.binaryPaths,
        datasources: options.datasources,
        envPaths: options.envPaths,
        outputDir,
        copyRuntime: Boolean(options.generator.config.copyRuntime),
        // TODO: is this needed/valid?
        copyRuntimeSourceMaps: Boolean(process.env.PRISMA_COPY_RUNTIME_SOURCEMAPS),
        dmmf: options.dmmf,
        generator: options.generator,
        engineVersion: options.version,
        clientVersion,
        activeProvider: options.datasources[0]?.activeProvider,
        postinstall: options.postinstall,
        copyEngine: !options.noEngine,
        typedSql: options.typedSql
      });
    }
  });
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  dmmfToTypes,
  externalToInternalDmmf
});
