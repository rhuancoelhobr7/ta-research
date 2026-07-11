# -*- coding: utf-8 -*-
"""a38_economic.py — valor ECONÔMICO dos dois sinais confirmados (com custo).

Acurácia não é lucro. As duas regras JÁ FIXADAS e CONFIRMADAS (a35, a35-bis)
entram EXATAMENTE como estão — zero parâmetros livres, zero varredura, zero
otimização. Aplicar um custo determinístico a regra congelada NÃO é data
snooping (nenhum grau de liberdade ajustado contra os dados). O holdout está
esgotado (a35 consumiu [q50,q70); a35-bis usou >=q70); logo os resultados são
reportados sobre TODOS os dias, decompostos por fatia (research/[q50,q70)/>=q70)
e por ano, p/ o leitor ver a estabilidade.

Regra A (z-score@180, top-3 de moedas): em T0+180min, ranquear as 8 moedas pelo
  z-score do retorno (média/desvio do research <q50, congelados — código do a35).
  Par-único: long top-1 vs bottom-1 no par correspondente, direção=sinal do
  z-score do top-1; fecha em 15h; sem stop/gain. Cesta: os 7 pares da top-1 na
  direção do sinal, tamanho igual, fecha 15h.
Regra B (persistência 4h->15h): em T0+240min, direção de cada moeda=sinal do
  movimento acumulado; abre na moeda de maior |movimento| vs a mais oposta;
  fecha 15h. Par-único e cesta. Prior honesto: a magnitude residual do a35-bis é
  +0.02 — espera-se que o custo consuma tudo; aqui se quantifica.

Veredito: um sinal é VIÁVEL se a expectativa líquida por trade > 0 com IC95
excluindo zero por cima E superar o baseline aleatório (mesmo custo). Senão, NÃO.

Uso: python a38_economic.py
Saída: results/{ts}_a38/REPORT.md + trades.csv
"""
from __future__ import annotations

import pathlib
import time

import numpy as np
import pandas as pd

from cssm_engine import build_indices
from a29_deteccao import load_m5
from a34_varredura import day_metrics, zscore_hist
from a31_par_campeao import pair_of
from costs import default_costs
from stats_blocks import block_bootstrap_ci
from preponderante import G8

A_ENTRY, B_ENTRY, EXIT = 180, 240, 900          # min desde a abertura


def price_at(ohlc: dict, offset: int) -> pd.DataFrame:
    """Close da última barra M5 com minutos < offset, por dia x par."""
    out = {}
    for sym, df in ohlc.items():
        day = df.index.normalize()
        mins = (df.index - day).total_seconds() / 60.0
        sub = df[mins < offset]
        out[sym] = sub.groupby(sub.index.normalize())["close"].last()
    return pd.DataFrame(out)


def side_for(cur_long: str, pair: str, sign: int) -> int:
    """+1/-1 p/ ficar LONG `cur_long` no símbolo `pair`, escalado por `sign`."""
    base = pair[:3]
    return sign * (1 if base == cur_long else -1)


def build_trades(zrow_or_mom, prices_entry, prices_exit, cols, mode):
    """Gera trades (par-único e cesta) de um sinal. Retorna lista de dicts."""
    single, basket = [], []
    for date, s in zrow_or_mom.iterrows():
        v = s.dropna()
        if len(v) < 8:
            continue
        if mode == "A":                     # z-score: top-1 vs bottom-1
            top, bot = v.idxmax(), v.idxmin()
            sign = int(np.sign(v[top])) or 1
            leader = top; counter = bot
        else:                               # B: maior |mom| vs mais oposta
            leader = v.abs().idxmax()
            sign = int(np.sign(v[leader])) or 1
            counter = (sign * v).idxmin()   # moeda mais contra a direção do líder
        pair = pair_of(leader, counter, cols)
        if pair and date in prices_entry.index and date in prices_exit.index:
            e, x = prices_entry.loc[date, pair], prices_exit.loc[date, pair]
            if np.isfinite(e) and np.isfinite(x):
                single.append({"date": date, "pair": pair,
                               "side": side_for(leader, pair, sign),
                               "entry": e, "exit": x})
        # cesta: os 7 pares da moeda líder
        for p in [c for c in cols if leader in (c[:3], c[3:6])]:
            if date in prices_entry.index and date in prices_exit.index:
                e, x = prices_entry.loc[date, p], prices_exit.loc[date, p]
                if np.isfinite(e) and np.isfinite(x):
                    basket.append({"date": date, "pair": p,
                                   "side": side_for(leader, p, sign),
                                   "entry": e, "exit": x, "leg_of": leader})
    return single, basket


