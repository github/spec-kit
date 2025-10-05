AES-JS
======

[![npm version](https://badge.fury.io/js/aes-js.svg)](https://badge.fury.io/js/aes-js)

A pure JavaScript implementation of the AES block cipher algorithm and all common modes of operation (CBC, CFB, CTR, ECB and OFB).

Features
--------

- Pure JavaScript (with no dependencies)
- Supports all key sizes (128-bit, 192-bit and 256-bit)
- Supports all common modes of operation (CBC, CFB, CTR, ECB and OFB)
- Works in either node.js or web browsers

Migrating from 2.x to 3.x
-------------------------

The utility functions have been renamed in the 3.x branch, since they were causing a great deal of confusion converting between bytes and string.

The examples have also been updated to encode binary data as printable hex strings.

**Strings and Bytes**

Strings should **NOT** be used as keys. UTF-8 allows variable length, multi-byte characters, so a string that is 16 *characters* long may not be 16 *bytes* long.

Also, UTF8 should **NOT** be used to store arbitrary binary data as it is a *string* encoding format, not a *binary* encoding format.

```javascript
// aesjs.util.convertStringToBytes(aString)
// Becomes:
aesjs.utils.utf8.toBytes(aString)


// aesjs.util.convertBytesToString(aString)
// Becomes:
aesjs.utils.utf8.fromBytes(aString)
```

**Bytes and Hex strings**

Binary data, such as encrypted bytes, can safely be stored and printed as hexidecimal strings.

```javascript
// aesjs.util.convertStringToBytes(aString, 'hex')
// Becomes:
aesjs.utils.hex.toBytes(aString)


// aesjs.util.convertBytesToString(aString, 'hex')
// Becomes:
aesjs.utils.hex.fromBytes(aString)
```

**Typed Arrays**

The 3.x and above versions of aes-js use [Uint8Array](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Uint8Array) instead of Array, which reduces code size when used with Browserify (it no longer pulls in Buffer) and is also about **twice** the speed.

However, if you need to support browsers older than IE 10, you should continue using version 2.x.


API
===

#### Node.js

To install `aes-js` in your node.js project:

```
npm install aes-js
```

And to access it from within node, simply add:

```javascript
var aesjs = require('aes-js');
```

#### Web Browser

To use `aes-js` in a web page, add the following:

```html
<script type="text/javascript" src="https://cdn.rawgit.com/ricmoo/aes-js/e27b99df/index.js"></script>
```

Keys
----

All keys must be 128 bits (16 bytes), 192 bits (24 bytes) or 256 bits (32 bytes) long.

The library work with `Array`, `Uint8Array` and `Buffer` objects as well as any *array-like* object (i.e. must have a `length` property, and have a valid byte value for each entry).

```javascript
// 128-bit, 192-bit and 256-bit keys
var key_128 = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15];
var key_192 = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
               16, 17, 18, 19, 20, 21, 22, 23];
var key_256 = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
               16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28,
               29, 30, 31];

// or, you may use Uint8Array:
var key_128_array = new Uint8Array(key_128);
var key_192_array = new Uint8Array(key_192);
var key_256_array = new Uint8Array(key_256);

// or, you may use Buffer in node.js:
var key_128_buffer = Buffer.from(key_128);
var key_192_buffer = Buffer.from(key_192);
var key_256_buffer = Buffer.from(key_256);
```


To generate keys from simple-to-remember passwords, consider using a password-based key-derivation function such as [scrypt](https://www.npmjs.com/package/scrypt-js) or [bcrypt](https://www.npmjs.com/search?q=bcrypt).


Common Modes of Operation
-------------------------

There are several modes of operations, each with various pros and cons. In general though, the **CBC** and **CTR** modes are recommended. The **ECB is NOT recommended.**, and is included primarily for completeness.

### CTR - Counter (recommended)

```javascript
// An example 128-bit key (16 bytes * 8 bits/byte = 128 bits)
var key = [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16 ];

// Convert text to bytes
var text = 'Text may be any length you wish, no padding is required.';
var textBytes = aesjs.utils.utf8.toBytes(text);

// The counter is optional, and if omitted will begin at 1
var aesCtr = new aesjs.ModeOfOperation.ctr(key, new aesjs.Counter(5));
var encryptedBytes = aesCtr.encrypt(textBytes);

// To print or store the binary data, you may convert it to hex
var encryptedHex = aesjs.utils.hex.fromBytes(encryptedBytes);
console.log(encryptedHex);
// "a338eda3874ed884b6199150d36f49988c90f5c47fe7792b0cf8c7f77eeffd87
//  ea145b73e82aefcf2076f881c88879e4e25b1d7b24ba2788"

// When ready to decrypt the hex string, convert it back to bytes
var encryptedBytes = aesjs.utils.hex.toBytes(encryptedHex);

// The counter mode of operation maintains internal state, so to
// decrypt a new instance must be instantiated.
var aesCtr = new aesjs.ModeOfOperation.ctr(key, new aesjs.Counter(5));
var decryptedBytes = aesCtr.decrypt(encryptedBytes);

// Convert our bytes back into text
var decryptedText = aesjs.utils.utf8.fromBytes(decryptedBytes);
console.log(decryptedText);
// "Text may be any length you wish, no padding is required."
```


### CBC - Cipher-Block Chaining (recommended)

```javascript
// An example 128-bit key
var key = [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16 ];

// The initialization vector (must be 16 bytes)
var iv = [ 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34,35, 36 ];

// Convert text to bytes (text must be a multiple of 16 bytes)
var text = 'TextMustBe16Byte';
var textBytes = aesjs.utils.utf8.toBytes(text);

var aesCbc = new aesjs.ModeOfOperation.cbc(key, iv);
var encryptedBytes = aesCbc.encrypt(textBytes);

// To print or store the binary data, you may convert it to hex
var encryptedHex = aesjs.utils.hex.fromBytes(encryptedBytes);
console.log(encryptedHex);
// "104fb073f9a131f2cab49184bb864ca2"

// When ready to decrypt the hex string, convert it back to bytes
var encryptedBytes = aesjs.utils.hex.toBytes(encryptedHex);

// The cipher-block chaining mode of operation maintains internal
// state, so to decrypt a new instance must be instantiated.
var aesCbc = new aesjs.ModeOfOperation.cbc(key, iv);
var decryptedBytes = aesCbc.decrypt(encryptedBytes);

// Convert our bytes back into text
var decryptedText = aesjs.utils.utf8.fromBytes(decryptedBytes);
console.log(decryptedText);
// "TextMustBe16Byte"
```


### CFB - Cipher Feedback 

```javascript
// An example 128-bit key
var key = [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16 ];

// The initialization vector (must be 16 bytes)
var iv = [ 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34,35, 36 ];

// Convert text to bytes (must be a multiple of the segment size you choose below)
var text = 'TextMustBeAMultipleOfSegmentSize';
var textBytes = aesjs.utils.utf8.toBytes(text);

// The segment size is optional, and defaults to 1
var segmentSize = 8;
var aesCfb = new aesjs.ModeOfOperation.cfb(key, iv, segmentSize);
var encryptedBytes = aesCfb.encrypt(textBytes);

// To print or store the binary data, you may convert it to hex
var encryptedHex = aesjs.utils.hex.fromBytes(encryptedBytes);
console.log(encryptedHex);
// "55e3af2638c560b4fdb9d26a630733ea60197ec23deb85b1f60f71f10409ce27"

// When ready to decrypt the hex string, convert it back to bytes
var encryptedBytes = aesjs.utils.hex.toBytes(encryptedHex);

// The cipher feedback mode of operation maintains internal state,
// so to decrypt a new instance must be instantiated.
var aesCfb = new aesjs.ModeOfOperation.cfb(key, iv, 8);
var decryptedBytes = aesCfb.decrypt(encryptedBytes);

// Convert our bytes back into text
var decryptedText = aesjs.utils.utf8.fromBytes(decryptedBytes);
console.log(decryptedText);
// "TextMustBeAMultipleOfSegmentSize"
```


### OFB - Output Feedback

```javascript
// An example 128-bit key
var key = [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16 ];

// The initialization vector (must be 16 bytes)
var iv = [ 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34,35, 36 ];

// Convert text to bytes
var text = 'Text may be any length you wish, no padding is required.';
var textBytes = aesjs.utils.utf8.toBytes(text);

var aesOfb = new aesjs.ModeOfOperation.ofb(key, iv);
var encryptedBytes = aesOfb.encrypt(textBytes);

// To print or store the binary data, you may convert it to hex
var encryptedHex = aesjs.utils.hex.fromBytes(encryptedBytes);
console.log(encryptedHex);
// "55e3af2655dd72b9f32456042f39bae9accff6259159e608be55a1aa313c598d
//  b4b18406d89c83841c9d1af13b56de8eda8fcfe9ec8e75e8"

// When ready to decrypt the hex string, convert it back to bytes
var encryptedBytes = aesjs.utils.hex.toBytes(encryptedHex);

// The output feedback mode of operation maintains internal state,
// so to decrypt a new instance must be instantiated.
var aesOfb = new aesjs.ModeOfOperation.ofb(key, iv);
var decryptedBytes = aesOfb.decrypt(encryptedBytes);

// Convert our bytes back into text
var decryptedText = aesjs.utils.utf8.fromBytes(decryptedBytes);
console.log(decryptedText);
// "Text may be any length you wish, no padding is required."
```


### ECB - Electronic Codebook (NOT recommended)

This mode is **not** recommended. Since, for a given key, the same plaintext block in produces the same ciphertext block out, this mode of operation can leak data, such as patterns. For more details and examples, see the Wikipedia article, [Electronic Codebook](http://en.wikipedia.org/wiki/Block_cipher_mode_of_operation#Electronic_Codebook_.28ECB.29).

```javascript
// An example 128-bit key
var key = [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16 ];

// Convert text to bytes
var text = 'TextMustBe16Byte';
var textBytes = aesjs.utils.utf8.toBytes(text);

var aesEcb = new aesjs.ModeOfOperation.ecb(key);
var encryptedBytes = aesEcb.encrypt(textBytes);

// To print or store the binary data, you may convert it to hex
var encryptedHex = aesjs.utils.hex.fromBytes(encryptedBytes);
console.log(encryptedHex);
// "a7d93b35368519fac347498dec18b458"

// When ready to decrypt the hex string, convert it back to bytes
var encryptedBytes = aesjs.utils.hex.toBytes(encryptedHex);

// Since electronic codebook does not store state, we can
// reuse the same instance.
//var aesEcb = new aesjs.ModeOfOperation.ecb(key);
var decryptedBytes = aesEcb.decrypt(encryptedBytes);

// Convert our bytes back into text
var decryptedText = aesjs.utils.utf8.fromBytes(decryptedBytes);
console.log(decryptedText);
// "TextMustBe16Byte"
```



Block Cipher
------------

You should usually use one of the above common modes of operation. Using the block cipher algorithm directly is also possible using **ECB** as that mode of operation is merely a thin wrapper.

But this might be useful to experiment with custom modes of operation or play with block cipher algorithms.

```javascript

// the AES block cipher algorithm works on 16 byte bloca ks, no more, no less
var text = "ABlockIs16Bytes!";
var textAsBytes = aesjs.utils.utf8.toBytes(text)
console.log(textAsBytes);
// [65, 66, 108, 111, 99, 107, 73, 115, 49, 54, 66, 121, 116, 101, 115, 33]

// create an instance of the block cipher algorithm
var key = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8, 9, 7, 9, 3];
var aes = new aesjs.AES(key);

// encrypt...
var encryptedBytes = aes.encrypt(textAsBytes);
console.log(encryptedBytes);
// [136, 15, 199, 174, 118, 133, 233, 177, 143, 47, 42, 211, 96, 55, 107, 109] 

// To print or store the binary data, you may convert it to hex
var encryptedHex = aesjs.utils.hex.fromBytes(encryptedBytes);
console.log(encryptedHex);
// "880fc7ae7685e9b18f2f2ad360376b6d"

// When ready to decrypt the hex string, convert it back to bytes
var encryptedBytes = aesjs.utils.hex.toBytes(encryptedHex);

// decrypt...
var decryptedBytes = aes.decrypt(encryptedBytes);
console.log(decryptedBytes);
// [65, 66, 108, 111, 99, 107, 73, 115, 49, 54, 66, 121, 116, 101, 115, 33]


// decode the bytes back into our original text
var decryptedText = aesjs.utils.utf8.fromBytes(decryptedBytes);
console.log(decryptedText);
// "ABlockIs16Bytes!"
```


Notes
=====

What is a Key
-------------

This seems to be a point of confusion for many people new to using encryption. You can think of the key as the *"password"*. However, these algorithms require the *"password"* to be a specific length.

With AES, there are three possible key lengths, 128-bit (16 bytes), 192-bit (24 bytes) or 256-bit (32 bytes). When you create an AES object, the key size is automatically detected, so it is important to pass in a key of the correct length.

Often, you wish to provide a password of arbitrary length, for example, something easy to remember or write down. In these cases, you must come up with a way to transform the password into a key of a specific length. A **Password-Based Key Derivation Function** (PBKDF) is an algorithm designed for this exact purpose.

Here is an example, using the popular (possibly obsolete?) pbkdf2:

```javascript
var pbkdf2 = require('pbkdf2');

var key_128 = pbkdf2.pbkdf2Sync('password', 'salt', 1, 128 / 8, 'sha512');
var key_192 = pbkdf2.pbkdf2Sync('password', 'salt', 1, 192 / 8, 'sha512');
var key_256 = pbkdf2.pbkdf2Sync('password', 'salt', 1, 256 / 8, 'sha512');
```

Another possibility, is to use a hashing function, such as SHA256 to hash the password, but this method is vulnerable to [Rainbow Attacks](http://en.wikipedia.org/wiki/Rainbow_table), unless you use a [salt](http://en.wikipedia.org/wiki/Salt_(cryptography)).

Performance
-----------

Todo...

Tests
-----

A test suite has been generated (`test/test-vectors.json`) from a known correct implementation, [pycrypto](https://www.dlitz.net/software/pycrypto/). To generate new test vectors, run `python generate-tests.py`.

To run the node.js test suite:

```
npm test
```

To run the web browser tests, open the `test/test.html` file in your browser.

FAQ
---

#### How do I get a question I have added?

E-mail me at aes-js@ricmoo.com with any questions, suggestions, comments, et cetera.


Donations
---------

Obviously, it's all licensed under the MIT license, so use it as you wish; but if you'd like to buy me a coffee, I won't complain. =)

- Bitcoin - `1K1Ax9t6uJmjE4X5xcoVuyVTsiLrYRqe2P`
- Ethereum - `0x70bDC274028F3f391E398dF8e3977De64FEcBf04`
