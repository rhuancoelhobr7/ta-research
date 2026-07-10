# -*- coding: utf-8 -*-
"""a31_par_campeao.py — o par campeão dentro da moeda preponderante.

Dado que uma moeda LÍDER (mais forte do dia, preponderante.py) domina, qual dos
seus 7 pares anda mais? É sempre o mesmo? É a líder contra a ANTI-LÍDER?

Q15 existe sempre um campeão claro (vs movimento distribuído)?
Q16 quanto o campeão anda A MAIS que a média dos outros 6 (pips, ATR, %)?
Q17 estabilidade: líder X -> sempre o mesmo par campeão? (matriz líder×campeão)
Q18 hipótese anti-líder: o campeão é líder×anti-líder? (fração; baseline 1/7)
Q19 o campeão do dia já é o campeão da sessão asia (identificável cedo)?

Campeão ABSOLUTO = maior range em pips (o que o trader captura). Campeão
RELATIVO = maior range/ATR-do-par (controla a largura estrutural) — usado no
Q17/Q18 p/ teste justo. Descritivo, por preço.

Uso: python a31_par_campeao.py
Saída: results/{ts}_a31/REPORT.md + matriz_lider_campeao.csv
"""
from __future__ import annotations

import json
import pathlib
import time

import numpy as np
import pandas as pd

from sessions import SEQ_SESSIONS, session_ranges, daily_range
from a28_preponderante import leaders_panel

RAW = pathlib.Path("data/raw")


def load_pips() -> dict[str, float]:
    meta = json.loads((RAW / "_meta_ta.json").read_text(encoding="utf-8"))
    return {s: v["pip"] for s, v in meta["symbols"].items()}


def pair_of(a: str, b: str, cols: set) -> str | None:
    return a + b if a + b in cols else (b + a if b + a in cols else None)


def build() -> dict:
    pips = load_pips()
    rng, net, asia_rng = {}, {}, {}
    for f in sorted(RAW.glob("M15_*.parquet")):
        sym = f.stem.removeprefix("M15_")
        df = pd.read_parquet(f)
        dr = daily_range(df, pips[sym])
        rng[sym] = dr["day_range"]; net[sym] = dr["day_net"]
        sr = session_ranges(df, pips[sym], SEQ_SESSIONS)
        asia_rng[sym] = sr[sr.session == "asia"].set_index("date")["range_pips"]
    rng = pd.DataFrame(rng); net = pd.DataFrame(net); asia = pd.DataFrame(asia_rng)
    atr = rng.median()                                    # ATR estrutural por par
    return {"rng": rng, "net": net, "asia": asia, "atr": atr}