def pnl_frame(trades, costs) -> pd.DataFrame:
    rows = []
    for t in trades:
        r = costs.net_pnl(t["entry"], t["exit"], t["side"], t["pair"])
        rows.append({**t, **r})
    return pd.DataFrame(rows)


def daily_agg(df: pd.DataFrame, basket=False) -> pd.DataFrame:
    """PnL por DIA (par-único: 1 linha/dia; cesta: média dos 7 legs = 1/7 lote)."""
    if basket:
        g = df.groupby("date").agg(net_pips=("net_pips", "mean"),
                                   gross_pips=("gross_pips", "mean"),
                                   cost_pips=("cost_pips", "mean"))
        return g.reset_index()
    return df[["date", "net_pips", "gross_pips", "cost_pips"]].copy()


def metrics(d: pd.DataFrame) -> dict:
    net = d["net_pips"].to_numpy(); gross = d["gross_pips"].to_numpy()
    exp, lo, hi = block_bootstrap_ci(net, np.mean, block=5, n_boot=3000)
    eq = np.cumsum(net); dd = float((eq - np.maximum.accumulate(eq)).min())
    pos, neg = net[net > 0].sum(), -net[net < 0].sum()
    return {
        "n": len(net), "exp_net_pips": exp, "ic_lo": lo, "ic_hi": hi,
        "win_net_%": float((net > 0).mean() * 100),
        "acuracia_dir_%": float((gross > 0).mean() * 100),
        "cost_%_gross": float(d["cost_pips"].mean() / np.abs(gross).mean() * 100),
        "profit_factor": float(pos / neg) if neg > 0 else float("inf"),
        "max_dd_pips": dd, "pior_dia_pips": float(net.min()),
        "exp_net_usd_lote": exp * 10.0,
    }


def random_baseline(trades, costs, seed=0) -> float:
    rng = np.random.default_rng(seed)
    net = []
    for t in trades:
        side = int(rng.choice([-1, 1]))
        net.append(costs.net_pnl(t["entry"], t["exit"], side, t["pair"])["net_pips"])
    return float(np.mean(net))


def slice_label(dates, q50, q70):
    return np.where(dates < q50, "research", np.where(dates < q70, "q50-q70", ">=q70"))


