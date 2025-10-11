import { TypeRegistry } from "../TypeRegistry";
export class Schema {
    static assign(instance, values) {
        const schema = Object.assign(instance, values);
        TypeRegistry.for(schema.namespace).register(schema.name, schema);
        return schema;
    }
    static [Symbol.hasInstance](lhs) {
        const isPrototype = this.prototype.isPrototypeOf(lhs);
        if (!isPrototype && typeof lhs === "object" && lhs !== null) {
            const list = lhs;
            return list.symbol === this.symbol;
        }
        return isPrototype;
    }
    getName() {
        return this.namespace + "#" + this.name;
    }
}
