import data from './data/bidiMirroring.data.js'
import { parseCharacterMap } from './util/parseCharacterMap.js'

let mirrorMap

function parse () {
  if (!mirrorMap) {
    //const start = performance.now()
    const { map, reverseMap } = parseCharacterMap(data, true)
    // Combine both maps into one
    reverseMap.forEach((value, key) => {
      map.set(key, value)
    })
    mirrorMap = map
    //console.log(`mirrored chars parsed in ${performance.now() - start}ms`)
  }
}

export function getMirroredCharacter (char) {
  parse()
  return mirrorMap.get(char) || null
}

/**
 * Given a string and its resolved embedding levels, build a map of indices to replacement chars
 * for any characters in right-to-left segments that have defined mirrored characters.
 * @param string
 * @param embeddingLevels
 * @param [start]
 * @param [end]
 * @return {Map<number, string>}
 */
export function getMirroredCharactersMap(string, embeddingLevels, start, end) {
  let strLen = string.length
  start = Math.max(0, start == null ? 0 : +start)
  end = Math.min(strLen - 1, end == null ? strLen - 1 : +end)

  const map = new Map()
  for (let i = start; i <= end; i++) {
    if (embeddingLevels[i] & 1) { //only odd (rtl) levels
      const mirror = getMirroredCharacter(string[i])
      if (mirror !== null) {
        map.set(i, mirror)
      }
    }
  }
  return map
}
