import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import math
import os
import sys

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.engine.capacity_engine import (
    get_dynamic_available_hours,
    get_market_demand,
    get_market_summary_by_year,
    get_model_mapping_table,
    get_operation_mapping_table,
    get_headcount_requirements,
    get_takt_time_analysis,
    get_control_frame_pools_analysis,
    get_unmeasured_operations_scope,
    get_shift_alternative_simulator,
    get_sap_comparison_modo_a_and_b,
    get_sap_vs_va_comparison_matrix,
    get_model_complexity_index,
    get_model_workload_hours_matrix,
    get_total_monthly_workload_capacity_summary,
    get_pareto_nva_corrected,
    get_pareto_nnva_corrected,
    get_data_coverage_matrix,
    get_ai_rebalancing_suggestions,
    run_sanity_check_suite,
    get_shift_performance_summary,
    get_shift_loss_pareto,
    get_hourly_24h_timeline
)
from src.cpm.cpm_engine import (
    build_process_dag,
    calculate_cpm,
    calculate_backward_scheduling,
    get_operation_sensitivity
)

st.set_page_config(
    page_title="Factory Capacity Planning — Siemens Energy QRO (CB Line)",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Siemens Energy Premium Executive Dark/Light Palette)
st.markdown("""
    <style>
    .main-title { font-size: 24px; font-weight: bold; color: #002B49; margin-bottom: 2px; }
    .sub-title { font-size: 14px; color: #555555; margin-bottom: 15px; }
    .kpi-card { background-color: #F8F9FA; padding: 12px; border-radius: 6px; border-left: 4px solid #002B49; margin-bottom: 10px; }
    .kpi-title { font-size: 11px; font-weight: bold; color: #555555; text-transform: uppercase; }
    .kpi-value { font-size: 20px; font-weight: bold; color: #002B49; }
    .kpi-status { font-size: 11px; font-weight: bold; }
    .lastro-box { background-color: #EBF3F8; border-radius: 4px; padding: 8px; font-size: 11px; color: #1C3D5A; margin-top: 4px; }
    .concept-box { background-color: #F0F4F8; border-left: 4px solid #002B49; padding: 10px; margin-bottom: 15px; font-size: 13px; color: #002B49; }
    .action-box { background-color: #E8F5E9; border-left: 4px solid #2E7D32; padding: 10px; margin-bottom: 15px; font-size: 13px; color: #1B5E20; }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# SIDEBAR NAVIGATION & PARAMETERS
# -------------------------------------------------------------
if os.path.exists("assets/siemens_energy_logo.png"):
    st.sidebar.image("assets/siemens_energy_logo.png", use_container_width=True)
else:
    st.sidebar.markdown('## ⚡ SIEMENS ENERGY')
st.sidebar.title("Capacity Planning QRO")
st.sidebar.caption("High Voltage Circuit Breakers (CB Line)")

st.sidebar.markdown("### ⚙️ Operating Parameters")
turnos_sel = st.sidebar.slider("Number of Shifts:", min_value=1, max_value=3, value=2)
horas_turno_sel = st.sidebar.number_input("Shift Duration (Hours/Shift):", min_value=6.0, max_value=12.0, value=12.0, step=0.5)
descanso_sel = st.sidebar.number_input("Shift Break (-1h/operator):", min_value=0.0, max_value=2.0, value=1.0, step=0.5)
dias_uteis_sel = st.sidebar.slider("Working Days / Month:", min_value=1, max_value=31, value=20)
eficiencia_sel = st.sidebar.radio("Productivity Baseline:", ["Measured Reality (38.5% VA)", "Siemens Standard (85% Target)"])

st.sidebar.markdown("---")
st.sidebar.markdown("### 🏛️ Control Frame Physical Layout Model")
st.sidebar.info("• 8 Small Stations (1 op/st = 8 posts, CFE+Jupiter+Export)\n• 4 Large Stations (2 ops/st = 8 posts, JXN priority)")
flex_toggle = st.sidebar.checkbox("🔀 Flex Scenario: Allow Large Station Spillover", value=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🌍 Market & Fiscal Year Filter")
mercado_sel = st.sidebar.selectbox("Market Filter:", ["Consolidated", "CFE (Domestic)", "Jupiter", "JXN", "Export"])
ano_sel = st.sidebar.selectbox("Fiscal Year (FY):", [2027, 2028, 2029, 2030, 2031])

# Map CFE (Domestic) internally to México
mercado_query = "México" if mercado_sel == "CFE (Domestic)" else mercado_sel

st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "📍 Module Navigation:",
    [
        "1. 🏠 Executive Dashboard",
        "2. 📊 Sales Forecast & Market Demand",
        "3. 🔀 Process Topology & Flow (DAG)",
        "4. ⏱️ Available Resources & Working Hours",
        "5. ⚡ Takt Time & Line Balancing",
        "6. ⚖️ System Data Quality (SAP Internal Diagnostic)",
        "7. 🛑 Waste & NVA Pareto Analysis",
        "8. 🛠️ Necessary Non-Value-Added (NNVA) Process Analysis",
        "9. 📊 Shift & Productivity Analysis (Day vs Night)",
        "10. 📊 Data Coverage & Scope Transparency (46 HC Pool Overview)",
        "11. 🔍 Data Audit & Sanity Suite"
    ]
)

# Helper KPI Card
def render_kpi_card(title, value, status, status_color, source, reference, rule_meaning):
    color_code = "#D9534F" if status_color == "red" else ("#F0AD4E" if status_color == "yellow" else "#5CB85C")
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-status" style="color: {color_code};">Status: {status}</div>
            <div class="lastro-box">
                <b>📌 DATA SOURCE:</b> {source}<br/>
                <b>⚖️ EVALUATED REFERENCE:</b> {reference}<br/>
                <b>🎨 STATUS RULE:</b> {rule_meaning}
            </div>
        </div>
    """, unsafe_allow_html=True)

# Shared calculated data
res = get_dynamic_available_hours(turnos_sel, horas_turno_sel, descanso_sel, dias_uteis_sel)
df_takt, takt_h, takt_m, takt_ef, vol_m = get_takt_time_analysis(mercado_query, ano_sel, turnos_sel, horas_turno_sel, descanso_sel, dias_uteis_sel, flex_toggle)
ef_modo = "Real" if "Measured" in eficiencia_sel else "85%"
df_hc, tot_hh_m, pess_real, pess_85, _ = get_headcount_requirements(mercado_query, ano_sel, turnos_sel, horas_turno_sel, descanso_sel, dias_uteis_sel, ef_modo)
takt_b_m = takt_m

st.markdown("---")

