[![Build Status](https://travis-ci.org/EventEmitter2/EventEmitter2.svg?branch=master)](https://travis-ci.org/EventEmitter2/EventEmitter2)
[![Coverage Status](https://coveralls.io/repos/github/EventEmitter2/EventEmitter2/badge.svg?branch=v6.4.3)](https://coveralls.io/github/EventEmitter2/EventEmitter2?branch=v6.4.3)
[![NPM version](https://badge.fury.io/js/eventemitter2.svg)](http://badge.fury.io/js/eventemitter2)
[![Dependency Status](https://img.shields.io/david/asyncly/eventemitter2.svg)](https://david-dm.org/asyncly/eventemitter2)
[![npm](https://img.shields.io/npm/dm/eventemitter2.svg?maxAge=2592000)]()

# SYNOPSIS

EventEmitter2 is an implementation of the EventEmitter module found in Node.js. 
In addition to having a better benchmark performance than EventEmitter and being browser-compatible, 
it also extends the interface of EventEmitter with many additional non-breaking features.

If you like this project please show your support with a [GitHub :star:](https://github.com/EventEmitter2/EventEmitter2/stargazers)!

# DESCRIPTION

### FEATURES
 - ES5 compatible UMD module, that supports node.js, browser and workers of any kind
 - Namespaces/Wildcards
 - [Any](#emitteronanylistener) listeners
 - Times To Listen (TTL), extends the `once` concept with [`many`](#emittermanyevent--eventns-timestolisten-listener-options)
 - [Async listeners](#emitteronevent-listener-options-objectboolean) (using setImmediate|setTimeout|nextTick) with promise|async function support
 - The [emitAsync](#emitteremitasyncevent--eventns-arg1-arg2-) method to return the results of the listeners via Promise.all
 - Subscription methods ([on](#emitteronevent-listener-options-objectboolean), [once](#emitterprependoncelistenerevent--eventns-listener-options), [many](#emittermanyevent--eventns-timestolisten-listener-options), ...) can return a 
 [listener](#listener) object that makes it easy to remove the subscription when needed - just call the listener.off() method.
 - Feature-rich [waitFor](#emitterwaitforevent--eventns-options) method to wait for events using promises
 - [listenTo](#listentotargetemitter-events-objectevent--eventns-function-options) & [stopListeningTo](#stoplisteningtotarget-object-event-event--eventns-boolean) methods
 for listening to an external event emitter of any kind and propagate its events through itself using optional reducers/filters 
 - Extended version of the [events.once](#eventemitter2onceemitter-event--eventns-options) method from the [node events API](https://nodejs.org/api/events.html#events_events_once_emitter_name)
 - Browser & Workers environment compatibility
 - Demonstrates good performance in benchmarks

```
Platform: win32, x64, 15267MB
Node version: v13.11.0
CPU: 4 x AMD Ryzen 3 2200U with Radeon Vega Mobile Gfx @ 2495MHz
----------------------------------------------------------------
EventEmitterHeatUp x 2,897,056 ops/sec ±3.86% (67 runs sampled)
EventEmitter x 3,232,934 ops/sec ±3.50% (65 runs sampled)
EventEmitter2 x 12,261,042 ops/sec ±4.72% (59 runs sampled)
EventEmitter2 (wild) x 242,751 ops/sec ±5.15% (68 runs sampled)
EventEmitter2 (wild) using plain events x 358,916 ops/sec ±2.58% (78 runs sampled)
EventEmitter2 (wild) emitting ns x 1,837,323 ops/sec ±3.50% (72 runs sampled)
EventEmitter2 (wild) emitting a plain event x 2,743,707 ops/sec ±4.08% (65 runs sampled)
EventEmitter3 x 10,380,258 ops/sec ±3.93% (67 runs sampled)

Fastest is EventEmitter2
```

### What's new

To find out what's new see the project [CHANGELOG](https://github.com/EventEmitter2/EventEmitter2/blob/master/CHANGELOG.md)

### Differences (Non-breaking, compatible with existing EventEmitter)

 - The EventEmitter2 constructor takes an optional configuration object with the following default values:
```javascript
var EventEmitter2 = require('eventemitter2');
var emitter = new EventEmitter2({

  // set this to `true` to use wildcards
  wildcard: false,

  // the delimiter used to segment namespaces
  delimiter: '.', 

  // set this to `true` if you want to emit the newListener event
  newListener: false, 

  // set this to `true` if you want to emit the removeListener event
  removeListener: false, 

  // the maximum amount of listeners that can be assigned to an event
  maxListeners: 10,

  // show event name in memory leak message when more than maximum amount of listeners is assigned
  verboseMemoryLeak: false,

  // disable throwing uncaughtException if an error event is emitted and it has no listeners
  ignoreErrors: false
});
```

 - Getting the actual event that fired.

```javascript
emitter.on('foo.*', function(value1, value2) {
  console.log(this.event, value1, value2);
});

emitter.emit('foo.bar', 1, 2); // 'foo.bar' 1 2
emitter.emit(['foo', 'bar'], 3, 4); // 'foo.bar' 3 4

emitter.emit(Symbol(), 5, 6); // Symbol() 5 6
emitter.emit(['foo', Symbol()], 7, 8); // ['foo', Symbol()] 7 8
```
**Note**: Generally this.event is normalized to a string ('event', 'event.test'),
except the cases when event is a symbol or namespace contains a symbol. 
In these cases this.event remains as is (symbol and array). 

 - Fire an event N times and then remove it, an extension of the `once` concept.

```javascript
emitter.many('foo', 4, function() {
  console.log('hello');
});
```

 - Pass in a namespaced event as an array rather than a delimited string.

```javascript
emitter.many(['foo', 'bar', 'bazz'], 4, function() {
  console.log('hello');
});
```

# Installing

```console
$ npm install eventemitter2
```

Or you can use unpkg.com CDN to import this [module](https://unpkg.com/eventemitter2) as a script directly from the browser 

# API

### Types definition
- `Event`: string | symbol
- `EventNS`: string | Event []

## Class EventEmitter2

### instance:
- [emit(event: event | eventNS, ...values: any[]): boolean](#emitteremitevent--eventns-arg1-arg2-);

- [emitAsync(event: event | eventNS, ...values: any[]): Promise<any[]>](#emitteremitasyncevent--eventns-arg1-arg2-)

- [addListener(event: event | eventNS, listener: ListenerFn, boolean|options?: object): this|Listener](#emitteraddlistenerevent-listener-options-objectboolean)

- [on(event: event | eventNS, listener: ListenerFn, boolean|options?: object): this|Listener](#emitteraddlistenerevent-listener-options-objectboolean)

- [once(event: event | eventNS, listener: ListenerFn, boolean|options?: object): this|Listener](#emitteronceevent--eventns-listener-options)

- [many(event: event | eventNS, timesToListen: number, listener: ListenerFn, boolean|options?: object): this|Listener](#emittermanyevent--eventns-timestolisten-listener-options)

- [prependMany(event: event | eventNS, timesToListen: number, listener: ListenerFn, boolean|options?: object): this|Listener](#emitterprependanylistener)

- [prependOnceListener(event: event | eventNS, listener: ListenerFn, boolean|options?: object): this|Listener](#emitterprependoncelistenerevent--eventns-listener-options)

- [prependListener(event: event | eventNS, listener: ListenerFn, boolean|options?: object): this|Listener](#emitterprependlistenerevent-listener-options)

- [prependAny(listener: EventAndListener): this](#emitterprependanylistener)

- [onAny(listener: EventAndListener): this](#emitteronanylistener)

- [offAny(listener: ListenerFn): this](#emitteroffanylistener)

- [removeListener(event: event | eventNS, listener: ListenerFn): this](#emitterremovelistenerevent--eventns-listener)

- [off(event: event | eventNS, listener: ListenerFn): this](#emitteroffevent--eventns-listener)

- [removeAllListeners(event?: event | eventNS): this](#emitterremovealllistenersevent--eventns)

- [setMaxListeners(n: number): void](#emittersetmaxlistenersn)

- [getMaxListeners(): number](#emittergetmaxlisteners)

- [eventNames(nsAsArray?: boolean): string[]](#emittereventnamesnsasarray)

- [listeners(event: event | eventNS): ListenerFn[]](#emitterlistenersevent--eventns)

- [listenersAny(): ListenerFn[]](#emitterlistenersany)

- [hasListeners(event?: event | eventNS): Boolean](#haslistenersevent--eventnsstringboolean)

- [waitFor(event: event | eventNS, timeout?: number): CancelablePromise<any[]>](#emitterwaitforevent--eventns-timeout)

- [waitFor(event: event | eventNS, filter?: WaitForFilter): CancelablePromise<any[]>](#emitterwaitforevent--eventns-filter)

- [waitFor(event: event | eventNS, options?: WaitForOptions): CancelablePromise<any[]>](#emitterwaitforevent--eventns-options)

- [listenTo(target: GeneralEventEmitter, event: event | eventNS, options?: ListenToOptions): this](#listentotargetemitter-events-objectevent--eventns-function-options)

- [listenTo(target: GeneralEventEmitter, events: (event | eventNS)[], options?: ListenToOptions): this](#listentotargetemitter-events-event--eventns-options)

- [listenTo(target: GeneralEventEmitter, events: Object<event | eventNS, Function>, options?: ListenToOptions): this](#listentotargetemitter-events-objectevent--eventns-function-options)

- [stopListeningTo(target?: GeneralEventEmitter, event?: event | eventNS): Boolean](#stoplisteningtarget-object-event-event--eventns-boolean)

### static:

- [static once(emitter: EventEmitter2, event: string | symbol, options?: OnceOptions): CancelablePromise<any[]>](#eventemitter2onceemitter-event--eventns-options)

- [static defaultMaxListeners: number](#eventemitter2defaultmaxlisteners)

The `event` argument specified in the API declaration can be a string or symbol for a simple event emitter
and a string|symbol|Array(string|symbol) in a case of a wildcard emitter; 

When an `EventEmitter` instance experiences an error, the typical action is
to emit an `error` event. Error events are treated as a special case.
If there is no listener for it, then the default action is to print a stack
trace and exit the program.

All EventEmitters emit the event `newListener` when new listeners are
added. EventEmitters also emit the event `removeListener` when listeners are
removed, and `removeListenerAny` when listeners added through `onAny` are
removed.


**Namespaces** with **Wildcards**
To use namespaces/wildcards, pass the `wildcard` option into the EventEmitter 
constructor. When namespaces/wildcards are enabled, events can either be 
strings (`foo.bar`) separated by a delimiter or arrays (`['foo', 'bar']`). The 
delimiter is also configurable as a constructor option.

An event name passed to any event emitter method can contain a wild card (the 
`*` character). If the event name is a string, a wildcard may appear as `foo.*`. 
If the event name is an array, the wildcard may appear as `['foo', '*']`.

If either of the above described events were passed to the `on` method, 
subsequent emits such as the following would be observed...

```javascript
emitter.emit(Symbol());
emitter.emit('foo');
emitter.emit('foo.bazz');
emitter.emit(['foo', 'bar']);
emitter.emit(['foo', Symbol()]);
```

**NOTE:** An event name may use more than one wildcard. For example, 
`foo.*.bar.*` is a valid event name, and would match events such as
`foo.x.bar.y`, or `['foo', 'bazz', 'bar', 'test']` 

# Multi-level Wildcards
A double wildcard (the string `**`) matches any number of levels (zero or more) of events. So if for example `'foo.**'` is passed to the `on` method, the following events would be observed:

````javascript
emitter.emit('foo');
emitter.emit('foo.bar');
emitter.emit('foo.bar.baz');
emitter.emit(['foo', Symbol(), 'baz']);
````

On the other hand, if the single-wildcard event name was passed to the on method, the callback would only observe the second of these events.


### emitter.addListener(event, listener, options?: object|boolean)
### emitter.on(event, listener, options?: object|boolean)

Adds a listener to the end of the listeners array for the specified event.

```javascript
emitter.on('data', function(value1, value2, value3, ...) {
  console.log('The event was raised!');
});
```
```javascript
emitter.on('data', function(value) {
  console.log('The event was raised!');
});
```

**Options:**

- `async:boolean= false`- invoke the listener in async mode using setImmediate (fallback to setTimeout if not available)
or process.nextTick depending on the `nextTick` option.

- `nextTick:boolean= false`- use process.nextTick instead of setImmediate to invoke the listener asynchronously. 

- `promisify:boolean= false`- additionally wraps the listener to a Promise for later invocation using `emitAsync` method.
This option will be activated by default if its value is `undefined`
and the listener function is an `asynchronous function` (whose constructor name is `AsyncFunction`). 

- `objectify:boolean= false`- activates returning a [listener](#listener) object instead of 'this' by the subscription method.

#### listener
The listener object has the following properties:
- `emitter: EventEmitter2` - reference to the event emitter instance
- `event: event|eventNS` - subscription event
- `listener: Function` - reference to the listener
- `off(): Function`- removes the listener (voids the subscription)

````javascript
var listener= emitter.on('event', function(){
  console.log('hello!');
}, {objectify: true});

emitter.emit('event');

listener.off();
````

**Note:** If the options argument is `true` it will be considered as `{promisify: true}`

**Note:** If the options argument is `false` it will be considered as `{async: true}`

```javascript
var EventEmitter2= require('eventemitter2');
var emitter= new EventEmitter2();

emitter.on('event', function(){
    console.log('The event was raised!');
}, {async: true});

emitter.emit('event');
console.log('emitted');
```
Since the `async` option was set the output from the code above is as follows:
````
emitted
The event was raised!
````

If the listener is an async function or function which returns a promise, use the `promisify` option as follows:

```javascript
var EventEmitter2= require('eventemitter2');
var emitter= new EventEmitter2();

emitter.on('event', function(){
    console.log('The event was raised!');
    return new Promise(function(resolve){
       console.log('listener resolved');
       setTimeout(resolve, 1000);
    });
}, {promisify: true});

emitter.emitAsync('event').then(function(){
    console.log('all listeners were resolved!');
});

console.log('emitted');
````
Output:
````
emitted
The event was raised!
listener resolved
all listeners were resolved!
````
If the `promisify` option is false (default value) the output of the same code is as follows:
````
The event was raised!
listener resolved
emitted
all listeners were resolved!
````


### emitter.prependListener(event, listener, options?)

Adds a listener to the beginning of the listeners array for the specified event.

```javascript
emitter.prependListener('data', function(value1, value2, value3, ...) {
  console.log('The event was raised!');
});
```

**options:**

`options?`: See the [addListener options](#emitteronevent-listener-options-objectboolean)

### emitter.onAny(listener)

Adds a listener that will be fired when any event is emitted. The event name is passed as the first argument to the callback.

```javascript
emitter.onAny(function(event, value) {
  console.log('All events trigger this.');
});
```

### emitter.prependAny(listener)

Adds a listener that will be fired when any event is emitted. The event name is passed as the first argument to the callback. The listener is added to the beginning of the listeners array

```javascript
emitter.prependAny(function(event, value) {
  console.log('All events trigger this.');
});
```

### emitter.offAny(listener)

Removes the listener that will be fired when any event is emitted.

```javascript
emitter.offAny(function(value) {
  console.log('The event was raised!');
});
```

#### emitter.once(event | eventNS, listener, options?)

Adds a **one time** listener for the event. The listener is invoked 
only the first time the event is fired, after which it is removed.

```javascript
emitter.once('get', function (value) {
  console.log('Ah, we have our first value!');
});
```

**options:**

`options?`: See the [addListener options](#emitteronevent-listener-options-objectboolean)

#### emitter.prependOnceListener(event | eventNS, listener, options?)

Adds a **one time** listener for the event. The listener is invoked 
only the first time the event is fired, after which it is removed.
The listener is added to the beginning of the listeners array

```javascript
emitter.prependOnceListener('get', function (value) {
  console.log('Ah, we have our first value!');
});
```

**options:**

`options?`: See the [addListener options](#emitteronevent-listener-options-objectboolean)

### emitter.many(event | eventNS, timesToListen, listener, options?)

Adds a listener that will execute **n times** for the event before being
removed. The listener is invoked only the first **n times** the event is 
fired, after which it is removed.

```javascript
emitter.many('get', 4, function (value) {
  console.log('This event will be listened to exactly four times.');
});
```

**options:**

`options?`: See the [addListener options](#emitteronevent-listener-options-objectboolean)

### emitter.prependMany(event | eventNS, timesToListen, listener, options?)

Adds a listener that will execute **n times** for the event before being
removed. The listener is invoked only the first **n times** the event is 
fired, after which it is removed.
The listener is added to the beginning of the listeners array.

```javascript
emitter.many('get', 4, function (value) {
  console.log('This event will be listened to exactly four times.');
});
```

**options:**

`options?`: See the [addListener options](#emitteronevent-listener-options-objectboolean)

### emitter.removeListener(event | eventNS, listener)
### emitter.off(event | eventNS, listener)

Remove a listener from the listener array for the specified event. 
**Caution**: Calling this method changes the array indices in the listener array behind the listener.

```javascript
var callback = function(value) {
  console.log('someone connected!');
};
emitter.on('get', callback);
// ...
emitter.removeListener('get', callback);
```


### emitter.removeAllListeners([event | eventNS])

Removes all listeners, or those of the specified event.


### emitter.setMaxListeners(n)

By default EventEmitters will print a warning if more than 10 listeners 
are added to it. This is a useful default which helps finding memory leaks. 
Obviously not all Emitters should be limited to 10. This function allows 
that to be increased. Set to zero for unlimited.


### emitter.getMaxListeners()

Returns the current max listener value for the EventEmitter which is either set by emitter.setMaxListeners(n) or defaults to EventEmitter2.defaultMaxListeners


### emitter.listeners(event | eventNS)

Returns an array of listeners for the specified event. This array can be 
manipulated, e.g. to remove listeners.

```javascript
emitter.on('get', function(value) {
  console.log('someone connected!');
});
console.log(emitter.listeners('get')); // [ [Function] ]
```

### emitter.listenersAny()

Returns an array of listeners that are listening for any event that is 
specified. This array can be manipulated, e.g. to remove listeners.

```javascript
emitter.onAny(function(value) {
  console.log('someone connected!');
});
console.log(emitter.listenersAny()[0]); // [ [Function] ]
```

### emitter.emit(event | eventNS, [arg1], [arg2], [...])
Execute each of the listeners that may be listening for the specified event 
name in order with the list of arguments.

### emitter.emitAsync(event | eventNS, [arg1], [arg2], [...])

Return the results of the listeners via [Promise.all](https://developer.mozilla.org/ja/docs/Web/JavaScript/Reference/Global_Objects/Promise/all).
Only this method doesn't work [IE](http://caniuse.com/#search=promise).

```javascript
emitter.on('get',function(i) {
  return new Promise(function(resolve){
    setTimeout(function(){
      resolve(i+3);
    },50);
  });
});
emitter.on('get',function(i) {
  return new Promise(function(resolve){
    resolve(i+2)
  });
});
emitter.on('get',function(i) {
  return Promise.resolve(i+1);
});
emitter.on('get',function(i) {
  return i+0;
});
emitter.on('get',function(i) {
  // noop
});

emitter.emitAsync('get',0)
.then(function(results){
  console.log(results); // [3,2,1,0,undefined]
});
```

### emitter.waitFor(event | eventNS, [options])
### emitter.waitFor(event | eventNS, [timeout])
### emitter.waitFor(event | eventNS, [filter])

Returns a thenable object (promise interface) that resolves when a specific event occurs

````javascript
emitter.waitFor('event').then(function (data) { 
    console.log(data); // ['bar']
});

emitter.emit('event', 'bar');
````

````javascript
emitter.waitFor('event', { 
    // handle first event data argument as an error (err, ...data)
    handleError: false,
    // the timeout for resolving the promise before it is rejected with an error (Error: timeout).
    timeout: 0, 
    //filter function to determine acceptable values for resolving the promise.
    filter: function(arg0, arg1){ 
        return arg0==='foo' && arg1==='bar'
    },
    Promise: Promise, // Promise constructor to use,
    overload: false // overload cancellation api in a case of external Promise class
}).then(function(data){
    console.log(data); // ['foo', 'bar']
});

emitter.emit('event', 'foo', 'bar')
````

````javascript
var promise= emitter.waitFor('event');

promise.then(null, function(error){
    console.log(error); //Error: canceled
});

promise.cancel(); //stop listening the event and reject the promise
````

````javascript
emitter.waitFor('event', {
    handleError: true
}).then(null, function(error){
    console.log(error); //Error: custom error
});

emitter.emit('event', new Error('custom error')); // reject the promise
````
### emitter.eventNames(nsAsArray)

Returns an array listing the events for which the emitter has registered listeners.
```javascript
var emitter= new EventEmitter2();
emitter.on('foo', () => {});
emitter.on('bar', () => {});
emitter.on(Symbol('test'), () => {});
emitter.on(['foo', Symbol('test2')], () => {});

console.log(emitter.eventNames());
// Prints: [ 'bar', 'foo', [ 'foo', Symbol(test2) ], [ 'foo', Symbol(test2) ] ]
```
**Note**: Listeners order not guaranteed
### listenTo(targetEmitter, events: event | eventNS, options?)

### listenTo(targetEmitter, events: (event | eventNS)[], options?)

### listenTo(targetEmitter, events: Object<event | eventNS, Function>, options?)

Listens to the events emitted by an external emitter and propagate them through itself.
The target object could be of any type that implements methods for subscribing and unsubscribing to its events. 
By default this method attempts to use `addListener`/`removeListener`, `on`/`off` and `addEventListener`/`removeEventListener` pairs,
but you able to define own hooks `on(event, handler)` and `off(event, handler)` in the options object to use
custom subscription API. In these hooks `this` refers to the target object.

The options object has the following interface:
- `on(event, handler): void`
- `off(event, handler): void`
- `reducer: (Function) | (Object<Function>): Boolean`

In case you selected the `newListener` and `removeListener` options when creating the emitter, 
the subscription to the events of the target object will be conditional, 
depending on whether there are listeners in the emitter that could listen them.

````javascript
var EventEmitter2 = require('EventEmitter2');
var http = require('http');

var server = http.createServer(function(request, response){
    console.log(request.url);
    response.end('Hello Node.js Server!')
}).listen(3000);

server.on('connection', function(req, socket, head){
   console.log('connect');
});

// activate the ability to attach listeners on demand 
var emitter= new EventEmitter2({
    newListener: true,
    removeListener: true
});

emitter.listenTo(server, {
    'connection': 'localConnection',
    'close': 'close'
}, {
    reducers: {
        connection: function(event){
            console.log('event name:' + event.name); //'localConnection'
            console.log('original event name:' + event.original); //'connection'
            return event.data[0].remoteAddress==='::1';
        }
    }
});

emitter.on('localConnection', function(socket){
   console.log('local connection', socket.remoteAddress);
});

setTimeout(function(){
    emitter.stopListeningTo(server);
}, 30000);
````
An example of using a wildcard emitter in a browser:
````javascript
const ee= new EventEmitter2({
   wildcard: true
});

ee.listenTo(document.querySelector('#test'), {
   'click': 'div.click',
   'mouseup': 'div.mouseup',
   'mousedown': 'div.mousedown'
});

ee.on('div.*', function(evt){
    console.log('listenTo: '+ evt.type);
});

setTimeout(function(){
    ee.stopListeningTo(document.querySelector('#test'));
}, 30000);
````

### stopListeningTo(target?: Object, event: event | eventNS): Boolean

Stops listening the targets. Returns true if some listener was removed.

### hasListeners(event | eventNS?:String):Boolean

Checks whether emitter has any listeners.

### emitter.listeners(event | eventNS)

Returns the array of listeners for the event named eventName.
In wildcard mode this method returns namespaces as strings:
````javascript
var emitter= new EventEmitter2({
    wildcard: true
});
emitter.on('a.b.c', function(){});
emitter.on(['z', 'x', 'c'], function(){});
console.log(emitter.eventNames()) // [ 'z.x.c', 'a.b.c' ]
````
If some namespace contains a Symbol member or the `nsAsArray` option is set the method will return namespace as an array of its members;
````javascript
var emitter= new EventEmitter2({
    wildcard: true
});
emitter.on('a.b.c', function(){});
emitter.on(['z', 'x', Symbol()], function(){});
console.log(emitter.eventNames()) // [ [ 'z', 'x', Symbol() ], 'a.b.c' ]
````

### EventEmitter2.once(emitter, event | eventNS, [options])
Creates a cancellable Promise that is fulfilled when the EventEmitter emits the given event or that is rejected
when the EventEmitter emits 'error'. 
The Promise will resolve with an array of all the arguments emitted to the given event.
This method is intentionally generic and works with the web platform EventTarget interface,
which has no special 'error' event semantics and does not listen to the 'error' event.

Basic example:
````javascript
var emitter= new EventEmitter2();

EventEmitter2.once(emitter, 'event', {
    timeout: 0,
    Promise: Promise, // a custom Promise constructor
    overload: false // overload promise cancellation api if exists with library implementation
}).then(function(data){
    console.log(data); // [1, 2, 3]
});

emitter.emit('event', 1, 2, 3);
````
With timeout option:
````javascript
EventEmitter2.once(emitter, 'event', {
    timeout: 1000
}).then(null, function(err){
    console.log(err); // Error: timeout
});
````
The library promise cancellation API:
````javascript
promise= EventEmitter2.once(emitter, 'event');
// notice: the cancel method exists only in the first promise chain
promise.then(null, function(err){
    console.log(err); // Error: canceled
});

promise.cancel();
````
Using the custom Promise class (**[bluebird.js](https://www.npmjs.com/package/bluebird)**):
````javascript
var BBPromise = require("bluebird");

EventEmitter2.once(emitter, 'event', {
    Promise: BBPromise
}).then(function(data){
    console.log(data); // [4, 5, 6]
});

emitter.emit('event', 4, 5, 6);
````

````javascript
var BBPromise = require("bluebird");

BBPromise.config({
    // if false or options.overload enabled, the library cancellation API will be used
    cancellation: true 
});

var promise= EventEmitter2.once(emitter, 'event', {
    Promise: BBPromise,
    overload: false // use bluebird cancellation API
}).then(function(data){
    // notice: never executed due to BlueBird cancellation logic
}, function(err){
    // notice: never executed due to BlueBird cancellation logic
});

promise.cancel();

emitter.emit('event', 'never handled');
````

### EventEmitter2.defaultMaxListeners

Sets default max listeners count globally for all instances, including those created before the change is made.
