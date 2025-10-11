function bidiFactory() {
var bidi = (function (exports) {

  // Bidi character types data, auto generated
  var DATA = {
    "R": "13k,1a,2,3,3,2+1j,ch+16,a+1,5+2,2+n,5,a,4,6+16,4+3,h+1b,4mo,179q,2+9,2+11,2i9+7y,2+68,4,3+4,5+13,4+3,2+4k,3+29,8+cf,1t+7z,w+17,3+3m,1t+3z,16o1+5r,8+30,8+mc,29+1r,29+4v,75+73",
    "EN": "1c+9,3d+1,6,187+9,513,4+5,7+9,sf+j,175h+9,qw+q,161f+1d,4xt+a,25i+9",
    "ES": "17,2,6dp+1,f+1,av,16vr,mx+1,4o,2",
    "ET": "z+2,3h+3,b+1,ym,3e+1,2o,p4+1,8,6u,7c,g6,1wc,1n9+4,30+1b,2n,6d,qhx+1,h0m,a+1,49+2,63+1,4+1,6bb+3,12jj",
    "AN": "16o+5,2j+9,2+1,35,ed,1ff2+9,87+u",
    "CS": "18,2+1,b,2u,12k,55v,l,17v0,2,3,53,2+1,b",
    "B": "a,3,f+2,2v,690",
    "S": "9,2,k",
    "WS": "c,k,4f4,1vk+a,u,1j,335",
    "ON": "x+1,4+4,h+5,r+5,r+3,z,5+3,2+1,2+1,5,2+2,3+4,o,w,ci+1,8+d,3+d,6+8,2+g,39+1,9,6+1,2,33,b8,3+1,3c+1,7+1,5r,b,7h+3,sa+5,2,3i+6,jg+3,ur+9,2v,ij+1,9g+9,7+a,8m,4+1,49+x,14u,2+2,c+2,e+2,e+2,e+1,i+n,e+e,2+p,u+2,e+2,36+1,2+3,2+1,b,2+2,6+5,2,2,2,h+1,5+4,6+3,3+f,16+2,5+3l,3+81,1y+p,2+40,q+a,m+13,2r+ch,2+9e,75+hf,3+v,2+2w,6e+5,f+6,75+2a,1a+p,2+2g,d+5x,r+b,6+3,4+o,g,6+1,6+2,2k+1,4,2j,5h+z,1m+1,1e+f,t+2,1f+e,d+3,4o+3,2s+1,w,535+1r,h3l+1i,93+2,2s,b+1,3l+x,2v,4g+3,21+3,kz+1,g5v+1,5a,j+9,n+v,2,3,2+8,2+1,3+2,2,3,46+1,4+4,h+5,r+5,r+a,3h+2,4+6,b+4,78,1r+24,4+c,4,1hb,ey+6,103+j,16j+c,1ux+7,5+g,fsh,jdq+1t,4,57+2e,p1,1m,1m,1m,1m,4kt+1,7j+17,5+2r,d+e,3+e,2+e,2+10,m+4,w,1n+5,1q,4z+5,4b+rb,9+c,4+c,4+37,d+2g,8+b,l+b,5+1j,9+9,7+13,9+t,3+1,27+3c,2+29,2+3q,d+d,3+4,4+2,6+6,a+o,8+6,a+2,e+6,16+42,2+1i",
    "BN": "0+8,6+d,2s+5,2+p,e,4m9,1kt+2,2b+5,5+5,17q9+v,7k,6p+8,6+1,119d+3,440+7,96s+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+75,6p+2rz,1ben+1,1ekf+1,1ekf+1",
    "NSM": "lc+33,7o+6,7c+18,2,2+1,2+1,2,21+a,1d+k,h,2u+6,3+5,3+1,2+3,10,v+q,2k+a,1n+8,a,p+3,2+8,2+2,2+4,18+2,3c+e,2+v,1k,2,5+7,5,4+6,b+1,u,1n,5+3,9,l+1,r,3+1,1m,5+1,5+1,3+2,4,v+1,4,c+1,1m,5+4,2+1,5,l+1,n+5,2,1n,3,2+3,9,8+1,c+1,v,1q,d,1f,4,1m+2,6+2,2+3,8+1,c+1,u,1n,g+1,l+1,t+1,1m+1,5+3,9,l+1,u,21,8+2,2,2j,3+6,d+7,2r,3+8,c+5,23+1,s,2,2,1k+d,2+4,2+1,6+a,2+z,a,2v+3,2+5,2+1,3+1,q+1,5+2,h+3,e,3+1,7,g,jk+2,qb+2,u+2,u+1,v+1,1t+1,2+6,9,3+a,a,1a+2,3c+1,z,3b+2,5+1,a,7+2,64+1,3,1n,2+6,2,2,3+7,7+9,3,1d+g,1s+3,1d,2+4,2,6,15+8,d+1,x+3,3+1,2+2,1l,2+1,4,2+2,1n+7,3+1,49+2,2+c,2+6,5,7,4+1,5j+1l,2+4,k1+w,2db+2,3y,2p+v,ff+3,30+1,n9x+3,2+9,x+1,29+1,7l,4,5,q+1,6,48+1,r+h,e,13+7,q+a,1b+2,1d,3+3,3+1,14,1w+5,3+1,3+1,d,9,1c,1g,2+2,3+1,6+1,2,17+1,9,6n,3,5,fn5,ki+f,h+f,r2,6b,46+4,1af+2,2+1,6+3,15+2,5,4m+1,fy+3,as+1,4a+a,4x,1j+e,1l+2,1e+3,3+1,1y+2,11+4,2+7,1r,d+1,1h+8,b+3,3,2o+2,3,2+1,7,4h,4+7,m+1,1m+1,4,12+6,4+4,5g+7,3+2,2,o,2d+5,2,5+1,2+1,6n+3,7+1,2+1,s+1,2e+7,3,2+1,2z,2,3+5,2,2u+2,3+3,2+4,78+8,2+1,75+1,2,5,41+3,3+1,5,x+5,3+1,15+5,3+3,9,a+5,3+2,1b+c,2+1,bb+6,2+5,2d+l,3+6,2+1,2+1,3f+5,4,2+1,2+6,2,21+1,4,2,9o+1,f0c+4,1o+6,t5,1s+3,2a,f5l+1,43t+2,i+7,3+6,v+3,45+2,1j0+1i,5+1d,9,f,n+4,2+e,11t+6,2+g,3+6,2+1,2+4,7a+6,c6+3,15t+6,32+6,gzhy+6n",
    "AL": "16w,3,2,e+1b,z+2,2+2s,g+1,8+1,b+m,2+t,s+2i,c+e,4h+f,1d+1e,1bwe+dp,3+3z,x+c,2+1,35+3y,2rm+z,5+7,b+5,dt+l,c+u,17nl+27,1t+27,4x+6n,3+d",
    "LRO": "6ct",
    "RLO": "6cu",
    "LRE": "6cq",
    "RLE": "6cr",
    "PDF": "6cs",
    "LRI": "6ee",
    "RLI": "6ef",
    "FSI": "6eg",
    "PDI": "6eh"
  };

  var TYPES = {};
  var TYPES_TO_NAMES = {};
  TYPES.L = 1; //L is the default
  TYPES_TO_NAMES[1] = 'L';
  Object.keys(DATA).forEach(function (type, i) {
    TYPES[type] = 1 << (i + 1);
    TYPES_TO_NAMES[TYPES[type]] = type;
  });
  Object.freeze(TYPES);

  var ISOLATE_INIT_TYPES = TYPES.LRI | TYPES.RLI | TYPES.FSI;
  var STRONG_TYPES = TYPES.L | TYPES.R | TYPES.AL;
  var NEUTRAL_ISOLATE_TYPES = TYPES.B | TYPES.S | TYPES.WS | TYPES.ON | TYPES.FSI | TYPES.LRI | TYPES.RLI | TYPES.PDI;
  var BN_LIKE_TYPES = TYPES.BN | TYPES.RLE | TYPES.LRE | TYPES.RLO | TYPES.LRO | TYPES.PDF;
  var TRAILING_TYPES = TYPES.S | TYPES.WS | TYPES.B | ISOLATE_INIT_TYPES | TYPES.PDI | BN_LIKE_TYPES;

  var map = null;

  function parseData () {
    if (!map) {
      //const start = performance.now()
      map = new Map();
      var loop = function ( type ) {
        if (DATA.hasOwnProperty(type)) {
          var lastCode = 0;
          DATA[type].split(',').forEach(function (range) {
            var ref = range.split('+');
            var skip = ref[0];
            var step = ref[1];
            skip = parseInt(skip, 36);
            step = step ? parseInt(step, 36) : 0;
            map.set(lastCode += skip, TYPES[type]);
            for (var i = 0; i < step; i++) {
              map.set(++lastCode, TYPES[type]);
            }
          });
        }
      };

      for (var type in DATA) loop( type );
      //console.log(`char types parsed in ${performance.now() - start}ms`)
    }
  }

  /**
   * @param {string} char
   * @return {number}
   */
  function getBidiCharType (char) {
    parseData();
    return map.get(char.codePointAt(0)) || TYPES.L
  }

  function getBidiCharTypeName(char) {
    return TYPES_TO_NAMES[getBidiCharType(char)]
  }

  // Bidi bracket pairs data, auto generated
  var data$1 = {
    "pairs": "14>1,1e>2,u>2,2wt>1,1>1,1ge>1,1wp>1,1j>1,f>1,hm>1,1>1,u>1,u6>1,1>1,+5,28>1,w>1,1>1,+3,b8>1,1>1,+3,1>3,-1>-1,3>1,1>1,+2,1s>1,1>1,x>1,th>1,1>1,+2,db>1,1>1,+3,3>1,1>1,+2,14qm>1,1>1,+1,4q>1,1e>2,u>2,2>1,+1",
    "canonical": "6f1>-6dx,6dy>-6dx,6ec>-6ed,6ee>-6ed,6ww>2jj,-2ji>2jj,14r4>-1e7l,1e7m>-1e7l,1e7m>-1e5c,1e5d>-1e5b,1e5c>-14qx,14qy>-14qx,14vn>-1ecg,1ech>-1ecg,1edu>-1ecg,1eci>-1ecg,1eda>-1ecg,1eci>-1ecg,1eci>-168q,168r>-168q,168s>-14ye,14yf>-14ye"
  };

  /**
   * Parses an string that holds encoded codepoint mappings, e.g. for bracket pairs or
   * mirroring characters, as encoded by scripts/generateBidiData.js. Returns an object
   * holding the `map`, and optionally a `reverseMap` if `includeReverse:true`.
   * @param {string} encodedString
   * @param {boolean} includeReverse - true if you want reverseMap in the output
   * @return {{map: Map<number, number>, reverseMap?: Map<number, number>}}
   */
  function parseCharacterMap (encodedString, includeReverse) {
    var radix = 36;
    var lastCode = 0;
    var map = new Map();
    var reverseMap = includeReverse && new Map();
    var prevPair;
    encodedString.split(',').forEach(function visit(entry) {
      if (entry.indexOf('+') !== -1) {
        for (var i = +entry; i--;) {
          visit(prevPair);
        }
      } else {
        prevPair = entry;
        var ref = entry.split('>');
        var a = ref[0];
        var b = ref[1];
        a = String.fromCodePoint(lastCode += parseInt(a, radix));
        b = String.fromCodePoint(lastCode += parseInt(b, radix));
        map.set(a, b);
        includeReverse && reverseMap.set(b, a);
      }
    });
    return { map: map, reverseMap: reverseMap }
  }

  var openToClose, closeToOpen, canonical;

  function parse$1 () {
    if (!openToClose) {
      //const start = performance.now()
      var ref = parseCharacterMap(data$1.pairs, true);
      var map = ref.map;
      var reverseMap = ref.reverseMap;
      openToClose = map;
      closeToOpen = reverseMap;
      canonical = parseCharacterMap(data$1.canonical, false).map;
      //console.log(`brackets parsed in ${performance.now() - start}ms`)
    }
  }

  function openingToClosingBracket (char) {
    parse$1();
    return openToClose.get(char) || null
  }

  function closingToOpeningBracket (char) {
    parse$1();
    return closeToOpen.get(char) || null
  }

  function getCanonicalBracket (char) {
    parse$1();
    return canonical.get(char) || null
  }

  // Local type aliases
  var TYPE_L = TYPES.L;
  var TYPE_R = TYPES.R;
  var TYPE_EN = TYPES.EN;
  var TYPE_ES = TYPES.ES;
  var TYPE_ET = TYPES.ET;
  var TYPE_AN = TYPES.AN;
  var TYPE_CS = TYPES.CS;
  var TYPE_B = TYPES.B;
  var TYPE_S = TYPES.S;
  var TYPE_ON = TYPES.ON;
  var TYPE_BN = TYPES.BN;
  var TYPE_NSM = TYPES.NSM;
  var TYPE_AL = TYPES.AL;
  var TYPE_LRO = TYPES.LRO;
  var TYPE_RLO = TYPES.RLO;
  var TYPE_LRE = TYPES.LRE;
  var TYPE_RLE = TYPES.RLE;
  var TYPE_PDF = TYPES.PDF;
  var TYPE_LRI = TYPES.LRI;
  var TYPE_RLI = TYPES.RLI;
  var TYPE_FSI = TYPES.FSI;
  var TYPE_PDI = TYPES.PDI;

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
  function getEmbeddingLevels (string, baseDirection) {
    var MAX_DEPTH = 125;

    // Start by mapping all characters to their unicode type, as a bitmask integer
    var charTypes = new Uint32Array(string.length);
    for (var i = 0; i < string.length; i++) {
      charTypes[i] = getBidiCharType(string[i]);
    }

    var charTypeCounts = new Map(); //will be cleared at start of each paragraph
    function changeCharType(i, type) {
      var oldType = charTypes[i];
      charTypes[i] = type;
      charTypeCounts.set(oldType, charTypeCounts.get(oldType) - 1);
      if (oldType & NEUTRAL_ISOLATE_TYPES) {
        charTypeCounts.set(NEUTRAL_ISOLATE_TYPES, charTypeCounts.get(NEUTRAL_ISOLATE_TYPES) - 1);
      }
      charTypeCounts.set(type, (charTypeCounts.get(type) || 0) + 1);
      if (type & NEUTRAL_ISOLATE_TYPES) {
        charTypeCounts.set(NEUTRAL_ISOLATE_TYPES, (charTypeCounts.get(NEUTRAL_ISOLATE_TYPES) || 0) + 1);
      }
    }

    var embedLevels = new Uint8Array(string.length);
    var isolationPairs = new Map(); //init->pdi and pdi->init

    // === 3.3.1 The Paragraph Level ===
    // 3.3.1 P1: Split the text into paragraphs
    var paragraphs = []; // [{start, end, level}, ...]
    var paragraph = null;
    for (var i$1 = 0; i$1 < string.length; i$1++) {
      if (!paragraph) {
        paragraphs.push(paragraph = {
          start: i$1,
          end: string.length - 1,
          // 3.3.1 P2-P3: Determine the paragraph level
          level: baseDirection === 'rtl' ? 1 : baseDirection === 'ltr' ? 0 : determineAutoEmbedLevel(i$1, false)
        });
      }
      if (charTypes[i$1] & TYPE_B) {
        paragraph.end = i$1;
        paragraph = null;
      }
    }

    var FORMATTING_TYPES = TYPE_RLE | TYPE_LRE | TYPE_RLO | TYPE_LRO | ISOLATE_INIT_TYPES | TYPE_PDI | TYPE_PDF | TYPE_B;
    var nextEven = function (n) { return n + ((n & 1) ? 1 : 2); };
    var nextOdd = function (n) { return n + ((n & 1) ? 2 : 1); };

    // Everything from here on will operate per paragraph.
    for (var paraIdx = 0; paraIdx < paragraphs.length; paraIdx++) {
      paragraph = paragraphs[paraIdx];
      var statusStack = [{
        _level: paragraph.level,
        _override: 0, //0=neutral, 1=L, 2=R
        _isolate: 0 //bool
      }];
      var stackTop = (void 0);
      var overflowIsolateCount = 0;
      var overflowEmbeddingCount = 0;
      var validIsolateCount = 0;
      charTypeCounts.clear();

      // === 3.3.2 Explicit Levels and Directions ===
      for (var i$2 = paragraph.start; i$2 <= paragraph.end; i$2++) {
        var charType = charTypes[i$2];
        stackTop = statusStack[statusStack.length - 1];

        // Set initial counts
        charTypeCounts.set(charType, (charTypeCounts.get(charType) || 0) + 1);
        if (charType & NEUTRAL_ISOLATE_TYPES) {
          charTypeCounts.set(NEUTRAL_ISOLATE_TYPES, (charTypeCounts.get(NEUTRAL_ISOLATE_TYPES) || 0) + 1);
        }

        // Explicit Embeddings: 3.3.2 X2 - X3
        if (charType & FORMATTING_TYPES) { //prefilter all formatters
          if (charType & (TYPE_RLE | TYPE_LRE)) {
            embedLevels[i$2] = stackTop._level; // 5.2
            var level = (charType === TYPE_RLE ? nextOdd : nextEven)(stackTop._level);
            if (level <= MAX_DEPTH && !overflowIsolateCount && !overflowEmbeddingCount) {
              statusStack.push({
                _level: level,
                _override: 0,
                _isolate: 0
              });
            } else if (!overflowIsolateCount) {
              overflowEmbeddingCount++;
            }
          }

          // Explicit Overrides: 3.3.2 X4 - X5
          else if (charType & (TYPE_RLO | TYPE_LRO)) {
            embedLevels[i$2] = stackTop._level; // 5.2
            var level$1 = (charType === TYPE_RLO ? nextOdd : nextEven)(stackTop._level);
            if (level$1 <= MAX_DEPTH && !overflowIsolateCount && !overflowEmbeddingCount) {
              statusStack.push({
                _level: level$1,
                _override: (charType & TYPE_RLO) ? TYPE_R : TYPE_L,
                _isolate: 0
              });
            } else if (!overflowIsolateCount) {
              overflowEmbeddingCount++;
            }
          }

          // Isolates: 3.3.2 X5a - X5c
          else if (charType & ISOLATE_INIT_TYPES) {
            // X5c - FSI becomes either RLI or LRI
            if (charType & TYPE_FSI) {
              charType = determineAutoEmbedLevel(i$2 + 1, true) === 1 ? TYPE_RLI : TYPE_LRI;
            }

            embedLevels[i$2] = stackTop._level;
            if (stackTop._override) {
              changeCharType(i$2, stackTop._override);
            }
            var level$2 = (charType === TYPE_RLI ? nextOdd : nextEven)(stackTop._level);
            if (level$2 <= MAX_DEPTH && overflowIsolateCount === 0 && overflowEmbeddingCount === 0) {
              validIsolateCount++;
              statusStack.push({
                _level: level$2,
                _override: 0,
                _isolate: 1,
                _isolInitIndex: i$2
              });
            } else {
              overflowIsolateCount++;
            }
          }

          // Terminating Isolates: 3.3.2 X6a
          else if (charType & TYPE_PDI) {
            if (overflowIsolateCount > 0) {
              overflowIsolateCount--;
            } else if (validIsolateCount > 0) {
              overflowEmbeddingCount = 0;
              while (!statusStack[statusStack.length - 1]._isolate) {
                statusStack.pop();
              }
              // Add to isolation pairs bidirectional mapping:
              var isolInitIndex = statusStack[statusStack.length - 1]._isolInitIndex;
              if (isolInitIndex != null) {
                isolationPairs.set(isolInitIndex, i$2);
                isolationPairs.set(i$2, isolInitIndex);
              }
              statusStack.pop();
              validIsolateCount--;
            }
            stackTop = statusStack[statusStack.length - 1];
            embedLevels[i$2] = stackTop._level;
            if (stackTop._override) {
              changeCharType(i$2, stackTop._override);
            }
          }


          // Terminating Embeddings and Overrides: 3.3.2 X7
          else if (charType & TYPE_PDF) {
            if (overflowIsolateCount === 0) {
              if (overflowEmbeddingCount > 0) {
                overflowEmbeddingCount--;
              } else if (!stackTop._isolate && statusStack.length > 1) {
                statusStack.pop();
                stackTop = statusStack[statusStack.length - 1];
              }
            }
            embedLevels[i$2] = stackTop._level; // 5.2
          }

          // End of Paragraph: 3.3.2 X8
          else if (charType & TYPE_B) {
            embedLevels[i$2] = paragraph.level;
          }
        }

        // Non-formatting characters: 3.3.2 X6
        else {
          embedLevels[i$2] = stackTop._level;
          // NOTE: This exclusion of BN seems to go against what section 5.2 says, but is required for test passage
          if (stackTop._override && charType !== TYPE_BN) {
            changeCharType(i$2, stackTop._override);
          }
        }
      }

      // === 3.3.3 Preparations for Implicit Processing ===

      // Remove all RLE, LRE, RLO, LRO, PDF, and BN characters: 3.3.3 X9
      // Note: Due to section 5.2, we won't remove them, but we'll use the BN_LIKE_TYPES bitset to
      // easily ignore them all from here on out.

      // 3.3.3 X10
      // Compute the set of isolating run sequences as specified by BD13
      var levelRuns = [];
      var currentRun = null;
      for (var i$3 = paragraph.start; i$3 <= paragraph.end; i$3++) {
        var charType$1 = charTypes[i$3];
        if (!(charType$1 & BN_LIKE_TYPES)) {
          var lvl = embedLevels[i$3];
          var isIsolInit = charType$1 & ISOLATE_INIT_TYPES;
          var isPDI = charType$1 === TYPE_PDI;
          if (currentRun && lvl === currentRun._level) {
            currentRun._end = i$3;
            currentRun._endsWithIsolInit = isIsolInit;
          } else {
            levelRuns.push(currentRun = {
              _start: i$3,
              _end: i$3,
              _level: lvl,
              _startsWithPDI: isPDI,
              _endsWithIsolInit: isIsolInit
            });
          }
        }
      }
      var isolatingRunSeqs = []; // [{seqIndices: [], sosType: L|R, eosType: L|R}]
      for (var runIdx = 0; runIdx < levelRuns.length; runIdx++) {
        var run = levelRuns[runIdx];
        if (!run._startsWithPDI || (run._startsWithPDI && !isolationPairs.has(run._start))) {
          var seqRuns = [currentRun = run];
          for (var pdiIndex = (void 0); currentRun && currentRun._endsWithIsolInit && (pdiIndex = isolationPairs.get(currentRun._end)) != null;) {
            for (var i$4 = runIdx + 1; i$4 < levelRuns.length; i$4++) {
              if (levelRuns[i$4]._start === pdiIndex) {
                seqRuns.push(currentRun = levelRuns[i$4]);
                break
              }
            }
          }
          // build flat list of indices across all runs:
          var seqIndices = [];
          for (var i$5 = 0; i$5 < seqRuns.length; i$5++) {
            var run$1 = seqRuns[i$5];
            for (var j = run$1._start; j <= run$1._end; j++) {
              seqIndices.push(j);
            }
          }
          // determine the sos/eos types:
          var firstLevel = embedLevels[seqIndices[0]];
          var prevLevel = paragraph.level;
          for (var i$6 = seqIndices[0] - 1; i$6 >= 0; i$6--) {
            if (!(charTypes[i$6] & BN_LIKE_TYPES)) { //5.2
              prevLevel = embedLevels[i$6];
              break
            }
          }
          var lastIndex = seqIndices[seqIndices.length - 1];
          var lastLevel = embedLevels[lastIndex];
          var nextLevel = paragraph.level;
          if (!(charTypes[lastIndex] & ISOLATE_INIT_TYPES)) {
            for (var i$7 = lastIndex + 1; i$7 <= paragraph.end; i$7++) {
              if (!(charTypes[i$7] & BN_LIKE_TYPES)) { //5.2
                nextLevel = embedLevels[i$7];
                break
              }
            }
          }
          isolatingRunSeqs.push({
            _seqIndices: seqIndices,
            _sosType: Math.max(prevLevel, firstLevel) % 2 ? TYPE_R : TYPE_L,
            _eosType: Math.max(nextLevel, lastLevel) % 2 ? TYPE_R : TYPE_L
          });
        }
      }

      // The next steps are done per isolating run sequence
      for (var seqIdx = 0; seqIdx < isolatingRunSeqs.length; seqIdx++) {
        var ref = isolatingRunSeqs[seqIdx];
        var seqIndices$1 = ref._seqIndices;
        var sosType = ref._sosType;
        var eosType = ref._eosType;
        /**
         * All the level runs in an isolating run sequence have the same embedding level.
         * 
         * DO NOT change any `embedLevels[i]` within the current scope.
         */
        var embedDirection = ((embedLevels[seqIndices$1[0]]) & 1) ? TYPE_R : TYPE_L;

        // === 3.3.4 Resolving Weak Types ===

        // W1 + 5.2. Search backward from each NSM to the first character in the isolating run sequence whose
        // bidirectional type is not BN, and set the NSM to ON if it is an isolate initiator or PDI, and to its
        // type otherwise. If the NSM is the first non-BN character, change the NSM to the type of sos.
        if (charTypeCounts.get(TYPE_NSM)) {
          for (var si = 0; si < seqIndices$1.length; si++) {
            var i$8 = seqIndices$1[si];
            if (charTypes[i$8] & TYPE_NSM) {
              var prevType = sosType;
              for (var sj = si - 1; sj >= 0; sj--) {
                if (!(charTypes[seqIndices$1[sj]] & BN_LIKE_TYPES)) { //5.2 scan back to first non-BN
                  prevType = charTypes[seqIndices$1[sj]];
                  break
                }
              }
              changeCharType(i$8, (prevType & (ISOLATE_INIT_TYPES | TYPE_PDI)) ? TYPE_ON : prevType);
            }
          }
        }

        // W2. Search backward from each instance of a European number until the first strong type (R, L, AL, or sos)
        // is found. If an AL is found, change the type of the European number to Arabic number.
        if (charTypeCounts.get(TYPE_EN)) {
          for (var si$1 = 0; si$1 < seqIndices$1.length; si$1++) {
            var i$9 = seqIndices$1[si$1];
            if (charTypes[i$9] & TYPE_EN) {
              for (var sj$1 = si$1 - 1; sj$1 >= -1; sj$1--) {
                var prevCharType = sj$1 === -1 ? sosType : charTypes[seqIndices$1[sj$1]];
                if (prevCharType & STRONG_TYPES) {
                  if (prevCharType === TYPE_AL) {
                    changeCharType(i$9, TYPE_AN);
                  }
                  break
                }
              }
            }
          }
        }

        // W3. Change all ALs to R
        if (charTypeCounts.get(TYPE_AL)) {
          for (var si$2 = 0; si$2 < seqIndices$1.length; si$2++) {
            var i$10 = seqIndices$1[si$2];
            if (charTypes[i$10] & TYPE_AL) {
              changeCharType(i$10, TYPE_R);
            }
          }
        }

        // W4. A single European separator between two European numbers changes to a European number. A single common
        // separator between two numbers of the same type changes to that type.
        if (charTypeCounts.get(TYPE_ES) || charTypeCounts.get(TYPE_CS)) {
          for (var si$3 = 1; si$3 < seqIndices$1.length - 1; si$3++) {
            var i$11 = seqIndices$1[si$3];
            if (charTypes[i$11] & (TYPE_ES | TYPE_CS)) {
              var prevType$1 = 0, nextType = 0;
              for (var sj$2 = si$3 - 1; sj$2 >= 0; sj$2--) {
                prevType$1 = charTypes[seqIndices$1[sj$2]];
                if (!(prevType$1 & BN_LIKE_TYPES)) { //5.2
                  break
                }
              }
              for (var sj$3 = si$3 + 1; sj$3 < seqIndices$1.length; sj$3++) {
                nextType = charTypes[seqIndices$1[sj$3]];
                if (!(nextType & BN_LIKE_TYPES)) { //5.2
                  break
                }
              }
              if (prevType$1 === nextType && (charTypes[i$11] === TYPE_ES ? prevType$1 === TYPE_EN : (prevType$1 & (TYPE_EN | TYPE_AN)))) {
                changeCharType(i$11, prevType$1);
              }
            }
          }
        }

        // W5. A sequence of European terminators adjacent to European numbers changes to all European numbers.
        if (charTypeCounts.get(TYPE_EN)) {
          for (var si$4 = 0; si$4 < seqIndices$1.length; si$4++) {
            var i$12 = seqIndices$1[si$4];
            if (charTypes[i$12] & TYPE_EN) {
              for (var sj$4 = si$4 - 1; sj$4 >= 0 && (charTypes[seqIndices$1[sj$4]] & (TYPE_ET | BN_LIKE_TYPES)); sj$4--) {
                changeCharType(seqIndices$1[sj$4], TYPE_EN);
              }
              for (si$4++; si$4 < seqIndices$1.length && (charTypes[seqIndices$1[si$4]] & (TYPE_ET | BN_LIKE_TYPES | TYPE_EN)); si$4++) {
                if (charTypes[seqIndices$1[si$4]] !== TYPE_EN) {
                  changeCharType(seqIndices$1[si$4], TYPE_EN);
                }
              }
            }
          }
        }

        // W6. Otherwise, separators and terminators change to Other Neutral.
        if (charTypeCounts.get(TYPE_ET) || charTypeCounts.get(TYPE_ES) || charTypeCounts.get(TYPE_CS)) {
          for (var si$5 = 0; si$5 < seqIndices$1.length; si$5++) {
            var i$13 = seqIndices$1[si$5];
            if (charTypes[i$13] & (TYPE_ET | TYPE_ES | TYPE_CS)) {
              changeCharType(i$13, TYPE_ON);
              // 5.2 transform adjacent BNs too:
              for (var sj$5 = si$5 - 1; sj$5 >= 0 && (charTypes[seqIndices$1[sj$5]] & BN_LIKE_TYPES); sj$5--) {
                changeCharType(seqIndices$1[sj$5], TYPE_ON);
              }
              for (var sj$6 = si$5 + 1; sj$6 < seqIndices$1.length && (charTypes[seqIndices$1[sj$6]] & BN_LIKE_TYPES); sj$6++) {
                changeCharType(seqIndices$1[sj$6], TYPE_ON);
              }
            }
          }
        }

        // W7. Search backward from each instance of a European number until the first strong type (R, L, or sos)
        // is found. If an L is found, then change the type of the European number to L.
        // NOTE: implemented in single forward pass for efficiency
        if (charTypeCounts.get(TYPE_EN)) {
          for (var si$6 = 0, prevStrongType = sosType; si$6 < seqIndices$1.length; si$6++) {
            var i$14 = seqIndices$1[si$6];
            var type = charTypes[i$14];
            if (type & TYPE_EN) {
              if (prevStrongType === TYPE_L) {
                changeCharType(i$14, TYPE_L);
              }
            } else if (type & STRONG_TYPES) {
              prevStrongType = type;
            }
          }
        }

        // === 3.3.5 Resolving Neutral and Isolate Formatting Types ===

        if (charTypeCounts.get(NEUTRAL_ISOLATE_TYPES)) {
          // N0. Process bracket pairs in an isolating run sequence sequentially in the logical order of the text
          // positions of the opening paired brackets using the logic given below. Within this scope, bidirectional
          // types EN and AN are treated as R.
          var R_TYPES_FOR_N_STEPS = (TYPE_R | TYPE_EN | TYPE_AN);
          var STRONG_TYPES_FOR_N_STEPS = R_TYPES_FOR_N_STEPS | TYPE_L;

          // * Identify the bracket pairs in the current isolating run sequence according to BD16.
          var bracketPairs = [];
          {
            var openerStack = [];
            for (var si$7 = 0; si$7 < seqIndices$1.length; si$7++) {
              // NOTE: for any potential bracket character we also test that it still carries a NI
              // type, as that may have been changed earlier. This doesn't seem to be explicitly
              // called out in the spec, but is required for passage of certain tests.
              if (charTypes[seqIndices$1[si$7]] & NEUTRAL_ISOLATE_TYPES) {
                var char = string[seqIndices$1[si$7]];
                var oppositeBracket = (void 0);
                // Opening bracket
                if (openingToClosingBracket(char) !== null) {
                  if (openerStack.length < 63) {
                    openerStack.push({ char: char, seqIndex: si$7 });
                  } else {
                    break
                  }
                }
                // Closing bracket
                else if ((oppositeBracket = closingToOpeningBracket(char)) !== null) {
                  for (var stackIdx = openerStack.length - 1; stackIdx >= 0; stackIdx--) {
                    var stackChar = openerStack[stackIdx].char;
                    if (stackChar === oppositeBracket ||
                      stackChar === closingToOpeningBracket(getCanonicalBracket(char)) ||
                      openingToClosingBracket(getCanonicalBracket(stackChar)) === char
                    ) {
                      bracketPairs.push([openerStack[stackIdx].seqIndex, si$7]);
                      openerStack.length = stackIdx; //pop the matching bracket and all following
                      break
                    }
                  }
                }
              }
            }
            bracketPairs.sort(function (a, b) { return a[0] - b[0]; });
          }
          // * For each bracket-pair element in the list of pairs of text positions
          for (var pairIdx = 0; pairIdx < bracketPairs.length; pairIdx++) {
            var ref$1 = bracketPairs[pairIdx];
            var openSeqIdx = ref$1[0];
            var closeSeqIdx = ref$1[1];
            // a. Inspect the bidirectional types of the characters enclosed within the bracket pair.
            // b. If any strong type (either L or R) matching the embedding direction is found, set the type for both
            // brackets in the pair to match the embedding direction.
            var foundStrongType = false;
            var useStrongType = 0;
            for (var si$8 = openSeqIdx + 1; si$8 < closeSeqIdx; si$8++) {
              var i$15 = seqIndices$1[si$8];
              if (charTypes[i$15] & STRONG_TYPES_FOR_N_STEPS) {
                foundStrongType = true;
                var lr = (charTypes[i$15] & R_TYPES_FOR_N_STEPS) ? TYPE_R : TYPE_L;
                if (lr === embedDirection) {
                  useStrongType = lr;
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
              useStrongType = sosType;
              for (var si$9 = openSeqIdx - 1; si$9 >= 0; si$9--) {
                var i$16 = seqIndices$1[si$9];
                if (charTypes[i$16] & STRONG_TYPES_FOR_N_STEPS) {
                  var lr$1 = (charTypes[i$16] & R_TYPES_FOR_N_STEPS) ? TYPE_R : TYPE_L;
                  if (lr$1 !== embedDirection) {
                    useStrongType = lr$1;
                  } else {
                    useStrongType = embedDirection;
                  }
                  break
                }
              }
            }
            if (useStrongType) {
              charTypes[seqIndices$1[openSeqIdx]] = charTypes[seqIndices$1[closeSeqIdx]] = useStrongType;
              // * Any number of characters that had original bidirectional character type NSM prior to the application
              // of W1 that immediately follow a paired bracket which changed to L or R under N0 should change to match
              // the type of their preceding bracket.
              if (useStrongType !== embedDirection) {
                for (var si$10 = openSeqIdx + 1; si$10 < seqIndices$1.length; si$10++) {
                  if (!(charTypes[seqIndices$1[si$10]] & BN_LIKE_TYPES)) {
                    if (getBidiCharType(string[seqIndices$1[si$10]]) & TYPE_NSM) {
                      charTypes[seqIndices$1[si$10]] = useStrongType;
                    }
                    break
                  }
                }
              }
              if (useStrongType !== embedDirection) {
                for (var si$11 = closeSeqIdx + 1; si$11 < seqIndices$1.length; si$11++) {
                  if (!(charTypes[seqIndices$1[si$11]] & BN_LIKE_TYPES)) {
                    if (getBidiCharType(string[seqIndices$1[si$11]]) & TYPE_NSM) {
                      charTypes[seqIndices$1[si$11]] = useStrongType;
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
          for (var si$12 = 0; si$12 < seqIndices$1.length; si$12++) {
            if (charTypes[seqIndices$1[si$12]] & NEUTRAL_ISOLATE_TYPES) {
              var niRunStart = si$12, niRunEnd = si$12;
              var prevType$2 = sosType; //si === 0 ? sosType : (charTypes[seqIndices[si - 1]] & R_TYPES_FOR_N_STEPS) ? TYPE_R : TYPE_L
              for (var si2 = si$12 - 1; si2 >= 0; si2--) {
                if (charTypes[seqIndices$1[si2]] & BN_LIKE_TYPES) {
                  niRunStart = si2; //5.2 treat BNs adjacent to NIs as NIs
                } else {
                  prevType$2 = (charTypes[seqIndices$1[si2]] & R_TYPES_FOR_N_STEPS) ? TYPE_R : TYPE_L;
                  break
                }
              }
              var nextType$1 = eosType;
              for (var si2$1 = si$12 + 1; si2$1 < seqIndices$1.length; si2$1++) {
                if (charTypes[seqIndices$1[si2$1]] & (NEUTRAL_ISOLATE_TYPES | BN_LIKE_TYPES)) {
                  niRunEnd = si2$1;
                } else {
                  nextType$1 = (charTypes[seqIndices$1[si2$1]] & R_TYPES_FOR_N_STEPS) ? TYPE_R : TYPE_L;
                  break
                }
              }
              for (var sj$7 = niRunStart; sj$7 <= niRunEnd; sj$7++) {
                charTypes[seqIndices$1[sj$7]] = prevType$2 === nextType$1 ? prevType$2 : embedDirection;
              }
              si$12 = niRunEnd;
            }
          }
        }
      }

      // === 3.3.6 Resolving Implicit Levels ===

      for (var i$17 = paragraph.start; i$17 <= paragraph.end; i$17++) {
        var level$3 = embedLevels[i$17];
        var type$1 = charTypes[i$17];
        // I2. For all characters with an odd (right-to-left) embedding level, those of type L, EN or AN go up one level.
        if (level$3 & 1) {
          if (type$1 & (TYPE_L | TYPE_EN | TYPE_AN)) {
            embedLevels[i$17]++;
          }
        }
          // I1. For all characters with an even (left-to-right) embedding level, those of type R go up one level
        // and those of type AN or EN go up two levels.
        else {
          if (type$1 & TYPE_R) {
            embedLevels[i$17]++;
          } else if (type$1 & (TYPE_AN | TYPE_EN)) {
            embedLevels[i$17] += 2;
          }
        }

        // 5.2: Resolve any LRE, RLE, LRO, RLO, PDF, or BN to the level of the preceding character if there is one,
        // and otherwise to the base level.
        if (type$1 & BN_LIKE_TYPES) {
          embedLevels[i$17] = i$17 === 0 ? paragraph.level : embedLevels[i$17 - 1];
        }

        // 3.4 L1.1-4: Reset the embedding level of segment/paragraph separators, and any sequence of whitespace or
        // isolate formatting characters preceding them or the end of the paragraph, to the paragraph level.
        // NOTE: this will also need to be applied to each individual line ending after line wrapping occurs.
        if (i$17 === paragraph.end || getBidiCharType(string[i$17]) & (TYPE_S | TYPE_B)) {
          for (var j$1 = i$17; j$1 >= 0 && (getBidiCharType(string[j$1]) & TRAILING_TYPES); j$1--) {
            embedLevels[j$1] = paragraph.level;
          }
        }
      }
    }

    // DONE! The resolved levels can then be used, after line wrapping, to flip runs of characters
    // according to section 3.4 Reordering Resolved Levels
    return {
      levels: embedLevels,
      paragraphs: paragraphs
    }

    function determineAutoEmbedLevel (start, isFSI) {
      // 3.3.1 P2 - P3
      for (var i = start; i < string.length; i++) {
        var charType = charTypes[i];
        if (charType & (TYPE_R | TYPE_AL)) {
          return 1
        }
        if ((charType & (TYPE_B | TYPE_L)) || (isFSI && charType === TYPE_PDI)) {
          return 0
        }
        if (charType & ISOLATE_INIT_TYPES) {
          var pdi = indexOfMatchingPDI(i);
          i = pdi === -1 ? string.length : pdi;
        }
      }
      return 0
    }

    function indexOfMatchingPDI (isolateStart) {
      // 3.1.2 BD9
      var isolationLevel = 1;
      for (var i = isolateStart + 1; i < string.length; i++) {
        var charType = charTypes[i];
        if (charType & TYPE_B) {
          break
        }
        if (charType & TYPE_PDI) {
          if (--isolationLevel === 0) {
            return i
          }
        } else if (charType & ISOLATE_INIT_TYPES) {
          isolationLevel++;
        }
      }
      return -1
    }
  }

  // Bidi mirrored chars data, auto generated
  var data = "14>1,j>2,t>2,u>2,1a>g,2v3>1,1>1,1ge>1,1wd>1,b>1,1j>1,f>1,ai>3,-2>3,+1,8>1k0,-1jq>1y7,-1y6>1hf,-1he>1h6,-1h5>1ha,-1h8>1qi,-1pu>1,6>3u,-3s>7,6>1,1>1,f>1,1>1,+2,3>1,1>1,+13,4>1,1>1,6>1eo,-1ee>1,3>1mg,-1me>1mk,-1mj>1mi,-1mg>1mi,-1md>1,1>1,+2,1>10k,-103>1,1>1,4>1,5>1,1>1,+10,3>1,1>8,-7>8,+1,-6>7,+1,a>1,1>1,u>1,u6>1,1>1,+5,26>1,1>1,2>1,2>2,8>1,7>1,4>1,1>1,+5,b8>1,1>1,+3,1>3,-2>1,2>1,1>1,+2,c>1,3>1,1>1,+2,h>1,3>1,a>1,1>1,2>1,3>1,1>1,d>1,f>1,3>1,1a>1,1>1,6>1,7>1,13>1,k>1,1>1,+19,4>1,1>1,+2,2>1,1>1,+18,m>1,a>1,1>1,lk>1,1>1,4>1,2>1,f>1,3>1,1>1,+3,db>1,1>1,+3,3>1,1>1,+2,14qm>1,1>1,+1,6>1,4j>1,j>2,t>2,u>2,2>1,+1";

  var mirrorMap;

  function parse () {
    if (!mirrorMap) {
      //const start = performance.now()
      var ref = parseCharacterMap(data, true);
      var map = ref.map;
      var reverseMap = ref.reverseMap;
      // Combine both maps into one
      reverseMap.forEach(function (value, key) {
        map.set(key, value);
      });
      mirrorMap = map;
      //console.log(`mirrored chars parsed in ${performance.now() - start}ms`)
    }
  }

  function getMirroredCharacter (char) {
    parse();
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
  function getMirroredCharactersMap(string, embeddingLevels, start, end) {
    var strLen = string.length;
    start = Math.max(0, start == null ? 0 : +start);
    end = Math.min(strLen - 1, end == null ? strLen - 1 : +end);

    var map = new Map();
    for (var i = start; i <= end; i++) {
      if (embeddingLevels[i] & 1) { //only odd (rtl) levels
        var mirror = getMirroredCharacter(string[i]);
        if (mirror !== null) {
          map.set(i, mirror);
        }
      }
    }
    return map
  }

  /**
   * Given a start and end denoting a single line within a string, and a set of precalculated
   * bidi embedding levels, produce a list of segments whose ordering should be flipped, in sequence.
   * @param {string} string - the full input string
   * @param {GetEmbeddingLevelsResult} embeddingLevelsResult - the result object from getEmbeddingLevels
   * @param {number} [start] - first character in a subset of the full string
   * @param {number} [end] - last character in a subset of the full string
   * @return {number[][]} - the list of start/end segments that should be flipped, in order.
   */
  function getReorderSegments(string, embeddingLevelsResult, start, end) {
    var strLen = string.length;
    start = Math.max(0, start == null ? 0 : +start);
    end = Math.min(strLen - 1, end == null ? strLen - 1 : +end);

    var segments = [];
    embeddingLevelsResult.paragraphs.forEach(function (paragraph) {
      var lineStart = Math.max(start, paragraph.start);
      var lineEnd = Math.min(end, paragraph.end);
      if (lineStart < lineEnd) {
        // Local slice for mutation
        var lineLevels = embeddingLevelsResult.levels.slice(lineStart, lineEnd + 1);

        // 3.4 L1.4: Reset any sequence of whitespace characters and/or isolate formatting characters at the
        // end of the line to the paragraph level.
        for (var i = lineEnd; i >= lineStart && (getBidiCharType(string[i]) & TRAILING_TYPES); i--) {
          lineLevels[i] = paragraph.level;
        }

        // L2. From the highest level found in the text to the lowest odd level on each line, including intermediate levels
        // not actually present in the text, reverse any contiguous sequence of characters that are at that level or higher.
        var maxLevel = paragraph.level;
        var minOddLevel = Infinity;
        for (var i$1 = 0; i$1 < lineLevels.length; i$1++) {
          var level = lineLevels[i$1];
          if (level > maxLevel) { maxLevel = level; }
          if (level < minOddLevel) { minOddLevel = level | 1; }
        }
        for (var lvl = maxLevel; lvl >= minOddLevel; lvl--) {
          for (var i$2 = 0; i$2 < lineLevels.length; i$2++) {
            if (lineLevels[i$2] >= lvl) {
              var segStart = i$2;
              while (i$2 + 1 < lineLevels.length && lineLevels[i$2 + 1] >= lvl) {
                i$2++;
              }
              if (i$2 > segStart) {
                segments.push([segStart + lineStart, i$2 + lineStart]);
              }
            }
          }
        }
      }
    });
    return segments
  }

  /**
   * @param {string} string
   * @param {GetEmbeddingLevelsResult} embedLevelsResult
   * @param {number} [start]
   * @param {number} [end]
   * @return {string} the new string with bidi segments reordered
   */
  function getReorderedString(string, embedLevelsResult, start, end) {
    var indices = getReorderedIndices(string, embedLevelsResult, start, end);
    var chars = [].concat( string );
    indices.forEach(function (charIndex, i) {
      chars[i] = (
        (embedLevelsResult.levels[charIndex] & 1) ? getMirroredCharacter(string[charIndex]) : null
      ) || string[charIndex];
    });
    return chars.join('')
  }

  /**
   * @param {string} string
   * @param {GetEmbeddingLevelsResult} embedLevelsResult
   * @param {number} [start]
   * @param {number} [end]
   * @return {number[]} an array with character indices in their new bidi order
   */
  function getReorderedIndices(string, embedLevelsResult, start, end) {
    var segments = getReorderSegments(string, embedLevelsResult, start, end);
    // Fill an array with indices
    var indices = [];
    for (var i = 0; i < string.length; i++) {
      indices[i] = i;
    }
    // Reverse each segment in order
    segments.forEach(function (ref) {
      var start = ref[0];
      var end = ref[1];

      var slice = indices.slice(start, end + 1);
      for (var i = slice.length; i--;) {
        indices[end - i] = slice[i];
      }
    });
    return indices
  }

  exports.closingToOpeningBracket = closingToOpeningBracket;
  exports.getBidiCharType = getBidiCharType;
  exports.getBidiCharTypeName = getBidiCharTypeName;
  exports.getCanonicalBracket = getCanonicalBracket;
  exports.getEmbeddingLevels = getEmbeddingLevels;
  exports.getMirroredCharacter = getMirroredCharacter;
  exports.getMirroredCharactersMap = getMirroredCharactersMap;
  exports.getReorderSegments = getReorderSegments;
  exports.getReorderedIndices = getReorderedIndices;
  exports.getReorderedString = getReorderedString;
  exports.openingToClosingBracket = openingToClosingBracket;

  Object.defineProperty(exports, '__esModule', { value: true });

  return exports;

}({}));
return bidi}

export default bidiFactory;
