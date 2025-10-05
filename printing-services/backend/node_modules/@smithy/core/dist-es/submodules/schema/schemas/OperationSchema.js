import { Schema } from "./Schema";
export class OperationSchema extends Schema {
    constructor() {
        super(...arguments);
        this.symbol = OperationSchema.symbol;
    }
}
OperationSchema.symbol = Symbol.for("@smithy/ope");
export const op = (namespace, name, traits, input, output) => Schema.assign(new OperationSchema(), {
    name,
    namespace,
    traits,
    input,
    output,
});
