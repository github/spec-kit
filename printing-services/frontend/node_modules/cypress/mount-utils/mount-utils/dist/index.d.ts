export declare const ROOT_SELECTOR = "[data-cy-root]";
/**
 * Gets the root element used to mount the component.
 * @returns {HTMLElement} The root element
 * @throws {Error} If the root element is not found
 */
export declare const getContainerEl: () => HTMLElement;
/**
 * Utility function to register CT side effects and run cleanup code during the "test:before:run" Cypress hook
 * @param optionalCallback Callback to be called before the next test runs
 */
export declare function setupHooks(optionalCallback?: Function): void;
