# request-progress

[![NPM version][npm-image]][npm-url] [![Downloads][downloads-image]][npm-url] [![Build Status][travis-image]][travis-url] [![Coverage Status][coveralls-image]][coveralls-url] [![Dependency status][david-dm-image]][david-dm-url] [![Dev Dependency status][david-dm-dev-image]][david-dm-dev-url]

[npm-url]:https://npmjs.org/package/request-progress
[downloads-image]:http://img.shields.io/npm/dm/request-progress.svg
[npm-image]:http://img.shields.io/npm/v/request-progress.svg
[travis-url]:https://travis-ci.org/IndigoUnited/node-request-progress
[travis-image]:http://img.shields.io/travis/IndigoUnited/node-request-progress/master.svg
[coveralls-url]:https://coveralls.io/r/IndigoUnited/node-request-progress
[coveralls-image]:https://img.shields.io/coveralls/IndigoUnited/node-request-progress/master.svg
[david-dm-url]:https://david-dm.org/IndigoUnited/node-request-progress
[david-dm-image]:https://img.shields.io/david/IndigoUnited/node-request-progress.svg
[david-dm-dev-url]:https://david-dm.org/IndigoUnited/node-request-progress#info=devDependencies
[david-dm-dev-image]:https://img.shields.io/david/dev/IndigoUnited/node-request-progress.svg

Tracks the download progress of a request made with [request](https://github.com/mikeal/request), giving insight of various metrics including progress percentage, download speed and time remaining.


## Installation

`$ npm install request-progress`


## Usage

```js
var fs = require('fs');
var request = require('request');
var progress = require('request-progress');

// The options argument is optional so you can omit it
progress(request('https://az412801.vo.msecnd.net/vhd/VMBuild_20141027/VirtualBox/IE11/Windows/IE11.Win8.1.For.Windows.VirtualBox.zip'), {
    // throttle: 2000,                    // Throttle the progress event to 2000ms, defaults to 1000ms
    // delay: 1000,                       // Only start to emit after 1000ms delay, defaults to 0ms
    // lengthHeader: 'x-transfer-length'  // Length header to use, defaults to content-length
})
.on('progress', function (state) {
    // The state is an object that looks like this:
    // {
    //     percent: 0.5,               // Overall percent (between 0 to 1)
    //     speed: 554732,              // The download speed in bytes/sec
    //     size: {
    //         total: 90044871,        // The total payload size in bytes
    //         transferred: 27610959   // The transferred payload size in bytes
    //     },
    //     time: {
    //         elapsed: 36.235,        // The total elapsed seconds since the start (3 decimals)
    //         remaining: 81.403       // The remaining seconds to finish (3 decimals)
    //     }
    // }
    console.log('progress', state);
})
.on('error', function (err) {
    // Do something with err
})
.on('end', function () {
    // Do something after request finishes
})
.pipe(fs.createWriteStream('IE11.Win8.1.For.Windows.VirtualBox.zip'));
```

If the request's response does not include the `content-length` header, the values of some metrics will be `null`.
Also `speed` and `time.remaining` will be `null` until it can be calculated.

The `state` object emitted in the `progress` event is reused to avoid creating a new object for each event.   
If you wish to peek the `state` object at any time, it is available in `request.progressState`.


## Tests

`$ npm test`   
`$ npm test-cov` to get coverage report


## License

Released under the [MIT License](http://www.opensource.org/licenses/mit-license.php).