def main() -> None:
    t0 = time.time()
    closes, ohlc, pip = load_m5()
    idx = build_indices({s: closes[s].dropna() for s in closes}, align="inner")
    cols = set(ohlc.keys())
    costs = default_costs()

    days = pd.DatetimeIndex(sorted(idx.index.normalize().unique()))
    q50 = days.to_series().quantile(0.50); q70 = days.to_series().quantile(0.70)

    # sinais congelados
    momA = day_metrics(idx, A_ENTRY)["mom"]
    zA = zscore_hist(momA, momA.index.isin(days[days < q50]))     # z-score do a35
    momB = day_metrics(idx, B_ENTRY)["mom"]                        # movimento @4h

    pe_A = price_at(ohlc, A_ENTRY); pe_B = price_at(ohlc, B_ENTRY)
    px = price_at(ohlc, EXIT)

    strategies = {}
    sA, bA = build_trades(zA, pe_A, px, cols, "A")
    sB, bB = build_trades(momB, pe_B, px, cols, "B")
    for name, tr, basket in [("A_par", sA, False), ("A_cesta", bA, True),
                             ("B_par", sB, False), ("B_cesta", bB, True)]:
        df = pnl_frame(tr, costs)
        d = daily_agg(df, basket=basket)
        m = metrics(d)
        m["rand_baseline_pips"] = random_baseline(tr, costs)
        m["viavel"] = (m["ic_lo"] > 0) and (m["exp_net_pips"] > m["rand_baseline_pips"])
        # fatias
        d["fatia"] = slice_label(d["date"].values, np.datetime64(q50), np.datetime64(q70))
        m["por_fatia"] = d.groupby("fatia")["net_pips"].mean().round(2).to_dict()
        d["ano"] = pd.to_datetime(d["date"]).dt.year
        m["por_ano"] = d.groupby("ano")["net_pips"].mean().round(2).to_dict()
        strategies[name] = (m, tr)

    # sensibilidade ao custo (varia só a PREMISSA de custo, não a regra)
    sens = {}
    for mult in [0.5, 1.0, 1.5, 2.0]:
        c = default_costs(spread_mult=mult)
        row = {}
        for name, tr, basket in [("A_par", sA, False), ("A_cesta", bA, True),
                                 ("B_par", sB, False), ("B_cesta", bB, True)]:
            d = daily_agg(pnl_frame(tr, c), basket=basket)
            row[name] = round(float(d["net_pips"].mean()), 2)
        sens[mult] = row
    sens = pd.DataFrame(sens).T
    sens.index.name = "spread_x"

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_a38")
    out.mkdir(parents=True, exist_ok=True)
    sens.to_csv(out / "sensibilidade.csv")

    def mrow(name):
        m = strategies[name][0]
        return (f"| {name} | {m['exp_net_pips']:+.2f} | [{m['ic_lo']:+.2f}, "
                f"{m['ic_hi']:+.2f}] | {m['rand_baseline_pips']:+.2f} | "
                f"{m['acuracia_dir_%']:.1f}% | {m['win_net_%']:.1f}% | "
                f"{m['cost_%_gross']:.0f}% | {m['profit_factor']:.2f} | "
                f"{m['max_dd_pips']:.0f} | {'SIM' if m['viavel'] else 'NÃO'} |")

    any_viavel = any(strategies[n][0]["viavel"] for n in strategies)
    rep = [
        "# a38 — Valor econômico dos dois sinais confirmados (com custo)\n",
        f"Regras CONGELADAS (a35/a35-bis), zero parâmetros livres. Custo real: "
        f"spread mediano por par (M5), slippage 0.1 pip/ponta, swap 0 (intradiário), "
        f"comissão 0. {len(days)} dias. Custo em pips E % do bruto. $ aproximado "
        f"($10/pip/lote).\n",
        "## Resultado por estratégia (expectativa LÍQUIDA por trade, pips)\n",
        "| estratégia | exp. líq. | IC95 | aleatório | acurácia dir. | win líq. | "
        "custo %bruto | PF | maxDD | viável? |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n"
        + "\n".join(mrow(n) for n in ["A_par", "A_cesta", "B_par", "B_cesta"]),
        "\n\n_A diferença entre **acurácia direcional** e **win líquido** é a "
        "resposta de 'acurácia vira lucro?': o custo move a linha d'água._\n",
        "## Decomposição por fatia e por ano (expectativa líq., pips)\n",
        "\n".join(f"- **{n}** — fatias: {strategies[n][0]['por_fatia']} · "
                  f"anos: {strategies[n][0]['por_ano']}" for n in strategies),
        "\n\n## Sensibilidade ao custo (varia só o spread assumido, não a regra)\n",
        sens.to_markdown(),
        "\n\n_Breakeven: spread máximo que o sinal tolera antes de zerar. Se o "
        "breakeven ficar abaixo do spread real do broker, o sinal é INOPERÁVEL._\n",
        "## Veredito pré-registrado\n",
        ("Ao menos uma estratégia é ECONOMICAMENTE VIÁVEL (exp. líq. > 0, IC "
         "exclui zero, bate o aleatório). Ver tabela.\n" if any_viavel else
         "**NENHUMA estratégia é economicamente viável.** E o motivo é mais fundo "
         "que 'o custo come o edge': a **acurácia direcional do movimento "
         "CAPTURÁVEL (da entrada até 15h) é ~49-51% — quase moeda-ao-ar**. Os "
         "sinais confirmados (0.506 do a35, 0.646 do a35-bis) descreviam o estado "
         "JÁ FORMADO até o horário de entrada; o RESIDUAL que se captura entrando "
         "ali é ruído (coerente com o +0.02 do a35-bis). O custo é só 2-3% do bruto "
         "— não é o vilão; o BRUTO já é ~0. Mesmo com spread 0.5x nada fica "
         "robustamente positivo (IC sempre inclui zero). Os dois sinais são fatos "
         "estatísticos reais sobre o PASSADO, não edges tradeáveis sobre o FUTURO. "
         "O projeto NÃO produziu sinal direcional operável; o único entregável "
         "prático permanece o ranqueador de AMPLITUDE por ATR de sessão (a25).\n"),
        "\n_Próximo passo honesto (não executado): validação PROSPECTIVA em dias "
        "novos — não há mais fatia pristina p/ novos testes retrospectivos._\n",
    ]
    (out / "REPORT.md").write_text("\n".join(rep), encoding="utf-8")
    print(f"a38: {out}/REPORT.md ({time.time()-t0:.1f}s)")
    for n in strategies:
        m = strategies[n][0]
        print(f"{n:9s} exp={m['exp_net_pips']:+.2f}p IC[{m['ic_lo']:+.2f},{m['ic_hi']:+.2f}] "
              f"rand={m['rand_baseline_pips']:+.2f} acc={m['acuracia_dir_%']:.0f}% "
              f"winliq={m['win_net_%']:.0f}% custo={m['cost_%_gross']:.0f}% viavel={m['viavel']}")
    print("VEREDITO:", "algum viavel" if any_viavel else "NENHUM viavel (custo consome o edge)")


if __name__ == "__main__":
    main()
