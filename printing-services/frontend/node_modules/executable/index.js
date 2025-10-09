'use strict';
const fs = require('fs');
const pify = require('pify');

const isExe = (mode, gid, uid) => {
	if (process.platform === 'win32') {
		return true;
	}

	const isGroup = gid ? process.getgid && gid === process.getgid() : true;
	const isUser = uid ? process.getuid && uid === process.getuid() : true;

	return Boolean((mode & 0o0001) ||
		((mode & 0o0010) && isGroup) ||
		((mode & 0o0100) && isUser));
};

module.exports = name => {
	if (typeof name !== 'string') {
		return Promise.reject(new TypeError('Expected a string'));
	}

	return pify(fs.stat)(name).then(stats => stats && stats.isFile() && isExe(stats.mode, stats.gid, stats.uid));
};

module.exports.sync = name => {
	if (typeof name !== 'string') {
		throw new TypeError('Expected a string');
	}

	const stats = fs.statSync(name);

	return stats && stats.isFile() && isExe(stats.mode, stats.gid, stats.uid);
};

module.exports.checkMode = isExe;
