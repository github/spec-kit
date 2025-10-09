/// <reference types="cypress" />

import { InputSignal, WritableSignal, Type } from '@angular/core';
import { TestModuleMetadata, ComponentFixture, TestComponentRenderer } from '@angular/core/testing';

/**
 * Additional module configurations needed while mounting the component, like
 * providers, declarations, imports and even component @Inputs()
 *
 * @interface MountConfig
 * @see https://angular.io/api/core/testing/TestModuleMetadata
 */
interface MountConfig<T> extends TestModuleMetadata {
    /**
     * @memberof MountConfig
     * @description flag to automatically create a cy.spy() for every component @Output() property
     * @example
     * export class ButtonComponent {
     *  @Output clicked = new EventEmitter()
     * }
     *
     * cy.mount(ButtonComponent, { autoSpyOutputs: true })
     * cy.get('@clickedSpy).should('have.been.called')
     */
    autoSpyOutputs?: boolean;
    /**
     * @memberof MountConfig
     * @description flag defaulted to true to automatically detect changes in your components
     */
    autoDetectChanges?: boolean;
    /**
     * @memberof MountConfig
     * @example
     * import { ButtonComponent } from 'button/button.component'
     * it('renders a button with Save text', () => {
     *  cy.mount(ButtonComponent, { componentProperties: { text: 'Save' }})
     *  cy.get('button').contains('Save')
     * })
     *
     * it('renders a button with a cy.spy() replacing EventEmitter', () => {
     *  cy.mount(ButtonComponent, {
     *    componentProperties: {
     *      clicked: cy.spy().as('mySpy)
     *    }
     *  })
     *  cy.get('button').click()
     *  cy.get('@mySpy').should('have.been.called')
     * })
     */
    componentProperties?: Partial<{
        [P in keyof T]: T[P] extends InputSignal<infer V> ? InputSignal<V> | WritableSignal<V> | V : T[P];
    }>;
}
/**
 * Type that the `mount` function returns
 * @type MountResponse<T>
 */
type MountResponse<T> = {
    /**
     * Fixture for debugging and testing a component.
     *
     * @memberof MountResponse
     * @see https://angular.io/api/core/testing/ComponentFixture
     */
    fixture: ComponentFixture<T>;
    /**
     * The instance of the root component class
     *
     * @memberof MountResponse
     * @see https://angular.io/api/core/testing/ComponentFixture#componentInstance
     */
    component: T;
};
declare class CypressTestComponentRenderer extends TestComponentRenderer {
    insertRootElement(rootElId: string): void;
    removeAllRootElements(): void;
}
/**
 * Mounts an Angular component inside Cypress browser
 *
 * @param component Angular component being mounted or its template
 * @param config configuration used to configure the TestBed
 * @example
 * import { mount } from '@cypress/angular'
 * import { StepperComponent } from './stepper.component'
 * import { MyService } from 'services/my.service'
 * import { SharedModule } from 'shared/shared.module';
 * it('mounts', () => {
 *    mount(StepperComponent, {
 *      providers: [MyService],
 *      imports: [SharedModule]
 *    })
 *    cy.get('[data-cy=increment]').click()
 *    cy.get('[data-cy=counter]').should('have.text', '1')
 * })
 *
 * // or
 *
 * it('mounts with template', () => {
 *   mount('<app-stepper></app-stepper>', {
 *     declarations: [StepperComponent],
 *   })
 * })
 *
 * @see {@link https://on.cypress.io/mounting-angular} for more details.
 *
 * @returns A component and component fixture
 */
declare function mount<T>(component: Type<T> | string, config?: MountConfig<T>): Cypress.Chainable<MountResponse<T>>;
/**
 * Creates a new Event Emitter and then spies on it's `emit` method
 *
 * @param {string} alias name you want to use for your cy.spy() alias
 * @returns EventEmitter<T>
 * @example
 * import { StepperComponent } from './stepper.component'
 * import { mount, createOutputSpy } from '@cypress/angular'
 *
 * it('Has spy', () => {
 *   mount(StepperComponent, { componentProperties: { change: createOutputSpy('changeSpy') } })
 *   cy.get('[data-cy=increment]').click()
 *   cy.get('@changeSpy').should('have.been.called')
 * })
 *
 * // Or for use with Angular Signals following the output nomenclature.
 * // see https://v17.angular.io/guide/model-inputs#differences-between-model-and-input/
 *
 * it('Has spy', () => {
 *   mount(StepperComponent, { componentProperties: { count: signal(0), countChange: createOutputSpy('countChange') } })
 *   cy.get('[data-cy=increment]').click()
 *   cy.get('@countChange').should('have.been.called')
 * })
 */
declare const createOutputSpy: <T>(alias: string) => any;

export { CypressTestComponentRenderer, MountConfig, MountResponse, createOutputSpy, mount };
