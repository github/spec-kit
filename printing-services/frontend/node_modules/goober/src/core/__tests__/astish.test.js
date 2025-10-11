import { astish } from '../astish';

describe('astish', () => {
    it('regular', () => {
        expect(
            astish(`
            prop: value;
        `)
        ).toEqual({
            prop: 'value'
        });
    });

    it('nested', () => {
        expect(
            astish(`
            prop: value;
            @keyframes foo {
                0% {
                    attr: value;
                }
                50% {
                    opacity: 1;
                }
                100% {
                    foo: baz;
                }
            }
            named {
                background-image: url('/path-to-jpg.png');
            }
            opacity: 0;
            .class,
            &:hover {
                -webkit-touch: none;
            }
        `)
        ).toEqual({
            prop: 'value',
            opacity: '0',
            '.class, &:hover': {
                '-webkit-touch': 'none'
            },
            '@keyframes foo': {
                '0%': {
                    attr: 'value'
                },
                '50%': {
                    opacity: '1'
                },

                '100%': {
                    foo: 'baz'
                }
            },
            named: {
                'background-image': "url('/path-to-jpg.png')"
            }
        });
    });

    it('merging', () => {
        expect(
            astish(`
            .c {
                font-size:24px;
            }
        
            .c {
                color:red;
            }
        `)
        ).toEqual({
            '.c': {
                'font-size': '24px',
                color: 'red'
            }
        });
    });

    it('regression', () => {
        expect(
            astish(`
            &.g0ssss {
                aa: foo;
                box-shadow: 0 1px rgba(0, 2, 33, 4) inset;
            }
            named {
                transform: scale(1.2), rotate(1, 1);
            }
            @media screen and (some-rule: 100px) {
                foo: baz;
                opacity: 1;
                level {
                    one: 1;
                    level {
                        two: 2;
                    }
                }
            }
            .a{
                color: red;
            }
            .b  {
                color: blue;
            }
        `)
        ).toEqual({
            '&.g0ssss': {
                aa: 'foo',
                'box-shadow': '0 1px rgba(0, 2, 33, 4) inset'
            },
            '.a': {
                color: 'red'
            },
            '.b': {
                color: 'blue'
            },
            named: {
                transform: 'scale(1.2), rotate(1, 1)'
            },
            '@media screen and (some-rule: 100px)': {
                foo: 'baz',
                opacity: '1',
                level: {
                    one: '1',

                    level: {
                        two: '2'
                    }
                }
            }
        });
    });

    it('should strip comments', () => {
        expect(
            astish(`
                color: red;
                /*
                    some comment
                */
                transform: translate3d(0, 0, 0);
                /**
                 * other comment
                 */
                background: peachpuff;
                font-size: xx-large; /* inline comment */
                /* foo: bar */
                font-weight: bold;
            `)
        ).toEqual({
            color: 'red',
            transform: 'translate3d(0, 0, 0)',
            background: 'peachpuff',
            'font-size': 'xx-large',
            'font-weight': 'bold'
        });
    });

    // for reference on what is valid:
    // https://www.w3.org/TR/CSS22/syndata.html#value-def-identifier
    it('should not mangle valid css identifiers', () => {
        expect(
            astish(`
                :root {
                  --azAZ-_中文09: 0;
                }
            `)
        ).toEqual({
            ':root': {
                '--azAZ-_中文09': '0'
            }
        });
    });

    it('should parse multiline background declaration', () => {
        expect(
            astish(`
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="white"><path d="M7.5 36.7h58.4v10.6H7.5V36.7zm0-15.9h58.4v10.6H7.5V20.8zm0 31.9h58.4v10.6H7.5V52.7zm0 15.9h58.4v10.6H7.5V68.6zm63.8-15.9l10.6 15.9 10.6-15.9H71.3zm21.2-5.4L81.9 31.4 71.3 47.3h21.2z"/></svg>')
                    center/contain;
            `)
        ).toEqual({
            background: `url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="white"><path d="M7.5 36.7h58.4v10.6H7.5V36.7zm0-15.9h58.4v10.6H7.5V20.8zm0 31.9h58.4v10.6H7.5V52.7zm0 15.9h58.4v10.6H7.5V68.6zm63.8-15.9l10.6 15.9 10.6-15.9H71.3zm21.2-5.4L81.9 31.4 71.3 47.3h21.2z"/></svg>') center/contain`
        });
    });

    it('should handle inline @media block', () => {
        expect(
            astish(
                `h1 { font-size: 1rem; } @media only screen and (min-width: 850px) { h1 { font-size: 2rem; } }`
            )
        ).toEqual({
            h1: {
                'font-size': '1rem'
            },
            '@media only screen and (min-width: 850px)': {
                h1: {
                    'font-size': '2rem'
                }
            }
        });
    });

    it('should handle newlines as part of the rule value', () => {
        expect(
            astish(
                `tag {
                    font-size: first
                        second;
                }`
            )
        ).toEqual({
            tag: {
                'font-size': 'first second'
            }
        });
    });
});
