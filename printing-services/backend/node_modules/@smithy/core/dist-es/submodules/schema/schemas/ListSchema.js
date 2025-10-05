import { Schema } from "./Schema";
export class ListSchema extends Schema {
    constructor() {
        super(...arguments);
        this.symbol = ListSchema.symbol;
    }
}
ListSchema.symbol = Symbol.for("@smithy/lis");
export const list = (namespace, name, traits, valueSchema) => Schema.assign(new ListSchema(), {
    name,
    namespace,
    traits,
    valueSchema,
});
