/* eslint-env mocha */

const assert = require('assert')
const os = require('os')
const proxyquire = require('proxyquire')

const platforms = [
  ['aix', `${os.homedir()}/.cache/linusu`],
  ['darwin', `${os.homedir()}/Library/Caches/linusu`],
  ['freebsd', `${os.homedir()}/.cache/linusu`],
  ['linux', `${os.homedir()}/.cache/linusu`],
  ['netbsd', `${os.homedir()}/.cache/linusu`],
  ['openbsd', `${os.homedir()}/.cache/linusu`],
  ['sunos', `${os.homedir()}/.cache/linusu`],
  ['win32', `${os.homedir()}/AppData/Local/linusu/Cache`]
]

platforms.forEach((platform) => {
  describe(platform[0], () => {
    let cachedir

    before(() => {
      const os = {
        platform () { return platform[0] }
      }

      cachedir = proxyquire('./', { os })
    })

    it('should give the correct path', () => {
      const actual = cachedir('linusu')
      const expected = platform[1]

      assert.strictEqual(actual, expected)
    })

    if (platform[0] === 'win32') {
      describe('when LOCALAPPDATA is set', () => {
        it('should give the correct path', () => {
          const oldLocalAppData = process.env.LOCALAPPDATA
          process.env.LOCALAPPDATA = 'X:/LocalAppData'
          const actual = cachedir('linusu')
          process.env.LOCALAPPDATA = oldLocalAppData
          const expected = 'X:/LocalAppData/linusu/Cache'

          assert.strictEqual(actual, expected)
        })
      })
    }

    it('should throw on bad input', () => {
      assert.throws(() => cachedir())
      assert.throws(() => cachedir(''))
      assert.throws(() => cachedir({}))
      assert.throws(() => cachedir([]))
      assert.throws(() => cachedir(null))
      assert.throws(() => cachedir(1337))
      assert.throws(() => cachedir('test!!'))
      assert.throws(() => cachedir(undefined))
    })
  })
})

describe('fallback', () => {
  it('should fallback to posix with warning', () => {
    const originalError = console.error

    try {
      const logs = []
      console.error = (msg) => logs.push(msg)

      const os = { platform: () => 'test' }
      const cachedir = proxyquire('./', { os })

      const actual = cachedir('linusu')
      const expected = `${os.homedir()}/.cache/linusu`
      assert.strictEqual(actual, expected)

      assert.deepStrictEqual(logs, [
        `(node:${process.pid}) [cachedir] Warning: the platform "test" is not currently supported by node-cachedir, falling back to "posix". Please file an issue with your platform here: https://github.com/LinusU/node-cachedir/issues/new`
      ])
    } finally {
      console.error = originalError
    }
  })
})
