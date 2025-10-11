import { css, glob, keyframes } from '../css';
import { hash } from '../core/hash';
import { compile } from '../core/compile';
import { getSheet } from '../core/get-sheet';

jest.mock('../core/hash', () => ({
    hash: jest.fn().mockReturnValue('hash()')
}));

jest.mock('../core/compile', () => ({
    compile: jest.fn().mockReturnValue('compile()')
}));

jest.mock('../core/get-sheet', () => ({
    getSheet: jest.fn().mockReturnValue('getSheet()')
}));

describe('css', () => {
    beforeEach(() => {
        hash.mockClear();
        compile.mockClear();
        getSheet.mockClear();
    });

    it('type', () => {
        expect(typeof css).toEqual('function');
    });

    it('args: tagged', () => {
        const out = css`base${1}`;

        expect(compile).toBeCalledWith(['base', ''], [1], undefined);
        expect(getSheet).toBeCalled();
        expect(hash).toBeCalledWith('compile()', 'getSheet()', undefined, undefined, undefined);
        expect(out).toEqual('hash()');
    });

    it('args: object', () => {
        const out = css({ foo: 1 });

        expect(hash).toBeCalledWith({ foo: 1 }, 'getSheet()', undefined, undefined, undefined);
        expect(compile).not.toBeCalled();
        expect(getSheet).toBeCalled();
        expect(out).toEqual('hash()');
    });

    it('args: array', () => {
        const propsBased = jest.fn().mockReturnValue({
            backgroundColor: 'gold'
        });
        const payload = [{ foo: 1 }, { baz: 2 }, { opacity: 0, color: 'red' }, propsBased];
        const out = css(payload);

        expect(propsBased).toHaveBeenCalled();
        expect(hash).toBeCalledWith(
            { foo: 1, baz: 2, opacity: 0, color: 'red', backgroundColor: 'gold' },
            'getSheet()',
            undefined,
            undefined,
            undefined
        );
        expect(compile).not.toBeCalled();
        expect(getSheet).toBeCalled();
        expect(out).toEqual('hash()');
    });

    it('args: function', () => {
        const incoming = { foo: 'foo' };
        const out = css.call({ p: incoming }, (props) => ({ foo: props.foo }));

        expect(hash).toBeCalledWith(incoming, 'getSheet()', undefined, undefined, undefined);
        expect(compile).not.toBeCalled();
        expect(getSheet).toBeCalled();
        expect(out).toEqual('hash()');
    });

    it('bind', () => {
        const target = '';
        const p = {};
        const g = true;
        const out = css.bind({
            target,
            p,
            g
        })`foo: 1`;

        expect(hash).toBeCalledWith('compile()', 'getSheet()', true, undefined, undefined);
        expect(compile).toBeCalledWith(['foo: 1'], [], p);
        expect(getSheet).toBeCalledWith(target);
        expect(out).toEqual('hash()');
    });
});

describe('glob', () => {
    it('type', () => {
        expect(typeof glob).toEqual('function');
    });

    it('args: g', () => {
        glob`a:b`;
        expect(hash).toBeCalledWith('compile()', 'getSheet()', 1, undefined, undefined);
    });
});

describe('keyframes', () => {
    it('type', () => {
        expect(typeof keyframes).toEqual('function');
    });

    it('args: k', () => {
        keyframes`a:b`;
        expect(hash).toBeCalledWith('compile()', 'getSheet()', undefined, undefined, 1);
    });
});
