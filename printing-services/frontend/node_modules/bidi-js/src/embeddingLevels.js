import {
  BN_LIKE_TYPES,
  getBidiCharType,
  ISOLATE_INIT_TYPES,
  NEUTRAL_ISOLATE_TYPES,
  STRONG_TYPES,
  TRAILING_TYPES,
  TYPES
} from './charTypes.js'
import { closingToOpeningBracket, getCanonicalBracket, openingToClosingBracket } from './brackets.js'

// Local type aliases
const {
  L: TYPE_L,
  R: TYPE_R,
  EN: TYPE_EN,
  ES: TYPE_ES,
  ET: TYPE_ET,
  AN: TYPE_AN,
  CS: TYPE_CS,
  B: TYPE_B,
  S: TYPE_S,
  ON: TYPE_ON,
  BN: TYPE_BN,
  NSM: TYPE_NSM,
  AL: TYPE_AL,
  LRO: TYPE_LRO,
  RLO: TYPE_RLO,
  LRE: TYPE_LRE,
  RLE: TYPE_RLE,
  PDF: TYPE_PDF,
  LRI: TYPE_LRI,
  RLI: TYPE_RLI,
  FSI: TYPE_FSI,
  PDI: TYPE_PDI
} = TYPES

/**
 * @typedef {object} GetEmbeddingLevelsResult
 * @property {{start, end, level}[]} paragraphs
 * @property {Uint8Array} levels
 */

/**
 * This function applies the Bidirectional Algorithm to a string, returning the resolved embedding levels
 * in a single Uint8Array plus a list of objects holding each paragraph's start and end indices and resolved
 * base embedding level.
 *
 * @param {string} string - The input string
 * @param {"ltr"|"rtl"|"auto"} [baseDirection] - Use "ltr" or "rtl" to force a base paragraph direction,
 *        otherwise a direction will be chosen automatically from each paragraph's contents.
 * @return {GetEmbeddingLevelsResult}
 */
