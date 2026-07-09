# -*- coding: utf-8 -*-
"""a22_sessoes.py — mapa descritivo de movimento por sessão (Tokyo/Londres/NY/
overlap) × par × dia da semana. Puro fato de mercado; NENHUMA decisão de trade.

Q1 — distribuição de range por sessão×par×dia-da-semana; ranquear sessões
     (mediana + dispersão, pois range é assimétrico).
Q2 — qual par domina cada sessão (maior mediana de range em pips).
Q3 — segunda/sexta e viradas de mês têm assinatura diferente? Dias de notícia
     HIGH (calendário a18, 2024-07→) como covariável.

Baseline honesto (regra de ouro): o range é reportado em pips (comparação entre
pares) E normalizado pela mediana do próprio par (comparação entre sessões).

Metodologia: barras fechadas, sem lookahead (só descreve o passado); tempo
convertido servidor→UTC DST-aware (sessions.py). Robustez: correlação das
medianas par×sessão entre 1ª metade e 2ª metade da amostra.

Uso: python a22_sessoes.py
Saída: results/{ts}_a22/REPORT.md + session_pair_pips.csv + ranges_long.parquet
"""
from __future__ import annotations

import json
import pathlib
import time

import numpy as np
import pandas as pd

from sessions import SESSIONS, session_ranges, server_to_utc

RAW = pathlib.Path("data/raw")
CAL = pathlib.Path("data/calendar/calendar_mt5.csv")
SHADE = " ░▒▓█"


# ----------------------------------------------------------------------------
# Carga
# ----------------------------------------------------------------------------

def load_pips() -> dict[str, float]:
    meta = json.loads((RAW / "_meta_ta.json").read_text(encoding="utf-8"))
    return {s: v["pip"] for s, v in meta["symbols"].items()}


def load_all_ranges() -> pd.DataFrame:
    """Concatena session_ranges de todos os pares num DataFrame long."""
    pips = load_pips()
    rows = []
    for f in sorted(RAW.glob("M15_*.parquet")):
        sym = f.stem.removeprefix("M15_")
        df = pd.read_parquet(f)
        r = session_ranges(df, pips[sym])
        if r.empty:
            continue
        r["pair"] = sym
        rows.append(r)
    out = pd.concat(rows, ignore_index=True)
    out["date"] = pd.to_datetime(out["date"])
    out["weekday"] = out["date"].dt.dayofweek        # 0=seg .. 4=sex
    dom = out["date"].dt.day
    dim = out["date"].dt.days_in_month
    out["month_turn"] = (dom <= 2) | (dom >= dim - 1)  # ±2 da virada
    # INTENSIDADE: pips/hora, p/ comparar sessões de DURAÇÃO diferente
    # (overlap tem 3h; tokyo/londres/ny têm 9h — total confunde com duração).
    hours = {s: b - a for s, (a, b) in SESSIONS.items()}
    out["range_ph"] = out["range_pips"] / out["session"].map(hours)
    # normalizado pela mediana de intensidade do próprio par (todas as sessões)
    med_pair = out.groupby("pair")["range_ph"].transform("median")
    out["range_norm"] = out["range_ph"] / med_pair
    return out


# ----------------------------------------------------------------------------
# Notícias (Q3) — calendário HIGH, mapeado a dia-UTC
# ----------------------------------------------------------------------------

def high_news_days() -> tuple[set[tuple[pd.Timestamp, str]], pd.Timestamp | None]:
    if not CAL.exists():
        return set(), None
    c = pd.read_csv(CAL, encoding="latin-1")
    c = c[c["importance"] == "HIGH"].copy()
    ts = pd.to_datetime(c["time_server"], format="%Y.%m.%d %H:%M:%S")
    utc = server_to_utc(pd.DatetimeIndex(ts))
    c["date"] = pd.Series(utc, index=c.index).dt.normalize()
    days = set(zip(c["date"], c["currency"]))
    start = c["date"].min()
    return days, start


