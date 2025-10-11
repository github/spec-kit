### Intro

The prerequisite for this code mod is to migrate your usages to the new syntax, so overloads for hooks and `QueryClient` methods shouldn't be available anymore.

### Affected usages

Please note, this code mod transforms usages only where the first argument is an object expression.

The following usage should be transformed by the code mod:

```ts
const { data } = useQuery({
  queryKey: ['posts'],
  queryFn: queryFn,
  keepPreviousData: true,
})
```

But the following usage won't be transformed by the code mod, because the first argument an identifier:

```ts
const hookArgument = {
  queryKey: ['posts'],
  queryFn: queryFn,
  keepPreviousData: true,
}
const { data } = useQuery(hookArgument)
```

### Troubleshooting

In case of any errors, feel free to reach us out via Discord or open an issue. If you open an issue, please provide a code snippet as well, because without a snippet we cannot find the bug in the code mod.
