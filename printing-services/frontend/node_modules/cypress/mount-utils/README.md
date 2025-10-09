# @cypress/mount-utils

> **Note** this package is not meant to be used outside of cypress component testing.

This library exports some shared types and utility functions designed to build adapters for components frameworks.

It is used in:

- [`@cypress/react`](https://github.com/cypress-io/cypress/tree/develop/npm/react)
- [`@cypress/vue`](https://github.com/cypress-io/cypress/tree/develop/npm/vue)
- [`@cypress/svelte`](https://github.com/cypress-io/cypress/tree/develop/npm/svelte)
- [`@cypress/angular`](https://github.com/cypress-io/cypress/tree/develop/npm/angular)

## What is a Mount Adapter?

All Component Tests require a component to be **mounted**. This is generally done with a custom command, `cy.mount` by default.


### Requirements

All the functionality used to create the first party Mount adapters is available to support third parties adapters. At minimum, a Mount Adapter must:

- Receive a component as the first argument. This could be class, function etc - depends on the framework.
- Return a Cypress Chainable (for example using `cy.wrap`) that resolves whatever is idiomatic for your framework
- Call `getContainerEl` to access the root DOM element

In addition, we recommend that Mount Adapters:

- call `setupHooks` to register the required lifecycle hooks for `@cypress/mount-utils` to work

### Example Mount Adapter: Web Components 

Here's a simple yet realistic example of Mount Adapter targeting Web Components. It uses utilities from this package (`@cypress/mount-utils`) This is recommended, so your adapter behaves similar to the first party Mount Adapters.

```ts
import {
  ROOT_SELECTOR,
  setupHooks,
  getContainerEl
} from "@cypress/mount-utils";

Cypress.on("run:start", () => {
  // Consider doing a check to ensure your adapter only runs in Component Testing mode.
  if (Cypress.testingType !== "component") {
    return;
  }

  Cypress.on("test:before:run", () => {
    // Do some cleanup from previous test - for example, clear the DOM.
    getContainerEl().innerHTML = "";
  });
});

function maybeRegisterComponent<T extends CustomElementConstructor>(
  name: string,
  webComponent: T
) {
  // Avoid double-registering a Web Component.
  if (window.customElements.get(name)) {
    return;
  }

  window.customElements.define(name, webComponent);
}

export function mount(
  webComponent: CustomElementConstructor
): Cypress.Chainable {
  // Get root selector defined in `cypress/support.component-index.html
  const $root = document.querySelector(ROOT_SELECTOR)!;

  // Change to kebab-case to comply with Web Component naming convention
  const name = webComponent.name
    .replace(/([a-z0–9])([A-Z])/g, "$1-$2")
    .toLowerCase();

  /// Register Web Component
  maybeRegisterComponent(name, webComponent);

  // Render HTML containing component.
  $root.innerHTML = `<${name} id="root"></${name}>`;

  // Log a messsage in the Command Log.
  Cypress.log({
    name: "mount",
    message: [`<${name} ... />`],
  });

  // Return a `Cypress.Chainable` that returns whatever is idiomatic
  // in the framework your mount adapter targets.
  return cy.wrap(document.querySelector("#root"), { log: false });
}

// Setup Cypress lifecycle hooks.
setupHooks();
```

Usage:

```ts
// User will generally register a `cy.mount` command in `cypress/support/component.js`:

import { mount } from '@package/cypress-web-components'

Cypress.Commands.add('mount', mount)

// Test
export class WebCounter extends HTMLElement {
  constructor() {
    super();
  }

  connectedCallback() {
    this.innerHTML = `
      <div>
        <button>Counter</button>
      </div>`;
  }
}


describe('web-component.cy.ts', () => {
  it('playground', () => {
    cy.mount(WebCounter)
  })
})
```

For more robust, production ready examples, check out our first party adapters.

## Compatibility

| @cypress/mount-utils | cypress |
| -------------------- | ------- |
| <= v1                | <= v9   |
| >= v2                | >= v10  |

## Changelog

[Changelog](./CHANGELOG.md)
