# executable [![Build Status](https://travis-ci.org/kevva/executable.svg?branch=master)](https://travis-ci.org/kevva/executable)

> Check if a file is executable


## Install

```
$ npm install --save executable
```


## Usage

```js
const executable = require('executable');

executable('bash').then(exec => {
	console.log(exec);
	//=> true
});
```


## API

### executable(file)

Returns a Promise for a boolean.

### executable.sync(file)

Returns a boolean of whether the file is executable.

#### file

Type: `string`

Path of the file.

### executable.checkMode(mode, [gid], [uid])

Returns a boolean of whether the mode passed as first argument means that the file is executable.

#### mode

Type: `number`

Property `mode` of `fs.Stats` instance returned by `fs.stat()` (or `fs.statSync()`) function.

#### gid, uid

Type: `number`

Respectively the group identity and user identity of the file. If not set, permissions will be evaluated without considering owner or group of the file.

## Related

* [executable-cli](https://github.com/kevva/executable-cli) - CLI for this module


## License

MIT © [Kevin Mårtensson](https://github.com/kevva)
