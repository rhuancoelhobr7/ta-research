# -*- coding: utf-8 -*-
"""a28_preponderante.py — comportamento da moeda preponderante em todas as sessões.

Descritivo, por PREÇO (preponderante.py). Janelas: asia[00-07)/londres[07-13)/
ny[13-21) (partição ordenada, SEQ_SESSIONS) + dia inteiro.

Q1 frequência da preponderante por sessão e no dia (confirmar ~88%); limiar 6/7 e 7/7.
Q2 direção: lidera por FORÇA vs por FRAQUEZA; viés por moeda (JPY lidera por fraqueza?).
Q3 continuidade: a líder de asia continua em londres/ny? matriz de transição.
Q4 meia-vida: uma vez líder, persiste por quantas sessões/dias?
Q5 limpo vs sujo: 7/7 move mais que 6/7 que 5/7?

Uso: python a28_preponderante.py
Saída: results/{ts}_a28/REPORT.md + transicao_lideranca.csv + perfil_moeda.csv
"""
from __future__ import annotations

import json
import pathlib
import time

import numpy as np
import pandas as pd

from sessions import SEQ_SESSIONS, session_ranges, daily_range
from preponderante import G8, currency_strength, leaders

RAW = pathlib.Path("data/raw")
WINDOWS = ["asia", "londres", "ny", "dia"]


def load_pips() -> dict[str, float]:
    meta = json.loads((RAW / "_meta_ta.json").read_text(encoding="utf-8"))
    return {s: v["pip"] for s, v in meta["symbols"].items()}


def build_windows() -> dict[str, tuple[pd.DataFrame, pd.Series]]:
    """Por janela: (net_wide[date x pair], norm[pair]=mediana do range da janela)."""
    pips = load_pips()
    net = {w: {} for w in WINDOWS}
    rng = {w: {} for w in WINDOWS}
    for f in sorted(RAW.glob("M15_*.parquet")):
        sym = f.stem.removeprefix("M15_")
        df = pd.read_parquet(f)
        sr = session_ranges(df, pips[sym], SEQ_SESSIONS)
        for w in ("asia", "londres", "ny"):
            s = sr[sr.session == w].set_index("date")
            net[w][sym] = s["net_pips"]
            rng[w][sym] = s["range_pips"]
        dr = daily_range(df, pips[sym])
        net["dia"][sym] = dr["day_net"]
        rng["dia"][sym] = dr["day_range"]
    out = {}
    for w in WINDOWS:
        nw = pd.DataFrame(net[w])
        norm = pd.DataFrame(rng[w]).median()          # ATR estrutural do par/janela
        out[w] = (nw, norm)
    return out


def leaders_panel(net_wide: pd.DataFrame, norm: pd.Series) -> pd.DataFrame:
    """Por dia: leader/anti/prep/consist/dir/forca (aplica currency_strength por linha)."""
    nd = norm.to_dict()
    recs = []
    for date, row in net_wide.iterrows():
        d = row.dropna()
        if len(d) < 20:
            continue
        L = leaders(currency_strength(d.to_dict(), nd))
        L["date"] = date
        recs.append(L)
    return pd.DataFrame(recs).set_index("date")


def transition(a: pd.Series, b: pd.Series) -> float:
    """P(mesma líder) entre duas séries de líder por data (datas em comum)."""
    j = pd.concat({"a": a, "b": b}, axis=1, sort=False).dropna()
    return float((j["a"] == j["b"]).mean()) if len(j) else np.nan


