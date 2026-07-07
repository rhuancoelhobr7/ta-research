# v3_usd_casocontrole — Regras duras (não negociáveis)

Estudo caso-controle pré-registrado: features engine-agnostic em T0
discriminam fora da amostra os dias em que o USD é protagonista?
O protocolo completo está no PR de abertura e resumido em `config.yaml`
(todos os parâmetros pré-registrados). Contexto do programa: ver
`../CLAUDE.md` e `../CHANGELOG.md`.

1. **Nunca usar dados com timestamp > T0 em qualquer feature.**
   `tests/test_no_leakage.py` é GATE de execução: o estudo não roda se
   ele falhar. T0 = último fechamento H1 do dia anterior (timestamps de
   FECHAMENTO; T0 = meia-noite do servidor, ~2-3h antes da abertura de
   Tóquio).
2. **A janela de confirmação só pode ser tocada UMA vez**, pelo modelo
   congelado da descoberta. `fase5_estatistica.py` se recusa a rodar se
   `resultados/RELATORIO_CONFIRMACAO.md` já existe. Qualquer segunda
   execução exige autorização humana explícita (flag
   `--autorizado-por-humano`) e é registrada como violação de protocolo
   no próprio relatório.
3. **Lista de features FECHADA** (F1–F4, definidas em `config.yaml` e
   implementadas em `src/fase3_features.py`). Ideias novas vão para
   `IDEIAS_FUTURAS.md` — nunca para este estudo.
4. **Resultados nulos são reportados como nulos**, sem suavização de
   linguagem ("quase significativo" é proibido).
5. **F4 (CSSM) nunca entra no mesmo modelo que F1–F3.** É benchmark em
   quarentena, comparação head-to-head apenas.
6. **Todos os limiares e parâmetros vêm de `config.yaml`**; nenhum
   número mágico no código.
7. **Baselines de persistência e reversão são obrigatórios** em todo
   relatório, junto com a taxa-base.
8. **Relatórios explicam em linguagem conceitual acessível**, com
   interpretação honesta — não apenas tabelas de métricas.

## Decisões de implementação documentadas ANTES dos resultados

(registradas aqui na construção do estudo, antes da primeira rodada;
ver também os comentários em `config.yaml`)

- **Direção do dia por par** = sinal de (close − open) do D1 (movimento
  do próprio dia, sem contaminação de gap).
- **Magnitude normalizada** = movimento TOTAL do dia (True Range) / p60
  dos TR dos 60 dias ANTERIORES (rolling shiftado; o dia não define o
  próprio limiar). Critério: mediana das 7 razões ≥ 1.0. A diretividade
  fica a cargo do breadth.
  *Trilha de calibração (antes de qualquer feature/modelo)*: a leitura
  literal-estrita |close−open| ≥ p60(TR) deu taxa-base 6,4% e disparou o
  gate da Fase 1; investigação mostrou breadth≥6/7 sozinho em 58,4% dos
  dias (pares do USD são correlacionados) e a magnitude dominando o
  rótulo. Leitura adotada: 26,5% — 1,5pp acima do teto esperado (12–25%),
  dentro da banda dura [8–32%]. Alternativa rejeitada: limiar sobre
  p60(|close−open|) trocaria a base do limiar pré-registrado ("range
  verdadeiro") — infiel ao texto (30,2%).
- **Orientação USD**: features por par são orientadas ao USD (log-preço
  invertido para pares xxxUSD) antes de agregar por mediana — sem isso a
  agregação cancelaria os dois lados da cotação.
- **F2 distâncias a extremos**: sobre CLOSES orientados (não highs/lows,
  que trocariam de papel na inversão), normalizadas por sd dos retornos
  diários orientados (60d).
- **F3 "protagonista de qualquer moeda"**: NÃO implementável exatamente
  com 7 pares (protagonismo de EUR exige os 7 pares do EUR). Substituído
  pelo proxy contínuo `f3_atividade_prev` (mediana das magnitudes
  normalizadas dos 7 pares em D-1) + `f3_usd_prot_prev` exato. Desvio
  registrado; versão exata exigiria os 28 pares (IDEIAS_FUTURAS.md).
- **F4 lentes**: H1 (w=18, detecção) e H4 (w=30, contexto) do v1.41 com
  gates calibrados. A lente D1 estrutural (w=64, z_win=500) é EXCLUÍDA:
  aquecimento de ~564 barras D1 ≈ 2,2 anos consumiria metade da amostra.
- **Baselines no alvo pooled**: persistência = "ontem protagonista →
  hoje protagonista"; reversão = "ontem NÃO protagonista → hoje
  protagonista". Variantes direcionais reportadas sob H2.
- **Melhor baseline** para o critério de saída = o de maior precision@k
  medida NA CONFIRMAÇÃO (escolha conservadora: a régua mais difícil).
