# -*- coding: utf-8 -*-
"""a26_anatomia.py — anatomia dos dias valiosos vs mortos (costura a agenda).

Ao nível de MOEDA. Atividade da moeda no dia = média do range normalizado
(range/mediana-causal-do-par) dos seus 7 pares. Líder = moeda mais ativa;
dispersão = espalhamento das 8 moedas. Dia "com destaque" (os ~valiosos) vs dia
"morto" (moedas amontoadas).

Q11 — nos dias com moeda de range alto: a líder era identificável NA VIRADA
     (estado CSS de manhã, pré-Tokyo 00:00 UTC) ou só óbvia depois?
Q12 — nos dias mortos: há assinatura prévia (ranking amontoado = baixa dispersão
     de pct de manhã)? Dá pra saber "hoje é dia de ficar de fora"?
Q13 — persistência de liderança: a líder de hoje repete amanhã? (vs base 1/8.)

Descritivo, sem lookahead (estado de manhã usa barras fechadas < 00:00 UTC).
Amarra ao a24: se a líder NÃO é identificável de manhã, confirma o CSS não-
preditivo. Uso: python a26_anatomia.py
Saída: results/{ts}_a26/REPORT.md + perfil_dias.csv
"""
from __future__ import annotations

import json
import pathlib
import time
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", message="Mean of empty slice")

from sessions import daily_range
from a24_preditores import css_state_at_turns, TFS, G8

RAW = pathlib.Path("data/raw")
STANDOUT_THR = 1.5   # líder ≥50% acima da norma das suas moedas = dia com destaque


def load_pips() -> dict[str, float]:
    meta = json.loads((RAW / "_meta_ta.json").read_text(encoding="utf-8"))
    return {s: v["pip"] for s, v in meta["symbols"].items()}


def currency_activity() -> pd.DataFrame:
    """Atividade normalizada por moeda×dia (média dos 7 pares da moeda)."""
    pips = load_pips()
    pair_norm = {}
    for f in sorted(RAW.glob("M15_*.parquet")):
        sym = f.stem.removeprefix("M15_")
        dr = daily_range(pd.read_parquet(f), pips[sym])["day_range"]
        med = dr.rolling(60, min_periods=20).median().shift(1)   # causal
        pair_norm[sym] = dr / med
    pn = pd.DataFrame(pair_norm)
    act = {}
    for cur in G8:
        cols = [s for s in pn.columns if cur in s]
        act[cur] = pn[cols].mean(axis=1)
    return pd.DataFrame(act).dropna(how="all")


