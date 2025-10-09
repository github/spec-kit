
/**
 * @cypress/angular v0.0.0-development
 * (c) 2025 Cypress.io
 * Released under the MIT License
 */

import 'zone.js';
import 'zone.js/testing';
import { CommonModule } from '@angular/common';
import { assertInInjectionContext, inject, Injector, effect, untracked, DestroyRef, Injectable, Component, EventEmitter, ErrorHandler, SimpleChange } from '@angular/core';
import { getTestBed, TestComponentRenderer, TestBed } from '@angular/core/testing';
import { BrowserDynamicTestingModule, platformBrowserDynamicTesting } from '@angular/platform-browser-dynamic/testing';

/******************************************************************************
Copyright (c) Microsoft Corporation.

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.
***************************************************************************** */
/* global Reflect, Promise, SuppressedError, Symbol */

var extendStatics = function(d, b) {
  extendStatics = Object.setPrototypeOf ||
      ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
      function (d, b) { for (var p in b) if (Object.prototype.hasOwnProperty.call(b, p)) d[p] = b[p]; };
  return extendStatics(d, b);
};

function __extends(d, b) {
  if (typeof b !== "function" && b !== null)
      throw new TypeError("Class extends value " + String(b) + " is not a constructor or null");
  extendStatics(d, b);
  function __() { this.constructor = d; }
  d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
}

function __rest(s, e) {
  var t = {};
  for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p) && e.indexOf(p) < 0)
      t[p] = s[p];
  if (s != null && typeof Object.getOwnPropertySymbols === "function")
      for (var i = 0, p = Object.getOwnPropertySymbols(s); i < p.length; i++) {
          if (e.indexOf(p[i]) < 0 && Object.prototype.propertyIsEnumerable.call(s, p[i]))
              t[p[i]] = s[p[i]];
      }
  return t;
}

function __decorate(decorators, target, key, desc) {
  var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
  if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
  else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
  return c > 3 && r && Object.defineProperty(target, key, r), r;
}

function __values(o) {
  var s = typeof Symbol === "function" && Symbol.iterator, m = s && o[s], i = 0;
  if (m) return m.call(o);
  if (o && typeof o.length === "number") return {
      next: function () {
          if (o && i >= o.length) o = void 0;
          return { value: o && o[i++], done: !o };
      }
  };
  throw new TypeError(s ? "Object is not iterable." : "Symbol.iterator is not defined.");
}

function __read(o, n) {
  var m = typeof Symbol === "function" && o[Symbol.iterator];
  if (!m) return o;
  var i = m.call(o), r, ar = [], e;
  try {
      while ((n === void 0 || n-- > 0) && !(r = i.next()).done) ar.push(r.value);
  }
  catch (error) { e = { error: error }; }
  finally {
      try {
          if (r && !r.done && (m = i["return"])) m.call(i);
      }
      finally { if (e) throw e.error; }
  }
  return ar;
}

function __spreadArray(to, from, pack) {
  if (pack || arguments.length === 2) for (var i = 0, l = from.length, ar; i < l; i++) {
      if (ar || !(i in from)) {
          if (!ar) ar = Array.prototype.slice.call(from, 0, i);
          ar[i] = from[i];
      }
  }
  return to.concat(ar || Array.prototype.slice.call(from));
}

typeof SuppressedError === "function" ? SuppressedError : function (error, suppressed, message) {
  var e = new Error(message);
  return e.name = "SuppressedError", e.error = error, e.suppressed = suppressed, e;
};

function isFunction(value) {
    return typeof value === 'function';
}

function createErrorClass(createImpl) {
    var _super = function (instance) {
        Error.call(instance);
        instance.stack = new Error().stack;
    };
    var ctorFunc = createImpl(_super);
    ctorFunc.prototype = Object.create(Error.prototype);
    ctorFunc.prototype.constructor = ctorFunc;
    return ctorFunc;
}

var UnsubscriptionError = createErrorClass(function (_super) {
    return function UnsubscriptionErrorImpl(errors) {
        _super(this);
        this.message = errors
            ? errors.length + " errors occurred during unsubscription:\n" + errors.map(function (err, i) { return i + 1 + ") " + err.toString(); }).join('\n  ')
            : '';
        this.name = 'UnsubscriptionError';
        this.errors = errors;
    };
});

function arrRemove(arr, item) {
    if (arr) {
        var index = arr.indexOf(item);
        0 <= index && arr.splice(index, 1);
    }
}

