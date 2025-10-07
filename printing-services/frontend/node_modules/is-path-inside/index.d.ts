/**
Check if a path is inside another path.

Note that relative paths are resolved against `process.cwd()` to make them absolute.

_Important:_ This package is meant for use with path manipulation. It does not check if the paths exist nor does it resolve symlinks. You should not use this as a security mechanism to guard against access to certain places on the file system.

@example
```
import isPathInside = require('is-path-inside');

isPathInside('a/b/c', 'a/b');
//=> true

isPathInside('a/b/c', 'x/y');
//=> false

isPathInside('a/b/c', 'a/b/c');
//=> false

isPathInside('/Users/sindresorhus/dev/unicorn', '/Users/sindresorhus');
//=> true
```
*/
declare function isPathInside(childPath: string, parentPath: string): boolean;

export = isPathInside;
