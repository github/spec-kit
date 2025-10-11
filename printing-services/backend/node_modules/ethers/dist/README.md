Distribution Folder
===================

The contents of this folder are for using `import` in ESM
browser-base projects.

The `ethers.js` (and `ethers.min.js`) files only include the
English wordlist to conserve space.

For additional Wordlist support, the `wordlist-extra.js` (and
`wordlist-extra.min.js`) should be imported too.


Notes
-----

The contents are generated via the `npm build dist` target using
`rollup` and the `/rollup.config.js` configuration.

Do not modify the files in this folder. They are deleted on `build-clean`.

To modify this `README.md`, see the `/output/post-build/dist`.
