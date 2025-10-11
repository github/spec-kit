"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.selectUnknownFields = exports.selectFields = void 0;
exports.reconstructFieldPath = reconstructFieldPath;
const _ = require("lodash");
const selectFields = (req, fields, locations) => _(fields)
    .flatMap(field => _.flatMap(locations, location => {
    return expandField(req, field, location);
}))
    // Avoid duplicates if multiple field selections would return the same field twice.
    // E.g. with fields = ['*.foo', 'bar.foo'] and req.body = { bar: { foo: 1 }, baz: { foo: 2 } },
    // the instance bla.foo would appear twice, and baz.foo once.
    .uniqWith(isSameFieldInstance)
    .value();
exports.selectFields = selectFields;
function isSameFieldInstance(a, b) {
    return a.path === b.path && a.location === b.location;
}
function expandField(req, field, location) {
    const originalPath = field;
    const pathToExpand = location === 'headers' ? field.toLowerCase() : field;
    const paths = expandPath(req[location], pathToExpand, []);
    return paths.map(({ path, values }) => {
        const value = path === '' ? req[location] : _.get(req[location], path);
        return {
            location,
            path,
            originalPath,
            pathValues: values,
            value,
        };
    });
}
function expandPath(object, path, currPath, currValues = []) {
    const segments = _.toPath(path);
    if (!segments.length) {
        // no more paths to traverse
        return [
            {
                path: reconstructFieldPath(currPath),
                values: currValues,
            },
        ];
    }
    const key = segments[0];
    const rest = segments.slice(1);
    if (object != null && !_.isObjectLike(object)) {
        if (key === '**') {
            if (!rest.length) {
                // globstar leaves are always selected
                return [
                    {
                        path: reconstructFieldPath(currPath),
                        values: currValues,
                    },
                ];
            }
            return [];
        }
        if (key === '*') {
            // wildcard position does not exist
            return [];
        }
        // value is a primitive, paths being traversed from here might be in their prototype, return the entire path
        return [
            {
                path: reconstructFieldPath([...currPath, ...segments]),
                values: currValues,
            },
        ];
    }
    // Use a non-null value so that inexistent fields are still selected
    object = object || {};
    if (key === '*') {
        return Object.keys(object).flatMap(key => expandPath(object[key], rest, currPath.concat(key), currValues.concat(key)));
    }
    if (key === '**') {
        return Object.keys(object).flatMap(key => {
            const nextPath = currPath.concat(key);
            const value = object[key];
            // recursively find matching subpaths
            const selectedPaths = expandPath(value, segments, nextPath, [key]).concat(
            // skip the first remaining segment, if it matches the current key
            rest[0] === key ? expandPath(value, rest.slice(1), nextPath, []) : []);
            return _.uniqBy(selectedPaths, ({ path }) => path).map(({ path, values }) => ({
                path,
                values: values.length ? [...currValues, values.flat()] : currValues,
            }));
        });
    }
    return expandPath(object[key], rest, currPath.concat(key), currValues);
}
const selectUnknownFields = (req, knownFields, locations) => {
    const tree = {};
    knownFields.map(field => {
        const segments = field === '' ? [''] : _.toPath(field);
        pathToTree(segments, tree);
    });
    const instances = [];
    for (const location of locations) {
        if (req[location] != null) {
            instances.push(...findUnknownFields(location, req[location], tree));
        }
    }
    return instances;
};
exports.selectUnknownFields = selectUnknownFields;
function pathToTree(segments, tree) {
    // Will either create or merge into existing branch for the current path segment
    const branch = tree[segments[0]] || (tree[segments[0]] = {});
    if (segments.length > 1) {
        pathToTree(segments.slice(1), branch);
    }
    else {
        // Leaf value.
        branch[''] = {};
    }
}
/**
 * Performs a depth-first search for unknown fields in `value`.
 * The path to the unknown fields will be pushed to the `unknownFields` argument.
 *
 * Known fields must be passed via `tree`. A field won't be considered unknown if:
 * - its branch is validated as a whole; that is, it contains an empty string key (e.g `{ ['']: {} }`); OR
 * - its path is individually validated; OR
 * - it's covered by a wildcard (`*`).
 *
 * @returns the list of unknown fields
 */
function findUnknownFields(location, value, tree, treePath = [], unknownFields = []) {
    const globstarBranch = tree['**'];
    if (tree[''] || globstarBranch?.['']) {
        // The rest of the tree from here is covered by some validation chain
        // For example, when the current treePath is `['foo', 'bar']` but `foo` is known
        return unknownFields;
    }
    if (typeof value !== 'object') {
        if (!treePath.length || globstarBranch) {
            // This is either
            // a. a req.body that isn't an object (e.g. `req.body = 'bla'`), and wasn't validated either
            // b. a leaf value which wasn't the target of a globstar path, e.g. `foo.**.bar`
            unknownFields.push({
                path: reconstructFieldPath(treePath),
                value,
                location,
            });
        }
        return unknownFields;
    }
    const wildcardBranch = tree['*'];
    for (const key of Object.keys(value)) {
        const keyBranch = tree[key];
        const path = treePath.concat([key]);
        if (!keyBranch && !wildcardBranch && !globstarBranch) {
            // No trees cover this path, so it's an unknown one.
            unknownFields.push({
                path: reconstructFieldPath(path),
                value: value[key],
                location,
            });
            continue;
        }
        const keyUnknowns = keyBranch ? findUnknownFields(location, value[key], keyBranch, path) : [];
        const wildcardUnknowns = wildcardBranch
            ? findUnknownFields(location, value[key], wildcardBranch, path)
            : [];
        const globstarUnknowns = globstarBranch
            ? findUnknownFields(location, value[key], { ['**']: globstarBranch, ...globstarBranch }, path)
            : [];
        // If any of the tested branches contain only known fields, then don't mark the fields not covered
        // by the other branches to the list of unknown ones.
        // For example, `foo` is more comprehensive than `foo.*.bar`.
        if ((!keyBranch || keyUnknowns.length) &&
            (!wildcardBranch || wildcardUnknowns.length) &&
            (!globstarBranch || globstarUnknowns.length)) {
            unknownFields.push(...keyUnknowns, ...wildcardUnknowns, ...globstarUnknowns);
        }
    }
    return unknownFields;
}
/**
 * Reconstructs a field path from a list of path segments.
 *
 * Most segments will be concatenated by a dot, for example `['foo', 'bar']` becomes `foo.bar`.
 * However, a numeric segment will be wrapped in brackets to match regular JS array syntax:
 *
 * ```
 * reconstructFieldPath(['foo', 0, 'bar']) // foo[0].bar
 * ```
 *
 * Segments which have a special character such as `.` will be wrapped in brackets and quotes,
 * which also matches JS syntax for objects with such keys.
 *
 * ```
 * reconstructFieldPath(['foo', 'bar.baz', 'qux']) // foo["bar.baz"].qux
 * ```
 */
function reconstructFieldPath(segments) {
    return segments.reduce((prev, segment) => {
        let part = '';
        segment = segment === '\\*' ? '*' : segment;
        // TODO: Handle brackets?
        if (segment.includes('.')) {
            // Special char key access
            part = `["${segment}"]`;
        }
        else if (/^\d+$/.test(segment)) {
            // Index access
            part = `[${segment}]`;
        }
        else if (prev) {
            // Object key access
            part = `.${segment}`;
        }
        else {
            // Top level key
            part = segment;
        }
        return prev + part;
    }, '');
}
