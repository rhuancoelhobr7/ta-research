# -*- coding: utf-8 -*-
"""a18_calendar.py — Calendário econômico × rótulos v1 (pré-registrado).

Pré-registro na íntegra no CHANGELOG (2026-07-07), commitado ANTES de
existir qualquer CSV de calendário no repo. Hipóteses:

  H-A18-1 (notícia CRIA rótulo): P(rótulo_C | >=1 evento HIGH de C na
    janela [T0,T0+12h] do dia) > P(rótulo_C | sem evento HIGH de C).
    Diferença de proporções, IC95% bootstrap em blocos por dia; NULO se
    o IC contém 0.
  H-A18-2 (conflito IMPEDE rótulo): dias sem nenhum rótulo são
    enriquecidos em "conflito" (HIGH de >=2 moedas distintas na janela)
    vs dias rotulados. Mesmo teste.
  H-A18-3 (agenda prevê em T0 — única leitura EX-ANTE): prever como
    protagonista a moeda com evento HIGH agendado na janela (se várias,
    a de mais eventos HIGH; empate = abstém); direção = persistência D-1
    do protagonista quando disponível, senão abstém. Métricas: top-1 nos
    dias em que opina + taxa de abstenção. Baselines: persistência D-1 e
    reality check por permutação. Sucesso = bater ambos.
    PROIBIDO (travado em teste): actual/forecast/previous em H-A18-3 —
    só a AGENDA é conhecida ex-ante.

Descritivo adicional (se houver resultado do a17): histograma de
(t_lock − horário do evento HIGH mais próximo da moeda no dia).

Fluxo de dados: o dono roda s1_export_calendar.mq5 no MT5, copia
MQL5\\Files\\calendar_mt5.csv para data/calendar/, e roda
`python a18_calendar.py --ingest` — que valida FUSO (âncora: CPI dos EUA
08:30 NY = 15:30 server no verão / 16:30 no inverno... ver nota) e grava
o _meta.json. A análise NÃO RODA sem meta verificado (falha alto).

Nota de fuso: servidor = UTC+2/+3 com DST dos EUA (ver data/raw/_meta).
Como o DST do servidor acompanha o dos EUA, o CPI dos EUA (08:30 NY) cai
SEMPRE em 15:30 do servidor, verão e inverno — é essa invariância que a
verificação usa (eventos "Consumer Price Index" dos EUA às 15:30).

Só dias research; holdout intocado.

Uso: python a18_calendar.py --ingest      # valida fuso e grava meta
     python a18_calendar.py               # roda H1/H2/H3 (exige meta ok)
"""
from __future__ import annotations

import argparse, json, pathlib, time

import numpy as np
import pandas as pd

from a1_label_days import window_bounds
from splits_days import research_days
from stats_blocks import block_permute, reality_check_p95

CAL_DIR = pathlib.Path("data/calendar")
CSV_PATH = CAL_DIR / "calendar_mt5.csv"
META_PATH = CAL_DIR / "_meta.json"
T0_HOUR, WINDOW_HOURS = 0.0, 12.0
G8 = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"]
COLS = ["event_id", "time_server", "country", "currency", "name",
        "importance", "actual", "forecast", "previous"]


# ----------------------------------------------------------------------------
# Carga / ingest
# ----------------------------------------------------------------------------

def load_calendar(path=CSV_PATH) -> pd.DataFrame:
    """Parser tolerante a encoding do MT5 (FILE_ANSI/UTF-16 conforme flag)."""
    p = pathlib.Path(path)
    if not p.exists():
        raise SystemExit(
            f"{p} não existe — rode s1_export_calendar.mq5 no MT5 e copie "
            "MQL5\\Files\\calendar_mt5.csv para data/calendar/.")
    df = None
    for enc in ("utf-8", "utf-16", "cp1252", "latin-1"):
        try:
            df = pd.read_csv(p, encoding=enc)
            if list(df.columns[:2]) == ["event_id", "time_server"]:
                break
        except (UnicodeError, UnicodeDecodeError):
            continue
    if df is None or list(df.columns[:2]) != ["event_id", "time_server"]:
        raise SystemExit("calendar_mt5.csv ilegível ou com colunas erradas")
    missing = [c for c in COLS if c not in df.columns]
    if missing:
        raise SystemExit(f"colunas ausentes no calendário: {missing}")
    df["time_server"] = pd.to_datetime(df["time_server"])
    df = df[df.currency.isin(G8)].copy()      # G8 only (defesa em profundidade)
    df["time_server"] = _normalize_calendar_tz(df["time_server"])
    return df


