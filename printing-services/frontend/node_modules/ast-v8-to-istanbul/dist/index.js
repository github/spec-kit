import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { LEAST_UPPER_BOUND, TraceMap, allGeneratedPositionsFor, originalPositionFor } from "@jridgewell/trace-mapping";
import { asyncWalk } from "estree-walker";
import jsTokens from "js-tokens";
import { readFile } from "node:fs/promises";

//#region src/ast.ts
function getWalker() {
	let nextIgnore = false;
	function onIgnore(node) {
		nextIgnore = node;
	}
	async function walk(ast, ignoreHints, ignoreClassMethods, visitors) {
		return await asyncWalk(ast, {
			async enter(node) {
				if (nextIgnore !== false) return;
				const hint = getIgnoreHint(node);
				if (hint === "next") return onIgnore(node);
				if (isSkipped(node)) onIgnore(node);
				switch (node.type) {
					case "FunctionDeclaration": return visitors.onFunctionDeclaration(node);
					case "FunctionExpression":
						if (ignoreClassMethods && node.id?.name) {
							if (ignoreClassMethods.includes(node.id.name)) return onIgnore(node);
						}
						return visitors.onFunctionExpression(node);
					case "MethodDefinition": return visitors.onMethodDefinition(node);
					case "Property": return visitors.onProperty(node);
					case "ArrowFunctionExpression":
						if (node.body?.type === "ParenthesizedExpression") node.body = node.body.expression;
						return visitors.onArrowFunctionExpression(node);
					case "ExpressionStatement": return visitors.onExpressionStatement(node);
					case "BreakStatement": return visitors.onBreakStatement(node);
					case "ContinueStatement": return visitors.onContinueStatement(node);
					case "DebuggerStatement": return visitors.onDebuggerStatement(node);
					case "ReturnStatement": return visitors.onReturnStatement(node);
					case "ThrowStatement": return visitors.onThrowStatement(node);
					case "TryStatement": return visitors.onTryStatement(node);
					case "ForStatement": return visitors.onForStatement(node);
					case "ForInStatement": return visitors.onForInStatement(node);
					case "ForOfStatement": return visitors.onForOfStatement(node);
					case "WhileStatement": return visitors.onWhileStatement(node);
					case "DoWhileStatement": return visitors.onDoWhileStatement(node);
					case "WithStatement": return visitors.onWithStatement(node);
					case "LabeledStatement": return visitors.onLabeledStatement(node);
					case "VariableDeclarator": return visitors.onVariableDeclarator(node);
					case "ClassBody": {
						const classBody = node;
						if (ignoreClassMethods) {
							for (const child of classBody.body) if (child.type === "MethodDefinition" || child.type === "ClassMethod") {
								const name = child.key.type === "Identifier" && child.key.name;
								if (name && ignoreClassMethods.includes(name)) setSkipped(child);
							}
							classBody.body = classBody.body.filter((child) => !isSkipped(child));
						}
						return visitors.onClassBody(classBody);
					}
					case "IfStatement": {
						const branches = [];
						if (node.consequent.type !== "BlockStatement") node.consequent = {
							type: "BlockStatement",
							body: [node.consequent],
							start: node.consequent.start,
							end: node.consequent.end
						};
						if (node.alternate && node.alternate.type !== "BlockStatement") node.alternate = {
							type: "BlockStatement",
							body: [node.alternate],
							start: node.alternate.start,
							end: node.alternate.end
						};
						if (hint === "if") setSkipped(node.consequent);
						else branches.push(node.consequent);
						if (hint === "else" && node.alternate) setSkipped(node.alternate);
						else if (hint !== "if" && hint !== "else") branches.push(node.alternate);
						return visitors.onIfStatement(node, branches);
					}
					case "SwitchStatement": {
						const cases = [];
						for (const _case of node.cases) if (getIgnoreHint(_case) !== "next") cases.push(_case);
						return visitors.onSwitchStatement(node, cases);
					}
					case "ConditionalExpression": return visitors.onConditionalExpression(node);
					case "LogicalExpression": {
						if (isSkipped(node)) return;
						const branches = [];
						function visit(child) {
							if (child.type === "LogicalExpression") {
								setSkipped(child);
								if (getIgnoreHint(child) !== "next") {
									visit(child.left);
									return visit(child.right);
								}
							}
							branches.push(child);
						}
						visit(node);
						return visitors.onLogicalExpression(node, branches);
					}
					case "AssignmentPattern": return visitors.onAssignmentPattern(node);
					case "ClassMethod": return visitors.onClassMethod(node);
					case "ObjectMethod": return visitors.onObjectMethod(node);
				}
			},
			async leave(node) {
				if (node === nextIgnore) nextIgnore = false;
			}
		});
		function getIgnoreHint(node) {
			for (const hint of ignoreHints) if (hint.loc.end === node.start) return hint.type;
			return null;
		}
	}
	return {
		walk,
		onIgnore
	};
}
function getFunctionName(node) {
	if (node.type === "Identifier") return node.name;
	if ("id" in node && node.id) return getFunctionName(node.id);
}
function setSkipped(node) {
	node.__skipped = true;
}
function isSkipped(node) {
	return node.__skipped === true;
}

