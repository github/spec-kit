# Config Array

by [Nicholas C. Zakas](https://humanwhocodes.com)

If you find this useful, please consider supporting my work with a [donation](https://humanwhocodes.com/donate).

## Description

A config array is a way of managing configurations that are based on glob pattern matching of filenames. Each config array contains the information needed to determine the correct configuration for any file based on the filename. 

## Background

In 2019, I submitted an [ESLint RFC](https://github.com/eslint/rfcs/pull/9) proposing a new way of configuring ESLint. The goal was to streamline what had become an increasingly complicated configuration process. Over several iterations, this proposal was eventually born.

The basic idea is that all configuration, including overrides, can be represented by a single array where each item in the array is a config object. Config objects appearing later in the array override config objects appearing earlier in the array. You can calculate a config for a given file by traversing all config objects in the array to find the ones that match the filename. Matching is done by specifying glob patterns in `files` and `ignores` properties on each config object. Here's an example:

```js
export default [

    // match all JSON files
    {
        name: "JSON Handler",
        files: ["**/*.json"],
        handler: jsonHandler
    },

    // match only package.json
    {
        name: "package.json Handler",
        files: ["package.json"],
        handler: packageJsonHandler
    }
];
```

In this example, there are two config objects: the first matches all JSON files in all directories and the second matches just `package.json` in the base path directory (all the globs are evaluated as relative to a base path that can be specified). When you retrieve a configuration for `foo.json`, only the first config object matches so `handler` is equal to `jsonHandler`; when you retrieve a configuration for `package.json`, `handler` is equal to `packageJsonHandler` (because both config objects match, the second one wins).

## Installation

You can install the package using npm or Yarn:

```bash
npm install @humanwhocodes/config-array --save

# or

yarn add @humanwhocodes/config-array
```

## Usage

First, import the `ConfigArray` constructor:

```js
import { ConfigArray } from "@humanwhocodes/config-array";

// or using CommonJS

const { ConfigArray } = require("@humanwhocodes/config-array");
```

When you create a new instance of `ConfigArray`, you must pass in two arguments: an array of configs and an options object. The array of configs is most likely read in from a configuration file, so here's a typical example:

```js
const configFilename = path.resolve(process.cwd(), "my.config.js");
const { default: rawConfigs } = await import(configFilename);
const configs = new ConfigArray(rawConfigs, {
    
    // the path to match filenames from
    basePath: process.cwd(),

    // additional items in each config
    schema: mySchema
});
```

This example reads in an object or array from `my.config.js` and passes it into the `ConfigArray` constructor as the first argument. The second argument is an object specifying the `basePath` (the directory in which `my.config.js` is found) and a `schema` to define the additional properties of a config object beyond `files`, `ignores`, and `name`.

### Specifying a Schema

The `schema` option is required for you to use additional properties in config objects. The schema is an object that follows the format of an [`ObjectSchema`](https://npmjs.com/package/@humanwhocodes/object-schema). The schema specifies both validation and merge rules that the `ConfigArray` instance needs to combine configs when there are multiple matches. Here's an example:

```js
const configFilename = path.resolve(process.cwd(), "my.config.js");
const { default: rawConfigs } = await import(configFilename);

const mySchema = {

    // define the handler key in configs
    handler: {
        required: true,
        merge(a, b) {
            if (!b) return a;
            if (!a) return b;
        },
        validate(value) {
            if (typeof value !== "function") {
                throw new TypeError("Function expected.");
            }
        }
    }
};

const configs = new ConfigArray(rawConfigs, {
    
    // the path to match filenames from
    basePath: process.cwd(),

    // additional item schemas in each config
    schema: mySchema,

    // additional config types supported (default: [])
    extraConfigTypes: ["array", "function"];
});
```

### Config Arrays

Config arrays can be multidimensional, so it's possible for a config array to contain another config array when `extraConfigTypes` contains `"array"`, such as:

```js
export default [
    
    // JS config
    {
        files: ["**/*.js"],
        handler: jsHandler
    },

    // JSON configs
    [

        // match all JSON files
        {
            name: "JSON Handler",
            files: ["**/*.json"],
            handler: jsonHandler
        },

        // match only package.json
        {
            name: "package.json Handler",
            files: ["package.json"],
            handler: packageJsonHandler
        }
    ],

    // filename must match function
    {
        files: [ filePath => filePath.endsWith(".md") ],
        handler: markdownHandler
    },

    // filename must match all patterns in subarray
    {
        files: [ ["*.test.*", "*.js"] ],
        handler: jsTestHandler
    },

    // filename must not match patterns beginning with !
    {
        name: "Non-JS files",
        files: ["!*.js"],
        settings: {
            js: false
        }
    }
];
```

In this example, the array contains both config objects and a config array. When a config array is normalized (see details below), it is flattened so only config objects remain. However, the order of evaluation remains the same.

If the `files` array contains a function, then that function is called with the absolute path of the file and is expected to return `true` if there is a match and `false` if not. (The `ignores` array can also contain functions.)

If the `files` array contains an item that is an array of strings and functions, then all patterns must match in order for the config to match. In the preceding examples, both `*.test.*` and `*.js` must match in order for the config object to be used.

If a pattern in the files array begins with `!` then it excludes that pattern. In the preceding example, any filename that doesn't end with `.js` will automatically get a `settings.js` property set to `false`.

You can also specify an `ignores` key that will force files matching those patterns to not be included. If the `ignores` key is in a config object without any other keys, then those ignores will always be applied; otherwise those ignores act as exclusions. Here's an example:

```js
export default [
    
    // Always ignored
    {
        ignores: ["**/.git/**", "**/node_modules/**"]
    },

    // .eslintrc.js file is ignored only when .js file matches
    {
        files: ["**/*.js"],
        ignores: [".eslintrc.js"]
        handler: jsHandler
    }
];
```

You can use negated patterns in `ignores` to exclude a file that was already ignored, such as:

```js
export default [
    
    // Ignore all JSON files except tsconfig.json
    {
        files: ["**/*"],
        ignores: ["**/*.json", "!tsconfig.json"]
    },

];
```

### Config Functions

Config arrays can also include config functions when `extraConfigTypes` contains `"function"`. A config function accepts a single parameter, `context` (defined by you), and must return either a config object or a config array (it cannot return another function). Config functions allow end users to execute code in the creation of appropriate config objects. Here's an example:

```js
export default [
    
    // JS config
    {
        files: ["**/*.js"],
        handler: jsHandler
    },

    // JSON configs
    function (context) {
        return [

            // match all JSON files
            {
                name: context.name + " JSON Handler",
                files: ["**/*.json"],
                handler: jsonHandler
            },

            // match only package.json
            {
                name: context.name + " package.json Handler",
                files: ["package.json"],
                handler: packageJsonHandler
            }
        ];
    }
];
```

When a config array is normalized, each function is executed and replaced in the config array with the return value.

**Note:** Config functions can also be async.

### Normalizing Config Arrays

Once a config array has been created and loaded with all of the raw config data, it must be normalized before it can be used. The normalization process goes through and flattens the config array as well as executing all config functions to get their final values.

To normalize a config array, call the `normalize()` method and pass in a context object:

```js
await configs.normalize({
    name: "MyApp"
});
```

The `normalize()` method returns a promise, so be sure to use the `await` operator. The config array instance is normalized in-place, so you don't need to create a new variable.

If you want to disallow async config functions, you can call `normalizeSync()` instead. This method is completely synchronous and does not require using the `await` operator as it does not return a promise:

```js
await configs.normalizeSync({
    name: "MyApp"
});
```

**Important:** Once a `ConfigArray` is normalized, it cannot be changed further. You can, however, create a new `ConfigArray` and pass in the normalized instance to create an unnormalized copy.

### Getting Config for a File

To get the config for a file, use the `getConfig()` method on a normalized config array and pass in the filename to get a config for:

```js
// pass in absolute filename
const fileConfig = configs.getConfig(path.resolve(process.cwd(), "package.json"));
```

The config array always returns an object, even if there are no configs matching the given filename. You can then inspect the returned config object to determine how to proceed.

A few things to keep in mind:

* You must pass in the absolute filename to get a config for.
* The returned config object never has `files`, `ignores`, or `name` properties; the only properties on the object will be the other configuration options specified.
* The config array caches configs, so subsequent calls to `getConfig()` with the same filename will return in a fast lookup rather than another calculation.
* A config will only be generated if the filename matches an entry in a `files` key. A config will not be generated without matching a `files` key (configs without a `files` key are only applied when another config with a `files` key is applied; configs without `files` are never applied on their own). Any config with a `files` key entry ending with `/**` or `/*` will only be applied if another entry in the same `files` key matches or another config matches.

## Determining Ignored Paths

You can determine if a file is ignored by using the `isFileIgnored()` method and passing in the absolute path of any file, as in this example:

```js
const ignored = configs.isFileIgnored('/foo/bar/baz.txt');
```

A file is considered ignored if any of the following is true:

* **It's parent directory is ignored.** For example, if `foo` is in `ignores`, then `foo/a.js` is considered ignored.
* **It has an ancestor directory that is ignored.** For example, if `foo` is in `ignores`, then `foo/baz/a.js` is considered ignored.
* **It matches an ignored file pattern.** For example, if `**/a.js` is in `ignores`, then `foo/a.js` and `foo/baz/a.js` are considered ignored.
* **If it matches an entry in `files` and also in `ignores`.** For example, if `**/*.js` is in `files` and `**/a.js` is in `ignores`, then `foo/a.js` and `foo/baz/a.js` are considered ignored.
* **The file is outside the `basePath`.** If the `basePath` is `/usr/me`, then `/foo/a.js` is considered ignored.

For directories, use the `isDirectoryIgnored()` method and pass in the absolute path of any directory, as in this example:

```js
const ignored = configs.isDirectoryIgnored('/foo/bar/');
```

A directory is considered ignored if any of the following is true:

* **It's parent directory is ignored.** For example, if `foo` is in `ignores`, then `foo/baz` is considered ignored.
* **It has an ancestor directory that is ignored.** For example, if `foo` is in `ignores`, then `foo/bar/baz/a.js` is considered ignored.
* **It matches and ignored file pattern.** For example, if `**/a.js` is in `ignores`, then `foo/a.js` and `foo/baz/a.js` are considered ignored.
* **If it matches an entry in `files` and also in `ignores`.** For example, if `**/*.js` is in `files` and `**/a.js` is in `ignores`, then `foo/a.js` and `foo/baz/a.js` are considered ignored.
* **The file is outside the `basePath`.** If the `basePath` is `/usr/me`, then `/foo/a.js` is considered ignored.

**Important:** A pattern such as `foo/**` means that `foo` and `foo/` are *not* ignored whereas `foo/bar` is ignored. If you want to ignore `foo` and all of its subdirectories, use the pattern `foo` or `foo/` in `ignores`.

## Caching Mechanisms

Each `ConfigArray` aggressively caches configuration objects to avoid unnecessary work. This caching occurs in two ways:

1. **File-based Caching.** For each filename that is passed into a method, the resulting config is cached against that filename so you're always guaranteed to get the same object returned from `getConfig()` whenever you pass the same filename in.
2. **Index-based Caching.** Whenever a config is calculated, the config elements that were used to create the config are also cached. So if a given filename matches elements 1, 5, and 7, the resulting config is cached with a key of `1,5,7`. That way, if another file is passed that matches the same config elements, the result is already known and doesn't have to be recalculated. That means two files that match all the same elements will return the same config from `getConfig()`.

## Acknowledgements

The design of this project was influenced by feedback on the ESLint RFC, and incorporates ideas from:

* Teddy Katz (@not-an-aardvark)
* Toru Nagashima (@mysticatea)
* Kai Cataldo (@kaicataldo)

## License

Apache 2.0
