"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.poseidon = exports.splitConstants = exports.validateOpts = void 0;
/*! noble-curves - MIT License (c) 2022 Paul Miller (paulmillr.com) */
// Poseidon Hash: https://eprint.iacr.org/2019/458.pdf, https://www.poseidon-hash.info
const modular_js_1 = require("./modular.js");
function validateOpts(opts) {
    const { Fp, mds, reversePartialPowIdx: rev, roundConstants: rc } = opts;
    const { roundsFull, roundsPartial, sboxPower, t } = opts;
    (0, modular_js_1.validateField)(Fp);
    for (const i of ['t', 'roundsFull', 'roundsPartial']) {
        if (typeof opts[i] !== 'number' || !Number.isSafeInteger(opts[i]))
            throw new Error(`Poseidon: invalid param ${i}=${opts[i]} (${typeof opts[i]})`);
    }
    // MDS is TxT matrix
    if (!Array.isArray(mds) || mds.length !== t)
        throw new Error('Poseidon: wrong MDS matrix');
    const _mds = mds.map((mdsRow) => {
        if (!Array.isArray(mdsRow) || mdsRow.length !== t)
            throw new Error(`Poseidon MDS matrix row: ${mdsRow}`);
        return mdsRow.map((i) => {
            if (typeof i !== 'bigint')
                throw new Error(`Poseidon MDS matrix value=${i}`);
            return Fp.create(i);
        });
    });
    if (rev !== undefined && typeof rev !== 'boolean')
        throw new Error(`Poseidon: invalid param reversePartialPowIdx=${rev}`);
    if (roundsFull % 2 !== 0)
        throw new Error(`Poseidon roundsFull is not even: ${roundsFull}`);
    const rounds = roundsFull + roundsPartial;
    if (!Array.isArray(rc) || rc.length !== rounds)
        throw new Error('Poseidon: wrong round constants');
    const roundConstants = rc.map((rc) => {
        if (!Array.isArray(rc) || rc.length !== t)
            throw new Error(`Poseidon wrong round constants: ${rc}`);
        return rc.map((i) => {
            if (typeof i !== 'bigint' || !Fp.isValid(i))
                throw new Error(`Poseidon wrong round constant=${i}`);
            return Fp.create(i);
        });
    });
    if (!sboxPower || ![3, 5, 7].includes(sboxPower))
        throw new Error(`Poseidon wrong sboxPower=${sboxPower}`);
    const _sboxPower = BigInt(sboxPower);
    let sboxFn = (n) => (0, modular_js_1.FpPow)(Fp, n, _sboxPower);
    // Unwrapped sbox power for common cases (195->142μs)
    if (sboxPower === 3)
        sboxFn = (n) => Fp.mul(Fp.sqrN(n), n);
    else if (sboxPower === 5)
        sboxFn = (n) => Fp.mul(Fp.sqrN(Fp.sqrN(n)), n);
    return Object.freeze({ ...opts, rounds, sboxFn, roundConstants, mds: _mds });
}
exports.validateOpts = validateOpts;
function splitConstants(rc, t) {
    if (typeof t !== 'number')
        throw new Error('poseidonSplitConstants: wrong t');
    if (!Array.isArray(rc) || rc.length % t)
        throw new Error('poseidonSplitConstants: wrong rc');
    const res = [];
    let tmp = [];
    for (let i = 0; i < rc.length; i++) {
        tmp.push(rc[i]);
        if (tmp.length === t) {
            res.push(tmp);
            tmp = [];
        }
    }
    return res;
}
exports.splitConstants = splitConstants;
function poseidon(opts) {
    const _opts = validateOpts(opts);
    const { Fp, mds, roundConstants, rounds, roundsPartial, sboxFn, t } = _opts;
    const halfRoundsFull = _opts.roundsFull / 2;
    const partialIdx = _opts.reversePartialPowIdx ? t - 1 : 0;
    const poseidonRound = (values, isFull, idx) => {
        values = values.map((i, j) => Fp.add(i, roundConstants[idx][j]));
        if (isFull)
            values = values.map((i) => sboxFn(i));
        else
            values[partialIdx] = sboxFn(values[partialIdx]);
        // Matrix multiplication
        values = mds.map((i) => i.reduce((acc, i, j) => Fp.add(acc, Fp.mulN(i, values[j])), Fp.ZERO));
        return values;
    };
    const poseidonHash = function poseidonHash(values) {
        if (!Array.isArray(values) || values.length !== t)
            throw new Error(`Poseidon: wrong values (expected array of bigints with length ${t})`);
        values = values.map((i) => {
            if (typeof i !== 'bigint')
                throw new Error(`Poseidon: wrong value=${i} (${typeof i})`);
            return Fp.create(i);
        });
        let round = 0;
        // Apply r_f/2 full rounds.
        for (let i = 0; i < halfRoundsFull; i++)
            values = poseidonRound(values, true, round++);
        // Apply r_p partial rounds.
        for (let i = 0; i < roundsPartial; i++)
            values = poseidonRound(values, false, round++);
        // Apply r_f/2 full rounds.
        for (let i = 0; i < halfRoundsFull; i++)
            values = poseidonRound(values, true, round++);
        if (round !== rounds)
            throw new Error(`Poseidon: wrong number of rounds: last round=${round}, total=${rounds}`);
        return values;
    };
    // For verification in tests
    poseidonHash.roundConstants = roundConstants;
    return poseidonHash;
}
exports.poseidon = poseidon;
//# sourceMappingURL=poseidon.js.map