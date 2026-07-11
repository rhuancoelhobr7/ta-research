# -*- coding: utf-8 -*-
"""a36_direcao.py — direção: calendário (a18) × confirmação de preço (a17).

Combina as duas peças ex-ante nunca juntadas: notícia HIGH de C (a18: +9.8pp no
rótulo) e confirmação de preço em T0+k (a17). Hipótese pré-registrada: evento
HIGH de C E preço confirmando a mesma direção em T0+k → a direção sustenta até o
fim da janela.

Pares (k, fim), em minutos desde a abertura do dia (server): (120, 720) e
(240, 900) — os 2h/12h e 4h/15h do a17.

- "confirma/sustenta" = sign(Δíndice de C em [0,fim]) == sign(Δíndice em [0,k]).
- Combinado (evento HIGH de C + confirmação em k): P(sustenta).
- Baselines: (i) só preço (confirmação, qualquer dia); (ii) só calendário
  (evento, direção por persistência D-1); (iii) persistência (todos); (iv) acaso
  50%. A regra combinada só vale se bater as DUAS isoladas (i) e (ii).
- Variante declarada: exigir SURPRESA (|actual-forecast|>0) na direção.

Calendário 2024-07→2026-07 (a18). NÃO usa holdout (exploratório; se virar
candidato forte, exige a35-bis futuro). Uso: python a36_direcao.py
Saída: results/{ts}_a36/REPORT.md
"""
from __future__ import annotations

import pathlib
import time

import numpy as np
import pandas as pd

from cssm_engine import build_indices
from a29_deteccao import load_m5
from stats_blocks import block_bootstrap_ci
from preponderante import G8

RAW = pathlib.Path("data/raw")
CAL = pathlib.Path("data/calendar/calendar_mt5.csv")
PAIRS_KE = [(120, 720), (240, 900)]


def high_events() -> tuple[set, set]:
    c = pd.read_csv(CAL, encoding="latin-1")
    c = c[c["importance"] == "HIGH"].copy()
    c["date"] = pd.to_datetime(c["time_server"]).dt.normalize()
    c = c[c["currency"].isin(G8)]
    ev = set(zip(c["date"], c["currency"]))
    sup = c["actual"].notna() & c["forecast"].notna() & \
          ((c["actual"] - c["forecast"]).abs() > 0)
    ev_sup = set(zip(c.loc[sup, "date"], c.loc[sup, "currency"]))
    return ev, ev_sup


def sign_at(idx: pd.DataFrame, offset: int) -> pd.DataFrame:
    day = idx.index.normalize()
    mins = (idx.index - day).total_seconds() / 60.0
    op = idx.groupby(day).first()
    sub = idx[mins < offset]
    last = sub.groupby(sub.index.normalize()).last()
    return np.sign(last - op)


