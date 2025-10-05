import { FieldInstance, Location, Request, UnknownFieldInstance } from './base';
export type SelectFields = (req: Request, fields: string[], locations: Location[]) => FieldInstance[];
export declare const selectFields: SelectFields;
export declare const selectUnknownFields: (req: Request, knownFields: string[], locations: Location[]) => UnknownFieldInstance[];
/**
 * Reconstructs a field path from a list of path segments.
 *
 * Most segments will be concatenated by a dot, for example `['foo', 'bar']` becomes `foo.bar`.
 * However, a numeric segment will be wrapped in brackets to match regular JS array syntax:
 *
 * ```
 * reconstructFieldPath(['foo', 0, 'bar']) // foo[0].bar
 * ```
 *
 * Segments which have a special character such as `.` will be wrapped in brackets and quotes,
 * which also matches JS syntax for objects with such keys.
 *
 * ```
 * reconstructFieldPath(['foo', 'bar.baz', 'qux']) // foo["bar.baz"].qux
 * ```
 */
export declare function reconstructFieldPath(segments: readonly string[]): string;
