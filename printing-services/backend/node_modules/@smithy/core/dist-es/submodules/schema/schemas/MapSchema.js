import { Schema } from "./Schema";
export class MapSchema extends Schema {
    constructor() {
        super(...arguments);
        this.symbol = MapSchema.symbol;
    }
}
MapSchema.symbol = Symbol.for("@smithy/map");
export const map = (namespace, name, traits, keySchema, valueSchema) => Schema.assign(new MapSchema(), {
    name,
    namespace,
    traits,
    keySchema,
    valueSchema,
});
