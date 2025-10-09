# Changelog

## not yet released

None yet.

## v2.0.2 (2021-11-16)

* #30 json-schema dep is vulnerable to prototype pollution
      See also https://security.snyk.io/vuln/SNYK-JS-JSONSCHEMA-1920922

## v2.0.1 (2021-11-03)

* Remove use of `git://` URLs.
## v2.0.0 (2017-10-25)

Major bump due to a change in the semantics of `deepEqual`. Code that relies on
`deepEqual` to fail if inherited properties are present on the objects compared
should be updated accordingly.

* #24 `deepEqual` is incorrect when there are inherited properties

## v1.4.1 (2017-08-02)

* #21 Update verror dep
* #22 Update extsprintf dependency
* #23 update contribution guidelines

## v1.4.0 (2017-03-13)

* #7 Add parseInteger() function for safer number parsing

## v1.3.1 (2016-09-12)

* #13 Incompatible with webpack

## v1.3.0 (2016-06-22)

* #14 add safer version of hasOwnProperty()
* #15 forEachKey() should ignore inherited properties

## v1.2.2 (2015-10-15)

* #11 NPM package shouldn't include any code that does `require('JSV')`
* #12 jsl.node.conf missing definition for "module"

## v1.2.1 (2015-10-14)

* #8 odd date parsing behaviour

## v1.2.0 (2015-10-13)

* #9 want function for returning RFC1123 dates

## v1.1.0 (2015-09-02)

* #6 a new suite of hrtime manipulation routines: `hrtimeAdd()`,
  `hrtimeAccum()`, `hrtimeNanosec()`, `hrtimeMicrosec()` and
  `hrtimeMillisec()`.

## v1.0.0 (2015-09-01)

First tracked release.  Includes everything in previous releases, plus:

* #4 want function for merging objects
