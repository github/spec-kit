'use strict';
const fs = require('fs');
const globalDirs = require('global-dirs');
const isPathInside = require('is-path-inside');

module.exports = (() => {
	try {
		return (
			isPathInside(__dirname, globalDirs.yarn.packages) ||
			isPathInside(__dirname, fs.realpathSync(globalDirs.npm.packages))
		);
	} catch {
		return false;
	}
})();
