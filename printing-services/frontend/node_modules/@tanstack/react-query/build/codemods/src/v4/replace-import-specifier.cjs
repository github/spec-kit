module.exports = (file, api) => {
  const jscodeshift = api.jscodeshift
  const root = jscodeshift(file.source)

  const replacements = [
    { from: 'react-query', to: '@tanstack/react-query' },
    { from: 'react-query/devtools', to: '@tanstack/react-query-devtools' },
  ]

  replacements.forEach(({ from, to }) => {
    root
      .find(jscodeshift.ImportDeclaration, {
        source: {
          value: from,
        },
      })
      .replaceWith(({ node }) => {
        node.source.value = to

        return node
      })
  })

  return root.toSource({ quote: 'single', lineTerminator: '\n' })
}