# -------------------------------------------------------------
# SCREEN 1: Executive Dashboard
# -------------------------------------------------------------
if menu == "1. 🏠 Executive Dashboard":
    st.markdown('<div class="main-title">EXECUTIVE CAPACITY DASHBOARD — SIEMENS ENERGY QRO</div>', unsafe_allow_html=True)
    
    active_hc_req = pess_real if "Measured" in eficiencia_sel else pess_85
    headline_text = f"Sales demand + real measured times → <b>REQUIRED WORKFORCE: {active_hc_req:.1f} Operators ({'38.5% VA Measured Reality' if 'Measured' in eficiencia_sel else '85% Siemens Corporate Target'})</b>. Compared to our fixed electrical workforce pool of <b>46 Current Electrical HC</b>, man-hour capacity has a <b>4–8× surplus</b>. The delivery bottleneck is not headcount, but the <b>53% NVA waste & 12.5% NNVA process time</b>."
    st.markdown(f'<div class="concept-box">💡 <b>Executive Decision Assessment</b>: {headline_text}</div>', unsafe_allow_html=True)

    # Top Strip — 4 CEO KPI Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card(
            "Delivery Feasibility", "FEASIBLE (Station Bottleneck)", "Physical Capacity > Sales Plan", "green",
            "Chronoanalysis Video Data & Official Sales Forecast", "Station Throughput Limit", "Green: 12 physical Control Frame stations (16 work posts) cover sales plan"
        )
    with c2:
        render_kpi_card(
            "Current Electrical Workforce Pool", "46.0 Current HC", f"Demand Req: {active_hc_req:.1f} Ops (@ {eficiencia_sel})", "green",
            "Fixed Factory Headcount Reference", "46 Current Electrical Operators Pool", "Green: 46 HC pool provides 4–8× man-hour capacity surplus"
        )
    with c3:
        render_kpi_card(
            "Primary Bottleneck Station", df_takt.iloc[0]['nombre_estacion'], f"{df_takt.iloc[0]['ciclo_mins_p50']} Min/Unit", "red",
            "Stopwatch P50 Cycle Time", f"Pool Takt ({df_takt.iloc[0]['takt_bruto_min']:.1f} Min/Unit)", "Red if Station Cycle Time > Pool Takt Time"
        )
    with c4:
        render_kpi_card(
            "Productivity Baseline Mode", "38.5% VA" if "Measured" in eficiencia_sel else "85.0% Target", f"Baseline: {eficiencia_sel}", "green" if "Siemens" in eficiencia_sel else "red",
            "Sidebar Operating Parameter", "Corporate 85% Target", "Controls required headcount baseline across dashboard"
        )

    st.info(f"📌 **Productivity Baseline Impact ({eficiencia_sel})**: The selected baseline directly determines the required headcount to meet FY{ano_sel} sales plan. Under **Measured Reality (38.5% VA)**, the line requires **{pess_real:.1f} operators**. Achieving **Siemens Standard (85% Target)** through NVA waste elimination and NNVA process optimization reduces required workforce to **{pess_85:.1f} operators**, freeing **{pess_real - pess_85:.1f} Full-Time Equivalent Operators** for factory growth.")

    st.markdown("---")
    st.subheader("📊 1. Flagship Yamazumi: Station Cycle Time (VA / NNVA / NVA) vs Line Takt")
    st.caption("📐 **Calculation & Formula**: Stacked Stopwatch P50 Cycle Time = Value-Added (38.5%) + Necessary Non-Value-Added (12.5%) + NVA Waste (49.0%). Dashed line represents Required Line Takt Time (= Net Available Working Time/Month ÷ Monthly Sales Units). Time Horizon: **Unit Level**.")
    
    col_yam1, col_yam2 = st.columns([3, 1])
    with col_yam1:
        yam_components = st.multiselect(
            "🎯 Filter Yamazumi Time Components:",
            options=["Value-Added (VA)", "Necessary Non-Value-Added (NNVA)", "NVA Waste"],
            default=["Value-Added (VA)", "Necessary Non-Value-Added (NNVA)", "NVA Waste"],
            help="Select which cycle time breakdown components (VA, NNVA, NVA Waste) to display in the chart."
        )
    with col_yam2:
        yam_unit = st.radio("⏱️ Time Unit:", ["Hours (h/unit)", "Minutes (min/unit)"], index=0, horizontal=True)

    use_hours = yam_unit.startswith("Hours")
    div_factor = 60.0 if use_hours else 1.0
    unit_label = "Hours / Unit" if use_hours else "Minutes / Unit"
    unit_suffix = "h" if use_hours else "min"

    df_yam = df_takt.copy()
    df_yam['va_val'] = round((df_yam['ciclo_mins_p50'] * 0.385) / div_factor, 2 if use_hours else 1)
    df_yam['nnva_val'] = round((df_yam['ciclo_mins_p50'] * 0.125) / div_factor, 2 if use_hours else 1)
    df_yam['nva_val'] = round((df_yam['ciclo_mins_p50'] * 0.490) / div_factor, 2 if use_hours else 1)

    fig_yam = go.Figure()
    if "Value-Added (VA)" in yam_components:
        fig_yam.add_trace(go.Bar(
            x=df_yam['nombre_estacion'], 
            y=df_yam['va_val'], 
            name="1. Value-Added (VA - 38.5%)", 
            marker_color="#5CB85C", 
            text=[f"{v:.1f}{unit_suffix}" if use_hours else f"{v:.0f}" for v in df_yam['va_val']], 
            textposition="inside"
        ))
    if "Necessary Non-Value-Added (NNVA)" in yam_components:
        fig_yam.add_trace(go.Bar(
            x=df_yam['nombre_estacion'], 
            y=df_yam['nnva_val'], 
            name="2. Necessary Non-Value-Added (NNVA - 12.5%)", 
            marker_color="#F0AD4E", 
            text=[f"{v:.1f}{unit_suffix}" if use_hours else f"{v:.0f}" for v in df_yam['nnva_val']], 
            textposition="inside"
        ))
    if "NVA Waste" in yam_components:
        fig_yam.add_trace(go.Bar(
            x=df_yam['nombre_estacion'], 
            y=df_yam['nva_val'], 
            name="3. Waste / Non-Value-Added (NVA - 49.0%)", 
            marker_color="#D9534F", 
            text=[f"{v:.1f}{unit_suffix}" if use_hours else f"{v:.0f}" for v in df_yam['nva_val']], 
            textposition="inside"
        ))
    
    takt_line_val = (takt_m / 60.0) if use_hours else takt_m
    fig_yam.add_hline(
        y=takt_line_val, 
        line_dash="dash", 
        line_color="#002B49", 
        annotation_text=f"Line Takt Time ({takt_line_val:.1f} {unit_suffix})"
    )

    fig_yam.update_layout(
        barmode="stack",
        title=f"Yamazumi Workstation Cycle Breakdown (VA vs NNVA vs NVA) vs Line Takt ({unit_label})",
        xaxis_title="Work Station / Production Pool",
        yaxis_title=f"Cycle Time ({unit_label})",
        height=450,
        legend=dict(orientation="h", y=1.12, x=0.05)
    )
    st.plotly_chart(fig_yam, use_container_width=True)

    c_left, c_right = st.columns(2)
    with c_left:
        st.subheader("👥 2. Workload & Headcount Required per Workstation")
        st.caption("📐 **Calculation & Formula**: Required Operators = Total Monthly Workload Hours (Monthly Units × Unit Hours) ÷ Net Available Hours/Person/Month. Time Horizon: **Monthly View (Operators Required/Month)**.")
        fig_hc_home = go.Figure()
        active_baseline_label = "Measured Reality (38.5% VA)" if "Measured" in eficiencia_sel else "Siemens Standard (85% Target)"
        fig_hc_home.add_trace(go.Bar(
            x=df_hc['estacion'], 
            y=df_hc['active_personas_requeridas'], 
            name=f"ACTIVE SELECTION: {active_baseline_label}", 
            marker_color="#D9534F" if "Measured" in eficiencia_sel else "#5CB85C",
            text=df_hc['active_personas_requeridas'],
            textposition="outside"
        ))
        fig_hc_home.add_trace(go.Bar(
            x=df_hc['estacion'], 
            y=df_hc['paso5_personas_meta85'] if "Measured" in eficiencia_sel else df_hc['paso5_personas_real'], 
            name="Comparison Baseline: " + ("85% Target" if "Measured" in eficiencia_sel else "38.5% Measured Reality"), 
            marker_color="#A9A9A9",
            opacity=0.6
        ))
        fig_hc_home.update_layout(
            barmode="group",
            title=f"Headcount Required per Work Station — Active Baseline: {active_baseline_label}",
            xaxis_title="Work Station / Pool",
            yaxis_title="Required Operators (Headcount)",
            height=380,
            legend=dict(orientation="h", y=1.15, x=0.05)
        )
        st.plotly_chart(fig_hc_home, use_container_width=True)

    with c_right:
        st.subheader("🛑 3. Top-5 NVA Waste Pareto (Root Causes)")
        st.caption("📐 **Demand-Driven Calculation**: Total Projected NVA Hours/Month = ∑ (Monthly Sales Demand for Model y × NVA Hours/Unit for Model y). Time Horizon: **Monthly View (Demand-Driven NVA Hours/Month)**.")
        df_par_home, _ = get_pareto_nva_corrected(turnos=turnos_sel, horas_turno=horas_turno_sel, descanso_h=descanso_sel, dias_uteis=dias_uteis_sel, mercado=mercado_query, ano=ano_sel, modo_demanda=True)
        if not df_par_home.empty:
            fig_par_home = px.bar(
                df_par_home.head(5), x="motivo_reclassificado", y="horas_perdidas",
                text="rotulo_barra", title=f"Top NVA Waste Causes — Demand Forecast {ano_sel} (Monthly Hours Lost)", color_discrete_sequence=["#D9534F"],
                labels={"motivo_reclassificado": "NVA Root Cause", "horas_perdidas": "Man-Hours Lost (h/month)"}
            )
            fig_par_home.update_layout(
                height=380,
                margin=dict(b=110, t=40, l=50, r=30),
                xaxis=dict(tickangle=-20, tickfont=dict(size=11), title="NVA Root Cause"),
                yaxis_title="Man-Hours Lost (h/month)"
            )
            st.plotly_chart(fig_par_home, use_container_width=True)

    st.markdown("---")
    st.subheader("👥 Total Factory Workforce Requirement (Sum of Measured Stations) vs 46 HC Contracted Pool")
    st.caption("📐 **Total Factory Headcount Sum**: Sum of required operators across the 6 measured electrical workstations compared against the 46 fixed contracted operators pool (which includes 19 HC in unmeasured stations).")

    st.markdown("""
        <div style="background-color: #FFF8E1; border-left: 4px solid #FFA000; padding: 12px; border-radius: 4px; color: #5D4037; margin-bottom: 15px; font-size: 13px;">
            <b>⚠️ Data Scope & Coverage Honesty Note (Unmeasured Electrical Stations)</b>:<br/>
            • The calculated total headcount above covers the <b>6 measured electrical stations</b> (Control Frame, Wire Cutting, Harness Enablement, Cabinet Enablement, Door Enablement, Continuity Test).<br/>
            • <b>19 operators (41% of the 46 HC pool)</b> belong to electrical stations that have <b>NOT YET BEEN MEASURED</b> with video chronoanalysis: <code>Placas de TC's</code> (~2 HC), <code>Sub-ensambles</code> (~2 HC) and <code>Final Assembly (Ensamble Final)</code> (19 HC pool priority).<br/>
            📌 <i>As chronoanalysis video measurements are conducted for Ensamble Final and remaining sub-assemblies, their required headcount will be incorporated into this calculation.</i>
        </div>
    """, unsafe_allow_html=True)

    tot_real_sum = round(df_hc['paso5_personas_real'].sum(), 1)
    tot_85_sum = round(df_hc['paso5_personas_meta85'].sum(), 1)
    pool_fixed = 46.0

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric(
            label="Total Required (38.5% VA Measured Reality)",
            value=f"{tot_real_sum} Operators",
            delta=f"+{pool_fixed - tot_real_sum:.1f} HC Surplus available from 46 pool",
            delta_color="normal"
        )
    with col_m2:
        st.metric(
            label="Total Required (85% Target Siemens Standard)",
            value=f"{tot_85_sum} Operators",
            delta=f"+{pool_fixed - tot_85_sum:.1f} HC Surplus available from 46 pool",
            delta_color="normal"
        )
    with col_m3:
        st.metric(
            label="Fixed Factory Workforce Pool",
            value="46.0 Operators",
            help="Total contracted electrical workforce pool available in factory"
        )

    fig_tot_hc = go.Figure()
    fig_tot_hc.add_trace(go.Bar(
        x=["Total Factory Workforce Comparison"],
        y=[tot_real_sum],
        name="1. Total Required (38.5% VA Measured Reality)",
        marker_color="#D9534F",
        text=[f"{tot_real_sum} HC"],
        textposition="outside"
    ))
    fig_tot_hc.add_trace(go.Bar(
        x=["Total Factory Workforce Comparison"],
        y=[tot_85_sum],
        name="2. Total Required (85% Target Siemens Standard)",
        marker_color="#5CB85C",
        text=[f"{tot_85_sum} HC"],
        textposition="outside"
    ))
    fig_tot_hc.add_trace(go.Bar(
        x=["Total Factory Workforce Comparison"],
        y=[pool_fixed],
        name="3. Total Fixed Contracted Workforce Pool (46 HC)",
        marker_color="#002B49",
        text=["46.0 HC"],
        textposition="outside"
    ))

    fig_tot_hc.update_layout(
        barmode="group",
        title="Total Required Workforce (Sum of All Stations) vs 46 Fixed Contracted Operators Pool",
        yaxis_title="Total Operators (Headcount)",
        height=350,
        legend=dict(orientation="h", y=1.18, x=0.05)
    )
    st.plotly_chart(fig_tot_hc, use_container_width=True)