def _normalize_calendar_tz(ts: pd.Series) -> pd.Series:
    """Converte os timestamps do calendário para o RELÓGIO DOS PREÇOS.

    ACHADO da verificação de fuso (2026-07-07): o calendário do MT5 vem em
    UTC+3 FIXO o ano inteiro (CPI dos EUA: 15:30 no verão, 16:30 no
    inverno), enquanto o feed de preços é UTC+2/+3 com DST dos EUA
    (00:00 servidor = 17:00 NY o ano inteiro — data/raw/_meta.json). Sem
    esta conversão, toda junção evento×janela erraria 1h no inverno.

    Conversão: UTC = ts_calendário − 3h; NY = UTC→America/New_York;
    servidor = NY + 7h (invariante 00:00 = 17:00 NY)."""
    utc = ts - pd.Timedelta(hours=3)
    ny = utc.dt.tz_localize("UTC").dt.tz_convert("America/New_York")
    return ny.dt.tz_localize(None) + pd.Timedelta(hours=7)


def verify_tz(cal: pd.DataFrame) -> dict:
    """Âncora de fuso: CPI dos EUA (08:30 NY) deve cair às 15:30 do servidor
    o ano inteiro (DST do servidor acompanha o dos EUA). PARA se falhar."""
    # nomes vêm no idioma do terminal (PT-BR: "Índice de Preços ao
    # Consumidor (IPC)"); Cleveland/Fed regionais excluídos (horário próprio)
    usd = cal[(cal.currency == "USD") &
              cal.name.str.contains("CPI|Consumer Price Index|"
                                    "Preços ao Consumidor|IPC",
                                    case=False, regex=True) &
              ~cal.name.str.contains("Cleveland", case=False)]
    # eventos mensais 'm/m' e 'y/y' compartilham o horário do release
    if len(usd) < 6:
        raise SystemExit("verificação de fuso: <6 eventos de CPI dos EUA no "
                         "CSV — export incompleto? PARANDO (pré-registro).")
    horas = usd.time_server.dt.strftime("%H:%M").value_counts()
    top, frac = horas.index[0], horas.iloc[0] / len(usd)
    ok = (top == "15:30") and frac >= 0.8
    if not ok:
        raise SystemExit(
            f"verificação de fuso FALHOU: CPI dos EUA cai em {top} "
            f"({frac:.0%} dos casos) — esperado 15:30 server. PARANDO "
            "(pré-registro): confira o fuso do terminal/export.")
    return {"anchor": "US CPI", "horario_modal_server": top,
            "fracao_no_modal": round(float(frac), 3), "n_eventos_cpi": len(usd)}


def ingest():
    cal = load_calendar()
    ev = verify_tz(cal)
    META_PATH.parent.mkdir(parents=True, exist_ok=True)
    META_PATH.write_text(json.dumps({
        "ingest_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "n_eventos": len(cal), "n_high": int((cal.importance == "HIGH").sum()),
        "cobertura": [str(cal.time_server.min()), str(cal.time_server.max())],
        "tz_verificacao": ev, "tz_ok": True,
        "limitacao": "actual = valor atual no provedor (revisões não "
                     "reconstruíveis); uso preditivo só com a AGENDA",
    }, indent=2))
    print(f"ingest ok: {len(cal)} eventos, fuso verificado ({ev}) -> {META_PATH}")


# ----------------------------------------------------------------------------
# Análise (exige meta verificado)
# ----------------------------------------------------------------------------

