# a15 — Autenticação do ledger dos prints contra o M5

Ledger: specialist_ledger.csv | 63 pernas, 9 dias (2026-06-19 → 2026-07-06) | tol preço 15.0bp, tol lucro 3.0%

**Enquadramento honesto**: trades encerrados publicados ex-post — vencedores por construção. Este relatório atesta apenas CONSISTÊNCIA COM PREÇOS REAIS, que NÃO prova conta real nem skill (demo usa os mesmos preços; a seleção ex-post permanece). Hit rate preditivo = papel do a14.

**Holdout**: dias do ledger caem na região de holdout. Este script leu APENAS closes M5 brutos (sem labels, splits, índices ou regras) — precedente da Etapa 3 do a11.

**Limitação**: o print só tem horário de FECHAMENTO; a checagem de price_in é de plausibilidade (range do dia), não de carimbo exato.

## Resumo: price_out 48/63 | price_in 63/63 | profit 63/63

## ⚠ FALHAS (sem edição do CSV — achado, não conserto)

- 2026-06-22 EURGBP price_out: M5@-2min
- 2026-06-22 GBPAUD price_out: M5@-2min
- 2026-06-22 GBPCAD price_out: M5@-2min
- 2026-06-22 GBPCHF price_out: M5@-2min
- 2026-06-22 GBPJPY price_out: M5@-2min
- 2026-06-22 GBPNZD price_out: M5@-2min
- 2026-06-22 GBPUSD price_out: M5@-2min
- 2026-06-23 AUDCHF price_out: M5@-0min
- 2026-06-23 EURAUD price_out: M5@-1min
- 2026-06-24 AUDJPY price_out: M5@-1min
- 2026-06-24 GBPJPY price_out: M5@-2min
- 2026-06-24 NZDJPY price_out: M5@-2min
- 2026-06-25 EURCAD price_out: M5@+2min
- 2026-06-25 EURJPY price_out: M5@+2min
- 2026-06-25 EURUSD price_out: M5@+2min

## Por perna

