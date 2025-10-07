const UnknownUsageError = require('./unknown-usage-error.cjs')

module.exports = ({ jscodeshift, utils }) => {
  /**
   *
   * @param {import('jscodeshift').ObjectExpression} source
   * @param {import('jscodeshift').ObjectExpression} target
   * @param {(node: import('jscodeshift').Node) => boolean} predicate
   */
  const copyPropertiesFromSource = (source, target, predicate) => {
    source.properties.forEach((property) => {
      if (predicate(property)) {
        target.properties.push(property)
      }
    })
  }

  /**
   * @param {import('jscodeshift').NodePath} path
   * @param {string} argumentName
   * @param {string} filePath
   * @returns {*}
   */
  const getBindingFromScope = (path, argumentName, filePath) => {
    /**
     * If the current scope contains the declaration then we can use the actual one else we attempt to find the
     * binding from above.
     */
    const scope = path.scope.declares(argumentName)
      ? path.scope
      : path.scope.lookup(argumentName)

    /**
     * The declaration couldn't be found for some reason, time to move on. We warn the user it needs to be rewritten
     * by themselves.
     */
    if (!scope) {
      return undefined
    }

    const binding = scope.bindings[argumentName]
      .filter((item) => utils.isIdentifier(item.value))
      .map((item) => item.parentPath.value)
      .at(0)

    if (!binding) {
      throw new UnknownUsageError(path.node, filePath)
    }

    return binding
  }

  /**
   * @param {import('jscodeshift').VariableDeclarator} binding
   * @returns {import('jscodeshift').Node|undefined}
   */
  const getInitializerByDeclarator = (binding) => {
    const isVariableDeclaration = jscodeshift.match(binding, {
      type: jscodeshift.VariableDeclarator.name,
    })

    if (!isVariableDeclaration) {
      return undefined
    }

    const isTSAsExpression = jscodeshift.match(binding.init, {
      type: jscodeshift.TSAsExpression.name,
    })

    return isTSAsExpression ? binding.init.expression : binding.init
  }

  /**
   * @param {import('jscodeshift').Node} node
   * @returns {boolean}
   */
  const isArrayExpressionVariable = (node) =>
    jscodeshift.match(node, {
      type: jscodeshift.VariableDeclarator.name,
      init: {
        type: jscodeshift.ArrayExpression.name,
      },
    })

  /**
   * @param {import('jscodeshift').NodePath} path
   * @param {import('jscodeshift').Node} node
   * @param {"queryKey"|"mutationKey"} keyName
   * @param {string} filePath
   * @returns {import('jscodeshift').Property|undefined}
   */
  const transformArgumentToKey = (path, node, keyName, filePath) => {
    // If the first argument is an identifier we have to infer its type if possible.
    if (utils.isIdentifier(node)) {
      const binding = getBindingFromScope(path, node.name, filePath)

      if (isArrayExpressionVariable(binding)) {
        return jscodeshift.property(
          'init',
          jscodeshift.identifier(keyName),
          jscodeshift.identifier(binding.id.name),
        )
      }
    }

    // If the first argument is an array, then it matches the following overload:
    // methodName(queryKey?: QueryKey, firstObject?: TFirstObject, secondObject?: TSecondObject)
    if (utils.isArrayExpression(node)) {
      // Then we create the 'queryKey' property based on it, because it will be passed to the first argument
      // that should be an object according to the new signature.
      return jscodeshift.property('init', jscodeshift.identifier(keyName), node)
    }

    return undefined
  }

  return {
    copyPropertiesFromSource,
    getInitializerByDeclarator,
    getBindingFromScope,
    transformArgumentToKey,
  }
}