def high_events_by_day(cal: pd.DataFrame, days) -> pd.DataFrame:
    """(day, currency) -> n de eventos HIGH da moeda na janela do dia."""
    high = cal[cal.importance == "HIGH"]
    rows = []
    for day in days:
        t0, t1 = window_bounds(day, T0_HOUR, WINDOW_HOURS)
        w = high[(high.time_server >= t0) & (high.time_server <= t1)]
        for c in G8:
            rows.append({"day": day, "currency": c,
                         "n_high": int((w.currency == c).sum())})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ingest", action="store_true")
    ap.add_argument("--n-perm", type=int, default=200)
    ap.add_argument("--perm-block", type=int, default=5)
    ap.add_argument("--n-boot", type=int, default=2000)
    a = ap.parse_args()
    if a.ingest:
        ingest()
        return

    if not META_PATH.exists() or not json.loads(META_PATH.read_text()).get("tz_ok"):
        raise SystemExit("data/calendar/_meta.json ausente ou fuso não "
                         "verificado — rode `python a18_calendar.py --ingest` "
                         "após copiar o CSV do s1.")
    cal = load_calendar()

    lab = pd.read_parquet("data/labels/labels_v1.parquet")
    train, valid = research_days(pd.DatetimeIndex(lab.day.unique()))
    keep = sorted(set(train) | set(valid))
    lab = lab[lab.day.isin(keep)]
    days = pd.DatetimeIndex(sorted(lab.day.unique()))

    hbd = high_events_by_day(cal, days)
    df = lab.merge(hbd, on=["day", "currency"], how="left")
    df["n_high"] = df["n_high"].fillna(0)
    df["has_high"] = df.n_high > 0

    rng = np.random.default_rng(0)

    def boot_prop_diff(da: pd.DataFrame, db: pd.DataFrame, col="labeled"):
        """Diferença de proporções com bootstrap em blocos POR DIA."""
        days_a, days_b = da.day.unique(), db.day.unique()
        point = da[col].mean() - db[col].mean()
        diffs = np.empty(a.n_boot)
        ga, gb = da.groupby("day"), db.groupby("day")
        for i in range(a.n_boot):
            ia = _block_sample(len(days_a), a.perm_block, rng)
            ib = _block_sample(len(days_b), a.perm_block, rng)
            pa = np.concatenate([ga.get_group(days_a[j])[col].to_numpy()
                                 for j in ia]).mean()
            pb = np.concatenate([gb.get_group(days_b[j])[col].to_numpy()
                                 for j in ib]).mean()
            diffs[i] = pa - pb
        return point, np.percentile(diffs, 2.5), np.percentile(diffs, 97.5)

    lines = [f"# a18 — Calendário × rótulos (dias research: {len(days)})", "",
             f"Eventos G8 no CSV: {len(cal)} | HIGH: "
             f"{(cal.importance=='HIGH').sum()} | pré-registro CHANGELOG "
             f"2026-07-07.", ""]

    # ---- H-A18-1 ----------------------------------------------------------
    da, db = df[df.has_high], df[~df.has_high]
    pt, lo, hi = boot_prop_diff(da, db)
    nulo1 = lo <= 0 <= hi
    lines += ["## H-A18-1 — notícia HIGH da moeda CRIA rótulo?", "",
              f"P(rótulo | HIGH) = {da.labeled.mean():.3f} (n={len(da)}) vs "
              f"P(rótulo | sem HIGH) = {db.labeled.mean():.3f} (n={len(db)})",
              f"Δ = {pt:+.3f}, IC95% [{lo:+.3f}, {hi:+.3f}] → "
              f"**{'NULO' if nulo1 else 'SIGNIFICATIVO'}**", ""]

    # ---- H-A18-2 ----------------------------------------------------------
    day_any_label = df.groupby("day").labeled.any()
    day_conflict = (df[df.has_high].groupby("day").currency.nunique()
                    .reindex(day_any_label.index).fillna(0) >= 2)
    dfl = pd.DataFrame({"day": day_any_label.index,
                        "labeled": day_any_label.values,
                        "conflict": day_conflict.values})
    d_no, d_yes = dfl[~dfl.labeled], dfl[dfl.labeled]
    pt2 = d_no.conflict.mean() - d_yes.conflict.mean()
    diffs = np.empty(a.n_boot)
    for i in range(a.n_boot):
        i_no = _block_sample(len(d_no), a.perm_block, rng)
        i_yes = _block_sample(len(d_yes), a.perm_block, rng)
        diffs[i] = d_no.conflict.to_numpy()[i_no].mean() - \
            d_yes.conflict.to_numpy()[i_yes].mean()
    lo2, hi2 = np.percentile(diffs, [2.5, 97.5])
    nulo2 = lo2 <= 0 <= hi2
    lines += ["## H-A18-2 — conflito (HIGH de ≥2 moedas) IMPEDE rótulo?", "",
              f"P(conflito | dia sem rótulo) = {d_no.conflict.mean():.3f} "
              f"(n={len(d_no)}) vs P(conflito | dia rotulado) = "
              f"{d_yes.conflict.mean():.3f} (n={len(d_yes)})",
              f"Δ = {pt2:+.3f}, IC95% [{lo2:+.3f}, {hi2:+.3f}] → "
              f"**{'NULO' if nulo2 else 'SIGNIFICATIVO'}**", ""]

    # ---- H-A18-3 (ex-ante: SÓ agenda; actual/forecast proibidos) ---------
    top_by_day = (lab[lab.labeled].sort_values("score", ascending=False)
                  .groupby("day").first())
    truth = {day: (r.currency, r.direction) for day, r in top_by_day.iterrows()}
    days_eval = [d for d in days if d in truth]

    agenda = hbd[hbd.n_high > 0]
    preds = {}
    for i, day in enumerate(days_eval):
        g = agenda[agenda.day == day]
        if g.empty:
            preds[day] = None                    # abstém: sem HIGH
            continue
        mx = g.n_high.max()
        top = g[g.n_high == mx]
        if len(top) != 1:
            preds[day] = None                    # abstém: empate
            continue
        c = top.currency.iloc[0]
        prev = [dd for dd in days_eval[:i]]
        direc = None
        if prev and truth[prev[-1]][0] == c:
            direc = truth[prev[-1]][1]           # persistência D-1 da moeda
        if direc is None:
            preds[day] = None                    # abstém: sem direção ex-ante
            continue
        preds[day] = (c, direc)

    opina = {d: p for d, p in preds.items() if p is not None}
    n3 = len(opina)
    acc3 = np.mean([opina[d] == truth[d] for d in opina]) if n3 else np.nan
    abst = 1 - n3 / len(days_eval)

    pers_hits = sum(truth[days_eval[i - 1]] == truth[days_eval[i]]
                    for i in range(1, len(days_eval)))
    pers = pers_hits / (len(days_eval) - 1)

    tarr = [truth[d] for d in days_eval]
    maxima = np.empty(a.n_perm)
    for it in range(a.n_perm):
        p = block_permute(len(days_eval), a.perm_block, rng)
        tp = {days_eval[i]: tarr[p[i]] for i in range(len(days_eval))}
        hits = sum(opina[d] == tp[d] for d in opina)
        maxima[it] = hits / n3 if n3 else 0.0
    p95 = reality_check_p95(maxima)

    small = " (n<100!)" if n3 < 100 else ""
    beats, beyond = (acc3 > pers), (acc3 > p95)
    lines += ["## H-A18-3 — agenda prevê em T0 (ex-ante; SÓ agenda)", "",
              f"Opina em {n3}/{len(days_eval)} dias (abstenção "
              f"{100*abst:.1f}%){small} | top-1 = **{100*acc3:.1f}%** | "
              f"persistência = {100*pers:.1f}% | p95 permutado = "
              f"{100*p95:.1f}%",
              f"→ **{'SOBREVIVE' if beats and beyond and n3 >= 100 else 'NULO'}**"
              f" (critério: bater ambos, n>=100)", ""]

    # ---- descritivo: trava × horário de notícia (se a17 já rodou) --------
    trava = sorted(pathlib.Path("results").glob("*_a17/trava_eventos.parquet"))
    if trava:
        ev = pd.read_parquet(trava[-1])
        high = cal[cal.importance == "HIGH"]
        deltas = []
        for r in ev.dropna(subset=["t_lock"]).itertuples():
            t0, t1 = window_bounds(r.day, T0_HOUR, WINDOW_HOURS)
            he = high[(high.currency == r.currency) &
                      (high.time_server >= t0) & (high.time_server <= t1)]
            if he.empty:
                continue
            tl = t0 + pd.Timedelta(minutes=r.t_lock)
            deltas.append(min((tl - t).total_seconds() / 3600
                              for t in he.time_server))
        if deltas:
            s = pd.Series(deltas)
            hist = s.round().value_counts().sort_index()
            lines += ["## Descritivo — t_lock − evento HIGH mais próximo (h)",
                      "", f"n={len(s)} | mediana {s.median():+.1f}h | "
                      f"% trava DEPOIS da notícia: {(s>0).mean()*100:.0f}%",
                      "", "| Δh (arred.) | n |", "|---|---|"]
            lines += [f"| {int(k):+d} | {v} |" for k, v in hist.items()]
            lines.append("")

    out = pathlib.Path(f"results/{time.strftime('%Y%m%d_%H%M%S')}_a18")
    out.mkdir(parents=True, exist_ok=True)
    (out / "params.json").write_text(json.dumps(
        {"n_dias": len(days), "n_perm": a.n_perm, "n_boot": a.n_boot,
         "perm_block": a.perm_block}, indent=2))
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"REPORT -> {out}/REPORT.md")


def _block_sample(n: int, block: int, rng) -> np.ndarray:
    """Amostra bootstrap de índices em blocos circulares (tamanho n)."""
    out = np.empty(n, dtype=int)
    pos = 0
    while pos < n:
        start = rng.integers(0, n)
        for j in range(min(block, n - pos)):
            out[pos] = (start + j) % n
            pos += 1
    return out


if __name__ == "__main__":
    main()
