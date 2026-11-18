import pytest
import pandas as pd
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.database.db_manager import get_connection, run_query
from src.engine.capacity_engine import (
    get_dynamic_available_hours,
    get_market_demand,
    get_headcount_requirements,
    get_takt_time_analysis,
    get_control_frame_pools_analysis,
    get_unmeasured_operations_scope,
    get_shift_alternative_simulator,
    get_pareto_nva_corrected,
    get_model_workload_hours_matrix,
    get_total_monthly_workload_capacity_summary,
    run_sanity_check_suite
)

def test_db_master_populated():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM fato_medicion")
    count_med = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM fato_demanda_mercado")
    count_dem = cursor.fetchone()[0]
    conn.close()
    assert count_med > 0
    assert count_dem > 0

def test_control_frame_pools_segregation():
    df_pools = get_control_frame_pools_analysis(mercado="Consolidado", ano=2027)
    assert len(df_pools) == 2
    pool_names = df_pools['pool_name'].tolist()
    assert "CFE+Jupiter pool" in pool_names
    assert "JXN pool" in pool_names
    
    cfe_row = df_pools[df_pools['pool_name'] == "CFE+Jupiter pool"].iloc[0]
    jxn_row = df_pools[df_pools['pool_name'] == "JXN pool"].iloc[0]

    assert cfe_row['n_estaciones'] == 8
    assert jxn_row['n_estaciones'] == 4
    assert jxn_row['n_puestos'] == 8

def test_pool_takt_reference_math():
    df_pools = get_control_frame_pools_analysis(mercado="Consolidado", ano=2027, turnos=2, horas_turno=12.0, descanso_h=1.0, dias_uteis=26)
    jxn_row = df_pools[df_pools['pool_name'] == "JXN pool"].iloc[0]

    assert jxn_row['minutos_disp_pool_mes'] == 274560.0
    assert jxn_row['capacidade_mensal_unid'] >= 89.0

def test_headcount_sanity_real_greater_than_85meta():
    df_hc, tot_hh, p_real, p_85, _ = get_headcount_requirements(mercado="México", ano=2027)
    assert p_real > p_85, f"Sanity check failed: Pessoas Real ({p_real}) should be > Pessoas Meta 85% ({p_85})"
    for _, row in df_hc.iterrows():
        assert row['paso5_personas_real'] >= row['paso5_personas_meta85'] >= row['paso4_personas_100pct']

def test_headcount_changes_with_productivity_baseline():
    df_hc_real, _, _, _, _ = get_headcount_requirements(mercado="Consolidado", ano=2027, eficiencia_modo="Real")
    df_hc_85, _, _, _, _ = get_headcount_requirements(mercado="Consolidado", ano=2027, eficiencia_modo="85%")
    
    row_real = df_hc_real.iloc[0]
    row_85 = df_hc_85.iloc[0]
    
    assert row_real['active_personas_requeridas'] == row_real['paso5_personas_real']
    assert row_85['active_personas_requeridas'] == row_85['paso5_personas_meta85']
    assert row_real['active_personas_requeridas'] > row_85['active_personas_requeridas']

def test_model_complexity_matrix_export_mapped_to_cfe():
    df_mat = get_model_workload_hours_matrix()
    assert not df_mat.empty
    models = df_mat['modelo'].tolist()
    assert "Export Models (3AP1/3AP2)" in models
    
    cfe_row = df_mat[df_mat['modelo'] == "3AP1-FG"].iloc[0]
    export_row = df_mat[df_mat['modelo'] == "Export Models (3AP1/3AP2)"].iloc[0]
    
    assert cfe_row['hh_total_unid'] == export_row['hh_total_unid'] == 44.27
    assert cfe_row['sub_ensambles_h'] == export_row['sub_ensambles_h'] == 0.47
    assert cfe_row['control_frame_h'] == export_row['control_frame_h'] == 21.43

def test_total_monthly_workload_capacity_summary():
    df_sum = get_total_monthly_workload_capacity_summary(mercado="Consolidado", ano=2027, eficiencia_modo="Real")
    assert not df_sum.empty
    assert 'hh_mensal_ajustada' in df_sum.columns
    assert 'capacidade_disponivel_h' in df_sum.columns

def test_sap_vs_va_comparison_matrix_filtering():
    from src.engine.capacity_engine import get_sap_vs_va_comparison_matrix
    df_all = get_sap_vs_va_comparison_matrix(mercado="Todos", modelo="Todos")
    assert not df_all.empty
    assert 'std_horas_sap' in df_all.columns
    assert 'real_horas_sap' in df_all.columns
    assert 'va_horas_medido' in df_all.columns

    df_dt = get_sap_vs_va_comparison_matrix(mercado="Todos", modelo="DT-145")
    assert not df_dt.empty
    assert (df_dt['modelo'] == "DT-145").all()

def test_unmeasured_operations_scope_honesty():
    df_unmeas = get_unmeasured_operations_scope()
    assert not df_unmeas.empty
    assert len(df_unmeas) == 3
    assert df_unmeas['headcount_conhecido'].sum() == 14

