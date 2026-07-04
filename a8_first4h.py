"""a8_first4h.py — Dataset descritivo: rótulos do dia × estados nas 1as 4h.

Extensão DESCRITIVA do B1 (PLAN.md §5) — NENHUMA regra de trading é proposta
ou avaliada aqui; padrões salientes vão para "Hipóteses para estudo v2".

Período default: últimos ~126 dias úteis do conjunto RESEARCH (termina no
corte do holdout de splits_days; nunca depois). `--include-holdout` estende
até os dias mais recentes, marca `is_holdout` e imprime o aviso de exposição
no topo do REPORT — NÃO usar sem ordem explícita do usuário.

Por (dia, moeda):
  - rótulo do dia (labels_v1): labeled, direction, score, breadth_dir, z, er;
  - snapshots em T0+1h..T0+4h: state/dir do M30 e do H1 (+ M no H1), usando
    exclusivamente barras FECHADAS até cada instante (disciplina do a4;
    teste de lookahead em tests/test_first4h.py);
  - contexto de T0: state/dir do H4 e do D1, t/M/pers/dir do W1 (reduzido);
  - realizado: idx_ret_4h = Δ do índice sintético em [T0, T0+4h] (convenção
    de janela do a1) e align_4h = sinal das 4h bate com a direção rotulada.

Saídas: data/features/first4h.parquet
        results/{ts}_first4h/REPORT.md (lista dia-a-dia + resumo descritivo)

Uso: python a8_first4h.py [--n-days 126] [--include-holdout] [--boot-block 5]
"""
from __future__ import annotations

import argparse, json, pathlib, time
from datetime import timedelta

import numpy as np
import pandas as pd

from a1_label_days import load_closes, window_diff
from a4_features_t0 import features_at_t0, load_d1_closes, tf_feature_tables
from cssm_engine import G8, CssmParams, build_indices
from splits_days import day_cuts, research_days
from stats_blocks import block_bootstrap_ci

SNAP_HOURS = (1, 2, 3, 4)
CTX_COLS = ["H4_state", "H4_dir", "D1_state", "D1_dir",
            "W1_t", "W1_M", "W1_pers", "W1_dir"]
LABEL_COLS = ["labeled", "direction", "score", "breadth_dir", "z", "er"]
STATE_FMT = {0: "Ruído", 1: "Emergindo", 2: "Madura", 3: "Exausta", -1: "aquec"}


# ----------------------------------------------------------------------------
# Núcleo puro (testável)
# ----------------------------------------------------------------------------

def _validate_warmup(tables, days: pd.DatetimeIndex, t0_hour: float,
                     p: CssmParams):
    """M30/H1 em modo completo pedem ~w_mid+z_win barras fechadas até o 1º
    snapshot do período — aborta com mensagem clara se não houver."""
    need = p.w_mid + p.z_win
    first_snap = (days.min() + timedelta(hours=t0_hour + SNAP_HOURS[0]))
    for tf in ("M30", "H1"):
        f = tables[tf][G8[0]]
        have = int(np.searchsorted(f.index.to_numpy(),
                                   np.datetime64(first_snap), side="right"))
        if have < need:
            raise SystemExit(
                f"Aquecimento insuficiente no {tf}: {have} barras fechadas "
                f"até {first_snap}, mínimo {need} (w_mid+z_win). Escolha um "
                f"período mais tardio ou exporte mais histórico M5.")


def _lookup(f: pd.DataFrame, cols: list[str], when: np.ndarray) -> dict:
    """Última barra com FECHAMENTO <= instante (f é indexado por fechamento)."""
    pos = np.searchsorted(f.index.to_numpy(), when, side="right") - 1
    ok = pos >= 0
    sel = np.where(ok, pos, 0)
    return {c: np.where(ok, f[c].to_numpy()[sel], np.nan) for c in cols}