var Subscription = (function () {
    function Subscription(initialTeardown) {
        this.initialTeardown = initialTeardown;
        this.closed = false;
        this._parentage = null;
        this._finalizers = null;
    }
    Subscription.prototype.unsubscribe = function () {
        var e_1, _a, e_2, _b;
        var errors;
        if (!this.closed) {
            this.closed = true;
            var _parentage = this._parentage;
            if (_parentage) {
                this._parentage = null;
                if (Array.isArray(_parentage)) {
                    try {
                        for (var _parentage_1 = __values(_parentage), _parentage_1_1 = _parentage_1.next(); !_parentage_1_1.done; _parentage_1_1 = _parentage_1.next()) {
                            var parent_1 = _parentage_1_1.value;
                            parent_1.remove(this);
                        }
                    }
                    catch (e_1_1) { e_1 = { error: e_1_1 }; }
                    finally {
                        try {
                            if (_parentage_1_1 && !_parentage_1_1.done && (_a = _parentage_1.return)) _a.call(_parentage_1);
                        }
                        finally { if (e_1) throw e_1.error; }
                    }
                }
                else {
                    _parentage.remove(this);
                }
            }
            var initialFinalizer = this.initialTeardown;
            if (isFunction(initialFinalizer)) {
                try {
                    initialFinalizer();
                }
                catch (e) {
                    errors = e instanceof UnsubscriptionError ? e.errors : [e];
                }
            }
            var _finalizers = this._finalizers;
            if (_finalizers) {
                this._finalizers = null;
                try {
                    for (var _finalizers_1 = __values(_finalizers), _finalizers_1_1 = _finalizers_1.next(); !_finalizers_1_1.done; _finalizers_1_1 = _finalizers_1.next()) {
                        var finalizer = _finalizers_1_1.value;
                        try {
                            execFinalizer(finalizer);
                        }
                        catch (err) {
                            errors = errors !== null && errors !== void 0 ? errors : [];
                            if (err instanceof UnsubscriptionError) {
                                errors = __spreadArray(__spreadArray([], __read(errors)), __read(err.errors));
                            }
                            else {
                                errors.push(err);
                            }
                        }
                    }
                }
                catch (e_2_1) { e_2 = { error: e_2_1 }; }
                finally {
                    try {
                        if (_finalizers_1_1 && !_finalizers_1_1.done && (_b = _finalizers_1.return)) _b.call(_finalizers_1);
                    }
                    finally { if (e_2) throw e_2.error; }
                }
            }
            if (errors) {
                throw new UnsubscriptionError(errors);
            }
        }
    };
    Subscription.prototype.add = function (teardown) {
        var _a;
        if (teardown && teardown !== this) {
            if (this.closed) {
                execFinalizer(teardown);
            }
            else {
                if (teardown instanceof Subscription) {
                    if (teardown.closed || teardown._hasParent(this)) {
                        return;
                    }
                    teardown._addParent(this);
                }
                (this._finalizers = (_a = this._finalizers) !== null && _a !== void 0 ? _a : []).push(teardown);
            }
        }
    };
    Subscription.prototype._hasParent = function (parent) {
        var _parentage = this._parentage;
        return _parentage === parent || (Array.isArray(_parentage) && _parentage.includes(parent));
    };
    Subscription.prototype._addParent = function (parent) {
        var _parentage = this._parentage;
        this._parentage = Array.isArray(_parentage) ? (_parentage.push(parent), _parentage) : _parentage ? [_parentage, parent] : parent;
    };
    Subscription.prototype._removeParent = function (parent) {
        var _parentage = this._parentage;
        if (_parentage === parent) {
            this._parentage = null;
        }
        else if (Array.isArray(_parentage)) {
            arrRemove(_parentage, parent);
        }
    };
    Subscription.prototype.remove = function (teardown) {
        var _finalizers = this._finalizers;
        _finalizers && arrRemove(_finalizers, teardown);
        if (teardown instanceof Subscription) {
            teardown._removeParent(this);
        }
    };
    Subscription.EMPTY = (function () {
        var empty = new Subscription();
        empty.closed = true;
        return empty;
    })();
    return Subscription;
}());
var EMPTY_SUBSCRIPTION = Subscription.EMPTY;
function isSubscription(value) {
    return (value instanceof Subscription ||
        (value && 'closed' in value && isFunction(value.remove) && isFunction(value.add) && isFunction(value.unsubscribe)));
}
function execFinalizer(finalizer) {
    if (isFunction(finalizer)) {
        finalizer();
    }
    else {
        finalizer.unsubscribe();
    }
}

var config = {
    Promise: undefined};

var timeoutProvider = {
    setTimeout: function (handler, timeout) {
        var args = [];
        for (var _i = 2; _i < arguments.length; _i++) {
            args[_i - 2] = arguments[_i];
        }
        return setTimeout.apply(void 0, __spreadArray([handler, timeout], __read(args)));
    },
    clearTimeout: function (handle) {
        return (clearTimeout)(handle);
    },
    delegate: undefined,
};

function reportUnhandledError(err) {
    timeoutProvider.setTimeout(function () {
        {
            throw err;
        }
    });
}

function noop() { }

function errorContext(cb) {
    {
        cb();
    }
}

