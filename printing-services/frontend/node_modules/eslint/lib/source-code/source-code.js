/**
 * @fileoverview Abstraction of JavaScript source code.
 * @author Nicholas C. Zakas
 */
"use strict";

//------------------------------------------------------------------------------
// Requirements
//------------------------------------------------------------------------------

const
    { isCommentToken } = require("@eslint-community/eslint-utils"),
    TokenStore = require("./token-store"),
    astUtils = require("../shared/ast-utils"),
    Traverser = require("../shared/traverser"),
    globals = require("../../conf/globals"),
    {
        directivesPattern
    } = require("../shared/directives"),

    /* eslint-disable-next-line n/no-restricted-require -- Too messy to figure out right now. */
    ConfigCommentParser = require("../linter/config-comment-parser"),
    eslintScope = require("eslint-scope");

//------------------------------------------------------------------------------
// Type Definitions
//------------------------------------------------------------------------------

/** @typedef {import("eslint-scope").Variable} Variable */

//------------------------------------------------------------------------------
// Private
//------------------------------------------------------------------------------

const commentParser = new ConfigCommentParser();

/**
 * Validates that the given AST has the required information.
 * @param {ASTNode} ast The Program node of the AST to check.
 * @throws {Error} If the AST doesn't contain the correct information.
 * @returns {void}
 * @private
 */
function validate(ast) {
    if (!ast.tokens) {
        throw new Error("AST is missing the tokens array.");
    }

    if (!ast.comments) {
        throw new Error("AST is missing the comments array.");
    }

    if (!ast.loc) {
        throw new Error("AST is missing location information.");
    }

    if (!ast.range) {
        throw new Error("AST is missing range information");
    }
}

/**
 * Retrieves globals for the given ecmaVersion.
 * @param {number} ecmaVersion The version to retrieve globals for.
 * @returns {Object} The globals for the given ecmaVersion.
 */
function getGlobalsForEcmaVersion(ecmaVersion) {

    switch (ecmaVersion) {
        case 3:
            return globals.es3;

        case 5:
            return globals.es5;

        default:
            if (ecmaVersion < 2015) {
                return globals[`es${ecmaVersion + 2009}`];
            }

            return globals[`es${ecmaVersion}`];
    }
}

/**
 * Check to see if its a ES6 export declaration.
 * @param {ASTNode} astNode An AST node.
 * @returns {boolean} whether the given node represents an export declaration.
 * @private
 */
function looksLikeExport(astNode) {
    return astNode.type === "ExportDefaultDeclaration" || astNode.type === "ExportNamedDeclaration" ||
        astNode.type === "ExportAllDeclaration" || astNode.type === "ExportSpecifier";
}

/**
 * Merges two sorted lists into a larger sorted list in O(n) time.
 * @param {Token[]} tokens The list of tokens.
 * @param {Token[]} comments The list of comments.
 * @returns {Token[]} A sorted list of tokens and comments.
 * @private
 */
function sortedMerge(tokens, comments) {
    const result = [];
    let tokenIndex = 0;
    let commentIndex = 0;

    while (tokenIndex < tokens.length || commentIndex < comments.length) {
        if (commentIndex >= comments.length || tokenIndex < tokens.length && tokens[tokenIndex].range[0] < comments[commentIndex].range[0]) {
            result.push(tokens[tokenIndex++]);
        } else {
            result.push(comments[commentIndex++]);
        }
    }

    return result;
}

/**
 * Normalizes a value for a global in a config
 * @param {(boolean|string|null)} configuredValue The value given for a global in configuration or in
 * a global directive comment
 * @returns {("readable"|"writeable"|"off")} The value normalized as a string
 * @throws Error if global value is invalid
 */
function normalizeConfigGlobal(configuredValue) {
    switch (configuredValue) {
        case "off":
            return "off";

        case true:
        case "true":
        case "writeable":
        case "writable":
            return "writable";

        case null:
        case false:
        case "false":
        case "readable":
        case "readonly":
            return "readonly";

        default:
            throw new Error(`'${configuredValue}' is not a valid configuration for a global (use 'readonly', 'writable', or 'off')`);
    }
}