# -------------------------------------------------------------
# SCREEN 2: Sales Forecast & Market Demand
# -------------------------------------------------------------
elif menu == "2. 📊 Sales Forecast & Market Demand":
    st.markdown('<div class="main-title">2. SALES FORECAST & MARKET DEMAND (FY27–FY31)</div>', unsafe_allow_html=True)
    st.markdown('<div class="concept-box">💡 <b>Demand Foundation</b>: Official Sales Forecast Projection by market (CFE Domestic, Jupiter, JXN, Export). Export demand is routed with CFE domestic (same CFE standard). JXN demand is routed exclusively to the dedicated JXN pool.</div>', unsafe_allow_html=True)
    st.caption("📐 **Calculation & Formula**: Annual Sales Forecast Volume (Units/Year) extracted from Official Sales Forecast Projection. Monthly Demand (Units/Month) = Annual Volume ÷ 12. Time Horizon: **Annual (Units/Year) & Monthly (Units/Month)**.")

    df_mkt = get_market_summary_by_year()
    if not df_mkt.empty:
        fig_mkt = px.bar(
            df_mkt, x="ano", y="total_unidades", color="mercado",
            title="Annual Sales Volume Forecast Projection by Market",
            barmode="group", text_auto=True, color_discrete_sequence=px.colors.qualitative.Prism,
            labels={"ano": "Fiscal Year (FY)", "total_unidades": "Annual Volume (Units/Year)", "mercado": "Market Segment"}
        )
        fig_mkt.update_layout(xaxis_title="Fiscal Year (FY)", yaxis_title="Annual Sales Volume (Units/Year)")
        st.plotly_chart(fig_mkt, use_container_width=True)

    st.subheader(f"📋 Monthly Sales Demand by Circuit Breaker Model — Market Filter: {mercado_sel} ({ano_sel})")
    df_dem = get_market_demand(mercado_query, ano_sel)
    if not df_dem.empty:
        df_dem_show = df_dem[['mercado', 'modelo', 'ano', 'quantidade']].copy()
        df_dem_show = df_dem_show.rename(columns={
            'mercado': 'Market Segment',
            'modelo': 'Circuit Breaker Model',
            'ano': 'Fiscal Year (FY)',
            'quantidade': 'Monthly Demand (Units/Month)'
        })
        st.dataframe(df_dem_show, use_container_width=True)