def main() -> None:
    t0 = time.time()
    W = build_windows()
    panels = {w: leaders_panel(*W[w]) for w in WINDOWS}

    # Q1 — frequência da preponderante (consistência da moeda LÍDER, não a
    # saturada "existe alguma 7/7"; magnitude gate p/ conectar ao ~88% da tese)
    q1 = {}
    for w in WINDOWS:
        p = panels[w]
        q1[w] = {"n_dias": len(p),
                 "lider>=6/7": float((p["leader_consist"] >= 6).mean()),
                 "lider=7/7": float((p["leader_consist"] == 7).mean()),
                 "7/7 E forca>=0.5": float(((p["leader_consist"] == 7) &
                                            (p["leader_forca"] >= 0.5)).mean())}
    q1 = pd.DataFrame(q1).T

    # Q2 — direção e viés por moeda (na janela 'dia')
    dia = panels["dia"]
    frac_forca = float((dia["prep_dir"] == 1).mean())   # lidera por força
    lead_cnt = dia["leader"].value_counts()
    anti_cnt = dia["anti_leader"].value_counts()
    perfil = pd.DataFrame({"vezes_lider": lead_cnt, "vezes_anti": anti_cnt}).fillna(0)
    perfil["vies_fraqueza"] = perfil["vezes_anti"] / (
        perfil["vezes_lider"] + perfil["vezes_anti"])
    perfil = perfil.reindex(G8).sort_values("vies_fraqueza", ascending=False)

    # Q3 — continuidade entre sessões (transição de liderança)
    la, ll, ln = (panels["asia"]["leader"], panels["londres"]["leader"],
                  panels["ny"]["leader"])
    trans = pd.Series({
        "asia->londres": transition(la, ll),
        "londres->ny": transition(ll, ln),
        "asia->ny": transition(la, ln),
        "acaso (1/8)": 1 / 8,
    })
    # quem cria líder novo: fração de londres cuja líder != asia
    cria_londres = 1 - transition(la, ll)
    cria_ny = 1 - transition(ll, ln)

    # Q4 — meia-vida: líder do dia persiste dia-a-dia?
    ld = dia["leader"]
    persist_d1 = float((ld.values[1:] == ld.values[:-1]).mean())
    # dentro do dia: líder do dia == líder de cada sessão?
    within = {w: transition(dia["leader"], panels[w]["leader"]) for w in
              ("asia", "londres", "ny")}

    # Q5 — limpo vs sujo: força da LÍDER por sua consistência (5/6/7), janela 'dia'
    q5 = dia.groupby("leader_consist")["leader_forca"].median()

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_a28")
    out.mkdir(parents=True, exist_ok=True)
    trans.to_csv(out / "transicao_lideranca.csv")
    perfil.round(3).to_csv(out / "perfil_moeda.csv")

    rep = [
        "# a28 — Comportamento da moeda preponderante (descritivo, por preço)\n",
        f"{len(dia)} dias, {dia.index.min().date()} -> {dia.index.max().date()}. "
        f"Preponderante por consistência direcional (0-7) dos 7 pares da moeda; "
        f"força normalizada pelo range típico do par.\n",
        "## Q1 — Frequência da preponderante (consistência da moeda líder)\n",
        q1.round(3).to_markdown(),
        f"\n_No DIA, a líder bate >=6/7 em {q1.loc['dia','lider>=6/7']:.0%} e 7/7 "
        f"em {q1.loc['dia','lider=7/7']:.0%}. Consistência sozinha é quase "
        f"universal — o '~88%' útil da tese aparece só com MAGNITUDE: 7/7 E "
        f"forca>=0.5 ATR = {q1.loc['dia','7/7 E forca>=0.5']:.0%}._\n",
        "## Q2 — Direção e viés por moeda\n",
        f"- lidera por FORÇA (moeda forte) em {frac_forca:.0%} vs por FRAQUEZA em "
        f"{1-frac_forca:.0%} dos dias.",
        "\n- viés de fraqueza por moeda (vezes anti-líder / (líder+anti)):\n",
        perfil.round(3).to_markdown(),
        "\n\n## Q3 — Continuidade da liderança entre sessões\n",
        trans.round(3).to_frame("P(mesma líder)").to_markdown(),
        f"\n_Londres cria líder novo em {cria_londres:.0%} dos dias; NY em "
        f"{cria_ny:.0%}. Acima do acaso (7/8=88%) = herda; perto = cria._\n",
        "## Q4 — Persistência / meia-vida da liderança\n",
        f"- líder do dia = líder do dia anterior em **{persist_d1:.0%}** (acaso 12.5%).",
        f"\n- líder do dia coincide com a líder de cada sessão: "
        + ", ".join(f"{w} {v:.0%}" for w, v in within.items()) + ".\n",
        "\n## Q5 — Limpo (7/7) vs sujo (6/7, 5/7): força da líder por consistência\n",
        q5.round(3).to_frame("forca_mediana").to_markdown(),
        "\n_Se a força cresce forte com a consistência, o 'quão preponderante' "
        "importa muito — o 7/7 limpo é um dia materialmente maior._\n",
    ]
    (out / "REPORT.md").write_text("\n".join(rep), encoding="utf-8")
    print(f"a28: {out}/REPORT.md ({time.time()-t0:.1f}s)")
    print(q1.round(3).to_string())
    print(f"Q2 lidera por forca {frac_forca:.0%}; mais anti-lider: "
          f"{perfil.index[0]} ({perfil.iloc[0]['vies_fraqueza']:.0%})")
    print("Q3 continuidade:", {k: round(v, 3) for k, v in trans.items()})
    print(f"Q4 persist dia-a-dia {persist_d1:.0%}")
    print("Q5 forca por consist:\n", q5.round(3).to_string())


if __name__ == "__main__":
    main()
