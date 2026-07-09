# a26b — Persistência de momentum (confirmação concorrente)

Gatilho: alinhamento |pct_base−pct_quote|≥70 em M15 E H1 (ao vivo). Janela 16 barras M15 (4h). 23,384 eventos alinhados vs 23,385 de controle. **Concorrente, não preditivo**; M15 proxy do M5.

## Q14 — Duração até devolver ≥30% (barras M15)

- alinhado: mediana **4** barras (60 min); controle: 4.

## MFE — excursão favorável máxima (pips)

- alinhado: mediana **16.8** IC95 [16.4, 17.2]

- controle:  mediana **11.6** IC95 [11.3, 11.8]

- **razão alinhado/controle: 1.45× → CSS-confirmação: movimento PERSISTE após o sinal**


> **CAVEAT**: o controle é de barras não-alinhadas, NÃO pareado por volatilidade recente. Alinhamento ocorre em trechos já voláteis, então parte da razão 1.45× é clustering de volatilidade (o ouro do a23, já capturado pelo ATR) — não valor ÚNICO do CSS. O achado limpo é a PERSISTÊNCIA (residual quase intacto em T+1/T+2), coerente com entrar no meio do movimento; isolar o incremento do CSS exige controle vol-pareado (follow-up).

## Q15 — Degradação do pct da moeda forte (média por barra)

T+0:90  T+2:89  T+4:86  T+6:82  T+8:79  T+10:76  T+12:73  T+14:71


_pct em T+0=90; cai p/ 70 em T+15. Mantém → janela de oportunidade ampla._

## Q16 — Entrada por lag (range residual mediano, pips)

T+0: 12.8  T+1: 11.5  T+2: 10.0


_Se T+2 ≈ T+0, entrar 2 barras depois ainda captura o grosso (movimento persistente); se cai muito, a entrada atrasada perde._

## Duração/MFE por sessão

| sess    |   dur_med |   mfe_med |     n |
|:--------|----------:|----------:|------:|
| londres |         4 |      19.8 | 10992 |
| ny      |         4 |      12.3 |  5042 |
| outro   |         4 |      13.3 |  1120 |
| tokyo   |         4 |      16.4 |  6230 |