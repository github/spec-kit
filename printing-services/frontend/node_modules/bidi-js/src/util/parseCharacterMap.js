/**
 * Parses an string that holds encoded codepoint mappings, e.g. for bracket pairs or
 * mirroring characters, as encoded by scripts/generateBidiData.js. Returns an object
 * holding the `map`, and optionally a `reverseMap` if `includeReverse:true`.
 * @param {string} encodedString
 * @param {boolean} includeReverse - true if you want reverseMap in the output
 * @return {{map: Map<number, number>, reverseMap?: Map<number, number>}}
 */
export function parseCharacterMap (encodedString, includeReverse) {
  const radix = 36
  let lastCode = 0
  const map = new Map()
  const reverseMap = includeReverse && new Map()
  let prevPair
  encodedString.split(',').forEach(function visit(entry) {
    if (entry.indexOf('+') !== -1) {
      for (let i = +entry; i--;) {
        visit(prevPair)
      }
    } else {
      prevPair = entry
      let [a, b] = entry.split('>')
      a = String.fromCodePoint(lastCode += parseInt(a, radix))
      b = String.fromCodePoint(lastCode += parseInt(b, radix))
      map.set(a, b)
      includeReverse && reverseMap.set(b, a)
    }
  })
  return { map, reverseMap }
}