| perna | price_out | price_in | profit | obs |
|---|---|---|---|---|
| 2026-06-19 AUDNZD buy | PASS (2.1bp) | PASS (0.0bp) | PASS (0.11%) | M5@+2min; range=[1.21732,1.22244]; recon=10,939.33 |
| 2026-06-19 EURNZD buy | PASS (1.8bp) | PASS (0.0bp) | PASS (0.11%) | M5@+2min; range=[1.98931,1.99639]; recon=19,608.23 |
| 2026-06-19 GBPNZD buy | PASS (13.8bp) | PASS (0.0bp) | PASS (0.11%) | M5@+2min; range=[2.29235,2.30220]; recon=36,326.82 |
| 2026-06-19 NZDCAD sell | PASS (9.0bp) | PASS (0.0bp) | PASS (0.03%) | M5@+2min; range=[0.81031,0.81454]; recon=8,396.77 |
| 2026-06-19 NZDCHF sell | PASS (0.6bp) | PASS (0.0bp) | PASS (0.13%) | M5@+2min; range=[0.46240,0.46351]; recon=1,634.72 |
| 2026-06-19 NZDJPY sell | PASS (11.4bp) | PASS (0.0bp) | PASS (0.00%) | M5@+2min; range=[92.39700,92.92000]; recon=8,926.86 |
| 2026-06-19 NZDUSD sell | PASS (12.4bp) | PASS (0.0bp) | PASS (0.00%) | M5@+2min; range=[0.57239,0.57618]; recon=9,000.00 |
| 2026-06-22 EURGBP sell | FAIL (21.4bp) | PASS (0.0bp) | PASS (0.33%) | M5@-2min; range=[0.86683,0.86859]; recon=18,049.80 |
| 2026-06-22 GBPAUD buy | FAIL (26.7bp) | PASS (0.0bp) | PASS (0.07%) | M5@-2min; range=[1.88089,1.88736]; recon=16,168.84 |
| 2026-06-22 GBPCAD buy | FAIL (26.7bp) | PASS (0.0bp) | PASS (0.07%) | M5@-2min; range=[1.86825,1.87517]; recon=16,165.32 |
| 2026-06-22 GBPCHF buy | FAIL (17.0bp) | PASS (0.0bp) | PASS (0.17%) | M5@-2min; range=[1.06484,1.06860]; recon=14,314.68 |
| 2026-06-22 GBPJPY buy | FAIL (31.4bp) | PASS (0.0bp) | PASS (0.03%) | M5@-2min; range=[213.08800,213.69700]; recon=33,419.47 |
| 2026-06-22 GBPNZD buy | FAIL (22.5bp) | PASS (0.0bp) | PASS (0.12%) | M5@-2min; range=[2.29970,2.30782]; recon=23,313.06 |
| 2026-06-22 GBPUSD buy | FAIL (34.1bp) | PASS (0.0bp) | PASS (0.00%) | M5@-2min; range=[1.31873,1.32322]; recon=21,300.00 |
| 2026-06-23 AUDCAD sell | PASS (5.2bp) | PASS (0.0bp) | PASS (0.11%) | M5@-0min; range=[0.98586,0.99139]; recon=14,735.56 |
| 2026-06-23 AUDCHF sell | FAIL (19.9bp) | PASS (0.0bp) | PASS (0.25%) | M5@-0min; range=[0.56223,0.56623]; recon=15,517.31 |
| 2026-06-23 AUDJPY sell | PASS (10.0bp) | PASS (0.0bp) | PASS (0.05%) | M5@-0min; range=[112.36800,113.15700]; recon=26,306.99 |
| 2026-06-23 AUDNZD sell | PASS (4.8bp) | PASS (0.0bp) | PASS (0.02%) | M5@-0min; range=[1.22221,1.22567]; recon=8,707.23 |
| 2026-06-23 AUDUSD sell | PASS (4.6bp) | PASS (0.0bp) | PASS (0.00%) | M5@-0min; range=[0.69502,0.70014]; recon=21,900.00 |
| 2026-06-23 EURAUD buy | FAIL (20.9bp) | PASS (0.0bp) | PASS (0.05%) | M5@-1min; range=[1.63114,1.64338]; recon=24,218.02 |
| 2026-06-23 GBPAUD buy | PASS (14.5bp) | PASS (0.0bp) | PASS (0.05%) | M5@-1min; range=[1.89171,1.90386]; recon=25,428.92 |
| 2026-06-24 AUDJPY sell | FAIL (18.5bp) | PASS (0.0bp) | PASS (0.01%) | M5@-1min; range=[111.51400,111.83700]; recon=11,799.48 |
| 2026-06-24 CADJPY sell | PASS (0.9bp) | PASS (0.0bp) | PASS (0.01%) | M5@-1min; range=[113.60800,113.74800]; recon=1,484.21 |
| 2026-06-24 CHFJPY sell | PASS (13.2bp) | PASS (0.3bp) | PASS (0.01%) | M5@-2min; range=[199.20200,199.59700]; recon=21,632.39 |
| 2026-06-24 EURJPY sell | PASS (14.6bp) | PASS (0.3bp) | PASS (0.01%) | M5@-2min; range=[183.54900,183.90900]; recon=19,517.38 |
| 2026-06-24 GBPJPY sell | FAIL (26.3bp) | PASS (0.0bp) | PASS (0.01%) | M5@-2min; range=[213.06600,213.48100]; recon=19,851.33 |
| 2026-06-24 NZDJPY sell | FAIL (30.6bp) | PASS (0.0bp) | PASS (0.01%) | M5@-2min; range=[91.28900,91.60200]; recon=15,250.28 |
| 2026-06-24 USDJPY sell | PASS (1.4bp) | PASS (0.0bp) | PASS (0.01%) | M5@-2min; range=[161.48500,161.72600]; recon=-5,343.16 |
| 2026-06-25 EURAUD sell | PASS (11.4bp) | PASS (0.0bp) | PASS (0.17%) | M5@+2min; range=[1.64520,1.64967]; recon=2,651.14 |
| 2026-06-25 EURCAD sell | FAIL (15.5bp) | PASS (0.0bp) | PASS (0.14%) | M5@+2min; range=[1.61535,1.61786]; recon=4,428.51 |
| 2026-06-25 EURCHF sell | PASS (0.1bp) | PASS (0.0bp) | PASS (0.30%) | M5@+2min; range=[0.92106,0.92265]; recon=5,847.45 |
| 2026-06-25 EURGBP sell | PASS (5.0bp) | PASS (0.0bp) | PASS (0.24%) | M5@+2min; range=[0.86135,0.86273]; recon=6,410.87 |
| 2026-06-25 EURJPY sell | FAIL (21.0bp) | PASS (0.0bp) | PASS (0.09%) | M5@+2min; range=[183.55300,183.97600]; recon=2,595.80 |
| 2026-06-25 EURNZD sell | PASS (8.0bp) | PASS (0.0bp) | PASS (0.20%) | M5@+2min; range=[2.00760,2.01666]; recon=372.81 |
| 2026-06-25 EURUSD sell | FAIL (29.3bp) | PASS (0.0bp) | PASS (0.00%) | M5@+2min; range=[1.13482,1.13716]; recon=9,180.00 |
| 2026-06-29 AUDJPY buy | PASS (8.4bp) | PASS (0.0bp) | PASS (0.03%) | M5@-1min; range=[111.33300,111.69400]; recon=4,115.81 |
| 2026-06-29 CADJPY buy | PASS (1.1bp) | PASS (0.0bp) | PASS (0.03%) | M5@-1min; range=[113.91100,114.12000]; recon=741.59 |
| 2026-06-29 CHFJPY buy | PASS (10.1bp) | PASS (0.0bp) | PASS (0.03%) | M5@-1min; range=[199.46000,200.11500]; recon=17,575.63 |
| 2026-06-29 EURJPY buy | PASS (5.4bp) | PASS (0.0bp) | PASS (0.03%) | M5@-1min; range=[184.02100,184.63700]; recon=13,830.61 |
| 2026-06-29 GBPJPY buy | PASS (5.3bp) | PASS (0.0bp) | PASS (0.03%) | M5@-1min; range=[213.38000,214.00800]; recon=16,389.09 |
| 2026-06-29 NZDJPY buy | PASS (2.5bp) | PASS (0.0bp) | PASS (0.03%) | M5@-1min; range=[91.09100,91.53500]; recon=8,417.02 |
| 2026-06-29 USDJPY buy | PASS (2.7bp) | PASS (0.0bp) | PASS (0.03%) | M5@-1min; range=[161.68800,161.83800]; recon=2,336.00 |
| 2026-06-30 AUDNZD sell | PASS (9.1bp) | PASS (0.0bp) | PASS (0.04%) | M5@+1min; range=[1.21572,1.21884]; recon=3,970.65 |
| 2026-06-30 EURNZD sell | PASS (3.0bp) | PASS (0.0bp) | PASS (0.04%) | M5@+1min; range=[2.01550,2.02254]; recon=20,905.32 |
| 2026-06-30 GBPNZD sell | PASS (0.9bp) | PASS (0.0bp) | PASS (0.04%) | M5@+1min; range=[2.34002,2.34655]; recon=20,396.26 |
| 2026-06-30 NZDCAD buy | PASS (4.8bp) | PASS (0.0bp) | PASS (0.03%) | M5@+1min; range=[0.80231,0.80497]; recon=9,781.81 |
| 2026-06-30 NZDCHF buy | PASS (1.3bp) | PASS (0.0bp) | PASS (0.01%) | M5@+1min; range=[0.45593,0.45758]; recon=9,269.79 |
| 2026-06-30 NZDJPY buy | PASS (9.2bp) | PASS (0.0bp) | PASS (0.07%) | M5@+1min; range=[91.40700,91.76200]; recon=12,463.63 |
| 2026-06-30 NZDUSD buy | PASS (2.5bp) | PASS (0.0bp) | PASS (0.00%) | M5@+1min; range=[0.56416,0.56585]; recon=3,420.00 |
| 2026-07-02 EURGBP sell | PASS (0.8bp) | PASS (0.0bp) | PASS (0.05%) | M5@+1min; range=[0.85643,0.86232]; recon=35,526.58 |
| 2026-07-02 GBPAUD buy | PASS (0.8bp) | PASS (0.0bp) | PASS (0.06%) | M5@+1min; range=[1.91517,1.92866]; recon=46,928.16 |
| 2026-07-02 GBPCAD buy | PASS (2.1bp) | PASS (0.0bp) | PASS (0.02%) | M5@+1min; range=[1.87979,1.88850]; recon=24,976.09 |
| 2026-07-02 GBPCHF buy | PASS (0.7bp) | PASS (0.0bp) | PASS (0.03%) | M5@+1min; range=[1.06915,1.07487]; recon=22,461.64 |
| 2026-07-02 GBPJPY buy | PASS (5.2bp) | PASS (0.0bp) | PASS (0.01%) | M5@+1min; range=[214.52500,215.92000]; recon=14,028.78 |
| 2026-07-02 GBPNZD buy | PASS (4.3bp) | PASS (0.0bp) | PASS (0.01%) | M5@+1min; range=[2.33171,2.34655]; recon=22,661.32 |
| 2026-07-02 GBPUSD buy | PASS (4.3bp) | PASS (0.0bp) | PASS (0.00%) | M5@+1min; range=[1.32133,1.32881]; recon=18,360.00 |
| 2026-07-06 AUDJPY buy | PASS (6.4bp) | PASS (0.0bp) | PASS (0.09%) | M5@-2min; range=[111.86600,112.48700]; recon=20,386.27 |
| 2026-07-06 CADJPY buy | PASS (9.6bp) | PASS (0.0bp) | PASS (0.09%) | M5@-2min; range=[113.56800,114.15300]; recon=18,573.33 |
| 2026-07-06 CHFJPY buy | PASS (4.7bp) | PASS (0.0bp) | PASS (0.09%) | M5@-2min; range=[200.51200,201.47600]; recon=22,680.18 |
| 2026-07-06 EURJPY buy | PASS (3.6bp) | PASS (0.0bp) | PASS (0.09%) | M5@-2min; range=[184.34400,185.38700]; recon=25,566.08 |
| 2026-07-06 GBPJPY buy | PASS (6.7bp) | PASS (0.0bp) | PASS (0.09%) | M5@-2min; range=[215.30400,216.49300]; recon=36,406.69 |
| 2026-07-06 NZDJPY buy | PASS (0.3bp) | PASS (0.0bp) | PASS (0.09%) | M5@-2min; range=[91.96100,92.32400]; recon=7,954.71 |
| 2026-07-06 USDJPY buy | PASS (8.8bp) | PASS (0.0bp) | PASS (0.09%) | M5@-2min; range=[161.24900,162.27700]; recon=30,856.89 |

