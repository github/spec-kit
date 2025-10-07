module.exports = ({
  jscodeshift,
  utils,
  root,
  packageName = '@tanstack/react-query',
}) => {
  const filterQueryClientMethodCalls = (node, methods) =>
    utils.isIdentifier(node) && methods.includes(node.name)

  const findQueryClientMethodCalls = (importIdentifiers, methods) => {
    /**
     * Here we collect all query client instantiations. We have to make aware of them because some method calls might
     * be invoked on these instances.
     */
    const queryClientIdentifiers =
      utils.queryClient.findQueryClientIdentifiers(importIdentifiers)

    return (
      utils
        // First, we need to find all method calls.
        .findAllMethodCalls()
        // Then we narrow the collection to `QueryClient` methods.
        .filter((node) =>
          filterQueryClientMethodCalls(node.value.callee.property, methods),
        )
        .filter((node) => {
          const object = node.value.callee.object

          // If the method is called on a `QueryClient` instance, we keep it in the collection.
          if (utils.isIdentifier(object)) {
            return queryClientIdentifiers.includes(object.name)
          }

          // If the method is called on the return value of `useQueryClient` hook, we keep it in the collection.
          return utils.isFunctionCallOf(
            object,
            utils.getSelectorByImports(importIdentifiers, 'useQueryClient'),
          )
        })
    )
  }

  const execute = (methods, replacer) => {
    findQueryClientMethodCalls(
      utils.locateImports(['QueryClient', 'useQueryClient'], packageName),
      methods,
    ).replaceWith(replacer)
  }

  return {
    execute,
  }
}
