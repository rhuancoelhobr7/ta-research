"""r1_relational.py — Camada relacional do CSSM (protótipo).

Restaura a informação que a média da cesta destrói (PLAN: os 8 índices somam
zero — 7 graus de liberdade — enquanto os 28 pares carregam 28):

  1. MOTOR POR PAR: as mesmas features do cssm_engine (t Newey-West, ER, M,
     estados) sobre cada um dos 28 pares diretamente (log-preço).
  2. MATRIZ 8x8: para cada moeda, contra QUEM ela está Madura/Emergindo/
     Exausta/Ruído — a resposta a "essa moeda está nessa tendência SOBRE quem?"
  3. BREADTH ROLANTE + NOWCAST: a tríade do rotulador de tendência absoluta
     (amplitude, magnitude, eficiência) como indicador de tempo real sobre
     barras fechadas — a tendência absoluta EM CURSO, não ex-post.
  4. DOMINÂNCIA: decomposição do M agregado por contraparte — o antídoto da
     contaminação cruzada ("60% da força do EUR vem do lado JPY").

NOTA HONESTA: camada DESCRITIVA (nowcasting/diagnóstico/seleção de par).
Os nulos preditivos do programa (A5/A8/v2) continuam de pé.

Uso:
  python r1_relational.py                          # snapshot na última barra
  python r1_relational.py --date 2026-06-22T12:00  # snapshot em um instante
  python r1_relational.py --tf H1 --w-mid 64 --top 15
Saídas:
  results/{ts}_relational/REPORT.md      (matriz + dominância + top dias)
  data/features/relational_{tf}_w{w}.parquet   (série de breadth/nowcast)
"""
from __future__ import annotations

import argparse, json, pathlib
from datetime import datetime

import numpy as np
import pandas as pd

from cssm_engine import G8, CssmParams, compute_currency, build_indices, tstat_nw

RAW = pathlib.Path("data/raw")
FEAT = pathlib.Path("data/features")
RES = pathlib.Path("results")

STATE_CHAR = {0: "·", 1: "E", 2: "M", 3: "X", -1: " "}
TF_RULES = {"M5": None, "M30": "30min", "H1": "1h", "H4": "4h", "D1": "1D"}


# ----------------------------------------------------------------------------
# Gates calibrados (autossuficiente; taxa de FP ~alvo em random walks)
# ----------------------------------------------------------------------------

def calibrate_gate(w_mid: int, target_fp: float = 0.05, n_walks: int = 20,
                   bars: int = 12000, seed: int = 42) -> float:
    rng = np.random.default_rng(seed)
    ts = []
    for _ in range(n_walks):
        x = np.cumsum(rng.normal(0, 1, bars))
        t = tstat_nw(x, w_mid)
        ts.append(np.abs(t[~np.isnan(t)]))
    allt = np.concatenate(ts)
    return float(np.quantile(allt, 1 - target_fp))


def get_gates(w_mid: int, cache: pathlib.Path = pathlib.Path("data/gates.json")
              ) -> tuple[float, float]:
    """(t_gate, t_low) calibrados p/ FP 5% / 20%, com cache em disco."""
    cache.parent.mkdir(parents=True, exist_ok=True)
    db = json.loads(cache.read_text()) if cache.exists() else {}
    key = str(w_mid)
    if key not in db:
        db[key] = {"t_gate": calibrate_gate(w_mid, 0.05),
                   "t_low": calibrate_gate(w_mid, 0.20)}
        cache.write_text(json.dumps(db, indent=2))
    return db[key]["t_gate"], db[key]["t_low"]


# ----------------------------------------------------------------------------
# Motor por par
# ----------------------------------------------------------------------------

def load_closes(tf: str) -> dict[str, pd.Series]:
    files = [f for f in sorted(RAW.glob("*.parquet"))
             if not f.name.startswith(("_", "D1_"))]
    if not files:
        raise SystemExit("data/raw vazio (contrato no CLAUDE.md).")
    closes = {f.stem: pd.read_parquet(f)["close"] for f in files}
    rule = TF_RULES[tf]
    if rule:
        closes = {s: v.resample(rule, label="right", closed="right")
                  .last().dropna() for s, v in closes.items()}
    return closes


def parse_pair(sym: str) -> tuple[str, str]:
    found = sorted({c for c in G8 if c in sym.upper()},
                   key=lambda c: sym.upper().find(c))
    if len(found) != 2:
        raise ValueError(f"par não-G8: {sym}")
    return found[0], found[1]


