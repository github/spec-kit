var assert = require('assert');
var throttle = require('./');

describe('throttle', function(){
  function counter() {
    function count(){
      count.invoked++;
    }
    count.invoked = 0;
    return count;
  }

  it('should throttle a function', function(done){
    var count = counter();
    var wait = 100;
    var total = 500;
    var fn = throttle(count, wait);
    var interval = setInterval(fn, 20);
    setTimeout(function(){
      clearInterval(interval);
      assert(count.invoked === (total / wait));
      done();
    }, total + 5);
  });

  it('should call the function last time', function(done){
    var count = counter();
    var wait = 100;
    var fn = throttle(count, wait);
    fn();
    fn();
    assert(count.invoked === 1);
    setTimeout(function(){
      assert(count.invoked === 2);
      done();
    }, wait + 5);
  });

  it('should pass last context', function(done){
    var wait = 100;
    var ctx;
    var fn = throttle(logctx, wait);
    var foo = {};
    var bar = {};
    fn.call(foo);
    fn.call(bar);
    assert(ctx === foo);
    setTimeout(function(){
      assert(ctx === bar);
      done();
    }, wait + 5);
    function logctx() {
      ctx = this;
    }
  });

  it('should pass last arguments', function(done){
    var wait = 100;
    var args;
    var fn = throttle(logargs, wait);
    fn.call(null, 1);
    fn.call(null, 2);
    assert(args && args[0] === 1);
    setTimeout(function(){
      assert(args && args[0] === 2);
      done();
    }, wait + 5);
    function logargs() {
      args = arguments;
    }
  });

});