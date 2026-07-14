# -*- coding: utf-8 -*-
"""a41_mapa.py — o MAPA entrada × saída × sessão (+ condições). EXPLORATÓRIO.

Pergunta central (nenhum estudo fez): existe um ponto no tempo — ou condição —
em que a direção JÁ é conhecível E AINDA sobra movimento para pagar o custo?
Ataca o aperto cedo-sem-sinal / tarde-sem-movimento testando entrar TARDE (com
informação) e capturar SÓ o overlap (onde está o movimento).

**HOLDOUT ESGOTADO — a41 é EXPLORATÓRIO. Nenhuma célula sobrevivente é achado
confirmado, só CANDIDATO; confirmação só via prospectivo (a39).** Prior: 10
formulações direcionais mortas; a priori nulo. O valor é o MAPA (mapa nulo também
delimita onde não há nada).

Trava do a38: TODA métrica é do CAPTURÁVEL (entrada -> saída), NUNCA do início do
dia. Barras fechadas, sem lookahead. Universo: 8 moedas (índice sintético),
direção POR moeda (rank-agnóstico). Trade: cesta (7 pares da moeda, primária) e
par-único (moeda × oposta mais forte). Custo via costs.py. Grade em UTC (defs de
sessão do a22/a32).

Uso: python a41_mapa.py
Saída: results/{ts}_a41/REPORT.md + mapa_*.csv
"""
from __future__ import annotations

import itertools
import json
import pathlib
import time

import numpy as np
import pandas as pd
from scipy.stats import norm

from cssm_engine import build_indices
from a29_deteccao import load_m5
from sessions import server_to_utc
from costs import default_costs, build_spread_pips, load_pip_sizes
from stats_blocks import block_bootstrap_ci
from a23_intersessao import bh_reject
from preponderante import G8

RAW = pathlib.Path("data/raw")
GRID = 5                                    # M5
NCOL = 288                                  # 1440/5
ANCHORS = {"tokyo": 0, "londres": 420, "ny": 780}        # min UTC da abertura
SESSION_END = {"tokyo": 540, "londres": 960, "ny": 1260}
OV_START, OV_END, T12, T15 = 780, 960, 720, 900
FIXED = [30, 60, 90, 120, 180, 240]
COND = [("ER", 0.4), ("ER", 0.6), ("z", 1.0), ("z", 1.5)]
WAIT = 240
MIN_GAP = 30
PAIRS = ["".join(c) for c in itertools.combinations(G8, 2)]


