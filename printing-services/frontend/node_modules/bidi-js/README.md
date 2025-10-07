# bidi-js

This is a pure JavaScript implementation of the [Unicode Bidirectional Algorithm](https://www.unicode.org/reports/tr9/) version 13.0.0. Its goals, in no particular order, are to be:

* Correct
* Small
* Fast


## Conformance

This implementation currently conforms to section [UAX-C1](https://unicode.org/reports/tr9/#C1) of the bidi spec, as verified by running all the provided [conformance tests](https://unicode.org/reports/tr9/#Bidi_Conformance_Testing).

## Compatibility

It has no external dependencies and therefore should run just fine in any relatively capable web browser, Node.js, etc. The provided distribution `.js` files are valid ES5.

## Usage

Install it from npm:

```shell
npm install bidi-js
```

[![NPM](https://nodei.co/npm/bidi-js.png?compact=true)](https://npmjs.org/package/bidi-js)

Import and initialize:

```js
import bidiFactory from 'bidi-js'
// or: const bidiFactory = require('bidi-js')

const bidi = bidiFactory()
```

The `bidi-js` package's only export is a factory function which you _must invoke_ to return a `bidi` object; that object exposes the methods for bidi processing.

(_Why a factory function?_ The main reason is to ensure the entire module's code is wrapped within a single self-contained function with no closure dependencies. This enables that function to be stringified and passed into a web worker, for example.)

Now that you have the `bidi` object, you can:

### Calculate bidi embedding levels

```js
const embeddingLevels = bidi.getEmbeddingLevels(
  text, //the input string containing mixed-direction text
  explicitDirection //"ltr" or "rtl" if you don't want to auto-detect it
)

const { levels, paragraphs } = embeddingLevels
```

The result object `embeddingLevels` will usually be passed to other functions described below. Its contents, should you need to inspect them individually, are:

* `levels` is a `Uint8Array` holding the calculated [bidi embedding levels](https://unicode.org/reports/tr9/#BD2) for each character in the string. The most important thing to know about these levels is that any given character is in a right-to-left scope if its embedding level is an odd number, and left-to-right if it's an even number.

* `paragraphs` is an array of `{start, end, level}` objects, one for each paragraph in the text (paragraphs are separated by explicit breaking characters, not soft line wrapping). The `start` and `end` indices are inclusive, and `level` is the resolved base embedding level of that paragraph.

### Calculate character reorderings

```js
const flips = bidi.getReorderSegments(
  text, //the full input string
  embeddingLevels //the full result object from getEmbeddingLevels
)

// Process all reversal sequences, in order:
flips.forEach(range => {
  const [start, end] = range
  // Reverse this sequence of characters from start to end, inclusive
  for (let i = start; i <= end; i++) {
    //...
  }
})
```

Each "flip" is a range that should be reversed in place; they must all be applied in order.

Sometimes you don't want to process the whole string at once, but just a particular substring. A common example would be if you've applied line wrapping, in which case you need to process each line individually (in particular this does some special handling for trailing whitespace for each line). For this you can pass the extra `start` and `end` parameters:

```js
yourWrappedLines.forEach(([lineStart, lineEnd]) => {
  const flips = bidi.getReorderSegments(
    text,
    embeddingLevels,
    lineStart,
    lineEnd //inclusive
  )
  // ...process flips for this line
})
```

### Handle right-to-left mirrored characters

Some characters that resolve to right-to-left need to be swapped with their "mirrored" characters. Examples of this are opening/closing parentheses. You can determine all the characters that need to be mirrored like so:

```js
const mirrored = bidi.getMirroredCharactersMap(
  text,
  embeddingLevels
)
```

This returns a `Map` of numeric character indices to replacement characters.

You can also process just a substring with extra `start` and `end` parameters:

```js
const mirrored = bidi.getMirroredCharactersMap(
  text,
  embeddingLevels,
  start,
  end //inclusive
)
```

If you'd rather process mirrored characters individually, you can use the single `getMirroredCharacter` function, just make sure you only do it for right-to-left characters (those whose embedding level is an odd number.) It will return `null` if the character doesn't support mirroring.

```js
const mirroredChar = (embeddingLevels.levels[charIndex] & 1) //odd number means RTL
    ? bidi.getMirroredCharacter(text[charIndex])
    : null
```

### Get a character's bidi type

This is used internally, but you can also ask for the ["bidi character type"](https://unicode.org/reports/tr9/#BD1) of any character, should you need it:

```js
const bidiType = bidi.getBidiCharTypeName(string[charIndex])
// e.g. "L", "R", "AL", "NSM", ...
```
