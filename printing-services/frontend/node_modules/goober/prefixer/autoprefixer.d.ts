export = autoprefixer;

export as namespace autoprefixer;

declare namespace autoprefixer {
    function prefix(key: string, val: any): string;
}
