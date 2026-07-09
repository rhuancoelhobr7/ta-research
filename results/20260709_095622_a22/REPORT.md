# a22 — Mapa de sessões (descritivo)

Amostra: 28 pares, 2016-07-11 → 2026-07-09, 290,739 linhas par×sessão×dia. Range em pips e normalizado pela mediana do próprio par. Tempo servidor→UTC DST-aware.

## Q1 — Ranking de sessões (INTENSIDADE = pips/hora)

_Ranqueado por intensidade (pips/h), não range total: overlap tem 3h vs 9h das outras — total confundiria com duração._

| session   |   pips_h_mediana |   intensidade_norm |   iqr_norm |   p90_norm |     n |
|:----------|-----------------:|-------------------:|-----------:|-----------:|------:|
| overlap   |           11.867 |              1.845 |      1.145 |      3.409 | 72572 |
| londres   |            6.167 |              0.967 |      0.592 |      1.754 | 72574 |
| ny        |            5.456 |              0.848 |      0.535 |      1.583 | 73047 |
| tokyo     |            4.589 |              0.724 |      0.466 |      1.373 | 72546 |

_Dispersão (IQR) reportada porque range é assimétrico. Estabilidade 1ª×2ª metade (Spearman medianas par×sessão): **0.868**._

## Q2 — Par dominante por sessão (mediana de pips)

**Top-5 NY:** GBPNZD (89), GBPCAD (83), GBPJPY (81), GBPAUD (81), EURNZD (71)


**Top-5 Londres:** GBPNZD (107), GBPJPY (99), GBPAUD (99), GBPCAD (94), EURNZD (83)


**Top-5 Tokyo:** GBPNZD (87), GBPAUD (80), GBPJPY (73), EURNZD (73), EURAUD (67)


### Heatmap par×sessão (mediana de pips, sombreado por coluna)

| par | tokyo | londres | ny | overlap |
|---|---|---|---|---|
| AUDCAD |     34 |     42 |     40 |     28 |
| AUDCHF |     31 |     36 |     31 |     23 |
| AUDJPY | ▒▒▒ 50 | ░░░ 51 | ░░░ 47 | ░░░ 34 |
| AUDNZD |     33 |     32 |     29 |     21 |
| AUDUSD | ░░░ 36 |     41 |     38 |     27 |
| CADCHF |     22 |     38 |     35 |     25 |
| CADJPY | ░░░ 40 | ░░░ 55 | ░░░ 52 | ░░░ 37 |
| CHFJPY | ▒▒▒ 50 | ▒▒▒ 65 | ▒▒▒ 54 | ▒▒▒ 40 |
| EURAUD | ▓▓▓ 67 | ▓▓▓ 78 | ▓▓▓ 66 | ▓▓▓ 49 |
| EURCAD | ░░░ 40 | ▒▒▒ 72 | ▓▓▓ 67 | ▓▓▓ 49 |
| EURCHF |     24 |     37 |     30 |     22 |
| EURGBP |     25 |     40 |     31 |     24 |
| EURJPY | ▒▒▒ 57 | ▒▒▒ 72 | ▒▒▒ 60 | ▒▒▒ 43 |
| EURNZD | ▓▓▓ 73 | ▓▓▓ 83 | ▓▓▓ 71 | ▓▓▓ 51 |
| EURUSD | ░░░ 35 | ░░░ 55 | ░░░ 49 | ░░░ 35 |
| GBPAUD | ███ 80 | ███ 99 | ███ 81 | ███ 61 |
| GBPCAD | ▒▒▒ 53 | ███ 94 | ███ 83 | ███ 60 |
| GBPCHF | ░░░ 42 | ▒▒▒ 66 | ░░░ 52 | ▒▒▒ 39 |
| GBPJPY | ▓▓▓ 73 | ███ 99 | ███ 81 | ███ 59 |
| GBPNZD | ███ 87 | ███ 107 | ███ 89 | ███ 65 |
| GBPUSD | ▒▒▒ 48 | ▒▒▒ 75 | ▒▒▒ 63 | ▒▒▒ 46 |
| NZDCAD |     33 |     42 |     40 |     28 |
| NZDCHF |     28 |     33 |     29 |     20 |
| NZDJPY | ░░░ 44 |     46 | ░░░ 41 |     29 |
| NZDUSD |     33 |     39 |     36 |     25 |
| USDCAD |     33 | ░░░ 57 | ▒▒▒ 59 | ▒▒▒ 42 |
| USDCHF |     29 |     47 | ░░░ 42 | ░░░ 30 |
| USDJPY | ░░░ 47 | ░░░ 58 | ▒▒▒ 55 | ░░░ 38 |


## Q2b — Afinidade relativa de sessão (folclore testado)

_Share de intensidade Tok/Ldn/NY (soma 1, exclui overlap). Absoluto (pips) é dominado por GBP em toda sessão; o relativo revela a praça._

|               |   tokyo |   londres |    ny |
|:--------------|--------:|----------:|------:|
| Asia(AUD/NZD) |   0.312 |     0.366 | 0.323 |
| Eur/USD/CAD   |   0.245 |     0.402 | 0.353 |
| JPY           |   0.304 |     0.369 | 0.327 |


_Mais Tokyo-heavy:_ AUDNZD (0.35), AUDJPY (0.34), NZDJPY (0.34), EURNZD (0.32)  ·  _menos Tokyo (Ldn/NY):_ GBPCAD (0.23), CADCHF (0.23), USDCAD (0.22), EURCAD (0.22)


## Q3 — Dia da semana (range normalizado, mediana)

| session   |   seg |   ter |   qua |   qui |   sex |
|:----------|------:|------:|------:|------:|------:|
| tokyo     | 0.692 | 0.761 | 0.733 | 0.748 | 0.694 |
| londres   | 0.872 | 0.975 | 0.971 | 1.002 | 1.011 |
| ny        | 0.733 | 0.829 | 0.91  | 0.899 | 0.893 |
| overlap   | 1.639 | 1.84  | 1.867 | 1.941 | 1.954 |


### Notícias HIGH (covariável, período do calendário)

| session   |   sem_news |   com_news |   lift |
|:----------|-----------:|-----------:|-------:|
| tokyo     |      0.691 |      0.698 |  1.01  |
| londres   |      0.828 |      0.911 |  1.1   |
| ny        |      0.733 |      0.837 |  1.141 |
| overlap   |      1.625 |      1.789 |  1.101 |

