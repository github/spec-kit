"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Context = void 0;
const _ = require("lodash");
function getDataMapKey(path, location) {
    return `${location}:${path}`;
}
class Context {
    get errors() {
        return this._errors;
    }
    constructor(fields, locations, stack, optional, bail, visibility = { type: 'visible' }, message) {
        this.fields = fields;
        this.locations = locations;
        this.stack = stack;
        this.optional = optional;
        this.bail = bail;
        this.visibility = visibility;
        this.message = message;
        this._errors = [];
        this.dataMap = new Map();
    }
    getData(options = { requiredOnly: false }) {
        const { optional } = this;
        const checks = options.requiredOnly && optional
            ? [
                (value) => value !== undefined,
                (value) => (optional === 'null' ? value != null : true),
                (value) => (optional === 'falsy' ? value : true),
            ]
            : [];
        return _([...this.dataMap.values()])
            .groupBy('originalPath')
            .flatMap((instances, group) => {
            const locations = _.uniqBy(instances, 'location');
            // #331 - When multiple locations are involved, all of them must pass the validation.
            // If none of the locations contain the field, we at least include one for error reporting.
            // #458, #531 - Wildcards are an exception though: they may yield 0..* instances with different
            // paths, so we may want to skip this filtering.
            if (instances.length > 1 && locations.length > 1 && !group.includes('*')) {
                const withValue = instances.filter(instance => instance.value !== undefined);
                return withValue.length ? withValue : [instances[0]];
            }
            return instances;
        })
            .filter(instance => checks.every(check => check(instance.value)))
            .valueOf();
    }
    addFieldInstances(instances) {
        instances.forEach(instance => {
            this.dataMap.set(getDataMapKey(instance.path, instance.location), { ...instance });
        });
    }
    setData(path, value, location) {
        const instance = this.dataMap.get(getDataMapKey(path, location));
        if (!instance) {
            throw new Error('Attempt to write data that did not pre-exist in context');
        }
        instance.value = value;
    }
    addError(opts) {
        const msg = opts.message || this.message || 'Invalid value';
        let error;
        switch (opts.type) {
            case 'field':
                error = this.updateVisibility({
                    type: 'field',
                    value: opts.value,
                    msg: typeof msg === 'function' ? msg(opts.value, opts.meta) : msg,
                    path: opts.meta?.path,
                    location: opts.meta?.location,
                });
                break;
            case 'unknown_fields':
                error = {
                    type: 'unknown_fields',
                    msg: typeof msg === 'function' ? msg(opts.fields, { req: opts.req }) : msg,
                    fields: opts.fields,
                };
                break;
            case 'alternative':
                error = {
                    type: 'alternative',
                    msg: typeof msg === 'function' ? msg(opts.nestedErrors, { req: opts.req }) : msg,
                    nestedErrors: opts.nestedErrors.map(error => this.updateVisibility(error)),
                };
                break;
            case 'alternative_grouped':
                error = {
                    type: 'alternative_grouped',
                    msg: typeof msg === 'function' ? msg(opts.nestedErrors, { req: opts.req }) : msg,
                    nestedErrors: opts.nestedErrors.map(errors => errors.map(error => this.updateVisibility(error))),
                };
                break;
            default:
                throw new Error(`Unhandled addError case`);
        }
        this._errors.push(error);
    }
    updateVisibility(error) {
        switch (this.visibility.type) {
            case 'hidden':
                error = { ...error };
                delete error.value;
                return error;
            case 'redacted':
                return {
                    ...error,
                    value: this.visibility.value,
                };
            case 'visible':
            default:
                return error;
        }
    }
}
exports.Context = Context;