def main() -> None:
    t0 = time.time()
    B = build()
    rng, net, asia, atr = B["rng"], B["net"], B["asia"], B["atr"]
    cols = set(rng.columns)
    lead = leaders_panel(net, atr)                        # leader/anti por dia

    recs = []
    for date, L in lead.iterrows():
        leader, anti = L["leader"], L["anti_leader"]
        if leader is None or date not in rng.index:
            continue
        lp = [p for p in cols if leader in (p[:3], p[3:6])]   # símbolos REAIS
        r = rng.loc[date, lp].dropna()
        if len(r) < 6:
            continue
        rel = (r / atr[r.index])                          # range/ATR (relativo)
        champ_abs = r.idxmax()
        champ_rel = rel.idxmax()
        others = r.drop(champ_abs)
        anti_pair = pair_of(leader, anti, cols)
        # clareza: campeão vs 2º (absoluto)
        top2 = r.nlargest(2)
        clareza = top2.iloc[0] / top2.iloc[1] if len(top2) > 1 else np.nan
        # asia champion (cedo)
        champ_asia = None
        if date in asia.index:
            ar = asia.loc[date, [p for p in lp if p in asia.columns]].dropna()
            if len(ar) >= 6:
                champ_asia = ar.idxmax()
        recs.append({
            "date": date, "leader": leader, "anti": anti,
            "champ_abs": champ_abs, "champ_rel": champ_rel,
            "champ_range": r[champ_abs], "mean_others": others.mean(),
            "excess_pips": r[champ_abs] - others.mean(),
            "excess_ratio": r[champ_abs] / others.mean() if others.mean() else np.nan,
            "excess_atr": (r[champ_abs] - others.mean()) / atr[champ_abs],
            "champ_share": r[champ_abs] / r.sum(),
            "clareza": clareza, "anti_pair": anti_pair,
            "is_anti_rel": champ_rel == anti_pair,
            "is_anti_abs": champ_abs == anti_pair,
            "champ_asia": champ_asia, "asia_hits": champ_asia == champ_abs,
        })
    d = pd.DataFrame(recs)

    # Q15 — clareza
    clear_frac = float((d["clareza"] >= 1.3).mean())
    share_med = float(d["champ_share"].median())
    # Q16 — quanto anda a mais
    q16 = d[["excess_pips", "excess_ratio", "excess_atr"]].describe(
        percentiles=[0.25, 0.5, 0.75, 0.9]).loc[["50%", "25%", "75%", "90%"]]
    # Q17 — estabilidade (matriz líder x campeão_rel: top share por líder)
    mat = (d.groupby("leader")["champ_rel"].agg(
        top=lambda s: s.value_counts().index[0],
        top_share=lambda s: s.value_counts(normalize=True).iloc[0],
        n=lambda s: len(s)))
    # Q18 — hipótese anti-líder
    anti_rel = float(d["is_anti_rel"].mean())
    anti_abs = float(d["is_anti_abs"].mean())
    # Q19 — identificável cedo
    early = float(d["asia_hits"].dropna().mean())

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_a31")
    out.mkdir(parents=True, exist_ok=True)
    mat.round(3).to_csv(out / "matriz_lider_campeao.csv")

    rep = [
        "# a31 — O par campeão dentro da moeda preponderante\n",
        f"{len(d)} dias com líder definida. Campeão ABS = maior range (pips); "
        f"REL = maior range/ATR (controla largura estrutural).\n",
        "## Q15 — Existe campeão claro?\n",
        f"- campeão >=1.3x o 2º par em **{clear_frac:.0%}** dos dias; o campeão "
        f"concentra mediana **{share_med:.0%}** do range somado dos 7 pares.\n",
        "## Q16 — Quanto o campeão anda A MAIS que a média dos outros 6\n",
        q16.round(2).to_markdown(),
        f"\n_Mediana: +{d['excess_pips'].median():.0f} pips "
        f"(+{d['excess_atr'].median():.2f} ATR, "
        f"{d['excess_ratio'].median():.2f}x a média dos outros 6)._\n",
        "## Q17 — Estabilidade (líder -> par campeão mais frequente, share)\n",
        mat.round(3).to_markdown(),
        "\n_top_share alto = quase sempre o mesmo par; baixo = muda muito._\n",
        "## Q18 — Hipótese anti-líder (campeão = líder x anti-líder?)\n",
        f"- campeão REL é líder×anti-líder em **{anti_rel:.0%}** (baseline 1/7 = 14%).",
        f"\n- campeão ABS é líder×anti-líder em **{anti_abs:.0%}**.",
        f"\n\n_{'Confirma: a anti-líder resolve boa parte da seleção do par.' if anti_rel > 0.25 else 'Fraco: a anti-líder não determina o campeão.'}_\n",
        "## Q19 — O campeão é identificável cedo (sessão asia)?\n",
        f"- campeão da asia == campeão do dia em **{early:.0%}** dos dias "
        f"(baseline 1/7 = 14%).\n",
    ]
    (out / "REPORT.md").write_text("\n".join(rep), encoding="utf-8")
    print(f"a31: {out}/REPORT.md ({time.time()-t0:.1f}s)")
    print(f"Q15 claro>=1.3x: {clear_frac:.0%}; share campeao {share_med:.0%}")
    print(f"Q16 excesso mediano: +{d['excess_pips'].median():.0f} pips "
          f"(+{d['excess_atr'].median():.2f} ATR)")
    print(f"Q18 anti-lider rel {anti_rel:.0%} / abs {anti_abs:.0%} (base 14%)")
    print(f"Q19 identificavel na asia: {early:.0%} (base 14%)")
    print("Q17 matriz lider->campeao:\n", mat.round(2).to_string())


if __name__ == "__main__":
    main()
