import { F as getDefaultExportFromCjs } from './dep-827b23df.js';
import require$$0 from 'path';
import require$$0__default from 'fs';
import { l as lib } from './dep-c423598f.js';

import { fileURLToPath as __cjs_fileURLToPath } from 'node:url';
import { dirname as __cjs_dirname } from 'node:path';
import { createRequire as __cjs_createRequire } from 'node:module';

const __filename = __cjs_fileURLToPath(import.meta.url);
const __dirname = __cjs_dirname(__filename);
const require = __cjs_createRequire(import.meta.url);
const __require = require;
function _mergeNamespaces(n, m) {
  for (var i = 0; i < m.length; i++) {
    var e = m[i];
    if (typeof e !== 'string' && !Array.isArray(e)) { for (var k in e) {
      if (k !== 'default' && !(k in n)) {
        n[k] = e[k];
      }
    } }
  }
  return n;
}

const startsWithKeywordRegexp = /^(all|not|only|print|screen)/i;

var joinMedia$1 = function (parentMedia, childMedia) {
  if (!parentMedia.length && childMedia.length) return childMedia
  if (parentMedia.length && !childMedia.length) return parentMedia
  if (!parentMedia.length && !childMedia.length) return []

  const media = [];

  parentMedia.forEach(parentItem => {
    const parentItemStartsWithKeyword = startsWithKeywordRegexp.test(parentItem);

    childMedia.forEach(childItem => {
      const childItemStartsWithKeyword = startsWithKeywordRegexp.test(childItem);
      if (parentItem !== childItem) {
        if (childItemStartsWithKeyword && !parentItemStartsWithKeyword) {
          media.push(`${childItem} and ${parentItem}`);
        } else {
          media.push(`${parentItem} and ${childItem}`);
        }
      }
    });
  });

  return media
};

var joinLayer$1 = function (parentLayer, childLayer) {
  if (!parentLayer.length && childLayer.length) return childLayer
  if (parentLayer.length && !childLayer.length) return parentLayer
  if (!parentLayer.length && !childLayer.length) return []

  return parentLayer.concat(childLayer)
};

var readCache$1 = {exports: {}};

var pify$2 = {exports: {}};

var processFn = function (fn, P, opts) {
	return function () {
		var that = this;
		var args = new Array(arguments.length);

		for (var i = 0; i < arguments.length; i++) {
			args[i] = arguments[i];
		}

		return new P(function (resolve, reject) {
			args.push(function (err, result) {
				if (err) {
					reject(err);
				} else if (opts.multiArgs) {
					var results = new Array(arguments.length - 1);

					for (var i = 1; i < arguments.length; i++) {
						results[i - 1] = arguments[i];
					}

					resolve(results);
				} else {
					resolve(result);
				}
			});

			fn.apply(that, args);
		});
	};
};

var pify$1 = pify$2.exports = function (obj, P, opts) {
	if (typeof P !== 'function') {
		opts = P;
		P = Promise;
	}

	opts = opts || {};
	opts.exclude = opts.exclude || [/.+Sync$/];

	var filter = function (key) {
		var match = function (pattern) {
			return typeof pattern === 'string' ? key === pattern : pattern.test(key);
		};

		return opts.include ? opts.include.some(match) : !opts.exclude.some(match);
	};

	var ret = typeof obj === 'function' ? function () {
		if (opts.excludeMain) {
			return obj.apply(this, arguments);
		}

		return processFn(obj, P, opts).apply(this, arguments);
	} : {};

	return Object.keys(obj).reduce(function (ret, key) {
		var x = obj[key];

		ret[key] = typeof x === 'function' && filter(key) ? processFn(x, P, opts) : x;

		return ret;
	}, ret);
};

pify$1.all = pify$1;

var pifyExports = pify$2.exports;

var fs = require$$0__default;
var path$2 = require$$0;
var pify = pifyExports;

var stat = pify(fs.stat);
var readFile = pify(fs.readFile);
var resolve = path$2.resolve;

var cache = Object.create(null);

function convert(content, encoding) {
	if (Buffer.isEncoding(encoding)) {
		return content.toString(encoding);
	}
	return content;
}

readCache$1.exports = function (path, encoding) {
	path = resolve(path);

	return stat(path).then(function (stats) {
		var item = cache[path];

		if (item && item.mtime.getTime() === stats.mtime.getTime()) {
			return convert(item.content, encoding);
		}

		return readFile(path).then(function (data) {
			cache[path] = {
				mtime: stats.mtime,
				content: data
			};

			return convert(data, encoding);
		});
	}).catch(function (err) {
		cache[path] = null;
		return Promise.reject(err);
	});
};