/**
 * Determines if two nodes or tokens overlap.
 * @param {ASTNode|Token} first The first node or token to check.
 * @param {ASTNode|Token} second The second node or token to check.
 * @returns {boolean} True if the two nodes or tokens overlap.
 * @private
 */
function nodesOrTokensOverlap(first, second) {
    return (first.range[0] <= second.range[0] && first.range[1] >= second.range[0]) ||
        (second.range[0] <= first.range[0] && second.range[1] >= first.range[0]);
}

/**
 * Determines if two nodes or tokens have at least one whitespace character
 * between them. Order does not matter. Returns false if the given nodes or
 * tokens overlap.
 * @param {SourceCode} sourceCode The source code object.
 * @param {ASTNode|Token} first The first node or token to check between.
 * @param {ASTNode|Token} second The second node or token to check between.
 * @param {boolean} checkInsideOfJSXText If `true` is present, check inside of JSXText tokens for backward compatibility.
 * @returns {boolean} True if there is a whitespace character between
 * any of the tokens found between the two given nodes or tokens.
 * @public
 */
function isSpaceBetween(sourceCode, first, second, checkInsideOfJSXText) {
    if (nodesOrTokensOverlap(first, second)) {
        return false;
    }

    const [startingNodeOrToken, endingNodeOrToken] = first.range[1] <= second.range[0]
        ? [first, second]
        : [second, first];
    const firstToken = sourceCode.getLastToken(startingNodeOrToken) || startingNodeOrToken;
    const finalToken = sourceCode.getFirstToken(endingNodeOrToken) || endingNodeOrToken;
    let currentToken = firstToken;

    while (currentToken !== finalToken) {
        const nextToken = sourceCode.getTokenAfter(currentToken, { includeComments: true });

        if (
            currentToken.range[1] !== nextToken.range[0] ||

                /*
                 * For backward compatibility, check spaces in JSXText.
                 * https://github.com/eslint/eslint/issues/12614
                 */
                (
                    checkInsideOfJSXText &&
                    nextToken !== finalToken &&
                    nextToken.type === "JSXText" &&
                    /\s/u.test(nextToken.value)
                )
        ) {
            return true;
        }

        currentToken = nextToken;
    }

    return false;
}

//-----------------------------------------------------------------------------
// Directive Comments
//-----------------------------------------------------------------------------

/**
 * Ensures that variables representing built-in properties of the Global Object,
 * and any globals declared by special block comments, are present in the global
 * scope.
 * @param {Scope} globalScope The global scope.
 * @param {Object|undefined} configGlobals The globals declared in configuration
 * @param {Object|undefined} inlineGlobals The globals declared in the source code
 * @returns {void}
 */
function addDeclaredGlobals(globalScope, configGlobals = {}, inlineGlobals = {}) {

    // Define configured global variables.
    for (const id of new Set([...Object.keys(configGlobals), ...Object.keys(inlineGlobals)])) {

        /*
         * `normalizeConfigGlobal` will throw an error if a configured global value is invalid. However, these errors would
         * typically be caught when validating a config anyway (validity for inline global comments is checked separately).
         */
        const configValue = configGlobals[id] === void 0 ? void 0 : normalizeConfigGlobal(configGlobals[id]);
        const commentValue = inlineGlobals[id] && inlineGlobals[id].value;
        const value = commentValue || configValue;
        const sourceComments = inlineGlobals[id] && inlineGlobals[id].comments;

        if (value === "off") {
            continue;
        }

        let variable = globalScope.set.get(id);

        if (!variable) {
            variable = new eslintScope.Variable(id, globalScope);

            globalScope.variables.push(variable);
            globalScope.set.set(id, variable);
        }

        variable.eslintImplicitGlobalSetting = configValue;
        variable.eslintExplicitGlobal = sourceComments !== void 0;
        variable.eslintExplicitGlobalComments = sourceComments;
        variable.writeable = (value === "writable");
    }

    /*
     * "through" contains all references which definitions cannot be found.
     * Since we augment the global scope using configuration, we need to update
     * references and remove the ones that were added by configuration.
     */
    globalScope.through = globalScope.through.filter(reference => {
        const name = reference.identifier.name;
        const variable = globalScope.set.get(name);

        if (variable) {

            /*
             * Links the variable and the reference.
             * And this reference is removed from `Scope#through`.
             */
            reference.resolved = variable;
            variable.references.push(reference);

            return false;
        }

        return true;
    });
}