def build_first4h(m5_closes: dict[str, pd.Series],
                  d1_closes: dict[str, pd.Series],
                  labels: pd.DataFrame, days: pd.DatetimeIndex,
                  t0_hour: float, p: CssmParams = CssmParams()) -> pd.DataFrame:
    """Uma linha por (dia, moeda) com rótulo, snapshots 4h, contexto e 4h
    realizadas. Função pura — não lê disco, não escreve."""
    days = pd.DatetimeIndex(sorted(days))
    tables = tf_feature_tables(m5_closes, d1_closes, p)
    _validate_warmup(tables, days, t0_hour, p)

    out = pd.DataFrame({"day": np.repeat(days, len(G8)),
                        "currency": np.tile(G8, len(days))})
    t0s = np.array([np.datetime64(d + timedelta(hours=t0_hour)) for d in days])

    # snapshots M30/H1 nas primeiras 4h
    for tf, cols in (("M30", ["state", "dir"]), ("H1", ["state", "dir", "M"])):
        for k in SNAP_HOURS:
            when = t0s + np.timedelta64(k, "h")
            block = {f"{tf}_{c}_h{k}": np.full(len(out), np.nan) for c in cols}
            for ci, c in enumerate(G8):
                vals = _lookup(tables[tf][c], cols, when)
                for col in cols:
                    block[f"{tf}_{col}_h{k}"][ci::len(G8)] = vals[col]
            for name, v in block.items():
                out[name] = v

    # contexto de T0 (reusa a disciplina e os gates do a4)
    ctx = features_at_t0(tables, days, t0_hour, p)
    out = out.merge(ctx[["day", "currency"] + CTX_COLS],
                    on=["day", "currency"], how="left")

    # rótulo do dia
    out = out.merge(labels[["day", "currency"] + LABEL_COLS],
                    on=["day", "currency"], how="left")
    out["labeled"] = out["labeled"].fillna(False).astype(bool)

    # realizado nas 4h (índice sintético M5; convenção de janela do a1)
    indices = build_indices(m5_closes, align="inner")
    ret4 = np.full(len(out), np.nan)
    for ci, c in enumerate(G8):
        s = indices[c]
        for di, d in enumerate(days):
            t0 = d + timedelta(hours=t0_hour)
            ret4[di * len(G8) + ci] = window_diff(s, t0, t0 + timedelta(hours=4))
    out["idx_ret_4h"] = ret4
    dir_sign = np.where(out.direction == "ALTA", 1.0,
                        np.where(out.direction == "BAIXA", -1.0, np.nan))
    out["align_4h"] = pd.array(
        np.where(np.isnan(ret4) | np.isnan(dir_sign), None,
                 np.sign(ret4) * dir_sign > 0), dtype="boolean")
    return out


# ----------------------------------------------------------------------------
# Relatório
# ----------------------------------------------------------------------------

def _fmt_state(st, dr) -> str:
    if pd.isna(st):
        return "?"
    name = STATE_FMT.get(int(st), "?")
    if st > 0 and not pd.isna(dr) and dr != 0:
        name += "↑" if dr > 0 else "↓"
    return name


def _day_lines(df: pd.DataFrame) -> list[str]:
    lines = []
    for day, g in df.groupby("day"):
        lab = g[g.labeled].sort_values("score", ascending=False)
        dstr = pd.Timestamp(day).date().isoformat()
        hold = " [HOLDOUT]" if g.is_holdout.iloc[0] else ""
        if lab.empty:
            lines.append(f"- {dstr}{hold} — sem tendência absoluta")
            continue
        for r in lab.itertuples():
            h1 = "→".join(_fmt_state(getattr(r, f"H1_state_h{k}"),
                                     getattr(r, f"H1_dir_h{k}"))
                          for k in SNAP_HOURS)
            m30 = "→".join(_fmt_state(getattr(r, f"M30_state_h{k}"),
                                      getattr(r, f"M30_dir_h{k}"))
                           for k in SNAP_HOURS)
            bp = (f"{r.idx_ret_4h*1e4:+.0f}bp"
                  if np.isfinite(r.idx_ret_4h) else "?")
            tick = "?" if pd.isna(r.align_4h) else ("✓" if r.align_4h else "✗")
            w1t = f"t={r.W1_t:+.1f}" if np.isfinite(r.W1_t) else "t=?"
            lines.append(
                f"- {dstr}{hold} — {r.currency} {r.direction} "
                f"(score {r.score:.2f}) | 4h: {bp} {tick} | H1: {h1} | "
                f"M30: {m30} | T0: H4 {_fmt_state(r.H4_state, r.H4_dir)} · "
                f"D1 {_fmt_state(r.D1_state, r.D1_dir)} · W1 {w1t}")
    return lines


