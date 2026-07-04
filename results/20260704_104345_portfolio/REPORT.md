# A6 — Portfólio diário de 7 pares (dias research)

a5 não produziu regra sobrevivente; a regra abaixo é apenas REFERÊNCIA (resultado nulo — regra dura nº 7). Custos por par: majors 1.0 bp, crosses 2.0 bp, exóticos G8 3.0 bp.

| estratégia | n dias | média/dia (bp) | IC95% (bp) | % dias vencedores | total | max DD |
|---|---|---|---|---|---|---|
| regra_maior_|M|_D1 [NAO sobrevivente] | 395 | -0.02 | [-2.46, +2.53] | 48.6% | -0.08% | -7.12% |
| baseline_continuacao_D1 | 395 | -3.89 | [-6.78, -0.77] | 40.3% | -15.37% | -19.01% |
| baseline_persistencia | 394 | +0.22 | [-2.50, +2.89] | 51.5% | +0.86% | -7.29% |
| teto_oracle [lookahead: só p/ dimensionar custos] | 346 | +40.81 | [+37.68, +44.54] | 100.0% | +141.20% | 0.00% |

Leitura: IC95% por bootstrap em blocos (blocos de 5 dias). Estratégia só seria reportável como positiva com IC inteiro acima de 0 E acima dos baselines — condição não atingida se os ICs cruzam 0.