/**
 * Sets the given variable names as exported so they won't be triggered by
 * the `no-unused-vars` rule.
 * @param {eslint.Scope} globalScope The global scope to define exports in.
 * @param {Record<string,string>} variables An object whose keys are the variable
 *      names to export.
 * @returns {void}
 */
function markExportedVariables(globalScope, variables) {

    Object.keys(variables).forEach(name => {
        const variable = globalScope.set.get(name);

        if (variable) {
            variable.eslintUsed = true;
            variable.eslintExported = true;
        }
    });

}

//------------------------------------------------------------------------------
// Public Interface
//------------------------------------------------------------------------------

const caches = Symbol("caches");

/**
 * Represents parsed source code.
 */
class SourceCode extends TokenStore {

    /**
     * @param {string|Object} textOrConfig The source code text or config object.
     * @param {string} textOrConfig.text The source code text.
     * @param {ASTNode} textOrConfig.ast The Program node of the AST representing the code. This AST should be created from the text that BOM was stripped.
     * @param {Object|null} textOrConfig.parserServices The parser services.
     * @param {ScopeManager|null} textOrConfig.scopeManager The scope of this source code.
     * @param {Object|null} textOrConfig.visitorKeys The visitor keys to traverse AST.
     * @param {ASTNode} [astIfNoConfig] The Program node of the AST representing the code. This AST should be created from the text that BOM was stripped.
     */
    constructor(textOrConfig, astIfNoConfig) {
        let text, ast, parserServices, scopeManager, visitorKeys;

        // Process overloading.
        if (typeof textOrConfig === "string") {
            text = textOrConfig;
            ast = astIfNoConfig;
        } else if (typeof textOrConfig === "object" && textOrConfig !== null) {
            text = textOrConfig.text;
            ast = textOrConfig.ast;
            parserServices = textOrConfig.parserServices;
            scopeManager = textOrConfig.scopeManager;
            visitorKeys = textOrConfig.visitorKeys;
        }

        validate(ast);
        super(ast.tokens, ast.comments);

        /**
         * General purpose caching for the class.
         */
        this[caches] = new Map([
            ["scopes", new WeakMap()],
            ["vars", new Map()],
            ["configNodes", void 0]
        ]);

        /**
         * The flag to indicate that the source code has Unicode BOM.
         * @type {boolean}
         */
        this.hasBOM = (text.charCodeAt(0) === 0xFEFF);

        /**
         * The original text source code.
         * BOM was stripped from this text.
         * @type {string}
         */
        this.text = (this.hasBOM ? text.slice(1) : text);

        /**
         * The parsed AST for the source code.
         * @type {ASTNode}
         */
        this.ast = ast;

        /**
         * The parser services of this source code.
         * @type {Object}
         */
        this.parserServices = parserServices || {};

        /**
         * The scope of this source code.
         * @type {ScopeManager|null}
         */
        this.scopeManager = scopeManager || null;

        /**
         * The visitor keys to traverse AST.
         * @type {Object}
         */
        this.visitorKeys = visitorKeys || Traverser.DEFAULT_VISITOR_KEYS;

        // Check the source text for the presence of a shebang since it is parsed as a standard line comment.
        const shebangMatched = this.text.match(astUtils.shebangPattern);
        const hasShebang = shebangMatched && ast.comments.length && ast.comments[0].value === shebangMatched[1];

        if (hasShebang) {
            ast.comments[0].type = "Shebang";
        }

        this.tokensAndComments = sortedMerge(ast.tokens, ast.comments);

        /**
         * The source code split into lines according to ECMA-262 specification.
         * This is done to avoid each rule needing to do so separately.
         * @type {string[]}
         */
        this.lines = [];
        this.lineStartIndices = [0];

        const lineEndingPattern = astUtils.createGlobalLinebreakMatcher();
        let match;

        /*
         * Previously, this was implemented using a regex that
         * matched a sequence of non-linebreak characters followed by a
         * linebreak, then adding the lengths of the matches. However,
         * this caused a catastrophic backtracking issue when the end
         * of a file contained a large number of non-newline characters.
         * To avoid this, the current implementation just matches newlines
         * and uses match.index to get the correct line start indices.
         */
        while ((match = lineEndingPattern.exec(this.text))) {
            this.lines.push(this.text.slice(this.lineStartIndices[this.lineStartIndices.length - 1], match.index));
            this.lineStartIndices.push(match.index + match[0].length);
        }
        this.lines.push(this.text.slice(this.lineStartIndices[this.lineStartIndices.length - 1]));

        // Cache for comments found using getComments().
        this._commentCache = new WeakMap();

        // don't allow further modification of this object
        Object.freeze(this);
        Object.freeze(this.lines);
    }

