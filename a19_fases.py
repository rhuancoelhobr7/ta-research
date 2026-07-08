# -*- coding: utf-8 -*-
"""a19_fases.py — Ciclo de fases do CSS (FORÇA→EXAUSTÃO→FRAQUEZA→EXPANSÃO).

Pré-registro no CHANGELOG (2026-07-08). Lente: css_screen (leitura ao
vivo, causal — ver decisão registrada; a TMA literal dos buffers é
centrada e vazaria futuro em Q3). Dados: H1 10 anos × 28 pares
(s2_export_h1.py), H4/D1/W1/MN reamostrados.

FASES (ciclo comprador; val COM sinal; delta = val_t − val_{t−3}):
  FORÇA     val >= +box e delta >= 0     (topo, enchendo)
  EXAUSTÃO  val >= +box e delta <  0     (topo, esvaziando — o "!")
  FRAQUEZA  val <  +box e delta <  0     (caindo)
  EXPANSÃO  val <  +box e delta >  0     (virou o fundo, subindo)
  delta == 0 fora da box: mantém a fase anterior (ffill).
Ciclo espelho (vendedor): mesmas fases com sinais invertidos.

Perguntas Q1–Q6 e critérios: ver CHANGELOG. Q3 usa bootstrap em blocos
(dia) + Benjamini-Hochberg. Nulo é resultado aceitável.

GATE: só executar após paridade MQ5×Python (p2_css_parity) confirmada.

Uso: python a19_fases.py [--tfs H1,H4,D1,W1,MN] [--breadth]
Saída: results/{ts}_a19/REPORT.md (+ fases_{tf}.parquet p/ o a20)
"""
from __future__ import annotations

import argparse, json, pathlib, time

import numpy as np
import pandas as pd

from css_classic import G8
from css_screen import BOX, KSLOPE, css_screen_lines, pair_contribution
from stats_blocks import block_bootstrap_ci

RAW = pathlib.Path("data/raw")
EXT = 0.50
FASES = ["FORCA", "EXAUSTAO", "FRAQUEZA", "EXPANSAO"]
ROTACAO = {"FORCA": "EXAUSTAO", "EXAUSTAO": "FRAQUEZA",
           "FRAQUEZA": "EXPANSAO", "EXPANSAO": "FORCA"}
HORIZONTES = (1, 3, 5, 10)
TF_RULES = {"H1": None, "H4": "4h", "D1": "1D", "W1": "W-FRI", "MN": "ME"}


# ----------------------------------------------------------------------------
# Dados e linhas
# ----------------------------------------------------------------------------

def load_h1_closes() -> pd.DataFrame:
    files = sorted(RAW.glob("H1_*.parquet"))
    if not files:
        raise SystemExit("sem data/raw/H1_*.parquet — rode s2_export_h1.py")
    # sem ffill: cada par calcula na sequência nativa (semântica MQ5)
    return pd.DataFrame({f.stem.removeprefix("H1_"):
                         pd.read_parquet(f)["close"] for f in files})


def grid_tf(h1: pd.DataFrame, tf: str) -> pd.DataFrame:
    rule = TF_RULES[tf]
    if rule is None:
        return h1
    return h1.resample(rule).last().dropna(how="all")


def classify_phases(lines: pd.DataFrame, box: float = BOX,
                    k: int = KSLOPE, mirror: bool = False) -> pd.DataFrame:
    """Fase por moeda×barra do ciclo comprador (mirror=True: vendedor)."""
    val = -lines if mirror else lines
    delta = val - val.shift(k)
    ph = pd.DataFrame(np.nan, index=val.index, columns=val.columns, dtype=object)
    ph[(val >= box) & (delta >= 0)] = "FORCA"
    ph[(val >= box) & (delta < 0)] = "EXAUSTAO"
    ph[(val < box) & (delta < 0)] = "FRAQUEZA"
    ph[(val < box) & (delta > 0)] = "EXPANSAO"
    # delta==0 dentro/abaixo da box: mantém fase anterior
    return ph.ffill()


