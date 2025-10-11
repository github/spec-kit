import data from './data/bidiBrackets.data.js'
import { parseCharacterMap } from './util/parseCharacterMap.js'

let openToClose, closeToOpen, canonical

function parse () {
  if (!openToClose) {
    //const start = performance.now()
    let { map, reverseMap } = parseCharacterMap(data.pairs, true)
    openToClose = map
    closeToOpen = reverseMap
    canonical = parseCharacterMap(data.canonical, false).map
    //console.log(`brackets parsed in ${performance.now() - start}ms`)
  }
}

export function openingToClosingBracket (char) {
  parse()
  return openToClose.get(char) || null
}

export function closingToOpeningBracket (char) {
  parse()
  return closeToOpen.get(char) || null
}

export function getCanonicalBracket (char) {
  parse()
  return canonical.get(char) || null
}
