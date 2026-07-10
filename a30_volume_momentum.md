# a30 — Volume e momentum da preponderante

Deliverable da bateria a28–a32. Sinais M5 cumulativos no dia (sem lookahead):
**volume** = tick-volume normalizado somado nos 7 pares da moeda; **momentum** =
índice sintético − abertura, COM SINAL. 237 dias OOS. `results/*_a30/REPORT.md`.

## Achados

**Q11 — Volume da líder.** A líder fica no **percentil 62%** de volume das 8
moedas — pouco acima da mediana. Destaca-se modestamente, não dramaticamente.

**Q12 — Momentum da líder.** Percentil **100%** no fim do dia — a líder é, quase
por definição, quem mais subiu.

**Q13 — Timing (o ponto crucial).**
- **Momentum de preço detecta a líder aos 90 min — o MESMO tempo do css M5** — e
  mais forte depois (top-3 0.63 às 4h). Como o CSS é uma **transformação do
  preço**, olhar quem subiu mais até agora dá o mesmo sinal, mais cedo e mais
  direto. → *O CSS não agrega nada sobre o preço bruto.*
- **Volume NUNCA detecta a líder** (não bate o acaso). Motivo estrutural: volume
  é **CEGO À DIREÇÃO** — marca a moeda mais ATIVA, que é a líder OU a anti-líder
  (ambas negociam muito). Serve para "algo está acontecendo", não "quem lidera".

**Q14 — Ablação.** Adicionar volume ao detector não ajuda a escolher a líder
(direção-cego), e o momentum já iguala o CSS. **Nada novo entra.**

## Leitura
Reforça o tema dos dois programas de pesquisa: **o sinal está no PREÇO**. O CSS/
CSSM é transformação, não informação extra; o volume é atividade, não direção. O
detector precoce mais honesto e simples é o próprio momentum de preço (quem
subiu mais até agora), que aos 90 min estreita a líder para o top-3 — sem
precisar do indicador.