def breadth_hard(closes: pd.DataFrame, lines: pd.DataFrame) -> pd.DataFrame:
    """Nº de pares da moeda cuja contribuição orientada confirma o sinal
    da linha (lição do a11; hard = >=3/7)."""
    conf = pd.DataFrame(0, index=lines.index, columns=G8)
    for sym in closes.columns:
        b, q = sym[:3], sym[3:6]
        if b not in G8 or q not in G8:
            continue
        v = pair_contribution(closes[sym])
        conf[b] += (np.sign(v) == np.sign(lines[b])).astype(int)
        conf[q] += (np.sign(-v) == np.sign(lines[q])).astype(int)
    return conf


# ----------------------------------------------------------------------------
# Q1/Q2/Q4 — mecânica do ciclo (por moeda×TF)
# ----------------------------------------------------------------------------

def transitions(ph: pd.Series) -> pd.DataFrame:
    """Matriz de transição entre fases DISTINTAS consecutivas."""
    s = ph.dropna()
    changed = s[s != s.shift(1)]
    t = pd.crosstab(changed.shift(1), changed).reindex(
        index=FASES, columns=FASES, fill_value=0)
    return t


def rotation_rate(ph: pd.Series) -> tuple[int, int]:
    """(rotações completas, saídas de FORÇA): saída de FORÇA que percorre
    EXAUSTÃO→FRAQUEZA→EXPANSÃO→FORÇA na ordem, sem voltar antes."""
    seq = ph.dropna()
    seq = seq[seq != seq.shift(1)].tolist()
    exits = ok = 0
    for i, f in enumerate(seq[:-1]):
        if f != "FORCA":
            continue
        exits += 1
        expected = ["EXAUSTAO", "FRAQUEZA", "EXPANSAO", "FORCA"]
        j, pos = i + 1, 0
        good = True
        while j < len(seq) and pos < 4:
            if seq[j] == expected[pos]:
                pos += 1
            elif seq[j] == "FORCA":
                good = False
                break
            else:
                good = False
                break
            j += 1
        ok += good and pos == 4
    return ok, exits


def dwell_times(ph: pd.Series) -> dict[str, np.ndarray]:
    s = ph.dropna()
    grp = (s != s.shift(1)).cumsum()
    runs = s.groupby(grp).agg(["first", "size"])
    return {f: runs[runs["first"] == f]["size"].to_numpy() for f in FASES}


def whipsaw_rate(lines: pd.Series, box: float = BOX) -> tuple[float, int]:
    """% de saídas de |val|>=box que voltam pra dentro em <=2 barras."""
    out = lines.abs() >= box
    exits = np.nonzero(out.to_numpy() & ~out.shift(1, fill_value=False).to_numpy())[0]
    n = whip = 0
    arr = out.to_numpy()
    for i in exits:
        n += 1
        end = min(i + 3, len(arr))
        run = arr[i:end]
        whip += not run.all()          # voltou pra box em <=2 barras
    return (whip / n if n else np.nan), n


# ----------------------------------------------------------------------------
# Q3 — retorno futuro condicionado à fase (BH sobre as células)
# ----------------------------------------------------------------------------

def q3_conditional(ph: pd.DataFrame, idx: pd.DataFrame, tf: str,
                   mask: pd.DataFrame | None) -> list[dict]:
    cells = []
    for c in G8:
        p = ph[c]
        if mask is not None:
            p = p.where(mask[c])
        for h in HORIZONTES:
            fwd = idx[c].shift(-h) - idx[c]
            for f in FASES:
                sel = fwd[(p == f) & fwd.notna()]
                if len(sel) < 50:
                    continue
                days = sel.index.normalize()
                # bootstrap em blocos por DIA com pooling PONDERADO:
                # reamostra dias inteiros e recalcula a média por barra.
                # (bootstrap de médias diárias não-ponderadas enviesa: dias
                # com 1-2 barras na fase são dias de reversão rápida e
                # dominariam o IC — bug pego na 1ª execução, corrigido
                # antes de publicar.)
                vals = sel.to_numpy()
                sums = pd.Series(vals).groupby(days.values).agg(["sum", "size"])
                if len(sums) < 20:
                    continue
                s_arr, n_arr = sums["sum"].to_numpy(), sums["size"].to_numpy()
                rng_ = np.random.default_rng(hash((tf, c, f, h)) % 2**32)
                pick = rng_.integers(0, len(s_arr), size=(400, len(s_arr)))
                bs = s_arr[pick].sum(axis=1) / n_arr[pick].sum(axis=1)
                lo, hi = np.percentile(bs, [2.5, 97.5])
                mean = vals.mean()
                pval = 2 * min((bs <= 0).mean(), (bs >= 0).mean())
                cells.append({"tf": tf, "cur": c, "fase": f, "h": h,
                              "n": len(sel), "mean_bps": mean * 1e4,
                              "lo": lo * 1e4, "hi": hi * 1e4, "p": max(pval, 1/400)})
    return cells