var Subscriber = (function (_super) {
    __extends(Subscriber, _super);
    function Subscriber(destination) {
        var _this = _super.call(this) || this;
        _this.isStopped = false;
        if (destination) {
            _this.destination = destination;
            if (isSubscription(destination)) {
                destination.add(_this);
            }
        }
        else {
            _this.destination = EMPTY_OBSERVER;
        }
        return _this;
    }
    Subscriber.create = function (next, error, complete) {
        return new SafeSubscriber(next, error, complete);
    };
    Subscriber.prototype.next = function (value) {
        if (this.isStopped) ;
        else {
            this._next(value);
        }
    };
    Subscriber.prototype.error = function (err) {
        if (this.isStopped) ;
        else {
            this.isStopped = true;
            this._error(err);
        }
    };
    Subscriber.prototype.complete = function () {
        if (this.isStopped) ;
        else {
            this.isStopped = true;
            this._complete();
        }
    };
    Subscriber.prototype.unsubscribe = function () {
        if (!this.closed) {
            this.isStopped = true;
            _super.prototype.unsubscribe.call(this);
            this.destination = null;
        }
    };
    Subscriber.prototype._next = function (value) {
        this.destination.next(value);
    };
    Subscriber.prototype._error = function (err) {
        try {
            this.destination.error(err);
        }
        finally {
            this.unsubscribe();
        }
    };
    Subscriber.prototype._complete = function () {
        try {
            this.destination.complete();
        }
        finally {
            this.unsubscribe();
        }
    };
    return Subscriber;
}(Subscription));
var ConsumerObserver = (function () {
    function ConsumerObserver(partialObserver) {
        this.partialObserver = partialObserver;
    }
    ConsumerObserver.prototype.next = function (value) {
        var partialObserver = this.partialObserver;
        if (partialObserver.next) {
            try {
                partialObserver.next(value);
            }
            catch (error) {
                handleUnhandledError(error);
            }
        }
    };
    ConsumerObserver.prototype.error = function (err) {
        var partialObserver = this.partialObserver;
        if (partialObserver.error) {
            try {
                partialObserver.error(err);
            }
            catch (error) {
                handleUnhandledError(error);
            }
        }
        else {
            handleUnhandledError(err);
        }
    };
    ConsumerObserver.prototype.complete = function () {
        var partialObserver = this.partialObserver;
        if (partialObserver.complete) {
            try {
                partialObserver.complete();
            }
            catch (error) {
                handleUnhandledError(error);
            }
        }
    };
    return ConsumerObserver;
}());
var SafeSubscriber = (function (_super) {
    __extends(SafeSubscriber, _super);
    function SafeSubscriber(observerOrNext, error, complete) {
        var _this = _super.call(this) || this;
        var partialObserver;
        if (isFunction(observerOrNext) || !observerOrNext) {
            partialObserver = {
                next: (observerOrNext !== null && observerOrNext !== void 0 ? observerOrNext : undefined),
                error: error !== null && error !== void 0 ? error : undefined,
                complete: complete !== null && complete !== void 0 ? complete : undefined,
            };
        }
        else {
            {
                partialObserver = observerOrNext;
            }
        }
        _this.destination = new ConsumerObserver(partialObserver);
        return _this;
    }
    return SafeSubscriber;
}(Subscriber));
function handleUnhandledError(error) {
    {
        reportUnhandledError(error);
    }
}
function defaultErrorHandler(err) {
    throw err;
}
var EMPTY_OBSERVER = {
    closed: true,
    next: noop,
    error: defaultErrorHandler,
    complete: noop,
};

var observable = (function () { return (typeof Symbol === 'function' && Symbol.observable) || '@@observable'; })();

function identity(x) {
    return x;
}

function pipeFromArray(fns) {
    if (fns.length === 0) {
        return identity;
    }
    if (fns.length === 1) {
        return fns[0];
    }
    return function piped(input) {
        return fns.reduce(function (prev, fn) { return fn(prev); }, input);
    };
}

var Observable = (function () {
    function Observable(subscribe) {
        if (subscribe) {
            this._subscribe = subscribe;
        }
    }
    Observable.prototype.lift = function (operator) {
        var observable = new Observable();
        observable.source = this;
        observable.operator = operator;
        return observable;
    };
    Observable.prototype.subscribe = function (observerOrNext, error, complete) {
        var _this = this;
        var subscriber = isSubscriber(observerOrNext) ? observerOrNext : new SafeSubscriber(observerOrNext, error, complete);
        errorContext(function () {
            var _a = _this, operator = _a.operator, source = _a.source;
            subscriber.add(operator
                ?
                    operator.call(subscriber, source)
                : source
                    ?
                        _this._subscribe(subscriber)
                    :
                        _this._trySubscribe(subscriber));
        });
        return subscriber;
    };
    Observable.prototype._trySubscribe = function (sink) {
        try {
            return this._subscribe(sink);
        }
        catch (err) {
            sink.error(err);
        }
    };
    Observable.prototype.forEach = function (next, promiseCtor) {
        var _this = this;
        promiseCtor = getPromiseCtor(promiseCtor);
        return new promiseCtor(function (resolve, reject) {
            var subscriber = new SafeSubscriber({
                next: function (value) {
                    try {
                        next(value);
                    }
                    catch (err) {
                        reject(err);
                        subscriber.unsubscribe();
                    }
                },
                error: reject,
                complete: resolve,
            });
            _this.subscribe(subscriber);
        });
    };
    Observable.prototype._subscribe = function (subscriber) {
        var _a;
        return (_a = this.source) === null || _a === void 0 ? void 0 : _a.subscribe(subscriber);
    };
    Observable.prototype[observable] = function () {
        return this;
    };
    Observable.prototype.pipe = function () {
        var operations = [];
        for (var _i = 0; _i < arguments.length; _i++) {
            operations[_i] = arguments[_i];
        }
        return pipeFromArray(operations)(this);
    };
    Observable.prototype.toPromise = function (promiseCtor) {
        var _this = this;
        promiseCtor = getPromiseCtor(promiseCtor);
        return new promiseCtor(function (resolve, reject) {
            var value;
            _this.subscribe(function (x) { return (value = x); }, function (err) { return reject(err); }, function () { return resolve(value); });
        });
    };
    Observable.create = function (subscribe) {
        return new Observable(subscribe);
    };
    return Observable;
}());
function getPromiseCtor(promiseCtor) {
    var _a;
    return (_a = promiseCtor !== null && promiseCtor !== void 0 ? promiseCtor : config.Promise) !== null && _a !== void 0 ? _a : Promise;
}
function isObserver(value) {
    return value && isFunction(value.next) && isFunction(value.error) && isFunction(value.complete);
}
function isSubscriber(value) {
    return (value && value instanceof Subscriber) || (isObserver(value) && isSubscription(value));
}

