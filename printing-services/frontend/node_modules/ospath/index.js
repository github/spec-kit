var path = require('path')
var os = require('os')

function data () {
  switch (this.__platform || process.platform) {
    case 'win32': return path.resolve(process.env.APPDATA)
    case 'darwin': return path.resolve(path.join(home.call(this), 'Library/Application Support/'))
    default: return process.env.XDG_CONFIG_HOME
      ? path.resolve(process.env.XDG_CONFIG_HOME)
      : path.resolve(path.join(home.call(this), '.config/'))
  }
}

function desktop () {
  return path.join(home.call(this), 'Desktop')
}

function home () {
  // io.js >= 2.3
  if ('homedir' in os) return os.homedir()

  switch (this.__platform || process.platform) {
    case 'win32': return path.resolve(process.env.USERPROFILE)
    default: return path.resolve(process.env.HOME)
  }
}

function tmp () {
  switch (this.__platform || process.platform) {
    case 'win32': return path.resolve(process.env.TEMP)
    default: return path.resolve('/tmp')
  }
}

var ospath = {
  __platform: process.platform,
  data: data,
  desktop: desktop,
  home: home,
  tmp: tmp
}

module.exports = ospath
