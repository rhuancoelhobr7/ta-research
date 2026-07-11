# a37 — a26b com controle PAREADO por volatilidade

Alinhamento |pct_base−pct_quote|>=70 em M15 E H1; janela 16 barras. 23,380 eventos alinhados, 958,596 controles (subamostrados). Pareamento por decil de range das 16 barras anteriores.

## Volatilidade prévia (mediana de range das barras anteriores, pips)

- alinhados: **47.0** vs controle bruto: **27.4** — alinhamento OCORRE em regime mais volátil (o pareamento importa).

## MFE (excursão favorável, pips) e razão

- alinhado: **16.8** IC[16.4, 17.2]

- controle NÃO pareado: 11.5 → razão **1.46×** (o número do a26b)

- controle PAREADO por vol: **15.6** IC[15.4, 15.9] → razão **1.08×**

## Veredito

O incremento do CSS **SOME** após parear por volatilidade (razão 1.08× vs 1.46× não pareado). O 1.45× do a26b era sobretudo CLUSTERING DE VOLATILIDADE, não valor do CSS. O badge de 'confirmação concorrente' CAI — o CSS fica APENAS descritivo. Atualizar INDICATOR_CHANGELOG e a proposta de badge.
