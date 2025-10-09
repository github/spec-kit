// Type definitions for Minimatch 3.0
// Project: https://github.com/isaacs/minimatch
// Definitions by: vvakame <https://github.com/vvakame>
//                 Shant Marouti <https://github.com/shantmarouti>
// Definitions: https://github.com/DefinitelyTyped/DefinitelyTyped

/**
 * Tests a path against the pattern using the options.
 */
declare function M(target: string, pattern: string, options?: M.IOptions): boolean;

declare namespace M {
    /**
     * Match against the list of files, in the style of fnmatch or glob.
     * If nothing is matched, and options.nonull is set,
     * then return a list containing the pattern itself.
     */
    function match(list: ReadonlyArray<string>, pattern: string, options?: IOptions): string[];

    /**
     * Returns a function that tests its supplied argument, suitable for use with Array.filter
     */
    function filter(pattern: string, options?: IOptions): (element: string, indexed: number, array: ReadonlyArray<string>) => boolean;

    /**
     * Make a regular expression object from the pattern.
     */
    function makeRe(pattern: string, options?: IOptions): RegExp;

    let Minimatch: IMinimatchStatic;

    interface IOptions {
        /**
         * Dump a ton of stuff to stderr.
         *
         * @default false
         */
        debug?: boolean | undefined;

        /**
         * Do not expand {a,b} and {1..3} brace sets.
         *
         * @default false
         */
        nobrace?: boolean | undefined;

        /**
         * Disable ** matching against multiple folder names.
         *
         * @default false
         */
        noglobstar?: boolean | undefined;

        /**
         * Allow patterns to match filenames starting with a period,
         * even if the pattern does not explicitly have a period in that spot.
         *
         * @default false
         */
        dot?: boolean | undefined;

        /**
         * Disable "extglob" style patterns like +(a|b).
         *
         * @default false
         */
        noext?: boolean | undefined;

        /**
         * Perform a case-insensitive match.
         *
         * @default false
         */
        nocase?: boolean | undefined;

        /**
         * When a match is not found by minimatch.match,
         * return a list containing the pattern itself if this option is set.
         * Otherwise, an empty list is returned if there are no matches.
         *
         * @default false
         */
        nonull?: boolean | undefined;

        /**
         * If set, then patterns without slashes will be matched against
         * the basename of the path if it contains slashes.
         *
         * @default false
         */
        matchBase?: boolean | undefined;

        /**
         * Suppress the behavior of treating #
         * at the start of a pattern as a comment.
         *
         * @default false
         */
        nocomment?: boolean | undefined;

        /**
         * Suppress the behavior of treating a leading ! character as negation.
         *
         * @default false
         */
        nonegate?: boolean | undefined;

        /**
         * Returns from negate expressions the same as if they were not negated.
         * (Ie, true on a hit, false on a miss.)
         *
         * @default false
         */
        flipNegate?: boolean | undefined;
    }

    interface IMinimatchStatic {
        new(pattern: string, options?: IOptions): IMinimatch;
        prototype: IMinimatch;
    }

    interface IMinimatch {
        /**
         * The original pattern the minimatch object represents.
         */
        pattern: string;

        /**
         * The options supplied to the constructor.
         */
        options: IOptions;

        /**
         * A 2-dimensional array of regexp or string expressions.
         */
        set: any[][]; // (RegExp | string)[][]

        /**
         * A single regular expression expressing the entire pattern.
         * Created by the makeRe method.
         */
        regexp: RegExp;

        /**
         * True if the pattern is negated.
         */
        negate: boolean;

        /**
         * True if the pattern is a comment.
         */
        comment: boolean;

        /**
         * True if the pattern is ""
         */
        empty: boolean;

        /**
         * Generate the regexp member if necessary, and return it.
         * Will return false if the pattern is invalid.
         */
        makeRe(): RegExp; // regexp or boolean

        /**
         * Return true if the filename matches the pattern, or false otherwise.
         */
        match(fname: string): boolean;

        /**
         * Take a /-split filename, and match it against a single row in the regExpSet.
         * This method is mainly for internal use, but is exposed so that it can be used
         * by a glob-walker that needs to avoid excessive filesystem calls.
         */
        matchOne(files: string[], pattern: string[], partial: boolean): boolean;

        /**
         * @deprecated. For internal use.
         */
        debug(): void;

        /**
         * @deprecated. For internal use.
         */
        make(): void;

        /**
         * @deprecated. For internal use.
         */
        parseNegate(): void;

        /**
         * @deprecated. For internal use.
         */
        braceExpand(pattern: string, options: IOptions): void;

        /**
         * @deprecated. For internal use.
         */
        parse(pattern: string, isSub?: boolean): void;
    }
}

export = M;