var ObjectUnsubscribedError = createErrorClass(function (_super) {
    return function ObjectUnsubscribedErrorImpl() {
        _super(this);
        this.name = 'ObjectUnsubscribedError';
        this.message = 'object unsubscribed';
    };
});

var Subject = (function (_super) {
    __extends(Subject, _super);
    function Subject() {
        var _this = _super.call(this) || this;
        _this.closed = false;
        _this.currentObservers = null;
        _this.observers = [];
        _this.isStopped = false;
        _this.hasError = false;
        _this.thrownError = null;
        return _this;
    }
    Subject.prototype.lift = function (operator) {
        var subject = new AnonymousSubject(this, this);
        subject.operator = operator;
        return subject;
    };
    Subject.prototype._throwIfClosed = function () {
        if (this.closed) {
            throw new ObjectUnsubscribedError();
        }
    };
    Subject.prototype.next = function (value) {
        var _this = this;
        errorContext(function () {
            var e_1, _a;
            _this._throwIfClosed();
            if (!_this.isStopped) {
                if (!_this.currentObservers) {
                    _this.currentObservers = Array.from(_this.observers);
                }
                try {
                    for (var _b = __values(_this.currentObservers), _c = _b.next(); !_c.done; _c = _b.next()) {
                        var observer = _c.value;
                        observer.next(value);
                    }
                }
                catch (e_1_1) { e_1 = { error: e_1_1 }; }
                finally {
                    try {
                        if (_c && !_c.done && (_a = _b.return)) _a.call(_b);
                    }
                    finally { if (e_1) throw e_1.error; }
                }
            }
        });
    };
    Subject.prototype.error = function (err) {
        var _this = this;
        errorContext(function () {
            _this._throwIfClosed();
            if (!_this.isStopped) {
                _this.hasError = _this.isStopped = true;
                _this.thrownError = err;
                var observers = _this.observers;
                while (observers.length) {
                    observers.shift().error(err);
                }
            }
        });
    };
    Subject.prototype.complete = function () {
        var _this = this;
        errorContext(function () {
            _this._throwIfClosed();
            if (!_this.isStopped) {
                _this.isStopped = true;
                var observers = _this.observers;
                while (observers.length) {
                    observers.shift().complete();
                }
            }
        });
    };
    Subject.prototype.unsubscribe = function () {
        this.isStopped = this.closed = true;
        this.observers = this.currentObservers = null;
    };
    Object.defineProperty(Subject.prototype, "observed", {
        get: function () {
            var _a;
            return ((_a = this.observers) === null || _a === void 0 ? void 0 : _a.length) > 0;
        },
        enumerable: false,
        configurable: true
    });
    Subject.prototype._trySubscribe = function (subscriber) {
        this._throwIfClosed();
        return _super.prototype._trySubscribe.call(this, subscriber);
    };
    Subject.prototype._subscribe = function (subscriber) {
        this._throwIfClosed();
        this._checkFinalizedStatuses(subscriber);
        return this._innerSubscribe(subscriber);
    };
    Subject.prototype._innerSubscribe = function (subscriber) {
        var _this = this;
        var _a = this, hasError = _a.hasError, isStopped = _a.isStopped, observers = _a.observers;
        if (hasError || isStopped) {
            return EMPTY_SUBSCRIPTION;
        }
        this.currentObservers = null;
        observers.push(subscriber);
        return new Subscription(function () {
            _this.currentObservers = null;
            arrRemove(observers, subscriber);
        });
    };
    Subject.prototype._checkFinalizedStatuses = function (subscriber) {
        var _a = this, hasError = _a.hasError, thrownError = _a.thrownError, isStopped = _a.isStopped;
        if (hasError) {
            subscriber.error(thrownError);
        }
        else if (isStopped) {
            subscriber.complete();
        }
    };
    Subject.prototype.asObservable = function () {
        var observable = new Observable();
        observable.source = this;
        return observable;
    };
    Subject.create = function (destination, source) {
        return new AnonymousSubject(destination, source);
    };
    return Subject;
}(Observable));
var AnonymousSubject = (function (_super) {
    __extends(AnonymousSubject, _super);
    function AnonymousSubject(destination, source) {
        var _this = _super.call(this) || this;
        _this.destination = destination;
        _this.source = source;
        return _this;
    }
    AnonymousSubject.prototype.next = function (value) {
        var _a, _b;
        (_b = (_a = this.destination) === null || _a === void 0 ? void 0 : _a.next) === null || _b === void 0 ? void 0 : _b.call(_a, value);
    };
    AnonymousSubject.prototype.error = function (err) {
        var _a, _b;
        (_b = (_a = this.destination) === null || _a === void 0 ? void 0 : _a.error) === null || _b === void 0 ? void 0 : _b.call(_a, err);
    };
    AnonymousSubject.prototype.complete = function () {
        var _a, _b;
        (_b = (_a = this.destination) === null || _a === void 0 ? void 0 : _a.complete) === null || _b === void 0 ? void 0 : _b.call(_a);
    };
    AnonymousSubject.prototype._subscribe = function (subscriber) {
        var _a, _b;
        return (_b = (_a = this.source) === null || _a === void 0 ? void 0 : _a.subscribe(subscriber)) !== null && _b !== void 0 ? _b : EMPTY_SUBSCRIPTION;
    };
    return AnonymousSubject;
}(Subject));

