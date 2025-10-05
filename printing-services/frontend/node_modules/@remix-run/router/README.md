# Remix Router

The `@remix-run/router` package is a framework-agnostic routing package (sometimes referred to as a browser-emulator) that serves as the heart of [React Router][react-router] and [Remix][remix] and provides all the core functionality for routing coupled with data loading and data mutations. It comes with built-in handling of errors, race-conditions, interruptions, cancellations, lazy-loading data, and much, much more.

If you're using React Router, you should never `import` anything directly from the `@remix-run/router` - you should have everything you need in `react-router-dom` (or `react-router`/`react-router-native` if you're not rendering in the browser). All of those packages should re-export everything you would otherwise need from `@remix-run/router`.

> [!WARNING]
>
> This router is a low-level package intended to be consumed by UI layer routing libraries. You should very likely not be using this package directly unless you are authoring a routing library such as [`react-router-dom`][react-router-repo] or one of it's other [UI ports][remix-routers-repo].

## API

A Router instance can be created using `createRouter`:

```js
// Create and initialize a router.  "initialize" contains all side effects
// including history listeners and kicking off the initial data fetch
let router = createRouter({
  // Required properties
  routes: [{
    path: '/',
    loader: ({ request, params }) => { /* ... */ },
    children: [{
      path: 'home',
      loader: ({ request, params }) => { /* ... */ },
    }]
  },
  history: createBrowserHistory(),

  // Optional properties
  basename, // Base path
  mapRouteProperties, // Map framework-agnostic routes to framework-aware routes
  future, // Future flags
  hydrationData, // Hydration data if using server-side-rendering
}).initialize();
```

Internally, the Router represents the state in an object of the following format, which is available through `router.state`. You can also register a subscriber of the signature `(state: RouterState) => void` to execute when the state updates via `router.subscribe()`;

```ts
interface RouterState {
  // False during the initial data load, true once we have our initial data
  initialized: boolean;
  // The `history` action of the most recently completed navigation
  historyAction: Action;
  // The current location of the router.  During a navigation this reflects
  // the "old" location and is updated upon completion of the navigation
  location: Location;
  // The current set of route matches
  matches: DataRouteMatch[];
  // The state of the current navigation
  navigation: Navigation;
  // The state of any in-progress router.revalidate() calls
  revalidation: RevalidationState;
  // Data from the loaders for the current matches
  loaderData: RouteData;
  // Data from the action for the current matches
  actionData: RouteData | null;
  // Errors thrown from loaders/actions for the current matches
  errors: RouteData | null;
  // Map of all active fetchers
  fetchers: Map<string, Fetcher>;
  // Scroll position to restore to for the active Location, false if we
  // should not restore, or null if we don't have a saved position
  // Note: must be enabled via router.enableScrollRestoration()
  restoreScrollPosition: number | false | null;
  // Proxied `preventScrollReset` value passed to router.navigate()
  preventScrollReset: boolean;
}
```

### Navigations

All navigations are done through the `router.navigate` API which is overloaded to support different types of navigations:

```js
// Link navigation (pushes onto the history stack by default)
router.navigate("/page");

// Link navigation (replacing the history stack)
router.navigate("/page", { replace: true });

// Pop navigation (moving backward/forward in the history stack)
router.navigate(-1);

// Form submission navigation
let formData = new FormData();
formData.append(key, value);
router.navigate("/page", {
  formMethod: "post",
  formData,
});

// Relative routing from a source routeId
router.navigate("../../somewhere", {
  fromRouteId: "active-route-id",
});
```

### Fetchers

Fetchers are a mechanism to call loaders/actions without triggering a navigation, and are done through the `router.fetch()` API. All fetch calls require a unique key to identify the fetcher.

```js
// Execute the loader for /page
router.fetch("key", "/page");

// Submit to the action for /page
let formData = new FormData();
formData.append(key, value);
router.fetch("key", "/page", {
  formMethod: "post",
  formData,
});
```

### Revalidation

By default, active loaders will revalidate after any navigation or fetcher mutation. If you need to kick off a revalidation for other use-cases, you can use `router.revalidate()` to re-execute all active loaders.

### Future Flags

We use _Future Flags_ in the router to help us introduce breaking changes in an opt-in fashion ahead of major releases. Please check out the [blog post][future-flags-post] and [React Router Docs][api-development-strategy] for more information on this process. The currently available future flags in `@remix-run/router` are:

| Flag                     | Description                                                               |
| ------------------------ | ------------------------------------------------------------------------- |
| `v7_normalizeFormMethod` | Normalize `useNavigation().formMethod` to be an uppercase HTTP Method     |
| `v7_prependBasename`     | Prepend the `basename` to incoming `router.navigate`/`router.fetch` paths |

[react-router]: https://reactrouter.com
[remix]: https://remix.run
[react-router-repo]: https://github.com/remix-run/react-router
[remix-routers-repo]: https://github.com/brophdawg11/remix-routers
[api-development-strategy]: https://reactrouter.com/v6/guides/api-development-strategy
[future-flags-post]: https://remix.run/blog/future-flags
