import { glob, createGlobalStyles } from '../index';
import { css, setup } from 'goober';

jest.mock('goober', () => ({
    css: jest.fn().mockReturnValue('css()')
}));

describe('global', () => {
    beforeEach(() => {
        css.mockClear();
    });

    it('type', () => {
        expect(typeof glob).toEqual('function');
        expect(typeof createGlobalStyles).toEqual('function');
    });

    it('glob', () => {
        glob`a:b`;
        expect(css).toBeCalledWith(['a:b']);
    });
});
