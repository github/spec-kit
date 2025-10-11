# goober-autoprefixer

A css autoprefixer for [🥜goober](https://github.com/cristianbote/goober) using [style-vendorizer](https://github.com/kripod/style-vendorizer).

## Install

`npm install --save goober`

## How to use it

This packages exports a `prefix` function that needs to be passed to goober's `setup` function like this:

```jsx
import React from 'react';
import { setup } from 'goober';
import { prefix } from 'goober/prefixer';

// Setup goober for react with autoprefixer
setup(React.createElement, prefix);
```
