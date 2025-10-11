import * as goober from '../index';

describe('goober', () => {
    it('exports', () => {
        expect(Object.keys(goober).sort()).toEqual([
            'css',
            'extractCss',
            'glob',
            'keyframes',
            'setup',
            'styled'
        ]);
    });
});
