const { createMacro, MacroError } = require('babel-plugin-macros');
const { addNamed } = require('@babel/helper-module-imports');

module.exports = createMacro(gooberMacro);

function gooberMacro({ references, babel, state }) {
    const program = state.file.path;

    if (references.default) {
        throw new MacroError('goober.macro does not support default import');
    }

    // Inject import {...} from 'goober'
    Object.keys(references).forEach((refName) => {
        const id = addNamed(program, refName, 'goober');
        references[refName].forEach((referencePath) => {
            referencePath.node.name = id.name;
        });
    });

    const t = babel.types;

    const styledReferences = references.styled || [];

    styledReferences.forEach((referencePath) => {
        const type = referencePath.parentPath.type;

        if (type === 'MemberExpression') {
            const node = referencePath.parentPath.node;
            const functionName = node.object.name;
            let elementName = node.property.name;

            // Support custom elements
            if (/[A-Z]/.test(elementName)) {
                elementName = elementName.replace(/[A-Z]/g, '-$&').toLowerCase();
            }

            referencePath.parentPath.replaceWith(
                t.callExpression(t.identifier(functionName), [t.stringLiteral(elementName)])
            );
        }
    });
}