readCache$1.exports.sync = function (path, encoding) {
	path = resolve(path);

	try {
		var stats = fs.statSync(path);
		var item = cache[path];

		if (item && item.mtime.getTime() === stats.mtime.getTime()) {
			return convert(item.content, encoding);
		}

		var data = fs.readFileSync(path);

		cache[path] = {
			mtime: stats.mtime,
			content: data
		};

		return convert(data, encoding);
	} catch (err) {
		cache[path] = null;
		throw err;
	}

};

readCache$1.exports.get = function (path, encoding) {
	path = resolve(path);
	if (cache[path]) {
		return convert(cache[path].content, encoding);
	}
	return null;
};

readCache$1.exports.clear = function () {
	cache = Object.create(null);
};

var readCacheExports = readCache$1.exports;

const dataURLRegexp = /^data:text\/css;base64,/i;

function isValid(url) {
  return dataURLRegexp.test(url)
}

function contents(url) {
  // "data:text/css;base64,".length === 21
  return Buffer.from(url.slice(21), "base64").toString()
}

var dataUrl = {
  isValid,
  contents,
};

const readCache = readCacheExports;
const dataURL$1 = dataUrl;

var loadContent$1 = filename => {
  if (dataURL$1.isValid(filename)) {
    return dataURL$1.contents(filename)
  }

  return readCache(filename, "utf-8")
};

// builtin tooling
const path$1 = require$$0;

// placeholder tooling
let sugarss;

var processContent$1 = function processContent(
  result,
  content,
  filename,
  options,
  postcss
) {
  const { plugins } = options;
  const ext = path$1.extname(filename);

  const parserList = [];

  // SugarSS support:
  if (ext === ".sss") {
    if (!sugarss) {
      try {
        sugarss = __require('sugarss');
      } catch {} // Ignore
    }
    if (sugarss)
      return runPostcss(postcss, content, filename, plugins, [sugarss])
  }

  // Syntax support:
  if (result.opts.syntax?.parse) {
    parserList.push(result.opts.syntax.parse);
  }

  // Parser support:
  if (result.opts.parser) parserList.push(result.opts.parser);
  // Try the default as a last resort:
  parserList.push(null);

  return runPostcss(postcss, content, filename, plugins, parserList)
};

function runPostcss(postcss, content, filename, plugins, parsers, index) {
  if (!index) index = 0;
  return postcss(plugins)
    .process(content, {
      from: filename,
      parser: parsers[index],
    })
    .catch(err => {
      // If there's an error, try the next parser
      index++;
      // If there are no parsers left, throw it
      if (index === parsers.length) throw err
      return runPostcss(postcss, content, filename, plugins, parsers, index)
    })
}

// external tooling
const valueParser = lib;

// extended tooling
const { stringify } = valueParser;

function split(params, start) {
  const list = [];
  const last = params.reduce((item, node, index) => {
    if (index < start) return ""
    if (node.type === "div" && node.value === ",") {
      list.push(item);
      return ""
    }
    return item + stringify(node)
  }, "");
  list.push(last);
  return list
}

var parseStatements$1 = function (result, styles) {
  const statements = [];
  let nodes = [];

  styles.each(node => {
    let stmt;
    if (node.type === "atrule") {
      if (node.name === "import") stmt = parseImport(result, node);
      else if (node.name === "media") stmt = parseMedia(result, node);
      else if (node.name === "charset") stmt = parseCharset(result, node);
    }

    if (stmt) {
      if (nodes.length) {
        statements.push({
          type: "nodes",
          nodes,
          media: [],
          layer: [],
        });
        nodes = [];
      }
      statements.push(stmt);
    } else nodes.push(node);
  });

  if (nodes.length) {
    statements.push({
      type: "nodes",
      nodes,
      media: [],
      layer: [],
    });
  }

  return statements
};

function parseMedia(result, atRule) {
  const params = valueParser(atRule.params).nodes;
  return {
    type: "media",
    node: atRule,
    media: split(params, 0),
    layer: [],
  }
}

function parseCharset(result, atRule) {
  if (atRule.prev()) {
    return result.warn("@charset must precede all other statements", {
      node: atRule,
    })
  }
  return {
    type: "charset",
    node: atRule,
    media: [],
    layer: [],
  }
}

