/// <reference types="cypress" />

import * as React from 'react';
import React__default from 'react';
import * as react_dom_client from 'react-dom/client';

interface UnmountArgs {
    log: boolean;
    boundComponentMessage?: string;
}
type MountOptions = Partial<MountReactComponentOptions>;
interface MountReactComponentOptions {
    ReactDom: typeof react_dom_client;
    /**
     * Log the mounting command into Cypress Command Log,
     * true by default.
     */
    log: boolean;
    /**
     * Render component in React [strict mode](https://reactjs.org/docs/strict-mode.html)
     * It activates additional checks and warnings for child components.
     */
    strict: boolean;
}
interface InternalMountOptions {
    reactDom: typeof react_dom_client;
    render: (reactComponent: ReturnType<typeof React__default.createElement>, el: HTMLElement, reactDomToUse: typeof react_dom_client) => void;
    unmount: (options: UnmountArgs) => void;
    cleanup: () => boolean;
}
interface MountReturn {
    /**
     * The component that was rendered.
     */
    component: React__default.ReactNode;
    /**
     * Rerenders the specified component with new props. This allows testing of components that store state (`setState`)
     * or have asynchronous updates (`useEffect`, `useLayoutEffect`).
     */
    rerender: (component: React__default.ReactNode) => globalThis.Cypress.Chainable<MountReturn>;
}

/**
 * Create an `mount` function. Performs all the non-React-version specific
 * behavior related to mounting. The React-version-specific code
 * is injected. This helps us to maintain a consistent public API
 * and handle breaking changes in React's rendering API.
 *
 * This is designed to be consumed by `npm/react{16,17,18}`, and other React adapters,
 * or people writing adapters for third-party, custom adapters.
 */
declare const makeMountFn: (type: 'mount' | 'rerender', jsx: React.ReactNode, options?: MountOptions, rerenderKey?: string, internalMountOptions?: InternalMountOptions) => globalThis.Cypress.Chainable<MountReturn>;
/**
 * Create an `unmount` function. Performs all the non-React-version specific
 * behavior related to unmounting.
 *
 * This is designed to be consumed by `npm/react{16,17,18}`, and other React adapters,
 * or people writing adapters for third-party, custom adapters.
 *
 * @param {UnmountArgs} options used during unmounting
 */
declare const makeUnmountFn: (options: UnmountArgs) => Cypress.Chainable<undefined>;
declare const createMount: (defaultOptions: MountOptions) => (element: React.ReactElement, options?: MountOptions) => Cypress.Chainable<MountReturn>;

/**
 * Gets the root element used to mount the component.
 * @returns {HTMLElement} The root element
 * @throws {Error} If the root element is not found
 */
declare const getContainerEl: () => HTMLElement;

/**
 * Mounts a React component into the DOM.
 * @param {import('react').JSX.Element} jsx The React component to mount.
 * @param {MountOptions} options Options to pass to the mount function.
 * @param {string} rerenderKey A key to use to force a rerender.
 *
 * @example
 * import { mount } from '@cypress/react'
 * import { Stepper } from './Stepper'
 *
 * it('mounts', () => {
 *   mount(<StepperComponent />)
 *   cy.get('[data-cy=increment]').click()
 *   cy.get('[data-cy=counter]').should('have.text', '1')
 * }
 *
 * @see {@link https://on.cypress.io/mounting-react} for more details.
 *
 * @returns {Cypress.Chainable<MountReturn>} The mounted component.
 */
declare function mount(jsx: React__default.ReactNode, options?: MountOptions, rerenderKey?: string): Cypress.Chainable<MountReturn>;

export { InternalMountOptions, MountOptions, MountReactComponentOptions, MountReturn, UnmountArgs, createMount, getContainerEl, makeMountFn, makeUnmountFn, mount };
