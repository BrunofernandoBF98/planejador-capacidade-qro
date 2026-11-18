import networkx as nx
import pandas as pd
import datetime
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.database.db_manager import run_query

# DAG Precedences template for the 4 Parallel Branches (PARTE 3.2 do PROMPT MESTRE)
DEFAULT_DAG_EDGES = [
    ("KITTING", "Control Frame Station", "Série"),
    ("KITTING", "Wire Cutting Station", "Série"),
    ("KITTING", "Door Enablement Station", "Série"),
    ("KITTING", "Cabinet Enablement Station", "Série"),
    ("KITTING", "Sub-Assembly Station", "Série"),
    ("Control Frame Station", "Continuity Test Station", "Série"),
    ("Wire Cutting Station", "Harness Enablement Station", "Série"),
    ("Harness Enablement Station", "Continuity Test Station", "Série"),
    ("Continuity Test Station", "Ensamble Final", "Série"),
    ("Door Enablement Station", "Ensamble Final", "Série"),
    ("Cabinet Enablement Station", "Ensamble Final", "Série"),
    ("Sub-Assembly Station", "Ensamble Final", "Série"),
    ("Ensamble Final", "Inspeção Final (WIP)", "Série")
]

def build_process_dag(modelo_code="FG-145", custom_times=None, rework_loop_pct=0.05):
    # Fetch station-level calibrated times
    sql = "SELECT nombre_estacion, hh_unidad_p50, p50_ciclo_mins FROM fato_tempo_estacion WHERE modelo = ?"
    df_times = run_query(sql, params=(modelo_code,))

    time_map = {
        "KITTING": 0.5,
        "Control Frame Station": 21.41,
        "Wire Cutting Station": 2.50,
        "Harness Enablement Station": 3.61,
        "Cabinet Enablement Station": 4.10,
        "Door Enablement Station": 2.80,
        "Sub-Assembly Station": 0.47,
        "Continuity Test Station": 9.36 * (1.0 + rework_loop_pct), # Rework loop inflates Continuity Test
        "Ensamble Final": 4.0,
        "Inspeção Final (WIP)": 1.5
    }

    if not df_times.empty:
        for _, r in df_times.iterrows():
            st_name = str(r['nombre_estacion'])
            dur_h = float(r['hh_unidad_p50'] or 1.0)
            if st_name == "Continuity Test Station":
                dur_h *= (1.0 + rework_loop_pct)
            time_map[st_name] = dur_h

    if custom_times:
        time_map.update(custom_times)

    G = nx.DiGraph()

    for pred, succ, edge_type in DEFAULT_DAG_EDGES:
        dur_pred = time_map.get(pred, 1.0)
        dur_succ = time_map.get(succ, 1.0)
        
        if not G.has_node(pred):
            G.add_node(pred, duration=dur_pred, name=pred)
        if not G.has_node(succ):
            G.add_node(succ, duration=dur_succ, name=pred)
            
        G.add_edge(pred, succ, type=edge_type)

    return G, time_map

def calculate_cpm(G):
    es = {}
    ef = {}
    
    for node in nx.topological_sort(G):
        dur = G.nodes[node]['duration']
        preds = list(G.predecessors(node))
        if not preds:
            es[node] = 0.0
        else:
            es[node] = max(ef[p] for p in preds)
        ef[node] = es[node] + dur

    makespan = max(ef.values()) if ef else 0.0

    ls = {}
    lf = {}
    
    for node in reversed(list(nx.topological_sort(G))):
        dur = G.nodes[node]['duration']
        succs = list(G.successors(node))
        if not succs:
            lf[node] = makespan
        else:
            lf[node] = min(ls[s] for s in succs)
        ls[node] = lf[node] - dur

    slack = {}
    critical_nodes = []
    
    for node in G.nodes():
        node_slack = round(ls[node] - es[node], 4)
        slack[node] = node_slack
        if abs(node_slack) < 1e-4:
            critical_nodes.append(node)

    results = []
    for node in G.nodes():
        results.append({
            "estacion": node,
            "duracao_h": round(G.nodes[node]['duration'], 2),
            "ES": round(es[node], 2),
            "EF": round(ef[node], 2),
            "LS": round(ls[node], 2),
            "LF": round(lf[node], 2),
            "folga_h": round(slack[node], 2),
            "is_critico": node in critical_nodes
        })

    df_cpm = pd.DataFrame(results).sort_values("ES")
    
    # Calculate Total HH (sum of all stations) vs Cycle Lead Time (MAX of parallel branches)
    total_hh = sum(G.nodes[n]['duration'] for n in G.nodes())
    
    return df_cpm, makespan, total_hh, critical_nodes

def calculate_backward_scheduling(orders_df, safety_buffer_days=2.0):
    results = []
    
    for _, row in orders_df.iterrows():
        ot_id = str(row.get("ot_id", "55250001"))
        modelo = str(row.get("modelo", "FG-145"))
        rdd_str = str(row.get("rdd_date", "2027-04-15"))
        rdd_date = datetime.datetime.strptime(rdd_str, "%Y-%m-%d").date()
        planned_start_str = str(row.get("planned_start", "2027-04-05"))
        planned_start_date = datetime.datetime.strptime(planned_start_str, "%Y-%m-%d").date()
        
        G, _ = build_process_dag(modelo)
        _, makespan_hours, total_hh, _ = calculate_cpm(G)
        
        lead_time_days = round(makespan_hours / 7.0, 1)
        total_lead_time_days = lead_time_days + safety_buffer_days
        
        start_by_date = rdd_date - datetime.timedelta(days=int(total_lead_time_days))
        
        is_born_delayed = planned_start_date > start_by_date
        days_delayed = (planned_start_date - start_by_date).days if is_born_delayed else 0
        
        results.append({
            "OT_ID": ot_id,
            "Modelo": modelo,
            "RDD (Data Entrega)": rdd_str,
            "Data Largada Planejada": planned_start_str,
            "Lead Time CPM (Dias)": lead_time_days,
            "HH Total Esforço": total_hh,
            "Buffer Segurança (Dias)": safety_buffer_days,
            "Data Largada Necessária (Start-by Date)": start_by_date.strftime("%Y-%m-%d"),
            "Status Largada": "🚨 JÁ NASCE ATRASADA" if is_born_delayed else "✅ LARGADA EM DIA",
            "Dias Antecipação Necessários": days_delayed
        })
        
    return pd.DataFrame(results)

def get_operation_sensitivity(modelo="FG-145"):
    G, _ = build_process_dag(modelo)
    df_cpm, base_makespan, _, crit = calculate_cpm(G)
    
    sensitivity = []
    for _, row in df_cpm.iterrows():
        st_name = row['estacion']
        is_crit = row['is_critico']
        
        custom_times = {st_name: max(0.1, row['duracao_h'] - 2.0)}
        G_sim, _ = build_process_dag(modelo, custom_times=custom_times)
        _, sim_makespan, _, _ = calculate_cpm(G_sim)
        
        hours_recovered = base_makespan - sim_makespan
        return_per_hour = hours_recovered / 2.0
        
        sensitivity.append({
            "Estação": st_name,
            "No Caminho Crítico?": "SIM (Zero Folga)" if is_crit else "NÃO (Tem Folga)",
            "Sensibilidade (Recuperação)": f"{return_per_hour:.1f}h recuperadas / 1h investida",
            "Diagnóstico de Engenharia": "ALTO IMPACTO (Reduz Lead Time)" if is_crit else "DESPERDÍCIO (Não reduz Lead Time final)"
        })
        
    return pd.DataFrame(sensitivity)