    /**
     * Split the source code into multiple lines based on the line delimiters.
     * @param {string} text Source code as a string.
     * @returns {string[]} Array of source code lines.
     * @public
     */
    static splitLines(text) {
        return text.split(astUtils.createGlobalLinebreakMatcher());
    }

    /**
     * Gets the source code for the given node.
     * @param {ASTNode} [node] The AST node to get the text for.
     * @param {int} [beforeCount] The number of characters before the node to retrieve.
     * @param {int} [afterCount] The number of characters after the node to retrieve.
     * @returns {string} The text representing the AST node.
     * @public
     */
    getText(node, beforeCount, afterCount) {
        if (node) {
            return this.text.slice(Math.max(node.range[0] - (beforeCount || 0), 0),
                node.range[1] + (afterCount || 0));
        }
        return this.text;
    }

    /**
     * Gets the entire source text split into an array of lines.
     * @returns {Array} The source text as an array of lines.
     * @public
     */
    getLines() {
        return this.lines;
    }

    /**
     * Retrieves an array containing all comments in the source code.
     * @returns {ASTNode[]} An array of comment nodes.
     * @public
     */
    getAllComments() {
        return this.ast.comments;
    }

    /**
     * Gets all comments for the given node.
     * @param {ASTNode} node The AST node to get the comments for.
     * @returns {Object} An object containing a leading and trailing array
     *      of comments indexed by their position.
     * @public
     * @deprecated replaced by getCommentsBefore(), getCommentsAfter(), and getCommentsInside().
     */
    getComments(node) {
        if (this._commentCache.has(node)) {
            return this._commentCache.get(node);
        }

        const comments = {
            leading: [],
            trailing: []
        };

        /*
         * Return all comments as leading comments of the Program node when
         * there is no executable code.
         */
        if (node.type === "Program") {
            if (node.body.length === 0) {
                comments.leading = node.comments;
            }
        } else {

            /*
             * Return comments as trailing comments of nodes that only contain
             * comments (to mimic the comment attachment behavior present in Espree).
             */
            if ((node.type === "BlockStatement" || node.type === "ClassBody") && node.body.length === 0 ||
                node.type === "ObjectExpression" && node.properties.length === 0 ||
                node.type === "ArrayExpression" && node.elements.length === 0 ||
                node.type === "SwitchStatement" && node.cases.length === 0
            ) {
                comments.trailing = this.getTokens(node, {
                    includeComments: true,
                    filter: isCommentToken
                });
            }

            /*
             * Iterate over tokens before and after node and collect comment tokens.
             * Do not include comments that exist outside of the parent node
             * to avoid duplication.
             */
            let currentToken = this.getTokenBefore(node, { includeComments: true });

            while (currentToken && isCommentToken(currentToken)) {
                if (node.parent && node.parent.type !== "Program" && (currentToken.start < node.parent.start)) {
                    break;
                }
                comments.leading.push(currentToken);
                currentToken = this.getTokenBefore(currentToken, { includeComments: true });
            }

            comments.leading.reverse();

            currentToken = this.getTokenAfter(node, { includeComments: true });

            while (currentToken && isCommentToken(currentToken)) {
                if (node.parent && node.parent.type !== "Program" && (currentToken.end > node.parent.end)) {
                    break;
                }
                comments.trailing.push(currentToken);
                currentToken = this.getTokenAfter(currentToken, { includeComments: true });
            }
        }

        this._commentCache.set(node, comments);
        return comments;
    }

