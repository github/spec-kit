interface DisallowedToken {
	type: 'disallowed';
	cp: number;
}
interface IgnoredToken {
	type: 'ignored';
	cp: number;
}
interface ValidToken {
	type: 'valid';
	cps: number[];
}
interface MappedToken {
	type: 'mapped';	
	cp: number;
	cps: number[];
}
type TextToken = DisallowedToken | IgnoredToken | ValidToken | MappedToken;
interface EmojiToken {
	type: 'emoji';
	input: number[];
	emoji: number[];
	cps: number[];
}
interface NFCToken {
	type: 'nfc';
	input: number[];
	cps: number[];
	tokens: TextToken[]; 
}
interface StopToken {
	type: 'stop';
}
type Token = TextToken | EmojiToken | NFCToken | StopToken;

interface Label {
	input: number[];
	offset: number;
	error?: Error;
	tokens?: number[][];
	output?: number[];
	emoji?: boolean;
	type?: string;
}

export function ens_normalize(name: string): string;
export function ens_normalize_fragment(frag: string, decompose?: boolean): string;
export function ens_beautify(name: string): string;
export function ens_tokenize(name: string, options?: {nf?: boolean}): Token[];
export function ens_split(name: string, preserve_emoji?: boolean): Label[];

export function ens_emoji(): number[][];

export function should_escape(cp: number): boolean;
export function is_combining_mark(cp: number): boolean;
export function safe_str_from_cps(cps: number[]): string;

export function nfd(cps: number[]): number[];
export function nfc(cps: number[]): number[];
