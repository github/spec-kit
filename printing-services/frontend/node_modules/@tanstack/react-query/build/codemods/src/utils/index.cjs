module.exports = ({ root, jscodeshift }) => {
  const findImportIdentifierOf = (importSpecifiers, identifier) => {
    const specifier = importSpecifiers
      .filter((node) => node.value.imported.name === identifier)
      .paths()

    if (specifier.length > 0) {
      return specifier[0].value.local
    }

    return jscodeshift.identifier(identifier)
  }

  const findImportSpecifiers = (packageName) =>
    root
      .find(jscodeshift.ImportDeclaration, {
        source: {
          value: packageName,
        },
      })
      .find(jscodeshift.ImportSpecifier, {})

  const locateImports = (
    identifiers,
    packageName = '@tanstack/react-query',
  ) => {
    const findNamespaceImportIdentifier = () => {
      const specifier = root
        .find(jscodeshift.ImportDeclaration, {
          source: {
            value: packageName,
          },
        })
        .find(jscodeshift.ImportNamespaceSpecifier)
        .paths()

      return specifier.length > 0 ? specifier[0].value.local : null
    }

    /**
     * First, we search for the namespace import identifier because if we have any, we assume the consumer uses
     * namespace imports. In this case, we won't search for named imports at all.
     */
    const namespaceImportIdentifier = findNamespaceImportIdentifier()

    if (namespaceImportIdentifier) {
      const identifierMap = {}

      for (const identifier of identifiers) {
        identifierMap[identifier] = jscodeshift.identifier(identifier)
      }

      return {
        namespace: namespaceImportIdentifier,
        ...identifierMap,
      }
    }

    const importSpecifiers = findImportSpecifiers(packageName)
    const identifierMap = {}

    for (const identifier of identifiers) {
      identifierMap[identifier] = findImportIdentifierOf(
        importSpecifiers,
        identifier,
      )
    }

    return {
      namespace: null,
      ...identifierMap,
    }
  }

  const findAllMethodCalls = () =>
    root
      // First, we need to find all method calls.
      .find(jscodeshift.CallExpression, {
        callee: {
          type: jscodeshift.MemberExpression.name,
          property: {
            type: jscodeshift.Identifier.name,
          },
        },
      })

  const findQueryClientIdentifiers = (importIdentifiers) =>
    root
      .find(jscodeshift.VariableDeclarator, {})
      .filter((node) => {
        if (node.value.init) {
          const initializer = node.value.init

          return (
            isClassInstantiationOf(
              initializer,
              getSelectorByImports(importIdentifiers, 'QueryClient'),
            ) ||
            isFunctionCallOf(
              initializer,
              getSelectorByImports(importIdentifiers, 'useQueryClient'),
            )
          )
        }

        return false
      })
      .paths()
      .map((node) => node.value.id.name)

  const isCallExpression = (node) =>
    jscodeshift.match(node, { type: jscodeshift.CallExpression.name })

  const isIdentifier = (node) =>
    jscodeshift.match(node, { type: jscodeshift.Identifier.name })

  const isMemberExpression = (node) =>
    jscodeshift.match(node, { type: jscodeshift.MemberExpression.name })

  const isNewExpression = (node) =>
    jscodeshift.match(node, { type: jscodeshift.NewExpression.name })

  const isArrayExpression = (node) =>
    jscodeshift.match(node, { type: jscodeshift.ArrayExpression.name })

  const isObjectExpression = (node) =>
    jscodeshift.match(node, { type: jscodeshift.ObjectExpression.name })

  const isObjectProperty = (node) =>
    jscodeshift.match(node, { type: jscodeshift.ObjectProperty.name })

  const isSpreadElement = (node) =>
    jscodeshift.match(node, { type: jscodeshift.SpreadElement.name })

  /**
   * @param {import('jscodeshift').Node} node
   * @returns {boolean}
   */
  const isFunctionDefinition = (node) => {
    const isArrowFunctionExpression = jscodeshift.match(node, {
      type: jscodeshift.ArrowFunctionExpression.name,
    })
    const isFunctionExpression = jscodeshift.match(node, {
      type: jscodeshift.FunctionExpression.name,
    })

    return isArrowFunctionExpression || isFunctionExpression
  }

  const warn = (message) => {
    if (process.env.NODE_ENV !== 'test') {
      console.warn(message)
    }
  }

  const isClassInstantiationOf = (node, selector) => {
    if (!isNewExpression(node)) {
      return false
    }

    const parts = selector.split('.')

    return parts.length === 1
      ? isIdentifier(node.callee) && node.callee.name === parts[0]
      : isMemberExpression(node.callee) &&
          node.callee.object.name === parts[0] &&
          node.callee.property.name === parts[1]
  }

  const isFunctionCallOf = (node, selector) => {
    if (!isCallExpression(node)) {
      return false
    }

    const parts = selector.split('.')

    return parts.length === 1
      ? isIdentifier(node.callee) && node.callee.name === parts[0]
      : isMemberExpression(node.callee) &&
          node.callee.object.name === parts[0] &&
          node.callee.property.name === parts[1]
  }

  const getSelectorByImports = (imports, path) =>
    imports.namespace
      ? `${imports.namespace.name}.${imports[path].name}`
      : imports[path].name

  return {
    findAllMethodCalls,
    getSelectorByImports,
    isCallExpression,
    isClassInstantiationOf,
    isFunctionCallOf,
    isIdentifier,
    isMemberExpression,
    isArrayExpression,
    isObjectExpression,
    isObjectProperty,
    isSpreadElement,
    isFunctionDefinition,
    locateImports,
    warn,
    queryClient: {
      findQueryClientIdentifiers,
    },
  }
}