def main() -> None:
    t0 = time.time()
    act = currency_activity()
    leader = act.idxmax(axis=1)
    leader_act = act.max(axis=1)
    dispersion = act.std(axis=1)
    standout = leader_act >= STANDOUT_THR
    frac_standout = float(standout.mean())
    # sensibilidade do threshold (o "88%" da spec era outra métrica — tendência
    # absoluta do projeto CSSM, não destaque de RANGE)
    frac_thr = {t: float((leader_act >= t).mean()) for t in (1.2, 1.3, 1.5, 2.0)}

    # estado CSS de manhã (pré-Tokyo 00:00 UTC), por moeda
    dates = pd.DatetimeIndex(act.index)
    state = css_state_at_turns(dates, "pct200", turn_h=0)
    # extremidade de pct de manhã por moeda = média_TF |pct-50|
    extrem = pd.DataFrame(index=state.index)
    disp_css = pd.DataFrame(index=state.index)
    pct_by_cur = {}
    for c in G8:
        cols = [f"{c}|pct|{tf}" for tf in TFS]
        pct_by_cur[c] = state[cols].mean(axis=1)
        extrem[c] = (state[cols] - 50).abs().mean(axis=1)
    pct_df = pd.DataFrame(pct_by_cur)
    css_dispersion = pct_df.std(axis=1)          # espalhamento do ranking de manhã

    # Q11: a moeda mais extrema de manhã é a líder do dia?
    css_leader = extrem.idxmax(axis=1)
    j = pd.concat({"leader": leader, "css_leader": css_leader,
                   "standout": standout}, axis=1).dropna()
    js = j[j["standout"]]
    hit_css = float((js["leader"] == js["css_leader"]).mean())
    # baseline: escolher pela maior atividade de ONTEM (persistência) prevê hoje?
    lead_prev = leader.shift(1)
    jp = pd.concat({"leader": leader, "prev": lead_prev, "standout": standout},
                   axis=1).dropna()
    hit_prev = float((jp[jp["standout"]]["leader"] == jp[jp["standout"]]["prev"]).mean())

    # Q12: dispersão CSS de manhã em dias mortos vs destaque
    cd = pd.concat({"css_disp": css_dispersion, "standout": standout,
                    "disp": dispersion}, axis=1).dropna()
    css_disp_standout = cd[cd["standout"]]["css_disp"].median()
    css_disp_dead = cd[~cd["standout"]]["css_disp"].median()

    # Q13: persistência de liderança dia-a-dia
    persist = float((leader.values[1:] == leader.values[:-1]).mean())

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_a26")
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"leader": leader, "leader_act": leader_act,
                  "dispersion": dispersion, "standout": standout}).to_csv(
        out / "perfil_dias.csv")

    q11 = ("líder NÃO identificável de manhã (CSS não antecipa)"
           if hit_css < 2 * (1 / 8) else "líder parcialmente identificável de manhã")
    q12 = ("dia morto TEM assinatura (ranking mais amontoado de manhã)"
           if css_disp_dead < 0.9 * css_disp_standout
           else "dia morto SEM assinatura prévia clara")
    q13 = ("persistência de liderança ACIMA do acaso"
           if persist > 1.5 * (1 / 8) else "persistência de liderança ~ acaso (nula)")
    rep = [
        "# a26 — Anatomia dos dias valiosos vs mortos\n",
        f"Nível de moeda, {len(act)} dias, {act.index.min().date()} → "
        f"{act.index.max().date()}. Dia com destaque = líder ≥{STANDOUT_THR}× a "
        f"norma: **{frac_standout:.0%}** dos dias (mortos: {1-frac_standout:.0%}). "
        f"Estado CSS de manhã (pré-Tokyo, sem lookahead).\n",
        "_Sensibilidade (fração de dias com destaque por threshold): "
        + ", ".join(f"{t}×={f:.0%}" for t, f in frac_thr.items())
        + ". O '~88%' da spec era outra métrica (tendência absoluta do projeto "
        "CSSM), não destaque de range._\n",
        "## Q11 — a líder era identificável na virada?\n",
        f"- acerto usando a moeda MAIS EXTREMA no CSS de manhã: **{hit_css:.1%}** "
        f"(acaso = 12.5%).",
        f"\n- acerto usando a líder de ONTEM (persistência): {hit_prev:.1%}.",
        f"\n\n_→ {q11}._\n",
        "## Q12 — dias mortos têm assinatura prévia?\n",
        f"- dispersão do ranking CSS de manhã — destaque: **{css_disp_standout:.1f}** "
        f"vs morto: **{css_disp_dead:.1f}**.",
        f"\n\n_→ {q12}._\n",
        "## Q13 — persistência de liderança\n",
        f"- líder de hoje = líder de ontem em **{persist:.1%}** dos dias "
        f"(acaso = 12.5%).",
        f"\n\n_→ {q13}._\n",
        "## Síntese (amarra ao a24)\n",
        "Coerente com o veredito do a24: a moeda que vai liderar o range do dia "
        "não se destaca no CSS de manhã. O valor do CSS, se existe, é concorrente "
        "(a26b), não na antecipação do dia valioso.\n",
    ]
    (out / "REPORT.md").write_text("\n".join(rep), encoding="utf-8")
    print(f"a26: {out}/REPORT.md ({time.time()-t0:.1f}s)")
    print(f"dias com destaque: {frac_standout:.0%}  |  Q11 acerto CSS={hit_css:.1%} "
          f"(acaso 12.5%)  prev={hit_prev:.1%}")
    print(f"Q12 dispersao manha destaque={css_disp_standout:.1f} vs morto={css_disp_dead:.1f}")
    print(f"Q13 persistencia lideranca={persist:.1%} (acaso 12.5%)")


if __name__ == "__main__":
    main()
