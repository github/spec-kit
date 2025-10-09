# untildify [![Build Status](https://travis-ci.org/sindresorhus/untildify.svg?branch=master)](https://travis-ci.org/sindresorhus/untildify)

> Convert a tilde path to an absolute path: `~/dev` → `/Users/sindresorhus/dev`


## Install

```
$ npm install untildify
```


## Usage

```js
const untildify = require('untildify');

untildify('~/dev');
//=> '/Users/sindresorhus/dev'
```


## Related

See [tildify](https://github.com/sindresorhus/tildify) for the inverse.


## License

MIT © [Sindre Sorhus](https://sindresorhus.com)
