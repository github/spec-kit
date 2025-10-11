const createUtilsObject = require('../../utils/index.cjs')
const createUseQueryLikeTransformer = require('../../utils/transformers/use-query-like-transformer.cjs')
const createQueryClientTransformer = require('../../utils/transformers/query-client-transformer.cjs')

const originalName = 'isLoading'
const newName = 'isPending'

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
   * @param {import('jscodeshift').ASTNode} node
   * @returns {boolean}
   */
  const isObjectExpression = (node) => {
    return jscodeshift.match(node, {
      type: jscodeshift.ObjectExpression.name,
    })
  }

  /**
   * @param {import('jscodeshift').ASTNode} node
   * @returns {boolean}
   */
  const isObjectPattern = (node) => {
    return jscodeshift.match(node, {
      type: jscodeshift.ObjectPattern.name,
    })
  }

  /**
   * @param {import('jscodeshift').ASTNode} node
   * @returns {boolean}
   */
  const isVariableDeclarator = (node) => {
    return jscodeshift.match(node, {
      type: jscodeshift.VariableDeclarator.name,
    })
  }

  /**
   * @param {import('jscodeshift').Node} node
   * @param {import('jscodeshift').Identifier} identifier
   * @returns {Collection<import('jscodeshift').MemberExpression>}
   */
  const findIsLoadingPropertiesOfIdentifier = (node, identifier) => {
    return jscodeshift(node).find(jscodeshift.MemberExpression, {
      object: {
        type: jscodeshift.Identifier.name,
        name: identifier.name,
      },
      property: {
        type: jscodeshift.Identifier.name,
        name: originalName,
      },
    })
  }

  /**
   * @param {import('jscodeshift').ObjectPattern} node
   * @returns {import('jscodeshift').ObjectProperty|null}
   */
  const findIsLoadingObjectPropertyInObjectPattern = (node) => {
    return (
      node.properties.find((property) =>
        jscodeshift.match(property, {
          key: {
            type: jscodeshift.Identifier.name,
            name: originalName,
          },
        }),
      ) ?? null
    )
  }

  /**
   * @param {import('jscodeshift').ObjectPattern} node
   * @returns {import('jscodeshift').RestElement|null}
   */
  const findRestElementInObjectPattern = (node) => {
    return (
      node.properties.find((property) =>
        jscodeshift.match(property, {
          type: jscodeshift.RestElement.name,
        }),
      ) ?? null
    )
  }

  const replacer = (path, transformNode) => {
    const node = path.node
    const parentNode = path.parentPath.value
    const { start, end } = getNodeLocation(node)

    try {
      if (!isVariableDeclarator(parentNode)) {
        // The parent node is not a variable declarator, the transformation will be skipped.
        return node
      }

      const lookupNode = path.scope.node
      const variableDeclaratorId = parentNode.id

      if (isObjectPattern(variableDeclaratorId)) {
        const isLoadingObjectProperty =
          findIsLoadingObjectPropertyInObjectPattern(variableDeclaratorId)

        if (isLoadingObjectProperty) {
          jscodeshift(lookupNode)
            .find(jscodeshift.ObjectProperty, {
              key: {
                type: jscodeshift.Identifier.name,
                name: originalName,
              },
            })
            .replaceWith((mutablePath) => {
              if (isObjectPattern(mutablePath.parent)) {
                const affectedProperty = mutablePath.value.value.shorthand
                  ? 'value'
                  : 'key'

                mutablePath.value[affectedProperty].name = newName

                return mutablePath.value
              }

              if (isObjectExpression(mutablePath.parent)) {
                const affectedProperty = mutablePath.value.value.shorthand
                  ? 'key'
                  : 'value'

                mutablePath.value[affectedProperty].name = newName

                return mutablePath.value
              }

              return mutablePath.value
            })

          // Renaming all other 'isLoading' references that are object properties.
          jscodeshift(lookupNode)
            .find(jscodeshift.Identifier, { name: originalName })
            .replaceWith((mutablePath) => {
              if (
                !jscodeshift.match(mutablePath.parent, {
                  type: jscodeshift.ObjectProperty.name,
                })
              ) {
                mutablePath.value.name = newName
              }

              return mutablePath.value
            })
        }

        const restElement = findRestElementInObjectPattern(variableDeclaratorId)

        if (restElement) {
          findIsLoadingPropertiesOfIdentifier(
            lookupNode,
            restElement.argument,
          ).replaceWith(({ node: mutableNode }) => {
            mutableNode.property.name = newName

            return mutableNode
          })
        }

        return node
      }

      if (utils.isIdentifier(variableDeclaratorId)) {
        findIsLoadingPropertiesOfIdentifier(
          lookupNode,
          variableDeclaratorId,
        ).replaceWith(({ node: mutableNode }) => {
          mutableNode.property.name = newName

          return mutableNode
        })

        return node
      }

      utils.warn(
        `The usage in file "${filePath}" at line ${start}:${end} could not be transformed. Please migrate this usage manually.`,
      )

      return node
    } catch (error) {
      utils.warn(
        `An unknown error occurred while processing the "${filePath}" file. Please review this file, because the codemod couldn't be applied.`,
      )

      return node
    }
  }

  createUseQueryLikeTransformer({ jscodeshift, utils, root }).execute(
    config.hooks,
    replacer,
  )

  createQueryClientTransformer({ jscodeshift, utils, root }).execute(
    config.queryClientMethods,
    replacer,
  )
}

module.exports = (file, api) => {
  const jscodeshift = api.jscodeshift
  const root = jscodeshift(file.source)
  const utils = createUtilsObject({ root, jscodeshift })
  const filePath = file.path

  const dependencies = { jscodeshift, utils, root, filePath }

  transformUsages({
    ...dependencies,
    config: {
      hooks: ['useQuery', 'useMutation'],
      queryClientMethods: [],
    },
  })

  return root.toSource({ quote: 'single', lineTerminator: '\n' })
}
