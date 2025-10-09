# @cypress/svelte

Mount Svelte components in the open source [Cypress.io](https://www.cypress.io/) test runner

> **Note:** This package is bundled with the `cypress` package and should not need to be installed separately. See the [Svelte Component Testing Docs](https://docs.cypress.io/guides/component-testing/svelte/overview) for mounting Svelte components. Installing and importing `mount` from `@cypress/svelte` should only be done for advanced use-cases or in the case you may require an older or non supported version of svelte.

## Requirements

- Svelte 5+ (Cypress 13 and under supports Svelte 4 and under)

## Development

Run `yarn build` to compile and sync packages to the `cypress` cli package.

Run `yarn cy:open` to open Cypress component testing against real-world examples.

Run `yarn test` to execute headless Cypress tests.

## [Changelog](./CHANGELOG.md)
