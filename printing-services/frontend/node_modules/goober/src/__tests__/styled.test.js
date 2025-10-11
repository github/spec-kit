import { styled, setup } from '../styled';
import { extractCss } from '../core/update';

const pragma = jest.fn((tag, props) => {
    return { tag, props: { ...props, className: props.className.replace(/go\d+/g, 'go') } };
});

expect.extend({
    toMatchVNode(received, tag, props) {
        expect(received.tag).toEqual(tag);
        expect(received.props).toEqual(props);
        return {
            message: 'Expected vnode to match vnode',
            pass: true
        };
    }
});

describe('styled', () => {
    beforeEach(() => {
        pragma.mockClear();
        setup(pragma);
        extractCss();
    });

    it('calls pragma', () => {
        setup(undefined);
        expect(() => styled()()()).toThrow();

        setup(pragma);
        const vnode = styled('div')``();

        expect(pragma).toBeCalledTimes(1);
        expect(vnode).toMatchVNode('div', {
            className: 'go'
        });
    });

    it('extend props', () => {
        const vnode = styled('tag')`
            color: peachpuff;
        `({ bar: 1 });

        expect(vnode).toMatchVNode('tag', {
            bar: 1,
            className: 'go'
        });
        expect(extractCss()).toEqual('.go3183460609{color:peachpuff;}');
    });

    it('concat className if present in props', () => {
        const vnode = styled('tag')`
            color: peachpuff;
        `({ bar: 1, className: 'existing' });

        expect(vnode).toMatchVNode('tag', {
            bar: 1,
            className: 'go existing'
        });
    });

    it('pass template function', () => {
        const vnode = styled('tag')((props) => ({ color: props.color }))({ color: 'red' });

        expect(vnode).toMatchVNode('tag', {
            className: 'go',
            color: 'red'
        });
        expect(extractCss()).toEqual('.go3433634237{color:red;}');
    });

    it('change tag via "as" prop', () => {
        const Tag = styled('tag')`
            color: red;
        `;

        // Simulate a render
        let vnode = Tag();
        expect(vnode).toMatchVNode('tag', { className: 'go' });

        // Simulate a render with
        vnode = Tag({ as: 'foo' });
        // Expect it to be changed to foo
        expect(vnode).toMatchVNode('foo', { className: 'go' });

        // Simulate a render
        vnode = Tag();
        expect(vnode).toMatchVNode('tag', { className: 'go' });
    });

    it('support forwardRef', () => {
        const forwardRef = jest.fn((fn) => (props) => fn(props, 'ref'));
        const vnode = styled('tag', forwardRef)`
            color: red;
        `({ bar: 1 });

        expect(vnode).toMatchVNode('tag', {
            bar: 1,
            className: 'go',
            ref: 'ref'
        });
    });

    it('setup useTheme', () => {
        setup(pragma, null, () => 'theme');

        const styleFn = jest.fn(() => ({}));
        const vnode = styled('tag')(styleFn)({ bar: 1 });

        expect(styleFn).toBeCalledWith({ bar: 1, theme: 'theme' });
        expect(vnode).toMatchVNode('tag', {
            bar: 1,
            className: 'go'
        });
    });

    it('setup useTheme with theme prop override', () => {
        setup(pragma, null, () => 'theme');

        const styleFn = jest.fn(() => ({}));
        const vnode = styled('tag')(styleFn)({ theme: 'override' });

        expect(styleFn).toBeCalledWith({ theme: 'override' });
        expect(vnode).toMatchVNode('tag', { className: 'go', theme: 'override' });
    });

    it('uses babel compiled classNames', () => {
        const Comp = styled('tag')``;
        Comp.className = 'foobar';
        const vnode = Comp({});
        expect(vnode).toMatchVNode('tag', { className: 'go foobar' });
    });

    it('omits css prop with falsy should forward prop function', () => {
        const shouldForwardProp = (props) => {
            for (let prop in props) {
                if (prop.includes('$')) delete props[prop];
            }
        };
        // Overwrite setup for this test
        setup(pragma, undefined, undefined, shouldForwardProp);

        const vnode = styled('tag')`
            color: peachpuff;
        `({ bar: 1, $templateColumns: '1fr 1fr' });

        expect(vnode).toMatchVNode('tag', { className: 'go', bar: 1 });
    });

    it('pass truthy logical and operator', () => {
        const Tag = styled('tag')((props) => props.draw && { color: 'yellow' });

        // Simulate a render
        let vnode = Tag({ draw: true });

        expect(vnode).toMatchVNode('tag', { className: 'go', draw: true });
        expect(extractCss()).toEqual('.go2986228274{color:yellow;}');
    });
});