//#endregion
//#region src/coverage-map.ts
function createCoverageMapData(filename, sourceMap) {
	const data = {};
	const directory = dirname(filename);
	for (const source of sourceMap.sources) {
		let path = filename;
		if (source) if (source.startsWith("file://")) path = fileURLToPath(source);
		else path = resolve(directory, source);
		const meta = {
			lastBranch: 0,
			lastFunction: 0,
			lastStatement: 0,
			seen: {}
		};
		data[path] = {
			path,
			statementMap: {},
			fnMap: {},
			branchMap: {},
			s: {},
			f: {},
			b: {},
			meta
		};
	}
	return data;
}
function addFunction(options) {
	const fileCoverage = options.coverageMapData[options.filename];
	const meta = fileCoverage.meta;
	const key = `f:${cacheKey(options.decl)}`;
	let index = meta.seen[key];
	if (index == null) {
		index = meta.lastFunction;
		meta.lastFunction++;
		meta.seen[key] = index;
		fileCoverage.fnMap[index] = {
			name: options.name || `(anonymous_${index})`,
			decl: pickLocation(options.decl),
			loc: pickLocation(options.loc),
			line: options.loc.start.line
		};
	}
	fileCoverage.f[index] ||= 0;
	fileCoverage.f[index] += options.covered || 0;
}
function addStatement(options) {
	const fileCoverage = options.coverageMapData[options.filename];
	const meta = fileCoverage.meta;
	const key = `s:${cacheKey(options.loc)}`;
	let index = meta.seen[key];
	if (index == null) {
		index = meta.lastStatement;
		meta.lastStatement++;
		meta.seen[key] = index;
		fileCoverage.statementMap[index] = pickLocation(options.loc);
	}
	fileCoverage.s[index] = options.covered || 0;
}
function addBranch(options) {
	const fileCoverage = options.coverageMapData[options.filename];
	const meta = fileCoverage.meta;
	const key = ["b", ...options.locations.map(cacheKey)].join(":");
	let index = meta.seen[key];
	if (index == null) {
		index = meta.lastBranch;
		meta.lastBranch++;
		meta.seen[key] = index;
		fileCoverage.branchMap[index] = {
			loc: pickLocation(options.loc),
			type: options.type,
			locations: options.locations.map((loc) => pickLocation(loc)),
			line: options.loc.start.line
		};
	}
	if (!fileCoverage.b[index]) fileCoverage.b[index] = Array(options.locations.length).fill(0);
	options.covered?.forEach((hit, i) => {
		fileCoverage.b[index][i] += hit;
	});
}
function pickLocation(loc) {
	return {
		start: {
			line: loc.start.line,
			column: loc.start.column
		},
		end: {
			line: loc.end.line,
			column: loc.end.column
		}
	};
}
function cacheKey(loc) {
	return `${loc.start.line}:${loc.start.column}:${loc.end.line}:${loc.end.column}`;
}