# -------------------------------------------------------------
# SCREEN 3: Process Topology & Flow (DAG)
# -------------------------------------------------------------
elif menu == "3. 🔀 Process Topology & Flow (DAG)":
    st.markdown('<div class="main-title">3. PROCESS TOPOLOGY & DAG FLOW (SERIES / PARALLEL)</div>', unsafe_allow_html=True)
    st.markdown('<div class="concept-box">💡 <b>Topology Rules</b>:<br/>'
                '• <b>Lead Time (Clock)</b>: Parallel branches take the <b>MAXIMUM</b> branch duration (never summed).<br/>'
                '• <b>Man-Hours (Workforce)</b>: Man-hours <b>ALWAYS SUM</b> across all stations regardless of parallelism.<br/>'
                '• <b>Convergence Wait</b>: Final Assembly waits for the slowest parallel branch to finish.</div>', unsafe_allow_html=True)
    st.caption("📐 **Calculation & Formula**: Critical Path Method (CPM) Network Graph. Block Lead Time = Max Path Duration (Hours). Total Man-Hours = Sum of Work Content across all stations. Time Horizon: **Unit Cycle (Hours/Unit)**.")

    G, tmap = build_process_dag("FG-145")
    df_cpm, makespan, total_hh, crit = calculate_cpm(G)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Block Lead Time (Critical Path MAX)", f"{makespan:.1f} Hours/Unit", help="Determined by Control Frame branch duration")
    with col2:
        st.metric("Total Man-Hours Workload (Sum of All Stations)", f"{total_hh:.1f} Man-Hours/Unit", help="Total work content across all parallel branches")

    st.subheader("🕸️ Critical Path & Float Times by Work Station")
    st.dataframe(df_cpm, use_container_width=True)

# -------------------------------------------------------------
# SCREEN 4: Available Resources & Working Hours
# -------------------------------------------------------------
elif menu == "4. ⏱️ Available Resources & Working Hours":
    st.markdown('<div class="main-title">4. AVAILABLE RESOURCES & NET WORKING HOURS</div>', unsafe_allow_html=True)
    st.markdown('<div class="concept-box">💡 <b>Resource Conversion Formula</b>:<br/>'
                '<code>Net Available Hours/Person/Day = (Shift Duration × Shifts) − (1.0h Legitimate Break × Shifts)</code><br/>'
                'Legitimate break of 1.0 h per shift (30 min meal + 2×15 min coffee) is subtracted from presence time.</div>', unsafe_allow_html=True)
    st.caption("📐 **Calculation & Formula**: Monthly Availability per Operator = Net Available Hours/Day × Working Days/Month. Time Horizon: **Daily (Hours/Day) & Monthly (Hours/Person/Month)**.")

    st.success(f"**Daily Availability**: {res['formula_dia']}")
    st.info(f"**Monthly Availability**: {res['formula_periodo']}")

    df_calc = pd.DataFrame([{
        "Selected Shifts": turnos_sel,
        "Shift Duration": f"{horas_turno_sel}h",
        "Legitimate Break Deduction": f"-{descanso_sel * turnos_sel}h",
        "Working Days / Month": dias_uteis_sel,
        "Net Available Hours / Person / Day": f"{res['horas_disp_dia']}h",
        "Net Available Hours / Person / Month": f"{res['horas_disp_periodo']}h"
    }])
    st.table(df_calc)

# -------------------------------------------------------------
# SCREEN 5: Takt Time & Line Balancing
# -------------------------------------------------------------
elif menu == "5. ⚡ Takt Time & Line Balancing":
    st.markdown('<div class="main-title">5. TAKT TIME & CONTROL FRAME PHYSICAL POOLS (12 STATIONS / 16 WORK POSTS)</div>', unsafe_allow_html=True)
    st.markdown('<div class="concept-box">💡 <b>Control Frame Physical Layout & Work Post Model</b>:<br/>'
                '• <b>8 Small Stations</b>: Max 1 operator / 1 cabinet per station (8 total work posts). Dedicated to CFE Domestic + Jupiter + Export.<br/>'
                '• <b>4 Large Stations</b>: Physically larger stations fitting <b>2 operators / 2 cabinets simultaneously</b> per station (8 total work posts). Accommodates all cabinets (JXN priority due to physical size requirement).<br/>'
                '📌 <i>Total physical layout: 12 physical work stations providing 16 simultaneous parallel work posts.</i></div>', unsafe_allow_html=True)
    st.caption("📐 **Calculation & Formula**: Takt Time (Min/Unit) = Available Pool Net Minutes/Month ÷ Monthly Sales Units. Gap = Station P50 Cycle Time − Takt Time. Time Horizon: **Unit Cycle Level (Minutes/Unit)**.")

    st.markdown("### 📊 Real Cycle Time vs Pool Takt Time")
    fig_takt = px.bar(
        df_takt, x="nombre_estacion", y="ciclo_mins_p50", color="is_gargalo_temporal",
        title=f"Station P50 Cycle Time vs Pool Takt Time ({mercado_sel} - {ano_sel})",
        labels={"ciclo_mins_p50": "P50 Cycle Time (Minutes / Unit)", "is_gargalo_temporal": "Exceeds Pool Takt?", "nombre_estacion": "Work Station / Pool"},
        color_discrete_map={True: "#D9534F", False: "#002B49"}, text_auto=True
    )
    fig_takt.update_layout(xaxis_title="Work Station / Pool", yaxis_title="Cycle Time (Minutes / Unit)")
    st.plotly_chart(fig_takt, use_container_width=True)

    st.markdown("### 🚨 Parallel Work Posts Required to Meet Takt")
    st.dataframe(
        df_takt[['codigo_operacion', 'nombre_estacion', 'ciclo_mins_p50', 'takt_bruto_min', 'gap_takt_bruto_min', 'recursos_paralelos_necessarios', 'is_gargalo_temporal']]
        .style.format({'ciclo_mins_p50': '{:.1f}', 'takt_bruto_min': '{:.1f}', 'gap_takt_bruto_min': '{:+.1f}'}),
        use_container_width=True
    )

    st.markdown("---")
    st.markdown("### 🏷️ Circuit Breaker Work Content & Complexity Breakdown (Hours / Unit)")
    st.info("📌 **Export Model Assumption**: As requested, Export models are calculated using the exact same complexity baseline as CFE domestic models (43.8 Man-Hours/Unit Total), since chronoanalysis studies for Export are pending.")
    
    df_matrix = get_model_workload_hours_matrix()
    st.dataframe(df_matrix, use_container_width=True)

    fig_matrix = px.bar(
        df_matrix, x="modelo", 
        y=["control_frame_h", "corte_crimpado_h", "arnes_accionamiento_h", "habilitado_chasis_h", "habilitado_puertas_h", "prueba_continuidad_h"],
        title="Unit Work Content (Man-Hours / Unit) per Workstation by Model & Complexity",
        labels={"value": "Work Content (Hours / Unit)", "variable": "Workstation / Process", "modelo": "Circuit Breaker Model"},
        barmode="stack"
    )
    fig_matrix.update_layout(xaxis_title="Circuit Breaker Model", yaxis_title="Work Content (Hours / Unit)")
    st.plotly_chart(fig_matrix, use_container_width=True)

    st.markdown("---")
    st.markdown(f"### 📊 Total Monthly Workload & Net Capacity Summary ({mercado_sel} - FY{ano_sel})")
    st.caption("📐 **Formula**: Monthly Workload Hours = Monthly Demand Volume × Unit Hours ÷ Efficiency Factor. Capacity Balance = Available Capacity Net Hours − Monthly Workload Hours.")
    
    df_summary = get_total_monthly_workload_capacity_summary(mercado_query, ano_sel, turnos_sel, horas_turno_sel, descanso_sel, dias_uteis_sel, ef_modo)
    st.dataframe(
        df_summary[['codigo_op', 'estacion', 'demanda_mensual_unid', 'hh_unit_p50', 'hh_mensal_100pct', 'hh_mensal_ajustada', 'capacidade_disponivel_h', 'saldo_horas_h', 'fator_carga_pct', 'status_capacidade']]
        .style.format({
            'demanda_mensual_unid': '{:.1f}',
            'hh_unit_p50': '{:.2f}',
            'hh_mensal_100pct': '{:.1f} h',
            'hh_mensal_ajustada': '{:.1f} h',
            'capacidade_disponivel_h': '{:.1f} h',
            'saldo_horas_h': '{:+.1f} h',
            'fator_carga_pct': '{:.1f}%'
        }),
        use_container_width=True
    )

    st.markdown("---")
    st.markdown("### 🎛️ Shift & Working Day Alternative Simulator")
    ciclo_ctrl = df_takt.iloc[0]['ciclo_mins_p50']
    df_sim = get_shift_alternative_simulator(vol_m, ciclo_ctrl)
    st.table(df_sim)

