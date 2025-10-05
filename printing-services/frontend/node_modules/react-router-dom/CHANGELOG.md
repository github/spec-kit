# `react-router-dom`

## 6.30.1

### Patch Changes

- Updated dependencies:
  - `react-router@6.30.1`

## 6.30.0

### Minor Changes

- Add `fetcherKey` as a parameter to `patchRoutesOnNavigation` ([#13109](https://github.com/remix-run/react-router/pull/13109))

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.23.0`
  - `react-router@6.30.0`

## 6.29.0

### Minor Changes

- Provide the request `signal` as a parameter to `patchRoutesOnNavigation` ([#12900](https://github.com/remix-run/react-router/pull/12900))

  - This can be used to abort any manifest fetches if the in-flight navigation/fetcher is aborted

### Patch Changes

- Do not log v7 deprecation warnings in production builds ([#12794](https://github.com/remix-run/react-router/pull/12794))
- Updated dependencies:
  - `react-router@6.29.0`
  - `@remix-run/router@1.22.0`

## 6.28.2

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.21.1`
  - `react-router@6.28.2`

## 6.28.1

### Patch Changes

- Updated dependencies:
  - `react-router@6.28.1`

## 6.28.0

### Minor Changes

- Log deprecation warnings for v7 flags ([#11750](https://github.com/remix-run/react-router/pull/11750))
  - Add deprecation warnings to `json`/`defer` in favor of returning raw objects
    - These methods will be removed in React Router v7

### Patch Changes

- Update JSDoc URLs for new website structure (add /v6/ segment) ([#12141](https://github.com/remix-run/react-router/pull/12141))
- Updated dependencies:
  - `react-router@6.28.0`
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
  - `react-router@6.27.0`
  - `@remix-run/router@1.20.0`

## 6.26.2

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.19.2`
  - `react-router@6.26.2`

## 6.26.1

### Patch Changes

- Rename `unstable_patchRoutesOnMiss` to `unstable_patchRoutesOnNavigation` to match new behavior ([#11888](https://github.com/remix-run/react-router/pull/11888))
- Updated dependencies:
  - `@remix-run/router@1.19.1`
  - `react-router@6.26.1`

## 6.26.0

### Minor Changes

- Add a new `replace(url, init?)` alternative to `redirect(url, init?)` that performs a `history.replaceState` instead of a `history.pushState` on client-side navigation redirects ([#11811](https://github.com/remix-run/react-router/pull/11811))

### Patch Changes

- Fix initial hydration behavior when using `future.v7_partialHydration` along with `unstable_patchRoutesOnMiss` ([#11838](https://github.com/remix-run/react-router/pull/11838))
  - During initial hydration, `router.state.matches` will now include any partial matches so that we can render ancestor `HydrateFallback` components
- Updated dependencies:
  - `@remix-run/router@1.19.0`
  - `react-router@6.26.0`

## 6.25.1

### Patch Changes

- Memoize some `RouterProvider` internals to reduce unnecessary re-renders ([#11803](https://github.com/remix-run/react-router/pull/11803))
- Updated dependencies:
  - `react-router@6.25.1`

## 6.25.0

### Minor Changes

- Stabilize `future.unstable_skipActionErrorRevalidation` as `future.v7_skipActionErrorRevalidation` ([#11769](https://github.com/remix-run/react-router/pull/11769))
  - When this flag is enabled, actions will not automatically trigger a revalidation if they return/throw a `Response` with a `4xx`/`5xx` status code
  - You may still opt-into revalidation via `shouldRevalidate`
  - This also changes `shouldRevalidate`'s `unstable_actionStatus` parameter to `actionStatus`

### Patch Changes

- Updated dependencies:
  - `react-router@6.25.0`
  - `@remix-run/router@1.18.0`

## 6.24.1

### Patch Changes

- Remove `polyfill.io` reference from warning message because the domain was sold and has since been determined to serve malware ([#11741](https://github.com/remix-run/react-router/pull/11741))
  - See <https://sansec.io/research/polyfill-supply-chain-attack>
- Export `NavLinkRenderProps` type for easier typing of custom `NavLink` callback ([#11553](https://github.com/remix-run/react-router/pull/11553))
- Updated dependencies:
  - `@remix-run/router@1.17.1`
  - `react-router@6.24.1`

## 6.24.0

### Minor Changes

- Add support for Lazy Route Discovery (a.k.a. Fog of War) ([#11626](https://github.com/remix-run/react-router/pull/11626))
  - RFC: <https://github.com/remix-run/react-router/discussions/11113>
  - `unstable_patchRoutesOnMiss` docs: <https://reactrouter.com/v6/routers/create-browser-router>

### Patch Changes

- Fix `fetcher.submit` types - remove incorrect `navigate`/`fetcherKey`/`unstable_viewTransition` options because they are only relevant for `useSubmit` ([#11631](https://github.com/remix-run/react-router/pull/11631))
- Allow falsy `location.state` values passed to `<StaticRouter>` ([#11495](https://github.com/remix-run/react-router/pull/11495))
- Updated dependencies:
  - `react-router@6.24.0`
  - `@remix-run/router@1.17.0`

## 6.23.1

### Patch Changes

- Check for `document` existence when checking `startViewTransition` ([#11544](https://github.com/remix-run/react-router/pull/11544))
- Change the `react-router-dom/server` import back to `react-router-dom` instead of `index.ts` ([#11514](https://github.com/remix-run/react-router/pull/11514))
- Updated dependencies:
  - `@remix-run/router@1.16.1`
  - `react-router@6.23.1`

## 6.23.0

### Minor Changes

- Add a new `unstable_dataStrategy` configuration option ([#11098](https://github.com/remix-run/react-router/pull/11098))
  - This option allows Data Router applications to take control over the approach for executing route loaders and actions
  - The default implementation is today's behavior, to fetch all loaders in parallel, but this option allows users to implement more advanced data flows including Remix single-fetch, middleware/context APIs, automatic loader caching, and more

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.16.0`
  - `react-router@6.23.0`

## 6.22.3

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.15.3`
  - `react-router@6.22.3`

## 6.22.2

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.15.2`
  - `react-router@6.22.2`

## 6.22.1

### Patch Changes

- Updated dependencies:
  - `react-router@6.22.1`
  - `@remix-run/router@1.15.1`

## 6.22.0

### Minor Changes

- Include a `window__reactRouterVersion` tag for CWV Report detection ([#11222](https://github.com/remix-run/react-router/pull/11222))

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.15.0`
  - `react-router@6.22.0`

## 6.21.3

### Patch Changes

- Fix `NavLink` `isPending` when a `basename` is used ([#11195](https://github.com/remix-run/react-router/pull/11195))
- Remove leftover `unstable_` prefix from `Blocker`/`BlockerFunction` types ([#11187](https://github.com/remix-run/react-router/pull/11187))
- Updated dependencies:
  - `react-router@6.21.3`

## 6.21.2

### Patch Changes

- Leverage `useId` for internal fetcher keys when available ([#11166](https://github.com/remix-run/react-router/pull/11166))
- Updated dependencies:
  - `@remix-run/router@1.14.2`
  - `react-router@6.21.2`

## 6.21.1

### Patch Changes

- Updated dependencies:
  - `react-router@6.21.1`
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

- Updated dependencies:
  - `@remix-run/router@1.14.0`
  - `react-router@6.21.0`

## 6.20.1

### Patch Changes

- Revert the `useResolvedPath` fix for splat routes due to a large number of applications that were relying on the buggy behavior (see <https://github.com/remix-run/react-router/issues/11052#issuecomment-1836589329>). We plan to re-introduce this fix behind a future flag in the next minor version. ([#11078](https://github.com/remix-run/react-router/pull/11078))
- Updated dependencies:
  - `react-router@6.20.1`
  - `@remix-run/router@1.13.1`

## 6.20.0

### Minor Changes

- Export the `PathParam` type from the public API ([#10719](https://github.com/remix-run/react-router/pull/10719))

### Patch Changes

- Updated dependencies:
  - `react-router@6.20.0`
  - `@remix-run/router@1.13.0`

## 6.19.0

### Minor Changes

- Add `unstable_flushSync` option to `useNavigate`/`useSumbit`/`fetcher.load`/`fetcher.submit` to opt-out of `React.startTransition` and into `ReactDOM.flushSync` for state updates ([#11005](https://github.com/remix-run/react-router/pull/11005))
- Allow `unstable_usePrompt` to accept a `BlockerFunction` in addition to a `boolean` ([#10991](https://github.com/remix-run/react-router/pull/10991))

### Patch Changes

- Fix issue where a changing fetcher `key` in a `useFetcher` that remains mounted wasn't getting picked up ([#11009](https://github.com/remix-run/react-router/pull/11009))
- Fix `useFormAction` which was incorrectly inheriting the `?index` query param from child route `action` submissions ([#11025](https://github.com/remix-run/react-router/pull/11025))
- Fix `NavLink` `active` logic when `to` location has a trailing slash ([#10734](https://github.com/remix-run/react-router/pull/10734))
- Updated dependencies:
  - `react-router@6.19.0`
  - `@remix-run/router@1.12.0`

## 6.18.0

### Minor Changes

- Add support for manual fetcher key specification via `useFetcher({ key: string })` so you can access the same fetcher instance from different components in your application without prop-drilling ([RFC](https://github.com/remix-run/remix/discussions/7698)) ([#10960](https://github.com/remix-run/react-router/pull/10960))

  - Fetcher keys are now also exposed on the fetchers returned from `useFetchers` so that they can be looked up by `key`

- Add `navigate`/`fetcherKey` params/props to `useSumbit`/`Form` to support kicking off a fetcher submission under the hood with an optionally user-specified `key` ([#10960](https://github.com/remix-run/react-router/pull/10960))

  - Invoking a fetcher in this way is ephemeral and stateless
  - If you need to access the state of one of these fetchers, you will need to leverage `useFetcher({ key })` to look it up elsewhere

### Patch Changes

- Adds a fetcher context to `RouterProvider` that holds completed fetcher data, in preparation for the upcoming future flag that will change the fetcher persistence/cleanup behavior ([#10961](https://github.com/remix-run/react-router/pull/10961))
- Fix the `future` prop on `BrowserRouter`, `HashRouter` and `MemoryRouter` so that it accepts a `Partial<FutureConfig>` instead of requiring all flags to be included. ([#10962](https://github.com/remix-run/react-router/pull/10962))
- Updated dependencies:
  - `@remix-run/router@1.11.0`
  - `react-router@6.18.0`

## 6.17.0

### Minor Changes

- Add experimental support for the [View Transitions API](https://developer.mozilla.org/en-US/docs/Web/API/ViewTransition) via `document.startViewTransition` to enable CSS animated transitions on SPA navigations in your application. ([#10916](https://github.com/remix-run/react-router/pull/10916))

  The simplest approach to enabling a View Transition in your React Router app is via the new `<Link unstable_viewTransition>` prop. This will cause the navigation DOM update to be wrapped in `document.startViewTransition` which will enable transitions for the DOM update. Without any additional CSS styles, you'll get a basic cross-fade animation for your page.

  If you need to apply more fine-grained styles for your animations, you can leverage the `unstable_useViewTransitionState` hook which will tell you when a transition is in progress and you can use that to apply classes or styles:

  ```jsx
  function ImageLink(to, src, alt) {
    let isTransitioning = unstable_useViewTransitionState(to);
    return (
      <Link to={to} unstable_viewTransition>
        <img
          src={src}
          alt={alt}
          style={{
            viewTransitionName: isTransitioning ? "image-expand" : "",
          }}
        />
      </Link>
    );
  }
  ```

  You can also use the `<NavLink unstable_viewTransition>` shorthand which will manage the hook usage for you and automatically add a `transitioning` class to the `<a>` during the transition:

  ```css
  a.transitioning img {
    view-transition-name: "image-expand";
  }
  ```

  ```jsx
  <NavLink to={to} unstable_viewTransition>
    <img src={src} alt={alt} />
  </NavLink>
  ```

  For an example usage of View Transitions with React Router, check out [our fork](https://github.com/brophdawg11/react-router-records) of the [Astro Records](https://github.com/Charca/astro-records) demo.

  For more information on using the View Transitions API, please refer to the [Smooth and simple transitions with the View Transitions API](https://developer.chrome.com/docs/web-platform/view-transitions/) guide from the Google Chrome team.

  Please note, that because the `ViewTransition` API is a DOM API, we now export a specific `RouterProvider` from `react-router-dom` with this functionality. If you are importing `RouterProvider` from `react-router`, then it will not support view transitions. ([#10928](https://github.com/remix-run/react-router/pull/10928)

### Patch Changes

- Log a warning and fail gracefully in `ScrollRestoration` when `sessionStorage` is unavailable ([#10848](https://github.com/remix-run/react-router/pull/10848))
- Updated dependencies:
  - `@remix-run/router@1.10.0`
  - `react-router@6.17.0`

## 6.16.0

### Minor Changes

- Updated dependencies:
  - `@remix-run/router@1.9.0`
  - `react-router@6.16.0`

### Patch Changes

- Properly encode rendered URIs in server rendering to avoid hydration errors ([#10769](https://github.com/remix-run/react-router/pull/10769))

## 6.15.0

### Minor Changes

- Add's a new `redirectDocument()` function which allows users to specify that a redirect from a `loader`/`action` should trigger a document reload (via `window.location`) instead of attempting to navigate to the redirected location via React Router ([#10705](https://github.com/remix-run/react-router/pull/10705))

### Patch Changes

- Fixes an edge-case affecting web extensions in Firefox that use `URLSearchParams` and the `useSearchParams` hook. ([#10620](https://github.com/remix-run/react-router/pull/10620))
- Do not include hash in `useFormAction()` for unspecified actions since it cannot be determined on the server and causes hydration issues ([#10758](https://github.com/remix-run/react-router/pull/10758))
- Reorder effects in `unstable_usePrompt` to avoid throwing an exception if the prompt is unblocked and a navigation is performed synchronously ([#10687](https://github.com/remix-run/react-router/pull/10687), [#10718](https://github.com/remix-run/react-router/pull/10718))
- Updated dependencies:
  - `@remix-run/router@1.8.0`
  - `react-router@6.15.0`

## 6.14.2

### Patch Changes

- Properly decode element id when emulating hash scrolling via `<ScrollRestoration>` ([#10682](https://github.com/remix-run/react-router/pull/10682))
- Add missing `<Form state>` prop to populate `history.state` on submission navigations ([#10630](https://github.com/remix-run/react-router/pull/10630))
- Support proper hydration of `Error` subclasses such as `ReferenceError`/`TypeError` ([#10633](https://github.com/remix-run/react-router/pull/10633))
- Updated dependencies:
  - `@remix-run/router@1.7.2`
  - `react-router@6.14.2`

## 6.14.1

### Patch Changes

- Updated dependencies:
  - `react-router@6.14.1`
  - `@remix-run/router@1.7.1`

## 6.14.0

### Minor Changes

- Add support for `application/json` and `text/plain` encodings for `useSubmit`/`fetcher.submit`. To reflect these additional types, `useNavigation`/`useFetcher` now also contain `navigation.json`/`navigation.text` and `fetcher.json`/`fetcher.text` which include the json/text submission if applicable ([#10413](https://github.com/remix-run/react-router/pull/10413))

  ```jsx
  // The default behavior will still serialize as FormData
  function Component() {
    let navigation = useNavigation();
    let submit = useSubmit();
    submit({ key: "value" }, { method: "post" });
    // navigation.formEncType => "application/x-www-form-urlencoded"
    // navigation.formData    => FormData instance
  }

  async function action({ request }) {
    // request.headers.get("Content-Type") => "application/x-www-form-urlencoded"
    // await request.formData()            => FormData instance
  }
  ```

  ```js
  // Opt-into JSON encoding with `encType: "application/json"`
  function Component() {
    let navigation = useNavigation();
    let submit = useSubmit();
    submit({ key: "value" }, { method: "post", encType: "application/json" });
    // navigation.formEncType => "application/json"
    // navigation.json        => { key: "value" }
  }

  async function action({ request }) {
    // request.headers.get("Content-Type") => "application/json"
    // await request.json()                => { key: "value" }
  }
  ```

  ```js
  // Opt-into text encoding with `encType: "text/plain"`
  function Component() {
    let navigation = useNavigation();
    let submit = useSubmit();
    submit("Text submission", { method: "post", encType: "text/plain" });
    // navigation.formEncType => "text/plain"
    // navigation.text        => "Text submission"
  }

  async function action({ request }) {
    // request.headers.get("Content-Type") => "text/plain"
    // await request.text()                => "Text submission"
  }
  ```

### Patch Changes

- When submitting a form from a `submitter` element, prefer the built-in `new FormData(form, submitter)` instead of the previous manual approach in modern browsers (those that support the new `submitter` parameter) ([#9865](https://github.com/remix-run/react-router/pull/9865), [#10627](https://github.com/remix-run/react-router/pull/10627))
  - For browsers that don't support it, we continue to just append the submit button's entry to the end, and we also add rudimentary support for `type="image"` buttons
  - If developers want full spec-compliant support for legacy browsers, they can use the `formdata-submitter-polyfill`
- Call `window.history.pushState/replaceState` before updating React Router state (instead of after) so that `window.location` matches `useLocation` during synchronous React 17 rendering ([#10448](https://github.com/remix-run/react-router/pull/10448))
  - ⚠️ However, generally apps should not be relying on `window.location` and should always reference `useLocation` when possible, as `window.location` will not be in sync 100% of the time (due to `popstate` events, concurrent mode, etc.)
- Fix `tsc --skipLibCheck:false` issues on React 17 ([#10622](https://github.com/remix-run/react-router/pull/10622))
- Upgrade `typescript` to 5.1 ([#10581](https://github.com/remix-run/react-router/pull/10581))
- Updated dependencies:
  - `react-router@6.14.0`
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
- Updated dependencies:
  - `react-router@6.13.0`

## 6.12.1

> \[!WARNING]
> Please use version `6.13.0` or later instead of `6.12.1`. This version suffers from a `webpack`/`terser` minification issue resulting in invalid minified code in your resulting production bundles which can cause issues in your application. See [#10579](https://github.com/remix-run/react-router/issues/10579) for more details.

### Patch Changes

- Adjust feature detection of `React.startTransition` to fix webpack + react 17 compilation error ([#10569](https://github.com/remix-run/react-router/pull/10569))
- Updated dependencies:
  - `react-router@6.12.1`

## 6.12.0

### Minor Changes

- Wrap internal router state updates with `React.startTransition` if it exists ([#10438](https://github.com/remix-run/react-router/pull/10438))

### Patch Changes

- Re-throw `DOMException` (`DataCloneError`) when attempting to perform a `PUSH` navigation with non-serializable state. ([#10427](https://github.com/remix-run/react-router/pull/10427))
- Updated dependencies:
  - `@remix-run/router@1.6.3`
  - `react-router@6.12.0`

## 6.11.2

### Patch Changes

- Export `SetURLSearchParams` type ([#10444](https://github.com/remix-run/react-router/pull/10444))
- Updated dependencies:
  - `react-router@6.11.2`
  - `@remix-run/router@1.6.2`

## 6.11.1

### Patch Changes

- Updated dependencies:
  - `react-router@6.11.1`
  - `@remix-run/router@1.6.1`

## 6.11.0

### Minor Changes

- Enable `basename` support in `useFetcher` ([#10336](https://github.com/remix-run/react-router/pull/10336))
  - If you were previously working around this issue by manually prepending the `basename` then you will need to remove the manually prepended `basename` from your `fetcher` calls (`fetcher.load('/basename/route') -> fetcher.load('/route')`)

### Patch Changes

- Fix inadvertent re-renders when using `Component` instead of `element` on a route definition ([#10287](https://github.com/remix-run/react-router/pull/10287))
- Fail gracefully on `<Link to="//">` and other invalid URL values ([#10367](https://github.com/remix-run/react-router/pull/10367))
- Switched from `useSyncExternalStore` to `useState` for internal `@remix-run/router` router state syncing in `<RouterProvider>`. We found some [subtle bugs](https://codesandbox.io/s/use-sync-external-store-loop-9g7b81) where router state updates got propagated _before_ other normal `useState` updates, which could lead to footguns in `useEffect` calls. ([#10377](https://github.com/remix-run/react-router/pull/10377), [#10409](https://github.com/remix-run/react-router/pull/10409))
- Add static prop to `StaticRouterProvider`'s internal `Router` component ([#10401](https://github.com/remix-run/react-router/pull/10401))
- When using a `RouterProvider`, `useNavigate`/`useSubmit`/`fetcher.submit` are now stable across location changes, since we can handle relative routing via the `@remix-run/router` instance and get rid of our dependence on `useLocation()`. When using `BrowserRouter`, these hooks remain unstable across location changes because they still rely on `useLocation()`. ([#10336](https://github.com/remix-run/react-router/pull/10336))
- Updated dependencies:
  - `react-router@6.11.0`
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

- Fix `createStaticHandler` to also check for `ErrorBoundary` on routes in addition to `errorElement` ([#10190](https://github.com/remix-run/react-router/pull/10190))
- Updated dependencies:
  - `@remix-run/router@1.5.0`
  - `react-router@6.10.0`

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
  - `react-router@6.9.0`
  - `@remix-run/router@1.4.0`

## 6.8.2

### Patch Changes

- Treat same-origin absolute URLs in `<Link to>` as external if they are outside of the router `basename` ([#10135](https://github.com/remix-run/react-router/pull/10135))
- Fix `useBlocker` to return `IDLE_BLOCKER` during SSR ([#10046](https://github.com/remix-run/react-router/pull/10046))
- Fix SSR of absolute `<Link to>` urls ([#10112](https://github.com/remix-run/react-router/pull/10112))
- Properly escape HTML characters in `StaticRouterProvider` serialized hydration data ([#10068](https://github.com/remix-run/react-router/pull/10068))
- Updated dependencies:
  - `@remix-run/router@1.3.3`
  - `react-router@6.8.2`

## 6.8.1

### Patch Changes

- Improved absolute url detection in `Link` component (now also supports `mailto:` urls) ([#9994](https://github.com/remix-run/react-router/pull/9994))
- Fix partial object (search or hash only) pathnames losing current path value ([#10029](https://github.com/remix-run/react-router/pull/10029))
- Updated dependencies:
  - `react-router@6.8.1`
  - `@remix-run/router@1.3.2`

## 6.8.0

### Minor Changes

- Support absolute URLs in `<Link to>`. If the URL is for the current origin, it will still do a client-side navigation. If the URL is for a different origin then it will do a fresh document request for the new origin. ([#9900](https://github.com/remix-run/react-router/pull/9900))

  ```tsx
  <Link to="https://neworigin.com/some/path">    {/* Document request */}
  <Link to="//neworigin.com/some/path">          {/* Document request */}
  <Link to="https://www.currentorigin.com/path"> {/* Client-side navigation */}
  ```

### Patch Changes

- Fix bug with search params removal via `useSearchParams` ([#9969](https://github.com/remix-run/react-router/pull/9969))
- Respect `preventScrollReset` on `<fetcher.Form>` ([#9963](https://github.com/remix-run/react-router/pull/9963))
- Fix navigation for hash routers on manual URL changes ([#9980](https://github.com/remix-run/react-router/pull/9980))
- Use `pagehide` instead of `beforeunload` for `<ScrollRestoration>`. This has better cross-browser support, specifically on Mobile Safari. ([#9945](https://github.com/remix-run/react-router/pull/9945))
- Updated dependencies:
  - `@remix-run/router@1.3.1`
  - `react-router@6.8.0`

## 6.7.0

### Minor Changes

- Add `unstable_useBlocker` hook for blocking navigations within the app's location origin ([#9709](https://github.com/remix-run/react-router/pull/9709))
- Add `unstable_usePrompt` hook for blocking navigations within the app's location origin ([#9932](https://github.com/remix-run/react-router/pull/9932))
- Add `preventScrollReset` prop to `<Form>` ([#9886](https://github.com/remix-run/react-router/pull/9886))

### Patch Changes

- Added pass-through event listener options argument to `useBeforeUnload` ([#9709](https://github.com/remix-run/react-router/pull/9709))
- Streamline jsdom bug workaround in tests ([#9824](https://github.com/remix-run/react-router/pull/9824))
- Updated dependencies:
  - `@remix-run/router@1.3.0`
  - `react-router@6.7.0`

## 6.6.2

### Patch Changes

- Ensure `useId` consistency during SSR ([#9805](https://github.com/remix-run/react-router/pull/9805))
- Updated dependencies:
  - `react-router@6.6.2`

## 6.6.1

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.2.1`
  - `react-router@6.6.1`

## 6.6.0

### Minor Changes

- Add `useBeforeUnload()` hook ([#9664](https://github.com/remix-run/react-router/pull/9664))
- Remove `unstable_` prefix from `createStaticHandler`/`createStaticRouter`/`StaticRouterProvider` ([#9738](https://github.com/remix-run/react-router/pull/9738))

### Patch Changes

- Proper hydration of `Error` objects from `StaticRouterProvider` ([#9664](https://github.com/remix-run/react-router/pull/9664))
- Support uppercase `<Form method>` and `useSubmit` method values ([#9664](https://github.com/remix-run/react-router/pull/9664))
- Skip initial scroll restoration for SSR apps with `hydrationData` ([#9664](https://github.com/remix-run/react-router/pull/9664))
- Fix `<button formmethod>` form submission overriddes ([#9664](https://github.com/remix-run/react-router/pull/9664))
- Updated dependencies:
  - `@remix-run/router@1.2.0`
  - `react-router@6.6.0`

## 6.5.0

### Patch Changes

- Updated dependencies:
  - `react-router@6.5.0`
  - `@remix-run/router@1.1.0`

## 6.4.5

### Patch Changes

- Updated dependencies:
  - `@remix-run/router@1.0.5`
  - `react-router@6.4.5`

## 6.4.4

### Patch Changes

- Fix issues with encoded characters in `NavLink` and descendant `<Routes>` ([#9589](https://github.com/remix-run/react-router/pull/9589), [#9647](https://github.com/remix-run/react-router/pull/9647))
- Properly serialize/deserialize `ErrorResponse` instances when using built-in hydration ([#9593](https://github.com/remix-run/react-router/pull/9593))
- Support `basename` in static data routers ([#9591](https://github.com/remix-run/react-router/pull/9591))
- Updated dependencies:
  - `@remix-run/router@1.0.4`
  - `react-router@6.4.4`

## 6.4.3

### Patch Changes

- Fix hrefs generated for `createHashRouter` ([#9409](https://github.com/remix-run/react-router/pull/9409))
- fix encoding/matching issues with special chars ([#9477](https://github.com/remix-run/react-router/pull/9477), [#9496](https://github.com/remix-run/react-router/pull/9496))
- Properly support `index` routes with a `path` in `useResolvedPath` ([#9486](https://github.com/remix-run/react-router/pull/9486))
- Respect `relative=path` prop on `NavLink` ([#9453](https://github.com/remix-run/react-router/pull/9453))
- Fix `NavLink` behavior for root urls ([#9497](https://github.com/remix-run/react-router/pull/9497))
- Updated dependencies:
  - `@remix-run/router@1.0.3`
  - `react-router@6.4.3`

## 6.4.2

### Patch Changes

- Respect `basename` in `useFormAction` ([#9352](https://github.com/remix-run/react-router/pull/9352))
- Enhance console error messages for invalid usage of data router hooks ([#9311](https://github.com/remix-run/react-router/pull/9311))
- If an index route has children, it will result in a runtime error. We have strengthened our `RouteObject`/`RouteProps` types to surface the error in TypeScript. ([#9366](https://github.com/remix-run/react-router/pull/9366))
- Updated dependencies:
  - `react-router@6.4.2`
  - `@remix-run/router@1.0.2`

## 6.4.1

### Patch Changes

- Updated dependencies:
  - `react-router@6.4.1`
  - `@remix-run/router@1.0.1`

## 6.4.0

Whoa this is a big one! `6.4.0` brings all the data loading and mutation APIs over from Remix. Here's a quick high level overview, but it's recommended you go check out the [docs](https://reactrouter.com), especially the [feature overview](https://reactrouter.com/en/6.4.0/start/overview) and the [tutorial](https://reactrouter.com/en/6.4.0/start/tutorial).

**New APIs**

- Create your router with `createMemoryRouter`/`createBrowserRouter`/`createHashRouter`
- Render your router with `<RouterProvider>`
- Load data with a Route `loader` and mutate with a Route `action`
- Handle errors with Route `errorElement`
- Submit data with the new `<Form>` component
- Perform in-page data loads and mutations with `useFetcher()`
- Defer non-critical data with `defer` and `Await`
- Manage scroll position with `<ScrollRestoration>`

**New Features**

- Perform path-relative navigations with `<Link relative="path">` (#9160)

**Bug Fixes**

- Path resolution is now trailing slash agnostic (#8861)
- `useLocation` returns the scoped location inside a `<Routes location>` component (#9094)
- respect the `<Link replace>` prop if it is defined (#8779)

**Updated Dependencies**

- `react-router@6.4.0`
