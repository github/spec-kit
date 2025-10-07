const createUtilsObject = require('../utils/index.cjs')
const createKeyReplacer = require('./utils/replacers/key-replacer.cjs')
const createUseQueryLikeTransformer = require('../utils/transformers/use-query-like-transformer.cjs')
const createQueryClientTransformer = require('../utils/transformers/query-client-transformer.cjs')
const createQueryCacheTransformer = require('../utils/transformers/query-cache-transformer.cjs')

const transformQueryClientUsages = ({
  jscodeshift,
  utils,
  root,
  filePath,
  packageName,
}) => {
  const transformer = createQueryClientTransformer({
    jscodeshift,
    utils,
    root,
    packageName,
  })
  const replacer = createKeyReplacer({ jscodeshift, root, filePath })

  transformer.execute(
    [
      // Not object syntax-aware methods.
      'getMutationDefaults',
      'getQueriesData',
      'getQueryData',
      'getQueryDefaults',
      'getQueryState',
      'isFetching',
      'setMutationDefaults',
      'setQueriesData',
      'setQueryData',
      'setQueryDefaults',
      // Object syntax-aware methods.
      'cancelQueries',
      'fetchInfiniteQuery',
      'fetchQuery',
      'invalidateQueries',
      'prefetchInfiniteQuery',
      'prefetchQuery',
      'refetchQueries',
      'removeQueries',
      'resetQueries',
    ],
    replacer,
  )
}

const transformUseQueriesUsages = ({
  jscodeshift,
  utils,
  root,
  packageName,
}) => {
  const transformer = createUseQueryLikeTransformer({
    jscodeshift,
    utils,
    root,
    packageName,
  })
  const replacer = ({ node }) => {
    /**
     * When the node doesn't have the 'original' property, that means the codemod has been already applied,
     * so we don't need to do any changes.
     */
    if (!node.original) {
      return node
    }

    const newCallExpression = jscodeshift.callExpression(node.original.callee, [
      jscodeshift.objectExpression([
        jscodeshift.property(
          'init',
          jscodeshift.identifier('queries'),
          node.original.arguments[0],
        ),
      ]),
    ])

    // TODO: This should be part of one function!
    if (node.typeParameters) {
      newCallExpression.typeArguments = node.typeParameters
    }

    return newCallExpression
  }

  transformer.execute(['useQueries'], replacer)
}

const transformUseQueryLikeUsages = ({
  jscodeshift,
  utils,
  root,
  filePath,
  packageName,
}) => {
  const transformer = createUseQueryLikeTransformer({
    jscodeshift,
    utils,
    root,
    packageName,
  })

  transformer.execute(
    ['useQuery', 'useInfiniteQuery', 'useIsFetching', 'useIsMutating'],
    createKeyReplacer({
      jscodeshift,
      root,
      filePath,
      keyName: 'queryKey',
    }),
  )
  transformer.execute(
    ['useMutation'],
    createKeyReplacer({
      jscodeshift,
      root,
      filePath,
      keyName: 'mutationKey',
    }),
  )
}

const transformQueryCacheUsages = ({
  jscodeshift,
  utils,
  root,
  filePath,
  packageName,
}) => {
  const transformer = createQueryCacheTransformer({
    jscodeshift,
    utils,
    root,
    packageName,
  })
  const replacer = createKeyReplacer({ jscodeshift, root, filePath })

  transformer.execute(replacer)
}

module.exports = (file, api) => {
  const jscodeshift = api.jscodeshift
  const root = jscodeshift(file.source)

  // TODO: Execute the transformers only when it contains a `react-query` import!

  const utils = createUtilsObject({ root, jscodeshift })
  const filePath = file.path
  const packageName = 'react-query'

  // This function transforms usages like `useQuery` and `useMutation`.
  transformUseQueryLikeUsages({
    jscodeshift,
    utils,
    root,
    filePath,
    packageName,
  })
  // This function transforms usages of `useQueries`.
  transformUseQueriesUsages({
    jscodeshift,
    utils,
    root,
    packageName,
  })
  // This function transforms usages of `QueryClient`.
  transformQueryClientUsages({
    jscodeshift,
    utils,
    root,
    filePath,
    packageName,
  })
  // This function transforms usages of `QueryCache`.
  transformQueryCacheUsages({ jscodeshift, utils, root, filePath, packageName })

  return root.toSource({ quote: 'single', lineTerminator: '\n' })
}
