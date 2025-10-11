import { h, createContext, render } from 'preact';
import { useContext } from 'preact/hooks';
import { setup, extractCss } from 'goober';
import { createGlobalStyles } from '../index';

describe('createGlobalStyles', () => {
    it('regular', () => {
        setup(h);

        const target = document.createElement('div');

        const GlobalStyle = createGlobalStyles`
            html, body {
                background: dodgerblue;
            }
        `;

        render(
            <div>
                <GlobalStyle />
            </div>,
            target
        );

        expect(extractCss()).toMatchSnapshot();
        expect(target.innerHTML).toMatchSnapshot();
    });

    it('with theme', () => {
        const ThemeContext = createContext();
        const useTheme = () => useContext(ThemeContext);

        setup(h, null, useTheme);

        const target = document.createElement('div');

        const GlobalStyle = createGlobalStyles`
            html, body {
                margin: 0;
                background: ${(props) => props.theme.color};
            }
        `;

        render(
            <ThemeContext.Provider value={{ color: 'blue' }}>
                <div>
                    <GlobalStyle />
                </div>
            </ThemeContext.Provider>,
            target
        );

        expect(extractCss()).toMatchSnapshot();
        expect(target.innerHTML).toMatchSnapshot();
    });
});
