
/**
 * @cypress/react v0.0.0-development
 * (c) 2025 Cypress.io
 * Released under the MIT License
 */

'use strict';

var React = require('react');
var ReactDOM = require('react-dom/client');

function _interopNamespaceDefault(e) {
  var n = Object.create(null);
  if (e) {
    Object.keys(e).forEach(function (k) {
      if (k !== 'default') {
        var d = Object.getOwnPropertyDescriptor(e, k);
        Object.defineProperty(n, k, d.get ? d : {
          enumerable: true,
          get: function () { return e[k]; }
        });
      }
    });
  }
  n.default = e;
  return Object.freeze(n);
}

var React__namespace = /*#__PURE__*/_interopNamespaceDefault(React);

/**
 * Gets the display name of the component when possible.
 * @param type {JSX} The type object returned from creating the react element.
 * @param fallbackName {string} The alias, or fallback name to use when the name cannot be derived.
 * @link https://github.com/facebook/react-devtools/blob/master/backend/getDisplayName.js
 */
function getDisplayName(node, fallbackName = 'Unknown') {
    const type = node === null || node === void 0 ? void 0 : node.type;
    if (!type) {
        return fallbackName;
    }
    let displayName = null;
    // The displayName property is not guaranteed to be a string.
    // It's only safe to use for our purposes if it's a string.
    // github.com/facebook/react-devtools/issues/803
    if (typeof type.displayName === 'string') {
        displayName = type.displayName;
    }
    if (!displayName) {
        displayName = type.name || fallbackName;
    }
    // Facebook-specific hack to turn "Image [from Image.react]" into just "Image".
    // We need displayName with module name for error reports but it clutters the DevTools.
    const match = displayName.match(/^(.*) \[from (.*)\]$/);
    if (match) {
        const componentName = match[1];
        const moduleName = match[2];
        if (componentName && moduleName) {
            if (moduleName === componentName ||
                moduleName.startsWith(`${componentName}.`)) {
                displayName = componentName;
            }
        }
    }
    return displayName;
}

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

let mountCleanup;
/**
 * Create an `mount` function. Performs all the non-React-version specific
 * behavior related to mounting. The React-version-specific code
 * is injected. This helps us to maintain a consistent public API
 * and handle breaking changes in React's rendering API.
 *
 * This is designed to be consumed by `npm/react{16,17,18}`, and other React adapters,
 * or people writing adapters for third-party, custom adapters.
 */
const makeMountFn = (type, jsx, options = {}, rerenderKey, internalMountOptions) => {
    if (!internalMountOptions) {
        throw Error('internalMountOptions must be provided with `render` and `reactDom` parameters');
    }
    mountCleanup = internalMountOptions.cleanup;
    return cy
        .then(() => {
        var _a, _b, _c;
        const reactDomToUse = internalMountOptions.reactDom;
        const el = getContainerEl();
        if (!el) {
            throw new Error([
                `[@cypress/react] 🔥 Hmm, cannot find root element to mount the component. Searched for ${ROOT_SELECTOR}`,
            ].join(' '));
        }
        const key = rerenderKey !== null && rerenderKey !== void 0 ? rerenderKey : 
        // @ts-ignore provide unique key to the the wrapped component to make sure we are rerendering between tests
        (((_c = (_b = (_a = Cypress === null || Cypress === void 0 ? void 0 : Cypress.mocha) === null || _a === void 0 ? void 0 : _a.getRunner()) === null || _b === void 0 ? void 0 : _b.test) === null || _c === void 0 ? void 0 : _c.title) || '') + Math.random();
        const props = {
            key,
        };
        const reactComponent = React__namespace.createElement(options.strict ? React__namespace.StrictMode : React__namespace.Fragment, props, jsx);
        // since we always surround the component with a fragment
        // let's get back the original component
        const userComponent = reactComponent.props.children;
        internalMountOptions.render(reactComponent, el, reactDomToUse);
        return (cy.wrap(userComponent, { log: false })
            .then(() => {
            return cy.wrap({
                component: userComponent,
                rerender: (newComponent) => makeMountFn('rerender', newComponent, options, key, internalMountOptions),
            }, { log: false });
        })
            // by waiting, we delaying test execution for the next tick of event loop
            // and letting hooks and component lifecycle methods to execute mount
            // https://github.com/bahmutov/cypress-react-unit-test/issues/200
            .wait(0, { log: false })
            .then(() => {
            if (options.log !== false) {
                // Get the display name property via the component constructor
                // @ts-ignore FIXME
                const componentName = getDisplayName(jsx);
                const jsxComponentName = `<${componentName} ... />`;
                Cypress.log({
                    name: type,
                    type: 'parent',
                    message: [jsxComponentName],
                    // @ts-ignore
                    $el: el.children.item(0),
                    consoleProps: () => {
                        return {
                            // @ts-ignore protect the use of jsx functional components use ReactNode
                            props: jsx === null || jsx === void 0 ? void 0 : jsx.props,
                            description: type === 'mount' ? 'Mounts React component' : 'Rerenders mounted React component',
                            home: 'https://github.com/cypress-io/cypress',
                        };
                    },
                });
            }
        }));
        // Bluebird types are terrible. I don't think the return type can be carried without this cast
    });
};
/**
 * Create an `unmount` function. Performs all the non-React-version specific
 * behavior related to unmounting.
 *
 * This is designed to be consumed by `npm/react{16,17,18}`, and other React adapters,
 * or people writing adapters for third-party, custom adapters.
 *
 * @param {UnmountArgs} options used during unmounting
 */
