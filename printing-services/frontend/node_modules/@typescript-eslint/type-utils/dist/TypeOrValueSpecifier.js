"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.typeMatchesSpecifier = exports.typeOrValueSpecifierSchema = void 0;
const typescript_estree_1 = require("@typescript-eslint/typescript-estree");
const path_1 = __importDefault(require("path"));
const tsutils = __importStar(require("ts-api-utils"));
exports.typeOrValueSpecifierSchema = {
    oneOf: [
        {
            type: 'string',
        },
        {
            type: 'object',
            additionalProperties: false,
            properties: {
                from: {
                    type: 'string',
                    enum: ['file'],
                },
                name: {
                    oneOf: [
                        {
                            type: 'string',
                        },
                        {
                            type: 'array',
                            minItems: 1,
                            uniqueItems: true,
                            items: {
                                type: 'string',
                            },
                        },
                    ],
                },
                path: {
                    type: 'string',
                },
            },
            required: ['from', 'name'],
        },
        {
            type: 'object',
            additionalProperties: false,
            properties: {
                from: {
                    type: 'string',
                    enum: ['lib'],
                },
                name: {
                    oneOf: [
                        {
                            type: 'string',
                        },
                        {
                            type: 'array',
                            minItems: 1,
                            uniqueItems: true,
                            items: {
                                type: 'string',
                            },
                        },
                    ],
                },
            },
            required: ['from', 'name'],
        },
        {
            type: 'object',
            additionalProperties: false,
            properties: {
                from: {
                    type: 'string',
                    enum: ['package'],
                },
                name: {
                    oneOf: [
                        {
                            type: 'string',
                        },
                        {
                            type: 'array',
                            minItems: 1,
                            uniqueItems: true,
                            items: {
                                type: 'string',
                            },
                        },
                    ],
                },
                package: {
                    type: 'string',
                },
            },
            required: ['from', 'name', 'package'],
        },
    ],
};
function specifierNameMatches(type, name) {
    if (typeof name === 'string') {
        name = [name];
    }
    if (name.some(item => item === type.intrinsicName)) {
        return true;
    }
    const symbol = type.aliasSymbol ?? type.getSymbol();
    if (symbol === undefined) {
        return false;
    }
    return name.some(item => item === symbol.escapedName);
}
function typeDeclaredInFile(relativePath, declarationFiles, program) {
    if (relativePath === undefined) {
        const cwd = (0, typescript_estree_1.getCanonicalFileName)(program.getCurrentDirectory());
        return declarationFiles.some(declaration => (0, typescript_estree_1.getCanonicalFileName)(declaration.fileName).startsWith(cwd));
    }
    const absolutePath = (0, typescript_estree_1.getCanonicalFileName)(path_1.default.join(program.getCurrentDirectory(), relativePath));
    return declarationFiles.some(declaration => (0, typescript_estree_1.getCanonicalFileName)(declaration.fileName) === absolutePath);
}
function typeDeclaredInPackage(packageName, declarationFiles, program) {
    // Handle scoped packages - if the name starts with @, remove it and replace / with __
    const typesPackageName = packageName.replace(/^@([^/]+)\//, '$1__');
    const matcher = new RegExp(`${packageName}|${typesPackageName}`);
    return declarationFiles.some(declaration => {
        const packageIdName = program.sourceFileToPackageName.get(declaration.path);
        return (packageIdName !== undefined &&
            matcher.test(packageIdName) &&
            program.isSourceFileFromExternalLibrary(declaration));
    });
}
function typeDeclaredInLib(declarationFiles, program) {
    // Assertion: The type is not an error type.
    // Intrinsic type (i.e. string, number, boolean, etc) - Treat it as if it's from lib.
    if (declarationFiles.length === 0) {
        return true;
    }
    return declarationFiles.some(declaration => program.isSourceFileDefaultLibrary(declaration));
}
function typeMatchesSpecifier(type, specifier, program) {
    if (tsutils.isIntrinsicErrorType(type)) {
        return false;
    }
    if (typeof specifier === 'string') {
        return specifierNameMatches(type, specifier);
    }
    if (!specifierNameMatches(type, specifier.name)) {
        return false;
    }
    const declarationFiles = type
        .getSymbol()
        ?.getDeclarations()
        ?.map(declaration => declaration.getSourceFile()) ?? [];
    switch (specifier.from) {
        case 'file':
            return typeDeclaredInFile(specifier.path, declarationFiles, program);
        case 'lib':
            return typeDeclaredInLib(declarationFiles, program);
        case 'package':
            return typeDeclaredInPackage(specifier.package, declarationFiles, program);
    }
}
exports.typeMatchesSpecifier = typeMatchesSpecifier;
//# sourceMappingURL=TypeOrValueSpecifier.js.map