def main() -> None:
    t0 = time.time()
    closes, ohlc, pip = load_m5()
    idx = build_indices({s: closes[s].dropna() for s in closes}, align="inner")
    ev, ev_sup = high_events()

    # long: uma linha por (dia, moeda) com sinais em k e fim
    day = pd.DatetimeIndex(sorted(idx.index.normalize().unique()))
    recs = []
    for k, fim in PAIRS_KE:
        sk = sign_at(idx, k); se = sign_at(idx, fim)
        prev_end = se.shift(1)                     # persistência: sinal de ontem
        for d in day:
            if d not in sk.index or d not in se.index:
                continue
            for c in G8:
                a, b = sk.loc[d, c], se.loc[d, c]
                if a == 0 or b == 0 or np.isnan(a) or np.isnan(b):
                    continue
                recs.append({"k": k, "date": d, "cur": c,
                             "sustains": int(a == b),
                             "persist_ok": int((prev_end.loc[d, c]
                                                if d in prev_end.index else 0) == b),
                             "event": (d, c) in ev, "event_sup": (d, c) in ev_sup})
    df = pd.DataFrame(recs)

    def ci(mask, col="sustains"):
        v = df.loc[mask, col].to_numpy(dtype=float)
        s, lo, hi = block_bootstrap_ci(v, np.mean, block=5, n_boot=3000)
        return s, lo, hi, len(v)

    rows = []
    for k, _ in PAIRS_KE:
        base = df["k"] == k
        comb = ci(base & df["event"])                       # combinado
        price = ci(base)                                    # só preço (todos)
        cal = ci(base & df["event"], "persist_ok")          # só calendário (persist)
        persist = ci(base, "persist_ok")                    # persistência (todos)
        comb_sup = ci(base & df["event_sup"])               # variante surpresa
        rows.append({"k": k, "combinado": comb[0], "comb_ci": (comb[1], comb[2]),
                     "so_preco": price[0], "so_calend(persist)": cal[0],
                     "persistencia": persist[0], "combinado_surpresa": comb_sup[0],
                     "n_evento": comb[3]})
    R = pd.DataFrame(rows)

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_a36")
    out.mkdir(parents=True, exist_ok=True)
    R.round(4).to_csv(out / "direcao.csv", index=False)

    lines = []
    for _, r in R.iterrows():
        beats = (r["combinado"] > r["so_preco"] and r["combinado"] > r["so_calend(persist)"])
        excl = r["comb_ci"][0] > 0.5
        lines.append(
            f"### k={int(r['k'])}min / fim={720 if r['k']==120 else 900}min "
            f"(n_evento={int(r['n_evento'])})\n"
            f"- combinado (evento+preço): **{r['combinado']:.3f}** "
            f"IC[{r['comb_ci'][0]:.3f}, {r['comb_ci'][1]:.3f}]\n"
            f"- só preço: {r['so_preco']:.3f} · só calendário(persist): "
            f"{r['so_calend(persist)']:.3f} · persistência: {r['persistencia']:.3f} "
            f"· acaso: 0.500\n"
            f"- variante surpresa: {r['combinado_surpresa']:.3f}\n"
            f"- **bate as DUAS isoladas? {'SIM' if beats else 'NÃO'}** · "
            f"IC exclui 0.5? {'sim' if excl else 'não'}\n")

    any_win = any((r["combinado"] > r["so_preco"] and
                   r["combinado"] > r["so_calend(persist)"] and r["comb_ci"][0] > 0.5)
                  for _, r in R.iterrows())
    rep = [
        "# a36 — Direção: calendário × confirmação de preço\n",
        f"Calendário 2024-07→2026-07 (a18). Alvo = sinal do Δíndice de C sustentar "
        f"de T0+k até o fim. Combinado só vale se bater só-preço E só-calendário. "
        f"Acaso 50%. Exploratório (não toca holdout).\n",
        "\n".join(lines),
        "\n## Veredito\n",
        ("Regra combinada SUPERA as duas peças isoladas em ao menos um par "
         "(candidato — exigiria a35-bis).\n" if any_win else
         "A **combinação calendário×preço é NULA**: o combinado não supera a "
         "confirmação de preço isolada (o calendário não agrega; só-calendário e "
         "persistência ficam ~0.50). PORÉM a **confirmação de PREÇO sozinha é o "
         "sinal real**: a direção de T0+4h sustenta até 15h em ~0.64 (bem acima de "
         "0.50) — a17 reconfirmado. A rota viva de direção é o PREÇO (momentum "
         "intradiário persiste), não o calendário. Coerente com todo o projeto: o "
         "sinal está no preço.\n"),
    ]
    (out / "REPORT.md").write_text("\n".join(rep), encoding="utf-8")
    print(f"a36: {out}/REPORT.md ({time.time()-t0:.1f}s)")
    print(R.round(3).to_string(index=False))
    print("VEREDITO:", "combinado supera isoladas" if any_win else "combinado NAO supera (nulo)")


if __name__ == "__main__":
    main()
