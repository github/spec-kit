/*
  @license
	Rollup.js v3.29.4
	Sat, 21 Sep 2024 06:29:06 GMT - commit 2ef77c00ec2635d42697cff2c0567ccc8db34fb4

	https://github.com/rollup/rollup

	Released under the MIT License.
*/
'use strict';

const rollup = require('./rollup.js');
const fseventsImporter = require('./fsevents-importer.js');

class WatchEmitter {
    constructor() {
        this.currentHandlers = Object.create(null);
        this.persistentHandlers = Object.create(null);
    }
    // Will be overwritten by Rollup
    async close() { }
    emit(event, ...parameters) {
        return Promise.all([...this.getCurrentHandlers(event), ...this.getPersistentHandlers(event)].map(handler => handler(...parameters)));
    }
    off(event, listener) {
        const listeners = this.persistentHandlers[event];
        if (listeners) {
            // A hack stolen from "mitt": ">>> 0" does not change numbers >= 0, but -1
            // (which would remove the last array element if used unchanged) is turned
            // into max_int, which is outside the array and does not change anything.
            listeners.splice(listeners.indexOf(listener) >>> 0, 1);
        }
        return this;
    }
    on(event, listener) {
        this.getPersistentHandlers(event).push(listener);
        return this;
    }
    onCurrentRun(event, listener) {
        this.getCurrentHandlers(event).push(listener);
        return this;
    }
    once(event, listener) {
        const selfRemovingListener = (...parameters) => {
            this.off(event, selfRemovingListener);
            return listener(...parameters);
        };
        this.on(event, selfRemovingListener);
        return this;
    }
    removeAllListeners() {
        this.removeListenersForCurrentRun();
        this.persistentHandlers = Object.create(null);
        return this;
    }
    removeListenersForCurrentRun() {
        this.currentHandlers = Object.create(null);
        return this;
    }
    getCurrentHandlers(event) {
        return this.currentHandlers[event] || (this.currentHandlers[event] = []);
    }
    getPersistentHandlers(event) {
        return this.persistentHandlers[event] || (this.persistentHandlers[event] = []);
    }
}

function watch(configs) {
    const emitter = new WatchEmitter();
    watchInternal(configs, emitter).catch(error => {
        rollup.handleError(error);
    });
    return emitter;
}
async function watchInternal(configs, emitter) {
    const optionsList = await Promise.all(rollup.ensureArray(configs).map(config => rollup.mergeOptions(config, true)));
    const watchOptionsList = optionsList.filter(config => config.watch !== false);
    if (watchOptionsList.length === 0) {
        return rollup.error(rollup.logInvalidOption('watch', rollup.URL_WATCH, 'there must be at least one config where "watch" is not set to "false"'));
    }
    await fseventsImporter.loadFsEvents();
    const { Watcher } = await Promise.resolve().then(() => require('./watch.js'));
    new Watcher(watchOptionsList, emitter);
}

exports.watch = watch;
//# sourceMappingURL=watch-proxy.js.map