export function getEmbeddingLevels (string, baseDirection) {
  const MAX_DEPTH = 125

  // Start by mapping all characters to their unicode type, as a bitmask integer
  const charTypes = new Uint32Array(string.length)
  for (let i = 0; i < string.length; i++) {
    charTypes[i] = getBidiCharType(string[i])
  }

  const charTypeCounts = new Map() //will be cleared at start of each paragraph
  function changeCharType(i, type) {
    const oldType = charTypes[i]
    charTypes[i] = type
    charTypeCounts.set(oldType, charTypeCounts.get(oldType) - 1)
    if (oldType & NEUTRAL_ISOLATE_TYPES) {
      charTypeCounts.set(NEUTRAL_ISOLATE_TYPES, charTypeCounts.get(NEUTRAL_ISOLATE_TYPES) - 1)
    }
    charTypeCounts.set(type, (charTypeCounts.get(type) || 0) + 1)
    if (type & NEUTRAL_ISOLATE_TYPES) {
      charTypeCounts.set(NEUTRAL_ISOLATE_TYPES, (charTypeCounts.get(NEUTRAL_ISOLATE_TYPES) || 0) + 1)
    }
  }

  const embedLevels = new Uint8Array(string.length)
  const isolationPairs = new Map() //init->pdi and pdi->init

  // === 3.3.1 The Paragraph Level ===
  // 3.3.1 P1: Split the text into paragraphs
  const paragraphs = [] // [{start, end, level}, ...]
  let paragraph = null
  for (let i = 0; i < string.length; i++) {
    if (!paragraph) {
      paragraphs.push(paragraph = {
        start: i,
        end: string.length - 1,
        // 3.3.1 P2-P3: Determine the paragraph level
        level: baseDirection === 'rtl' ? 1 : baseDirection === 'ltr' ? 0 : determineAutoEmbedLevel(i, false)
      })
    }
    if (charTypes[i] & TYPE_B) {
      paragraph.end = i
      paragraph = null
    }
  }

  const FORMATTING_TYPES = TYPE_RLE | TYPE_LRE | TYPE_RLO | TYPE_LRO | ISOLATE_INIT_TYPES | TYPE_PDI | TYPE_PDF | TYPE_B
  const nextEven = n => n + ((n & 1) ? 1 : 2)
  const nextOdd = n => n + ((n & 1) ? 2 : 1)

  // Everything from here on will operate per paragraph.
  for (let paraIdx = 0; paraIdx < paragraphs.length; paraIdx++) {
    paragraph = paragraphs[paraIdx]
    const statusStack = [{
      _level: paragraph.level,
      _override: 0, //0=neutral, 1=L, 2=R
      _isolate: 0 //bool
    }]
    let stackTop
    let overflowIsolateCount = 0
    let overflowEmbeddingCount = 0
    let validIsolateCount = 0
    charTypeCounts.clear()

    // === 3.3.2 Explicit Levels and Directions ===
    for (let i = paragraph.start; i <= paragraph.end; i++) {
      let charType = charTypes[i]
      stackTop = statusStack[statusStack.length - 1]

      // Set initial counts
      charTypeCounts.set(charType, (charTypeCounts.get(charType) || 0) + 1)
      if (charType & NEUTRAL_ISOLATE_TYPES) {
        charTypeCounts.set(NEUTRAL_ISOLATE_TYPES, (charTypeCounts.get(NEUTRAL_ISOLATE_TYPES) || 0) + 1)
      }

      // Explicit Embeddings: 3.3.2 X2 - X3
      if (charType & FORMATTING_TYPES) { //prefilter all formatters
        if (charType & (TYPE_RLE | TYPE_LRE)) {
          embedLevels[i] = stackTop._level // 5.2
          const level = (charType === TYPE_RLE ? nextOdd : nextEven)(stackTop._level)
          if (level <= MAX_DEPTH && !overflowIsolateCount && !overflowEmbeddingCount) {
            statusStack.push({
              _level: level,
              _override: 0,
              _isolate: 0
            })
          } else if (!overflowIsolateCount) {
            overflowEmbeddingCount++
          }
        }

        // Explicit Overrides: 3.3.2 X4 - X5
        else if (charType & (TYPE_RLO | TYPE_LRO)) {
          embedLevels[i] = stackTop._level // 5.2
          const level = (charType === TYPE_RLO ? nextOdd : nextEven)(stackTop._level)
          if (level <= MAX_DEPTH && !overflowIsolateCount && !overflowEmbeddingCount) {
            statusStack.push({
              _level: level,
              _override: (charType & TYPE_RLO) ? TYPE_R : TYPE_L,
              _isolate: 0
            })
          } else if (!overflowIsolateCount) {
            overflowEmbeddingCount++
          }
        }

        // Isolates: 3.3.2 X5a - X5c
        else if (charType & ISOLATE_INIT_TYPES) {
          // X5c - FSI becomes either RLI or LRI
          if (charType & TYPE_FSI) {
            charType = determineAutoEmbedLevel(i + 1, true) === 1 ? TYPE_RLI : TYPE_LRI
          }

          embedLevels[i] = stackTop._level
          if (stackTop._override) {
            changeCharType(i, stackTop._override)
          }
          const level = (charType === TYPE_RLI ? nextOdd : nextEven)(stackTop._level)
          if (level <= MAX_DEPTH && overflowIsolateCount === 0 && overflowEmbeddingCount === 0) {
            validIsolateCount++
            statusStack.push({
              _level: level,
              _override: 0,
              _isolate: 1,
              _isolInitIndex: i
            })
          } else {
            overflowIsolateCount++
          }
        }

        // Terminating Isolates: 3.3.2 X6a
        else if (charType & TYPE_PDI) {
          if (overflowIsolateCount > 0) {
            overflowIsolateCount--
          } else if (validIsolateCount > 0) {
            overflowEmbeddingCount = 0
            while (!statusStack[statusStack.length - 1]._isolate) {
              statusStack.pop()
            }
            // Add to isolation pairs bidirectional mapping:
            const isolInitIndex = statusStack[statusStack.length - 1]._isolInitIndex
            if (isolInitIndex != null) {
              isolationPairs.set(isolInitIndex, i)
              isolationPairs.set(i, isolInitIndex)
            }
            statusStack.pop()
            validIsolateCount--
          }
          stackTop = statusStack[statusStack.length - 1]
          embedLevels[i] = stackTop._level
          if (stackTop._override) {
            changeCharType(i, stackTop._override)
          }
        }


        // Terminating Embeddings and Overrides: 3.3.2 X7
        else if (charType & TYPE_PDF) {
          if (overflowIsolateCount === 0) {
            if (overflowEmbeddingCount > 0) {
              overflowEmbeddingCount--
            } else if (!stackTop._isolate && statusStack.length > 1) {
              statusStack.pop()
              stackTop = statusStack[statusStack.length - 1]
            }
          }
          embedLevels[i] = stackTop._level // 5.2
        }

        // End of Paragraph: 3.3.2 X8
        else if (charType & TYPE_B) {
          embedLevels[i] = paragraph.level
        }
      }

      // Non-formatting characters: 3.3.2 X6
      else {
        embedLevels[i] = stackTop._level
        // NOTE: This exclusion of BN seems to go against what section 5.2 says, but is required for test passage
        if (stackTop._override && charType !== TYPE_BN) {
          changeCharType(i, stackTop._override)
        }
      }
    }

    // === 3.3.3 Preparations for Implicit Processing ===

    // Remove all RLE, LRE, RLO, LRO, PDF, and BN characters: 3.3.3 X9
    // Note: Due to section 5.2, we won't remove them, but we'll use the BN_LIKE_TYPES bitset to
    // easily ignore them all from here on out.

    // 3.3.3 X10
    // Compute the set of isolating run sequences as specified by BD13
    const levelRuns = []
    let currentRun = null
    let isolationLevel = 0
    for (let i = paragraph.start; i <= paragraph.end; i++) {
      const charType = charTypes[i]
      if (!(charType & BN_LIKE_TYPES)) {
        const lvl = embedLevels[i]
        const isIsolInit = charType & ISOLATE_INIT_TYPES
        const isPDI = charType === TYPE_PDI
        if (isIsolInit) {
          isolationLevel++
        }
        if (currentRun && lvl === currentRun._level) {
          currentRun._end = i
          currentRun._endsWithIsolInit = isIsolInit
        } else {
          levelRuns.push(currentRun = {
            _start: i,
            _end: i,
            _level: lvl,
            _startsWithPDI: isPDI,
            _endsWithIsolInit: isIsolInit
          })
        }
        if (isPDI) {
          isolationLevel--
        }
      }
    }
    const isolatingRunSeqs = [] // [{seqIndices: [], sosType: L|R, eosType: L|R}]
    for (let runIdx = 0; runIdx < levelRuns.length; runIdx++) {
      const run = levelRuns[runIdx]
      if (!run._startsWithPDI || (run._startsWithPDI && !isolationPairs.has(run._start))) {
        const seqRuns = [currentRun = run]
        for (let pdiIndex; currentRun && currentRun._endsWithIsolInit && (pdiIndex = isolationPairs.get(currentRun._end)) != null;) {
          for (let i = runIdx + 1; i < levelRuns.length; i++) {
            if (levelRuns[i]._start === pdiIndex) {
              seqRuns.push(currentRun = levelRuns[i])
              break
            }
          }
        }
        // build flat list of indices across all runs:
        const seqIndices = []
        for (let i = 0; i < seqRuns.length; i++) {
          const run = seqRuns[i]
          for (let j = run._start; j <= run._end; j++) {
            seqIndices.push(j)
          }
        }
        // determine the sos/eos types:
        let firstLevel = embedLevels[seqIndices[0]]
        let prevLevel = paragraph.level
        for (let i = seqIndices[0] - 1; i >= 0; i--) {
          if (!(charTypes[i] & BN_LIKE_TYPES)) { //5.2
            prevLevel = embedLevels[i]
            break
          }
        }
        const lastIndex = seqIndices[seqIndices.length - 1]
        let lastLevel = embedLevels[lastIndex]
        let nextLevel = paragraph.level
        if (!(charTypes[lastIndex] & ISOLATE_INIT_TYPES)) {
          for (let i = lastIndex + 1; i <= paragraph.end; i++) {
            if (!(charTypes[i] & BN_LIKE_TYPES)) { //5.2
              nextLevel = embedLevels[i]
              break
            }
          }
        }
        isolatingRunSeqs.push({
          _seqIndices: seqIndices,
          _sosType: Math.max(prevLevel, firstLevel) % 2 ? TYPE_R : TYPE_L,
          _eosType: Math.max(nextLevel, lastLevel) % 2 ? TYPE_R : TYPE_L
        })
      }
    }

    // The next steps are done per isolating run sequence
    for (let seqIdx = 0; seqIdx < isolatingRunSeqs.length; seqIdx++) {
      const { _seqIndices: seqIndices, _sosType: sosType, _eosType: eosType } = isolatingRunSeqs[seqIdx]
      /**
       * All the level runs in an isolating run sequence have the same embedding level.
       * 
       * DO NOT change any `embedLevels[i]` within the current scope.
       */
      const embedDirection = ((embedLevels[seqIndices[0]]) & 1) ? TYPE_R : TYPE_L;

      // === 3.3.4 Resolving Weak Types ===

      // W1 + 5.2. Search backward from each NSM to the first character in the isolating run sequence whose
      // bidirectional type is not BN, and set the NSM to ON if it is an isolate initiator or PDI, and to its
      // type otherwise. If the NSM is the first non-BN character, change the NSM to the type of sos.
      if (charTypeCounts.get(TYPE_NSM)) {
        for (let si = 0; si < seqIndices.length; si++) {
          const i = seqIndices[si]
          if (charTypes[i] & TYPE_NSM) {
            let prevType = sosType
            for (let sj = si - 1; sj >= 0; sj--) {
              if (!(charTypes[seqIndices[sj]] & BN_LIKE_TYPES)) { //5.2 scan back to first non-BN
                prevType = charTypes[seqIndices[sj]]
                break
              }
            }
            changeCharType(i, (prevType & (ISOLATE_INIT_TYPES | TYPE_PDI)) ? TYPE_ON : prevType)
          }
        }
      }

      // W2. Search backward from each instance of a European number until the first strong type (R, L, AL, or sos)
      // is found. If an AL is found, change the type of the European number to Arabic number.
      if (charTypeCounts.get(TYPE_EN)) {
        for (let si = 0; si < seqIndices.length; si++) {
          const i = seqIndices[si]
          if (charTypes[i] & TYPE_EN) {
            for (let sj = si - 1; sj >= -1; sj--) {
              const prevCharType = sj === -1 ? sosType : charTypes[seqIndices[sj]]
              if (prevCharType & STRONG_TYPES) {
                if (prevCharType === TYPE_AL) {
                  changeCharType(i, TYPE_AN)
                }
                break
              }
            }
          }
        }
      }

      // W3. Change all ALs to R
      if (charTypeCounts.get(TYPE_AL)) {
        for (let si = 0; si < seqIndices.length; si++) {
          const i = seqIndices[si]
          if (charTypes[i] & TYPE_AL) {
            changeCharType(i, TYPE_R)
          }
        }
      }

      // W4. A single European separator between two European numbers changes to a European number. A single common
      // separator between two numbers of the same type changes to that type.
      if (charTypeCounts.get(TYPE_ES) || charTypeCounts.get(TYPE_CS)) {
        for (let si = 1; si < seqIndices.length - 1; si++) {
          const i = seqIndices[si]
          if (charTypes[i] & (TYPE_ES | TYPE_CS)) {
            let prevType = 0, nextType = 0
            for (let sj = si - 1; sj >= 0; sj--) {
              prevType = charTypes[seqIndices[sj]]
              if (!(prevType & BN_LIKE_TYPES)) { //5.2
                break
              }
            }
            for (let sj = si + 1; sj < seqIndices.length; sj++) {
              nextType = charTypes[seqIndices[sj]]
              if (!(nextType & BN_LIKE_TYPES)) { //5.2
                break
              }
            }
            if (prevType === nextType && (charTypes[i] === TYPE_ES ? prevType === TYPE_EN : (prevType & (TYPE_EN | TYPE_AN)))) {
              changeCharType(i, prevType)
            }
          }
        }
      }

      // W5. A sequence of European terminators adjacent to European numbers changes to all European numbers.
      if (charTypeCounts.get(TYPE_EN)) {
        for (let si = 0; si < seqIndices.length; si++) {
          const i = seqIndices[si]
          if (charTypes[i] & TYPE_EN) {
            for (let sj = si - 1; sj >= 0 && (charTypes[seqIndices[sj]] & (TYPE_ET | BN_LIKE_TYPES)); sj--) {
              changeCharType(seqIndices[sj], TYPE_EN)
            }
            for (si++; si < seqIndices.length && (charTypes[seqIndices[si]] & (TYPE_ET | BN_LIKE_TYPES | TYPE_EN)); si++) {
              if (charTypes[seqIndices[si]] !== TYPE_EN) {
                changeCharType(seqIndices[si], TYPE_EN)
              }
            }
          }
        }
      }

      // W6. Otherwise, separators and terminators change to Other Neutral.
      if (charTypeCounts.get(TYPE_ET) || charTypeCounts.get(TYPE_ES) || charTypeCounts.get(TYPE_CS)) {
        for (let si = 0; si < seqIndices.length; si++) {
          const i = seqIndices[si]
          if (charTypes[i] & (TYPE_ET | TYPE_ES | TYPE_CS)) {
            changeCharType(i, TYPE_ON)
            // 5.2 transform adjacent BNs too:
            for (let sj = si - 1; sj >= 0 && (charTypes[seqIndices[sj]] & BN_LIKE_TYPES); sj--) {
              changeCharType(seqIndices[sj], TYPE_ON)
            }
            for (let sj = si + 1; sj < seqIndices.length && (charTypes[seqIndices[sj]] & BN_LIKE_TYPES); sj++) {
              changeCharType(seqIndices[sj], TYPE_ON)
            }
          }
        }
      }

      // W7. Search backward from each instance of a European number until the first strong type (R, L, or sos)
      // is found. If an L is found, then change the type of the European number to L.
      // NOTE: implemented in single forward pass for efficiency
      if (charTypeCounts.get(TYPE_EN)) {
        for (let si = 0, prevStrongType = sosType; si < seqIndices.length; si++) {
          const i = seqIndices[si]
          const type = charTypes[i]
          if (type & TYPE_EN) {
            if (prevStrongType === TYPE_L) {
              changeCharType(i, TYPE_L)
            }
          } else if (type & STRONG_TYPES) {
            prevStrongType = type
          }
        }
      }

      // === 3.3.5 Resolving Neutral and Isolate Formatting Types ===

      if (charTypeCounts.get(NEUTRAL_ISOLATE_TYPES)) {
        // N0. Process bracket pairs in an isolating run sequence sequentially in the logical order of the text
        // positions of the opening paired brackets using the logic given below. Within this scope, bidirectional
        // types EN and AN are treated as R.
        const R_TYPES_FOR_N_STEPS = (TYPE_R | TYPE_EN | TYPE_AN)
        const STRONG_TYPES_FOR_N_STEPS = R_TYPES_FOR_N_STEPS | TYPE_L

        // * Identify the bracket pairs in the current isolating run sequence according to BD16.
        const bracketPairs = []
        {
          const openerStack = []
          for (let si = 0; si < seqIndices.length; si++) {
            // NOTE: for any potential bracket character we also test that it still carries a NI
            // type, as that may have been changed earlier. This doesn't seem to be explicitly
            // called out in the spec, but is required for passage of certain tests.
            if (charTypes[seqIndices[si]] & NEUTRAL_ISOLATE_TYPES) {
              const char = string[seqIndices[si]]
              let oppositeBracket
              // Opening bracket
              if (openingToClosingBracket(char) !== null) {
                if (openerStack.length < 63) {
                  openerStack.push({ char, seqIndex: si })
                } else {
                  break
                }
              }
              // Closing bracket
              else if ((oppositeBracket = closingToOpeningBracket(char)) !== null) {
                for (let stackIdx = openerStack.length - 1; stackIdx >= 0; stackIdx--) {
                  const stackChar = openerStack[stackIdx].char
                  if (stackChar === oppositeBracket ||
                    stackChar === closingToOpeningBracket(getCanonicalBracket(char)) ||
                    openingToClosingBracket(getCanonicalBracket(stackChar)) === char
                  ) {
                    bracketPairs.push([openerStack[stackIdx].seqIndex, si])
                    openerStack.length = stackIdx //pop the matching bracket and all following
                    break
                  }
                }
              }
            }
          }
          bracketPairs.sort((a, b) => a[0] - b[0])
        }
        // * For each bracket-pair element in the list of pairs of text positions
        for (let pairIdx = 0; pairIdx < bracketPairs.length; pairIdx++) {
          const [openSeqIdx, closeSeqIdx] = bracketPairs[pairIdx]
          // a. Inspect the bidirectional types of the characters enclosed within the bracket pair.
          // b. If any strong type (either L or R) matching the embedding direction is found, set the type for both
          // brackets in the pair to match the embedding direction.
          let foundStrongType = false
          let useStrongType = 0
          for (let si = openSeqIdx + 1; si < closeSeqIdx; si++) {
            const i = seqIndices[si]
            if (charTypes[i] & STRONG_TYPES_FOR_N_STEPS) {
              foundStrongType = true
              const lr = (charTypes[i] & R_TYPES_FOR_N_STEPS) ? TYPE_R : TYPE_L
              if (lr === embedDirection) {
                useStrongType = lr
                break
              }
            }
          }
          // c. Otherwise, if there is a strong type it must be opposite the embedding direction. Therefore, test
          // for an established context with a preceding strong type by checking backwards before the opening paired
          // bracket until the first strong type (L, R, or sos) is found.
          //    1. If the preceding strong type is also opposite the embedding direction, context is established, so
          //    set the type for both brackets in the pair to that direction.
          //    2. Otherwise set the type for both brackets in the pair to the embedding direction.
          if (foundStrongType && !useStrongType) {
            useStrongType = sosType
            for (let si = openSeqIdx - 1; si >= 0; si--) {
              const i = seqIndices[si]
              if (charTypes[i] & STRONG_TYPES_FOR_N_STEPS) {
                const lr = (charTypes[i] & R_TYPES_FOR_N_STEPS) ? TYPE_R : TYPE_L
                if (lr !== embedDirection) {
                  useStrongType = lr
                } else {
                  useStrongType = embedDirection
                }
                break
              }
            }
          }
          if (useStrongType) {
            charTypes[seqIndices[openSeqIdx]] = charTypes[seqIndices[closeSeqIdx]] = useStrongType
            // * Any number of characters that had original bidirectional character type NSM prior to the application
            // of W1 that immediately follow a paired bracket which changed to L or R under N0 should change to match
            // the type of their preceding bracket.
            if (useStrongType !== embedDirection) {
              for (let si = openSeqIdx + 1; si < seqIndices.length; si++) {
                if (!(charTypes[seqIndices[si]] & BN_LIKE_TYPES)) {
                  if (getBidiCharType(string[seqIndices[si]]) & TYPE_NSM) {
                    charTypes[seqIndices[si]] = useStrongType
                  }
                  break
                }
              }
            }
            if (useStrongType !== embedDirection) {
              for (let si = closeSeqIdx + 1; si < seqIndices.length; si++) {
                if (!(charTypes[seqIndices[si]] & BN_LIKE_TYPES)) {
                  if (getBidiCharType(string[seqIndices[si]]) & TYPE_NSM) {
                    charTypes[seqIndices[si]] = useStrongType
                  }
                  break
                }
              }
            }
          }
        }

        // N1. A sequence of NIs takes the direction of the surrounding strong text if the text on both sides has the
        // same direction.
        // N2. Any remaining NIs take the embedding direction.
        for (let si = 0; si < seqIndices.length; si++) {
          if (charTypes[seqIndices[si]] & NEUTRAL_ISOLATE_TYPES) {
            let niRunStart = si, niRunEnd = si
            let prevType = sosType //si === 0 ? sosType : (charTypes[seqIndices[si - 1]] & R_TYPES_FOR_N_STEPS) ? TYPE_R : TYPE_L
            for (let si2 = si - 1; si2 >= 0; si2--) {
              if (charTypes[seqIndices[si2]] & BN_LIKE_TYPES) {
                niRunStart = si2 //5.2 treat BNs adjacent to NIs as NIs
              } else {
                prevType = (charTypes[seqIndices[si2]] & R_TYPES_FOR_N_STEPS) ? TYPE_R : TYPE_L
                break
              }
            }
            let nextType = eosType
            for (let si2 = si + 1; si2 < seqIndices.length; si2++) {
              if (charTypes[seqIndices[si2]] & (NEUTRAL_ISOLATE_TYPES | BN_LIKE_TYPES)) {
                niRunEnd = si2
              } else {
                nextType = (charTypes[seqIndices[si2]] & R_TYPES_FOR_N_STEPS) ? TYPE_R : TYPE_L
                break
              }
            }
            for (let sj = niRunStart; sj <= niRunEnd; sj++) {
              charTypes[seqIndices[sj]] = prevType === nextType ? prevType : embedDirection
            }
            si = niRunEnd
          }
        }
      }
    }

    // === 3.3.6 Resolving Implicit Levels ===

    for (let i = paragraph.start; i <= paragraph.end; i++) {
      const level = embedLevels[i]
      const type = charTypes[i]
      // I2. For all characters with an odd (right-to-left) embedding level, those of type L, EN or AN go up one level.
      if (level & 1) {
        if (type & (TYPE_L | TYPE_EN | TYPE_AN)) {
          embedLevels[i]++
        }
      }
        // I1. For all characters with an even (left-to-right) embedding level, those of type R go up one level
      // and those of type AN or EN go up two levels.
      else {
        if (type & TYPE_R) {
          embedLevels[i]++
        } else if (type & (TYPE_AN | TYPE_EN)) {
          embedLevels[i] += 2
        }
      }

      // 5.2: Resolve any LRE, RLE, LRO, RLO, PDF, or BN to the level of the preceding character if there is one,
      // and otherwise to the base level.
      if (type & BN_LIKE_TYPES) {
        embedLevels[i] = i === 0 ? paragraph.level : embedLevels[i - 1]
      }

      // 3.4 L1.1-4: Reset the embedding level of segment/paragraph separators, and any sequence of whitespace or
      // isolate formatting characters preceding them or the end of the paragraph, to the paragraph level.
      // NOTE: this will also need to be applied to each individual line ending after line wrapping occurs.
      if (i === paragraph.end || getBidiCharType(string[i]) & (TYPE_S | TYPE_B)) {
        for (let j = i; j >= 0 && (getBidiCharType(string[j]) & TRAILING_TYPES); j--) {
          embedLevels[j] = paragraph.level
        }
      }
    }
  }

  // DONE! The resolved levels can then be used, after line wrapping, to flip runs of characters
  // according to section 3.4 Reordering Resolved Levels
  return {
    levels: embedLevels,
    paragraphs
  }

  function determineAutoEmbedLevel (start, isFSI) {
    // 3.3.1 P2 - P3
    for (let i = start; i < string.length; i++) {
      const charType = charTypes[i]
      if (charType & (TYPE_R | TYPE_AL)) {
        return 1
      }
      if ((charType & (TYPE_B | TYPE_L)) || (isFSI && charType === TYPE_PDI)) {
        return 0
      }
      if (charType & ISOLATE_INIT_TYPES) {
        const pdi = indexOfMatchingPDI(i)
        i = pdi === -1 ? string.length : pdi
      }
    }
    return 0
  }

  function indexOfMatchingPDI (isolateStart) {
    // 3.1.2 BD9
    let isolationLevel = 1
    for (let i = isolateStart + 1; i < string.length; i++) {
      const charType = charTypes[i]
      if (charType & TYPE_B) {
        break
      }
      if (charType & TYPE_PDI) {
        if (--isolationLevel === 0) {
          return i
        }
      } else if (charType & ISOLATE_INIT_TYPES) {
        isolationLevel++
      }
    }
    return -1
  }
}
