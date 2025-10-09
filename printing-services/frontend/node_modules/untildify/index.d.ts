/**
Convert a tilde path to an absolute path: `~/dev` → `/Users/sindresorhus/dev`.

@example
```
import untildify = require('untildify');

untildify('~/dev');
//=> '/Users/sindresorhus/dev'
```
*/
declare function untildify(pathWithTilde: string): string;

export = untildify;
