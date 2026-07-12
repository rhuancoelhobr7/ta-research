# data/specialist/ — posts do especialista (lote 2026-06-15..2026-07-10)

Dados novos fornecidos pelo usuário em 2026-07-11 (via repositório IFM-V2),
transcritos de prints promocionais do Instagram (@bonotofx). **NÃO substituem**
o `specialist_calls.csv` da raiz, que permanece a âncora de auditoria IMUTÁVEL
(regra dura nº 4 do CLAUDE.md): estes arquivos são observações adicionais,
sem peso especial em nenhuma fase.

## Arquivos

- `especialista_posts.csv` — 13 cestas (date, currency, direction + metadados:
  horário de fechamento server, dias de holding, nº de trades, lucro do print).
- `especialista_posts_detalhado.csv` — 77 trades individuais transcritos dos
  prints (11 das 13 cestas; 2026-06-15 e 2026-07-07 sem detalhamento).

## Estado e caveats (herdados do audit F0 do IFM-V2)

1. **Cobertura incompleta**: 7 dias úteis sem post capturado no intervalo
   (06-23, 06-24, 06-26, 07-01, 07-03, 07-08, 07-09). Pendente: usuário
   confirmar se são prints faltantes ou dias sem post (`NO_POST`).
2. **Discrepância com specialist_calls.csv**: a âncora contém 2026-07-03
   NZD ALTA, mas 07-03 não tem post neste lote. Não resolvido; nenhum
   arquivo foi alterado.
3. **Sanidade**: soma dos trades do detalhado == total do print em 10/11
   cestas (diff 0.00); 2026-07-02 diverge +966.06 (provável erro de
   transcrição de um dígito) e é multi-dia (abertura não confirmada).
4. **Só horários de FECHAMENTO** constam (10:40–10:56 em 11/13); janela de
   holding ≈ Tóquio + ~1h de Londres.
5. **Proveniência fraca**: prints promocionais, 77/77 trades positivos,
   conta não verificável. Adequado para auditoria de escolha+direção+data;
   inadequado para qualquer inferência de retorno.
