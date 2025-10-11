# `react-router`

## 6.30.1

### Patch Changes

- Partially revert optimization added in `6.29.0` to reduce calls to `matchRoutes` because it surfaced other issues ([#13623](https://github.com/remix-run/react-router/pull/13623))
- Stop logging invalid warning when `v7_relativeSplatPath` is set to false ([#13502](https://github.com/remix-run/react-router/pull/13502))

## 6.30.0

### Minor Changes

- Add `fetcherKey` as a parameter to `patchRoutesOnNavigation` ([#13109](https://github.com/remix-run/react-router/pull/13109))

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.23.0`

## 6.29.0

### Minor Changes

- Provide the request `signal` as a parameter to `patchRoutesOnNavigation` ([#12900](https://github.com/remix-run/react-router/pull/12900))

  - This can be used to abort any manifest fetches if the in-flight navigation/fetcher is aborted

### Patch Changes

- Do not log v7 deprecation warnings in production builds ([#12794](https://github.com/remix-run/react-router/pull/12794))
- Limit matchRoutes optimization to client side routers ([#12881](https://github.com/remix-run/react-router/pull/12881))
- Optimize route matching by skipping redundant `matchRoutes` calls when possible ([#12169](https://github.com/remix-run/react-router/pull/12169))
- Updated dependencies:
  - `@remix-run/router@1.22.0`

## 6.28.2

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.21.1`

## 6.28.1

### Patch Changes

- Allow users to opt out of deprecation warnings by setting flags to false ([#12441](https://github.com/remix-run/react-router/pull/12441))

## 6.28.0

### Minor Changes

- Log deprecation warnings for v7 flags ([#11750](https://github.com/remix-run/react-router/pull/11750))
  - Add deprecation warnings to `json`/`defer` in favor of returning raw objects
    - These methods will be removed in React Router v7

### Patch Changes

- Update JSDoc URLs for new website structure (add /v6/ segment) ([#12141](https://github.com/remix-run/react-router/pull/12141))
- Updated dependencies:
  - `@remix-run/router@1.21.0`

## 6.27.0

### Minor Changes

- Stabilize `unstable_patchRoutesOnNavigation` ([#11973](https://github.com/remix-run/react-router/pull/11973))
  - Add new `PatchRoutesOnNavigationFunctionArgs` type for convenience ([#11967](https://github.com/remix-run/react-router/pull/11967))
- Stabilize `unstable_dataStrategy` ([#11974](https://github.com/remix-run/react-router/pull/11974))
- Stabilize the `unstable_flushSync` option for navigations and fetchers ([#11989](https://github.com/remix-run/react-router/pull/11989))
- Stabilize the `unstable_viewTransition` option for navigations and the corresponding `unstable_useViewTransitionState` hook ([#11989](https://github.com/remix-run/react-router/pull/11989))

### Patch Changes

- Fix bug when submitting to the current contextual route (parent route with an index child) when an `?index` param already exists from a prior submission ([#12003](https://github.com/remix-run/react-router/pull/12003))

- Fix `useFormAction` bug - when removing `?index` param it would not keep other non-Remix `index` params ([#12003](https://github.com/remix-run/react-router/pull/12003))

- Fix types for `RouteObject` within `PatchRoutesOnNavigationFunction`'s `patch` method so it doesn't expect agnostic route objects passed to `patch` ([#11967](https://github.com/remix-run/react-router/pull/11967))

- Updated dependencies:
  - `@remix-run/router@1.20.0`

## 6.26.2

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.19.2`

## 6.26.1

### Patch Changes

- Rename `unstable_patchRoutesOnMiss` to `unstable_patchRoutesOnNavigation` to match new behavior ([#11888](https://github.com/remix-run/react-router/pull/11888))
- Updated dependencies:
  - `@remix-run/router@1.19.1`

## 6.26.0

### Minor Changes

- Add a new `replace(url, init?)` alternative to `redirect(url, init?)` that performs a `history.replaceState` instead of a `history.pushState` on client-side navigation redirects ([#11811](https://github.com/remix-run/react-router/pull/11811))

### Patch Changes

- Fix initial hydration behavior when using `future.v7_partialHydration` along with `unstable_patchRoutesOnMiss` ([#11838](https://github.com/remix-run/react-router/pull/11838))
  - During initial hydration, `router.state.matches` will now include any partial matches so that we can render ancestor `HydrateFallback` components
- Updated dependencies:
  - `@remix-run/router@1.19.0`

## 6.25.1

No significant changes to this package were made in this release. [See the repo `CHANGELOG.md`](https://github.com/remix-run/react-router/blob/main/CHANGELOG.md) for an overview of all changes in v6.25.1.

## 6.25.0

### Minor Changes

- Stabilize `future.unstable_skipActionErrorRevalidation` as `future.v7_skipActionErrorRevalidation` ([#11769](https://github.com/remix-run/react-router/pull/11769))
  - When this flag is enabled, actions will not automatically trigger a revalidation if they return/throw a `Response` with a `4xx`/`5xx` status code
  - You may still opt-into revalidation via `shouldRevalidate`
  - This also changes `shouldRevalidate`'s `unstable_actionStatus` parameter to `actionStatus`

### Patch Changes

- Fix regression and properly decode paths inside `useMatch` so matches/params reflect decoded params ([#11789](https://github.com/remix-run/react-router/pull/11789))
- Updated dependencies:
  - `@remix-run/router@1.18.0`

## 6.24.1

### Patch Changes

- When using `future.v7_relativeSplatPath`, properly resolve relative paths in splat routes that are children of pathless routes ([#11633](https://github.com/remix-run/react-router/pull/11633))
- Updated dependencies:
  - `@remix-run/router@1.17.1`

## 6.24.0

### Minor Changes

- Add support for Lazy Route Discovery (a.k.a. Fog of War) ([#11626](https://github.com/remix-run/react-router/pull/11626))
  - RFC: <https://github.com/remix-run/react-router/discussions/11113>
  - `unstable_patchRoutesOnMiss` docs: <https://reactrouter.com/v6/routers/create-browser-router>

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.17.0`

## 6.23.1

### Patch Changes

- allow undefined to be resolved with `<Await>` ([#11513](https://github.com/remix-run/react-router/pull/11513))
- Updated dependencies:
  - `@remix-run/router@1.16.1`

## 6.23.0

### Minor Changes

- Add a new `unstable_dataStrategy` configuration option ([#11098](https://github.com/remix-run/react-router/pull/11098))
  - This option allows Data Router applications to take control over the approach for executing route loaders and actions
  - The default implementation is today's behavior, to fetch all loaders in parallel, but this option allows users to implement more advanced data flows including Remix single-fetch, middleware/context APIs, automatic loader caching, and more

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.16.0`

## 6.22.3

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.15.3`

## 6.22.2

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.15.2`

## 6.22.1

### Patch Changes

- Fix encoding/decoding issues with pre-encoded dynamic parameter values ([#11199](https://github.com/remix-run/react-router/pull/11199))
- Updated dependencies:
  - `@remix-run/router@1.15.1`

## 6.22.0

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.15.0`

## 6.21.3

### Patch Changes

- Remove leftover `unstable_` prefix from `Blocker`/`BlockerFunction` types ([#11187](https://github.com/remix-run/react-router/pull/11187))

## 6.21.2

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.14.2`

## 6.21.1

### Patch Changes

- Fix bug with `route.lazy` not working correctly on initial SPA load when `v7_partialHydration` is specified ([#11121](https://github.com/remix-run/react-router/pull/11121))
- Updated dependencies:
  - `@remix-run/router@1.14.1`

## 6.21.0

### Minor Changes

- Add a new `future.v7_relativeSplatPath` flag to implement a breaking bug fix to relative routing when inside a splat route. ([#11087](https://github.com/remix-run/react-router/pull/11087))

  This fix was originally added in [#10983](https://github.com/remix-run/react-router/issues/10983) and was later reverted in [#11078](https://github.com/remix-run/react-router/pull/11078) because it was determined that a large number of existing applications were relying on the buggy behavior (see [#11052](https://github.com/remix-run/react-router/issues/11052))

  **The Bug**
  The buggy behavior is that without this flag, the default behavior when resolving relative paths is to _ignore_ any splat (`*`) portion of the current route path.

  **The Background**
  This decision was originally made thinking that it would make the concept of nested different sections of your apps in `<Routes>` easier if relative routing would _replace_ the current splat:

  ```jsx
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="dashboard/*" element={<Dashboard />} />
    </Routes>
  </BrowserRouter>
  ```

  Any paths like `/dashboard`, `/dashboard/team`, `/dashboard/projects` will match the `Dashboard` route. The dashboard component itself can then render nested `<Routes>`:

  ```jsx
  function Dashboard() {
    return (
      <div>
        <h2>Dashboard</h2>
        <nav>
          <Link to="/">Dashboard Home</Link>
          <Link to="team">Team</Link>
          <Link to="projects">Projects</Link>
        </nav>

        <Routes>
          <Route path="/" element={<DashboardHome />} />
          <Route path="team" element={<DashboardTeam />} />
          <Route path="projects" element={<DashboardProjects />} />
        </Routes>
      </div>
    );
  }
  ```

  Now, all links and route paths are relative to the router above them. This makes code splitting and compartmentalizing your app really easy. You could render the `Dashboard` as its own independent app, or embed it into your large app without making any changes to it.

  **The Problem**

  The problem is that this concept of ignoring part of a path breaks a lot of other assumptions in React Router - namely that `"."` always means the current location pathname for that route. When we ignore the splat portion, we start getting invalid paths when using `"."`:

  ```jsx
  // If we are on URL /dashboard/team, and we want to link to /dashboard/team:
  function DashboardTeam() {
    // ❌ This is broken and results in <a href="/dashboard">
    return <Link to=".">A broken link to the Current URL</Link>;

    // ✅ This is fixed but super unintuitive since we're already at /dashboard/team!
    return <Link to="./team">A broken link to the Current URL</Link>;
  }
  ```

  We've also introduced an issue that we can no longer move our `DashboardTeam` component around our route hierarchy easily - since it behaves differently if we're underneath a non-splat route, such as `/dashboard/:widget`. Now, our `"."` links will, properly point to ourself _inclusive of the dynamic param value_ so behavior will break from it's corresponding usage in a `/dashboard/*` route.

  Even worse, consider a nested splat route configuration:

  ```jsx
  <BrowserRouter>
    <Routes>
      <Route path="dashboard">
        <Route path="*" element={<Dashboard />} />
      </Route>
    </Routes>
  </BrowserRouter>
  ```

  Now, a `<Link to=".">` and a `<Link to="..">` inside the `Dashboard` component go to the same place! That is definitely not correct!

  Another common issue arose in Data Routers (and Remix) where any `<Form>` should post to it's own route `action` if you the user doesn't specify a form action:

  ```jsx
  let router = createBrowserRouter({
    path: "/dashboard",
    children: [
      {
        path: "*",
        action: dashboardAction,
        Component() {
          // ❌ This form is broken!  It throws a 405 error when it submits because
          // it tries to submit to /dashboard (without the splat value) and the parent
          // `/dashboard` route doesn't have an action
          return <Form method="post">...</Form>;
        },
      },
    ],
  });
  ```

  This is just a compounded issue from the above because the default location for a `Form` to submit to is itself (`"."`) - and if we ignore the splat portion, that now resolves to the parent route.

  **The Solution**
  If you are leveraging this behavior, it's recommended to enable the future flag, move your splat to it's own route, and leverage `../` for any links to "sibling" pages:

  ```jsx
  <BrowserRouter>
    <Routes>
      <Route path="dashboard">
        <Route index path="*" element={<Dashboard />} />
      </Route>
    </Routes>
  </BrowserRouter>

  function Dashboard() {
    return (
      <div>
        <h2>Dashboard</h2>
        <nav>
          <Link to="..">Dashboard Home</Link>
          <Link to="../team">Team</Link>
          <Link to="../projects">Projects</Link>
        </nav>

        <Routes>
          <Route path="/" element={<DashboardHome />} />
          <Route path="team" element={<DashboardTeam />} />
          <Route path="projects" element={<DashboardProjects />} />
        </Router>
      </div>
    );
  }
  ```

  This way, `.` means "the full current pathname for my route" in all cases (including static, dynamic, and splat routes) and `..` always means "my parents pathname".

### Patch Changes

- Properly handle falsy error values in ErrorBoundary's ([#11071](https://github.com/remix-run/react-router/pull/11071))
- Updated dependencies:
  - `@remix-run/router@1.14.0`

## 6.20.1

### Patch Changes

- Revert the `useResolvedPath` fix for splat routes due to a large number of applications that were relying on the buggy behavior (see <https://github.com/remix-run/react-router/issues/11052#issuecomment-1836589329>). We plan to re-introduce this fix behind a future flag in the next minor version. ([#11078](https://github.com/remix-run/react-router/pull/11078))
- Updated dependencies:
  - `@remix-run/router@1.13.1`

## 6.20.0

### Minor Changes

- Export the `PathParam` type from the public API ([#10719](https://github.com/remix-run/react-router/pull/10719))

### Patch Changes

- Fix bug with `resolveTo` in splat routes ([#11045](https://github.com/remix-run/react-router/pull/11045))
  - This is a follow up to [#10983](https://github.com/remix-run/react-router/pull/10983) to handle the few other code paths using `getPathContributingMatches`
  - This removes the `UNSAFE_getPathContributingMatches` export from `@remix-run/router` since we no longer need this in the `react-router`/`react-router-dom` layers
- Updated dependencies:
  - `@remix-run/router@1.13.0`

## 6.19.0

### Minor Changes

- Add `unstable_flushSync` option to `useNavigate`/`useSumbit`/`fetcher.load`/`fetcher.submit` to opt-out of `React.startTransition` and into `ReactDOM.flushSync` for state updates ([#11005](https://github.com/remix-run/react-router/pull/11005))
- Remove the `unstable_` prefix from the [`useBlocker`](https://reactrouter.com/v6/hooks/use-blocker) hook as it's been in use for enough time that we are confident in the API. We do not plan to remove the prefix from `unstable_usePrompt` due to differences in how browsers handle `window.confirm` that prevent React Router from guaranteeing consistent/correct behavior. ([#10991](https://github.com/remix-run/react-router/pull/10991))

### Patch Changes

- Fix `useActionData` so it returns proper contextual action data and not _any_ action data in the tree ([#11023](https://github.com/remix-run/react-router/pull/11023))

- Fix bug in `useResolvedPath` that would cause `useResolvedPath(".")` in a splat route to lose the splat portion of the URL path. ([#10983](https://github.com/remix-run/react-router/pull/10983))

  - ⚠️ This fixes a quite long-standing bug specifically for `"."` paths inside a splat route which incorrectly dropped the splat portion of the URL. If you are relative routing via `"."` inside a splat route in your application you should double check that your logic is not relying on this buggy behavior and update accordingly.

- Updated dependencies:
  - `@remix-run/router@1.12.0`

## 6.18.0

### Patch Changes

- Fix the `future` prop on `BrowserRouter`, `HashRouter` and `MemoryRouter` so that it accepts a `Partial<FutureConfig>` instead of requiring all flags to be included. ([#10962](https://github.com/remix-run/react-router/pull/10962))
- Updated dependencies:
  - `@remix-run/router@1.11.0`

## 6.17.0

### Patch Changes

- Fix `RouterProvider` `future` prop type to be a `Partial<FutureConfig>` so that not all flags must be specified ([#10900](https://github.com/remix-run/react-router/pull/10900))
- Updated dependencies:
  - `@remix-run/router@1.10.0`

## 6.16.0

### Minor Changes

- In order to move towards stricter TypeScript support in the future, we're aiming to replace current usages of `any` with `unknown` on exposed typings for user-provided data. To do this in Remix v2 without introducing breaking changes in React Router v6, we have added generics to a number of shared types. These continue to default to `any` in React Router and are overridden with `unknown` in Remix. In React Router v7 we plan to move these to `unknown` as a breaking change. ([#10843](https://github.com/remix-run/react-router/pull/10843))
  - `Location` now accepts a generic for the `location.state` value
  - `ActionFunctionArgs`/`ActionFunction`/`LoaderFunctionArgs`/`LoaderFunction` now accept a generic for the `context` parameter (only used in SSR usages via `createStaticHandler`)
  - The return type of `useMatches` (now exported as `UIMatch`) accepts generics for `match.data` and `match.handle` - both of which were already set to `unknown`
- Move the `@private` class export `ErrorResponse` to an `UNSAFE_ErrorResponseImpl` export since it is an implementation detail and there should be no construction of `ErrorResponse` instances in userland. This frees us up to export a `type ErrorResponse` which correlates to an instance of the class via `InstanceType`. Userland code should only ever be using `ErrorResponse` as a type and should be type-narrowing via `isRouteErrorResponse`. ([#10811](https://github.com/remix-run/react-router/pull/10811))
- Export `ShouldRevalidateFunctionArgs` interface ([#10797](https://github.com/remix-run/react-router/pull/10797))
- Removed private/internal APIs only required for the Remix v1 backwards compatibility layer and no longer needed in Remix v2 (`_isFetchActionRedirect`, `_hasFetcherDoneAnything`) ([#10715](https://github.com/remix-run/react-router/pull/10715))

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.9.0`

## 6.15.0

### Minor Changes

- Add's a new `redirectDocument()` function which allows users to specify that a redirect from a `loader`/`action` should trigger a document reload (via `window.location`) instead of attempting to navigate to the redirected location via React Router ([#10705](https://github.com/remix-run/react-router/pull/10705))

### Patch Changes

- Ensure `useRevalidator` is referentially stable across re-renders if revalidations are not actively occurring ([#10707](https://github.com/remix-run/react-router/pull/10707))
- Updated dependencies:
  - `@remix-run/router@1.8.0`

## 6.14.2

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.7.2`

## 6.14.1

### Patch Changes

- Fix loop in `unstable_useBlocker` when used with an unstable blocker function ([#10652](https://github.com/remix-run/react-router/pull/10652))
- Fix issues with reused blockers on subsequent navigations ([#10656](https://github.com/remix-run/react-router/pull/10656))
- Updated dependencies:
  - `@remix-run/router@1.7.1`

## 6.14.0

### Patch Changes

- Strip `basename` from locations provided to `unstable_useBlocker` functions to match `useLocation` ([#10573](https://github.com/remix-run/react-router/pull/10573))
- Fix `generatePath` when passed a numeric `0` value parameter ([#10612](https://github.com/remix-run/react-router/pull/10612))
- Fix `unstable_useBlocker` key issues in `StrictMode` ([#10573](https://github.com/remix-run/react-router/pull/10573))
- Fix `tsc --skipLibCheck:false` issues on React 17 ([#10622](https://github.com/remix-run/react-router/pull/10622))
- Upgrade `typescript` to 5.1 ([#10581](https://github.com/remix-run/react-router/pull/10581))
- Updated dependencies:
  - `@remix-run/router@1.7.0`

## 6.13.0

### Minor Changes

- Move [`React.startTransition`](https://react.dev/reference/react/startTransition) usage behind a [future flag](https://reactrouter.com/v6/guides/api-development-strategy) to avoid issues with existing incompatible `Suspense` usages. We recommend folks adopting this flag to be better compatible with React concurrent mode, but if you run into issues you can continue without the use of `startTransition` until v7. Issues usually boils down to creating net-new promises during the render cycle, so if you run into issues you should either lift your promise creation out of the render cycle or put it behind a `useMemo`. ([#10596](https://github.com/remix-run/react-router/pull/10596))

  Existing behavior will no longer include `React.startTransition`:

  ```jsx
  <BrowserRouter>
    <Routes>{/*...*/}</Routes>
  </BrowserRouter>

  <RouterProvider router={router} />
  ```

  If you wish to enable `React.startTransition`, pass the future flag to your component:

  ```jsx
  <BrowserRouter future={{ v7_startTransition: true }}>
    <Routes>{/*...*/}</Routes>
  </BrowserRouter>

  <RouterProvider router={router} future={{ v7_startTransition: true }}/>
  ```

### Patch Changes

- Work around webpack/terser `React.startTransition` minification bug in production mode ([#10588](https://github.com/remix-run/react-router/pull/10588))

## 6.12.1

> \[!WARNING]
> Please use version `6.13.0` or later instead of `6.12.1`. This version suffers from a `webpack`/`terser` minification issue resulting in invalid minified code in your resulting production bundles which can cause issues in your application. See [#10579](https://github.com/remix-run/react-router/issues/10579) for more details.

### Patch Changes

- Adjust feature detection of `React.startTransition` to fix webpack + react 17 compilation error ([#10569](https://github.com/remix-run/react-router/pull/10569))

## 6.12.0

### Minor Changes

- Wrap internal router state updates with `React.startTransition` if it exists ([#10438](https://github.com/remix-run/react-router/pull/10438))

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.6.3`

## 6.11.2

### Patch Changes

- Fix `basename` duplication in descendant `<Routes>` inside a `<RouterProvider>` ([#10492](https://github.com/remix-run/react-router/pull/10492))
- Updated dependencies:
  - `@remix-run/router@1.6.2`

## 6.11.1

### Patch Changes

- Fix usage of `Component` API within descendant `<Routes>` ([#10434](https://github.com/remix-run/react-router/pull/10434))
- Fix bug when calling `useNavigate` from `<Routes>` inside a `<RouterProvider>` ([#10432](https://github.com/remix-run/react-router/pull/10432))
- Fix usage of `<Navigate>` in strict mode when using a data router ([#10435](https://github.com/remix-run/react-router/pull/10435))
- Updated dependencies:
  - `@remix-run/router@1.6.1`

## 6.11.0

### Patch Changes

- Log loader/action errors to the console in dev for easier stack trace evaluation ([#10286](https://github.com/remix-run/react-router/pull/10286))
- Fix bug preventing rendering of descendant `<Routes>` when `RouterProvider` errors existed ([#10374](https://github.com/remix-run/react-router/pull/10374))
- Fix inadvertent re-renders when using `Component` instead of `element` on a route definition ([#10287](https://github.com/remix-run/react-router/pull/10287))
- Fix detection of `useNavigate` in the render cycle by setting the `activeRef` in a layout effect, allowing the `navigate` function to be passed to child components and called in a `useEffect` there. ([#10394](https://github.com/remix-run/react-router/pull/10394))
- Switched from `useSyncExternalStore` to `useState` for internal `@remix-run/router` router state syncing in `<RouterProvider>`. We found some [subtle bugs](https://codesandbox.io/s/use-sync-external-store-loop-9g7b81) where router state updates got propagated _before_ other normal `useState` updates, which could lead to footguns in `useEffect` calls. ([#10377](https://github.com/remix-run/react-router/pull/10377), [#10409](https://github.com/remix-run/react-router/pull/10409))
- Allow `useRevalidator()` to resolve a loader-driven error boundary scenario ([#10369](https://github.com/remix-run/react-router/pull/10369))
- Avoid unnecessary unsubscribe/resubscribes on router state changes ([#10409](https://github.com/remix-run/react-router/pull/10409))
- When using a `RouterProvider`, `useNavigate`/`useSubmit`/`fetcher.submit` are now stable across location changes, since we can handle relative routing via the `@remix-run/router` instance and get rid of our dependence on `useLocation()`. When using `BrowserRouter`, these hooks remain unstable across location changes because they still rely on `useLocation()`. ([#10336](https://github.com/remix-run/react-router/pull/10336))
- Updated dependencies:
  - `@remix-run/router@1.6.0`

## 6.10.0

### Minor Changes

- Added support for [**Future Flags**](https://reactrouter.com/v6/guides/api-development-strategy) in React Router. The first flag being introduced is `future.v7_normalizeFormMethod` which will normalize the exposed `useNavigation()/useFetcher()` `formMethod` fields as uppercase HTTP methods to align with the `fetch()` behavior. ([#10207](https://github.com/remix-run/react-router/pull/10207))

  - When `future.v7_normalizeFormMethod === false` (default v6 behavior),
    - `useNavigation().formMethod` is lowercase
    - `useFetcher().formMethod` is lowercase
  - When `future.v7_normalizeFormMethod === true`:
    - `useNavigation().formMethod` is uppercase
    - `useFetcher().formMethod` is uppercase

### Patch Changes

- Fix route ID generation when using Fragments in `createRoutesFromElements` ([#10193](https://github.com/remix-run/react-router/pull/10193))
- Updated dependencies:
  - `@remix-run/router@1.5.0`

## 6.9.0

### Minor Changes

- React Router now supports an alternative way to define your route `element` and `errorElement` fields as React Components instead of React Elements. You can instead pass a React Component to the new `Component` and `ErrorBoundary` fields if you choose. There is no functional difference between the two, so use whichever approach you prefer 😀. You shouldn't be defining both, but if you do `Component`/`ErrorBoundary` will "win". ([#10045](https://github.com/remix-run/react-router/pull/10045))

  **Example JSON Syntax**

  ```jsx
  // Both of these work the same:
  const elementRoutes = [{
    path: '/',
    element: <Home />,
    errorElement: <HomeError />,
  }]

  const componentRoutes = [{
    path: '/',
    Component: Home,
    ErrorBoundary: HomeError,
  }]

  function Home() { ... }
  function HomeError() { ... }
  ```

  **Example JSX Syntax**

  ```jsx
  // Both of these work the same:
  const elementRoutes = createRoutesFromElements(
    <Route path='/' element={<Home />} errorElement={<HomeError /> } />
  );

  const componentRoutes = createRoutesFromElements(
    <Route path='/' Component={Home} ErrorBoundary={HomeError} />
  );

  function Home() { ... }
  function HomeError() { ... }
  ```

- **Introducing Lazy Route Modules!** ([#10045](https://github.com/remix-run/react-router/pull/10045))

  In order to keep your application bundles small and support code-splitting of your routes, we've introduced a new `lazy()` route property. This is an async function that resolves the non-route-matching portions of your route definition (`loader`, `action`, `element`/`Component`, `errorElement`/`ErrorBoundary`, `shouldRevalidate`, `handle`).

  Lazy routes are resolved on initial load and during the `loading` or `submitting` phase of a navigation or fetcher call. You cannot lazily define route-matching properties (`path`, `index`, `children`) since we only execute your lazy route functions after we've matched known routes.

  Your `lazy` functions will typically return the result of a dynamic import.

  ```jsx
  // In this example, we assume most folks land on the homepage so we include that
  // in our critical-path bundle, but then we lazily load modules for /a and /b so
  // they don't load until the user navigates to those routes
  let routes = createRoutesFromElements(
    <Route path="/" element={<Layout />}>
      <Route index element={<Home />} />
      <Route path="a" lazy={() => import("./a")} />
      <Route path="b" lazy={() => import("./b")} />
    </Route>
  );
  ```

  Then in your lazy route modules, export the properties you want defined for the route:

  ```jsx
  export async function loader({ request }) {
    let data = await fetchData(request);
    return json(data);
  }

  // Export a `Component` directly instead of needing to create a React Element from it
  export function Component() {
    let data = useLoaderData();

    return (
      <>
        <h1>You made it!</h1>
        <p>{data}</p>
      </>
    );
  }

  // Export an `ErrorBoundary` directly instead of needing to create a React Element from it
  export function ErrorBoundary() {
    let error = useRouteError();
    return isRouteErrorResponse(error) ? (
      <h1>
        {error.status} {error.statusText}
      </h1>
    ) : (
      <h1>{error.message || error}</h1>
    );
  }
  ```

  An example of this in action can be found in the [`examples/lazy-loading-router-provider`](https://github.com/remix-run/react-router/tree/main/examples/lazy-loading-router-provider) directory of the repository.

  🙌 Huge thanks to @rossipedia for the [Initial Proposal](https://github.com/remix-run/react-router/discussions/9826) and [POC Implementation](https://github.com/remix-run/react-router/pull/9830).

- Updated dependencies:
  - `@remix-run/router@1.4.0`

### Patch Changes

- Fix `generatePath` incorrectly applying parameters in some cases ([#10078](https://github.com/remix-run/react-router/pull/10078))
- Improve memoization for context providers to avoid unnecessary re-renders ([#9983](https://github.com/remix-run/react-router/pull/9983))

## 6.8.2

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.3.3`

## 6.8.1

### Patch Changes

- Remove inaccurate console warning for POP navigations and update active blocker logic ([#10030](https://github.com/remix-run/react-router/pull/10030))
- Updated dependencies:
  - `@remix-run/router@1.3.2`

## 6.8.0

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.3.1`

## 6.7.0

### Minor Changes

- Add `unstable_useBlocker` hook for blocking navigations within the app's location origin ([#9709](https://github.com/remix-run/react-router/pull/9709))

### Patch Changes

- Fix `generatePath` when optional params are present ([#9764](https://github.com/remix-run/react-router/pull/9764))
- Update `<Await>` to accept `ReactNode` as children function return result ([#9896](https://github.com/remix-run/react-router/pull/9896))
- Updated dependencies:
  - `@remix-run/router@1.3.0`

## 6.6.2

### Patch Changes

- Ensure `useId` consistency during SSR ([#9805](https://github.com/remix-run/react-router/pull/9805))

## 6.6.1

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.2.1`

## 6.6.0

### Patch Changes

- Prevent `useLoaderData` usage in `errorElement` ([#9735](https://github.com/remix-run/react-router/pull/9735))
- Updated dependencies:
  - `@remix-run/router@1.2.0`

## 6.5.0

This release introduces support for [Optional Route Segments](https://github.com/remix-run/react-router/issues/9546). Now, adding a `?` to the end of any path segment will make that entire segment optional. This works for both static segments and dynamic parameters.

**Optional Params Examples**

- `<Route path=":lang?/about>` will match:
  - `/:lang/about`
  - `/about`
- `<Route path="/multistep/:widget1?/widget2?/widget3?">` will match:
  - `/multistep`
  - `/multistep/:widget1`
  - `/multistep/:widget1/:widget2`
  - `/multistep/:widget1/:widget2/:widget3`

**Optional Static Segment Example**

- `<Route path="/home?">` will match:
  - `/`
  - `/home`
- `<Route path="/fr?/about">` will match:
  - `/about`
  - `/fr/about`

### Minor Changes

- Allows optional routes and optional static segments ([#9650](https://github.com/remix-run/react-router/pull/9650))

### Patch Changes

- Stop incorrectly matching on partial named parameters, i.e. `<Route path="prefix-:param">`, to align with how splat parameters work. If you were previously relying on this behavior then it's recommended to extract the static portion of the path at the `useParams` call site: ([#9506](https://github.com/remix-run/react-router/pull/9506))

```jsx
// Old behavior at URL /prefix-123
<Route path="prefix-:id" element={<Comp /> }>

function Comp() {
  let params = useParams(); // { id: '123' }
  let id = params.id; // "123"
  ...
}

// New behavior at URL /prefix-123
<Route path=":id" element={<Comp /> }>

function Comp() {
  let params = useParams(); // { id: 'prefix-123' }
  let id = params.id.replace(/^prefix-/, ''); // "123"
  ...
}
```

- Updated dependencies:
  - `@remix-run/router@1.1.0`

## 6.4.5

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.0.5`

## 6.4.4

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.0.4`

## 6.4.3

### Patch Changes

- `useRoutes` should be able to return `null` when passing `locationArg` ([#9485](https://github.com/remix-run/react-router/pull/9485))
- fix `initialEntries` type in `createMemoryRouter` ([#9498](https://github.com/remix-run/react-router/pull/9498))
- Updated dependencies:
  - `@remix-run/router@1.0.3`

## 6.4.2

### Patch Changes

- Fix `IndexRouteObject` and `NonIndexRouteObject` types to make `hasErrorElement` optional ([#9394](https://github.com/remix-run/react-router/pull/9394))
- Enhance console error messages for invalid usage of data router hooks ([#9311](https://github.com/remix-run/react-router/pull/9311))
- If an index route has children, it will result in a runtime error. We have strengthened our `RouteObject`/`RouteProps` types to surface the error in TypeScript. ([#9366](https://github.com/remix-run/react-router/pull/9366))
- Updated dependencies:
  - `@remix-run/router@1.0.2`

## 6.4.1

### Patch Changes

- Preserve state from `initialEntries` ([#9288](https://github.com/remix-run/react-router/pull/9288))
- Updated dependencies:
  - `@remix-run/router@1.0.1`

## 6.4.0

Whoa this is a big one! `6.4.0` brings all the data loading and mutation APIs over from Remix. Here's a quick high level overview, but it's recommended you go check out the [docs](https://reactrouter.com), especially the [feature overview](https://reactrouter.com/en/6.4.0/start/overview) and the [tutorial](https://reactrouter.com/en/6.4.0/start/tutorial).

**New APIs**

- Create your router with `createMemoryRouter`
- Render your router with `<RouterProvider>`
- Load data with a Route `loader` and mutate with a Route `action`
- Handle errors with Route `errorElement`
- Defer non-critical data with `defer` and `Await`

**Bug Fixes**

- Path resolution is now trailing slash agnostic (#8861)
- `useLocation` returns the scoped location inside a `<Routes location>` component (#9094)

**Updated Dependencies**

- `@remix-run/router@1.0.0`
