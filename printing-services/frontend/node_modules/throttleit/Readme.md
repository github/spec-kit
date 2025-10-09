
# throttle

  Throttle a function

## Installation
```sh
$ component install component/throttle
```

```sh
$ npm install throttleit
```
## Example

```js
// with component:
var throttle = require('throttle');
// with npm: 
// var throttle = require('throttleit');

window.onresize = throttle(resize, 200);

function resize(e) {
  console.log('height', window.innerHeight);
  console.log('width', window.innerWidth);
}
```

## API

### throttle(fn, wait)

Creates a function that will call `fn` at most once every `wait` milliseconds.

Supports leading and trailing invocation.

`fn` will receive last context (`this`) and last arguments passed to a throttled wrapper before `fn` was invoked.

## License

  MIT
