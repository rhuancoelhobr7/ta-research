# A3 — Anatomia do fenômeno (dias research: treino+validação)
Definição v1 congelada: {'version': 'v1', 'frozen': True, 't0_hour': 0.0, 'window_hours': 12.0, 'breadth_min': 0.8571428571, 'z_min': 0.8, 'er_min': 0.12, 'vol_lookback': 63, 'n_days': 494, 'n_labels': 976}

## 1. Taxa-base
- Dias avaliados (research): **395**
- Dias com >=1 rótulo: **346** (87.6%)
- Média de rótulos/dia: **1.98**

| rótulos no dia | nº de dias |
|---|---|
| 0 | 49 |
| 1 | 97 |
| 2 | 102 |
| 3 | 105 |
| 4 | 42 |

## 2. Persistência dia-a-dia

| moeda | P(hoje) | P(hoje\|ontem) | lift | pares D-1,D |
|---|---|---|---|---|
| USD | 0.23 | 0.24 | 1.05 | 91 **(n<100 — amostra insuficiente)** |
| EUR | 0.26 | 0.25 | 0.94 | 105 |
| GBP | 0.26 | 0.26 | 0.98 | 104 |
| JPY | 0.30 | 0.29 | 0.95 | 118 |
| CHF | 0.28 | 0.24 | 0.85 | 109 |
| CAD | 0.18 | 0.25 | 1.41 | 71 **(n<100 — amostra insuficiente)** |
| AUD | 0.22 | 0.21 | 0.93 | 87 **(n<100 — amostra insuficiente)** |
| NZD | 0.24 | 0.23 | 0.94 | 96 **(n<100 — amostra insuficiente)** |

- **Agregado (8 moedas)**: P(hoje)=0.248; P(hoje|ontem)=**0.247** IC95% [0.216, 0.277] (bootstrap em blocos); lift=**0.99** (n=781)
- Independência implicaria lift=1. Lift>1 ⇒ o rótulo de ontem é informação — baseline crucial da Fase B.

## 3. Decomposição por sessão (dias rotulados)
- Sub-janelas: Tokyo=[T0, T0+8h], Londres=[T0+8h, T0+12h]; n=782
- Retorno orientado médio Tokyo: **22.25 bp** IC95% [20.19, 24.55]
- Retorno orientado médio Londres: **17.17 bp** IC95% [15.82, 18.59]
- Share do |movimento| em Tokyo: **56.1%**; dias em que Tokyo domina: **55.4%**

## 4. Ranking de protagonistas (top-score do dia)
n dias com rótulo = 346

| moeda | dias como protagonista | % |
|---|---|---|
| EUR | 62 | 17.9% |
| GBP | 60 | 17.3% |
| JPY | 48 | 13.9% |
| CHF | 47 | 13.6% |
| NZD | 34 | 9.8% |
| USD | 34 | 9.8% |
| AUD | 33 | 9.5% |
| CAD | 28 | 8.1% |

- Direções das protagonistas: ALTA=187, BAIXA=159

## 5. Dia-da-semana e proxy de evento

| dia | % dias com rótulo | n |
|---|---|---|
| seg | 90.0% | 80 |
| ter | 78.5% | 79 |
| qua | 88.5% | 78 |
| qui | 92.2% | 77 |
| sex | 88.9% | 81 |

- Vol realizada 1ª hora pós-T0 (z por moeda): rotulados **-0.02** IC95% [-0.10, +0.06] (n=747) vs não rotulados **+0.01** IC95% [-0.04, +0.06] (n=2301)
- Interpretação: se rotulados concentram vol pós-T0 alta, parte do fenômeno é dia-de-evento (PLAN.md §8).