function parseImport(result, atRule) {
  let prev = atRule.prev();
  if (prev) {
    do {
      if (
        prev.type !== "comment" &&
        (prev.type !== "atrule" ||
          (prev.name !== "import" &&
            prev.name !== "charset" &&
            !(prev.name === "layer" && !prev.nodes)))
      ) {
        return result.warn(
          "@import must precede all other statements (besides @charset or empty @layer)",
          { node: atRule }
        )
      }
      prev = prev.prev();
    } while (prev)
  }

  if (atRule.nodes) {
    return result.warn(
      "It looks like you didn't end your @import statement correctly. " +
        "Child nodes are attached to it.",
      { node: atRule }
    )
  }

  const params = valueParser(atRule.params).nodes;
  const stmt = {
    type: "import",
    node: atRule,
    media: [],
    layer: [],
  };

  // prettier-ignore
  if (
    !params.length ||
    (
      params[0].type !== "string" ||
      !params[0].value
    ) &&
    (
      params[0].type !== "function" ||
      params[0].value !== "url" ||
      !params[0].nodes.length ||
      !params[0].nodes[0].value
    )
  ) {
    return result.warn(`Unable to find uri in '${  atRule.toString()  }'`, {
      node: atRule,
    })
  }

  if (params[0].type === "string") stmt.uri = params[0].value;
  else stmt.uri = params[0].nodes[0].value;
  stmt.fullUri = stringify(params[0]);

  let remainder = params;
  if (remainder.length > 2) {
    if (
      (remainder[2].type === "word" || remainder[2].type === "function") &&
      remainder[2].value === "layer"
    ) {
      if (remainder[1].type !== "space") {
        return result.warn("Invalid import layer statement", { node: atRule })
      }

      if (remainder[2].nodes) {
        stmt.layer = [stringify(remainder[2].nodes)];
      } else {
        stmt.layer = [""];
      }
      remainder = remainder.slice(2);
    }
  }

  if (remainder.length > 2) {
    if (remainder[1].type !== "space") {
      return result.warn("Invalid import media statement", { node: atRule })
    }

    stmt.media = split(remainder, 2);
  }

  return stmt
}

var assignLayerNames$1 = function (layer, node, state, options) {
  layer.forEach((layerPart, i) => {
    if (layerPart.trim() === "") {
      if (options.nameLayer) {
        layer[i] = options
          .nameLayer(state.anonymousLayerCounter++, state.rootFilename)
          .toString();
      } else {
        throw node.error(
          `When using anonymous layers in @import you must also set the "nameLayer" plugin option`
        )
      }
    }
  });
};

// builtin tooling
const path = require$$0;

// internal tooling
const joinMedia = joinMedia$1;
const joinLayer = joinLayer$1;
const resolveId = (id) => id;
const loadContent = loadContent$1;
const processContent = processContent$1;
const parseStatements = parseStatements$1;
const assignLayerNames = assignLayerNames$1;
const dataURL = dataUrl;