## Por dia

| dia | moeda | dir | pernas | soma | total_print | bate? | perdedoras |
|---|---|---|---|---|---|---|---|
| 2026-06-19 | NZD | BAIXA | 7 | 94,908.40 | 94,908.40 | PASS | 0 |
| 2026-06-22 | GBP | ALTA | 7 | 142,876.42 | 142,876.42 | PASS | 0 |
| 2026-06-23 | AUD | BAIXA | 7 | 136,747.31 | 136,747.31 | PASS | 0 |
| 2026-06-24 | JPY | ALTA | 7 | 84,180.45 | 84,180.45 | PASS | 1 |
| 2026-06-25 | EUR | BAIXA | 7 | 31,440.39 | 31,440.39 | PASS | 0 |
| 2026-06-29 | JPY | BAIXA | 7 | 63,388.85 | 63,388.85 | PASS | 0 |
| 2026-06-30 | NZD | ALTA | 7 | 80,214.46 | 80,214.46 | PASS | 0 |
| 2026-07-02 | GBP | ALTA | 7 | 185,002.16 | 184,036.10 | FAIL | 0 |
| 2026-07-06 | JPY | BAIXA | 7 | 162,281.76 | 162,281.76 | PASS | 0 |

## Cobertura (dias úteis do intervalo)

