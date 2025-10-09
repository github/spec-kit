# node-cachedir

Provides a directory where the OS wants you to store cached files.

## Installation

```sh
npm install --save cachedir
```

## Usage

```javascript
const cachedir = require('cachedir')

console.log(cachedir('myapp'))
// e.g.
//=> '/Users/linus/Library/Caches/myapp'
//=> '/home/linus/.cache/myapp'
//=> 'C:\Users\linus\AppData\Local\myapp\Cache'
```

## API

### `cachedir(id)`

- `id` (`string`, required)
- returns `string`

Return path to an appropriate place to store cache files.
