
/**
 * @cypress/svelte v0.0.0-development
 * (c) 2025 Cypress.io
 * Released under the MIT License
 */

'use strict';

var svelte = require('svelte');

const ROOT_SELECTOR = '[data-cy-root]';
/**
 * Gets the root element used to mount the component.
 * @returns {HTMLElement} The root element
 * @throws {Error} If the root element is not found
 */
const getContainerEl = () => {
    const el = document.querySelector(ROOT_SELECTOR);
    if (el) {
        return el;
    }
    throw Error(`No element found that matches selector ${ROOT_SELECTOR}. Please add a root element with data-cy-root attribute to your "component-index.html" file so that Cypress can attach your component to the DOM.`);
};
/**
 * Utility function to register CT side effects and run cleanup code during the "test:before:run" Cypress hook
 * @param optionalCallback Callback to be called before the next test runs
 */
function setupHooks(optionalCallback) {
    // We don't want CT side effects to run when e2e
    // testing so we early return.
    // System test to verify CT side effects do not pollute e2e: system-tests/test/e2e_with_mount_import_spec.ts
    if (Cypress.testingType !== 'component') {
        return;
    }
    // When running component specs, we cannot allow "cy.visit"
    // because it will wipe out our preparation work, and does not make much sense
    // thus we overwrite "cy.visit" to throw an error
    Cypress.Commands.overwrite('visit', () => {
        throw new Error('cy.visit from a component spec is not allowed');
    });
    Cypress.Commands.overwrite('session', () => {
        throw new Error('cy.session from a component spec is not allowed');
    });
    Cypress.Commands.overwrite('origin', () => {
        throw new Error('cy.origin from a component spec is not allowed');
    });
    // @ts-ignore
    Cypress.on('test:before:after:run:async', () => {
        optionalCallback === null || optionalCallback === void 0 ? void 0 : optionalCallback();
    });
}

const DEFAULT_COMP_NAME = 'unknown';
let componentInstance;
const cleanup = () => {
    if (componentInstance) {
        svelte.unmount(componentInstance);
    }
};
// Extract the component name from the object passed to mount
const getComponentDisplayName = (Component) => {
    if (Component.name) {
        const [, match] = /Proxy\<(\w+)\>/.exec(Component.name) || [];
        return match || Component.name;
    }
    return DEFAULT_COMP_NAME;
};
/**
 * Mounts a Svelte component inside the Cypress browser
 *
 * @param {Record<string, any>} Component Svelte component being mounted
 * @param {MountReturn<T extends SvelteComponent>} options options to customize the component being mounted
 * @returns Cypress.Chainable<MountReturn>
 *
 * @example
 * import Counter from './Counter.svelte'
 * import { mount } from 'cypress/svelte'
 *
 * it('should render', () => {
 *   mount(Counter, { props: { count: 42 } })
 *   cy.get('button').contains(42)
 * })
 *
 * @see {@link https://on.cypress.io/mounting-svelte} for more details.
 */
function mount(Component, options = {}) {
    // In Svelte 5, the component name is no longer easily discoverable and logs as "wrapper"
    // so we default the logging of it to false as it doesn't provide a lot of value
    options.log = options.log || false;
    return cy.then(() => {
        // Remove last mounted component if cy.mount is called more than once in a test
        cleanup();
        const target = getContainerEl();
        const ComponentConstructor = (Component.default || Component);
        // @see https://svelte.dev/docs/svelte/v5-migration-guide#Components-are-no-longer-classes
        componentInstance = svelte.mount(ComponentConstructor, Object.assign({ target }, options));
        // by waiting, we are delaying test execution for the next tick of event loop
        // and letting hooks and component lifecycle methods to execute mount
        return cy.wait(0, { log: false }).then(() => {
            if (options.log !== false) {
                const mountMessage = `<${getComponentDisplayName(Component)} ... />`;
                Cypress.log({
                    name: 'mount',
                    message: [mountMessage],
                });
            }
        })
            .wrap({ component: componentInstance }, { log: false });
    });
}
// Side effects from "import { mount } from '@cypress/<my-framework>'" are annoying, we should avoid doing this
// by creating an explicit function/import that the user can register in their 'component.js' support file,
// such as:
//    import 'cypress/<my-framework>/support'
// or
//    import { registerCT } from 'cypress/<my-framework>'
//    registerCT()
// Note: This would be a breaking change
setupHooks(cleanup);

exports.mount = mount;