def pair_features(closes: dict[str, pd.Series],
                  p: CssmParams) -> dict[str, pd.DataFrame]:
    """Features do motor sobre o LOG-PREÇO de cada par (colunas do engine)."""
    out = {}
    for sym, s in closes.items():
        out[sym] = compute_currency(np.log(s).rename(sym), p)
    return out


def oriented_cell(pf: pd.DataFrame, flip: bool, ts) -> dict | None:
    """Linha do par em ts, orientada (flip inverte t/M/dir; estado mantém)."""
    if ts not in pf.index:
        idx = pf.index[pf.index <= ts]
        if len(idx) == 0:
            return None
        ts = idx[-1]
    r = pf.loc[ts]
    sgn = -1.0 if flip else 1.0
    st = int(r.state) if not np.isnan(r.state) else -1
    return {"t": sgn * r.t, "M": sgn * r.M, "er": r.er,
            "state": st, "dir": sgn * r["dir"]}


# ----------------------------------------------------------------------------
# 1+2. Matriz 8x8 em um instante
# ----------------------------------------------------------------------------

def matrix_at(pfeats: dict[str, pd.DataFrame], ts) -> pd.DataFrame:
    """DataFrame longo: base, contraparte, t, M, er, state, dir (orientado)."""
    rows = []
    for sym, pf in pfeats.items():
        a, b = parse_pair(sym)
        for base, other, flip in ((a, b, False), (b, a, True)):
            c = oriented_cell(pf, flip, ts)
            if c is not None:
                rows.append({"base": base, "vs": other, **c})
    return pd.DataFrame(rows)


def render_matrix(mx: pd.DataFrame) -> str:
    """Matriz compacta: célula = estado+seta orientados (ex.: M↑, E↓, ·)."""
    lines = ["|      | " + " | ".join(f"{c:>3s}" for c in G8) + " |",
             "|---" * 9 + "|"]
    for a in G8:
        cells = []
        for b in G8:
            if a == b:
                cells.append("  —")
                continue
            r = mx[(mx.base == a) & (mx.vs == b)]
            if r.empty or r.iloc[0].state < 0:
                cells.append("  ?")
                continue
            r = r.iloc[0]
            arrow = "↑" if r["dir"] > 0 else ("↓" if r["dir"] < 0 else " ")
            ch = STATE_CHAR[int(r.state)]
            cells.append(f" {ch}{arrow}" if ch != "·" else "  ·")
        lines.append(f"| {a:>4s} | " + " | ".join(cells) + " |")
    lines.append("\nLegenda: M=Madura E=Emergindo X=Exausta ·=Ruído; seta = direção da LINHA vs coluna.")
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# 3. Breadth rolante + nowcast (a tríade do rotulador, em tempo real)
# ----------------------------------------------------------------------------

def breadth_series(pfeats: dict[str, pd.DataFrame],
                   idx_feats: dict[str, pd.DataFrame],
                   t_gate: float) -> pd.DataFrame:
    """Por (timestamp, moeda): breadth soft/hard orientado à direção do índice,
    e nowcast = breadth_dir * min(|t_idx|/gate,1) * er_idx."""
    # t orientado de cada par p/ cada moeda, alinhado num índice comum
    per_cur: dict[str, list[pd.Series]] = {c: [] for c in G8}
    for sym, pf in pfeats.items():
        a, b = parse_pair(sym)
        per_cur[a].append(pf["t"])
        per_cur[b].append(-pf["t"])
    out = []
    for c in G8:
        T = pd.concat(per_cur[c], axis=1)          # colunas = 7 pares
        idx = idx_feats[c]
        d = np.sign(idx["t"]).reindex(T.index)     # direção do índice agregado
        ok = T.notna().sum(axis=1)
        soft = (np.sign(T).mul(d, axis=0) > 0).sum(axis=1) / ok
        hard = ((np.sign(T).mul(d, axis=0) > 0) &
                (T.abs() >= t_gate)).sum(axis=1) / ok
        tt = idx["t"].reindex(T.index)
        er = idx["er"].reindex(T.index)
        now = soft * np.minimum(tt.abs() / t_gate, 1.0) * er
        out.append(pd.DataFrame({"currency": c, "dir": d, "breadth_soft": soft,
                                 "breadth_hard": hard, "t_idx": tt,
                                 "er_idx": er, "nowcast": now,
                                 "n_pairs": ok}, index=T.index))
    return pd.concat(out).reset_index(names="ts")


# ----------------------------------------------------------------------------
# 4. Dominância (decomposição do movimento por contraparte)
# ----------------------------------------------------------------------------