def _day_block_ci(day_of_row: np.ndarray, values: np.ndarray, block: int,
                  seed: int = 0):
    """Bootstrap em blocos de DIAS (reamostra dias; média sobre as linhas)."""
    udays = np.array(sorted(pd.unique(day_of_row)))
    rows_by_day = [np.where(day_of_row == d)[0] for d in udays]
    def stat(day_idx):
        sel = np.concatenate([rows_by_day[int(i)] for i in day_idx])
        v = values[sel]
        v = v[~np.isnan(v)]
        return v.mean() if len(v) else np.nan
    return block_bootstrap_ci(np.arange(len(udays), dtype=float), stat=stat,
                              n_boot=2000, block=block, seed=seed)


def _active_in_dir(df: pd.DataFrame, tf: str, k: int) -> np.ndarray:
    """1.0 se estado ativo (>=Emergindo) NA direção do dia; NaN se sem info."""
    st = df[f"{tf}_state_h{k}"].to_numpy(dtype=float)
    dr = df[f"{tf}_dir_h{k}"].to_numpy(dtype=float)
    sgn = np.where(df.direction == "ALTA", 1.0,
                   np.where(df.direction == "BAIXA", -1.0, np.nan))
    val = ((st >= 1) & (dr * sgn > 0)).astype(float)
    val[np.isnan(st) | np.isnan(sgn) | (st < 0)] = np.nan
    return val


def _n_flag(n: int) -> str:
    return " (n<100 — amostra insuficiente)" if n < 100 else ""


def summary_lines(df: pd.DataFrame, block: int) -> list[str]:
    lines = ["## (b) Resumo descritivo (sem fitting, sem seleção de regra)", ""]
    day_arr = df.day.to_numpy()
    lab_m = df.labeled.to_numpy()
    hypotheses = []

    lines += ["### Estado ativo (≥Emergindo) na direção do dia",
              "", "| TF | instante | rotuladas | não-rotuladas |",
              "|---|---|---|---|"]
    for tf in ("H1", "M30"):
        for k in (2, 4):
            v = _active_in_dir(df, tf, k)
            va, vb = np.where(lab_m, v, np.nan), np.where(~lab_m, v, np.nan)
            na = int(np.isfinite(va).sum()); nb = int(np.isfinite(vb).sum())
            sa, la, ha = _day_block_ci(day_arr, va, block)
            sb, lb, hb = _day_block_ci(day_arr, vb, block, seed=1)
            lines.append(
                f"| {tf} | T0+{k}h | **{100*sa:.1f}%** "
                f"[{100*la:.1f}, {100*ha:.1f}] (n={na}{_n_flag(na)}) | "
                f"{100*sb:.1f}% [{100*lb:.1f}, {100*hb:.1f}] "
                f"(n={nb}{_n_flag(nb)}) |")
            if np.isfinite(la) and np.isfinite(hb) and la > hb:
                hypotheses.append(
                    f"{tf} em T0+{k}h ativo-na-direção é mais frequente nas "
                    f"rotuladas ({100*sa:.0f}% vs {100*sb:.0f}%, ICs disjuntos)"
                    " — candidata a feature de confirmação intraday em v2.")

    v = df.align_4h.to_numpy(dtype="float")
    va = np.where(lab_m, v, np.nan)
    na = int(np.isfinite(va).sum())
    sa, la, ha = _day_block_ci(day_arr, va, block, seed=2)
    lines += ["", "### align_4h (rotuladas): sinal das 4h bate com a direção "
              "do dia",
              f"- **{100*sa:.1f}%** IC95% [{100*la:.1f}, {100*ha:.1f}] "
              f"(n={na}{_n_flag(na)}); complemento = dias em que a tendência "
              "rotulada ainda não apontava na direção após 4h."]
    if np.isfinite(la) and la > 0.5:
        hypotheses.append(
            f"Nas rotuladas, o sinal das primeiras 4h já bate com a direção "
            f"do dia em {100*sa:.0f}% (IC acima de 50%) — as 4h iniciais "
            "carregam parte do movimento (coerente com A3/Tokyo).")

    st4 = df["H1_state_h4"].to_numpy(dtype=float)
    cat = np.where(np.isnan(st4), "sem dado",
                   np.vectorize(lambda s: STATE_FMT.get(int(s), "?"))(
                       np.nan_to_num(st4, nan=-1)))
    mat = pd.crosstab(pd.Series(cat, name="H1 em T0+4h"),
                      pd.Series(np.where(lab_m, "rotulou", "não"), name=""),
                      margins=True)
    pct = (100 * mat["rotulou"] / mat["All"]).round(1)
    lines += ["", "### Estado H1 em T0+4h × rotulou no dia", "",
              "| H1 em T0+4h | rotulou | não | P(rotulou\\|estado) |",
              "|---|---|---|---|"]
    for idx in mat.index:
        if idx == "All":
            continue
        lines.append(f"| {idx} | {mat.loc[idx, 'rotulou']} | "
                     f"{mat.loc[idx, 'não'] if 'não' in mat.columns else 0} | "
                     f"{pct[idx]}% |")
    lines += ["", "## Hipóteses para estudo v2", ""]
    lines += ([f"- {h}" for h in hypotheses] or
              ["- Nenhum padrão saliente além dos ICs reportados."])
    lines += ["", "*(Seção descritiva — nenhuma métrica de estratégia; "
              "qualquer hipótese acima exige v2 com Fase B reiniciada.)*"]
    return lines


