import { h, createContext, render } from 'preact';
import { useContext, forwardRef } from 'preact/compat';
import { setup, css, styled, keyframes } from '../index';
import { extractCss } from '../core/update';

describe('integrations', () => {
    it('preact', () => {
        const ThemeContext = createContext();
        const useTheme = () => useContext(ThemeContext);

        setup(h, null, useTheme);

        const target = document.createElement('div');

        const Span = styled('span', forwardRef)`
            color: red;
        `;

        const SpanWrapper = styled('div')`
            color: cyan;

            ${Span} {
                border: 1px solid red;
            }
        `;

        const BoxWithColor = styled('div')`
            color: ${(props) => props.color};
        `;

        const BoxWithColorFn = styled('div')(
            (props) => `
            color: ${props.color};
        `
        );

        const BoxWithThemeColor = styled('div')`
            color: ${(props) => props.theme.color};
        `;

        const BoxWithThemeColorFn = styled('div')(
            (props) => `
            color: ${props.theme.color};
        `
        );

        const fadeAnimation = keyframes`
            0% {
                opacity: 0;
            }
            99% {
                opacity: 1;
                color: dodgerblue;
            }
        `;

        const BoxWithAnimation = styled('span')`
            opacity: 0;
            animation: ${fadeAnimation} 500ms ease-in-out;
        `;

        const BoxWithConditionals = styled('div')([
            { foo: 1 },
            (props) => ({ color: props.isActive ? 'red' : 'tomato' }),
            null,
            { baz: 0 },
            false,
            { baz: 0 }
        ]);

        const shared = { opacity: 0 };
        const BoxWithShared = styled('div')(shared);
        const BoxWithSharedAndConditional = styled('div')([shared, { baz: 0 }]);

        const BoxWithHas = styled('div')`
            label:has(input, select),
            :has(foo, boo) {
                color: red;
            }
        `;

        const refSpy = jest.fn();

        render(
            <ThemeContext.Provider value={{ color: 'blue' }}>
                <div>
                    <Span ref={refSpy} />
                    <Span as={'div'} />
                    <SpanWrapper>
                        <Span />
                    </SpanWrapper>
                    <BoxWithColor color={'red'} />
                    <BoxWithColorFn color={'red'} />
                    <BoxWithThemeColor />
                    <BoxWithThemeColorFn />
                    <BoxWithThemeColor theme={{ color: 'green' }} />
                    <BoxWithThemeColorFn theme={{ color: 'orange' }} />
                    <BoxWithAnimation />
                    <BoxWithConditionals isActive />
                    <BoxWithShared />
                    <BoxWithSharedAndConditional />
                    <div className={css([shared, { background: 'cyan' }])} />
                    <BoxWithHas />
                </div>
            </ThemeContext.Provider>,
            target
        );

        expect(extractCss()).toMatchInlineSnapshot(
            [
                '"',
                ' ', // Empty white space that holds the textNode that the styles are appended
                '@keyframes go384228713{0%{opacity:0;}99%{opacity:1;color:dodgerblue;}}',
                '.go1127809067{opacity:0;background:cyan;}',
                '.go3865451590{color:red;}',
                '.go3991234422{color:cyan;}',
                '.go3991234422 .go3865451590{border:1px solid red;}',
                '.go1925576363{color:blue;}',
                '.go3206651468{color:green;}',
                '.go4276997079{color:orange;}',
                '.go2069586824{opacity:0;animation:go384228713 500ms ease-in-out;}',
                '.go631307347{foo:1;color:red;baz:0;}',
                '.go3865943372{opacity:0;}',
                '.go1162430001{opacity:0;baz:0;}',
                '.go2602823658 label:has(input, select),.go2602823658  :has(foo, boo){color:red;}',
                '"'
            ].join('')
        );

        expect(refSpy).toHaveBeenCalledWith(
            expect.objectContaining({
                tagName: 'SPAN'
            })
        );
    });

    it('support extending with as', () => {
        const list = ['p', 'm', 'as', 'bg'];
        setup(h, undefined, undefined, (props) => {
            for (let prop in props) {
                if (list.indexOf(prop) !== -1) {
                    delete props[prop];
                }
            }
        });
        const target = document.createElement('div');

        const Base = styled('div')(({ p = 0, m }) => [
            {
                color: 'white',
                padding: p + 'em'
            },
            m != null && { margin: m + 'em' }
        ]);

        const Super = styled(Base)`
            background: ${(p) => p.bg || 'none'};
        `;

        render(
            <div>
                <Base />
                <Base p={2} />
                <Base m={1} p={3} as={'span'} />
                <Super m={1} bg={'dodgerblue'} as={'button'} />
            </div>,
            target
        );

        // Makes sure the resulting DOM does not contain any props
        expect(target.innerHTML).toEqual(
            [
                '<div>',
                '<div class="go103173764"></div>',
                '<div class="go103194166"></div>',
                '<span class="go2081835032"></span>',
                '<button class="go1969245729 go1824201605"></button>',
                '</div>'
            ].join('')
        );

        expect(extractCss()).toMatchInlineSnapshot(
            [
                '"',
                '.go1969245729{color:white;padding:0em;margin:1em;}',
                '.go103173764{color:white;padding:0em;}',
                '.go103194166{color:white;padding:2em;}',
                '.go2081835032{color:white;padding:3em;margin:1em;}',
                '.go1824201605{background:dodgerblue;}',
                '"'
            ].join('')
        );
    });

    it('shouldForwardProps', () => {
        const list = ['p', 'm', 'as'];
        setup(h, undefined, undefined, (props) => {
            for (let prop in props) {
                if (list.indexOf(prop) !== -1) {
                    delete props[prop];
                }
            }
        });

        const target = document.createElement('div');

        const Base = styled('div')(({ p = 0, m }) => [
            {
                color: 'white',
                padding: p + 'em'
            },
            m != null && { margin: m + 'em' }
        ]);

        render(
            <div>
                <Base />
                <Base p={2} />
                <Base m={1} p={3} as={'span'} />
            </div>,
            target
        );

        // Makes sure the resulting DOM does not contain any props
        expect(target.innerHTML).toEqual(
            [
                '<div>',
                '<div class="go103173764"></div>',
                '<div class="go103194166"></div>',
                '<span class="go2081835032"></span>',
                '</div>'
            ].join(''),
            `"<div><div class=\\"go103173764\\"></div><div class=\\"go103194166\\"></div><span class=\\"go2081835032\\"></span></div>"`
        );

        expect(extractCss()).toMatchInlineSnapshot(
            [
                '"',
                '.go103173764{color:white;padding:0em;}',
                '.go103194166{color:white;padding:2em;}',
                '.go2081835032{color:white;padding:3em;margin:1em;}',
                '"'
            ].join('')
        );
    });
});
