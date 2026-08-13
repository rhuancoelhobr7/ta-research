# a41 — O MAPA entrada × saída × sessão (EXPLORATÓRIO)

**HOLDOUT ESGOTADO — a41 é EXPLORATÓRIO. Células sobreviventes são CANDIDATAS, não achados; confirmação só via prospectivo (a39).** Métrica PRIMÁRIA: PnL líquido do CAPTURÁVEL (entrada->saída, trava do a38). Cesta (7 pares/moeda). 215 células válidas. Reality check p95 = +2.32 pips.

## Sobreviventes (exp>0, IC exclui 0, BH, reality check)

**NENHUMA célula sobrevive — o mapa é NULO. Delimita que não há ponto entrada×saída×sessão com expectativa líquida positiva robusta.**


## Menos-ruim do mapa (top-8 por expectativa líquida)

| anchor   | entrada   | saida       |   exp_net |     lo |    hi |   acc_dir |   freq |
|:---------|:----------|:------------|----------:|-------:|------:|----------:|-------:|
| tokyo    | 120       | ini_overlap |     0.377 | -0.572 | 1.29  |     0.506 |  1     |
| tokyo    | 120       | fim_overlap |     0.353 | -0.746 | 1.35  |     0.508 |  1     |
| ny       | z>=1.5    | fim_overlap |     0.265 | -0.418 | 0.944 |     0.502 |  0.673 |
| tokyo    | 60        | ini_overlap |     0.258 | -0.697 | 1.216 |     0.506 |  1     |
| tokyo    | 180       | ini_overlap |     0.242 | -0.705 | 1.148 |     0.507 |  1     |
| ny       | 90        | +4h         |     0.232 | -0.343 | 0.79  |     0.496 |  1     |
| tokyo    | 90        | ini_overlap |     0.225 | -0.755 | 1.159 |     0.502 |  1     |
| tokyo    | 90        | fim_overlap |     0.22  | -0.933 | 1.233 |     0.501 |  1     |


## A célula que ninguém testou (fim do overlap)

| anchor   | entrada   |   exp_net |     lo |    hi |   acc_dir |
|:---------|:----------|----------:|-------:|------:|----------:|
| tokyo    | 120       |     0.353 | -0.746 | 1.35  |     0.508 |
| ny       | z>=1.5    |     0.265 | -0.418 | 0.944 |     0.502 |
| tokyo    | 90        |     0.22  | -0.933 | 1.233 |     0.501 |
| tokyo    | 60        |     0.206 | -0.926 | 1.318 |     0.503 |
| londres  | 60        |     0.111 | -0.782 | 0.99  |     0.503 |
| tokyo    | 30        |    -0.033 | -1.239 | 1.108 |     0.503 |


## F2 — condições sobre a melhor célula (exploratório sobre exploratório)

_Poder reduzido; achados aqui são HIPÓTESES, não resultados. Estratifica a melhor célula (tokyo/120/ini_overlap) por quartil de volatilidade prévia do dia._

expectativa líq. por quartil de vol: {'Q1': -0.148, 'Q2': -2.131, 'Q3': 0.527, 'Q4': 3.26}

**HIPÓTESE (não resultado)**: nos dias de MAIOR volatilidade prévia (Q4 = +3.26 pips) o trade-off esperar×capturar parece melhorar, enquanto os calmos são negativos — coerente com a memória de volatilidade (a23/a32). É a única pista do a41: um CANDIDATO para o prospectivo (a39), com poder reduzido e célula escolhida post-hoc; JAMAIS um achado confirmado.



_Mapas por âncora em mapa_*.csv. Nenhuma conclusão do a41 isolado; células sobreviventes (se houver) devem ser congeladas no a39.