//#endregion
//#region src/ignore-hints.ts
const IGNORE_PATTERN = /^\s*(?:istanbul|[cv]8|node:coverage)\s+ignore\s+(if|else|next|file)(?=\W|$)/;
function getIgnoreHints(code) {
	const ignoreHints = [];
	const tokens = jsTokens(code);
	let current = 0;
	let previousTokenWasIgnoreHint = false;
	for (const token of tokens) {
		if (previousTokenWasIgnoreHint && token.type !== "WhiteSpace" && token.type !== "LineTerminatorSequence") {
			const previous = ignoreHints.at(-1);
			if (previous) previous.loc.end = current;
			previousTokenWasIgnoreHint = false;
		}
		if (token.type === "SingleLineComment" || token.type === "MultiLineComment") {
			const loc = {
				start: current,
				end: current + token.value.length
			};
			const comment = token.value.replace(/^\/\*\*/, "").replace(/^\/\*/, "").replace(/\*\*\/$/, "").replace(/\*\/$/, "").replace(/^\/\//, "");
			const groups = comment.match(IGNORE_PATTERN);
			const type = groups?.[1];
			if (type === "file") return [{
				type: "file",
				loc: {
					start: 0,
					end: 0
				}
			}];
			if (type === "if" || type === "else" || type === "next") {
				ignoreHints.push({
					type,
					loc
				});
				previousTokenWasIgnoreHint = true;
			}
		}
		current += token.value.length;
	}
	return ignoreHints;
}

//#endregion
//#region src/location.ts
const WORD_PATTERN = /(\w+|\s|[^\w\s])/g;
const INLINE_MAP_PATTERN = /#\s*sourceMappingURL=(.*)\s*$/m;
const BASE_64_PREFIX = "data:application/json;base64,";
/** How often should offset calculations be cached */
const CACHE_THRESHOLD = 250;
var Locator = class {
	#cache = /* @__PURE__ */ new Map();
	#codeParts;
	#map;
	#directory;
	constructor(code, map, directory) {
		this.#codeParts = code.split("");
		this.#map = map;
		this.#directory = directory;
	}
	reset() {
		this.#cache.clear();
		this.#codeParts = [];
	}
	offsetToNeedle(offset) {
		const closestThreshold = Math.floor(offset / CACHE_THRESHOLD) * CACHE_THRESHOLD;
		const cacheHit = this.#cache.get(closestThreshold);
		let current = cacheHit ? closestThreshold : 0;
		let line = cacheHit?.line ?? 1;
		let column = cacheHit?.column ?? 0;
		for (let i = current; i <= this.#codeParts.length; i++) {
			const char = this.#codeParts[i];
			if (current === offset) return {
				line,
				column
			};
			if (char === "\r") continue;
			if (current % CACHE_THRESHOLD === 0) this.#cache.set(current, {
				line,
				column
			});
			if (char === "\n") {
				line++;
				column = 0;
			} else column++;
			current++;
		}
		return {
			line,
			column
		};
	}
	getLoc(node) {
		const startNeedle = this.offsetToNeedle(node.start);
		const start = getPosition(startNeedle, this.#map);
		if (start === null) return null;
		const endNeedle = this.offsetToNeedle(node.end);
		endNeedle.column -= 1;
		let end = getPosition(endNeedle, this.#map);
		if (end === null) {
			endNeedle.column++;
			end = getPosition(endNeedle, this.#map);
		}
		if (end === null) return null;
		const loc = {
			start,
			end
		};
		const afterEndMappings = allGeneratedPositionsFor(this.#map, {
			source: loc.end.filename,
			line: loc.end.line,
			column: loc.end.column + 1,
			bias: LEAST_UPPER_BOUND
		});
		if (afterEndMappings.length === 0) loc.end.column = Infinity;
		else for (const mapping of afterEndMappings) {
			if (mapping.line === null) continue;
			const original = originalPositionFor(this.#map, mapping);
			if (original.line === loc.end.line) {
				loc.end = {
					...original,
					filename: original.source
				};
				break;
			}
		}
		return loc;
	}
	getSourceLines(loc, filename) {
		const index = this.#map.resolvedSources.findIndex((source) => source === filename || resolve(this.#directory, source));
		const sourcesContent = this.#map.sourcesContent?.[index];
		if (sourcesContent == null) return null;
		const lines = sourcesContent.split("\n").slice(loc.start.line - 1, loc.end.line);
		lines[0] = lines[0].slice(loc.start.column);
		lines[lines.length - 1] = lines[lines.length - 1].slice(0, loc.end.column);
		return lines.join("\n");
	}
};
function getPosition(needle, map) {
	let position = originalPositionFor(map, needle);
	if (position.source == null) position = originalPositionFor(map, {
		column: needle.column,
		line: needle.line,
		bias: LEAST_UPPER_BOUND
	});
	if (position.source == null) return null;
	return {
		line: position.line,
		column: position.column,
		filename: position.source
	};
}
function createEmptySourceMap(filename, code) {
	const mappings = [];
	for (const [line, content] of code.split("\n").entries()) {
		const parts = content.match(WORD_PATTERN) || [];
		const segments = [];
		let column = 0;
		for (const part of parts) {
			segments.push([
				column,
				0,
				line,
				column
			]);
			column += part.length;
		}
		mappings.push(segments);
	}
	return {
		version: 3,
		mappings,
		file: filename,
		sources: [filename],
		sourcesContent: [code],
		names: []
	};
}
async function getInlineSourceMap(filename, code) {
	const matches = code.match(INLINE_MAP_PATTERN);
	const match = matches?.[1];
	if (!match) return null;
	try {
		if (match.includes(BASE_64_PREFIX)) {
			const encoded = match.split(BASE_64_PREFIX).at(-1) || "";
			const decoded = atob(encoded);
			return JSON.parse(decoded);
		}
		const directory = dirname(filename);
		const content = await readFile(resolve(directory, match), "utf-8");
		return JSON.parse(content);
	} catch {
		return null;
	}
}

//#endregion
//#region src/script-coverage.ts
function normalize(scriptCoverage) {
	if (scriptCoverage.functions.length === 0) return [];
	const ranges = scriptCoverage.functions.flatMap((fn) => fn.ranges.map((range) => ({
		start: range.startOffset,
		end: range.endOffset,
		count: range.count,
		area: range.endOffset - range.startOffset
	}))).sort((a, b) => {
		const diff = b.area - a.area;
		if (diff !== 0) return diff;
		return a.end - b.end;
	});
	let maxEnd = 0;
	for (const r of ranges) if (r.end > maxEnd) maxEnd = r.end;
	const hits = new Uint32Array(maxEnd + 1);
	for (const range of ranges) hits.fill(range.count, range.start, range.end + 1);
	const normalized = [];
	let start = 0;
	for (let end = 1; end <= hits.length; end++) {
		const isLast = end === hits.length;
		const current = isLast ? null : hits[end];
		const previous = hits[start];
		if (current !== previous || isLast) {
			normalized.push({
				start,
				end: end - 1,
				count: previous
			});
			start = end;
		}
	}
	return normalized;
}
function getCount(offset, coverages) {
	let low = 0;
	let high = coverages.length - 1;
	while (low <= high) {
		const mid = Math.floor((low + high) / 2);
		const coverage = coverages[mid];
		if (coverage.start <= offset.startOffset && offset.startOffset <= coverage.end) return coverage.count;
		else if (offset.startOffset < coverage.start) high = mid - 1;
		else low = mid + 1;
	}
	return 0;
}

//#endregion
//#region src/index.ts
/**
* Maps V8 `ScriptCoverage` to Istanbul's `CoverageMap`.
* Results are identical with `istanbul-lib-instrument`.
*/
async function convert(options) {
	const ignoreHints = getIgnoreHints(options.code);
	if (ignoreHints.length === 1 && ignoreHints[0].type === "file") return {};
	const wrapperLength = options.wrapperLength || 0;
	const filename = fileURLToPath(options.coverage.url);
	const directory = dirname(filename);
	const map = new TraceMap(options.sourceMap || await getInlineSourceMap(filename, options.code) || createEmptySourceMap(filename, options.code));
	const locator = new Locator(options.code, map, directory);
	const coverageMapData = createCoverageMapData(filename, map);
	const ranges = normalize(options.coverage);
	const ast = await options.ast;
	const walker = getWalker();
	await walker.walk(ast, ignoreHints, options.ignoreClassMethods, {
		onFunctionDeclaration(node) {
			onFunction(node, {
				loc: node.body,
				decl: node.id
			});
		},
		onFunctionExpression(node) {
			if (isCovered(node)) return;
			onFunction(node, {
				loc: node.body,
				decl: node.id || {
					...node,
					end: node.start + 1
				}
			});
		},
		onArrowFunctionExpression(node) {
			onFunction(node, {
				loc: node.body,
				decl: {
					...node,
					end: node.start + 1
				}
			});
			if (node.body.type !== "BlockStatement") onStatement(node.body, node);
		},
		onMethodDefinition(node) {
			if (node.value.type === "FunctionExpression") setCovered(node.value);
			onFunction(node, {
				loc: node.value.body,
				decl: node.key
			});
		},
		onProperty(node) {
			if (node.value.type === "FunctionExpression") {
				setCovered(node.value);
				onFunction(node, {
					loc: node.value.body,
					decl: node.key
				});
			}
		},
		onClassMethod(babelNode) {
			const node = {
				type: "FunctionExpression",
				start: babelNode.start,
				end: babelNode.end,
				body: {
					type: "BlockStatement",
					start: babelNode.body.start,
					end: babelNode.body.end,
					body: []
				},
				params: []
			};
			onFunction(node, {
				loc: node.body,
				decl: {
					start: babelNode.key.start,
					end: babelNode.key.end
				}
			});
		},
		onObjectMethod(babelNode) {
			const node = {
				type: "FunctionExpression",
				start: babelNode.start,
				end: babelNode.end,
				body: {
					type: "BlockStatement",
					start: babelNode.body.start,
					end: babelNode.body.end,
					body: []
				},
				params: []
			};
			onFunction(node, {
				loc: node.body,
				decl: {
					start: babelNode.key.start,
					end: babelNode.key.end
				}
			});
		},
		onBreakStatement: onStatement,
		onContinueStatement: onStatement,
		onDebuggerStatement: onStatement,
		onReturnStatement: onStatement,
		onThrowStatement: onStatement,
		onTryStatement: onStatement,
		onForStatement: onStatement,
		onForInStatement: onStatement,
		onForOfStatement: onStatement,
		onWhileStatement: onStatement,
		onDoWhileStatement: onStatement,
		onWithStatement: onStatement,
		onLabeledStatement: onStatement,
		onExpressionStatement(node) {
			if (node.expression.type === "Literal" && node.expression.value === "use strict") return;
			onStatement(node);
		},
		onVariableDeclarator(node) {
			if (node.init) onStatement(node.init, node);
		},
		onClassBody(node) {
			for (const child of node.body) if ((child.type === "PropertyDefinition" || child.type === "ClassProperty" || child.type === "ClassPrivateProperty") && child.value) onStatement(child.value);
		},
		onIfStatement(node, branches) {
			onBranch("if", node, branches);
			onStatement(node);
		},
		onConditionalExpression(node) {
			onBranch("cond-expr", node, [node.consequent, node.alternate]);
		},
		onLogicalExpression(node, branches) {
			onBranch("binary-expr", node, branches);
		},
		onSwitchStatement(node, cases) {
			onBranch("switch", node, cases);
			onStatement(node);
		},
		onAssignmentPattern(node) {
			onBranch("default-arg", node, [node.right]);
		}
	});
	locator.reset();
	return coverageMapData;
	function onFunction(node, positions) {
		if (onIgnore(node, "function")) return;
		const loc = locator.getLoc(positions.loc);
		if (loc === null) return;
		const decl = locator.getLoc(positions.decl);
		if (decl === null) return;
		const covered = getCount({
			startOffset: node.start + wrapperLength,
			endOffset: node.end + wrapperLength
		}, ranges);
		if (options.ignoreSourceCode) {
			const current = locator.getLoc(node) || loc;
			const sources = locator.getSourceLines(current, getSourceFilename(current));
			if (sources != null && options.ignoreSourceCode(sources, "function", {
				start: {
					line: current.start.line,
					column: current.start.column
				},
				end: {
					line: current.end.line,
					column: current.end.column
				}
			})) return;
		}
		addFunction({
			coverageMapData,
			covered,
			loc,
			decl,
			filename: getSourceFilename(loc),
			name: getFunctionName(node)
		});
	}
	function onStatement(node, parent) {
		if (onIgnore(parent || node, "statement")) return;
		const loc = locator.getLoc(node);
		if (loc === null) return;
		const covered = getCount({
			startOffset: (parent || node).start + wrapperLength,
			endOffset: (parent || node).end + wrapperLength
		}, ranges);
		if (options.ignoreSourceCode) {
			const current = parent && locator.getLoc(parent) || loc;
			const sources = locator.getSourceLines(current, getSourceFilename(current));
			if (sources != null && options.ignoreSourceCode(sources, "statement", {
				start: {
					line: current.start.line,
					column: current.start.column
				},
				end: {
					line: current.end.line,
					column: current.end.column
				}
			})) return;
		}
		addStatement({
			coverageMapData,
			loc,
			covered,
			filename: getSourceFilename(loc)
		});
	}
	function onBranch(type, node, branches) {
		if (onIgnore(node, "branch")) return;
		const loc = locator.getLoc(node);
		if (loc === null) return;
		const locations = [];
		const covered = [];
		for (const branch of branches) {
			if (!branch) {
				locations.push({
					start: {
						line: void 0,
						column: void 0
					},
					end: {
						line: void 0,
						coolumn: void 0
					}
				});
				const count = getCount({
					startOffset: node.start + wrapperLength,
					endOffset: node.end + wrapperLength
				}, ranges);
				const previous = covered.at(-1) || 0;
				covered.push(count - previous);
				continue;
			}
			const location = locator.getLoc(branch);
			if (location !== null) locations.push(location);
			const bias = branch.type === "BlockStatement" ? 1 : 0;
			covered.push(getCount({
				startOffset: branch.start + bias + wrapperLength,
				endOffset: branch.end - bias + wrapperLength
			}, ranges));
		}
		if (type === "if") {
			if (locations.length > 0) locations[0] = loc;
		}
		if (locations.length === 0) return;
		if (options.ignoreSourceCode) {
			const sources = locator.getSourceLines(loc, getSourceFilename(loc));
			if (sources != null && options.ignoreSourceCode(sources, "branch", {
				start: {
					line: loc.start.line,
					column: loc.start.column
				},
				end: {
					line: loc.end.line,
					column: loc.end.column
				}
			})) return;
		}
		addBranch({
			coverageMapData,
			loc,
			locations,
			type,
			covered,
			filename: getSourceFilename(loc)
		});
	}
	function getSourceFilename(position) {
		const sourceFilename = position.start.filename || position.end.filename;
		if (!sourceFilename) throw new Error(`Missing original filename for ${JSON.stringify(position, null, 2)}`);
		if (sourceFilename.startsWith("file://")) return fileURLToPath(sourceFilename);
		return resolve(directory, sourceFilename);
	}
	function onIgnore(node, type) {
		if (!options.ignoreNode) return false;
		const scope = options.ignoreNode(node, type);
		if (scope === "ignore-this-and-nested-nodes") walker.onIgnore(node);
		return scope;
	}
}
function setCovered(node) {
	node.__covered = true;
}
function isCovered(node) {
	return node.__covered === true;
}

//#endregion
export { convert, convert as default };