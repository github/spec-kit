import { update, extractCss } from '../update';
import { getSheet } from '../get-sheet';

describe('update', () => {
    it('regression', () => {
        const t = { data: '' };

        update('css', t);
        expect(t.data).toEqual('css');
    });

    it('regression: duplicate', () => {
        const t = { data: '' };

        update('css', t);
        update('foo', t);
        update('css', t);

        expect(t.data).toEqual('cssfoo');
    });

    it('regression: extract and flush', () => {
        update('filled', getSheet());
        expect(extractCss()).toEqual(' filled');
        expect(extractCss()).toEqual('');
    });

    it('regression: extract and flush without DOM', () => {
        const bkp = global.self;
        delete global.self;
        update('filled', getSheet());
        expect(extractCss()).toEqual('filled');
        expect(extractCss()).toEqual('');
        global.self = bkp;
    });

    it('regression: extract and flush from custom target', () => {
        const target = document.createElement('div');
        update('filled', getSheet());
        update('filledbody', getSheet(target));
        expect(extractCss(target)).toEqual(' filledbody');
        expect(extractCss(target)).toEqual('');
    });

    it('regression: append or prepend', () => {
        extractCss();
        update('end', getSheet());
        update('start', getSheet(), true);
        expect(extractCss()).toEqual('startend');
    });

    it('regression: global style replacement', () => {
        const t = { data: 'html, body { background-color: white; }' };

        update(
            'html, body { background-color: black; }',
            t,
            undefined,
            'html, body { background-color: white; }'
        );

        expect(t.data).toEqual('html, body { background-color: black; }');
    });
});