var dateTimestampProvider = {
    now: function () {
        return (dateTimestampProvider.delegate || Date).now();
    },
    delegate: undefined,
};

var ReplaySubject = (function (_super) {
    __extends(ReplaySubject, _super);
    function ReplaySubject(_bufferSize, _windowTime, _timestampProvider) {
        if (_bufferSize === void 0) { _bufferSize = Infinity; }
        if (_windowTime === void 0) { _windowTime = Infinity; }
        if (_timestampProvider === void 0) { _timestampProvider = dateTimestampProvider; }
        var _this = _super.call(this) || this;
        _this._bufferSize = _bufferSize;
        _this._windowTime = _windowTime;
        _this._timestampProvider = _timestampProvider;
        _this._buffer = [];
        _this._infiniteTimeWindow = true;
        _this._infiniteTimeWindow = _windowTime === Infinity;
        _this._bufferSize = Math.max(1, _bufferSize);
        _this._windowTime = Math.max(1, _windowTime);
        return _this;
    }
    ReplaySubject.prototype.next = function (value) {
        var _a = this, isStopped = _a.isStopped, _buffer = _a._buffer, _infiniteTimeWindow = _a._infiniteTimeWindow, _timestampProvider = _a._timestampProvider, _windowTime = _a._windowTime;
        if (!isStopped) {
            _buffer.push(value);
            !_infiniteTimeWindow && _buffer.push(_timestampProvider.now() + _windowTime);
        }
        this._trimBuffer();
        _super.prototype.next.call(this, value);
    };
    ReplaySubject.prototype._subscribe = function (subscriber) {
        this._throwIfClosed();
        this._trimBuffer();
        var subscription = this._innerSubscribe(subscriber);
        var _a = this, _infiniteTimeWindow = _a._infiniteTimeWindow, _buffer = _a._buffer;
        var copy = _buffer.slice();
        for (var i = 0; i < copy.length && !subscriber.closed; i += _infiniteTimeWindow ? 1 : 2) {
            subscriber.next(copy[i]);
        }
        this._checkFinalizedStatuses(subscriber);
        return subscription;
    };
    ReplaySubject.prototype._trimBuffer = function () {
        var _a = this, _bufferSize = _a._bufferSize, _timestampProvider = _a._timestampProvider, _buffer = _a._buffer, _infiniteTimeWindow = _a._infiniteTimeWindow;
        var adjustedBufferSize = (_infiniteTimeWindow ? 1 : 2) * _bufferSize;
        _bufferSize < Infinity && adjustedBufferSize < _buffer.length && _buffer.splice(0, _buffer.length - adjustedBufferSize);
        if (!_infiniteTimeWindow) {
            var now = _timestampProvider.now();
            var last = 0;
            for (var i = 1; i < _buffer.length && _buffer[i] <= now; i += 2) {
                last = i;
            }
            last && _buffer.splice(0, last + 1);
        }
    };
    return ReplaySubject;
}(Subject));

/**
 * @license Angular v18.2.13
 * (c) 2010-2024 Google LLC. https://angular.io/
 * License: MIT
 */


/**
 * Exposes the value of an Angular `Signal` as an RxJS `Observable`.
 *
 * The signal's value will be propagated into the `Observable`'s subscribers using an `effect`.
 *
 * `toObservable` must be called in an injection context unless an injector is provided via options.
 *
 * @developerPreview
 */
function toObservable(source, options) {
    !options?.injector && assertInInjectionContext(toObservable);
    const injector = options?.injector ?? inject(Injector);
    const subject = new ReplaySubject(1);
    const watcher = effect(() => {
        let value;
        try {
            value = source();
        }
        catch (err) {
            untracked(() => subject.error(err));
            return;
        }
        untracked(() => subject.next(value));
    }, { injector, manualCleanup: true });
    injector.get(DestroyRef).onDestroy(() => {
        watcher.destroy();
        subject.complete();
    });
    return subject.asObservable();
}

const ROOT_SELECTOR = '[data-cy-root]';
/**
 * Gets the root element used to mount the component.
 * @returns {HTMLElement} The root element
 * @throws {Error} If the root element is not found
 */
const getContainerEl = () => {
    const el = document.querySelector(ROOT_SELECTOR);
    if (el) {
        return el;
    }
    throw Error(`No element found that matches selector ${ROOT_SELECTOR}. Please add a root element with data-cy-root attribute to your "component-index.html" file so that Cypress can attach your component to the DOM.`);
};
/**
 * Utility function to register CT side effects and run cleanup code during the "test:before:run" Cypress hook
 * @param optionalCallback Callback to be called before the next test runs
 */
function setupHooks(optionalCallback) {
    // We don't want CT side effects to run when e2e
    // testing so we early return.
    // System test to verify CT side effects do not pollute e2e: system-tests/test/e2e_with_mount_import_spec.ts
    if (Cypress.testingType !== 'component') {
        return;
    }
    // When running component specs, we cannot allow "cy.visit"
    // because it will wipe out our preparation work, and does not make much sense
    // thus we overwrite "cy.visit" to throw an error
    Cypress.Commands.overwrite('visit', () => {
        throw new Error('cy.visit from a component spec is not allowed');
    });
    Cypress.Commands.overwrite('session', () => {
        throw new Error('cy.session from a component spec is not allowed');
    });
    Cypress.Commands.overwrite('origin', () => {
        throw new Error('cy.origin from a component spec is not allowed');
    });
    // @ts-ignore
    Cypress.on('test:before:after:run:async', () => {
        optionalCallback === null || optionalCallback === void 0 ? void 0 : optionalCallback();
    });
}

