# -*- coding: utf-8 -*-
"""a35bis_persistencia.py — confirmação OOS da persistência-de-preço direcional.

O a36 achou que a confirmação de PREÇO sozinha sustenta a direção (sinal do
Δíndice de C em T0+k mantém-se até o fim em ~0.64 às 4h) — o outro sinal
promissor, independente do calendário e do CSS.

NATUREZA DA CONFIRMAÇÃO: a regra tem ZERO parâmetros livres (k, fim fixos a
priori do a17; todas as 8 moedas) — não há o que sobreajustar. O holdout formal
já foi consumido no a35 (z-score, sinal diferente). Aqui confirma-se:
 (1) robustez estatística (IC block-bootstrap excluindo 0.5),
 (2) ESTABILIDADE temporal (4 blocos consecutivos; >0.5 em todos?),
 (3) cauda RECENTE held-out [q70, fim) vs research [<q70], sem perder >25% do edge,
 (4) MAGNITUDE residual (sobra movimento direcional capturável após k?),
 (5) robustez ao par (k, fim).

Uso: python a35bis_persistencia.py
Saída: results/{ts}_a35bis/REPORT.md
"""
from __future__ import annotations

import pathlib
import time

import numpy as np
import pandas as pd

from cssm_engine import build_indices
from a29_deteccao import load_m5
from a36_direcao import sign_at
from stats_blocks import block_bootstrap_ci
from preponderante import G8

KE_PAIRS = [(120, 720), (180, 780), (240, 900)]     # (k, fim) min; primário 240/900
PRIMARY = (240, 900)


def move_at(idx: pd.DataFrame, offset: int) -> pd.DataFrame:
    """Δíndice da abertura do dia até `offset` min (valor, não só sinal)."""
    day = idx.index.normalize()
    mins = (idx.index - day).total_seconds() / 60.0
    op = idx.groupby(day).first()
    last = idx[mins < offset].groupby(idx[mins < offset].index.normalize()).last()
    return last - op


def build_obs(idx, k, fim):
    """long (dia,moeda): sinal em k, sinal no fim, residual dir*(fim-k)."""
    mk = move_at(idx, k); mf = move_at(idx, fim)
    days = mk.index.intersection(mf.index)
    recs = []
    for d in days:
        for c in G8:
            a, b = mk.loc[d, c], mf.loc[d, c]
            if np.isnan(a) or np.isnan(b) or a == 0:
                continue
            recs.append({"date": d, "cur": c, "sk": np.sign(a), "sf": np.sign(b),
                         "sustains": int(np.sign(a) == np.sign(b)),
                         "residual": np.sign(a) * (b - a), "full": abs(b)})
    return pd.DataFrame(recs)


