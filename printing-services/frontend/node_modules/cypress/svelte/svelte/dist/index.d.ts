/// <reference types="cypress" />

import { Component, MountOptions } from 'svelte';

interface MountReturn {
    component: Record<string, any>;
}
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
declare function mount(Component: Component<Record<string, any>, Record<string, any>, any>, options?: Omit<MountOptions, 'target'> & {
    log?: boolean;
}): Cypress.Chainable<MountReturn>;

export { MountReturn, mount };