    /**
     * Retrieves the JSDoc comment for a given node.
     * @param {ASTNode} node The AST node to get the comment for.
     * @returns {Token|null} The Block comment token containing the JSDoc comment
     *      for the given node or null if not found.
     * @public
     * @deprecated
     */
    getJSDocComment(node) {

        /**
         * Checks for the presence of a JSDoc comment for the given node and returns it.
         * @param {ASTNode} astNode The AST node to get the comment for.
         * @returns {Token|null} The Block comment token containing the JSDoc comment
         *      for the given node or null if not found.
         * @private
         */
        const findJSDocComment = astNode => {
            const tokenBefore = this.getTokenBefore(astNode, { includeComments: true });

            if (
                tokenBefore &&
                isCommentToken(tokenBefore) &&
                tokenBefore.type === "Block" &&
                tokenBefore.value.charAt(0) === "*" &&
                astNode.loc.start.line - tokenBefore.loc.end.line <= 1
            ) {
                return tokenBefore;
            }

            return null;
        };
        let parent = node.parent;

        switch (node.type) {
            case "ClassDeclaration":
            case "FunctionDeclaration":
                return findJSDocComment(looksLikeExport(parent) ? parent : node);

            case "ClassExpression":
                return findJSDocComment(parent.parent);

            case "ArrowFunctionExpression":
            case "FunctionExpression":
                if (parent.type !== "CallExpression" && parent.type !== "NewExpression") {
                    while (
                        !this.getCommentsBefore(parent).length &&
                        !/Function/u.test(parent.type) &&
                        parent.type !== "MethodDefinition" &&
                        parent.type !== "Property"
                    ) {
                        parent = parent.parent;

                        if (!parent) {
                            break;
                        }
                    }

                    if (parent && parent.type !== "FunctionDeclaration" && parent.type !== "Program") {
                        return findJSDocComment(parent);
                    }
                }

                return findJSDocComment(node);

            // falls through
            default:
                return null;
        }
    }

    /**
     * Gets the deepest node containing a range index.
     * @param {int} index Range index of the desired node.
     * @returns {ASTNode} The node if found or null if not found.
     * @public
     */
    getNodeByRangeIndex(index) {
        let result = null;

        Traverser.traverse(this.ast, {
            visitorKeys: this.visitorKeys,
            enter(node) {
                if (node.range[0] <= index && index < node.range[1]) {
                    result = node;
                } else {
                    this.skip();
                }
            },
            leave(node) {
                if (node === result) {
                    this.break();
                }
            }
        });

        return result;
    }

    /**
     * Determines if two nodes or tokens have at least one whitespace character
     * between them. Order does not matter. Returns false if the given nodes or
     * tokens overlap.
     * @param {ASTNode|Token} first The first node or token to check between.
     * @param {ASTNode|Token} second The second node or token to check between.
     * @returns {boolean} True if there is a whitespace character between
     * any of the tokens found between the two given nodes or tokens.
     * @public
     */
    isSpaceBetween(first, second) {
        return isSpaceBetween(this, first, second, false);
    }