/**
 * @hack fixes "Mocha has already been patched with Zone" error.
 */
// @ts-ignore
window.Mocha['__zone_patch__'] = false;
let activeFixture = null;
let activeInternalSubscriptions = [];
function cleanup() {
    // Not public, we need to call this to remove the last component from the DOM
    try {
        getTestBed().tearDownTestingModule();
    }
    catch (e) {
        const notSupportedError = new Error(`Failed to teardown component. The version of Angular you are using may not be officially supported.`);
        notSupportedError.docsUrl = 'https://on.cypress.io/frameworks';
        throw notSupportedError;
    }
    // clean up internal subscriptions if any exist. We use this for two-way data binding for
    // signal() models
    activeInternalSubscriptions.forEach((subscription) => {
        subscription.unsubscribe();
    });
    getTestBed().resetTestingModule();
    activeFixture = null;
    activeInternalSubscriptions = [];
}
let CypressAngularErrorHandler = class CypressAngularErrorHandler {
    handleError(error) {
        throw error;
    }
};
CypressAngularErrorHandler = __decorate([
    Injectable()
], CypressAngularErrorHandler);
/**
 * Bootstraps the TestModuleMetaData passed to the TestBed
 *
 * @param {Type<T>} component Angular component being mounted
 * @param {MountConfig} config TestBed configuration passed into the mount function
 * @returns {MountConfig} MountConfig
 */
function bootstrapModule(component, config) {
    var _a;
    const { componentProperties } = config, testModuleMetaData = __rest(config, ["componentProperties"]);
    if (!testModuleMetaData.declarations) {
        testModuleMetaData.declarations = [];
    }
    if (!testModuleMetaData.imports) {
        testModuleMetaData.imports = [];
    }
    if (!testModuleMetaData.providers) {
        testModuleMetaData.providers = [];
    }
    // Replace default error handler since it will swallow uncaught exceptions.
    // We want these to be uncaught so Cypress catches it and fails the test
    testModuleMetaData.providers.push({
        provide: ErrorHandler,
        useClass: CypressAngularErrorHandler,
    });
    // check if the component is a standalone component
    if ((_a = component.ɵcmp) === null || _a === void 0 ? void 0 : _a.standalone) {
        testModuleMetaData.imports.push(component);
    }
    else {
        testModuleMetaData.declarations.push(component);
    }
    if (!testModuleMetaData.imports.includes(CommonModule)) {
        testModuleMetaData.imports.push(CommonModule);
    }
    return testModuleMetaData;
}
let CypressTestComponentRenderer = class CypressTestComponentRenderer extends TestComponentRenderer {
    insertRootElement(rootElId) {
        this.removeAllRootElements();
        const rootElement = getContainerEl();
        rootElement.setAttribute('id', rootElId);
    }
    removeAllRootElements() {
        getContainerEl().innerHTML = '';
    }
};
CypressTestComponentRenderer = __decorate([
    Injectable()
], CypressTestComponentRenderer);
/**
 * Initializes the TestBed
 *
 * @param {Type<T> | string} component Angular component being mounted or its template
 * @param {MountConfig} config TestBed configuration passed into the mount function
 * @returns {Type<T>} componentFixture
 */
function initTestBed(component, config) {
    const componentFixture = createComponentFixture(component);
    getTestBed().configureTestingModule(Object.assign({}, bootstrapModule(componentFixture, config)));
    getTestBed().overrideProvider(TestComponentRenderer, { useValue: new CypressTestComponentRenderer() });
    return componentFixture;
}
// if using the Wrapper Component (template strings), the component itself cannot be
// a standalone component
let WrapperComponent = class WrapperComponent {
};
WrapperComponent = __decorate([
    Component({ selector: 'cy-wrapper-component', template: '', standalone: false })
], WrapperComponent);
/**
 * Returns the Component if Type<T> or creates a WrapperComponent
 *
 * @param {Type<T> | string} component The component you want to create a fixture of
 * @returns {Type<T> | WrapperComponent}
 */
function createComponentFixture(component) {
    if (typeof component === 'string') {
        // getTestBed().overrideTemplate is available in v14+
        // The static TestBed.overrideTemplate is available across versions
        TestBed.overrideTemplate(WrapperComponent, component);
        return WrapperComponent;
    }
    return component;
}
/**
 * Creates the ComponentFixture
 *
 * @param {Type<T>} component Angular component being mounted
 * @param {MountConfig<T>} config MountConfig

 * @returns {ComponentFixture<T>} ComponentFixture
 */
