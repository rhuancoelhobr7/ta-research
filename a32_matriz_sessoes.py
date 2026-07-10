# -*- coding: utf-8 -*-
"""a32_matriz_sessoes.py — matriz completa de autocorrelação de range entre
sessões (fecha o a23, que achou só Tóquio->Londres->NY).

Sequência cronológica de sessões: asia[00-07) -> londres[07-13) -> ny[13-21) ->
asia(dia+1) ... Matriz 3x3 "de sessão X para a PRÓXIMA ocorrência da sessão Y"
(inclui NY->Tóquio do dia seguinte, wrap-around). Spearman por par, out-of-
sample (split 70/30), agregado entre os 28 pares com IC bootstrap em blocos.

Q20 matriz completa (Spearman por célula).
Q21 transições são iguais ou específicas? Tóquio->Londres vs Londres->NY.
Q22 NY->Tóquio(dia+1) com % (fração de variância de rank compartilhada = rho^2).
Q23 decaimento com a distância entre sessões (monotônico ou com saltos?).

Uso: python a32_matriz_sessoes.py
Saída: results/{ts}_a32/REPORT.md + matriz_sessoes.csv
"""
from __future__ import annotations

import json
import pathlib
import time

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from sessions import SEQ_SESSIONS, session_ranges
from stats_blocks import block_bootstrap_ci

RAW = pathlib.Path("data/raw")
SESS = ["asia", "londres", "ny"]
TRAIN_FRAC = 0.70

# célula (from -> to): (coluna_x, coluna_y, dia_seguinte?, distancia em sessões)
CELLS = {
    ("asia", "londres"): ("asia", "londres", False, 1),
    ("asia", "ny"): ("asia", "ny", False, 2),
    ("asia", "asia"): ("asia", "asia", True, 3),
    ("londres", "ny"): ("londres", "ny", False, 1),
    ("londres", "asia"): ("londres", "asia", True, 2),
    ("londres", "londres"): ("londres", "londres", True, 3),
    ("ny", "asia"): ("ny", "asia", True, 1),
    ("ny", "londres"): ("ny", "londres", True, 2),
    ("ny", "ny"): ("ny", "ny", True, 3),
}


def load_pips() -> dict[str, float]:
    meta = json.loads((RAW / "_meta_ta.json").read_text(encoding="utf-8"))
    return {s: v["pip"] for s, v in meta["symbols"].items()}


def pair_wide(sym: str, pip: float) -> pd.DataFrame:
    df = pd.read_parquet(RAW / f"M15_{sym}.parquet")
    sr = session_ranges(df, pip, SEQ_SESSIONS)
    return sr.pivot_table(index="date", columns="session", values="range_pips")


def cell_spearman(w: pd.DataFrame, x: str, y: str, next_day: bool,
                  cut) -> float:
    yy = w[y].shift(-1) if next_day else w[y]
    d = pd.concat({"x": w[x], "y": yy}, axis=1, sort=False).dropna()
    d = d[d.index >= cut]                          # teste out-of-sample
    if len(d) < 100 or d["x"].nunique() < 5:
        return np.nan
    return spearmanr(d["x"], d["y"])[0]


def main() -> None:
    t0 = time.time()
    pips = load_pips()
    wides = {}
    for f in sorted(RAW.glob("M15_*.parquet")):
        sym = f.stem.removeprefix("M15_")
        wides[sym] = pair_wide(sym, pips[sym])

    # Spearman por par por célula (no teste), depois mediana + IC entre pares
    per_cell = {c: [] for c in CELLS}
    for sym, w in wides.items():
        cut = w.index.to_series().quantile(TRAIN_FRAC)
        for c, (x, y, nd, _) in CELLS.items():
            per_cell[c].append(cell_spearman(w, x, y, nd, cut))

    rows = []
    for c, (x, y, nd, dist) in CELLS.items():
        vals = np.array([v for v in per_cell[c] if not np.isnan(v)])
        med, lo, hi = block_bootstrap_ci(vals, np.median, block=5)
        rows.append({"de": c[0], "para": c[1], "dia+1": nd, "dist": dist,
                     "spearman": med, "ic_lo": lo, "ic_hi": hi,
                     "rho2_%": 100 * med * med, "n_pares": len(vals)})
    tab = pd.DataFrame(rows)

    # matriz 3x3 (linhas=de, colunas=para) de Spearman mediano
    mat = tab.pivot(index="de", columns="para", values="spearman").reindex(
        index=SESS, columns=SESS)

    ny_asia = tab[(tab.de == "ny") & (tab.para == "asia")].iloc[0]
    # Q23: decaimento por distância
    decay = tab.groupby("dist")["spearman"].median()

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_a32")
    out.mkdir(parents=True, exist_ok=True)
    tab.round(4).to_csv(out / "matriz_sessoes.csv", index=False)

    rep = [
        "# a32 — Matriz completa de autocorrelação de range entre sessões\n",
        f"{len(wides)} pares. Sequência asia->londres->ny->asia(dia+1). Célula "
        f"(de->para) = range da sessão `de` prevê a PRÓXIMA `para`. Spearman "
        f"mediano entre pares, out-of-sample (30% finais), IC bootstrap em blocos.\n",
        "## Q20/Q21 — Matriz 3x3 (Spearman mediano; linha=de, coluna=para)\n",
        mat.round(3).to_markdown(),
        "\n\n### Detalhe por célula (com distância, IC e rho^2)\n",
        tab.sort_values("dist").round(3).to_markdown(index=False),
        f"\n\n## Q22 — NY -> Tóquio (dia+1)\n",
        f"- Spearman **{ny_asia['spearman']:.3f}** IC95 "
        f"[{ny_asia['ic_lo']:.3f}, {ny_asia['ic_hi']:.3f}]; **{ny_asia['rho2_%']:.1f}%** "
        f"da variância de rank compartilhada. A volatilidade de NY VAZA para a "
        f"abertura asiática seguinte "
        f"{'(efeito real)' if ny_asia['ic_lo'] > 0 else '(IC cruza 0)'}.\n",
        "## Q23 — Decaimento por distância entre sessões\n",
        decay.round(3).to_frame("spearman_mediano").to_markdown(),
        "\n_dist 1 = adjacente; 3 = mesma sessão no dia seguinte. Monotônico "
        "= vol decai com o tempo; salto no 3 = sazonalidade de sessão._\n",
    ]
    (out / "REPORT.md").write_text("\n".join(rep), encoding="utf-8")
    print(f"a32: {out}/REPORT.md ({time.time()-t0:.1f}s)")
    print("matriz 3x3 (Spearman):\n", mat.round(3).to_string())
    print(f"Q22 NY->asia(d+1): {ny_asia['spearman']:.3f} ({ny_asia['rho2_%']:.1f}%)")
    print("Q23 decaimento por dist:\n", decay.round(3).to_string())


if __name__ == "__main__":
    main()
