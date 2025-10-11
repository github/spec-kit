import { ContextItem } from './context-items';
import { Context, Optional } from './context';
import { Location } from './base';
export declare class ContextBuilder {
    private readonly stack;
    private fields;
    private locations;
    private message;
    private optional;
    private requestBail;
    private visibility;
    setFields(fields: string[]): this;
    setLocations(locations: Location[]): this;
    setMessage(message: any): this;
    addItem(...items: ContextItem[]): this;
    setOptional(options: Optional): this;
    setRequestBail(): this;
    setHidden(hidden: boolean, hiddenValue?: string): this;
    build(): Context;
}
