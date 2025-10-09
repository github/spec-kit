ospath
======

[![npm Package](https://img.shields.io/npm/v/ospath.svg?style=flat-square)](https://www.npmjs.org/package/ospath)
[![build status](https://api.travis-ci.org/jprichardson/ospath.svg)](http://travis-ci.org/jprichardson/ospath)

A JavaScript component that provides operating specific path values.


Installation
------------

    npm i --save ospath


API
---

### ospath.data()

Returns the directory where an application should store its data directory.

- **Windows**: `%APPDATA%`
- **OS X**: `~/Library/Application Support`
- **Unix-like**: `$XDG_CONFIG_HOME` or `~/.config`


### ospath.desktop()

Returns the users desktop directory. On every OS, this is just the `home()`
dir and `Desktop`.


### ospath.home()

Returns the user's home directory.

- **Windows**: `%USERPROFILE%`
- **Unix-like**: `$HOME`


### ospath.tmp()

Returns a temporary directory. Could also use `require('os').tmpdir()`.

- **Windows**: `%TEMP%`
- **Unix-like**: `/tmp`


License
-------

MIT
