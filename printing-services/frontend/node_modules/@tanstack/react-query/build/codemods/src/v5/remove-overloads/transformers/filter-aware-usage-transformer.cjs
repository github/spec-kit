const createV5UtilsObject = require('../utils/index.cjs')
const UnknownUsageError = require('../utils/unknown-usage-error.cjs')
const createQueryClientTransformer = require('../../../utils/transformers/query-client-transformer.cjs')
const createQueryCacheTransformer = require('../../../utils/transformers/query-cache-transformer.cjs')
const createUseQueryLikeTransformer = require('../../../utils/transformers/use-query-like-transformer.cjs')

/**
 * @param {import('jscodeshift').api} jscodeshift
 * @param {Object} utils
 * @param {import('jscodeshift').Collection} root
 * @param {string} filePath
 * @param {{keyName: "mutationKey"|"queryKey", fnName: "mutationFn"|"queryFn", queryClientMethods: ReadonlyArray<string>, hooks: ReadonlyArray<string>}} config
 */
const transformFilterAwareUsages = ({
  jscodeshift,
  utils,
  root,
  filePath,
  config,
}) => {
  const v5Utils = createV5UtilsObject({ jscodeshift, utils })

  /**
   * @param {import('jscodeshift').CallExpression} node
   * @param {"mutationKey"|"queryKey"} keyName
   * @param {"mutationFn"|"queryFn"} fnName
   * @returns {boolean}
   */
  const canSkipReplacement = (node, keyName, fnName) => {
    const callArguments = node.arguments

    const hasKeyOrFnProperty = () =>
      callArguments[0].properties.some(
        (property) =>
          utils.isObjectProperty(property) &&
          property.key.name !== keyName &&
          property.key.name !== fnName,
      )

    /**
     * This call has at least one argument. If it's an object expression and contains the "queryKey" or "mutationKey"
     * field, the transformation can be skipped, because it's already matching the expected signature.
     */
    return (
      callArguments.length > 0 &&
      utils.isObjectExpression(callArguments[0]) &&
      hasKeyOrFnProperty()
    )
  }

  /**
   * This function checks whether the given object property is a spread element or a property that's not named
   * "queryKey" or "mutationKey".
   *
   * @param {import('jscodeshift').ObjectProperty} property
   * @returns {boolean}
   */
  const predicate = (property) => {
    const isSpreadElement = utils.isSpreadElement(property)
    const isObjectProperty = utils.isObjectProperty(property)

    return (
      isSpreadElement ||
      (isObjectProperty && property.key.name !== config.keyName)
    )
  }

  const replacer = (path) => {
    const node = path.node

    const isFunctionDefinition = (functionArgument) => {
      if (utils.isFunctionDefinition(functionArgument)) {
        return true
      }

      if (utils.isIdentifier(functionArgument)) {
        const binding = v5Utils.getBindingFromScope(
          path,
          functionArgument.name,
          filePath,
        )

        const isVariableDeclarator = jscodeshift.match(binding, {
          type: jscodeshift.VariableDeclarator.name,
        })

        return isVariableDeclarator && utils.isFunctionDefinition(binding.init)
      }
    }

    try {
      // If the given method/function call matches certain criteria, the node doesn't need to be replaced, this step can be skipped.
      if (canSkipReplacement(node, config.keyName, config.fnName)) {
        return node
      }

      /**
       * Here we attempt to determine the first parameter of the function call.
       * If it's a function definition, we can create an object property from it (the mutation fn).
       */
      const firstArgument = node.arguments[0]
      if (isFunctionDefinition(firstArgument)) {
        const objectExpression = jscodeshift.objectExpression([
          jscodeshift.property(
            'init',
            jscodeshift.identifier(config.fnName),
            firstArgument,
          ),
        ])

        const secondArgument = node.arguments[1]

        if (secondArgument) {
          // If it's an object expression, we can copy the properties from it to the newly created object expression.
          if (utils.isObjectExpression(secondArgument)) {
            v5Utils.copyPropertiesFromSource(
              secondArgument,
              objectExpression,
              predicate,
            )
          } else {
            // Otherwise, we simply spread the second argument in the newly created object expression.
            objectExpression.properties.push(
              jscodeshift.spreadElement(secondArgument),
            )
          }
        }

        return jscodeshift.callExpression(node.original.callee, [
          objectExpression,
        ])
      }

      /**
       * If, instead, the first parameter is an array expression or an identifier that references
       * an array expression, then we create an object property from it (the query or mutation key).
       *
       * @type {import('jscodeshift').Property|undefined}
       */
      const keyProperty = v5Utils.transformArgumentToKey(
        path,
        node.arguments[0],
        config.keyName,
        filePath,
      )

      /**
       * The first parameter couldn't be transformed into an object property, so it's time to throw an exception,
       * it will notify the consumers that they need to rewrite this usage manually.
       */
      if (!keyProperty) {
        const secondArgument =
          node.arguments.length > 1 ? node.arguments[1] : null

        if (!secondArgument) {
          throw new UnknownUsageError(node, filePath)
        }

        if (utils.isFunctionDefinition(secondArgument)) {
          const originalArguments = node.arguments
          const firstArgument = jscodeshift.objectExpression([
            jscodeshift.property(
              'init',
              jscodeshift.identifier(config.keyName),
              originalArguments[0],
            ),
            jscodeshift.property(
              'init',
              jscodeshift.identifier(config.fnName),
              secondArgument,
            ),
          ])

          return jscodeshift.callExpression(node.original.callee, [
            firstArgument,
            ...originalArguments.slice(2),
          ])
        }
      }

      const functionArguments = [jscodeshift.objectExpression([keyProperty])]
      const secondParameter = node.arguments[1]

      if (secondParameter) {
        const createdObjectExpression = functionArguments[0]

        if (isFunctionDefinition(secondParameter)) {
          const objectExpression = jscodeshift.objectExpression([
            jscodeshift.property(
              'init',
              jscodeshift.identifier(config.keyName),
              node.arguments[0],
            ),
            jscodeshift.property(
              'init',
              jscodeshift.identifier(config.fnName),
              secondParameter,
            ),
          ])

          const thirdArgument = node.arguments[2]

          if (thirdArgument) {
            // If it's an object expression, we can copy the properties from it to the newly created object expression.
            if (utils.isObjectExpression(thirdArgument)) {
              v5Utils.copyPropertiesFromSource(
                thirdArgument,
                objectExpression,
                predicate,
              )
            } else {
              // Otherwise, we simply spread the third argument in the newly created object expression.
              objectExpression.properties.push(
                jscodeshift.spreadElement(thirdArgument),
              )
            }
          }

          return jscodeshift.callExpression(node.original.callee, [
            objectExpression,
          ])
        }

        /**
         * If it has a second argument, and it's an object expression, then we get the properties from it
         * (except the "queryKey" or "mutationKey" properties), because these arguments will also be moved to the
         * newly created object expression.
         */
        if (utils.isObjectExpression(secondParameter)) {
          v5Utils.copyPropertiesFromSource(
            secondParameter,
            createdObjectExpression,
            predicate,
          )
        } else {
          // Otherwise, we simply spread the second parameter in the newly created object expression.
          createdObjectExpression.properties.push(
            jscodeshift.spreadElement(secondParameter),
          )
        }
      }

      // The rest of the function arguments can be simply pushed to the function arguments object so all will be kept.
      functionArguments.push(...node.arguments.slice(2))

      return jscodeshift.callExpression(node.original.callee, functionArguments)
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

  createUseQueryLikeTransformer({ jscodeshift, utils, root }).execute(
    config.hooks,
    replacer,
  )

  createQueryCacheTransformer({ jscodeshift, utils, root }).execute(replacer)
}

module.exports = transformFilterAwareUsages