    /**
     * Determines if two nodes or tokens have at least one whitespace character
     * between them. Order does not matter. Returns false if the given nodes or
     * tokens overlap.
     * For backward compatibility, this method returns true if there are
     * `JSXText` tokens that contain whitespaces between the two.
     * @param {ASTNode|Token} first The first node or token to check between.
     * @param {ASTNode|Token} second The second node or token to check between.
     * @returns {boolean} True if there is a whitespace character between
     * any of the tokens found between the two given nodes or tokens.
     * @deprecated in favor of isSpaceBetween().
     * @public
     */
    isSpaceBetweenTokens(first, second) {
        return isSpaceBetween(this, first, second, true);
    }

    /**
     * Converts a source text index into a (line, column) pair.
     * @param {number} index The index of a character in a file
     * @throws {TypeError} If non-numeric index or index out of range.
     * @returns {Object} A {line, column} location object with a 0-indexed column
     * @public
     */
    getLocFromIndex(index) {
        if (typeof index !== "number") {
            throw new TypeError("Expected `index` to be a number.");
        }

        if (index < 0 || index > this.text.length) {
            throw new RangeError(`Index out of range (requested index ${index}, but source text has length ${this.text.length}).`);
        }

        /*
         * For an argument of this.text.length, return the location one "spot" past the last character
         * of the file. If the last character is a linebreak, the location will be column 0 of the next
         * line; otherwise, the location will be in the next column on the same line.
         *
         * See getIndexFromLoc for the motivation for this special case.
         */
        if (index === this.text.length) {
            return { line: this.lines.length, column: this.lines[this.lines.length - 1].length };
        }

        /*
         * To figure out which line index is on, determine the last place at which index could
         * be inserted into lineStartIndices to keep the list sorted.
         */
        const lineNumber = index >= this.lineStartIndices[this.lineStartIndices.length - 1]
            ? this.lineStartIndices.length
            : this.lineStartIndices.findIndex(el => index < el);

        return { line: lineNumber, column: index - this.lineStartIndices[lineNumber - 1] };
    }

    /**
     * Converts a (line, column) pair into a range index.
     * @param {Object} loc A line/column location
     * @param {number} loc.line The line number of the location (1-indexed)
     * @param {number} loc.column The column number of the location (0-indexed)
     * @throws {TypeError|RangeError} If `loc` is not an object with a numeric
     *   `line` and `column`, if the `line` is less than or equal to zero or
     *   the line or column is out of the expected range.
     * @returns {number} The range index of the location in the file.
     * @public
     */
    getIndexFromLoc(loc) {
        if (typeof loc !== "object" || typeof loc.line !== "number" || typeof loc.column !== "number") {
            throw new TypeError("Expected `loc` to be an object with numeric `line` and `column` properties.");
        }

        if (loc.line <= 0) {
            throw new RangeError(`Line number out of range (line ${loc.line} requested). Line numbers should be 1-based.`);
        }

        if (loc.line > this.lineStartIndices.length) {
            throw new RangeError(`Line number out of range (line ${loc.line} requested, but only ${this.lineStartIndices.length} lines present).`);
        }

        const lineStartIndex = this.lineStartIndices[loc.line - 1];
        const lineEndIndex = loc.line === this.lineStartIndices.length ? this.text.length : this.lineStartIndices[loc.line];
        const positionIndex = lineStartIndex + loc.column;

        /*
         * By design, getIndexFromLoc({ line: lineNum, column: 0 }) should return the start index of
         * the given line, provided that the line number is valid element of this.lines. Since the
         * last element of this.lines is an empty string for files with trailing newlines, add a
         * special case where getting the index for the first location after the end of the file
         * will return the length of the file, rather than throwing an error. This allows rules to
         * use getIndexFromLoc consistently without worrying about edge cases at the end of a file.
         */
        if (
            loc.line === this.lineStartIndices.length && positionIndex > lineEndIndex ||
            loc.line < this.lineStartIndices.length && positionIndex >= lineEndIndex
        ) {
            throw new RangeError(`Column number out of range (column ${loc.column} requested, but the length of line ${loc.line} is ${lineEndIndex - lineStartIndex}).`);
        }

        return positionIndex;
    }

