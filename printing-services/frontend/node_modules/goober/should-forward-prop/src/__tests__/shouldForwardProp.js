import { css } from 'goober';
import { shouldForwardProp } from '../index';

describe('shouldForwardProp', () => {
    it('type', () => {
        expect(typeof shouldForwardProp).toEqual('function');
    });

    it('shouldForwardProp', () => {
        const fn = shouldForwardProp((prop) => {
            // Filter out props prefixed with '$'
            return prop[0] !== '$';
        });

        const props = {
            color: 'red',
            $shouldAnimate: true
        };

        // 'render'
        fn(props);

        expect(props).toEqual({ color: 'red' });
    });
});
