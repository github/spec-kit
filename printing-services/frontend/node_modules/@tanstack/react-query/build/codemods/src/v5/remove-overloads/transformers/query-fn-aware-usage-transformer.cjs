const createV5UtilsObject = require('../utils/index.cjs')
const UnknownUsageError = require('../utils/unknown-usage-error.cjs')
const createQueryClientTransformer = require('../../../utils/transformers/query-client-transformer.cjs')

/**
 * @param {import('jscodeshift').api} jscodeshift
 * @param {Object} utils
 * @param {import('jscodeshift').Collection} root
 * @param {string} filePath
 * @param {{keyName: "mutationKey"|"queryKey", queryClientMethods: ReadonlyArray<string>, hooks: ReadonlyArray<string>}} config
 */
const transformQueryFnAwareUsages = ({
  jscodeshift,
  utils,
  root,
  filePath,
  config,
}) => {
  const v5Utils = createV5UtilsObject({ jscodeshift, utils })

  /**
   * @param {import('jscodeshift').CallExpression} node
   * @returns {boolean}
   */
  const canSkipReplacement = (node) => {
    const callArguments = node.arguments

    const hasKeyProperty = () =>
      callArguments[0].properties.some(
        (property) =>
          utils.isObjectProperty(property) &&
          [config.keyName, 'queryFn'].includes(property.key.name),
      )

    return (
      callArguments.length > 0 &&
      utils.isObjectExpression(callArguments[0]) &&
      hasKeyProperty()
    )
  }

  const predicate = (property) => {
    const isSpreadElement = utils.isSpreadElement(property)
    const isObjectProperty = utils.isObjectProperty(property)

    return (
      isSpreadElement ||
      (isObjectProperty && property.key.name !== config.keyName)
    )
  }

  const transformArgumentToQueryFunction = (path, node) => {
    const isIdentifier = utils.isIdentifier(node)
    const isFunctionDefinition = utils.isFunctionDefinition(node)

    if (!isIdentifier && !isFunctionDefinition) {
      return undefined
    }

    if (isFunctionDefinition) {
      return jscodeshift.property(
        'init',
        jscodeshift.identifier('queryFn'),
        node,
      )
    }

    const binding = v5Utils.getBindingFromScope(path, node.name, filePath)
    const initializer = v5Utils.getInitializerByDeclarator(binding)

    if (!utils.isFunctionDefinition(initializer)) {
      return undefined
    }

    return jscodeshift.property(
      'init',
      jscodeshift.identifier('queryFn'),
      binding.id,
    )
  }

  const transformArgumentToOptionsObject = (path, node) => {
    if (!utils.isIdentifier(node)) {
      return undefined
    }

    const binding = v5Utils.getBindingFromScope(path, node.name, filePath)
    const initializer = v5Utils.getInitializerByDeclarator(binding)

    if (utils.isObjectExpression(initializer)) {
      return jscodeshift.spreadElement(binding.id)
    }
  }

  const replacer = (path) => {
    const node = path.node

    try {
      // If the given method/function call matches certain criteria, the node doesn't need to be replaced, this step can be skipped.
      if (canSkipReplacement(node)) {
        return node
      }

      const keyProperty = v5Utils.transformArgumentToKey(
        path,
        node.arguments[0],
        config.keyName,
        filePath,
      )

      if (!keyProperty) {
        throw new UnknownUsageError(node, filePath)
      }

      const parameters = [jscodeshift.objectExpression([keyProperty])]
      const createdObjectExpression = parameters[0]
      const secondParameter = node.arguments[1]

      if (secondParameter) {
        const queryFnProperty = transformArgumentToQueryFunction(
          path,
          secondParameter,
        )

        if (queryFnProperty) {
          createdObjectExpression.properties.push(queryFnProperty)

          const thirdParameter = node.arguments[2]

          if (utils.isObjectExpression(thirdParameter)) {
            v5Utils.copyPropertiesFromSource(
              thirdParameter,
              createdObjectExpression,
              predicate,
            )
          } else {
            createdObjectExpression.properties.push(
              jscodeshift.spreadElement(thirdParameter),
            )
          }

          return jscodeshift.callExpression(node.original.callee, parameters)
        }

        const optionsProperty = transformArgumentToOptionsObject(
          path,
          secondParameter,
        )

        if (optionsProperty) {
          createdObjectExpression.properties.push(optionsProperty)

          return jscodeshift.callExpression(node.original.callee, parameters)
        }

        if (utils.isObjectExpression(secondParameter)) {
          v5Utils.copyPropertiesFromSource(
            secondParameter,
            createdObjectExpression,
            predicate,
          )
        }

        return jscodeshift.callExpression(node.original.callee, parameters)
      }

      return jscodeshift.callExpression(node.original.callee, parameters)
    } catch (error) {
      utils.warn(
        error.name === UnknownUsageError.name
          ? error.message
          : `An unknown error occurred while processing the "${filePath}" file. Please review this file, because the codemod couldn't be applied.`,
      )

      return node
    }
  }

  createQueryClientTransformer({ jscodeshift, utils, root }).execute(
    config.queryClientMethods,
    replacer,
  )
}

module.exports = transformQueryFnAwareUsages
