/**
Check if your package was installed globally.

@example
```
import isInstalledGlobally = require('is-installed-globally');

// With `npm install your-package`
console.log(isInstalledGlobally);
//=> false

// With `npm install --global your-package`
console.log(isInstalledGlobally);
//=> true
```
*/
declare const isInstalledGlobally: boolean;

export = isInstalledGlobally;