def test_subassembly_and_dt245_integration():
    from src.engine.capacity_engine import get_headcount_requirements, get_takt_time_analysis, get_pareto_nva_corrected

    df_st = run_query("SELECT DISTINCT nombre_estacion FROM fato_medicion")
    assert len(df_st) == 7
    assert "Sub-Assembly Station" in df_st['nombre_estacion'].tolist()

    df_m = run_query("SELECT DISTINCT modelo_disyuntor FROM fato_medicion")
    assert "DT-245" in df_m['modelo_disyuntor'].tolist()

    df_hc, _, _, _, _ = get_headcount_requirements()
    est_names = df_hc['estacion'].tolist()
    assert "Sub-Assembly Station" in est_names
    assert "Wire Cutting Station" in est_names
    assert "Continuity Test Station" in est_names

    df_takt, _, _, _, _ = get_takt_time_analysis()
    takt_names = df_takt['nombre_estacion'].tolist()
    assert "Sub-Assembly Station" in takt_names
    assert "Wire Cutting Station" in takt_names
    assert "Continuity Test Station" in takt_names

    df_par_sub, tot_sub_nva = get_pareto_nva_corrected(estacion="Sub-Assembly Station", modo_demanda=False)
    assert tot_sub_nva > 0
    assert not df_par_sub.empty

    from src.cpm.cpm_engine import build_process_dag
    G = build_process_dag()
    assert "Sub-Assembly Station" in G.nodes

def test_sanity_check_suite_v10_all_passed():
    df_sanity = run_sanity_check_suite()
    assert not df_sanity.empty
    assert len(df_sanity) >= 6
    for _, row in df_sanity.iterrows():
        assert "PASSED" in row['Status'], f"Sanity test failed: {row['Test Case']}"

def test_shift_performance_and_hourly_timeline():
    from src.engine.capacity_engine import get_shift_performance_summary, get_shift_loss_pareto, get_hourly_24h_timeline
    
    df_shift = get_shift_performance_summary()
    assert not df_shift.empty
    assert len(df_shift) == 2
    shifts = df_shift['shift_code'].tolist()
    assert "Day" in shifts
    assert "Night" in shifts
    
    # Check that day and night both have total_man_hours > 0
    assert (df_shift['total_man_hours'] > 0).all()
    assert (df_shift['pct_va'] > 0).all()
    
    # Check shift pareto loss
    df_p_day = get_shift_loss_pareto(turno="Day")
    assert not df_p_day.empty
    assert 'loss_reason' in df_p_day.columns
    
    # Check 24-hour timeline
    df_time = get_hourly_24h_timeline()
    assert len(df_time) == 24
    assert df_time['total_hours'].sum() > 0

def test_pareto_station_filtering_consistency():
    from src.engine.capacity_engine import get_pareto_nva_corrected, get_pareto_nnva_corrected
    
    # 1. Test Static Baseline (modo_demanda=False)
    df_nva_all, tot_nva_all = get_pareto_nva_corrected(estacion="Todas", modo_demanda=False)
    df_nva_cf, tot_nva_cf = get_pareto_nva_corrected(estacion="Control Frame Station", modo_demanda=False)
    df_nva_pool, tot_nva_pool = get_pareto_nva_corrected(estacion="Control Frame — CFE+Jupiter (8 st.)", modo_demanda=False)
    
    assert tot_nva_all > 0
    assert tot_nva_cf <= tot_nva_all, f"Station NVA {tot_nva_cf} must be <= Total {tot_nva_all}"
    assert tot_nva_pool == tot_nva_cf, "Pool name normalization failed"
    
    # 2. Test Demand-Driven Baseline (modo_demanda=True)
    df_dem_all, tot_dem_all = get_pareto_nva_corrected(estacion="Todas", modo_demanda=True)
    df_dem_cf, tot_dem_cf = get_pareto_nva_corrected(estacion="Control Frame Station", modo_demanda=True)
    df_dem_wire, tot_dem_wire = get_pareto_nva_corrected(estacion="Wire Cutting Station", modo_demanda=True)
    
    assert tot_dem_all > 0
    assert tot_dem_cf < tot_dem_all, f"Control Frame demand NVA {tot_dem_cf} must be < Total {tot_dem_all}"
    assert tot_dem_wire < tot_dem_all, f"Wire Cutting demand NVA {tot_dem_wire} must be < Total {tot_dem_all}"
    
    # 3. Test NNVA Consistency
    df_nnva_all, tot_nnva_all = get_pareto_nnva_corrected(estacion="Todas", modo_demanda=False)
    df_nnva_cf, tot_nnva_cf = get_pareto_nnva_corrected(estacion="Control Frame Station", modo_demanda=False)
    assert tot_nnva_cf <= tot_nnva_all, f"Station NNVA {tot_nnva_cf} must be <= Total {tot_nnva_all}"
    
    # 4. Test Unmeasured Station returns 0 with empty df (No fake mock data)
    df_empty, tot_empty = get_pareto_nva_corrected(estacion="Unmeasured Nonexistent Station", modo_demanda=False)
    assert tot_empty == 0.0
    assert df_empty.empty
