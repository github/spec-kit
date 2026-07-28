#!/usr/bin/env python3
"""Pipeline de clasificacion de modelos del orquestador.

Pasos:
1. Listar modelos del CLI (opencode models)
2. Traer datos de OpenRouter (3 llamadas JSON)
3. Matchear modelos del CLI <-> slugs OpenRouter
4. Aplicar regla de niveles (1-5)
5. Salida: mapa nivel -> modelos
"""
import json
import re
import subprocess
import urllib.request

OR = "https://openrouter.ai"


def fetch(url):
    with urllib.request.urlopen(url) as r:
        return json.load(r)


def paso1_modelos_cli():
    out = subprocess.run(["opencode", "models"], capture_output=True, text=True)
    return [l.strip() for l in out.stdout.splitlines() if l.strip()]


def paso2_datos_openrouter():
    models = fetch(f"{OR}/api/v1/models")["data"]
    bench = fetch(f"{OR}/api/frontend/v1/rankings/benchmarks")["data"]["aaData"]
    perf = fetch(f"{OR}/api/frontend/v1/rankings/performance")["data"]
    return models, bench, perf


def normalizar(nombre):
    """'9router/cc/claude-opus-4-8' -> 'claude-opus-4-8' (sin variante)."""
    base = nombre.split("/")[-1]
    base = re.sub(r"-(review|highspeed|thinking|free)$", "", base)
    base = re.sub(r"-\d{8}$", "", base)  # fecha tipo -20251001
    return base


def paso3_matchear(cli_models, or_models):
    """Matcheo por similitud de nombre normalizado contra el final del slug OR."""
    or_by_id = {m["id"]: m for m in or_models}
    matches, sin_match = {}, []
    for cm in cli_models:
        base = normalizar(cm)
        # candidatos: slug OR cuya parte final (sin autor) contiene el nombre base
        # con separadores normalizados (. y - equivalentes)
        norm = lambda s: s.lower().replace(".", "-").replace("_", "-")
        nb = norm(base)
        cands = [mid for mid in or_by_id if nb in norm(mid.split("/")[-1])]
        # elegir el candidato mas corto (mas especifico), preferir sin ':'
        cands = [c for c in cands if ":" not in c] or cands
        if cands:
            matches[cm] = min(cands, key=len)
        else:
            sin_match.append(cm)
    return matches, sin_match, or_by_id


# Alias manuales: modelo sin slug propio -> slug del que hereda los datos
ALIAS = {
    "anthropic/claude-fable-5": "anthropic/claude-5-fable-20260609",
    "anthropic/claude-haiku-4.5": "anthropic/claude-4.5-haiku-20251001",
    "moonshotai/kimi-latest": "moonshotai/kimi-k3",
    "google/gemini-3-flash-preview": None,   # sin datos AA: preview deprecado
    "poolside/laguna-s-2.1": None,           # sin datos AA: modelo de nicho
}


def paso4_clasificar(matches, or_by_id, bench, perf):
    # inteligencia: percentiles 0-100 (inteligencia) para TODOS los modelos
    pct = bench["percentilesBySlug"]

    def intel_de(or_id):
        slug = ALIAS.get(or_id.lstrip("~"), or_id.lstrip("~"))
        if slug is None:
            return None
        # quitar sufijo de fecha tipo -0905 o -20251001 y reintentar alias
        base = re.sub(r"-\d{4,8}$", "", slug)
        slug = ALIAS.get(base, base)
        if slug is None:
            return None
        if slug in pct:
            return pct[slug]["intelligence"]
        # variante con fecha u otro sufijo
        cands = [k for k in pct if k.startswith(slug) or slug.startswith(k)]
        return pct[cands[0]]["intelligence"] if cands else None

    speed = {}
    for p in perf:
        base = re.sub(r"-\d{8}$", "", p["slug"])
        cur = speed.get(base)
        if not cur or (p.get("p50_throughput") or 0) > (cur.get("p50_throughput") or 0):
            speed[base] = p

    niveles = {1: [], 2: [], 3: [], 4: [], 5: []}
    detalle = {}
    for cm, or_id in matches.items():
        m = or_by_id[or_id]
        score = intel_de(or_id)
        p = speed.get(or_id, {})
        thr = p.get("p50_throughput") or 0
        pin = float(m["pricing"]["prompt"]) * 1e6

        # regla de niveles: percentil de inteligencia (0-100)
        if score is None:
            # sin datos AA: respaldo por velocidad + precio (datos reales)
            if pin <= 0.30:
                nivel = 1
            elif thr > 100 and pin < 1.0:
                nivel = 2
            elif pin < 1.0:
                nivel = 2
            else:
                nivel = 3
        elif score >= 90:
            nivel = 5
        elif score >= 75:
            nivel = 4
        elif score >= 55:
            nivel = 3
        elif score >= 40:
            nivel = 2
        else:
            nivel = 1

        if nivel:
            niveles[nivel].append(cm)
        detalle[cm] = {"or": or_id, "nivel": nivel, "intel": score,
                       "tok_s": thr, "usd_m": pin}
    return niveles, detalle


def main():
    print("PASO 1: modelos del CLI")
    cli_models = paso1_modelos_cli()
    print(f"  {len(cli_models)} modelos")

    print("PASO 2: datos OpenRouter")
    or_models, bench, perf = paso2_datos_openrouter()
    print(f"  {len(or_models)} modelos, {len(bench['percentilesBySlug'])} percentiles, {len(perf)} perf")

    print("PASO 3: matcheo")
    matches, sin_match, or_by_id = paso3_matchear(cli_models, or_models)
    print(f"  {len(matches)} matcheados, {len(sin_match)} sin match")

    print("PASO 4: clasificacion")
    niveles, detalle = paso4_clasificar(matches, or_by_id, bench, perf)

    print("\nPASO 5: RESULTADO")
    for n in range(5, 0, -1):
        print(f"\nNIVEL {n}:")
        for cm in niveles[n]:
            d = detalle[cm]
            i = str(d["intel"]) if d["intel"] is not None else "est"
            print(f"  {cm:45} intel={i:>3} {d['tok_s']:>5} tok/s  ${d['usd_m']:.2f}/M")
    if sin_match:
        print("\nSIN MATCH EN OPENROUTER:", *sin_match, sep="\n  ")


if __name__ == "__main__":
    main()