def bh_correct(cells: list[dict], alpha: float = 0.05) -> int:
    if not cells:
        return 0
    ps = sorted((c["p"], i) for i, c in enumerate(cells))
    m = len(ps)
    k_sig = 0
    for rank, (p, i) in enumerate(ps, 1):
        if p <= alpha * rank / m:
            k_sig = rank
    thresh = ps[k_sig - 1][0] if k_sig else 0.0
    for c in cells:
        c["bh_sig"] = c["p"] <= thresh and k_sig > 0
    return sum(c["bh_sig"] for c in cells)


# ----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tfs", default="H1,H4,D1,W1,MN")
    a = ap.parse_args()
    tfs = a.tfs.split(",")

    h1 = load_h1_closes()
    from cssm_engine import build_indices
    out = pathlib.Path(f"results/{time.strftime('%Y%m%d_%H%M%S')}_a19")
    out.mkdir(parents=True, exist_ok=True)

    lines_rep = [f"# a19 — Ciclo de fases do CSS ({','.join(tfs)}; "
                 f"H1 10a, 28 pares)", "",
                 "Pré-registro CHANGELOG 2026-07-08. Lente causal "
                 "(css_screen, leitura ao vivo). Nulo é resultado.", ""]

    all_cells, all_cells_b = [], []
    for tf in tfs:
        g = grid_tf(h1, tf)
        lines = css_screen_lines(g)
        idx = build_indices({c: g[c] for c in g.columns}, align="inner")
        ph = classify_phases(lines)
        ph_m = classify_phases(lines, mirror=True)
        bh_ = breadth_hard(g, lines)
        mask = bh_ >= 3

        ph.to_parquet(out / f"fases_{tf}.parquet")
        lines.to_parquet(out / f"lines_{tf}.parquet")
        mask.to_parquet(out / f"breadth_{tf}.parquet")

        # ---- Q1: transições agregadas + rotação --------------------------
        T = sum(transitions(ph[c]) for c in G8)
        Tn = T.div(T.sum(axis=1), axis=0).round(3)
        rot_ok = rot_ex = 0
        for c in G8:
            o, e = rotation_rate(ph[c])
            rot_ok += o; rot_ex += e
        lines_rep += [f"## {tf} — Q1: matriz de transição (linhas→colunas, "
                      f"normalizada; ciclo comprador + espelho é simétrico)",
                      "", Tn.to_markdown(), "",
                      f"Rotação completa: **{rot_ok}/{rot_ex} "
                      f"({100*rot_ok/max(rot_ex,1):.1f}%)** das saídas de "
                      f"FORÇA percorrem o ciclo na ordem.", ""]
        # dominância da rotação: prob. média da transição "canônica"
        dom = np.mean([Tn.loc[f, ROTACAO[f]] for f in FASES])
        lines_rep.append(f"Prob. média da transição canônica: **{dom:.3f}** "
                         f"(H0 uniforme = 0.333)\n")

        # ---- Q1b: val na transição EXAUSTAO->FRAQUEZA ---------------------
        vals_tr = []
        for c in G8:
            s = ph[c].dropna()
            ch = s[s != s.shift(1)]
            m_ = (ch == "FRAQUEZA") & (ch.shift(1) == "EXAUSTAO")
            vals_tr += lines[c].reindex(ch[m_].index).dropna().tolist()
        if vals_tr:
            v = pd.Series(vals_tr)
            lines_rep += [f"Q1b — val na transição EXAUSTÃO→FRAQUEZA: mediana "
                          f"{v.median():.3f}, IQR [{v.quantile(.25):.3f}, "
                          f"{v.quantile(.75):.3f}]; fração em [0.4,0.6]: "
                          f"{((v>=.4)&(v<=.6)).mean():.1%} (nível 0.50 "
                          f"{'tem alguma base' if ((v>=.4)&(v<=.6)).mean()>0.3 else 'parece decoração'})", ""]

        # ---- Q2: dwell + hazard -------------------------------------------
        lines_rep += [f"### {tf} — Q2: dwell (mediana de barras por fase)", "",
                      "| fase | n runs | mediana | p90 |", "|---|---|---|---|"]
        for f in FASES:
            d = np.concatenate([dwell_times(ph[c])[f] for c in G8])
            if len(d):
                lines_rep.append(f"| {f} | {len(d)} | {np.median(d):.0f} | "
                                 f"{np.percentile(d,90):.0f} |")
        # hazard fora da box
        surv = []
        for c in G8:
            for f in ("FORCA", "EXAUSTAO"):
                surv += dwell_times(ph[c])[f].tolist()
        if surv:
            s = np.array(surv)
            hz = [(n, ((s == n).sum() / max((s >= n).sum(), 1)))
                  for n in (1, 2, 3, 5, 8, 13)]
            lines_rep += ["", "Hazard de sair do topo (prob. de a fase acabar "
                          "na barra n dado que durou n): " +
                          ", ".join(f"n={n}: {h:.2f}" for n, h in hz), ""]

        # ---- Q4: whipsaw ---------------------------------------------------
        wr = [whipsaw_rate(lines[c]) for c in G8]
        wmean = np.nanmean([w for w, _ in wr])
        lines_rep += [f"Q4 — whipsaw (reversão à box em ≤2 barras): "
                      f"**{wmean:.1%}** das saídas ({sum(n for _, n in wr)} "
                      f"saídas)", ""]

        # ---- Q5: percentis dos limiares ------------------------------------
        av = lines.abs().stack().dropna()
        p20 = (av <= 0.20).mean() * 100
        p50 = (av <= 0.50).mean() * 100
        lines_rep += [f"Q5 — |val|: 0.20 = p{p20:.0f}; 0.50 = p{p50:.0f} "
                      f"(mediana |val| = {av.median():.3f})", ""]

        # ---- Q3 (+Q6 versão breadth) ---------------------------------------
        all_cells += q3_conditional(ph, idx, tf, None)
        all_cells_b += q3_conditional(ph, idx, tf, mask)

    # ---- Q3: BH sobre todas as células -----------------------------------
    for nome, cells in (("sem filtro", all_cells),
                        ("breadth>=3/7 (Q6)", all_cells_b)):
        nsig = bh_correct(cells)
        lines_rep += [f"## Q3 — retorno futuro condicionado à fase "
                      f"({nome}): {len(cells)} células, "
                      f"**{nsig} sobrevivem a Benjamini-Hochberg (5%)**", ""]
        sig = [c for c in cells if c.get("bh_sig")]
        if sig:
            lines_rep += ["| tf | moeda | fase | h | n | média (bps) | IC95% |",
                          "|---|---|---|---|---|---|---|"]
            for c in sorted(sig, key=lambda x: x["p"])[:25]:
                lines_rep.append(
                    f"| {c['tf']} | {c['cur']} | {c['fase']} | {c['h']} | "
                    f"{c['n']} | {c['mean_bps']:+.2f} | "
                    f"[{c['lo']:+.2f}, {c['hi']:+.2f}] |")
            lines_rep.append("")
        else:
            lines_rep.append("Nenhuma célula significativa — NULO "
                             "(aceitável e publicável, como pré-registrado).\n")

    (out / "params.json").write_text(json.dumps(
        {"tfs": tfs, "box": BOX, "k": KSLOPE, "ext": EXT,
         "horizontes": HORIZONTES, "breadth_hard": 3}, indent=2))
    (out / "REPORT.md").write_text("\n".join(lines_rep), encoding="utf-8")
    print(f"REPORT -> {out}/REPORT.md")


if __name__ == "__main__":
    main()
