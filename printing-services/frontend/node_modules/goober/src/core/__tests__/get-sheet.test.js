import { getSheet } from '../get-sheet';

describe('getSheet', () => {
    it('regression', () => {
        const target = getSheet();
        expect(target.nodeType).toEqual(3);
    });

    it('custom target', () => {
        const custom = document.createElement('div');
        const sheet = getSheet(custom);

        expect(sheet.nodeType).toEqual(3);
        expect(sheet.parentElement.nodeType).toEqual(1);
        expect(sheet.parentElement.getAttribute('id')).toEqual('_goober');
    });

    it('reuse sheet', () => {
        const custom = document.createElement('div');
        const sheet = getSheet(custom);
        const second = getSheet(custom);

        expect(sheet === second).toBeTruthy();
    });

    it('server side', () => {
        const bkp = global.document;
        delete global.document;

        expect(() => getSheet()).not.toThrow();

        global.document = bkp;
    });

    it('server side with custom collector', () => {
        const bkp = global.document;
        const win = global.window;
        delete global.document;
        delete global.window;

        const collector = { data: '' };

        expect(collector === getSheet(collector)).toBeTruthy();

        global.document = bkp;
        global.window = win;
    });
});
