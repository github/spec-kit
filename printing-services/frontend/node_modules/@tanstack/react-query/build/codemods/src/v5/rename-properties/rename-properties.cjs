module.exports = (file, api) => {
  const jscodeshift = api.jscodeshift
  const root = jscodeshift(file.source)

  const baseRenameLogic = (kind, from, to) => {
    root
      .find(kind, (node) => {
        return (
          node.computed === false &&
          (node.key?.name === from || node.key?.value === from)
        )
      })
      .replaceWith(({ node: mutableNode }) => {
        if (mutableNode.key.name !== undefined) {
          mutableNode.key.name = to
        }

        if (mutableNode.key.value !== undefined) {
          mutableNode.key.value = to
        }

        return mutableNode
      })
  }

  const renameObjectProperty = (from, to) => {
    baseRenameLogic(jscodeshift.ObjectProperty, from, to)
  }

  const renameTypeScriptPropertySignature = (from, to) => {
    baseRenameLogic(jscodeshift.TSPropertySignature, from, to)
  }

  renameObjectProperty('cacheTime', 'gcTime')
  renameObjectProperty('useErrorBoundary', 'throwOnError')

  renameTypeScriptPropertySignature('cacheTime', 'gcTime')
  renameTypeScriptPropertySignature('useErrorBoundary', 'throwOnError')

  return root.toSource({ quote: 'single', lineTerminator: '\n' })
}
