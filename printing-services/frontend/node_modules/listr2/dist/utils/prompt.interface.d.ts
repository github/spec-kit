/// <reference types="node" />
import * as Enquirer from 'enquirer';
import { WriteStream } from 'fs';
import { Writable } from 'stream';
import { PromptError } from '../interfaces/listr-error.interface';
/** Returns all the prompt options depending on the type selected. */
export declare type PromptOptions<T extends boolean = false> = Unionize<{
    [K in PromptTypes]-?: T extends true ? {
        type: K;
    } & PromptOptionsType<K> & {
        name: string | (() => string);
    } : {
        type: K;
    } & PromptOptionsType<K>;
}> | ({
    type: string;
} & T extends true ? PromptOptionsType<string> & {
    name: string | (() => string);
} : PromptOptionsType<string>);
export declare type Unionize<T extends Record<PropertyKey, unknown>> = {
    [P in keyof T]: T[P];
}[keyof T];
interface BasePromptOptions {
    message: string | (() => string) | (() => Promise<string>);
    initial?: boolean | number | number[] | string | (() => string) | (() => Promise<string>);
    required?: boolean;
    stdin?: NodeJS.ReadStream;
    stdout?: NodeJS.WriteStream;
    header?: string;
    footer?: string;
    skip?(value: any): boolean | Promise<boolean>;
    format?(value: any): any | Promise<any>;
    result?(value: any): any | Promise<any>;
    validate?(value: any, state: any): boolean | Promise<boolean> | string | Promise<string> | Promise<string | boolean>;
    onSubmit?(name: any, value: any, prompt: Enquirer.Prompt): boolean | Promise<boolean>;
    onCancel?(name: any, value: any, prompt: Enquirer.Prompt): boolean | Promise<boolean>;
}
interface BasePromptOptionsWithName extends BasePromptOptions {
    name: string | (() => string);
}
interface ArrayPromptOptions extends BasePromptOptions {
    choices: string[] | BasePromptOptionsWithName[];
    maxChoices?: number;
    multiple?: boolean;
    initial?: number | number[];
    delay?: number;
    separator?: boolean;
    sort?: boolean;
    linebreak?: boolean;
    edgeLength?: number;
    align?: 'left' | 'right';
    scroll?: boolean;
}
interface BooleanPromptOptions extends BasePromptOptions {
    initial?: boolean | (() => string) | (() => Promise<string>);
}
interface StringPromptOptions extends BasePromptOptions {
    initial?: string;
    multiline?: boolean;
}
interface ScalePromptOptions extends ArrayPromptOptions {
    scale: StringPromptOptions[];
    margin?: [number, number, number, number];
}
interface NumberPromptOptions extends BasePromptOptions {
    min?: number;
    max?: number;
    delay?: number;
    float?: boolean;
    round?: boolean;
    major?: number;
    minor?: number;
    initial?: number;
}
interface SnippetPromptOptions extends BasePromptOptions {
    newline?: string;
    fields: Partial<BasePromptOptionsWithName>[];
    template: string;
}
interface SortPromptOptions extends BasePromptOptions {
    hint?: string;
    drag?: boolean;
    numbered?: boolean;
}
interface SurveyPromptOptions extends ArrayPromptOptions {
    scale: BasePromptOptionsWithName[];
    margin: [number, number, number, number];
}
interface QuizPromptOptions extends ArrayPromptOptions {
    correctChoice: number;
}
interface TogglePromptOptions extends BasePromptOptions {
    enabled?: string;
    disabled?: string;
}
export declare type PromptTypes = 'AutoComplete' | 'BasicAuth' | 'Confirm' | 'Editable' | 'Form' | 'Input' | 'Invisible' | 'List' | 'MultiSelect' | 'Numeral' | 'Password' | 'Quiz' | 'Scale' | 'Select' | 'Snippet' | 'Sort' | 'Survey' | 'Text' | 'Toggle';
export declare type PromptOptionsType<T> = T extends keyof PromptOptionsMap ? PromptOptionsMap[T] : T extends string ? BasePromptOptions & Record<PropertyKey, unknown> : any;
export declare class PromptOptionsMap implements Record<PromptTypes, Record<PropertyKey, any>> {
    AutoComplete: ArrayPromptOptions;
    BasicAuth: StringPromptOptions;
    Confirm: BooleanPromptOptions;
    Editable: ArrayPromptOptions;
    Form: ArrayPromptOptions;
    Input: StringPromptOptions;
    Invisible: StringPromptOptions;
    List: ArrayPromptOptions;
    MultiSelect: ArrayPromptOptions;
    Numeral: NumberPromptOptions;
    Password: StringPromptOptions;
    Quiz: QuizPromptOptions;
    Scale: ScalePromptOptions;
    Select: ArrayPromptOptions;
    Snippet: SnippetPromptOptions;
    Sort: SortPromptOptions;
    Survey: SurveyPromptOptions;
    Text: StringPromptOptions;
    Toggle: TogglePromptOptions;
}
export interface PromptSettings {
    error?: boolean;
    cancelCallback?: (settings?: PromptSettings) => string | Error | PromptError | void;
    stdout?: WriteStream | Writable;
    enquirer?: Enquirer;
}
export interface PromptInstance extends Omit<BasePromptOptions, 'onCancel' | 'onSubmit'> {
    submit(): void;
    cancel(err?: string): void;
}
export {};
