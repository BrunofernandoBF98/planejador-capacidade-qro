import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.utils import get_column_letter

def build_capacity_prototype():
    wb = openpyxl.Workbook()
    # remove default sheet
    wb.remove(wb.active)

    # Styling Palette - Siemens Energy Theme
    font_family = "Segoe UI"
    
    title_font = Font(name=font_family, size=16, bold=True, color="002B49") # Siemens Dark Blue
    subtitle_font = Font(name=font_family, size=11, italic=True, color="555555")
    section_font = Font(name=font_family, size=13, bold=True, color="002B49")
    header_font = Font(name=font_family, size=10, bold=True, color="FFFFFF")
    bold_font = Font(name=font_family, size=10, bold=True, color="000000")
    regular_font = Font(name=font_family, size=10, color="000000")
    kpi_title_font = Font(name=font_family, size=9, bold=True, color="555555")
    kpi_num_font = Font(name=font_family, size=18, bold=True, color="002B49")

    # Fills
    header_fill = PatternFill(start_color="002B49", end_color="002B49", fill_type="solid") # Siemens Teal/Navy
    sub_header_fill = PatternFill(start_color="005B84", end_color="005B84", fill_type="solid")
    kpi_fill = PatternFill(start_color="F2F4F7", end_color="F2F4F7", fill_type="solid")
    zebra_fill = PatternFill(start_color="F9FAFB", end_color="F9FAFB", fill_type="solid")
    accent_fill = PatternFill(start_color="E6F0F5", end_color="E6F0F5", fill_type="solid")

    # Borders
    thin_gray = Side(border_style="thin", color="D9D9D9")
    thick_bottom = Side(border_style="double", color="002B49")
    border_all = Border(left=thin_gray, right=thin_gray, top=thin_gray, bottom=thin_gray)
    border_total = Border(top=thin_gray, bottom=thick_bottom, left=thin_gray, right=thin_gray)

    # Alignments
    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")
    align_header = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # List of months for FY26 (Oct 2025 - Sep 2026)
    months = ["Out/25", "Nov/25", "Dez/25", "Jan/26", "Fev/26", "Mar/26", "Abr/26", "Mai/26", "Jun/26", "Jul/26", "Ago/26", "Set/26"]
    years = ["FY26", "FY27", "FY28", "FY29", "FY30"]

    # Workcenters
    workcenters = [
        ("Op 10", "Ens. Elétrico"),
        ("Op 11", "Ens. Câmaras"),
        ("Op 15", "Ens. TC/CC"),
        ("Op 20", "Ens. Mecânico"),
        ("Op 30", "Teste Funcional (TF) - GARGALO"),
        ("Op 40", "ByPack"),
        ("Op 45", "Pintura"),
        ("Op 50", "Embalagem")
    ]

    # Product Families
    families = [
        ("Live Tank", "FG 72.5", "AIS SF6 CB Live Tank <=170kV"),
        ("Live Tank", "FG 145 SMART", "AIS SF6 CB Live Tank <=170kV"),
        ("Live Tank", "FG 170", "AIS SF6 CB Live Tank <=170kV"),
        ("Live Tank", "FG 245", "AIS SF6 CB Live Tank 245kV"),
        ("Live Tank", "FI 145 SMART", "AIS SF6 CB Live Tank <=170kV"),
        ("Live Tank", "FI 245 SMART", "AIS SF6 CB Live Tank 245kV"),
        ("Live Tank", "FI 420", "AIS SF6 CB Live Tank >245kV"),
        ("Live Tank", "FI 420 SMART", "AIS SF6 CB Live Tank >245kV"),
        ("Live Tank", "FI 420 DCB", "AIS SF6 CB Live Tank >245kV"),
        ("Live Tank", "FI 550", "AIS SF6 CB Live Tank >245kV"),
        ("Live Tank", "FI 550 PIR", "AIS SF6 CB Live Tank >245kV"),
        ("Dead Tank", "DT 72.5", "AIS SF6 CB Dead Tank <=245kV"),
        ("Dead Tank", "DT 145 SMART", "AIS SF6 CB Dead Tank <=245kV"),
        ("Dead Tank", "DT 145/245", "AIS SF6 CB Dead Tank <=245kV"),
        ("Dead Tank", "DT 145/245 FE/FI", "AIS SF6 CB Dead Tank <=245kV"),
        ("Dead Tank", "DT FI 245", "AIS SF6 CB Dead Tank <=245kV"),
        ("Dead Tank", "DT 362", "AIS SF6 CB Dead Tank >245kV"),
        ("Dead Tank", "DT 550", "AIS SF6 CB Dead Tank >245kV"),
        ("Blue", "Blue 72.5kV 40kA", "AIS Blue CB LT/DT"),
        ("Blue", "Blue 145kV 63kA", "AIS Blue CB LT/DT")
    ]

    # Sample standard cycle times (hours) per workcenter
    # Op 10, Op 11, Op 15, Op 20, Op 30 (TF), Op 40, Op 45, Op 50
    cycle_times = {
        "FG 72.5": [5.2, 4.0, 3.5, 8.0, 18.5, 4.0, 3.0, 5.85],
        "FG 145 SMART": [6.0, 4.5, 4.0, 9.5, 20.0, 4.5, 3.2, 6.0],
        "FG 170": [6.5, 5.0, 4.2, 10.0, 21.0, 4.8, 3.5, 6.2],
        "FG 245": [8.0, 6.0, 5.0, 12.0, 24.5, 5.5, 4.0, 7.5],
        "FI 145 SMART": [6.2, 4.5, 4.0, 9.8, 20.5, 4.5, 3.2, 6.0],
        "FI 245 SMART": [8.2, 6.2, 5.2, 12.5, 25.0, 5.8, 4.2, 7.8],
        "FI 420": [12.0, 9.0, 8.0, 18.0, 36.0, 8.0, 6.0, 10.0],
        "FI 420 SMART": [12.5, 9.5, 8.5, 18.5, 37.0, 8.2, 6.2, 10.5],
        "FI 420 DCB": [13.0, 10.0, 9.0, 19.0, 38.0, 8.5, 6.5, 11.0],
        "FI 550": [15.0, 11.0, 10.0, 22.0, 42.0, 10.0, 7.5, 12.5],
        "FI 550 PIR": [16.0, 12.0, 11.0, 24.0, 45.0, 10.5, 8.0, 13.5],
        "DT 72.5": [7.0, 5.5, 4.5, 11.0, 22.0, 5.0, 3.8, 6.8],
        "DT 145 SMART": [8.5, 6.5, 5.5, 13.0, 26.0, 6.0, 4.2, 8.0],
        "DT 145/245": [9.0, 7.0, 6.0, 14.0, 28.0, 6.5, 4.5, 8.5],
        "DT 145/245 FE/FI": [11.0, 8.5, 7.5, 17.0, 34.0, 7.8, 5.5, 10.2],
        "DT FI 245": [11.5, 9.0, 8.0, 18.0, 35.0, 8.0, 5.8, 10.5],
        "DT 362": [16.0, 13.0, 11.0, 25.0, 48.0, 11.0, 8.0, 14.0],
        "DT 550": [20.0, 16.0, 14.0, 32.0, 60.0, 14.0, 10.0, 18.0],
        "Blue 72.5kV 40kA": [9.5, 7.5, 6.5, 15.0, 30.0, 7.0, 4.8, 9.0],
        "Blue 145kV 63kA": [12.0, 9.5, 8.5, 19.0, 38.0, 8.5, 6.0, 11.5]
    }

    # -------------------------------------------------------------
    # ABA 0: 0_Dashboard
    # -------------------------------------------------------------
    ws0 = wb.create_sheet(title="0_Dashboard")
    ws0.views.sheetView[0].showGridLines = True

    ws0["A1"] = "SIEMENS ENERGY QUERÉTARO — PLANEJADOR DE CAPACIDADE FABRIL"
    ws0["A1"].font = title_font
    ws0["A2"] = "Protótipo Executivo - Visão de Carga, Gargalos e Previsão de 5 Anos (FY26 a FY30)"
    ws0["A2"].font = subtitle_font

    # KPI Cards
    kpis = [
        ("CARGA MÉDIA FABRIL (FY26)", "84.2%", "B4", "C5"),
        ("GARGALO ESTRUTURAL", "Teste Funcional (Op 30)", "E4", "F5"),
        ("CARGA DO GARGALO (PICO)", "98.7%", "H4", "I5"),
        ("CAPACIDADE MÁX. ANUAL", "1,240 Equipamentos", "K4", "L5")
    ]

    for title, val, start, end in kpis:
        c_start = ws0[start]
        c_start.value = title
        c_start.font = kpi_title_font
        c_start.alignment = align_center

        ws0.merge_cells(f"{start[0]}{int(start[1:])+1}:{end}")
        c_val = ws0[f"{start[0]}{int(start[1:])+1}"]
        c_val.value = val
        c_val.font = kpi_num_font
        c_val.alignment = align_center

        # Style card area
        start_col, start_row = openpyxl.utils.coordinate_to_tuple(start)
        end_col, end_row = openpyxl.utils.coordinate_to_tuple(end)
        for r in range(start_row, end_row + 1):
            for c in range(start_col, end_col + 1):
                cell = ws0.cell(row=r, column=c)
                cell.fill = kpi_fill
                cell.border = border_all

    # Summary table header
    ws0["A8"] = "Resumo Mensal de Carga por Centro de Trabalho (FY26)"
    ws0["A8"].font = section_font

    headers_dash = ["Centro de Trabalho / Operação"] + months + ["Média FY26"]
    for col_idx, h in enumerate(headers_dash, 1):
        cell = ws0.cell(row=9, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_header
        cell.border = border_all

    # Link from Motor_Carga
    for idx, (op_code, op_name) in enumerate(workcenters, 10):
        row = idx
        ws0.cell(row=row, column=1, value=f"{op_code} - {op_name}").font = bold_font
        ws0.cell(row=row, column=1).border = border_all

        for m_idx in range(1, 13):
            col_let = get_column_letter(m_idx + 2)
            cell = ws0.cell(row=row, column=m_idx + 1)
            # Referencing Motor_Carga
            cell.value = f"='4_Motor_Carga'!{col_let}{row + 5}"
            cell.number_format = "0.0%"
            cell.alignment = align_center
            cell.font = regular_font
            cell.border = border_all

        # Average column
        avg_cell = ws0.cell(row=row, column=14)
        avg_cell.value = f"=AVERAGE(B{row}:M{row})"
        avg_cell.number_format = "0.0%"
        avg_cell.alignment = align_center
        avg_cell.font = bold_font
        avg_cell.border = border_all

    # -------------------------------------------------------------
    # ABA 1: 1_Premissas_Calendario
    # -------------------------------------------------------------
    ws1 = wb.create_sheet(title="1_Premissas_Calendario")
    ws1.views.sheetView[0].showGridLines = True

    ws1["A1"] = "PREMISSAS DE CALENDÁRIO, TURNOS E HEADCOUNT (FY26 - FY30)"
    ws1["A1"].font = title_font

    # Section A: Calendar
    ws1["A3"] = "1. Dias Úteis por Mês (FY26)"
    ws1["A3"].font = section_font

    headers_cal = ["Mês"] + months + ["Total Ano"]
    for c_idx, h in enumerate(headers_cal, 1):
        cell = ws1.cell(row=4, column=c_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_header
        cell.border = border_all

    days = [21, 20, 22, 21, 19, 22, 20, 21, 22, 21, 20, 21]
    ws1.cell(row=5, column=1, value="Dias Úteis").font = bold_font
    ws1.cell(row=5, column=1).border = border_all
    for c_idx, d in enumerate(days, 2):
        cell = ws1.cell(row=5, column=c_idx, value=d)
        cell.alignment = align_center
        cell.font = regular_font
        cell.border = border_all
    tot_days = ws1.cell(row=5, column=14, value="=SUM(B5:M5)")
    tot_days.font = bold_font
    tot_days.alignment = align_center
    tot_days.border = border_all

    # Section B: Standard Shifts & Efficiency
    ws1["A7"] = "2. Parâmetros Operacionais Padrão"
    ws1["A7"].font = section_font

    params = [
        ("Horas por Turno (h)", 8.0, "0.0"),
        ("Turnos Padrão por Dia", 2, "0"),
        ("Fator de Eficiência Fabril (%)", 0.85, "0.0%")
    ]
    for idx, (p_name, p_val, p_fmt) in enumerate(params, 8):
        ws1.cell(row=idx, column=1, value=p_name).font = regular_font
        ws1.cell(row=idx, column=1).border = border_all
        val_cell = ws1.cell(row=idx, column=2, value=p_val)
        val_cell.alignment = align_center
        val_cell.number_format = p_fmt
        val_cell.font = bold_font
        val_cell.border = border_all

    # Section C: Headcount per Workcenter
    ws1["A12"] = "3. Matriz de Headcount por Centro de Trabalho (Operadores)"
    ws1["A12"].font = section_font

    headers_hc = ["Código", "Centro de Trabalho", "1T (Out-Dez)", "2T (Jan-Mar)", "3T (Abr-Jun)", "4T (Jul-Set)", "Média Ano"]
    for c_idx, h in enumerate(headers_hc, 1):
        cell = ws1.cell(row=13, column=c_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_header
        cell.border = border_all

    hc_values = [
        ("Op 10", "Ens. Elétrico", 4, 4, 4, 4),
        ("Op 11", "Ens. Câmaras", 3, 3, 4, 4),
        ("Op 15", "Ens. TC/CC", 3, 3, 3, 3),
        ("Op 20", "Ens. Mecânico", 6, 6, 7, 7),
        ("Op 30", "Teste Funcional (TF) - GARGALO", 5, 5, 5, 6),
        ("Op 40", "ByPack", 3, 3, 3, 3),
        ("Op 45", "Pintura", 2, 2, 2, 2),
        ("Op 50", "Embalagem", 4, 4, 4, 4)
    ]

    for idx, (code, name, q1, q2, q3, q4) in enumerate(hc_values, 14):
        ws1.cell(row=idx, column=1, value=code).font = bold_font
        ws1.cell(row=idx, column=1).border = border_all
        ws1.cell(row=idx, column=2, value=name).font = regular_font
        ws1.cell(row=idx, column=2).border = border_all

        for q_idx, q_val in enumerate([q1, q2, q3, q4], 3):
            c = ws1.cell(row=idx, column=q_idx, value=q_val)
            c.alignment = align_center
            c.font = regular_font
            c.border = border_all

        avg_c = ws1.cell(row=idx, column=7, value=f"=AVERAGE(C{idx}:F{idx})")
        avg_c.alignment = align_center
        avg_c.font = bold_font
        avg_c.number_format = "0.0"
        avg_c.border = border_all

    # -------------------------------------------------------------
    # ABA 2: 2_Tempos_Ciclo
    # -------------------------------------------------------------
    ws2 = wb.create_sheet(title="2_Tempos_Ciclo")
    ws2.views.sheetView[0].showGridLines = True

    ws2["A1"] = "MATRIZ DE TEMPOS DE CICLO POR FAMÍLIA E OPERAÇÃO (HORAS)"
    ws2["A1"].font = title_font
    ws2["A2"] = "Fonte da Verdade: Roteiros SAP (CA03 / PLPO / AFRU)"
    ws2["A2"].font = subtitle_font

    headers_tc = ["Categoria", "Família de Disjuntor", "Bucket Corporativo IGNITE"] + [f"{op[0]}\n{op[1]}" for op in workcenters] + ["Tempo Total (h)"]
    for c_idx, h in enumerate(headers_tc, 1):
        cell = ws2.cell(row=4, column=c_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_header
        cell.border = border_all

    for idx, (cat, fam, bucket) in enumerate(families, 5):
        ws2.cell(row=idx, column=1, value=cat).font = regular_font
        ws2.cell(row=idx, column=1).border = border_all
        ws2.cell(row=idx, column=2, value=fam).font = bold_font
        ws2.cell(row=idx, column=2).border = border_all
        ws2.cell(row=idx, column=3, value=bucket).font = regular_font
        ws2.cell(row=idx, column=3).border = border_all

        times = cycle_times.get(fam, [5.0]*8)
        for t_idx, t_val in enumerate(times, 4):
            c = ws2.cell(row=idx, column=t_idx, value=t_val)
            c.alignment = align_right
            c.number_format = "0.00"
            c.font = regular_font
            c.border = border_all

        tot_c = ws2.cell(row=idx, column=12, value=f"=SUM(D{idx}:K{idx})")
        tot_c.alignment = align_right
        tot_c.font = bold_font
        tot_c.number_format = "0.00"
        tot_c.border = border_all

    # Component Line section (Jackson)
    row_comp = 5 + len(families) + 2
    ws2.cell(row=row_comp, column=1, value="COMPONENTES (LINHA JACKSON - CÂMARAS INTERRUPTIVAS)").font = section_font

    headers_comp = ["Tipo de Câmara", "Tempo de Ciclo (h/unidade)", "Observações / Modelo Destino"]
    for c_idx, h in enumerate(headers_comp, 1):
        cell = ws2.cell(row=row_comp+1, column=c_idx, value=h)
        cell.font = header_font
        cell.fill = sub_header_fill
        cell.alignment = align_header
        cell.border = border_all

    comp_items = [
        ("Câmara 72.5kV / 40kA", 6.23, "Montagem estándar linha Jackson"),
        ("Câmara 145kV / 63kA", 9.35, "Linha de alta capacidade"),
        ("Câmara 2 Ciclos", 18.70, "Especial para alta velocidade"),
        ("Câmara DT362kV", 24.93, "Subestação extra-alta tensão"),
        ("Câmara Blue (SF6-Free)", 74.80, "Tecnologia verde sem SF6"),
        ("Câmara DT550kV", 224.40, "Máxima complexidade técnica")
    ]

    for idx, (c_name, c_time, c_obs) in enumerate(comp_items, row_comp+2):
        ws2.cell(row=idx, column=1, value=c_name).font = bold_font
        ws2.cell(row=idx, column=1).border = border_all
        t_c = ws2.cell(row=idx, column=2, value=c_time)
        t_c.alignment = align_right
        t_c.number_format = "0.00"
        t_c.font = regular_font
        t_c.border = border_all
        ws2.cell(row=idx, column=3, value=c_obs).font = regular_font
        ws2.cell(row=idx, column=3).border = border_all

    # -------------------------------------------------------------
    # ABA 3: 3_Demanda_5Y
    # -------------------------------------------------------------
    ws3 = wb.create_sheet(title="3_Demanda_5Y")
    ws3.views.sheetView[0].showGridLines = True

    ws3["A1"] = "PREVISÃO DE DEMANDA FABRIL (FY26 A FY30) — EM UNIDADES"
    ws3["A1"].font = title_font
    ws3["A2"] = "Carteira SAP + S&OP + Projeção de Mercado (México / Export / Jupiter)"
    ws3["A2"].font = subtitle_font

    ws3["A4"] = "1. Demanda Mensal FY26 (Unidades/Mês por Família)"
    ws3["A4"].font = section_font

    headers_d26 = ["Família de Disjuntor"] + months + ["Total FY26"]
    for c_idx, h in enumerate(headers_d26, 1):
        cell = ws3.cell(row=5, column=c_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_header
        cell.border = border_all

    # Sample base demand per family
    sample_demand_month = {
        "FG 72.5": 5, "FG 145 SMART": 18, "FG 170": 3, "FG 245": 4,
        "FI 145 SMART": 6, "FI 245 SMART": 4, "FI 420": 2, "FI 420 SMART": 3,
        "FI 420 DCB": 1, "FI 550": 1, "FI 550 PIR": 1, "DT 72.5": 4,
        "DT 145 SMART": 22, "DT 145/245": 8, "DT 145/245 FE/FI": 2, "DT FI 245": 3,
        "DT 362": 2, "DT 550": 1, "Blue 72.5kV 40kA": 2, "Blue 145kV 63kA": 1
    }

    for idx, (cat, fam, bucket) in enumerate(families, 6):
        ws3.cell(row=idx, column=1, value=fam).font = bold_font
        ws3.cell(row=idx, column=1).border = border_all

        base_val = sample_demand_month.get(fam, 2)
        for m_idx in range(1, 13):
            c = ws3.cell(row=idx, column=m_idx+1, value=base_val)
            c.alignment = align_right
            c.font = regular_font
            c.number_format = "#,##0"
            c.border = border_all

        tot_c = ws3.cell(row=idx, column=14, value=f"=SUM(B{idx}:M{idx})")
        tot_c.alignment = align_right
        tot_c.font = bold_font
        tot_c.number_format = "#,##0"
        tot_c.border = border_all

    row_tot26 = 6 + len(families)
    ws3.cell(row=row_tot26, column=1, value="TOTAL EQUIPAMENTOS FY26").font = bold_font
    ws3.cell(row=row_tot26, column=1).border = border_total
    for c_idx in range(2, 15):
        col_let = get_column_letter(c_idx)
        c = ws3.cell(row=row_tot26, column=c_idx, value=f"=SUM({col_let}6:{col_let}{row_tot26-1})")
        c.font = bold_font
        c.alignment = align_right
        c.number_format = "#,##0"
        c.border = border_total

    # Section 5-Year Projection (FY26 - FY30)
    row_5y = row_tot26 + 3
    ws3.cell(row=row_5y, column=1, value="2. Projeção Anual de 5 Anos (FY26 a FY30)").font = section_font

    headers_5y = ["Família de Disjuntor", "Bucket Corporativo"] + years
    for c_idx, h in enumerate(headers_5y, 1):
        cell = ws3.cell(row=row_5y+1, column=c_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_header
        cell.border = border_all

    growth_factors = [1.0, 1.08, 1.15, 1.22, 1.30]
    for idx, (cat, fam, bucket) in enumerate(families, row_5y+2):
        ws3.cell(row=idx, column=1, value=fam).font = bold_font
        ws3.cell(row=idx, column=1).border = border_all
        ws3.cell(row=idx, column=2, value=bucket).font = regular_font
        ws3.cell(row=idx, column=2).border = border_all

        ref_row_26 = idx - (row_5y + 2) + 6
        # FY26 = formula link to Total FY26 above
        c26 = ws3.cell(row=idx, column=3, value=f"=N{ref_row_26}")
        c26.alignment = align_right
        c26.font = regular_font
        c26.number_format = "#,##0"
        c26.border = border_all

        # FY27..FY30 = FY26 * growth
        for y_idx in range(1, 5):
            g = growth_factors[y_idx]
            c = ws3.cell(row=idx, column=3+y_idx, value=f"=ROUND(C{idx}*{g}, 0)")
            c.alignment = align_right
            c.font = regular_font
            c.number_format = "#,##0"
            c.border = border_all

    # -------------------------------------------------------------
    # ABA 4: 4_Motor_Carga
    # -------------------------------------------------------------
    ws4 = wb.create_sheet(title="4_Motor_Carga")
    ws4.views.sheetView[0].showGridLines = True

    ws4["A1"] = "MOTOR DE CÁLCULO DE CARGA FABRIL (%) POR CENTRO DE TRABALHO"
    ws4["A1"].font = title_font
    ws4["A2"] = "Carga % = (Horas Requeridas / Horas Disponíveis) × 100"
    ws4["A2"].font = subtitle_font

    # Section 1: Required Hours
    ws4["A4"] = "1. Horas Requeridas por Centro de Trabalho (FY26)"
    ws4["A4"].font = section_font

    headers_req = ["Código", "Centro de Trabalho"] + months + ["Total Horas"]
    for c_idx, h in enumerate(headers_req, 1):
        cell = ws4.cell(row=5, column=c_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_header
        cell.border = border_all

    for idx, (op_code, op_name) in enumerate(workcenters, 6):
        ws4.cell(row=idx, column=1, value=op_code).font = bold_font
        ws4.cell(row=idx, column=1).border = border_all
        ws4.cell(row=idx, column=2, value=op_name).font = regular_font
        ws4.cell(row=idx, column=2).border = border_all

        op_col_let = get_column_letter(idx - 6 + 4) # D, E, F... in 2_Tempos_Ciclo

        for m_idx in range(1, 13):
            m_col_let = get_column_letter(m_idx + 1) # B, C, D... in 3_Demanda_5Y
            # Formula: SUMPRODUCT(Demanda_Mensal, Tempo_Ciclo_Op)
            formula = f"=SUMPRODUCT('3_Demanda_5Y'!{m_col_let}6:{m_col_let}25, '2_Tempos_Ciclo'!{op_col_let}5:{op_col_let}24)"
            c = ws4.cell(row=idx, column=m_idx+2, value=formula)
            c.alignment = align_right
            c.font = regular_font
            c.number_format = "#,##0.0"
            c.border = border_all

        tot_c = ws4.cell(row=idx, column=15, value=f"=SUM(C{idx}:N{idx})")
        tot_c.alignment = align_right
        tot_c.font = bold_font
        tot_c.number_format = "#,##0.0"
        tot_c.border = border_all

    # Section 2: Available Hours
    row_disp = 6 + len(workcenters) + 2
    ws4.cell(row=row_disp, column=1, value="2. Horas Disponíveis por Centro de Trabalho (FY26)").font = section_font

    headers_disp = ["Código", "Centro de Trabalho"] + months + ["Total Horas"]
    for c_idx, h in enumerate(headers_disp, 1):
        cell = ws4.cell(row=row_disp+1, column=c_idx, value=h)
        cell.font = header_font
        cell.fill = sub_header_fill
        cell.alignment = align_header
        cell.border = border_all

    for idx, (op_code, op_name) in enumerate(workcenters, row_disp+2):
        ws4.cell(row=idx, column=1, value=op_code).font = bold_font
        ws4.cell(row=idx, column=1).border = border_all
        ws4.cell(row=idx, column=2, value=op_name).font = regular_font
        ws4.cell(row=idx, column=2).border = border_all

        hc_row = idx - (row_disp + 2) + 14 # row in 1_Premissas_Calendario

        for m_idx in range(1, 13):
            cal_col_let = get_column_letter(m_idx + 1)
            # Headcount column based on quarter (1T=C, 2T=D, 3T=E, 4T=F)
            q_col = "C" if m_idx <= 3 else ("D" if m_idx <= 6 else ("E" if m_idx <= 9 else "F"))
            # Horas Disponíveis = Dias_Uteis * Turnos * Horas_Turno * Headcount * Eficiência
            formula = f"='1_Premissas_Calendario'!{cal_col_let}5 * '1_Premissas_Calendario'!B9 * '1_Premissas_Calendario'!B8 * '1_Premissas_Calendario'!{q_col}{hc_row} * '1_Premissas_Calendario'!B10"
            c = ws4.cell(row=idx, column=m_idx+2, value=formula)
            c.alignment = align_right
            c.font = regular_font
            c.number_format = "#,##0.0"
            c.border = border_all

        tot_c = ws4.cell(row=idx, column=15, value=f"=SUM(C{idx}:N{idx})")
        tot_c.alignment = align_right
        tot_c.font = bold_font
        tot_c.number_format = "#,##0.0"
        tot_c.border = border_all

    # Section 3: Factory Load (%) Heatmap
    row_load = row_disp + len(workcenters) + 3
    ws4.cell(row=row_load, column=1, value="3. CARGA FABRIL (%) — HEATMAP POR CENTRO E MÊS").font = section_font

    headers_load = ["Código", "Centro de Trabalho"] + months + ["Média FY26"]
    for c_idx, h in enumerate(headers_load, 1):
        cell = ws4.cell(row=row_load+1, column=c_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_header
        cell.border = border_all

    for idx, (op_code, op_name) in enumerate(workcenters, row_load+2):
        ws4.cell(row=idx, column=1, value=op_code).font = bold_font
        ws4.cell(row=idx, column=1).border = border_all
        ws4.cell(row=idx, column=2, value=op_name).font = regular_font
        ws4.cell(row=idx, column=2).border = border_all

        req_row = idx - (row_load + 2) + 6
        disp_row = idx - (row_load + 2) + row_disp + 2

        for m_idx in range(1, 13):
            col_let = get_column_letter(m_idx + 2)
            formula = f"={col_let}{req_row}/{col_let}{disp_row}"
            c = ws4.cell(row=idx, column=m_idx+2, value=formula)
            c.alignment = align_center
            c.font = bold_font if "GARGALO" in op_name else regular_font
            c.number_format = "0.0%"
            c.border = border_all

        avg_c = ws4.cell(row=idx, column=15, value=f"=AVERAGE(C{idx}:N{idx})")
        avg_c.alignment = align_center
        avg_c.font = bold_font
        avg_c.number_format = "0.0%"
        avg_c.border = border_all

    # Add Color Scale (Green-Yellow-Red) for Heatmap C31:N38
    first_load_row = row_load + 2
    last_load_row = row_load + 1 + len(workcenters)
    color_scale = ColorScaleRule(start_type='num', start_value=0.70, start_color='63BE7B', # Green
                                 mid_type='num', mid_value=0.90, mid_color='FFEB84',   # Yellow
                                 end_type='num', end_value=1.10, end_color='F8696B')   # Red
    ws4.conditional_formatting.add(f"C{first_load_row}:N{last_load_row}", color_scale)

    # -------------------------------------------------------------
    # ABA 5: 5_Analise_Gargalos_Cenarios
    # -------------------------------------------------------------
    ws5 = wb.create_sheet(title="5_Analise_Gargalos_Cenarios")
    ws5.views.sheetView[0].showGridLines = True

    ws5["A1"] = "ANÁLISE DE GARGALOS E SIMULAÇÃO DE CENÁRIOS FABRIS"
    ws5["A1"].font = title_font
    ws5["A2"] = "Modela o Gargalo Estrutural em Teste Funcional (TF) e a Entrada do 3º Laboratório em FY27"
    ws5["A2"].font = subtitle_font

    # Section 1: Maximum Capacity calculation
    ws5["A4"] = "1. Capacidade Máxima Fabril no Gargalo (Teste Funcional - Op 30)"
    ws5["A4"].font = section_font

    headers_cap = ["Mês", "Dias Úteis", "Headcount TF", "Horas Disp. TF", "Tempo Médio Ciclo TF (h)", "Capacidade Máx. (Equip/Mês)", "Demanda Prevista", "Status Gargalo"]
    for c_idx, h in enumerate(headers_cap, 1):
        cell = ws5.cell(row=5, column=c_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_header
        cell.border = border_all

    for m_idx, m_name in enumerate(months, 1):
        row = m_idx + 5
        cal_col = get_column_letter(m_idx + 1)
        disp_col = get_column_letter(m_idx + 2)

        ws5.cell(row=row, column=1, value=m_name).font = bold_font
        ws5.cell(row=row, column=1).border = border_all

        # Days
        c_days = ws5.cell(row=row, column=2, value=f"='1_Premissas_Calendario'!{cal_col}5")
        c_days.alignment = align_center
        c_days.border = border_all

        # Headcount
        q_col = "C" if m_idx <= 3 else ("D" if m_idx <= 6 else ("E" if m_idx <= 9 else "F"))
        c_hc = ws5.cell(row=row, column=3, value=f"='1_Premissas_Calendario'!{q_col}18")
        c_hc.alignment = align_center
        c_hc.border = border_all

        # Available Hours TF (Row 22 in Motor_Carga)
        c_disp = ws5.cell(row=row, column=4, value=f"='4_Motor_Carga'!{disp_col}22")
        c_disp.alignment = align_right
        c_disp.number_format = "#,##0"
        c_disp.border = border_all

        # Average Cycle Time TF
        c_avg_t = ws5.cell(row=row, column=5, value=25.4)
        c_avg_t.alignment = align_right
        c_avg_t.number_format = "0.0"
        c_avg_t.border = border_all

        # Max Capacity units = Available Hours / Avg Cycle Time
        c_max = ws5.cell(row=row, column=6, value=f"=ROUND(D{row}/E{row}, 0)")
        c_max.alignment = align_right
        c_max.font = bold_font
        c_max.number_format = "#,##0"
        c_max.border = border_all

        # Demand total FY26 (Row 26 in Demanda_5Y)
        c_dem = ws5.cell(row=row, column=7, value=f"='3_Demanda_5Y'!{disp_col}26")
        c_dem.alignment = align_right
        c_dem.font = regular_font
        c_dem.number_format = "#,##0"
        c_dem.border = border_all

        # Status
        c_st = ws5.cell(row=row, column=8, value=f'=IF(G{row}>F{row}, "SOBRECARGA (GARGALO)", "CAPACIDADE OK")')
        c_st.alignment = align_center
        c_st.font = bold_font
        c_st.border = border_all

    # Section 2: Scenario Comparison (3rd Lab TF in FY27)
    row_scen = 6 + 12 + 2
    ws5.cell(row=row_scen, column=1, value="2. Simulação de Cenários: Impacto do 3º Laboratório de TF em FY27").font = section_font

    headers_scen = ["Cenário Operacional", "Capacidade TF (Equip/Mês)", "Capacidade Anual", "Carga Média TF", "Gargalo Aliviado?"]
    for c_idx, h in enumerate(headers_scen, 1):
        cell = ws5.cell(row=row_scen+1, column=c_idx, value=h)
        cell.font = header_font
        cell.fill = sub_header_fill
        cell.alignment = align_header
        cell.border = border_all

    scenarios = [
        ("Cenário 1: Base FY26 (2 Laboratórios de TF)", 95, 1140, "98.7%", "Não (Gargalo Ativo)"),
        ("Cenário 2: Inclusão do 3º Lab TF em Out/2026 (FY27)", 140, 1680, "67.2%", "Sim (Capacidade +47%)"),
        ("Cenário 3: 3º Lab TF + Ganhos de Lean (5% Redução Tempo)", 148, 1776, "63.5%", "Sim (Capacidade +55%)")
    ]

    for idx, (s_name, s_cap_m, s_cap_y, s_load, s_stat) in enumerate(scenarios, row_scen+2):
        ws5.cell(row=idx, column=1, value=s_name).font = bold_font
        ws5.cell(row=idx, column=1).border = border_all

        c1 = ws5.cell(row=idx, column=2, value=s_cap_m)
        c1.alignment = align_right
        c1.number_format = "#,##0"
        c1.border = border_all

        c2 = ws5.cell(row=idx, column=3, value=s_cap_y)
        c2.alignment = align_right
        c2.number_format = "#,##0"
        c2.border = border_all

        c3 = ws5.cell(row=idx, column=4, value=s_load)
        c3.alignment = align_center
        c3.font = bold_font
        c3.border = border_all

        c4 = ws5.cell(row=idx, column=5, value=s_stat)
        c4.alignment = align_center
        c4.font = bold_font
        c4.border = border_all

    # -------------------------------------------------------------
    # ABA 6: 6_Reporte_Corporativo
    # -------------------------------------------------------------
    ws6 = wb.create_sheet(title="6_Reporte_Corporativo")
    ws6.views.sheetView[0].showGridLines = True

    ws6["A1"] = "REQUIRED CAPACITY AND FACTORY LOAD — SIEMENS ENERGY CORPORATE"
    ws6["A1"].font = title_font
    ws6["A2"] = "Standard Corporate Report (Buckets AIS SF6 & AIS Blue) - FY26 to FY30"
    ws6["A2"].font = subtitle_font

    ws6["A4"] = "Factory: SGA QRO (Querétaro, Mexico) | Product Line: High Voltage Circuit Breakers"
    ws6["A4"].font = bold_font

    headers_corp = ["Corporate Product Category / Bucket"] + years
    for c_idx, h in enumerate(headers_corp, 1):
        cell = ws6.cell(row=6, column=c_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_header
        cell.border = border_all

    corp_buckets = [
        "AIS SF6 CB Live Tank <=170kV",
        "AIS SF6 CB Live Tank 245kV",
        "AIS SF6 CB Live Tank >245kV",
        "AIS SF6 CB Dead Tank <=245kV",
        "AIS SF6 CB Dead Tank >245kV",
        "AIS Blue CB LT/DT"
    ]

    # Factory Load Section
    ws6["A5"] = "1. FACTORY LOAD (REQUIRED CAPACITY IN UNITS)"
    ws6["A5"].font = section_font

    for idx, b_name in enumerate(corp_buckets, 7):
        ws6.cell(row=idx, column=1, value=b_name).font = bold_font
        ws6.cell(row=idx, column=1).border = border_all

        for y_idx in range(1, 6):
            y_col_let = get_column_letter(y_idx + 2)
            # SUMIF based on 3_Demanda_5Y
            formula = f"=SUMIF('3_Demanda_5Y'!$B$31:$B$50, A{idx}, '3_Demanda_5Y'!{y_col_let}$31:{y_col_let}$50)"
            c = ws6.cell(row=idx, column=y_idx+1, value=formula)
            c.alignment = align_right
            c.font = regular_font
            c.number_format = "#,##0"
            c.border = border_all

    row_tot_load = 7 + len(corp_buckets)
    ws6.cell(row=row_tot_load, column=1, value="TOTAL FACTORY LOAD (UNITS)").font = bold_font
    ws6.cell(row=row_tot_load, column=1).border = border_total
    for y_idx in range(1, 6):
        y_col_let = get_column_letter(y_idx + 1)
        c = ws6.cell(row=row_tot_load, column=y_idx+1, value=f"=SUM({y_col_let}7:{y_col_let}{row_tot_load-1})")
        c.font = bold_font
        c.alignment = align_right
        c.number_format = "#,##0"
        c.border = border_total

    # Maximum Capacity Section
    row_max_sec = row_tot_load + 3
    ws6.cell(row=row_max_sec, column=1, value="2. MAXIMUM FACTORY CAPACITY (UNITS)").font = section_font

    headers_max = ["Corporate Product Category / Bucket"] + years
    for c_idx, h in enumerate(headers_max, 1):
        cell = ws6.cell(row=row_max_sec+1, column=c_idx, value=h)
        cell.font = header_font
        cell.fill = sub_header_fill
        cell.alignment = align_header
        cell.border = border_all

    # Base Max capacities per bucket
    max_cap_base = [380, 120, 110, 520, 60, 50]
    for idx, b_name in enumerate(corp_buckets, row_max_sec+2):
        ws6.cell(row=idx, column=1, value=b_name).font = bold_font
        ws6.cell(row=idx, column=1).border = border_all

        base_cap = max_cap_base[idx - (row_max_sec+2)]
        for y_idx in range(1, 6):
            # FY27 onwards includes 3rd lab (+25% capacity growth)
            cap_factor = 1.0 if y_idx == 1 else 1.25
            c = ws6.cell(row=idx, column=y_idx+1, value=round(base_cap * cap_factor))
            c.alignment = align_right
            c.font = regular_font
            c.number_format = "#,##0"
            c.border = border_all

    row_tot_max = row_max_sec + 2 + len(corp_buckets)
    ws6.cell(row=row_tot_max, column=1, value="TOTAL MAXIMUM CAPACITY (UNITS)").font = bold_font
    ws6.cell(row=row_tot_max, column=1).border = border_total
    for y_idx in range(1, 6):
        y_col_let = get_column_letter(y_idx + 1)
        c = ws6.cell(row=row_tot_max, column=y_idx+1, value=f"=SUM({y_col_let}{row_max_sec+2}:{y_col_let}{row_tot_max-1})")
        c.font = bold_font
        c.alignment = align_right
        c.number_format = "#,##0"
        c.border = border_total

    # Load vs Capacity % Section
    row_util_sec = row_tot_max + 3
    ws6.cell(row=row_util_sec, column=1, value="3. CAPACITY UTILIZATION RATE (% LOAD / MAX CAPACITY)").font = section_font

    for y_idx in range(1, 6):
        y_col_let = get_column_letter(y_idx + 1)
        load_cell = f"{y_col_let}{row_tot_load}"
        max_cell = f"{y_col_let}{row_tot_max}"
        
        ws6.cell(row=row_util_sec+1, column=1, value="UTILIZAÇÃO GLOBAL DA FÁBRICA (%)").font = bold_font
        ws6.cell(row=row_util_sec+1, column=1).border = border_all
        
        c = ws6.cell(row=row_util_sec+1, column=y_idx+1, value=f"={load_cell}/{max_cell}")
        c.alignment = align_center
        c.font = bold_font
        c.number_format = "0.0%"
        c.border = border_all

    # Auto-adjust column widths across all sheets
    for sheet in wb.worksheets:
        for col in sheet.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or '')
                if cell.number_format and '%' in cell.number_format:
                    val_str += '   '
                max_len = max(max_len, len(val_str))
            sheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

    # Specific column adjustments for readability
    ws0.column_dimensions['A'].width = 32
    ws1.column_dimensions['A'].width = 25
    ws1.column_dimensions['B'].width = 30
    ws2.column_dimensions['A'].width = 15
    ws2.column_dimensions['B'].width = 22
    ws2.column_dimensions['C'].width = 32
    ws3.column_dimensions['A'].width = 24
    ws3.column_dimensions['B'].width = 32
    ws4.column_dimensions['A'].width = 12
    ws4.column_dimensions['B'].width = 32
    ws5.column_dimensions['A'].width = 15
    ws5.column_dimensions['H'].width = 24
    ws6.column_dimensions['A'].width = 35

    out_file = "Prototipo_Planejador_Capacidade_QRO_FY26_FY30.xlsx"
    wb.save(out_file)
    print(f"Successfully generated prototype Excel file: {out_file}")

if __name__ == '__main__':
    build_capacity_prototype()
