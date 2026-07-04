# PROTOCOLO — condições e cenários (especificação formal, estudo v2)

Formaliza a leitura MTF do especialista para uso mecânico. O A5 (v1) usou
aproximações declaradas por falta deste documento; a partir do v2, TODA
implementação dos cenários referencia ESTA especificação. Mudanças aqui
são mudanças de metodologia: exigem PR + entrada no CHANGELOG.md.

## 1. Condições por (moeda, TF)

Calculadas sobre a saída do motor CSSM (`cssm_engine.py`) no TF, com a
lente (parâmetros) vigente e gates CALIBRADOS por `calibrate_gates`
(taxa-alvo de excedência em random walk: 5% p/ `t_gate`, 20% p/ `t_low`).

### TFs em modo completo (M30, H1, H4, D1)

| Código | Nome | Predicado (dir = sign(t)) |
|---|---|---|
| **FP** | Força Plena | estado = Madura |
| **FN** | Força Nascente | estado = Emergindo |
| **FR** | Força Reduzida | Madura E (desaceleração: `acc_z·dir < 0` OU idade > 40 barras) |
| **EX** | Exaurida | estado = Exausta |
| **N** | Neutro/Ruído | estado = Ruído |

- FR tem precedência sobre FP (FP "puro" = Madura sem os agravantes).
- `idade` = nº de barras consecutivas (incluindo a atual) em Madura.
- Aquecimento (estado −1) ⇒ condição indisponível (NaN).

### TFs em modo reduzido (W1; MN quando houver ≥ 7a de D1)

Sem z-features ⇒ FN e EX **indisponíveis por construção** (registrar nos
metadados). Com `gate` = t_gate calibrado para o w do TF:

| Código | Predicado |
|---|---|
| **FP** | `\|t\| ≥ gate` E `pers ≥ 0.55` |
| **FR** | FP E `\|t\|` em queda vs 5 barras atrás (`\|t\|_now < \|t\|_{-5}`) |
| **N** | resto |

- w_mid: W1 = 64 (semanas); MN = 24 (meses; aquecimento = 24+20 = 44 barras
  mensais ⇒ exige ~5,7 anos de D1 para cobrir 2 anos de estudo).
- Sem 7 anos de D1, MN é OMITIDO e o W1 assume o papel de macro (registrar).

## 2. Cenários (avaliados por moeda C e direção candidata d ∈ {ALTA, BAIXA})

Vocabulário: *a favor* = condição com dir = d; *contra* = dir = −d;
*ativa* = condição ∈ {FP, FN, FR}. **macro** = MN se disponível, senão W1.
`idade_D1` = nº de barras D1 consecutivas com condição ativa a favor
(mesma direção), incluindo a atual.

### Cenário A — Reversão
O macro esgotado contra abre espaço para o intraday virar a mão.
1. macro ∈ {EX, FR} **contra** (no W1, que não tem EX, aceita-se FR contra);
2. D1 **não bloqueia**: condição D1 contra ∉ {FP, FN};
3. H4 ∈ {FP, FN} **a favor** E H1 ∈ {FP, FN} **a favor**.

### Cenário B — Continuação amparada
O macro contra é aparente; o D1 já virou e sustenta há dias.
1. macro ∈ {FP, FR} **contra**;
2. D1 ∈ {FP, FN} **a favor** com `idade_D1 ≥ 3`;
3. H4 **ativa a favor**.

### Cenário C — Cascata
Alinhamento pleno de cima a baixo.
1. macro **ativa a favor** OU macro ∈ {FR, EX} **contra**;
2. D1 **ativa a favor**;
3. H4 = **FP a favor**.

### Ranking entre candidatas do dia
Cada (C, d) que satisfaz um cenário vira candidata com score =
`alin(C,d)` (nº de TFs, entre MN/W1/D1/H4/H1/M30 disponíveis, com condição
ativa a favor) + `|M_H4|` como desempate. Previsão do dia = ranking
decrescente; top-1 e hit@2 avaliados contra os rótulos congelados v1.

## 3. O que este documento NÃO cobre

Gestão de posição, stops, notícias e discricionariedade do especialista.
Aqui só entra o que é computável de barras fechadas — o objeto do estudo.
