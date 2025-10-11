module.exports = ({
  jscodeshift,
  utils,
  root,
  packageName = '@tanstack/react-query',
}) => {
  const filterUseQueryLikeHookCalls = (node, importIdentifiers, hooks) => {
    for (const hook of hooks) {
      const selector = utils.getSelectorByImports(importIdentifiers, hook)

      if (utils.isFunctionCallOf(node, selector)) {
        return true
      }
    }

    return false
  }

  const findUseQueryLikeHookCalls = (importIdentifiers, hooks) =>
    root
      // First, we need to find all call expressions.
      .find(jscodeshift.CallExpression, {})
      // Then we narrow the collection to the `useQuery` like hook calls.
      .filter((node) =>
        filterUseQueryLikeHookCalls(node.value, importIdentifiers, hooks),
      )

  const execute = (hooks, replacer) => {
    findUseQueryLikeHookCalls(
      utils.locateImports(hooks, packageName),
      hooks,
    ).replaceWith(replacer)
  }

  return {
    execute,
  }
}
