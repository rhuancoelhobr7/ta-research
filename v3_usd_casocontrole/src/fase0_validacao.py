"""fase0_validacao.py — Gate de validação de dados (aborta se falhar).

Checa (config.yaml `dados`): (1) cobertura >= 4 anos contínuos nos 7 pares
e 2 TFs; (2) gaps <= 2% contra a grade teórica de pregão (seg 00:00 - sex
23:00 do servidor); (3) timezone documentado + evidência empírica (barras
de segunda abrem 00:00); (4) sanidade OHLC. Falha crítica => escreve
resultados/RELATORIO_FASE0_FALHA.md e sai com código 1 — NÃO degrada
silenciosamente. Sucesso => data/fase0_ok.json (gate das fases seguintes).
"""
from __future__ import annotations

import json
import sys

import pandas as pd

from comum import DATA, RES, config


def grade_teorica(ini: pd.Timestamp, fim: pd.Timestamp, tf: str) -> pd.DatetimeIndex:
    """Aberturas esperadas: seg 00:00 até sex 23:00 (H1) / seg-sex (D1)."""
    if tf == "H1":
        g = pd.date_range(ini.ceil("h"), fim.floor("h"), freq="1h")
        return g[(g.dayofweek < 5)]
    g = pd.date_range(ini.normalize(), fim.normalize(), freq="1D")
    return g[g.dayofweek < 5]


def main() -> int:
    cfg = config()["dados"]
    problemas: list[str] = []
    linhas = ["# RELATÓRIO FASE 0 — validação de dados", ""]
    resumo = {}

    for tf in cfg["timeframes"]:
        linhas.append(f"\n## {tf}\n")
        linhas.append("| par | barras | de | até | cobertura (dias) | gaps % | OHLC inválido | vol=0 | preço<=0 |")
        linhas.append("|---|---|---|---|---|---|---|---|---|")
        for par in cfg["pares"]:
            f = DATA / f"{tf}_{par}.parquet"
            if not f.exists():
                problemas.append(f"CRÍTICO: {f.name} ausente")
                continue
            df = pd.read_parquet(f)          # índice = ABERTURA (cru)
            ini, fim = df.index[0], df.index[-1]
            dias = (fim - ini).days
            alvo = cfg["anos"] * 365 - cfg["cobertura_tolerancia_dias"]
            if dias < alvo:
                problemas.append(f"CRÍTICO: {tf} {par} cobre só {dias}d (< {alvo}d)")

            grade = grade_teorica(ini, fim, tf)
            falt = grade.difference(df.index)
            pct = 100.0 * len(falt) / max(len(grade), 1)
            if pct > cfg["gap_max_pct"]:
                blocos = pd.Series(falt).dt.normalize().value_counts().head(15)
                problemas.append(
                    f"CRÍTICO: {tf} {par} com {pct:.2f}% de barras faltantes "
                    f"(> {cfg['gap_max_pct']}%). Dias mais afetados:\n"
                    + blocos.to_string())

            bad_ohlc = int(((df.high < df[["open", "close"]].max(axis=1)) |
                            (df.low > df[["open", "close"]].min(axis=1))).sum())
            vol0 = int((df.tick_volume <= 0).sum())
            neg = int((df[["open", "high", "low", "close"]] <= 0).any(axis=1).sum())
            if bad_ohlc or neg:
                problemas.append(f"CRÍTICO: {tf} {par} OHLC inválido={bad_ohlc}, preço<=0={neg}")

            linhas.append(f"| {par} | {len(df)} | {ini} | {fim} | {dias} | "
                          f"{pct:.2f} | {bad_ohlc} | {vol0} | {neg} |")
            resumo[f"{tf}_{par}"] = {"barras": len(df), "gap_pct": round(pct, 3)}

    # timezone: documentação + evidência (segundas H1 abrem 00:00)
    seg_ok, seg_n = 0, 0
    df = pd.read_parquet(DATA / "H1_EURUSD.parquet")
    aberturas = df.index[df.index.dayofweek == 0]
    primeiras = pd.Series(aberturas).groupby(pd.Series(aberturas).dt.normalize()).min()
    seg_n = len(primeiras)
    seg_ok = int((primeiras.dt.hour == 0).sum())
    linhas += ["\n## Timezone\n",
               "- Servidor (herdado do programa, `data/raw/_meta.json` verificado "
               "pelo usuário): **UTC+2 (inverno NA) / UTC+3 (verão NA)**, DST dos EUA; "
               "meia-noite do servidor = 17:00 NY.",
               "- Abertura de Tóquio (09:00 JST = 00:00 UTC) = **02:00/03:00 do servidor** "
               "→ T0 (meia-noite do servidor) precede Tóquio por 2-3h.",
               f"- Evidência empírica: {seg_ok}/{seg_n} segundas-feiras com primeira "
               f"barra H1 às 00:00 do servidor."]
    if seg_ok / max(seg_n, 1) < 0.95:
        problemas.append(f"CRÍTICO: só {seg_ok}/{seg_n} segundas abrem 00:00 — "
                         "fuso do servidor mudou vs programa; validar manualmente")

    RES.mkdir(exist_ok=True)
    if problemas:
        rel = RES / "RELATORIO_FASE0_FALHA.md"
        rel.write_text("\n".join(
            ["# FASE 0 FALHOU — estudo NÃO roda", ""] + [f"- {p}" for p in problemas]
            + ["", "---", ""] + linhas), encoding="utf-8")
        print(f"FASE 0 FALHOU — ver {rel}")
        return 1

    linhas += ["\n## Veredito\n", "Todas as validações passaram. Estudo liberado."]
    (RES / "RELATORIO_FASE0.md").write_text("\n".join(linhas), encoding="utf-8")
    (DATA / "fase0_ok.json").write_text(json.dumps(resumo, indent=2))
    print("FASE 0 OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