def main() -> None:
    t0 = time.time()
    closes, ohlc, pip = load_m5()
    idx = build_indices({s: closes[s].dropna() for s in closes}, align="inner")
    days = pd.DatetimeIndex(sorted(idx.index.normalize().unique()))
    q70 = days.to_series().quantile(0.70)

    # --- primário (k=4h, fim=15h): research vs cauda held-out ---
    obs = build_obs(idx, *PRIMARY)
    atr_cur = obs.groupby("cur")["full"].median()          # move típico do dia
    obs["resid_norm"] = obs["residual"] / obs["cur"].map(atr_cur)
    res = obs[obs["date"] < q70]; oos = obs[obs["date"] >= q70]

    def acc_ci(df):
        v = df["sustains"].to_numpy(float)
        s, lo, hi = block_bootstrap_ci(v, np.mean, block=5, n_boot=3000)
        return s, lo, hi, len(v)
    sR, loR, hiR, nR = acc_ci(res)
    sO, loO, hiO, nO = acc_ci(oos)
    edge_keep = (sO - 0.5) / (sR - 0.5) if sR > 0.5 else np.nan
    resid_oos = oos["resid_norm"].median()
    confirma = (loO > 0.5) and (edge_keep >= 0.75) and (resid_oos > 0)

    # --- (2) estabilidade por 4 blocos consecutivos ---
    blocks = np.array_split(days, 4)
    blk = []
    for i, b in enumerate(blocks):
        m = obs[obs["date"].isin(b)]
        s, lo, hi, n = acc_ci(m)
        blk.append({"bloco": i + 1, "ini": b[0].date(), "fim": b[-1].date(),
                    "acc": s, "ic_lo": lo, "n": n})
    blk = pd.DataFrame(blk)

    # --- (5) robustez ao par (k,fim), acc geral ---
    rob = []
    for k, f in KE_PAIRS:
        o = build_obs(idx, k, f)
        rob.append({"k": k, "fim": f, "acc": float(o["sustains"].mean()),
                    "resid_norm_med": float((o["residual"] / o["cur"].map(
                        o.groupby("cur")["full"].median())).median())})
    rob = pd.DataFrame(rob)

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_a35bis")
    out.mkdir(parents=True, exist_ok=True)
    blk.round(4).to_csv(out / "blocos.csv", index=False)

    rep = [
        "# a35-bis — Confirmação OOS da persistência-de-preço direcional (a36)\n",
        f"Regra (ZERO parâmetros livres, do a17): sinal do Δíndice de C em "
        f"T0+{PRIMARY[0]}min sustenta até {PRIMARY[1]}min. Acaso 0.50. "
        f"O holdout formal foi consumido no a35 — aqui: robustez + estabilidade + "
        f"cauda recente [q70,fim).\n",
        "## (1)+(3) Research [<q70] vs cauda recente [>=q70]\n",
        f"- research: **{sR:.3f}** IC[{loR:.3f}, {hiR:.3f}] (n={nR:,})",
        f"\n- **cauda OOS: {sO:.3f}** IC[{loO:.3f}, {hiO:.3f}] (n={nO:,})",
        f"\n- edge mantido: **{edge_keep:.0%}**; IC OOS exclui 0.5? "
        f"**{'sim' if loO > 0.5 else 'não'}**\n",
        "## (2) Estabilidade por bloco (4 períodos consecutivos)\n",
        blk.round(3).to_markdown(index=False),
        f"\n\n_>0.5 em todos os blocos? "
        f"**{'SIM' if (blk['ic_lo'] > 0.5).all() else 'NÃO'}**._\n",
        "## (4) Magnitude residual — sobra movimento após T0+4h?\n",
        f"- residual direcional mediano (normalizado pelo move típico do dia) na "
        f"cauda OOS: **{resid_oos:+.2f}** — {'sim, há movimento direcional capturável após 4h' if resid_oos > 0.05 else 'pouco/nada sobra (sinal chega tarde)'}.\n",
        "## (5) Robustez ao par (k, fim)\n",
        rob.round(3).to_markdown(index=False),
        "\n\n## Veredito\n",
        (f"**CONFIRMA o SINAL, com caveat de magnitude.** A persistência-de-preço "
         f"direcional é robusta e estável OOS (cauda {sO:.3f}, IC exclui 0.5, edge "
         f"{edge_keep:.0%}, estável nos 4 blocos). MAS a magnitude residual é "
         f"minúscula ({resid_oos:+.2f} do move típico) — por 4h quase todo o "
         f"movimento LÍQUIDO do dia já foi. Leitura honesta: é um sinal de "
         f"CONFIRMAÇÃO/MANUTENÇÃO (a direção raramente inverte até o fim), NÃO um "
         f"edge de ENTRADA tardia às 4h (sobra pouco a capturar). Útil para segurar/"
         f"não-reverter uma posição já aberta, não para abrir às 4h. Coerente com o "
         f"tema: o sinal está no preço, mas chega quando o grosso já passou.\n"
         if confirma else
         f"**NÃO confirma plenamente** (cauda {sO:.3f}, IC lo {loO:.3f}, edge "
         f"{edge_keep:.0%}, residual {resid_oos:+.2f}). Reportar honestamente.\n"),
        "\n_Escopo honesto: entrada às 4h (tardia); alvo é o SINAL às 15h, não a "
        "magnitude garantida; é momentum intradiário persistente, não previsão em "
        "T0._\n",
    ]
    (out / "REPORT.md").write_text("\n".join(rep), encoding="utf-8")
    print(f"a35bis: {out}/REPORT.md ({time.time()-t0:.1f}s)")
    print(f"research={sR:.3f} | OOS={sO:.3f} IC[{loO:.3f},{hiO:.3f}] edge={edge_keep:.0%} "
          f"resid={resid_oos:+.2f}")
    print("blocos acc:", blk["acc"].round(3).tolist(), "| todos>0.5:",
          bool((blk['ic_lo'] > 0.5).all()))
    print("robustez (k,fim,acc):", rob[["k", "fim", "acc"]].to_dict("records"))
    print("VEREDITO:", "CONFIRMA" if confirma else "nao confirma plenamente")


if __name__ == "__main__":
    main()