function setupFixture(component, config) {
    const fixture = getTestBed().createComponent(component);
    setupComponent(config, fixture);
    fixture.whenStable().then(() => {
        var _a;
        fixture.autoDetectChanges((_a = config.autoDetectChanges) !== null && _a !== void 0 ? _a : true);
    }).catch((e) => {
        // If this promise does not settle in Angular 19 it is rejected
        // https://github.com/angular/angular/blob/main/CHANGELOG.md#1900-2024-11-19
        // eslint-disable-next-line no-console
        console.error(e);
    });
    return fixture;
}
// Best known way to currently detect whether or not a function is a signal is if the signal symbol exists.
// From there, we can take our best guess based on what exists on the object itself.
// @see https://github.com/cypress-io/cypress/issues/29731.
function isSignal(prop) {
    try {
        const symbol = Object.getOwnPropertySymbols(prop).find((symbol) => symbol.toString() === 'Symbol(SIGNAL)');
        return !!symbol;
    }
    catch (e) {
        // likely a primitive type, object, array, or something else (i.e. not a signal).
        // We can return false here.
        return false;
    }
}
// currently not a great way to detect if a function is an InputSignal.
// @see https://github.com/cypress-io/cypress/issues/29731.
function isInputSignal(prop) {
    return isSignal(prop) && typeof prop === 'function' && prop['name'] === 'inputValueFn';
}
// currently not a great way to detect if a function is a Model Signal.
// @see https://github.com/cypress-io/cypress/issues/29731.
function isModelSignal(prop) {
    return isSignal(prop) && isWritableSignal(prop) && typeof prop.subscribe === 'function';
}
// currently not a great way to detect if a function is a Writable Signal.
// @see https://github.com/cypress-io/cypress/issues/29731.
function isWritableSignal(prop) {
    return isSignal(prop) && typeof prop === 'function' && typeof prop.set === 'function';
}
function registerSignalEventsIfNeeded(propKey, propValue, componentValue, injector, fixture) {
    const isPropValueASignal = isSignal(propValue);
    if (isPropValueASignal) {
        // propValue -> componentValue
        const convertedToObservable = toObservable(propValue, {
            injector,
        });
        // push the subscription into an array to be cleaned up at the end of the test
        // to prevent a memory leak
        activeInternalSubscriptions.push(convertedToObservable.subscribe((value) => {
            // keep the component up to date as prop signal changes
            fixture.componentRef.setInput(propKey, value);
        }));
    }
    const isComponentValueAModelSignal = isModelSignal(componentValue);
    if (isPropValueASignal && isComponentValueAModelSignal) {
        // propValue <- componentValue
        const modelChanged$ = toObservable(componentValue, {
            injector,
        });
        activeInternalSubscriptions.push(modelChanged$.subscribe((value) => {
            propValue.set(value);
        }));
    }
}
// In the case of signals, if we need to create an output spy, we need to check first whether or not a user has one defined first or has it created through
// autoSpyOutputs. If so, we need to subscribe to the writable signal to push updates into the event emitter. We do NOT observe input signals and output spies will not
// work for input signals.
function detectAndRegisterOutputSpyToSignal(config, component, key, injector) {
    if (config.componentProperties) {
        const expectedChangeKey = `${key}Change`;
        let changeKeyIfExists = !!Object.keys(config.componentProperties).find((componentKey) => componentKey === expectedChangeKey);
        if (changeKeyIfExists) {
            component[expectedChangeKey] =
                // @ts-expect-error
                config.componentProperties[expectedChangeKey];
        }
        // since spies do NOT make change handlers by default, similar to the Output() decorator, we need to create the spy and subscribe to the signal
        if (!changeKeyIfExists && config.autoSpyOutputs) {
            component[expectedChangeKey] = createOutputSpy(`${expectedChangeKey}Spy`);
            changeKeyIfExists = true;
        }
        if (changeKeyIfExists) {
            const componentValue = component[key];
            // if the user passed in a change key or we created one due to config.autoSpyOutputs being set to true for a given signal,
            // we will create a subscriber that will emit an event every time the value inside the signal changes. We only do this
            // if the signal is writable and not an input signal.
            if (isWritableSignal(componentValue) && !isInputSignal(componentValue)) {
                toObservable(componentValue, {
                    injector,
                }).subscribe((value) => {
                    var _a;
                    (_a = component[expectedChangeKey]) === null || _a === void 0 ? void 0 : _a.emit(value);
                });
            }
        }
    }
}
/**
 * Gets the componentInstance and Object.assigns any componentProperties() passed in the MountConfig
 *
 * @param {MountConfig} config TestBed configuration passed into the mount function
 * @param {ComponentFixture<T>} fixture Fixture for debugging and testing a component.
 * @returns {T} Component being mounted
 */