const makeUnmountFn = (options) => {
    return cy.then(() => {
        var _a;
        const wasUnmounted = mountCleanup === null || mountCleanup === void 0 ? void 0 : mountCleanup();
        if (wasUnmounted && options.log) {
            Cypress.log({
                name: 'unmount',
                type: 'parent',
                message: [(_a = options.boundComponentMessage) !== null && _a !== void 0 ? _a : 'Unmounted component'],
                consoleProps: () => {
                    return {
                        description: 'Unmounts React component',
                        parent: getContainerEl().parentNode,
                        home: 'https://github.com/cypress-io/cypress',
                    };
                },
            });
        }
    });
};
// Cleanup before each run
// NOTE: we cannot use unmount here because
// we are not in the context of a test
const preMountCleanup = () => {
    mountCleanup === null || mountCleanup === void 0 ? void 0 : mountCleanup();
};
const _mount = (jsx, options = {}) => makeMountFn('mount', jsx, options);
const createMount = (defaultOptions) => {
    return (element, options) => {
        return _mount(element, Object.assign(Object.assign({}, defaultOptions), options));
    };
};
// Side effects from "import { mount } from '@cypress/<my-framework>'" are annoying, we should avoid doing this
// by creating an explicit function/import that the user can register in their 'component.js' support file,
// such as:
//    import 'cypress/<my-framework>/support'
// or
//    import { registerCT } from 'cypress/<my-framework>'
//    registerCT()
// Note: This would be a breaking change
// it is required to unmount component in beforeEach hook in order to provide a clean state inside test
// because `mount` can be called after some preparation that can side effect unmount
// @see npm/react/cypress/component/advanced/set-timeout-example/loading-indicator-spec.js
setupHooks(preMountCleanup);

let root;
const cleanup = () => {
    if (root) {
        root.unmount();
        root = null;
        return true;
    }
    return false;
};
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
function mount(jsx, options = {}, rerenderKey) {
    // Remove last mounted component if cy.mount is called more than once in a test
    // React by default removes the last component when calling render, but we should remove the root
    // to wipe away any state
    cleanup();
    const internalOptions = {
        reactDom: ReactDOM,
        render: (reactComponent, el) => {
            if (!root) {
                root = ReactDOM.createRoot(el);
            }
            return root.render(reactComponent);
        },
        unmount: internalUnmount,
        cleanup,
    };
    return makeMountFn('mount', jsx, Object.assign({ ReactDom: ReactDOM }, options), rerenderKey, internalOptions);
}
function internalUnmount(options = { log: true }) {
    return makeUnmountFn(options);
}

exports.createMount = createMount;
exports.getContainerEl = getContainerEl;
exports.makeMountFn = makeMountFn;
exports.makeUnmountFn = makeUnmountFn;
exports.mount = mount;
