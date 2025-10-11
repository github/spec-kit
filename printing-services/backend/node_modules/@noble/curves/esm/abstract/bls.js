import { getMinHashLength, mapHashToField } from './modular.js';
import { bitLen, bitGet, ensureBytes } from './utils.js';
import * as htf from './hash-to-curve.js';
import { weierstrassPoints, } from './weierstrass.js';
// prettier-ignore
const _2n = BigInt(2), _3n = BigInt(3);
export function bls(CURVE) {
    // Fields are specific for curve, so for now we'll need to pass them with opts
    const { Fp, Fr, Fp2, Fp6, Fp12 } = CURVE.fields;
    const BLS_X_LEN = bitLen(CURVE.params.x);
    // Pre-compute coefficients for sparse multiplication
    // Point addition and point double calculations is reused for coefficients
    function calcPairingPrecomputes(p) {
        const { x, y } = p;
        // prettier-ignore
        const Qx = x, Qy = y, Qz = Fp2.ONE;
        // prettier-ignore
        let Rx = Qx, Ry = Qy, Rz = Qz;
        let ell_coeff = [];
        for (let i = BLS_X_LEN - 2; i >= 0; i--) {
            // Double
            let t0 = Fp2.sqr(Ry); // Ry²
            let t1 = Fp2.sqr(Rz); // Rz²
            let t2 = Fp2.multiplyByB(Fp2.mul(t1, _3n)); // 3 * T1 * B
            let t3 = Fp2.mul(t2, _3n); // 3 * T2
            let t4 = Fp2.sub(Fp2.sub(Fp2.sqr(Fp2.add(Ry, Rz)), t1), t0); // (Ry + Rz)² - T1 - T0
            ell_coeff.push([
                Fp2.sub(t2, t0),
                Fp2.mul(Fp2.sqr(Rx), _3n),
                Fp2.neg(t4), // -T4
            ]);
            Rx = Fp2.div(Fp2.mul(Fp2.mul(Fp2.sub(t0, t3), Rx), Ry), _2n); // ((T0 - T3) * Rx * Ry) / 2
            Ry = Fp2.sub(Fp2.sqr(Fp2.div(Fp2.add(t0, t3), _2n)), Fp2.mul(Fp2.sqr(t2), _3n)); // ((T0 + T3) / 2)² - 3 * T2²
            Rz = Fp2.mul(t0, t4); // T0 * T4
            if (bitGet(CURVE.params.x, i)) {
                // Addition
                let t0 = Fp2.sub(Ry, Fp2.mul(Qy, Rz)); // Ry - Qy * Rz
                let t1 = Fp2.sub(Rx, Fp2.mul(Qx, Rz)); // Rx - Qx * Rz
                ell_coeff.push([
                    Fp2.sub(Fp2.mul(t0, Qx), Fp2.mul(t1, Qy)),
                    Fp2.neg(t0),
                    t1, // T1
                ]);
                let t2 = Fp2.sqr(t1); // T1²
                let t3 = Fp2.mul(t2, t1); // T2 * T1
                let t4 = Fp2.mul(t2, Rx); // T2 * Rx
                let t5 = Fp2.add(Fp2.sub(t3, Fp2.mul(t4, _2n)), Fp2.mul(Fp2.sqr(t0), Rz)); // T3 - 2 * T4 + T0² * Rz
                Rx = Fp2.mul(t1, t5); // T1 * T5
                Ry = Fp2.sub(Fp2.mul(Fp2.sub(t4, t5), t0), Fp2.mul(t3, Ry)); // (T4 - T5) * T0 - T3 * Ry
                Rz = Fp2.mul(Rz, t3); // Rz * T3
            }
        }
        return ell_coeff;
    }
    function millerLoop(ell, g1) {
        const { x } = CURVE.params;
        const Px = g1[0];
        const Py = g1[1];
        let f12 = Fp12.ONE;
        for (let j = 0, i = BLS_X_LEN - 2; i >= 0; i--, j++) {
            const E = ell[j];
            f12 = Fp12.multiplyBy014(f12, E[0], Fp2.mul(E[1], Px), Fp2.mul(E[2], Py));
            if (bitGet(x, i)) {
                j += 1;
                const F = ell[j];
                f12 = Fp12.multiplyBy014(f12, F[0], Fp2.mul(F[1], Px), Fp2.mul(F[2], Py));
            }
            if (i !== 0)
                f12 = Fp12.sqr(f12);
        }
        return Fp12.conjugate(f12);
    }
    const utils = {
        randomPrivateKey: () => {
            const length = getMinHashLength(Fr.ORDER);
            return mapHashToField(CURVE.randomBytes(length), Fr.ORDER);
        },
        calcPairingPrecomputes,
    };
    // Point on G1 curve: (x, y)
    const G1_ = weierstrassPoints({ n: Fr.ORDER, ...CURVE.G1 });
    const G1 = Object.assign(G1_, htf.createHasher(G1_.ProjectivePoint, CURVE.G1.mapToCurve, {
        ...CURVE.htfDefaults,
        ...CURVE.G1.htfDefaults,
    }));
    function pairingPrecomputes(point) {
        const p = point;
        if (p._PPRECOMPUTES)
            return p._PPRECOMPUTES;
        p._PPRECOMPUTES = calcPairingPrecomputes(point.toAffine());
        return p._PPRECOMPUTES;
    }
    // TODO: export
    // function clearPairingPrecomputes(point: G2) {
    //   const p = point as G2 & withPairingPrecomputes;
    //   p._PPRECOMPUTES = undefined;
    // }
    // Point on G2 curve (complex numbers): (x₁, x₂+i), (y₁, y₂+i)
    const G2_ = weierstrassPoints({ n: Fr.ORDER, ...CURVE.G2 });
    const G2 = Object.assign(G2_, htf.createHasher(G2_.ProjectivePoint, CURVE.G2.mapToCurve, {
        ...CURVE.htfDefaults,
        ...CURVE.G2.htfDefaults,
    }));
    const { Signature } = CURVE.G2;
    // Calculates bilinear pairing
    function pairing(Q, P, withFinalExponent = true) {
        if (Q.equals(G1.ProjectivePoint.ZERO) || P.equals(G2.ProjectivePoint.ZERO))
            throw new Error('pairing is not available for ZERO point');
        Q.assertValidity();
        P.assertValidity();
        // Performance: 9ms for millerLoop and ~14ms for exp.
        const Qa = Q.toAffine();
        const looped = millerLoop(pairingPrecomputes(P), [Qa.x, Qa.y]);
        return withFinalExponent ? Fp12.finalExponentiate(looped) : looped;
    }
    function normP1(point) {
        return point instanceof G1.ProjectivePoint ? point : G1.ProjectivePoint.fromHex(point);
    }
    function normP2(point) {
        return point instanceof G2.ProjectivePoint ? point : Signature.fromHex(point);
    }
    function normP2Hash(point, htfOpts) {
        return point instanceof G2.ProjectivePoint
            ? point
            : G2.hashToCurve(ensureBytes('point', point), htfOpts);
    }
    // Multiplies generator by private key.
    // P = pk x G
    function getPublicKey(privateKey) {
        return G1.ProjectivePoint.fromPrivateKey(privateKey).toRawBytes(true);
    }
    function sign(message, privateKey, htfOpts) {
        const msgPoint = normP2Hash(message, htfOpts);
        msgPoint.assertValidity();
        const sigPoint = msgPoint.multiply(G1.normPrivateKeyToScalar(privateKey));
        if (message instanceof G2.ProjectivePoint)
            return sigPoint;
        return Signature.toRawBytes(sigPoint);
    }
    // Checks if pairing of public key & hash is equal to pairing of generator & signature.
    // e(P, H(m)) == e(G, S)
    function verify(signature, message, publicKey, htfOpts) {
        const P = normP1(publicKey);
        const Hm = normP2Hash(message, htfOpts);
        const G = G1.ProjectivePoint.BASE;
        const S = normP2(signature);
        // Instead of doing 2 exponentiations, we use property of billinear maps
        // and do one exp after multiplying 2 points.
        const ePHm = pairing(P.negate(), Hm, false);
        const eGS = pairing(G, S, false);
        const exp = Fp12.finalExponentiate(Fp12.mul(eGS, ePHm));
        return Fp12.eql(exp, Fp12.ONE);
    }
    function aggregatePublicKeys(publicKeys) {
        if (!publicKeys.length)
            throw new Error('Expected non-empty array');
        const agg = publicKeys.map(normP1).reduce((sum, p) => sum.add(p), G1.ProjectivePoint.ZERO);
        const aggAffine = agg; //.toAffine();
        if (publicKeys[0] instanceof G1.ProjectivePoint) {
            aggAffine.assertValidity();
            return aggAffine;
        }
        // toRawBytes ensures point validity
        return aggAffine.toRawBytes(true);
    }
    function aggregateSignatures(signatures) {
        if (!signatures.length)
            throw new Error('Expected non-empty array');
        const agg = signatures.map(normP2).reduce((sum, s) => sum.add(s), G2.ProjectivePoint.ZERO);
        const aggAffine = agg; //.toAffine();
        if (signatures[0] instanceof G2.ProjectivePoint) {
            aggAffine.assertValidity();
            return aggAffine;
        }
        return Signature.toRawBytes(aggAffine);
    }
    // https://ethresear.ch/t/fast-verification-of-multiple-bls-signatures/5407
    // e(G, S) = e(G, SUM(n)(Si)) = MUL(n)(e(G, Si))
    function verifyBatch(signature, messages, publicKeys, htfOpts) {
        // @ts-ignore
        // console.log('verifyBatch', bytesToHex(signature as any), messages, publicKeys.map(bytesToHex));
        if (!messages.length)
            throw new Error('Expected non-empty messages array');
        if (publicKeys.length !== messages.length)
            throw new Error('Pubkey count should equal msg count');
        const sig = normP2(signature);
        const nMessages = messages.map((i) => normP2Hash(i, htfOpts));
        const nPublicKeys = publicKeys.map(normP1);
        try {
            const paired = [];
            for (const message of new Set(nMessages)) {
                const groupPublicKey = nMessages.reduce((groupPublicKey, subMessage, i) => subMessage === message ? groupPublicKey.add(nPublicKeys[i]) : groupPublicKey, G1.ProjectivePoint.ZERO);
                // const msg = message instanceof PointG2 ? message : await PointG2.hashToCurve(message);
                // Possible to batch pairing for same msg with different groupPublicKey here
                paired.push(pairing(groupPublicKey, message, false));
            }
            paired.push(pairing(G1.ProjectivePoint.BASE.negate(), sig, false));
            const product = paired.reduce((a, b) => Fp12.mul(a, b), Fp12.ONE);
            const exp = Fp12.finalExponentiate(product);
            return Fp12.eql(exp, Fp12.ONE);
        }
        catch {
            return false;
        }
    }
    G1.ProjectivePoint.BASE._setWindowSize(4);
    return {
        getPublicKey,
        sign,
        verify,
        verifyBatch,
        aggregatePublicKeys,
        aggregateSignatures,
        millerLoop,
        pairing,
        G1,
        G2,
        Signature,
        fields: {
            Fr,
            Fp,
            Fp2,
            Fp6,
            Fp12,
        },
        params: {
            x: CURVE.params.x,
            r: CURVE.params.r,
            G1b: CURVE.G1.b,
            G2b: CURVE.G2.b,
        },
        utils,
    };
}
//# sourceMappingURL=bls.js.map