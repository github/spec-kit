import { compile } from '../compile';

const template = (str, ...defs) => {
    return (props) => compile(str, defs, props);
};

describe('compile', () => {
    it('simple', () => {
        expect(template`prop: 1;`({})).toEqual('prop: 1;');
    });

    it('vnode', () => {
        expect(template`prop: 1; ${() => ({ props: { className: 'class' } })}`({})).toEqual(
            'prop: 1; .class'
        );

        // Empty or falsy
        expect(template`prop: 1; ${() => ({ props: { foo: 1 } })}`({})).toEqual('prop: 1; ');
    });

    it('vanilla classname', () => {
        expect(template`prop: 1; ${() => 'go0ber'}`({})).toEqual('prop: 1; .go0ber');
    });

    it('value interpolations', () => {
        // This interpolations are testing the ability to interpolate thruty and falsy values
        expect(template`prop: 1; ${() => 0},${() => undefined},${() => null},${2}`({})).toEqual(
            'prop: 1; 0,,,2'
        );

        const tmpl = template`
            background: dodgerblue;
            ${(props) =>
                props.padding === 'bloo' &&
                `
                padding: ${props.padding}px;
            `}
            border: 1px solid blue;
        `;
        expect(tmpl({})).toEqual(`
            background: dodgerblue;
            
            border: 1px solid blue;
        `);
    });

    describe('objects', () => {
        it('normal', () => {
            expect(template`prop: 1;${(p) => ({ color: p.color })}`({ color: 'red' })).toEqual(
                'prop: 1;color:red;'
            );
        });

        it('styled-system', () => {
            const color = (p) => ({ color: p.color });
            const background = (p) => ({ backgroundColor: p.backgroundColor });

            const props = { color: 'red', backgroundColor: 'blue' };
            const res = template`
                prop: 1;
                ${color}
                ${background}
            `(props);

            expect(res.replace(/([\s|\n]+)/gm, '').trim()).toEqual(
                'prop:1;color:red;background-color:blue;'
            );
        });
    });
});