# -------------------------------------------------------------
# SCREEN 6: System Data Quality (SAP Internal Diagnostic)
# -------------------------------------------------------------
elif menu == "6. ⚖️ System Data Quality (SAP Internal Diagnostic)":
    st.markdown('<div class="main-title">6. SYSTEM DATA QUALITY — 3-LAYER BENCHMARK (SAP STANDARD VS REAL ENTERED VS MEASURED VA)</div>', unsafe_allow_html=True)
    st.markdown('<div class="concept-box">💡 <b>3-Layer Routing Benchmark Rule</b>:<br/>'
                '• <b>1. SAP Standard Routing (std_horas_sap)</b>: Official baseline programmed in SAP routings.<br/>'
                '• <b>2. SAP Operator Real Entered (real_horas_sap)</b>: Operator OT entries in SAP (~1.8–2.2× higher due to unmeasured NVA/idle time).<br/>'
                '• <b>3. Real Measured VA Time (va_horas_medido)</b>: Pure Value-Added (38.5%) measured in stopwatch video chronoanalysis — <b>the engineering benchmark to build correct SAP routings!</b><br/>'
                '📌 <i>Note: For models/markets where chronoanalysis VA time is not yet measured, status is transparently marked as SEM DADO - PENDENTE.</i></div>', unsafe_allow_html=True)
    st.caption("📐 **Calculation & Formula**: 3-Layer Comparison Factor = SAP Standard Hours ÷ Real Measured VA Hours. Time Horizon: **Unit Level (Hours/Unit) & Monthly Aggregate**.")

    col_sap1, col_sap2 = st.columns(2)
    with col_sap1:
        mercado_sap_sel = st.selectbox("Filter by Market Segment:", ["Todos", "CFE (Domestic)", "Jupiter", "JXN", "Export"], key="mkt_sap_filter")
    with col_sap2:
        modelo_sap_sel = st.selectbox("Filter by Circuit Breaker Model:", ["Todos", "DT-145", "FG-145", "FG-150", "FG-170", "FI-145", "FI-245", "FI-420", "FS-170"], key="mod_sap_filter")

    df_3layer = get_sap_vs_va_comparison_matrix(mercado=mercado_sap_sel, modelo=modelo_sap_sel)

    st.subheader(f"📌 3-Layer Routing Benchmark Comparison — Market: {mercado_sap_sel} | Model: {modelo_sap_sel}")
    st.dataframe(
        df_3layer[['modelo', 'mercado', 'codigo_operacion', 'nombre_operacion', 'std_horas_sap', 'real_horas_sap', 'va_horas_medido', 'status_crono', 'fator_desvio_sap', 'total_ots_sap', 'flag_confianca']]
        .style.format({
            'std_horas_sap': '{:.2f} h',
            'real_horas_sap': '{:.2f} h',
            'va_horas_medido': lambda x: f'{x:.2f} h' if pd.notnull(x) and not pd.isna(x) else 'SEM DADO - PENDENTE',
            'fator_desvio_sap': '{:.2f}x'
        }),
        use_container_width=True
    )

    st.markdown("---")
    st.subheader(f"📊 3-Way Operations Comparison: SAP Standard vs SAP Real Entered vs Measured VA Time")
    
    # Filter chart data for specific selected model or default to first available model in selection
    chart_model = modelo_sap_sel if modelo_sap_sel != "Todos" else ("DT-145" if "DT-145" in df_3layer['modelo'].values else df_3layer['modelo'].iloc[0] if not df_3layer.empty else "DT-145")
    df_chart = df_3layer[df_3layer['modelo'] == chart_model].copy()

    if not df_chart.empty:
        fig_sap_3bar = go.Figure()
        fig_sap_3bar.add_trace(go.Bar(
            x=df_chart['nombre_operacion'],
            y=df_chart['std_horas_sap'],
            name="1. SAP Standard Routing (std_horas_sap)",
            marker_color="#002B49",
            text=df_chart['std_horas_sap'],
            textposition="outside"
        ))
        fig_sap_3bar.add_trace(go.Bar(
            x=df_chart['nombre_operacion'],
            y=df_chart['real_horas_sap'],
            name="2. SAP Operator Real Entered (real_horas_sap)",
            marker_color="#5BC0DE",
            text=df_chart['real_horas_sap'],
            textposition="outside"
        ))
        fig_sap_3bar.add_trace(go.Bar(
            x=df_chart['nombre_operacion'],
            y=df_chart['va_horas_medido'],
            name="3. Real Measured VA Time (Cronoanálise Op 0010 Benchmark)",
            marker_color="#5CB85C",
            text=df_chart['va_horas_medido'].apply(lambda v: f"{v:.2f}h" if pd.notnull(v) and not pd.isna(v) else ""),
            textposition="outside"
        ))

        fig_sap_3bar.update_layout(
            barmode="group",
            title=f"Model {chart_model} — SAP Standard vs SAP Real Entered vs Real Measured VA Time (Hours/Unit)",
            xaxis_title="SAP Operation",
            yaxis_title="Hours per Unit (h/unit)",
            height=460,
            legend=dict(orientation="h", y=1.15, x=0.05)
        )
        st.plotly_chart(fig_sap_3bar, use_container_width=True)

