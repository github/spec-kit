import { Schema } from "./Schema";
export class SimpleSchema extends Schema {
    constructor() {
        super(...arguments);
        this.symbol = SimpleSchema.symbol;
    }
}
SimpleSchema.symbol = Symbol.for("@smithy/sim");
export const sim = (namespace, name, schemaRef, traits) => Schema.assign(new SimpleSchema(), {
    name,
    namespace,
    traits,
    schemaRef,
});