function AtImport(options) {
  options = {
    root: process.cwd(),
    path: [],
    skipDuplicates: true,
    resolve: resolveId,
    load: loadContent,
    plugins: [],
    addModulesDirectories: [],
    nameLayer: null,
    ...options,
  };

  options.root = path.resolve(options.root);

  // convert string to an array of a single element
  if (typeof options.path === "string") options.path = [options.path];

  if (!Array.isArray(options.path)) options.path = [];

  options.path = options.path.map(p => path.resolve(options.root, p));

  return {
    postcssPlugin: "postcss-import",
    Once(styles, { result, atRule, postcss }) {
      const state = {
        importedFiles: {},
        hashFiles: {},
        rootFilename: null,
        anonymousLayerCounter: 0,
      };

      if (styles.source?.input?.file) {
        state.rootFilename = styles.source.input.file;
        state.importedFiles[styles.source.input.file] = {};
      }

      if (options.plugins && !Array.isArray(options.plugins)) {
        throw new Error("plugins option must be an array")
      }

      if (options.nameLayer && typeof options.nameLayer !== "function") {
        throw new Error("nameLayer option must be a function")
      }

      return parseStyles(result, styles, options, state, [], []).then(
        bundle => {
          applyRaws(bundle);
          applyMedia(bundle);
          applyStyles(bundle, styles);
        }
      )

      function applyRaws(bundle) {
        bundle.forEach((stmt, index) => {
          if (index === 0) return

          if (stmt.parent) {
            const { before } = stmt.parent.node.raws;
            if (stmt.type === "nodes") stmt.nodes[0].raws.before = before;
            else stmt.node.raws.before = before;
          } else if (stmt.type === "nodes") {
            stmt.nodes[0].raws.before = stmt.nodes[0].raws.before || "\n";
          }
        });
      }

      function applyMedia(bundle) {
        bundle.forEach(stmt => {
          if (
            (!stmt.media.length && !stmt.layer.length) ||
            stmt.type === "charset"
          ) {
            return
          }

          if (stmt.layer.length > 1) {
            assignLayerNames(stmt.layer, stmt.node, state, options);
          }

          if (stmt.type === "import") {
            const parts = [stmt.fullUri];

            const media = stmt.media.join(", ");

            if (stmt.layer.length) {
              const layerName = stmt.layer.join(".");

              let layerParams = "layer";
              if (layerName) {
                layerParams = `layer(${layerName})`;
              }

              parts.push(layerParams);
            }

            if (media) {
              parts.push(media);
            }

            stmt.node.params = parts.join(" ");
          } else if (stmt.type === "media") {
            if (stmt.layer.length) {
              const layerNode = atRule({
                name: "layer",
                params: stmt.layer.join("."),
                source: stmt.node.source,
              });

              if (stmt.parentMedia?.length) {
                const mediaNode = atRule({
                  name: "media",
                  params: stmt.parentMedia.join(", "),
                  source: stmt.node.source,
                });

                mediaNode.append(layerNode);
                layerNode.append(stmt.node);
                stmt.node = mediaNode;
              } else {
                layerNode.append(stmt.node);
                stmt.node = layerNode;
              }
            } else {
              stmt.node.params = stmt.media.join(", ");
            }
          } else {
            const { nodes } = stmt;
            const { parent } = nodes[0];

            let outerAtRule;
            let innerAtRule;
            if (stmt.media.length && stmt.layer.length) {
              const mediaNode = atRule({
                name: "media",
                params: stmt.media.join(", "),
                source: parent.source,
              });

              const layerNode = atRule({
                name: "layer",
                params: stmt.layer.join("."),
                source: parent.source,
              });

              mediaNode.append(layerNode);
              innerAtRule = layerNode;
              outerAtRule = mediaNode;
            } else if (stmt.media.length) {
              const mediaNode = atRule({
                name: "media",
                params: stmt.media.join(", "),
                source: parent.source,
              });

              innerAtRule = mediaNode;
              outerAtRule = mediaNode;
            } else if (stmt.layer.length) {
              const layerNode = atRule({
                name: "layer",
                params: stmt.layer.join("."),
                source: parent.source,
              });

              innerAtRule = layerNode;
              outerAtRule = layerNode;
            }

            parent.insertBefore(nodes[0], outerAtRule);

            // remove nodes
            nodes.forEach(node => {
              node.parent = undefined;
            });

            // better output
            nodes[0].raws.before = nodes[0].raws.before || "\n";

            // wrap new rules with media query and/or layer at rule
            innerAtRule.append(nodes);

            stmt.type = "media";
            stmt.node = outerAtRule;
            delete stmt.nodes;
          }
        });
      }

      function applyStyles(bundle, styles) {
        styles.nodes = [];

        // Strip additional statements.
        bundle.forEach(stmt => {
          if (["charset", "import", "media"].includes(stmt.type)) {
            stmt.node.parent = undefined;
            styles.append(stmt.node);
          } else if (stmt.type === "nodes") {
            stmt.nodes.forEach(node => {
              node.parent = undefined;
              styles.append(node);
            });
          }
        });
      }

      function parseStyles(result, styles, options, state, media, layer) {
        const statements = parseStatements(result, styles);

        return Promise.resolve(statements)
          .then(stmts => {
            // process each statement in series
            return stmts.reduce((promise, stmt) => {
              return promise.then(() => {
                stmt.media = joinMedia(media, stmt.media || []);
                stmt.parentMedia = media;
                stmt.layer = joinLayer(layer, stmt.layer || []);

                // skip protocol base uri (protocol://url) or protocol-relative
                if (
                  stmt.type !== "import" ||
                  /^(?:[a-z]+:)?\/\//i.test(stmt.uri)
                ) {
                  return
                }

                if (options.filter && !options.filter(stmt.uri)) {
                  // rejected by filter
                  return
                }

                return resolveImportId(result, stmt, options, state)
              })
            }, Promise.resolve())
          })
          .then(() => {
            let charset;
            const imports = [];
            const bundle = [];

            function handleCharset(stmt) {
              if (!charset) charset = stmt;
              // charsets aren't case-sensitive, so convert to lower case to compare
              else if (
                stmt.node.params.toLowerCase() !==
                charset.node.params.toLowerCase()
              ) {
                throw new Error(
                  `Incompatable @charset statements:
  ${stmt.node.params} specified in ${stmt.node.source.input.file}
  ${charset.node.params} specified in ${charset.node.source.input.file}`
                )
              }
            }

            // squash statements and their children
            statements.forEach(stmt => {
              if (stmt.type === "charset") handleCharset(stmt);
              else if (stmt.type === "import") {
                if (stmt.children) {
                  stmt.children.forEach((child, index) => {
                    if (child.type === "import") imports.push(child);
                    else if (child.type === "charset") handleCharset(child);
                    else bundle.push(child);
                    // For better output
                    if (index === 0) child.parent = stmt;
                  });
                } else imports.push(stmt);
              } else if (stmt.type === "media" || stmt.type === "nodes") {
                bundle.push(stmt);
              }
            });

            return charset
              ? [charset, ...imports.concat(bundle)]
              : imports.concat(bundle)
          })
      }

      function resolveImportId(result, stmt, options, state) {
        if (dataURL.isValid(stmt.uri)) {
          return loadImportContent(result, stmt, stmt.uri, options, state).then(
            result => {
              stmt.children = result;
            }
          )
        }

        const atRule = stmt.node;
        let sourceFile;
        if (atRule.source?.input?.file) {
          sourceFile = atRule.source.input.file;
        }
        const base = sourceFile
          ? path.dirname(atRule.source.input.file)
          : options.root;

        return Promise.resolve(options.resolve(stmt.uri, base, options))
          .then(paths => {
            if (!Array.isArray(paths)) paths = [paths];
            // Ensure that each path is absolute:
            return Promise.all(
              paths.map(file => {
                return !path.isAbsolute(file)
                  ? resolveId(file)
                  : file
              })
            )
          })
          .then(resolved => {
            // Add dependency messages:
            resolved.forEach(file => {
              result.messages.push({
                type: "dependency",
                plugin: "postcss-import",
                file,
                parent: sourceFile,
              });
            });

            return Promise.all(
              resolved.map(file => {
                return loadImportContent(result, stmt, file, options, state)
              })
            )
          })
          .then(result => {
            // Merge loaded statements
            stmt.children = result.reduce((result, statements) => {
              return statements ? result.concat(statements) : result
            }, []);
          })
      }

      function loadImportContent(result, stmt, filename, options, state) {
        const atRule = stmt.node;
        const { media, layer } = stmt;

        assignLayerNames(layer, atRule, state, options);

        if (options.skipDuplicates) {
          // skip files already imported at the same scope
          if (state.importedFiles[filename]?.[media]?.[layer]) {
            return
          }

          // save imported files to skip them next time
          if (!state.importedFiles[filename]) {
            state.importedFiles[filename] = {};
          }
          if (!state.importedFiles[filename][media]) {
            state.importedFiles[filename][media] = {};
          }
          state.importedFiles[filename][media][layer] = true;
        }

        return Promise.resolve(options.load(filename, options)).then(
          content => {
            if (content.trim() === "") {
              result.warn(`${filename} is empty`, { node: atRule });
              return
            }

            // skip previous imported files not containing @import rules
            if (state.hashFiles[content]?.[media]?.[layer]) {
              return
            }

            return processContent(
              result,
              content,
              filename,
              options,
              postcss
            ).then(importedResult => {
              const styles = importedResult.root;
              result.messages = result.messages.concat(importedResult.messages);

              if (options.skipDuplicates) {
                const hasImport = styles.some(child => {
                  return child.type === "atrule" && child.name === "import"
                });
                if (!hasImport) {
                  // save hash files to skip them next time
                  if (!state.hashFiles[content]) {
                    state.hashFiles[content] = {};
                  }
                  if (!state.hashFiles[content][media]) {
                    state.hashFiles[content][media] = {};
                  }
                  state.hashFiles[content][media][layer] = true;
                }
              }

              // recursion: import @import from imported file
              return parseStyles(result, styles, options, state, media, layer)
            })
          }
        )
      }
    },
  }
}

AtImport.postcss = true;

var postcssImport = AtImport;

var index = /*@__PURE__*/getDefaultExportFromCjs(postcssImport);

var index$1 = /*#__PURE__*/_mergeNamespaces({
  __proto__: null,
  default: index
}, [postcssImport]);

export { index$1 as i };
