---
name: planejador-capacidade-qro
description: Ferramenta de Previsão de Capacidade e SCHEDULING (Planejamento Temporal) para a fábrica de disjuntores da Siemens Energy Querétaro (SGA QRO, linha CB). Automatiza a previsão de 5 anos (FY27 a FY31) por mercado (Book1.xlsx), calibrada por medições reais (BD_Estudios_Tiempo_Queretaro.xlsx), com descontos diários de descanso (1h/dia/operador), Takt vs Gargalo, Backward Scheduling (data de largada necessária / start-by date), simulação de recuperação de atrasos no caminho crítico (NetworkX CPM) e 5 Visões de Atraso (Visões A a E).
---

# PROMPT MESTRE (ADENDO v4) — Ferramenta de Previsão & SCHEDULING | Siemens Energy Querétaro (Linha CB)

## 0. REGRA SUPREMA — "NENHUM NÚMERO SEM LASTRO"

Todo indicador, KPI, cor ou status exibido DEVE responder três perguntas (visíveis ou em tooltip):
1. **DE ONDE VEM** — qual dado real o alimenta (aba/arquivo, quantas OTs/medições, data/amostra).
2. **CONTRA QUE É JULGADO** — qual a referência que torna o número "bom" ou "ruim" (Takt, meta, capacidade real, benchmark).
3. **O QUE A COR SIGNIFICA** — a regra exata do verde/amarelo/vermelho.

Se o dado NÃO existe, a aplicação exibe **"SEM DADO — não medido / não configurado no SAP"**.

## 1. AJUSTE DE BASE — HORAS DISPONÍVEIS E DESCANSO LEGÍTIMO

- **Desconto de 1h/dia/operador**: De cada turno/dia por operador, descontar **1 hora de descanso legítimo**. NÃO é NVA, NÃO é desperdício, NÃO entra no Pareto de perdas.
  - `Horas disponíveis/operador/dia = (horas_turno × turnos) − 1h_descanso`.
- **Reclassificação NVA de Ausência**: A 1ª hora de ausência/dia por operador é reclassificada como **Descanso Legítimo**. Ausência além disso permanece **NVA Real (Atacável)**.
- **Operadores por Estação**:
  - `Tempo de Ciclo (Wall Clock)` = duração da operação no relógio de parede.
  - `Hora-Homem (HH)` = ciclo × nº de operadores.
  - Curva de paralelização: exibir ganho de ciclo com 1 vs N operadores.

## 2. TAKT VS GARGALO — DIAGNÓSTICO TEMPORAL

- `Takt Time (min/un) = tempo_disponivel_periodo / demanda_periodo` (já com −1h descanso).
- `Gap ao Takt = Ciclo Real − Takt`. Se positivo → operação NÃO acompanha a demanda.
- `Gargalo Real` = operação com maior Gap positivo.
- `Ritmo de Saída Real = 1 / ciclo_do_gargalo` (unidades/hora).
- `Déficit de Ritmo = 1/Takt − 1/Ciclo` (unidades/dia não produzidas).

## 3. BACKWARD SCHEDULING (DATA DE LARGADA NECESSÁRIA)

- `Lead Time Real = Makespan CPM NetworkX` (com precedências reais, filas e buffers).
- `Data de Largada Necessária = RDD (Data de Entrega) − Lead Time Real − Buffer`.
- Se `Data de Largada < Data Atual / Planejada` → a ordem **já nasce atrasada**.
- **Sensibilidade de Recuperação**: Adiantar operação NO caminho crítico recupera a data; adiantar operação com folga NÃO recupera.

## 4. ANÁLISE DE ATRASOS — 5 VISÕES

1. **Visão A (Estado Atual)**: Ritmo real com todo NVA.
2. **Visão B (Eliminando NVA Atacável)**: Remove NVA real (mantendo descanso 1h).
3. **Visão C (+1 Operador / Turno Extra no Gargalo)**: Novo ritmo acelerado.
4. **Visão D (3º Laboratório / Capacidade Extra em FY27)**: Expansão de capacidade.
5. **Visão E (Mix Mais Complexo)**: Impacto da entrada de modelos pesados (`DT-362`, `FI-420`, `FG-145`).

## 5. MÓDULOS & RECURSOS NO STREAMLIT

- ⏱️ **Takt vs Ciclo**: Barras de ciclo vs linha de Takt por centro/mercado.
- 📅 **Gantt de Backward Scheduling**: Data de largada necessária vs planejada.
- 📈 **Curva de Atraso Acumulado**: Projeção mês a mês nas Visões A a E.
- 💧 **Waterfall de Recuperação**: Horas e dias recuperados por ação.
- 🎯 **Sensibilidade de Adiantamento**: Retorno por hora investida por operação no caminho crítico.
- 🌐 **Painel de Atrasos por Mercado**: Quantidade de disjuntores atrasados, atraso médio e máximo para o `Book1.xlsx`.
