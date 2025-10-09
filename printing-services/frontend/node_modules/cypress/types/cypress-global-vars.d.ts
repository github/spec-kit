/**
 * Global variables `cy` added by Cypress with all API commands.
 * @see https://on.cypress.io/api
 *
```
cy.get('button').click()
cy.get('.result').contains('Expected text')
```
 */
declare var cy: Cypress.cy & CyEventEmitter

/**
 * Global variable `Cypress` holds common utilities and constants.
 * @see https://on.cypress.io/api
 *
```
Cypress.config("pageLoadTimeout") // => 60000
Cypress.version // => "1.4.0"
Cypress._ // => Lodash _
```
 */
declare var Cypress: Cypress.Cypress & CyEventEmitter
