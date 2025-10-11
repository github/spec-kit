//#region src/utils.ts
const postfixRE = /[?#].*$/;
function cleanUrl(url) {
	return url.replace(postfixRE, "");
}
function extractQueryWithoutFragment(url) {
	const questionMarkIndex = url.indexOf("?");
	if (questionMarkIndex === -1) return "";
	const fragmentIndex = url.indexOf("#", questionMarkIndex);
	if (fragmentIndex === -1) return url.substring(questionMarkIndex);
	else return url.substring(questionMarkIndex, fragmentIndex);
}

//#endregion
//#region src/composable-filters.ts
var And = class {
	kind;
	args;
	constructor(...args) {
		if (args.length === 0) throw new Error("`And` expects at least one operand");
		this.args = args;
		this.kind = "and";
	}
};
var Or = class {
	kind;
	args;
	constructor(...args) {
		if (args.length === 0) throw new Error("`Or` expects at least one operand");
		this.args = args;
		this.kind = "or";
	}
};
var Not = class {
	kind;
	expr;
	constructor(expr) {
		this.expr = expr;
		this.kind = "not";
	}
};
var Id = class {
	kind;
	pattern;
	params;
	constructor(pattern, params) {
		this.pattern = pattern;
		this.kind = "id";
		this.params = params ?? { cleanUrl: false };
	}
};
var ModuleType = class {
	kind;
	pattern;
	constructor(pattern) {
		this.pattern = pattern;
		this.kind = "moduleType";
	}
};
var Code = class {
	kind;
	pattern;
	constructor(expr) {
		this.pattern = expr;
		this.kind = "code";
	}
};
var Query = class {
	kind;
	key;
	pattern;
	constructor(key, pattern) {
		this.pattern = pattern;
		this.key = key;
		this.kind = "query";
	}
};
var Include = class {
	kind;
	expr;
	constructor(expr) {
		this.expr = expr;
		this.kind = "include";
	}
};
var Exclude = class {
	kind;
	expr;
	constructor(expr) {
		this.expr = expr;
		this.kind = "exclude";
	}
};
function and(...args) {
	return new And(...args);
}
function or(...args) {
	return new Or(...args);
}
function not(expr) {
	return new Not(expr);
}
function id(pattern, params) {
	return new Id(pattern, params);
}
function moduleType(pattern) {
	return new ModuleType(pattern);
}
function code(pattern) {
	return new Code(pattern);
}
function query(key, pattern) {
	return new Query(key, pattern);
}
function include(expr) {
	return new Include(expr);
}
function exclude(expr) {
	return new Exclude(expr);
}
/**
* convert a queryObject to FilterExpression like
* ```js
*   and(query(k1, v1), query(k2, v2))
* ```
* @param queryFilterObject The query filter object needs to be matched.
* @returns a `And` FilterExpression
*/
function queries(queryFilter) {
	let arr = Object.entries(queryFilter).map(([key, value]) => {
		return new Query(key, value);
	});
	return and(...arr);
}
function interpreter(exprs, code$1, id$1, moduleType$1) {
	let arr = [];
	if (Array.isArray(exprs)) arr = exprs;
	else arr = [exprs];
	return interpreterImpl(arr, code$1, id$1, moduleType$1);
}
function interpreterImpl(expr, code$1, id$1, moduleType$1, ctx = {}) {
	let hasInclude = false;
	for (const e of expr) switch (e.kind) {
		case "include": {
			hasInclude = true;
			if (exprInterpreter(e.expr, code$1, id$1, moduleType$1, ctx)) return true;
			break;
		}
		case "exclude": {
			if (exprInterpreter(e.expr, code$1, id$1, moduleType$1)) return false;
			break;
		}
	}
	return !hasInclude;
}
function exprInterpreter(expr, code$1, id$1, moduleType$1, ctx = {}) {
	switch (expr.kind) {
		case "and": return expr.args.every((e) => exprInterpreter(e, code$1, id$1, moduleType$1, ctx));
		case "or": return expr.args.some((e) => exprInterpreter(e, code$1, id$1, moduleType$1, ctx));
		case "not": return !exprInterpreter(expr.expr, code$1, id$1, moduleType$1, ctx);
		case "id": {
			if (id$1 === void 0) throw new Error("`id` is required for `id` expression");
			if (expr.params.cleanUrl) id$1 = cleanUrl(id$1);
			return typeof expr.pattern === "string" ? id$1 === expr.pattern : expr.pattern.test(id$1);
		}
		case "moduleType": {
			if (moduleType$1 === void 0) throw new Error("`moduleType` is required for `moduleType` expression");
			return moduleType$1 === expr.pattern;
		}
		case "code": {
			if (code$1 === void 0) throw new Error("`code` is required for `code` expression");
			return typeof expr.pattern === "string" ? code$1.includes(expr.pattern) : expr.pattern.test(code$1);
		}
		case "query": {
			if (id$1 === void 0) throw new Error("`id` is required for `Query` expression");
			if (!ctx.urlSearchParamsCache) {
				let queryString = extractQueryWithoutFragment(id$1);
				ctx.urlSearchParamsCache = new URLSearchParams(queryString);
			}
			let urlParams = ctx.urlSearchParamsCache;
			if (typeof expr.pattern === "boolean") if (expr.pattern) return urlParams.has(expr.key);
			else return !urlParams.has(expr.key);
			else if (typeof expr.pattern === "string") return urlParams.get(expr.key) === expr.pattern;
			else return expr.pattern.test(urlParams.get(expr.key) ?? "");
		}
		default: throw new Error(`Expression ${JSON.stringify(expr)} is not expected.`);
	}
}

//#endregion
//#region src/simple-filters.ts
/**
* Constructs a RegExp that matches the exact string specified.
*
* This is useful for plugin hook filters.
*
* @param str the string to match.
* @param flags flags for the RegExp.
*
* @example
* ```ts
* import { exactRegex } from '@rolldown/pluginutils';
* const plugin = {
*   name: 'plugin',
*   resolveId: {
*     filter: { id: exactRegex('foo') },
*     handler(id) {} // will only be called for `foo`
*   }
* }
* ```
*/
function exactRegex(str, flags) {
	return new RegExp(`^${escapeRegex(str)}$`, flags);
}
/**
* Constructs a RegExp that matches a value that has the specified prefix.
*
* This is useful for plugin hook filters.
*
* @param str the string to match.
* @param flags flags for the RegExp.
*
* @example
* ```ts
* import { prefixRegex } from '@rolldown/pluginutils';
* const plugin = {
*   name: 'plugin',
*   resolveId: {
*     filter: { id: prefixRegex('foo') },
*     handler(id) {} // will only be called for IDs starting with `foo`
*   }
* }
* ```
*/
function prefixRegex(str, flags) {
	return new RegExp(`^${escapeRegex(str)}`, flags);
}
const escapeRegexRE = /[-/\\^$*+?.()|[\]{}]/g;
function escapeRegex(str) {
	return str.replace(escapeRegexRE, "\\$&");
}
function makeIdFiltersToMatchWithQuery(input) {
	if (!Array.isArray(input)) return makeIdFilterToMatchWithQuery(input);
	return input.map((i) => makeIdFilterToMatchWithQuery(i));
}
function makeIdFilterToMatchWithQuery(input) {
	if (typeof input === "string") return `${input}{?*,}`;
	return makeRegexIdFilterToMatchWithQuery(input);
}
function makeRegexIdFilterToMatchWithQuery(input) {
	return new RegExp(input.source.replace(/(?<!\\)\$/g, "(?:\\?.*)?$"), input.flags);
}

//#endregion
export { and, code, exactRegex, exclude, exprInterpreter, id, include, interpreter, interpreterImpl, makeIdFiltersToMatchWithQuery, moduleType, not, or, prefixRegex, queries, query };