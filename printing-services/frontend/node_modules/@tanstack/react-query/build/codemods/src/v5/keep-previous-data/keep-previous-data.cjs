const createUtilsObject = require('../../utils/index.cjs')
const createUseQueryLikeTransformer = require('../../utils/transformers/use-query-like-transformer.cjs')
const createQueryClientTransformer = require('../../utils/transformers/query-client-transformer.cjs')
const AlreadyHasPlaceholderDataProperty = require('./utils/already-has-placeholder-data-property.cjs')

/**
 * @param {import('jscodeshift')} jscodeshift
 * @param {Object} utils
 * @param {import('jscodeshift').Collection} root
 * @param {string} filePath
 * @param {{keyName: "mutationKey"|"queryKey", queryClientMethods: ReadonlyArray<string>, hooks: ReadonlyArray<string>}} config
 */
const transformUsages = ({ jscodeshift, utils, root, filePath, config }) => {
  /**
   * @param {import('jscodeshift').CallExpression | import('jscodeshift').ExpressionStatement} node
   * @returns {{start: number, end: number}}
   */
  const getNodeLocation = (node) => {
    const location = utils.isCallExpression(node) ? node.callee.loc : node.loc
    const start = location.start.line
    const end = location.end.line

    return { start, end }
  }

  /**
   * @param {import('jscodeshift').ObjectProperty} objectProperty
   * @returns {boolean}
   */
  const isKeepPreviousDataObjectProperty = (objectProperty) => {
    return jscodeshift.match(objectProperty.key, {
      type: jscodeshift.Identifier.name,
      name: 'keepPreviousData',
    })
  }

  /**
   * @param {import('jscodeshift').ObjectProperty} objectProperty
   * @returns {boolean}
   */
  const isObjectPropertyHasTrueBooleanLiteralValue = (objectProperty) => {
    return jscodeshift.match(objectProperty.value, {
      type: jscodeshift.BooleanLiteral.name,
      value: true,
    })
  }

  /**
   * @param {import('jscodeshift').ObjectExpression} objectExpression
   * @returns {Array<import('jscodeshift').ObjectProperty>}
   */
  const filterKeepPreviousDataProperty = (objectExpression) => {
    return objectExpression.properties.filter((objectProperty) => {
      return !isKeepPreviousDataObjectProperty(objectProperty)
    })
  }

  const createPlaceholderDataObjectProperty = () => {
    return jscodeshift.objectProperty(
      jscodeshift.identifier('placeholderData'),
      jscodeshift.identifier('keepPreviousData'),
    )
  }

  /**
   * @param {import('jscodeshift').ObjectExpression} objectExpression
   * @returns {boolean}
   */
  const hasPlaceholderDataProperty = (objectExpression) => {
    return (
      objectExpression.properties.findIndex((objectProperty) => {
        return jscodeshift.match(objectProperty.key, {
          type: jscodeshift.Identifier.name,
          name: 'placeholderData',
        })
      }) !== -1
    )
  }

  /**
   * @param {import('jscodeshift').ObjectExpression} objectExpression
   * @returns {import('jscodeshift').ObjectProperty | undefined}
   */
  const getKeepPreviousDataProperty = (objectExpression) => {
    return objectExpression.properties.find(isKeepPreviousDataObjectProperty)
  }

  let shouldAddKeepPreviousDataImport = false

  const replacer = (path, resolveTargetArgument, transformNode) => {
    const node = path.node
    const { start, end } = getNodeLocation(node)

    try {
      const targetArgument = resolveTargetArgument(node)

      if (targetArgument && utils.isObjectExpression(targetArgument)) {
        const isPlaceholderDataPropertyPresent =
          hasPlaceholderDataProperty(targetArgument)

        if (hasPlaceholderDataProperty(targetArgument)) {
          throw new AlreadyHasPlaceholderDataProperty(node, filePath)
        }

        const keepPreviousDataProperty =
          getKeepPreviousDataProperty(targetArgument)

        const keepPreviousDataPropertyHasTrueValue =
          isObjectPropertyHasTrueBooleanLiteralValue(keepPreviousDataProperty)

        if (!keepPreviousDataPropertyHasTrueValue) {
          utils.warn(
            `The usage in file "${filePath}" at line ${start}:${end} already contains a "keepPreviousData" property but its value is not "true". Please migrate this usage manually.`,
          )

          return node
        }

        if (keepPreviousDataPropertyHasTrueValue) {
          // Removing the `keepPreviousData` property from the object.
          const mutableObjectExpressionProperties =
            filterKeepPreviousDataProperty(targetArgument)

          if (!isPlaceholderDataPropertyPresent) {
            shouldAddKeepPreviousDataImport = true

            // When the `placeholderData` property is not present, the `placeholderData: keepPreviousData` property will be added.
            mutableObjectExpressionProperties.push(
              createPlaceholderDataObjectProperty(),
            )
          }

          return transformNode(
            node,
            jscodeshift.objectExpression(mutableObjectExpressionProperties),
          )
        }
      }

      utils.warn(
        `The usage in file "${filePath}" at line ${start}:${end} could not be transformed, because the first parameter is not an object expression. Please migrate this usage manually.`,
      )

      return node
    } catch (error) {
      utils.warn(
        error.name === AlreadyHasPlaceholderDataProperty.name
          ? error.message
          : `An unknown error occurred while processing the "${filePath}" file. Please review this file, because the codemod couldn't be applied.`,
      )

      return node
    }
  }

  createUseQueryLikeTransformer({ jscodeshift, utils, root }).execute(
    config.hooks,
    (path) => {
      const resolveTargetArgument = (node) => node.arguments[0] ?? null
      const transformNode = (node, transformedArgument) =>
        jscodeshift.callExpression(node.original.callee, [transformedArgument])

      return replacer(path, resolveTargetArgument, transformNode)
    },
  )

  createQueryClientTransformer({ jscodeshift, utils, root }).execute(
    config.queryClientMethods,
    (path) => {
      const resolveTargetArgument = (node) => node.arguments[1] ?? null
      const transformNode = (node, transformedArgument) => {
        return jscodeshift.callExpression(node.original.callee, [
          node.arguments[0],
          transformedArgument,
          ...node.arguments.slice(2, 0),
        ])
      }

      return replacer(path, resolveTargetArgument, transformNode)
    },
  )

  const importIdentifierOfQueryClient = utils.getSelectorByImports(
    utils.locateImports(['QueryClient']),
    'QueryClient',
  )

  root
    .find(jscodeshift.ExpressionStatement, {
      expression: {
        type: jscodeshift.NewExpression.name,
        callee: {
          type: jscodeshift.Identifier.name,
          name: importIdentifierOfQueryClient,
        },
      },
    })
    .filter((path) => path.node.expression)
    .replaceWith((path) => {
      const resolveTargetArgument = (node) => {
        const paths = jscodeshift(node)
          .find(jscodeshift.ObjectProperty, {
            key: {
              type: jscodeshift.Identifier.name,
              name: 'keepPreviousData',
            },
          })
          .paths()

        return paths.length > 0 ? paths[0].parent.node : null
      }
      const transformNode = (node, transformedArgument) => {
        jscodeshift(node.expression)
          .find(jscodeshift.ObjectProperty, {
            key: {
              type: jscodeshift.Identifier.name,
              name: 'queries',
            },
          })
          .replaceWith(({ node: mutableNode }) => {
            mutableNode.value.properties = transformedArgument.properties

            return mutableNode
          })

        return node
      }

      return replacer(path, resolveTargetArgument, transformNode)
    })

  return { shouldAddKeepPreviousDataImport }
}

module.exports = (file, api) => {
  const jscodeshift = api.jscodeshift
  const root = jscodeshift(file.source)
  const utils = createUtilsObject({ root, jscodeshift })
  const filePath = file.path

  const dependencies = { jscodeshift, utils, root, filePath }

  const { shouldAddKeepPreviousDataImport } = transformUsages({
    ...dependencies,
    config: {
      hooks: ['useInfiniteQuery', 'useQueries', 'useQuery'],
      queryClientMethods: ['setQueryDefaults'],
    },
  })

  if (shouldAddKeepPreviousDataImport) {
    root
      .find(jscodeshift.ImportDeclaration, {
        source: {
          value: '@tanstack/react-query',
        },
      })
      .replaceWith(({ node: mutableNode }) => {
        mutableNode.specifiers = [
          jscodeshift.importSpecifier(
            jscodeshift.identifier('keepPreviousData'),
          ),
          ...mutableNode.specifiers,
        ]

        return mutableNode
      })
  }

  return root.toSource({ quote: 'single', lineTerminator: '\n' })
}
