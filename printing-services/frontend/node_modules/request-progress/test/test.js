'use strict';

var expect = require('expect.js');
var EventEmitter = require('events').EventEmitter;
var progress = require('../');

function normalizeStates(states) {
    states.forEach(function (state) {
        state.time.elapsed = Math.round(state.time.elapsed),
        state.time.remaining = state.time.remaining != null ? Math.round(state.time.remaining) : null;
        state.speed = state.speed != null ? Math.round(state.speed) : null;
    });
}

describe('request-progress', function () {
    var request;
    var states;
    var response;

    beforeEach(function () {
        states = [];
        request = new EventEmitter();
        response = new EventEmitter();

        request.on('progress', function (state) {
            states.push(JSON.parse(JSON.stringify(state)));
        });
    });

    it('should emit the progress event with the correct state information', function (done) {
        progress(request, { throttle: 0 })
        .on('end', function () {
            normalizeStates(states);

            expect(states).to.eql([{
                percent: 0.5,
                speed: null,
                size: { total: 10, transferred: 5, },
                time: { elapsed: 0, remaining: null }
            }, {
                percent: 0.8,
                speed: 7,
                size: { total: 10, transferred: 8 },
                time: { elapsed: 1, remaining: 0 }
            }, {
                percent: 1,
                speed: 8,
                size: { total: 10, transferred: 10 },
                time: { elapsed: 1, remaining: 0 }
            }]);

            done();
        });

        request.emit('request');
        request.emit('response', Object.assign(response, { headers: { 'content-length': 10 } }));

        setTimeout(function () {
            response.emit('data', new Buffer('aaaaa'));
        }, 25);

        setTimeout(function () {
            response.emit('data', new Buffer('bbb'));
        }, 1150);

        setTimeout(function () {
            response.emit('data', new Buffer('cc'));
            request.emit('end');
        }, 1250);
    });

    it('should provide request.progressState (and request.progressContext)', function (done) {
        progress(request, { throttle: 0 })
        .on('end', function () {
            expect(request.progressState).to.be(null);
            expect(request.progressContext).to.be(null);
            done();
        });

        expect(request.progressContext).to.be.an('object');
        expect(request.progressState).to.be(undefined);

        request.emit('request');
        request.emit('response', Object.assign(response, { headers: { 'content-length': 2 } }));

        expect(request.progressContext).to.be.an('object');
        expect(request.progressState).to.be.an('object');

        setTimeout(function () {
            response.emit('data', new Buffer('a'));
            expect(request.progressContext).to.be.an('object');
            expect(request.progressState).to.be.an('object');
            expect(request.progressState.percent).to.be(0.5);
        }, 25);

        setTimeout(function () {
            response.emit('data', new Buffer('b'));
            expect(request.progressContext).to.be.an('object');
            expect(request.progressState).to.be.an('object');
            expect(request.progressState.percent).to.be(1);
            request.emit('end');
        }, 100);
    });

    it('should have a option.delay default of 0', function () {
        progress(request);
        expect(request.progressContext.options.delay).to.be(0);
    });

    it('should respect the passed option.delay', function (done) {
        progress(request, { throttle: 0, delay: 250 })
        .on('end', function () {
            expect(states).to.have.length(2);
            expect(states[0].percent).to.be(0.6);
            expect(states[1].percent).to.be(1);

            done();
        });

        request.emit('request');
        request.emit('response', Object.assign(response, { headers: { 'content-length': 10 } }));

        setTimeout(function () {
            response.emit('data', new Buffer('aa'));
        }, 25);

        setTimeout(function () {
            response.emit('data', new Buffer('bb'));
        }, 200);

        setTimeout(function () {
            response.emit('data', new Buffer('cc'));
        }, 300);

        setTimeout(function () {
            response.emit('data', new Buffer('dddd'));
            request.emit('end');
        }, 400);
    });

    it('should have a option.throttle default of 1000', function () {
        progress(request);
        expect(request.progressContext.options.throttle).to.be(1000);
    });

    it('should respect the passed option.throttle', function (done) {
        progress(request, { throttle: 300, delay: 0 })
        .on('end', function () {
            expect(states).to.have.length(3);
            expect(states[0].percent).to.be(0.2);
            expect(states[1].percent).to.be(0.6);
            expect(states[2].percent).to.be(0.9);

            done();
        });

        request.emit('request');
        request.emit('response', Object.assign(response, { headers: { 'content-length': 10 } }));

        setTimeout(function () {
            response.emit('data', new Buffer('aa'));
        }, 25);

        setTimeout(function () {
            response.emit('data', new Buffer('bb'));
        }, 100);

        setTimeout(function () {
            response.emit('data', new Buffer('cc'));
        }, 300);

        setTimeout(function () {
            response.emit('data', new Buffer('dd'));
        }, 400);

        setTimeout(function () {
            response.emit('data', new Buffer('e'));
        }, 500);

        setTimeout(function () {
            response.emit('data', new Buffer('bf'));
            request.emit('end');
        }, 700);
    });

    it('should have a option.lengthHeader default of "content-length"', function () {
        progress(request);
        expect(request.progressContext.options.lengthHeader).to.be('content-length');
    });

    it('should use option.lengthHeader', function (done) {
        progress(request, {
            throttle: 0,
            lengthHeader: 'x-transfer-length'
        })
        .on('end', function () {
            expect(states).to.have.length(2);
            expect(states[0].percent).to.be(0.5);
            expect(states[0].size.total).to.be(10);
            expect(states[1].percent).to.be(1);
            expect(states[1].size.total).to.be(10);

            done();
        });

        request.emit('request');
        request.emit('response', Object.assign(response, {
            headers: { 'x-transfer-length': 10, 'content-length': 5 }
        }));

        setTimeout(function () {
            response.emit('data', new Buffer('aaaaa'));
        }, 25);

        setTimeout(function () {
            response.emit('data', new Buffer('bbbbb'));
            request.emit('end');
        }, 200);
    });

    it('should fail if response is already set', function () {
        request.response = { headers: { 'content-length': 10 } };

        expect(function () {
            progress(request);
        }).to.throwException(/too late/);
    });

    it('should deal with unknown content length', function (done) {
        progress(request, { throttle: 0 })
        .on('end', function () {
            normalizeStates(states);

            expect(states).to.eql([{
                percent: null,
                speed: null,
                size: { total: null, transferred: 5, },
                time: { elapsed: 0, remaining: null }
            }, {
                percent: null,
                speed: 10,
                size: { total: null, transferred: 12, },
                time: { elapsed: 1, remaining: null }
            }]);

            done();
        });

        request.emit('request');
        request.emit('response', Object.assign(response, { headers: {} }));

        setTimeout(function () {
            response.emit('data', new Buffer('aaaaa'));
        }, 25);

        setTimeout(function () {
            response.emit('data', new Buffer('bbbbbbb'));
            request.emit('end');
        }, 1150);
    });

    it('should deal with payloads higher than the content length', function (done) {
        progress(request, { throttle: 0 })
        .on('end', function () {
            normalizeStates(states);

            expect(states).to.eql([{
                percent: 0.5,
                speed: null,
                size: { total: 10, transferred: 5, },
                time: { elapsed: 0, remaining: null }
            }, {
                percent: 1,
                speed: 10,
                size: { total: 10, transferred: 12 },
                time: { elapsed: 1, remaining: 0 }
            }]);

            done();
        });

        request.emit('request');
        request.emit('response', Object.assign(response, { headers: { 'content-length': 10 } }));

        setTimeout(function () {
            response.emit('data', new Buffer('aaaaa'));
        }, 25);

        setTimeout(function () {
            response.emit('data', new Buffer('bbbbbbb'));
            request.emit('end');
        }, 1150);
    });

    it('should not report after the request ends', function (done) {
        progress(request, { throttle: 100 });

        request.emit('request');
        request.emit('response', Object.assign(response, { headers: { 'content-length': 10 } }));

        setTimeout(function () {
            response.emit('data', new Buffer('aa'));
        }, 25);

        setTimeout(function () {
            response.emit('data', new Buffer('bbbbbbbb'));
            request.emit('end');
        }, 50);

        setTimeout(function () {
            normalizeStates(states);

            expect(states).to.have.length(1);
            expect(states[0].percent).to.be(0.2);

            done();
        }, 500);
    });

    it('should not generate duplicate progress events if called twice', function (done) {
        progress(request, { throttle: 0 });
        progress(request, { throttle: 0 })
        .on('end', function () {
            expect(states).to.have.length(1);
            expect(states[0].percent).to.be(1);

            done();
        });

        request.emit('request');
        request.emit('response', Object.assign(response, { headers: { 'content-length': 2 } }));

        setTimeout(function () {
            response.emit('data', new Buffer('aa'));
            request.emit('end');
        }, 25);
    });

    it('should reset stuff on "request" event', function () {
        progress(request, { throttle: 0 });

        expect(request.progressContext).to.be.an('object');
        expect(request.progressState).to.be(undefined);

        request.emit('request');
        request.emit('response', Object.assign(response, { headers: { 'content-length': 2 } }));

        expect(request.progressContext).to.be.an('object');
        expect(request.progressState).to.be.an('object');

        request.emit('request');

        expect(request.progressContext).to.be.an('object');
        expect(request.progressState).to.be(null);
    });

    it('should hook into "data" event from the response and not the request', function (done) {
        // See: https://github.com/IndigoUnited/node-request-progress/issues/20

        progress(request, { throttle: 0 })
            .on('end', function () {
                expect(states).to.have.length(2);
                expect(states[0].percent).to.be(0.5);
                expect(states[1].percent).to.be(1);

                done();
            });

        request.emit('request');
        request.emit('response', Object.assign(response, { headers: { 'content-length': 4 } }));

        setTimeout(function () {
            response.emit('data', new Buffer('aa'));
        }, 25);

        setTimeout(function () {
            request.emit('data', new Buffer('aa'));
        }, 50);

        setTimeout(function () {
            response.emit('data', new Buffer('aa'));
            request.emit('end');
        }, 100);
    });
});
