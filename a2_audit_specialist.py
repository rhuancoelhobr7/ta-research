"""a2_audit_specialist.py — Fase A2: auditoria das chamadas do especialista.

Para cada chamada em specialist_calls.csv responde, com os rótulos v1:
  (1) O dia era rotulável? (a moeda chamada teve tendência absoluta medida)
  (2) A direção bate?
  (3) A moeda chamada era a de MAIOR score do dia, ou havia protagonista maior?
Saída: results/audit_specialist/REPORT.md (+ tabela csv).

Uso: python a2_audit_specialist.py
"""
import pathlib
import pandas as pd

LAB = pathlib.Path("data/labels/labels_v1.parquet")
CALLS = pathlib.Path("specialist_calls.csv")
OUT = pathlib.Path("results/audit_specialist")


def main():
    labels = pd.read_parquet(LAB)
    calls = pd.read_csv(CALLS, parse_dates=["date"])
    OUT.mkdir(parents=True, exist_ok=True)

    rows, lines = [], ["# Auditoria das chamadas do especialista\n"]
    for _, c in calls.iterrows():
        day = labels[labels.day == c.date]
        row = {"date": c.date.date(), "call": f"{c.currency} {c.direction}"}
        if day.empty:
            row |= {"in_data": False}
            lines.append(f"## {row['date']} — {row['call']}\nSEM DADOS para o dia "
                         f"(fora do período exportado ou feriado).\n")
        else:
            me = day[day.currency == c.currency]
            top = day.sort_values("score", ascending=False).iloc[0]
            labeled = bool(me.labeled.iloc[0]) if len(me) else False
            dir_ok = (me.direction.iloc[0] == c.direction) if len(me) else False
            row |= {"in_data": True, "labeled": labeled, "direction_match": dir_ok,
                    "score": float(me.score.iloc[0]) if len(me) else None,
                    "rank_of_call": int((day.score > me.score.iloc[0]).sum()) + 1
                                    if len(me) else None,
                    "day_top": f"{top.currency} {top.direction} (score {top.score:.2f})"}
            lines.append(
                f"## {row['date']} — chamada: {row['call']}\n"
                f"- Rotulável: **{labeled}** | Direção bate: **{dir_ok}** | "
                f"score {row['score']:.2f} | rank no dia: {row['rank_of_call']}\n"
                f"- Protagonista medida do dia: {row['day_top']}\n")
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "audit.csv", index=False)
    ok = df.get("labeled", pd.Series(dtype=bool)).fillna(False)
    dm = df.get("direction_match", pd.Series(dtype=bool)).fillna(False)
    lines.append(f"\n## Resumo\n{int((ok & dm).sum())}/{len(df)} chamadas "
                 f"confirmadas (rotulável + direção).\n\nLimite honesto: 7 casos "
                 f"validam a DEFINIÇÃO e auditam chamadas individuais; não medem "
                 f"a taxa de acerto do método (isso é a Fase B).\n")
    (OUT / "REPORT.md").write_text("\n".join(lines))
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