# ----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-days", type=int, default=126)
    ap.add_argument("--include-holdout", action="store_true",
                    help="EXPÕE O HOLDOUT no relatório — só sob ordem "
                         "explícita do usuário")
    ap.add_argument("--boot-block", type=int, default=5)
    a = ap.parse_args()

    meta = json.loads(
        pathlib.Path("data/labels/labels_v1_meta.json").read_text())
    labels = pd.read_parquet("data/labels/labels_v1.parquet")
    all_days = pd.DatetimeIndex(sorted(labels.day.unique()))
    train, valid = research_days(all_days)
    research = pd.DatetimeIndex(np.concatenate([train, valid]))
    _, v_cut = day_cuts(all_days)

    sel = research[-a.n_days:]
    if a.include_holdout:
        sel = sel.append(all_days[all_days >= v_cut])
    sel = pd.DatetimeIndex(sorted(sel.unique()))

    df = build_first4h(load_closes(), load_d1_closes(), labels, sel,
                       meta["t0_hour"])
    df["is_holdout"] = df.day >= v_cut

    outdir = pathlib.Path("data/features")
    outdir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(outdir / "first4h.parquet")

    ts = time.strftime("%Y%m%d_%H%M%S")
    rep = pathlib.Path(f"results/{ts}_first4h")
    rep.mkdir(parents=True, exist_ok=True)
    lines = []
    if a.include_holdout:
        lines += ["> **ESTE RELATÓRIO EXPÕE O HOLDOUT — qualquer regra "
                  "derivada dele não pode mais ser testada como final**", ""]
    lines += ["# A8 — Rótulos do dia × estados nas primeiras 4h",
              f"Período: {sel.min().date()} a {sel.max().date()} "
              f"({len(sel)} dias; research{' + holdout' if a.include_holdout else ''}). "
              f"Definição v1 congelada; T0+{SNAP_HOURS[0]}h..T0+{SNAP_HOURS[-1]}h; "
              "snapshots só com barras fechadas.", "",
              "## (a) A lista", ""]
    lines += _day_lines(df)
    lines.append("")
    lines += summary_lines(df, a.boot_block)

    (rep / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    (rep / "params.json").write_text(json.dumps(
        {"n_days": a.n_days, "include_holdout": a.include_holdout,
         "boot_block": a.boot_block, "period": [str(sel.min().date()),
                                                str(sel.max().date())],
         "n_rows": len(df), "labels_meta": meta}, indent=2))
    print(f"{len(df)} linhas -> data/features/first4h.parquet | "
          f"OK -> {rep}/REPORT.md")


if __name__ == "__main__":
    main()
