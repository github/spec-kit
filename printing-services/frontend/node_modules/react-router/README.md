# React Router

The `react-router` package is the heart of [React Router](https://github.com/remix-run/react-router) and provides all
the core functionality for both
[`react-router-dom`](https://github.com/remix-run/react-router/tree/main/packages/react-router-dom)
and
[`react-router-native`](https://github.com/remix-run/react-router/tree/main/packages/react-router-native).

If you're using React Router, you should never `import` anything directly from
the `react-router` package, but you should have everything you need in either
`react-router-dom` or `react-router-native`. Both of those packages re-export
everything from `react-router`.

If you'd like to extend React Router and you know what you're doing, you should
add `react-router` **as a peer dependency, not a regular dependency** in your
package.