    /**
     * Gets the scope for the given node
     * @param {ASTNode} currentNode The node to get the scope of
     * @returns {eslint-scope.Scope} The scope information for this node
     * @throws {TypeError} If the `currentNode` argument is missing.
     */
    getScope(currentNode) {

        if (!currentNode) {
            throw new TypeError("Missing required argument: node.");
        }

        // check cache first
        const cache = this[caches].get("scopes");
        const cachedScope = cache.get(currentNode);

        if (cachedScope) {
            return cachedScope;
        }

        // On Program node, get the outermost scope to avoid return Node.js special function scope or ES modules scope.
        const inner = currentNode.type !== "Program";

        for (let node = currentNode; node; node = node.parent) {
            const scope = this.scopeManager.acquire(node, inner);

            if (scope) {
                if (scope.type === "function-expression-name") {
                    cache.set(currentNode, scope.childScopes[0]);
                    return scope.childScopes[0];
                }

                cache.set(currentNode, scope);
                return scope;
            }
        }

        cache.set(currentNode, this.scopeManager.scopes[0]);
        return this.scopeManager.scopes[0];
    }

    /**
     * Get the variables that `node` defines.
     * This is a convenience method that passes through
     * to the same method on the `scopeManager`.
     * @param {ASTNode} node The node for which the variables are obtained.
     * @returns {Array<Variable>} An array of variable nodes representing
     *      the variables that `node` defines.
     */
    getDeclaredVariables(node) {
        return this.scopeManager.getDeclaredVariables(node);
    }

    /* eslint-disable class-methods-use-this -- node is owned by SourceCode */
    /**
     * Gets all the ancestors of a given node
     * @param {ASTNode} node The node
     * @returns {Array<ASTNode>} All the ancestor nodes in the AST, not including the provided node, starting
     * from the root node at index 0 and going inwards to the parent node.
     * @throws {TypeError} When `node` is missing.
     */
    getAncestors(node) {

        if (!node) {
            throw new TypeError("Missing required argument: node.");
        }

        const ancestorsStartingAtParent = [];

        for (let ancestor = node.parent; ancestor; ancestor = ancestor.parent) {
            ancestorsStartingAtParent.push(ancestor);
        }

        return ancestorsStartingAtParent.reverse();
    }
    /* eslint-enable class-methods-use-this -- node is owned by SourceCode */

    /**
     * Marks a variable as used in the current scope
     * @param {string} name The name of the variable to mark as used.
     * @param {ASTNode} [refNode] The closest node to the variable reference.
     * @returns {boolean} True if the variable was found and marked as used, false if not.
     */
    markVariableAsUsed(name, refNode = this.ast) {

        const currentScope = this.getScope(refNode);
        let initialScope = currentScope;

        /*
         * When we are in an ESM or CommonJS module, we need to start searching
         * from the top-level scope, not the global scope. For ESM the top-level
         * scope is the module scope; for CommonJS the top-level scope is the
         * outer function scope.
         *
         * Without this check, we might miss a variable declared with `var` at
         * the top-level because it won't exist in the global scope.
         */
        if (
            currentScope.type === "global" &&
            currentScope.childScopes.length > 0 &&

            // top-level scopes refer to a `Program` node
            currentScope.childScopes[0].block === this.ast
        ) {
            initialScope = currentScope.childScopes[0];
        }

        for (let scope = initialScope; scope; scope = scope.upper) {
            const variable = scope.variables.find(scopeVar => scopeVar.name === name);

            if (variable) {
                variable.eslintUsed = true;
                return true;
            }
        }

        return false;
    }


    /**
     * Returns an array of all inline configuration nodes found in the
     * source code.
     * @returns {Array<Token>} An array of all inline configuration nodes.
     */
    getInlineConfigNodes() {

        // check the cache first
        let configNodes = this[caches].get("configNodes");

        if (configNodes) {
            return configNodes;
        }

        // calculate fresh config nodes
        configNodes = this.ast.comments.filter(comment => {

            // shebang comments are never directives
            if (comment.type === "Shebang") {
                return false;
            }

            const { directivePart } = commentParser.extractDirectiveComment(comment.value);

            const directiveMatch = directivesPattern.exec(directivePart);

            if (!directiveMatch) {
                return false;
            }

            // only certain comment types are supported as line comments
            return comment.type !== "Line" || !!/^eslint-disable-(next-)?line$/u.test(directiveMatch[1]);
        });

        this[caches].set("configNodes", configNodes);

        return configNodes;
    }

