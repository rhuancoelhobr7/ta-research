# Validação prospectiva — protocolo

A única forma honesta de testar os sinais daqui em diante: o holdout está esgotado
(a35/a35-bis) e o retrospecto (a38) mostrou os dois sinais econômicamente inúteis.
Aqui acumula-se uma amostra **genuinamente out-of-sample** ao longo do tempo,
registrando as previsões das regras **congeladas** ANTES do desfecho.

## Arquivos
- `frozen_params.json` — parâmetros do z-score (média/desvio do research),
  CONGELADOS. **Versionado. Não reeditar** (mudar = quebra a validade prospectiva).
- `predictions.csv` — 1 linha por (dia, sinal), escrita ANTES da janela fechar.
  Append-only, nunca reescrita. Versionar a cada rodada = história tamper-evident.
- `outcomes.csv` — pontuação, escrita só após a janela de 15h fechar. Append-only.

## Regras congeladas (idênticas ao a35/a35-bis/a38, zero parâmetros livres)
- **A (z-score@180)**: z = (mov@180 − média_research)/desvio_research; long top-1
  vs bottom-1 do ranking, fecha 15h.
- **B (persistência@240)**: direção = sinal do mov acumulado até 4h; long a moeda
  de maior |mov| vs a mais oposta, fecha 15h.
- Só entram dias **estritamente posteriores** ao `freeze_date` (o resto o projeto
  já viu).

## Cadência operacional (após exportar/ingerir M5 novo)
```
python a39_prospective.py --record   # registra previsões dos dias novos
python a39_prospective.py --score     # pontua as que já fecharam a janela de 15h
python a39_prospective.py --report     # estatística acumulada OOS
git add data/prospective/*.csv && git commit -m "prospectivo: +N dias"
```
Rodar `--freeze` UMA vez só (já feito); reexecutar sobrescreve os params — não
fazer sem motivo registrado.

## Critério (pré-registrado, sem parâmetros novos)
A amostra prospectiva confirma o veredito do a38 se acurácia direcional ~50% e
expectativa líquida por trade não-positiva. Se DIVERGIR muito do retrospecto,
investigar antes de qualquer conclusão. Nenhuma regra é ajustada aqui — só se
acumula evidência honesta.