| dia útil | print? |
|---|---|
| 2026-06-19 | sim |
| 2026-06-22 | sim |
| 2026-06-23 | sim |
| 2026-06-24 | sim |
| 2026-06-25 | sim |
| 2026-06-26 | **NÃO** |
| 2026-06-29 | sim |
| 2026-06-30 | sim |
| 2026-07-01 | **NÃO** |
| 2026-07-02 | sim |
| 2026-07-03 | **NÃO** |
| 2026-07-06 | sim |

## Continuidade entre prints (descritivo)

| símbolo | de | para | gap (bp) |
|---|---|---|---|
| GBPNZD | 2026-06-19 | 2026-06-22 | -2.6 |
| GBPAUD | 2026-06-22 | 2026-06-23 | +23.0 |
| AUDJPY | 2026-06-23 | 2026-06-24 | -46.9 |
| EURJPY | 2026-06-24 | 2026-06-25 | +15.4 |
| EURJPY | 2026-06-25 | 2026-06-29 | +33.1 |
| NZDJPY | 2026-06-29 | 2026-06-30 | +1.5 |
| GBPNZD | 2026-06-30 | 2026-07-02 | -19.7 |
| GBPJPY | 2026-07-02 | 2026-07-06 | -14.1 |

## Veredito

Preços consistentes com o mercado real = prints AUTÊNTICOS quanto a preços. Isso não diferencia conta real de demo e não corrige o viés de seleção dos dias publicados; a taxa de acerto real segue sendo medida exclusivamente pelo a14 (prospectivo).
