import { toHash } from '../to-hash';

describe('to-hash', () => {
    it('regression', () => {
        const res = toHash('goober');

        expect(res).toEqual('go1990315141');
        expect(toHash('goober')).toEqual('go1990315141');
    });

    it('collision', () => {
        const a = toHash('background:red;color:black;');
        const b = toHash('background:black;color:red;');

        expect(a === b).toBeFalsy();
    });
});
