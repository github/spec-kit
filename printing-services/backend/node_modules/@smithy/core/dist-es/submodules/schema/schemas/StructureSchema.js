import { Schema } from "./Schema";
export class StructureSchema extends Schema {
    constructor() {
        super(...arguments);
        this.symbol = StructureSchema.symbol;
    }
}
StructureSchema.symbol = Symbol.for("@smithy/str");
export const struct = (namespace, name, traits, memberNames, memberList) => Schema.assign(new StructureSchema(), {
    name,
    namespace,
    traits,
    memberNames,
    memberList,
});
