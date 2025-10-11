module.exports = (file, api) => {
  const jscodeshift = api.jscodeshift
  const root = jscodeshift(file.source)

  const importSpecifiers = root
    .find(jscodeshift.ImportDeclaration, {
      source: {
        value: '@tanstack/react-query',
      },
    })
    .find(jscodeshift.ImportSpecifier, {
      imported: {
        name: 'Hydrate',
      },
    })

  if (importSpecifiers.length > 0) {
    const names = {
      searched: 'Hydrate', // By default, we want to replace the `Hydrate` usages.
      target: 'HydrationBoundary', // We want to replace them with `HydrationBoundary`.
    }

    importSpecifiers.replaceWith(({ node: mutableNode }) => {
      /**
       * When the local and imported names match which means the code doesn't contain import aliases, we need
       * to replace only the import specifier.
       * @type {boolean}
       */
      const usesDefaultImport =
        mutableNode.local.name === mutableNode.imported.name

      if (!usesDefaultImport) {
        // If the code uses import aliases, we must re-use the alias.
        names.searched = mutableNode.local.name
        names.target = mutableNode.local.name
      }

      // Override the import specifier.
      mutableNode.imported.name = 'HydrationBoundary'

      return mutableNode
    })

    root
      .findJSXElements(names.searched)
      .replaceWith(({ node: mutableNode }) => {
        mutableNode.openingElement.name.name = names.target
        mutableNode.closingElement.name.name = names.target

        return mutableNode
      })
  }

  return root.toSource({ quote: 'single', lineTerminator: '\n' })
}