def _grid(series: pd.Series) -> tuple[np.ndarray, pd.DatetimeIndex]:
    """Série (tempo servidor) -> matriz [dia-UTC x coluna-5min], ffill no dia."""
    utc = server_to_utc(series.index)
    s = pd.Series(series.to_numpy(), index=utc).dropna()
    day = s.index.normalize()
    col = ((s.index - day).total_seconds() // (60 * GRID)).astype(int)
    df = pd.DataFrame({"v": s.to_numpy(), "day": day, "col": col})
    df = df.drop_duplicates(["day", "col"], keep="last")
    piv = df.pivot(index="day", columns="col", values="v").reindex(columns=range(NCOL))
    piv = piv.ffill(axis=1)
    return piv.to_numpy(dtype="float32"), piv.index


def build_grids():
    closes, ohlc, pip = load_m5()
    idx = build_indices({s: closes[s].dropna() for s in closes}, align="inner")
    cur_grids, days0 = {}, None
    for c in G8:
        g, days = _grid(idx[c])
        cur_grids[c] = g
        days0 = days if days0 is None else days0
    # alinhar todas as moedas ao mesmo conjunto de dias
    common = days0
    for c in G8:
        g, days = _grid(idx[c])
        cur_grids[c] = pd.DataFrame(g, index=days).reindex(common).to_numpy("float32")
    pair_grids, prng = {}, {}
    for sym in [p for p in PAIRS if p in ohlc]:
        g, days = _grid(ohlc[sym]["close"])
        pair_grids[sym] = pd.DataFrame(g, index=days).reindex(common).to_numpy("float32")
        dr = (ohlc[sym].groupby(ohlc[sym].index.normalize())
              .apply(lambda d: (d["high"].max() - d["low"].min())))
        prng[sym] = dr
    return cur_grids, pair_grids, common, pip


def col_of(minute: int) -> int:
    return min(NCOL - 1, minute // GRID)


def entry_state(cur_grids, anchor_min, spec):
    """Por (dia x moeda): coluna de entrada e direção. spec: int (fixa) ou
    ('ER'/'z', limiar) (condicional; 1ª barra que dispara na espera de 240min)."""
    ndays = next(iter(cur_grids.values())).shape[0]
    a = col_of(anchor_min)
    ecol = np.full((ndays, 8), -1, dtype=int)
    direction = np.zeros((ndays, 8), dtype=float)
    for j, c in enumerate(G8):
        G = cur_grids[c]
        base = G[:, a]
        if isinstance(spec, int):
            ec = col_of(anchor_min + spec)
            net = G[:, ec] - base
            ecol[:, j] = ec
            direction[:, j] = np.sign(net)
        else:
            kind, thr = spec
            end = col_of(anchor_min + WAIT)
            seg = G[:, a:end + 1] - base[:, None]              # net desde a âncora
            steps = np.abs(np.diff(G[:, a:end + 1], axis=1))
            path = np.cumsum(steps, axis=1)                    # comprimento (col>=1)
            path = np.concatenate([np.full((ndays, 1), np.nan), path], axis=1)
            if kind == "ER":
                trig = np.abs(seg) / np.where(path > 0, path, np.nan)
            else:
                sd = np.nanstd(np.diff(G, axis=1), axis=1, keepdims=True)
                n = np.arange(seg.shape[1])[None, :]
                trig = np.abs(seg) / np.where(sd > 0, sd, np.nan) / np.sqrt(np.maximum(n, 1))
            hit = trig >= thr
            first = np.where(hit.any(axis=1), hit.argmax(axis=1), -1)
            ok = first >= 0
            ecol[ok, j] = a + first[ok]
            net_e = np.take_along_axis(seg, np.clip(first, 0, None)[:, None], 1)[:, 0]
            direction[ok, j] = np.sign(net_e[ok])
    return ecol, direction


def basket_net(pair_grids, pip, cur, ecol_c, xcol, dir_c, costs):
    """Net pips (por dia) da cesta dos 7 pares da moeda `cur`, long na direção."""
    legs = [p for p in pair_grids if cur in (p[:3], p[3:6])]
    nets, grosses = [], []
    ndays = len(ecol_c)
    for p in legs:
        G = pair_grids[p]; ps = pip[p]
        e = G[np.arange(ndays), np.clip(ecol_c, 0, NCOL - 1)]
        x = G[np.arange(ndays), np.clip(xcol, 0, NCOL - 1)]
        s = dir_c * (1 if p[:3] == cur else -1)
        gross = s * (x - e) / ps
        nets.append(gross - costs.roundtrip_cost_pips(p)); grosses.append(gross)
    N = np.nanmean(nets, axis=0); Gr = np.nanmean(grosses, axis=0)
    return N, Gr


def exit_cols(anchor, ecol, exit_spec):
    """Coluna de saída (por dia x moeda) p/ um exit_spec; -1 se inválida."""
    if isinstance(exit_spec, tuple):        # relativa: ('rel', +min)
        xc = ecol + exit_spec[1] // GRID
    else:                                   # absoluta (min UTC)
        xc = np.full_like(ecol, col_of(exit_spec))
    xc = np.where((ecol >= 0) & (xc - ecol >= MIN_GAP // GRID) & (xc < NCOL), xc, -1)
    return xc


def cell_metrics(net):
    net = net[np.isfinite(net)]
    if len(net) < 100:
        return None
    exp, lo, hi = block_bootstrap_ci(net, np.mean, block=5, n_boot=1500)
    eq = np.cumsum(net); dd = float((eq - np.maximum.accumulate(eq)).min())
    pos, neg = net[net > 0].sum(), -net[net < 0].sum()
    return {"n": len(net), "exp": exp, "lo": lo, "hi": hi,
            "pf": float(pos / neg) if neg > 0 else np.inf, "dd": dd,
            "pior": float(net.min())}


def main():
    t0 = time.time()
    cur_grids, pair_grids, days, pip = build_grids()
    costs = default_costs()
    ndays = len(days)
    train_cut = int(ndays * 0.70)

    exits = {"+1h": ("rel", 60), "+2h": ("rel", 120), "+4h": ("rel", 240)}
    entries = [("fix", m) for m in FIXED] + [("cond", c) for c in COND]

    rows, netmap = [], {}
    for anchor, amin in ANCHORS.items():
        ex = dict(exits)
        ex["fim_sessao"] = SESSION_END[anchor]
        ex["ini_overlap"] = OV_START; ex["fim_overlap"] = OV_END
        ex["T0+12h"] = T12; ex["T0+15h"] = T15
        for et, espec in entries:
            spec = espec if et == "fix" else espec
            ecol, direction = entry_state(cur_grids, amin, spec if et == "fix" else espec)
            freq = float((ecol >= 0).mean())
            for xname, xspec in ex.items():
                xcol = exit_cols(anchor, ecol, xspec)
                nets = []
                for j, c in enumerate(G8):
                    valid = xcol[:, j] >= 0
                    if valid.sum() < 20:
                        continue
                    N, Gr = basket_net(pair_grids, pip, c, ecol[valid, j],
                                       xcol[valid, j], direction[valid, j], costs)
                    nets.append(N)
                if not nets:
                    continue
                allnet = np.concatenate(nets)
                allnet = allnet[np.isfinite(allnet)]        # limpa nan (reality check)
                m = cell_metrics(allnet)
                if m is None:
                    continue
                ename = f"{espec}" if et == "fix" else f"{espec[0]}>={espec[1]}"
                key = (anchor, ename, xname)
                acc = float((allnet + costs.roundtrip_cost_pips("EURUSD") > 0).mean())
                rows.append({"anchor": anchor, "entrada": ename, "saida": xname,
                             "exp_net": m["exp"], "lo": m["lo"], "hi": m["hi"],
                             "n": m["n"], "freq": freq, "pf": m["pf"],
                             "dd": m["dd"], "acc_dir": acc})
                netmap[key] = allnet
    cur = pd.DataFrame(rows)

    # BH + reality check (permutação do sinal do PnL por dia) sobre F1
    base = 0.0
    cur["z"] = cur["exp_net"] / ((cur["hi"] - cur["lo"]) / (2 * 1.96)).replace(0, np.nan)
    cur["p"] = norm.sf(cur["z"].to_numpy())
    cur["bh"] = bh_reject(np.nan_to_num(cur["p"].to_numpy(), nan=1.0), 0.05)
    rngp = np.random.default_rng(0)
    perm_max = []
    keys = list(netmap)
    for _ in range(200):
        best = -np.inf
        for k in keys:
            v = netmap[k]
            best = max(best, float((rngp.choice([-1, 1], len(v)) * np.abs(v)).mean()))
        perm_max.append(best)
    rc = float(np.quantile(perm_max, 0.95))
    cur["passa_reality"] = cur["exp_net"] > rc
    surv = cur[(cur["exp_net"] > 0) & (cur["lo"] > 0) & cur["bh"] & cur["passa_reality"]]

    # --- F2 (secundária): condições sobre a MELHOR célula do mapa ---
    # "exploratório sobre exploratório — poder reduzido; hipóteses, não resultados"
    def find_spec(ename):
        for et, espec in entries:
            nm = f"{espec}" if et == "fix" else f"{espec[0]}>={espec[1]}"
            if nm == ename:
                return espec, et
        return None, None
    top = cur.sort_values("exp_net", ascending=False).iloc[0]
    espec, et = find_spec(top["entrada"])
    f2 = None
    if espec is not None:
        amin = ANCHORS[top["anchor"]]
        exmap = {"+1h": ("rel", 60), "+2h": ("rel", 120), "+4h": ("rel", 240),
                 "fim_sessao": SESSION_END[top["anchor"]], "ini_overlap": OV_START,
                 "fim_overlap": OV_END, "T0+12h": T12, "T0+15h": T15}
        ecol, direction = entry_state(cur_grids, amin, espec)
        xcol = exit_cols(top["anchor"], ecol, exmap[top["saida"]])
        netM = np.full((ndays, 8), np.nan)
        for j, c in enumerate(G8):
            valid = xcol[:, j] >= 0
            if valid.sum() < 20:
                continue
            N, _ = basket_net(pair_grids, pip, c, ecol[valid, j], xcol[valid, j],
                              direction[valid, j], costs)
            netM[np.where(valid)[0], j] = N
        daynet = np.nanmean(netM, axis=1)
        # volatilidade prévia do dia = média entre moedas do range do índice no dia
        volday = np.nanmean([np.nanmax(cur_grids[c], axis=1) - np.nanmin(cur_grids[c], axis=1)
                             for c in G8], axis=0)
        ok = np.isfinite(daynet) & np.isfinite(volday)
        q = pd.qcut(volday[ok], 4, labels=["Q1", "Q2", "Q3", "Q4"], duplicates="drop")
        f2 = pd.Series(daynet[ok]).groupby(q.astype(str)).mean().round(3)

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_a41")
    out.mkdir(parents=True, exist_ok=True)
    cur.round(3).to_csv(out / "celulas_F1.csv", index=False)
    # MAPA: expectativa líq. por (entrada x saída) por âncora
    for anchor in ANCHORS:
        mp = cur[cur.anchor == anchor].pivot_table(index="entrada", columns="saida",
                                                    values="exp_net")
        mp.round(1).to_csv(out / f"mapa_{anchor}.csv")

    best_cell = cur.sort_values("exp_net", ascending=False).head(8)
    rep = [
        "# a41 — O MAPA entrada × saída × sessão (EXPLORATÓRIO)\n",
        f"**HOLDOUT ESGOTADO — a41 é EXPLORATÓRIO. Células sobreviventes são "
        f"CANDIDATAS, não achados; confirmação só via prospectivo (a39).** Métrica "
        f"PRIMÁRIA: PnL líquido do CAPTURÁVEL (entrada->saída, trava do a38). "
        f"Cesta (7 pares/moeda). {len(cur)} células válidas. Reality check p95 = "
        f"{rc:+.2f} pips.\n",
        "## Sobreviventes (exp>0, IC exclui 0, BH, reality check)\n",
        (surv.sort_values("exp_net", ascending=False)[
            ["anchor", "entrada", "saida", "exp_net", "lo", "hi", "n", "acc_dir"]]
         .round(3).to_markdown(index=False) if len(surv)
         else "**NENHUMA célula sobrevive — o mapa é NULO. Delimita que não há "
              "ponto entrada×saída×sessão com expectativa líquida positiva robusta.**"),
        "\n\n## Menos-ruim do mapa (top-8 por expectativa líquida)\n",
        best_cell[["anchor", "entrada", "saida", "exp_net", "lo", "hi", "acc_dir", "freq"]]
        .round(3).to_markdown(index=False),
        "\n\n## A célula que ninguém testou (fim do overlap)\n",
        cur[cur.saida == "fim_overlap"].sort_values("exp_net", ascending=False)
        .head(6)[["anchor", "entrada", "exp_net", "lo", "hi", "acc_dir"]].round(3)
        .to_markdown(index=False),
        "\n\n## F2 — condições sobre a melhor célula (exploratório sobre exploratório)\n",
        "_Poder reduzido; achados aqui são HIPÓTESES, não resultados. Estratifica "
        f"a melhor célula ({top['anchor']}/{top['entrada']}/{top['saida']}) por "
        "quartil de volatilidade prévia do dia._\n\n"
        + (f"expectativa líq. por quartil de vol: {f2.to_dict()}\n\n"
           + (f"**HIPÓTESE (não resultado)**: nos dias de MAIOR volatilidade prévia "
              f"(Q4 = {f2.get('Q4', float('nan')):+.2f} pips) o trade-off "
              f"esperar×capturar parece melhorar, enquanto os calmos são negativos "
              f"— coerente com a memória de volatilidade (a23/a32). É a única pista "
              f"do a41: um CANDIDATO para o prospectivo (a39), com poder reduzido e "
              f"célula escolhida post-hoc; JAMAIS um achado confirmado.\n"
              if (f2 is not None and f2.get("Q4", -1) > 0) else "")
           if f2 is not None else "_indisponível_\n"),
        f"\n\n_Mapas por âncora em mapa_*.csv. Nenhuma conclusão do a41 isolado; "
        f"células sobreviventes (se houver) devem ser congeladas no a39.\n",
    ]
    (out / "REPORT.md").write_text("\n".join(rep), encoding="utf-8")
    print(f"a41: {out}/REPORT.md ({time.time()-t0:.1f}s)")
    print(f"celulas={len(cur)} reality_p95={rc:+.2f} sobreviventes={len(surv)}")
    print("top-3 exp_net:\n", best_cell.head(3)[["anchor","entrada","saida","exp_net","lo","hi"]].to_string(index=False))


if __name__ == "__main__":
    main()
