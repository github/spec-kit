module.exports = ({
  jscodeshift,
  utils,
  root,
  packageName = '@tanstack/react-query',
}) => {
  const isGetQueryCacheMethodCall = (
    initializer,
    importIdentifiers,
    knownQueryClientIds,
  ) => {
    const isKnownQueryClient = (node) =>
      utils.isIdentifier(node) && knownQueryClientIds.includes(node.name)

    const isGetQueryCacheIdentifier = (node) =>
      utils.isIdentifier(node) && node.name === 'getQueryCache'

    const isValidInitializer = (node) =>
      utils.isCallExpression(node) && utils.isMemberExpression(node.callee)

    if (isValidInitializer(initializer)) {
      const instance = initializer.callee.object

      return (
        isGetQueryCacheIdentifier(initializer.callee.property) &&
        (isKnownQueryClient(instance) ||
          utils.isFunctionCallOf(
            instance,
            utils.getSelectorByImports(importIdentifiers, 'useQueryClient'),
          ))
      )
    }

    return false
  }

  const findQueryCacheInstantiations = (
    importIdentifiers,
    knownQueryClientIds,
  ) =>
    root.find(jscodeshift.VariableDeclarator, {}).filter((node) => {
      if (node.value.init) {
        const initializer = node.value.init

        return (
          utils.isClassInstantiationOf(
            initializer,
            utils.getSelectorByImports(importIdentifiers, 'QueryCache'),
          ) ||
          isGetQueryCacheMethodCall(
            initializer,
            importIdentifiers,
            knownQueryClientIds,
          )
        )
      }

      return false
    })

  const filterQueryCacheMethodCalls = (node) =>
    utils.isIdentifier(node) && ['find', 'findAll'].includes(node.name)

  const findQueryCacheMethodCalls = (importIdentifiers) => {
    /**
     * Here we collect all query client instantiations. We have to make aware of them because the query cache can be
     * accessed by the query client as well.
     */
    const queryClientIdentifiers =
      utils.queryClient.findQueryClientIdentifiers(importIdentifiers)
    /**
     * Here we collect all query cache instantiations. The reason is simple: the methods can be called on query cache
     * instances, to locate the possible usages we need to be aware of the identifier names.
     */
    const queryCacheIdentifiers = findQueryCacheInstantiations(
      importIdentifiers,
      queryClientIdentifiers,
    )
      .paths()
      .map((node) => node.value.id.name)

    return (
      utils
        // First, we need to find all method calls.
        .findAllMethodCalls()
        // Then we narrow the collection to all `fetch` and `fetchAll` methods.
        .filter((node) =>
          filterQueryCacheMethodCalls(node.value.callee.property),
        )
        .filter((node) => {
          const object = node.value.callee.object

          // If the method is called on a `QueryCache` instance, we keep it in the collection.
          if (utils.isIdentifier(object)) {
            return queryCacheIdentifiers.includes(object.name)
          }

          // If the method is called on a `QueryClient` instance, we keep it in the collection.
          if (utils.isCallExpression(object)) {
            return isGetQueryCacheMethodCall(
              object,
              importIdentifiers,
              queryClientIdentifiers,
            )
          }

          return false
        })
    )
  }

  const execute = (replacer) => {
    findQueryCacheMethodCalls(
      utils.locateImports(
        ['QueryCache', 'QueryClient', 'useQueryClient'],
        packageName,
      ),
    ).replaceWith(replacer)
  }

  return {
    execute,
  }
}