# -------------------------------------------------------------
# SCREEN 7: Waste & NVA Pareto Analysis
# -------------------------------------------------------------
elif menu == "7. 🛑 Waste & NVA Pareto Analysis":
    st.markdown('<div class="main-title">7. WASTE & NON-VALUE-ADDED (NVA) PARETO ANALYSIS</div>', unsafe_allow_html=True)
    st.markdown('<div class="concept-box">💡 <b>Waste Pareto Rules</b>: Bars ordered strictly decreasing on left Y-axis. Cumulative % line on right secondary Y-axis (0–100%) with 80% reference line. Legitimate 1.0h break per shift excluded from NVA.</div>', unsafe_allow_html=True)
    st.caption("📐 **Calculation & Formula**: Monthly NVA Hours Lost = ∑ (Monthly Demand of Model y × NVA Hours/Unit of Model y). Equivalent Full-Time Operators = Monthly NVA Hours ÷ Net Available Hours/Person/Month. Time Horizon: **Monthly View (Man-Hours Lost/Month)**.")

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        estacion_pareto = st.selectbox("Filter by Station / Pool:", ["Todas", "Control Frame Station", "Wire Cutting Station", "Harness Enablement Station", "Cabinet Enablement Station", "Door Enablement Station", "Continuity Test Station"])
    with col_p2:
        modo_pareto = st.radio("NVA Calculation Basis:", ["Demand-Driven Forecast (Monthly Units × Model NVA/Unit)", "Static Stopwatch Video Sample Baseline (Raw Sample)"], index=0)

    use_demand = modo_pareto.startswith("Demand-Driven")
    df_pareto, tot_perdidas = get_pareto_nva_corrected(estacion_pareto, turnos_sel, horas_turno_sel, descanso_sel, dias_uteis_sel, mercado=mercado_query, ano=ano_sel, modo_demanda=use_demand)

    if use_demand:
        st.info(f"📐 **Demand-Driven NVA Waste Projection (FY{ano_sel} - {mercado_sel})**: Total Projected NVA Waste = **{tot_perdidas:.1f} Man-Hours/Month** (Calculated as ∑ [Monthly Volume Forecast for Model y × NVA Hours/Unit for Model y]). This shows the expected lost hours based on future sales forecast demand.")
    else:
        st.info(f"📐 **Static Video Sample Baseline**: Total Sample NVA Waste = **{tot_perdidas:.1f} Man-Hours** (Direct sum of recorded NVA events in the historical stopwatch video measurement database).")

    if not df_pareto.empty:
        fig_par = go.Figure()
        fig_par.add_trace(go.Bar(
            x=df_pareto['motivo_reclassificado'],
            y=df_pareto['horas_perdidas'],
            name="Man-Hours Lost (NVA)",
            marker_color="#D9534F",
            text=df_pareto['rotulo_barra'],
            textposition="outside"
        ))

        fig_par.add_trace(go.Scatter(
            x=df_pareto['motivo_reclassificado'],
            y=df_pareto['pct_acumulado'],
            name="Cumulative NVA Waste %",
            yaxis="y2",
            mode="lines+markers",
            line=dict(color="#002B49", width=3),
            marker=dict(size=7)
        ))

        fig_par.add_shape(
            type="line", x0=-0.5, x1=len(df_pareto)-0.5, y0=80, y1=80, yref="y2",
            line=dict(color="Red", width=2, dash="dash")
        )

        fig_par.update_layout(
            title=f"Pareto of NVA Waste Root Causes ({'Demand Projection ' + str(ano_sel) if use_demand else 'Sample Baseline'}) — Total: {tot_perdidas:.1f} Monthly Man-Hours Lost",
            yaxis=dict(title="Man-Hours Lost (h / Month)", side="left"),
            yaxis2=dict(title="Cumulative Pareto %", overlaying="y", side="right", range=[0, 105]),
            xaxis=dict(title="NVA Waste Root Cause", tickangle=-20, tickfont=dict(size=11)),
            height=540,
            margin=dict(b=120, t=50, l=50, r=50),
            legend=dict(x=0.7, y=1.1, orientation="h")
        )
        st.plotly_chart(fig_par, use_container_width=True)

        st.markdown("### 🧮 Waste Translation into Freed Full-Time Operators")
        top3_hh = df_pareto.head(3)['horas_perdidas'].sum()
        top3_ops = round(top3_hh / res['horas_disp_periodo'], 1)
        
        st.info(f"💡 **Eliminating the Top 3 Waste Causes** ({top3_hh:.1f} Monthly Hours Lost) **frees {top3_ops} Full-Time Equivalent Operators** ({res['horas_disp_periodo']:.0f}h/person/month available).")
        st.dataframe(df_pareto[['motivo_reclassificado', 'ocorrencias', 'horas_perdidas', 'pct_individual', 'pct_acumulado', 'pessoas_equivalentes']], use_container_width=True)
    else:
        st.info("ℹ️ No NVA waste recorded for the selected workstation / filters.")

# -------------------------------------------------------------
# SCREEN 8: Necessary Non-Value-Added (NNVA) Process Analysis
# -------------------------------------------------------------
elif menu == "8. 🛠️ Necessary Non-Value-Added (NNVA) Process Analysis":
    st.markdown('<div class="main-title">8. NECESSARY NON-VALUE-ADDED (NNVA) PROCESS ANALYSIS & OPTIMIZATION LEVERS</div>', unsafe_allow_html=True)
    st.markdown('<div class="concept-box">💡 <b>NNVA Process Engineering Focus</b>: Unlike pure NVA waste (idle time/distractions), <b>NNVA consists of necessary auxiliary work steps</b> (e.g., drawing consultation, manual data logging, quality checks, fixture setup, material kitting). Because NNVA is embedded directly inside standard operating procedures, <b>NNVA represents the primary actionable lever for Process Engineers</b> to redesign workflows, introduce digital instructions, SMED, and barcode automation.</div>', unsafe_allow_html=True)
    st.caption("📐 **Calculation & Formula**: Monthly NNVA Hours = ∑ (Monthly Demand of Model y × NNVA Hours/Unit of Model y). Equivalent Full-Time Operators = Monthly NNVA Hours ÷ Net Available Hours/Person/Month. Time Horizon: **Monthly View (Man-Hours/Month)**.")

    col_nn1, col_nn2 = st.columns(2)
    with col_nn1:
        estacion_nnva = st.selectbox("Filter by Station / Pool (NNVA):", ["Todas", "Control Frame Station", "Wire Cutting Station", "Harness Enablement Station", "Cabinet Enablement Station", "Door Enablement Station", "Continuity Test Station"])
    with col_nn2:
        modo_nnva = st.radio("NNVA Calculation Basis:", ["Demand-Driven Forecast (Monthly Units × Model NNVA/Unit)", "Static Stopwatch Video Sample Baseline (Raw Sample)"], index=0)

    use_demand_nnva = modo_nnva.startswith("Demand-Driven")
    df_nnva, tot_nnva = get_pareto_nnva_corrected(estacion_nnva, turnos_sel, horas_turno_sel, descanso_sel, dias_uteis_sel, mercado=mercado_query, ano=ano_sel, modo_demanda=use_demand_nnva)

    if use_demand_nnva:
        st.info(f"🛠️ **Demand-Driven NNVA Process Projection (FY{ano_sel} - {mercado_sel})**: Total Projected NNVA Workload = **{tot_nnva:.1f} Man-Hours/Month** (Equivalent to **{tot_nnva / res['horas_disp_periodo']:.1f} Full-Time Equivalent Operators** dedicated to auxiliary process steps).")
    else:
        st.info(f"🛠️ **Static Stopwatch Video Sample Baseline**: Total Sample NNVA Workload = **{tot_nnva:.1f} Man-Hours** (Direct sum of recorded NNVA events in video chronoanalysis).")

    if not df_nnva.empty:
        fig_nnva = go.Figure()
        fig_nnva.add_trace(go.Bar(
            x=df_nnva['motivo_reclassificado'],
            y=df_nnva['horas_perdidas'],
            name="Man-Hours (NNVA)",
            marker_color="#F0AD4E",
            text=df_nnva['rotulo_barra'],
            textposition="outside"
        ))

        fig_nnva.add_trace(go.Scatter(
            x=df_nnva['motivo_reclassificado'],
            y=df_nnva['pct_acumulado'],
            name="Cumulative %",
            yaxis="y2",
            line=dict(color="#002B49", width=3),
            mode="lines+markers"
        ))

        fig_nnva.add_shape(
            type="line", x0=-0.5, x1=len(df_nnva)-0.5, y0=80, y1=80, yref="y2",
            line=dict(color="Orange", width=2, dash="dash")
        )

        fig_nnva.update_layout(
            title=f"Pareto of NNVA Process Activities ({'Demand Projection ' + str(ano_sel) if use_demand_nnva else 'Sample Baseline'}) — Total: {tot_nnva:.1f} Monthly Man-Hours",
            yaxis=dict(title="Man-Hours (h / Month)", side="left"),
            yaxis2=dict(title="Cumulative NNVA Pareto %", overlaying="y", side="right", range=[0, 105]),
            xaxis=dict(title="NNVA Process Activity", tickangle=-20, tickfont=dict(size=11)),
            height=540,
            margin=dict(b=120, t=50, l=50, r=50),
            legend=dict(x=0.7, y=1.1, orientation="h")
        )
        st.plotly_chart(fig_nnva, use_container_width=True)

        st.markdown("### 🧮 NNVA Activity Breakdown & Operator Workload Translation")
        df_nnva_show = df_nnva.rename(columns={
            'motivo_reclassificado': 'NNVA Process Activity',
            'ocorrencias': 'Stopwatch Sample Count',
            'horas_perdidas': 'Monthly Workload (h/month)',
            'pct_individual': 'Share of Total NNVA (%)',
            'pct_acumulado': 'Cumulative Share (%)',
            'pessoas_equivalentes': 'Equivalent Full-Time Operators (FTE)'
        })
        st.dataframe(df_nnva_show[['NNVA Process Activity', 'Stopwatch Sample Count', 'Monthly Workload (h/month)', 'Share of Total NNVA (%)', 'Cumulative Share (%)', 'Equivalent Full-Time Operators (FTE)']], use_container_width=True)

        st.markdown("### 🚀 Process Engineering Optimization Levers (Action Plan)")
        dwg_hh = df_nnva[df_nnva['motivo_reclassificado']=='Drawing & DWG Consultation']['horas_perdidas'].sum()
        log_hh = df_nnva[df_nnva['motivo_reclassificado']=='Data Logging & Board Entry']['horas_perdidas'].sum()
        qc_hh = df_nnva[df_nnva['motivo_reclassificado']=='Quality & Visual Verification']['horas_perdidas'].sum()
        setup_hh = df_nnva[df_nnva['motivo_reclassificado']=='Tooling Setup & Fixture Prep']['horas_perdidas'].sum()
        kit_hh = df_nnva[df_nnva['motivo_reclassificado']=='Material Prep & Kitting Sorting']['horas_perdidas'].sum()

        levers_data = [
            {"NNVA Category": "Drawing & DWG Consultation", "Process Impact": "Paper drawing lookup during assembly", "Engineering Lever": "Digital 3D Assembly Tablets at Control Frame stations", "Target Reduction": "-75% time", "FTE Impact": f"Frees ~{(dwg_hh * 0.75 / res['horas_disp_periodo']):.1f} Ops"},
            {"NNVA Category": "Data Logging & Board Entry", "Process Impact": "Manual paper logging of serial numbers & test parameters", "Engineering Lever": "Barcode / RFID Auto-Scanning directly integrated to SAP", "Target Reduction": "-85% time", "FTE Impact": f"Frees ~{(log_hh * 0.85 / res['horas_disp_periodo']):.1f} Ops"},
            {"NNVA Category": "Quality & Visual Verification", "Process Impact": "Manual ruler/gauge measurement checks", "Engineering Lever": "Poka-Yoke laser fixtures & automatic vision checking", "Target Reduction": "-50% time", "FTE Impact": f"Frees ~{(qc_hh * 0.50 / res['horas_disp_periodo']):.1f} Ops"},
            {"NNVA Category": "Tooling Setup & Fixture Prep", "Process Impact": "Manual wrench adjustment of fixtures and work tables", "Engineering Lever": "SMED quick-release pneumatic clamps & standardized fixtures", "Target Reduction": "-60% time", "FTE Impact": f"Frees ~{(setup_hh * 0.60 / res['horas_disp_periodo']):.1f} Ops"},
            {"NNVA Category": "Material Prep & Kitting Sorting", "Process Impact": "Unpacking & sorting hardware components at station", "Engineering Lever": "Pre-sorted Kitting Trolleys delivered directly from warehouse", "Target Reduction": "-70% time", "FTE Impact": f"Frees ~{(kit_hh * 0.70 / res['horas_disp_periodo']):.1f} Ops"}
        ]
        st.table(pd.DataFrame(levers_data))