# ----------------------------------------------------------------------------
# Tabelas Q1/Q2/Q3
# ----------------------------------------------------------------------------

def q1_session_rank(df: pd.DataFrame) -> pd.DataFrame:
    """Ranking de sessões por range_norm (mediana + IQR = dispersão)."""
    g = df.groupby("session")
    tab = pd.DataFrame({
        "pips_h_mediana": g["range_ph"].median(),          # intensidade absoluta
        "intensidade_norm": g["range_norm"].median(),       # vs mediana do par
        "iqr_norm": g["range_norm"].quantile(0.75) - g["range_norm"].quantile(0.25),
        "p90_norm": g["range_norm"].quantile(0.90),
        "n": g["range_norm"].size(),
    }).reindex(SESSIONS.keys())
    return tab.sort_values("intensidade_norm", ascending=False)


def q2_pair_per_session(df: pd.DataFrame) -> pd.DataFrame:
    """Mediana de range_pips por par×sessão (pivot) + o par dominante."""
    piv = (df.groupby(["pair", "session"])["range_pips"].median()
             .unstack("session").reindex(columns=list(SESSIONS)))
    return piv


def session_pair_matrix(piv: pd.DataFrame) -> str:
    """Heatmap unicode da matriz par×sessão (sombreado por coluna)."""
    lines = ["| par | " + " | ".join(SESSIONS) + " |",
             "|---|" + "---|" * len(SESSIONS)]
    # normaliza por coluna p/ o sombreado
    norm = (piv - piv.min()) / (piv.max() - piv.min())
    for pair in piv.index:
        cells = []
        for s in SESSIONS:
            v = piv.loc[pair, s]
            q = norm.loc[pair, s]
            sh = SHADE[min(len(SHADE) - 1, int(q * len(SHADE)))] if pd.notna(q) else " "
            cells.append(f"{sh*3} {v:.0f}")
        lines.append(f"| {pair} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def q2b_affinity(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Afinidade RELATIVA de sessão: share de intensidade Tok/Ldn/NY (soma 1,
    exclui overlap) por par. Responde o folclore ('JPY-crosses no Tokyo') no
    sentido relativo — o absoluto (pips) é dominado pelos crosses de GBP."""
    piv = (df[df.session != "overlap"]
           .groupby(["pair", "session"])["range_ph"].median()
           .unstack("session")[["tokyo", "londres", "ny"]])
    share = piv.div(piv.sum(axis=1), axis=0)
    grupo = pd.Series(["JPY" if "JPY" in p else
                       ("Asia(AUD/NZD)" if ("AUD" in p or "NZD" in p) else "Eur/USD/CAD")
                       for p in share.index], index=share.index)
    gmean = share.groupby(grupo).mean()
    return gmean, share["tokyo"].sort_values(ascending=False)


def q3_weekday(df: pd.DataFrame) -> pd.DataFrame:
    wd = {0: "seg", 1: "ter", 2: "qua", 3: "qui", 4: "sex"}
    t = (df[df["weekday"] <= 4].groupby(["session", "weekday"])["range_norm"]
         .median().unstack("weekday").rename(columns=wd).reindex(SESSIONS.keys()))
    return t


def q3_news(df: pd.DataFrame) -> pd.DataFrame | None:
    days, start = high_news_days()
    if not days:
        return None
    sub = df[df["date"] >= start].copy()
    base = sub["pair"].str[:3]
    quote = sub["pair"].str[3:6]
    has = [((d, b) in days) or ((d, q) in days)
           for d, b, q in zip(sub["date"], base, quote)]
    sub["news"] = has
    t = (sub.groupby(["session", "news"])["range_norm"].median()
         .unstack("news").reindex(SESSIONS.keys()))
    t.columns = ["sem_news", "com_news"][: t.shape[1]]
    t["lift"] = t.get("com_news") / t.get("sem_news")
    return t


def stability(df: pd.DataFrame) -> float:
    """Correlação de Spearman das medianas par×sessão entre 1ª e 2ª metade."""
    cut = df["date"].quantile(0.5)
    a = df[df["date"] < cut].groupby(["pair", "session"])["range_pips"].median()
    b = df[df["date"] >= cut].groupby(["pair", "session"])["range_pips"].median()
    j = pd.concat({"a": a, "b": b}, axis=1).dropna()
    return float(j["a"].corr(j["b"], method="spearman"))


# ----------------------------------------------------------------------------
# Driver
# ----------------------------------------------------------------------------

def main() -> None:
    t0 = time.time()
    df = load_all_ranges()
    q1 = q1_session_rank(df)
    piv = q2_pair_per_session(df)
    heat = session_pair_matrix(piv)
    gmean, tok_share = q2b_affinity(df)
    wd = q3_weekday(df)
    news = q3_news(df)
    stab = stability(df)

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_a22")
    out.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out / "ranges_long.parquet")
    piv.to_csv(out / "session_pair_pips.csv")

    top_ny = piv["ny"].sort_values(ascending=False).head(5)
    top_tok = piv["tokyo"].sort_values(ascending=False).head(5)
    top_ldn = piv["londres"].sort_values(ascending=False).head(5)

    rep = [f"# a22 — Mapa de sessões (descritivo)\n",
           f"Amostra: {df['pair'].nunique()} pares, "
           f"{df['date'].min().date()} → {df['date'].max().date()}, "
           f"{len(df):,} linhas par×sessão×dia. Range em pips e normalizado "
           f"pela mediana do próprio par. Tempo servidor→UTC DST-aware.\n",
           "## Q1 — Ranking de sessões (INTENSIDADE = pips/hora)\n",
           "_Ranqueado por intensidade (pips/h), não range total: overlap tem "
           "3h vs 9h das outras — total confundiria com duração._\n",
           q1.round(3).to_markdown(),
           f"\n_Dispersão (IQR) reportada porque range é assimétrico. "
           f"Estabilidade 1ª×2ª metade (Spearman medianas par×sessão): "
           f"**{stab:.3f}**._\n",
           "## Q2 — Par dominante por sessão (mediana de pips)\n",
           "**Top-5 NY:** " + ", ".join(f"{p} ({v:.0f})" for p, v in top_ny.items()),
           "\n\n**Top-5 Londres:** " + ", ".join(f"{p} ({v:.0f})" for p, v in top_ldn.items()),
           "\n\n**Top-5 Tokyo:** " + ", ".join(f"{p} ({v:.0f})" for p, v in top_tok.items()),
           "\n\n### Heatmap par×sessão (mediana de pips, sombreado por coluna)\n",
           heat,
           "\n\n## Q2b — Afinidade relativa de sessão (folclore testado)\n",
           "_Share de intensidade Tok/Ldn/NY (soma 1, exclui overlap). Absoluto "
           "(pips) é dominado por GBP em toda sessão; o relativo revela a praça._\n",
           gmean.round(3).to_markdown(),
           f"\n\n_Mais Tokyo-heavy:_ " + ", ".join(
               f"{p} ({v:.2f})" for p, v in tok_share.head(4).items()) +
           "  ·  _menos Tokyo (Ldn/NY):_ " + ", ".join(
               f"{p} ({v:.2f})" for p, v in tok_share.tail(4).items()),
           "\n\n## Q3 — Dia da semana (range normalizado, mediana)\n",
           wd.round(3).to_markdown(),
           "\n\n### Notícias HIGH (covariável, período do calendário)\n",
           (news.round(3).to_markdown() if news is not None
            else "_calendário indisponível_"),
           "\n"]
    (out / "REPORT.md").write_text("\n".join(rep), encoding="utf-8")
    print(f"a22: {out}/REPORT.md  ({time.time()-t0:.1f}s)")
    print(q1.round(3).to_string())
    print("estabilidade par×sessão (Spearman):", round(stab, 3))


if __name__ == "__main__":
    main()