function setupComponent(config, fixture) {
    let component = fixture.componentInstance;
    const injector = fixture.componentRef.injector;
    if (config === null || config === void 0 ? void 0 : config.componentProperties) {
        if (component instanceof WrapperComponent) {
            component = Object.assign(component, config.componentProperties);
        }
        getComponentInputs(fixture.componentRef.componentType).forEach((key) => {
            var _a;
            // only assign props if they are passed into the component
            if ((_a = config === null || config === void 0 ? void 0 : config.componentProperties) === null || _a === void 0 ? void 0 : _a.hasOwnProperty(key)) {
                // @ts-expect-error
                const passedInValue = config === null || config === void 0 ? void 0 : config.componentProperties[key];
                registerSignalEventsIfNeeded(key, passedInValue, component[key], injector, fixture);
                detectAndRegisterOutputSpyToSignal(config, component, key, injector);
                fixture.componentRef.setInput(key, isSignal(passedInValue) ? passedInValue() : passedInValue);
            }
        });
        getComponentOutputs(fixture.componentRef.componentType).forEach((key) => {
            var _a, _b;
            const property = component[key];
            // With the introduction of https://github.com/cypress-io/cypress/pull/31993, we want to make sure that component inputs are reference safe inside cy.mount().
            // However, the exception to this is if the user passes in a Cypress output spy as a property in order to maintain backwards compatibility.
            // @ts-expect-error
            if (property instanceof EventEmitter || (((_a = config === null || config === void 0 ? void 0 : config.componentProperties) === null || _a === void 0 ? void 0 : _a.hasOwnProperty(key)) && (config === null || config === void 0 ? void 0 : config.componentProperties[key]) instanceof EventEmitter)) {
                // only assign props if they are passed into the component
                if ((_b = config === null || config === void 0 ? void 0 : config.componentProperties) === null || _b === void 0 ? void 0 : _b.hasOwnProperty(key)) {
                    // @ts-expect-error
                    const passedInValue = config === null || config === void 0 ? void 0 : config.componentProperties[key];
                    component[key] = passedInValue;
                }
            }
        });
    }
    if (config.autoSpyOutputs) {
        Object.keys(component).forEach((key) => {
            const property = component[key];
            if (property instanceof EventEmitter) {
                component[key] = createOutputSpy(`${key}Spy`);
            }
        });
    }
    // Manually call ngOnChanges when mounting components using the class syntax.
    // This is necessary because we are assigning input values to the class directly
    // on mount and therefore the ngOnChanges() lifecycle is not triggered.
    if (component.ngOnChanges && config.componentProperties) {
        const { componentProperties } = config;
        const simpleChanges = Object.entries(componentProperties).reduce((acc, [key, value]) => {
            acc[key] = new SimpleChange(null, value, true);
            return acc;
        }, {});
        if (Object.keys(componentProperties).length > 0) {
            component.ngOnChanges(simpleChanges);
        }
    }
}
/**
 * Gets the input properties of a component - cannot rely on Object.keys() because inclusion of optional properties depends on useDefineForClassFields=true
 *   Since Angular 15, useDefineForClassFields=false
 * @param componentType
 * @returns array of input property names
 */
function getComponentInputs(componentType) {
    var _a;
    // Access Angular's metadata to get input properties
    const propMetadata = ((_a = componentType.ɵcmp) === null || _a === void 0 ? void 0 : _a.inputs) || {};
    return Object.keys(propMetadata);
}
function getComponentOutputs(componentType) {
    var _a;
    // Access Angular's metadata to get output properties
    const propMetadata = ((_a = componentType.ɵcmp) === null || _a === void 0 ? void 0 : _a.outputs) || {};
    return Object.keys(propMetadata);
}
/**
 * Mounts an Angular component inside Cypress browser
 *
 * @param component Angular component being mounted or its template
 * @param config configuration used to configure the TestBed
 * @example
 * import { mount } from '@cypress/angular'
 * import { StepperComponent } from './stepper.component'
 * import { MyService } from 'services/my.service'
 * import { SharedModule } from 'shared/shared.module';
 * it('mounts', () => {
 *    mount(StepperComponent, {
 *      providers: [MyService],
 *      imports: [SharedModule]
 *    })
 *    cy.get('[data-cy=increment]').click()
 *    cy.get('[data-cy=counter]').should('have.text', '1')
 * })
 *
 * // or
 *
 * it('mounts with template', () => {
 *   mount('<app-stepper></app-stepper>', {
 *     declarations: [StepperComponent],
 *   })
 * })
 *
 * @see {@link https://on.cypress.io/mounting-angular} for more details.
 *
 * @returns A component and component fixture
 */
function mount(component, config = {}) {
    // Remove last mounted component if cy.mount is called more than once in a test
    if (activeFixture) {
        cleanup();
    }
    const componentFixture = initTestBed(component, config);
    activeFixture = setupFixture(componentFixture, config);
    const mountResponse = {
        fixture: activeFixture,
        component: activeFixture.componentInstance,
    };
    const logMessage = typeof component === 'string' ? 'Component' : componentFixture.name;
    Cypress.log({
        name: 'mount',
        message: logMessage,
        consoleProps: () => ({ result: mountResponse }),
    });
    return cy.wrap(mountResponse, { log: false });
}
/**
 * Creates a new Event Emitter and then spies on it's `emit` method
 *
 * @param {string} alias name you want to use for your cy.spy() alias
 * @returns EventEmitter<T>
 * @example
 * import { StepperComponent } from './stepper.component'
 * import { mount, createOutputSpy } from '@cypress/angular'
 *
 * it('Has spy', () => {
 *   mount(StepperComponent, { componentProperties: { change: createOutputSpy('changeSpy') } })
 *   cy.get('[data-cy=increment]').click()
 *   cy.get('@changeSpy').should('have.been.called')
 * })
 *
 * // Or for use with Angular Signals following the output nomenclature.
 * // see https://v17.angular.io/guide/model-inputs#differences-between-model-and-input/
 *
 * it('Has spy', () => {
 *   mount(StepperComponent, { componentProperties: { count: signal(0), countChange: createOutputSpy('countChange') } })
 *   cy.get('[data-cy=increment]').click()
 *   cy.get('@countChange').should('have.been.called')
 * })
 */
const createOutputSpy = (alias) => {
    const emitter = new EventEmitter();
    cy.spy(emitter, 'emit').as(alias);
    return emitter;
};
// Only needs to run once, we reset before each test
getTestBed().initTestEnvironment(BrowserDynamicTestingModule, platformBrowserDynamicTesting(), {
    teardown: { destroyAfterEach: false },
});
setupHooks(cleanup);

export { CypressTestComponentRenderer, createOutputSpy, mount };