# -------------------------------------------------------------
# SCREEN 9: Shift & Productivity Analysis (Day vs Night - 12h)
# -------------------------------------------------------------
elif menu.startswith("9. 📊 Shift & Productivity Analysis"):
    st.markdown('<div class="main-title">9. SHIFT & PRODUCTIVITY ANALYSIS (DAY VS NIGHT - 12H SHIFTS)</div>', unsafe_allow_html=True)
    st.markdown('<div class="concept-box">💡 <b>Factory Operational Shift Breakdown</b>:<br/>'
                'Direct side-by-side comparative analysis of productivity (<b>Value-Added %</b>), process support (<b>NNVA %</b>), and waste losses (<b>NVA %</b>) between <b>Day Shift (07:00 – 19:00)</b> and <b>Night Shift (19:00 – 07:00)</b>.</div>', unsafe_allow_html=True)

    # Filters
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        stations_list = ["All", "Control Frame Station", "Wire Cutting Station", "Harness Enablement Station", "Cabinet Enablement Station", "Door Enablement Station", "Continuity Test Station"]
        sel_station = st.selectbox("Filter by Workstation:", stations_list, key="shift_station_filter")
    with col_f2:
        models_list = ["All", "FG-145", "DT-362", "DT-145", "FI-420", "FI-245", "FI-145", "FG-150"]
        sel_model = st.selectbox("Filter by Breaker Model:", models_list, key="shift_model_filter")

    df_shift = get_shift_performance_summary(estacion=sel_station, modelo=sel_model)
    
    if not df_shift.empty:
        col_day, col_night = st.columns(2)
        
        day_row = df_shift[df_shift['shift_code'] == 'Day']
        night_row = df_shift[df_shift['shift_code'] == 'Night']
        
        with col_day:
            st.markdown("### ☀️ Day Shift (07:00 – 19:00)")
            if not day_row.empty:
                r_day = day_row.iloc[0]
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total Man-Hours", f"{r_day['total_man_hours']}h")
                c2.metric("Productivity (% VA)", f"{r_day['pct_va']}%")
                c3.metric("Support (% NNVA)", f"{r_day['pct_nnva']}%")
                c4.metric("Loss Rate (% NVA)", f"{r_day['pct_nva']}%")
            else:
                st.info("No data recorded for Day Shift with selected filters.")
                
        with col_night:
            st.markdown("### 🌙 Night Shift (19:00 – 07:00)")
            if not night_row.empty:
                r_night = night_row.iloc[0]
                cn1, cn2, cn3, cn4 = st.columns(4)
                cn1.metric("Total Man-Hours", f"{r_night['total_man_hours']}h")
                cn2.metric("Productivity (% VA)", f"{r_night['pct_va']}%")
                cn3.metric("Support (% NNVA)", f"{r_night['pct_nnva']}%")
                cn4.metric("Loss Rate (% NVA)", f"{r_night['pct_nva']}%")
            else:
                st.info("No data recorded for Night Shift with selected filters.")

        st.markdown("---")
        
        # Plot 1: Stacked Bar Chart comparing VA, NNVA, NVA by Shift
        st.subheader("📈 Time Composition Comparison by Shift (Man-Hours)")
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(name='Value-Added (VA)', x=df_shift['shift_name'], y=df_shift['va_hours'], marker_color='#2CA02C', text=df_shift['va_hours'], textposition='auto'))
        fig_comp.add_trace(go.Bar(name='Necessary Non-VA (NNVA)', x=df_shift['shift_name'], y=df_shift['nnva_hours'], marker_color='#FF7F0E', text=df_shift['nnva_hours'], textposition='auto'))
        fig_comp.add_trace(go.Bar(name='Waste Loss (NVA)', x=df_shift['shift_name'], y=df_shift['nva_hours'], marker_color='#D62728', text=df_shift['nva_hours'], textposition='auto'))
        fig_comp.update_layout(barmode='stack', height=400, title="Total Man-Hours Composition: VA vs NNVA vs NVA per Shift", xaxis_title="Operational Shift", yaxis_title="Man-Hours (h)")
        st.plotly_chart(fig_comp, use_container_width=True)

        st.markdown("---")
        
        # Plot 2 & 3: Loss Pareto by Shift side by side
        st.subheader("🛑 Loss Pareto Comparison: Top NVA Causes per Shift")
        cp_day, cp_night = st.columns(2)
        
        with cp_day:
            st.markdown("#### ☀️ Day Shift — Top Loss Causes")
            df_p_day = get_shift_loss_pareto(turno="Day", estacion=sel_station, modelo=sel_model)
            if not df_p_day.empty:
                fig_p_day = px.bar(df_p_day.head(7), x='loss_hours', y='loss_reason', orientation='h', text='loss_hours', color='loss_hours', color_continuous_scale='Reds', title="Day Shift Loss Distribution (Hours)")
                fig_p_day.update_layout(yaxis=dict(autorange="reversed"), height=350, showlegend=False)
                st.plotly_chart(fig_p_day, use_container_width=True)
                st.dataframe(df_p_day[['loss_reason', 'occurrences', 'loss_hours', 'pct_share']], use_container_width=True, hide_index=True)
                
        with cp_night:
            st.markdown("#### 🌙 Night Shift — Top Loss Causes")
            df_p_night = get_shift_loss_pareto(turno="Night", estacion=sel_station, modelo=sel_model)
            if not df_p_night.empty:
                fig_p_night = px.bar(df_p_night.head(7), x='loss_hours', y='loss_reason', orientation='h', text='loss_hours', color='loss_hours', color_continuous_scale='Reds', title="Night Shift Loss Distribution (Hours)")
                fig_p_night.update_layout(yaxis=dict(autorange="reversed"), height=350, showlegend=False)
                st.plotly_chart(fig_p_night, use_container_width=True)
                st.dataframe(df_p_night[['loss_reason', 'occurrences', 'loss_hours', 'pct_share']], use_container_width=True, hide_index=True)

        st.markdown("---")
        
        # Plot 4: 24-Hour Timeline Distribution
        st.subheader("⏰ 24-Hour Factory Time Composition Timeline (Hourly Breakdown)")
        st.markdown("Distribution of recorded time study activity across every hour of the day (00:00 to 23:00).")
        df_timeline = get_hourly_24h_timeline(estacion=sel_station, modelo=sel_model)
        
        if not df_timeline.empty:
            fig_time = go.Figure()
            fig_time.add_trace(go.Bar(name='Value-Added (VA)', x=df_timeline['hour_label'], y=df_timeline['va_hours'], marker_color='#2CA02C'))
            fig_time.add_trace(go.Bar(name='Necessary Non-VA (NNVA)', x=df_timeline['hour_label'], y=df_timeline['nnva_hours'], marker_color='#FF7F0E'))
            fig_time.add_trace(go.Bar(name='Waste Loss (NVA)', x=df_timeline['hour_label'], y=df_timeline['nva_hours'], marker_color='#D62728'))
            fig_time.update_layout(barmode='stack', height=420, title="Hourly Activity Composition (00:00 - 23:00)", xaxis_title="Hour of Day", yaxis_title="Man-Hours Recorded (h)")
            st.plotly_chart(fig_time, use_container_width=True)

