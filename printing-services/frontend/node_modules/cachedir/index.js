const os = require('os')
const path = require('path')

function posix (id) {
  const cacheHome = process.env.XDG_CACHE_HOME || path.join(os.homedir(), '.cache')
  return path.join(cacheHome, id)
}

function darwin (id) {
  return path.join(os.homedir(), 'Library', 'Caches', id)
}

function win32 (id) {
  const appData = process.env.LOCALAPPDATA || path.join(os.homedir(), 'AppData', 'Local')
  return path.join(appData, id, 'Cache')
}

const implementation = (function () {
  switch (os.platform()) {
    case 'darwin':
      return darwin
    case 'win32':
      return win32
    case 'aix':
    case 'android':
    case 'freebsd':
    case 'linux':
    case 'netbsd':
    case 'openbsd':
    case 'sunos':
      return posix
    default:
      console.error(`(node:${process.pid}) [cachedir] Warning: the platform "${os.platform()}" is not currently supported by node-cachedir, falling back to "posix". Please file an issue with your platform here: https://github.com/LinusU/node-cachedir/issues/new`)
      return posix
  }
}())

module.exports = function cachedir (id) {
  if (typeof id !== 'string') {
    throw new TypeError('id is not a string')
  }
  if (id.length === 0) {
    throw new Error('id cannot be empty')
  }
  if (/[^0-9a-zA-Z-]/.test(id)) {
    throw new Error('id cannot contain special characters')
  }

  return implementation(id)
}
