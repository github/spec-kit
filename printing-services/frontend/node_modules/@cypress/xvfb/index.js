/* eslint-disable node/no-deprecated-api */

'use strict'

// our debug log messages
const debug = require('debug')('xvfb')
const once = require('lodash.once')
const fs = require('fs')
const path = require('path')
const spawn = require('child_process').spawn
fs.exists = fs.exists || path.exists
fs.existsSync = fs.existsSync || path.existsSync

function Xvfb(options) {
  options = options || {}
  this._display = options.displayNum ? `:${options.displayNum}` : null
  this._reuse = options.reuse
  this._timeout = options.timeout || options.timeOut || 2000
  this._silent = options.silent
  this._onStderrData = options.onStderrData || (() => {})
  this._xvfb_args = options.xvfb_args || []
}

Xvfb.prototype = {
  start(cb) {
    let self = this

    if (!self._process) {
      let lockFile = self._lockFile()

      self._setDisplayEnvVariable()

      fs.exists(lockFile, function(exists) {
        let didSpawnFail = false
        try {
          self._spawnProcess(exists, function(e) {
            debug('XVFB spawn failed')
            debug(e)
            didSpawnFail = true
            if (cb) cb(e)
          })
        } catch (e) {
          debug('spawn process error')
          debug(e)
          return cb && cb(e)
        }

        let totalTime = 0
        ;(function checkIfStarted() {
          debug('checking if started by looking for the lock file', lockFile)
          fs.exists(lockFile, function(exists) {
            if (didSpawnFail) {
              // When spawn fails, the callback will immediately be called.
              // So we don't have to check whether the lock file exists.
              debug('while checking for lock file, saw that spawn failed')
              return
            }
            if (exists) {
              debug('lock file %s found after %d ms', lockFile, totalTime)
              return cb && cb(null, self._process)
            } else {
              totalTime += 10
              if (totalTime > self._timeout) {
                debug(
                  'could not start XVFB after %d ms (timeout %d ms)',
                  totalTime,
                  self._timeout
                )
                const err = new Error('Could not start Xvfb.')
                err.timedOut = true
                return cb && cb(err)
              } else {
                setTimeout(checkIfStarted, 10)
              }
            }
          })
        })()
      })
    }
  },

  stop(cb) {
    let self = this

    if (self._process) {
      self._killProcess()
      self._restoreDisplayEnvVariable()

      let lockFile = self._lockFile()
      debug('lock file', lockFile)
      let totalTime = 0
      ;(function checkIfStopped() {
        fs.exists(lockFile, function(exists) {
          if (!exists) {
            debug('lock file %s not found when stopping', lockFile)
            return cb && cb(null, self._process)
          } else {
            totalTime += 10
            if (totalTime > self._timeout) {
              debug('lock file %s is still there', lockFile)
              debug(
                'after waiting for %d ms (timeout %d ms)',
                totalTime,
                self._timeout
              )
              const err = new Error('Could not stop Xvfb.')
              err.timedOut = true
              return cb && cb(err)
            } else {
              setTimeout(checkIfStopped, 10)
            }
          }
        })
      })()
    } else {
      return cb && cb(null)
    }
  },

  display() {
    if (!this._display) {
      let displayNum = 98
      let lockFile
      do {
        displayNum++
        lockFile = this._lockFile(displayNum)
      } while (!this._reuse && fs.existsSync(lockFile))
      this._display = `:${displayNum}`
    }

    return this._display
  },

  _setDisplayEnvVariable() {
    this._oldDisplay = process.env.DISPLAY
    process.env.DISPLAY = this.display()
    debug('setting DISPLAY %s', process.env.DISPLAY)
  },

  _restoreDisplayEnvVariable() {
    debug('restoring process.env.DISPLAY variable')
    // https://github.com/cypress-io/xvfb/issues/1
    // only reset truthy backed' up values
    if (this._oldDisplay) {
      process.env.DISPLAY = this._oldDisplay
    } else {
      // else delete the values to get back
      // to undefined
      delete process.env.DISPLAY
    }
  },

  _spawnProcess(lockFileExists, onAsyncSpawnError) {
    let self = this

    const onError = once(onAsyncSpawnError)

    let display = self.display()
    if (lockFileExists) {
      if (!self._reuse) {
        throw new Error(
          `Display ${display} is already in use and the "reuse" option is false.`
        )
      }
    } else {
      const stderr = []

      const allArguments = [display].concat(self._xvfb_args)
      debug('all Xvfb arguments', allArguments)

      self._process = spawn('Xvfb', allArguments)
      self._process.stderr.on('data', function(data) {
        stderr.push(data.toString())

        if (self._silent) {
          return
        }

        self._onStderrData(data)
      })

      self._process.on('close', (code, signal) => {
        if (code !== 0) {
          const str = stderr.join('\n')
          debug('xvfb closed with error code', code)
          debug('after receiving signal %s', signal)
          debug('and stderr output')
          debug(str)
          const err = new Error(str)
          err.nonZeroExitCode = true
          onError(err)
        }
      })

      // Bind an error listener to prevent an error from crashing node.
      self._process.once('error', function(e) {
        debug('xvfb spawn process error')
        debug(e)
        onError(e)
      })
    }
  },

  _killProcess() {
    this._process.kill()
    this._process = null
  },

  _lockFile(displayNum) {
    displayNum =
      displayNum ||
      this.display()
        .toString()
        .replace(/^:/, '')
    const filename = `/tmp/.X${displayNum}-lock`
    debug('lock filename %s', filename)
    return filename
  },
}

module.exports = Xvfb
