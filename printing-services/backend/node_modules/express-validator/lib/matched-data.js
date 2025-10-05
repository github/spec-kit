"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.matchedData = matchedData;
const _ = require("lodash");
const base_1 = require("./base");
/**
 * Extracts data validated or sanitized from the request, and builds an object with them.
 *
 * @param req the express request object
 * @param options
 * @returns an object of data that's been validated or sanitized in the passed request
 */
function matchedData(req, options = {}) {
    const internalReq = req;
    const fieldExtractor = createFieldExtractor(options.includeOptionals !== true);
    const validityFilter = createValidityFilter(options.onlyValidData);
    const locationFilter = createLocationFilter(options.locations);
    return _(internalReq[base_1.contextsKey])
        .flatMap(fieldExtractor)
        .filter(validityFilter)
        .map(field => field.instance)
        .filter(locationFilter)
        .reduce((state, instance) => _.set(state, instance.path, instance.value), {});
}
function createFieldExtractor(removeOptionals) {
    return (context) => {
        const instances = context.getData({ requiredOnly: removeOptionals });
        return instances.map((instance) => ({ instance, context }));
    };
}
function createValidityFilter(onlyValidData = true) {
    return !onlyValidData
        ? () => true
        : (field) => {
            const hasError = field.context.errors.some(error => error.type === 'field' &&
                error.location === field.instance.location &&
                error.path === field.instance.path);
            return !hasError;
        };
}
function createLocationFilter(locations = []) {
    // No locations mean all locations
    const allLocations = locations.length === 0;
    return allLocations ? () => true : (field) => locations.includes(field.location);
}