def dominance_at(closes: dict[str, pd.Series], currency: str, ts,
                 w: int) -> pd.DataFrame:
    """Retorno log orientado de cada par da moeda nas últimas w barras até ts,
    com % de participação no total absoluto."""
    rows = []
    for sym, s in closes.items():
        a, b = parse_pair(sym)
        if currency not in (a, b):
            continue
        lp = np.log(s[s.index <= ts])
        if len(lp) < w + 1:
            continue
        ret = float(lp.iloc[-1] - lp.iloc[-1 - w])
        if b == currency:
            ret = -ret
        rows.append({"vs": b if a == currency else a, "ret_bp": ret * 1e4})
    df = pd.DataFrame(rows)
    tot = df.ret_bp.abs().sum()
    df["share_pct"] = 100 * df.ret_bp / tot if tot > 0 else 0.0
    return df.sort_values("ret_bp", ascending=False).reset_index(drop=True)


# ----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tf", default="H1", choices=list(TF_RULES))
    ap.add_argument("--w-mid", type=int, default=64)
    ap.add_argument("--date", default=None,
                    help="instante do snapshot (ISO); default = última barra")
    ap.add_argument("--top", type=int, default=15,
                    help="nº de instantes de maior nowcast a listar")
    a = ap.parse_args()

    t_gate, t_low = get_gates(a.w_mid)
    p = CssmParams(w_mid=a.w_mid, w_fast=max(4, a.w_mid // 4),
                   z_win=min(500, a.w_mid * 8), t_gate=t_gate, t_low=t_low)

    closes = load_closes(a.tf)
    pfeats = pair_features(closes, p)
    indices = build_indices(closes, align="inner")
    idx_feats = {c: compute_currency(indices[c], p) for c in G8}

    common = pfeats[list(pfeats)[0]].index
    ts = pd.Timestamp(a.date) if a.date else common[-1]

    mx = matrix_at(pfeats, ts)
    br = breadth_series(pfeats, idx_feats, t_gate)
    FEAT.mkdir(parents=True, exist_ok=True)
    br.to_parquet(FEAT / f"relational_{a.tf}_w{a.w_mid}.parquet")

    # snapshot de breadth no instante
    snap = br[br.ts == br.ts[br.ts <= ts].max()].sort_values(
        "nowcast", ascending=False)

    out = RES / f"{datetime.now():%Y%m%d_%H%M}_relational"
    out.mkdir(parents=True, exist_ok=True)
    L = [f"# Camada relacional — {a.tf}, w={a.w_mid} "
         f"(gates calibrados: t_gate={t_gate:.2f}, t_low={t_low:.2f})",
         f"\n## Matriz 8×8 em {ts}\n", render_matrix(mx),
         "\n## Breadth / nowcast no instante (ordenado)\n",
         "| moeda | dir | breadth soft | breadth hard | t_idx | ER | nowcast |",
         "|---|---|---|---|---|---|---|"]
    for _, r in snap.iterrows():
        arrow = "↑" if r["dir"] > 0 else "↓"
        L.append(f"| {r.currency} | {arrow} | {r.breadth_soft:.0%} "
                 f"({r.breadth_soft*r.n_pairs:.0f}/{r.n_pairs:.0f}) | "
                 f"{r.breadth_hard:.0%} | {r.t_idx:+.2f} | {r.er_idx:.2f} | "
                 f"{r.nowcast:.3f} |")

    lead = snap.iloc[0]
    dom = dominance_at(closes, lead.currency, ts, a.w_mid)
    L += [f"\n## Dominância — {lead.currency} (últimas {a.w_mid} barras)\n",
          "| vs | ret orientado (bp) | share |", "|---|---|---|"]
    for _, r in dom.iterrows():
        L.append(f"| {r.vs} | {r.ret_bp:+.1f} | {r.share_pct:+.1f}% |")

    hist = (br[br.breadth_hard.notna()]
            .sort_values("nowcast", ascending=False).head(a.top))
    L += [f"\n## Top {a.top} instantes por nowcast (histórico {a.tf})\n",
          "| ts | moeda | dir | soft | hard | nowcast |", "|---|---|---|---|---|---|"]
    for _, r in hist.iterrows():
        arrow = "↑" if r["dir"] > 0 else "↓"
        L.append(f"| {r.ts} | {r.currency} | {arrow} | {r.breadth_soft:.0%} | "
                 f"{r.breadth_hard:.0%} | {r.nowcast:.3f} |")
    L.append("\n*Camada descritiva (nowcasting/diagnóstico). Os resultados "
             "preditivos nulos do programa (A5/A8/v2) permanecem válidos.*")

    (out / "REPORT.md").write_text("\n".join(L), encoding="utf-8")
    print(f"REPORT em {out/'REPORT.md'}")
    print(render_matrix(mx))


if __name__ == "__main__":
    main()
