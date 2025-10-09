## @cypress/xvfb

> easily start and stop an X Virtual Frame Buffer from your node apps.

[![CircleCI](https://circleci.com/gh/cypress-io/xvfb/tree/master.svg?style=svg)](https://circleci.com/gh/cypress-io/xvfb/tree/master)
[![Build Status](https://travis-ci.org/cypress-io/xvfb.svg?branch=master)](https://travis-ci.org/cypress-io/xvfb)
[![semantic-release](https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg)](https://github.com/semantic-release/semantic-release) [![renovate-app badge][renovate-badge]][renovate-app]

### Usage

```javascript
var Xvfb = require('xvfb');
var options = {}; // optional
var xvfb = new Xvfb(options);
xvfb.start(function(err, xvfbProcess) {
  // code that uses the virtual frame buffer here
  xvfb.stop(function(err) {
    // the Xvfb is stopped
  });
});
```

The Xvfb constructor takes four options:

* <code>displayNum</code> - the X display to use, defaults to the lowest unused display number >= 99 if <code>reuse</code> is false or 99 if <code>reuse</code> is true.
* <code>reuse</code> - whether to reuse an existing Xvfb instance if it already exists on the X display referenced by displayNum.
* <code>timeout</code> - number of milliseconds to wait when starting Xvfb before assuming it failed to start, defaults to 2000.
* <code>silent</code> - don't pipe Xvfb stderr to the process's stderr.
* <code>xvfb_args</code> - Extra arguments to pass to `Xvfb`.
* <code>onStderrData</code> - Function to receive `stderr` output

### Debugging

Run with `DEBUG=xvfb` environment variable to see debug messages. If you want
to see log messages from the Xvfb process itself, use `DEBUG=xvfb,xvfb-process`.

### Thanks to

Forked from [node-xvfb](https://github.com/Rob--W/node-xvfb)

* [kesla](https://github.com/kesla) for https://github.com/kesla/node-headless
* [leonid-shevtsov](https://github.com/leonid-shevtsov) for https://github.com/leonid-shevtsov/headless
* [paulbaumgart](https://github.com/paulbaumgart) for creating the initial version of this package.

both of which served as inspiration for this package.

[renovate-badge]: https://img.shields.io/badge/renovate-app-blue.svg
[renovate-app]: https://renovateapp.com/
