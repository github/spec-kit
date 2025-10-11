# Lucide React

Implementation of the lucide icon library for react applications.

> What is lucide? Read it [here](https://github.com/lucide-icons/lucide#what-is-lucide).

## Installation

```sh
yarn add lucide-react
```

or

```sh
npm install lucide-react
```

## How to use

It's built with ES modules so it's completely tree-shakable.
Each icon can be imported as a react component.

### Example

You can pass additional props to adjust the icon.

```js
import { Camera } from 'lucide-react';

const App = () => {
  return <Camera color="red" size={48} />;
};

export default App;
```

### Props

| name          | type     | default      |
| ------------- | -------- | ------------ |
| `size`        | _Number_ | 24           |
| `color`       | _String_ | currentColor |
| `strokeWidth` | _Number_ | 2            |

### Custom props

You can also pass custom props that will be added in the svg as attributes.

```js
const App = () => {
  return <Camera fill="red" />;
};
```

### Generic icon component

It is possible to create a generic icon component to load icons.

> :warning: The example below is importing all ES modules. This is **not** recommended when you using a bundler since your application build size will grow substantially.

```js
import { icons } from 'lucide-react';

const Icon = ({ name, color, size }) => {
  const LucideIcon = icons[name];

  return <LucideIcon color={color} size={size} />;
};

export default Icon;
```

#### With Dynamic Imports

Lucide react exports a dynamic import map `dynamicIconImports`. Useful for applications that want to show icons dynamically by icon name. For example when using a content management system with where icon names are stored in a database.

When using client side rendering, it will fetch the icon component when it's needed. This will reduce the initial bundle size.

The keys of the dynamic import map are the lucide original icon names.

Example with React suspense:

```tsx
import React, { lazy, Suspense } from 'react';
import { dynamicIconImports, LucideProps } from 'lucide-react';

const fallback = <div style={{ background: '#ddd', width: 24, height: 24 }}/>

interface IconProps extends Omit<LucideProps, 'ref'> {
  name: keyof typeof dynamicIconImports;
}

const Icon = ({ name, ...props }: IconProps) => {
  const LucideIcon = lazy(dynamicIconImports[name]);

  return (
    <Suspense fallback={fallback}>
      <LucideIcon {...props} />
    </Suspense>
  );
}

export default Icon
```

##### NextJS Example

In NextJS, [the dynamic function](https://nextjs.org/docs/pages/building-your-application/optimizing/lazy-loading#nextdynamic) can be used to dynamically load the icon component.

To make dynamic imports work with NextJS, you need to add `lucide-react` to the [`transpilePackages`](https://nextjs.org/docs/app/api-reference/next-config-js/transpilePackages) option in your `next.config.js` like this:

```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ['lucide-react'] // add this
}

module.exports = nextConfig

```

You can then start using it:

```tsx
import dynamic from 'next/dynamic'
import { LucideProps } from 'lucide-react';
import dynamicIconImports from 'lucide-react/dynamicIconImports';

interface IconProps extends LucideProps {
  name: keyof typeof dynamicIconImports;
}

const Icon = ({ name, ...props }: IconProps) => {
  const LucideIcon = dynamic(dynamicIconImports[name])

  return <LucideIcon {...props} />;
};

export default Icon;
```