# -------------------------------------------------------------
# SCREEN 10: Data Coverage & Scope Transparency (46 HC Pool Overview)
# -------------------------------------------------------------
elif menu.startswith("10. 📊 Data Coverage"):
    st.markdown('<div class="main-title">10. DATA COVERAGE & ELECTRICAL WORKFORCE OVERVIEW (46 HC POOL)</div>', unsafe_allow_html=True)
    st.markdown('<div class="concept-box">💡 <b>Confirmed Workforce Structure (46 HC Total Electrical Pool)</b>:<br/>'
                'The electrical area has a total fixed workforce of <b>46 operators</b> across 23 physical stations. 19 HC (41%) belong to Final Assembly and sub-assemblies which are not yet measured with stopwatch chronoanalysis.</div>', unsafe_allow_html=True)

    overview_data = [
        {"Station": "Wire Cutting", "Type": "Single", "Physical Stations": 1, "Work Posts": 1, "HC from 46 Pool": "~2", "Chrono Measured": "✅ Yes", "Delivery Calc": "Included"},
        {"Station": "Control Frame — Small", "Type": "CF Small (1 op/st)", "Physical Stations": 8, "Work Posts": 8, "HC from 46 Pool": "(Shared Pool)", "Chrono Measured": "✅ Yes", "Delivery Calc": "CFE + Jupiter + Export"},
        {"Station": "Control Frame — Large", "Type": "CF Large (2 ops/st)", "Physical Stations": 4, "Work Posts": 8, "HC from 46 Pool": "(Shared Pool)", "Chrono Measured": "✅ Yes", "Delivery Calc": "All Markets (JXN Priority)"},
        {"Station": "Harness Enablement", "Type": "Single", "Physical Stations": 1, "Work Posts": 1, "HC from 46 Pool": "~2", "Chrono Measured": "✅ Yes", "Delivery Calc": "Included"},
        {"Station": "Cabinet Enablement", "Type": "Single", "Physical Stations": 1, "Work Posts": 1, "HC from 46 Pool": "~2", "Chrono Measured": "✅ Yes", "Delivery Calc": "Included"},
        {"Station": "Door Enablement", "Type": "Single", "Physical Stations": 1, "Work Posts": 1, "HC from 46 Pool": "~2", "Chrono Measured": "✅ Yes", "Delivery Calc": "Included"},
        {"Station": "Continuity Test", "Type": "Single", "Physical Stations": 1, "Work Posts": 1, "HC from 46 Pool": "~2", "Chrono Measured": "✅ Yes", "Delivery Calc": "Included"},
        {"Station": "Placas de TC's", "Type": "Single", "Physical Stations": 1, "Work Posts": 1, "HC from 46 Pool": "~2", "Chrono Measured": "❌ No Time", "Delivery Calc": "Excluded (No Time)"},
        {"Station": "Sub ensambles", "Type": "Single", "Physical Stations": 1, "Work Posts": 1, "HC from 46 Pool": "~2", "Chrono Measured": "❌ No Time", "Delivery Calc": "Excluded (No Time)"},
        {"Station": "Final Assembly (Ensamble Final) ⚠ PRIORITY", "Type": "Multi", "Physical Stations": 8, "Work Posts": 8, "HC from 46 Pool": "19", "Chrono Measured": "❌ No Time", "Delivery Calc": "Excluded (Priority for Next Measurement)"}
    ]
    st.table(pd.DataFrame(overview_data))

    st.markdown("---")
    pivot_cov = get_data_coverage_matrix()
    if not pivot_cov.empty:
        st.subheader("📊 Chronoanalysis Coverage Matrix (Model × Operation)")
        st.dataframe(pivot_cov.style.format("{:.0f}"), use_container_width=True)

# -------------------------------------------------------------
# SCREEN 11: Data Audit & Sanity Suite
# -------------------------------------------------------------
elif menu.startswith("11. 🔍 Data Audit"):
    st.markdown('<div class="main-title">10. DATA AUDIT & SANITY TEST SUITE</div>', unsafe_allow_html=True)
    st.markdown('<div class="concept-box">💡 <b>Sanity Assertion Suite</b>: Automated logical consistency tests guaranteeing board-survivable metrics.</div>', unsafe_allow_html=True)

    st.subheader("📋 Automated Sanity Checklist Results")
    df_sanity = pd.DataFrame(run_sanity_check_suite(mercado=mercado_query, ano=ano_sel, turnos=turnos_sel, horas_turno=horas_turno_sel, descanso_h=descanso_sel, dias_uteis=dias_uteis_sel))
    st.dataframe(df_sanity, use_container_width=True)

    st.markdown("---")
    st.subheader("📌 Model Nomenclature Unification Mapping")
    st.table(get_model_mapping_table())