    /**
     * Applies language options sent in from the core.
     * @param {Object} languageOptions The language options for this run.
     * @returns {void}
     */
    applyLanguageOptions(languageOptions) {

        /*
         * Add configured globals and language globals
         *
         * Using Object.assign instead of object spread for performance reasons
         * https://github.com/eslint/eslint/issues/16302
         */
        const configGlobals = Object.assign(
            Object.create(null), // https://github.com/eslint/eslint/issues/18363
            getGlobalsForEcmaVersion(languageOptions.ecmaVersion),
            languageOptions.sourceType === "commonjs" ? globals.commonjs : void 0,
            languageOptions.globals
        );
        const varsCache = this[caches].get("vars");

        varsCache.set("configGlobals", configGlobals);
    }

    /**
     * Applies configuration found inside of the source code. This method is only
     * called when ESLint is running with inline configuration allowed.
     * @returns {{problems:Array<Problem>,configs:{config:FlatConfigArray,node:ASTNode}}} Information
     *      that ESLint needs to further process the inline configuration.
     */
    applyInlineConfig() {

        const problems = [];
        const configs = [];
        const exportedVariables = {};
        const inlineGlobals = Object.create(null);

        this.getInlineConfigNodes().forEach(comment => {

            const { directiveText, directiveValue } = commentParser.parseDirective(comment);

            switch (directiveText) {
                case "exported":
                    Object.assign(exportedVariables, commentParser.parseStringConfig(directiveValue, comment));
                    break;

                case "globals":
                case "global":
                    for (const [id, { value }] of Object.entries(commentParser.parseStringConfig(directiveValue, comment))) {
                        let normalizedValue;

                        try {
                            normalizedValue = normalizeConfigGlobal(value);
                        } catch (err) {
                            problems.push({
                                ruleId: null,
                                loc: comment.loc,
                                message: err.message
                            });
                            continue;
                        }

                        if (inlineGlobals[id]) {
                            inlineGlobals[id].comments.push(comment);
                            inlineGlobals[id].value = normalizedValue;
                        } else {
                            inlineGlobals[id] = {
                                comments: [comment],
                                value: normalizedValue
                            };
                        }
                    }
                    break;

                case "eslint": {
                    const parseResult = commentParser.parseJsonConfig(directiveValue, comment.loc);

                    if (parseResult.success) {
                        configs.push({
                            config: {
                                rules: parseResult.config
                            },
                            node: comment
                        });
                    } else {
                        problems.push(parseResult.error);
                    }

                    break;
                }

                // no default
            }
        });

        // save all the new variables for later
        const varsCache = this[caches].get("vars");

        varsCache.set("inlineGlobals", inlineGlobals);
        varsCache.set("exportedVariables", exportedVariables);

        return {
            configs,
            problems
        };
    }

    /**
     * Called by ESLint core to indicate that it has finished providing
     * information. We now add in all the missing variables and ensure that
     * state-changing methods cannot be called by rules.
     * @returns {void}
     */
    finalize() {

        // Step 1: ensure that all of the necessary variables are up to date
        const varsCache = this[caches].get("vars");
        const globalScope = this.scopeManager.scopes[0];
        const configGlobals = varsCache.get("configGlobals");
        const inlineGlobals = varsCache.get("inlineGlobals");
        const exportedVariables = varsCache.get("exportedVariables");

        addDeclaredGlobals(globalScope, configGlobals, inlineGlobals);

        if (exportedVariables) {
            markExportedVariables(globalScope, exportedVariables);
        }

    }

}

module.exports = SourceCode;
