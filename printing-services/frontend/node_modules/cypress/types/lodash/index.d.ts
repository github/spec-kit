// Type definitions for Lo-Dash 4.14
// Project: https://lodash.com
// Definitions by: Brian Zengel <https://github.com/bczengel>,
//                 Ilya Mochalov <https://github.com/chrootsu>,
//                 Stepan Mikhaylyuk <https://github.com/stepancar>,
//                 AJ Richardson <https://github.com/aj-r>,
//                 e-cloud <https://github.com/e-cloud>,
//                 Georgii Dolzhykov <https://github.com/thorn0>,
//                 Jack Moore <https://github.com/jtmthf>,
//                 Dominique Rau <https://github.com/DomiR>
//                 William Chelman <https://github.com/WilliamChelman>
// Definitions: https://github.com/DefinitelyTyped/DefinitelyTyped

/// <reference path="./common/common.d.ts" />
/// <reference path="./common/array.d.ts" />
/// <reference path="./common/collection.d.ts" />
/// <reference path="./common/date.d.ts" />
/// <reference path="./common/function.d.ts" />
/// <reference path="./common/lang.d.ts" />
/// <reference path="./common/math.d.ts" />
/// <reference path="./common/number.d.ts" />
/// <reference path="./common/object.d.ts" />
/// <reference path="./common/seq.d.ts" />
/// <reference path="./common/string.d.ts" />
/// <reference path="./common/util.d.ts" />

export = _;
export as namespace _;

declare const _: _.LoDashStatic;
declare namespace _ {
    // tslint:disable-next-line no-empty-interface (This will be augmented)
    interface LoDashStatic {}
}

// Backward compatibility with --target es5
declare global {
    // tslint:disable-next-line:no-empty-interface
    interface Set<T> { }
    // tslint:disable-next-line:no-empty-interface
    interface Map<K, V> { }
    // tslint:disable-next-line:no-empty-interface
    interface WeakSet<T> { }
    // tslint:disable-next-line:no-empty-interface
    interface WeakMap<K extends object, V> { }
}
