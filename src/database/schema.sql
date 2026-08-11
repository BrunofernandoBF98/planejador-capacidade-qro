-- Schema SQLite Completo para o Planejador de Capacidade QRO (PROMPT MESTRE) --

CREATE TABLE IF NOT EXISTS dim_modelo (
    id_modelo INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_modelo TEXT UNIQUE NOT NULL,
    familia TEXT NOT NULL,
    bucket_corporativo TEXT NOT NULL,
    tier_complexidade TEXT DEFAULT 'Médio',
    amostra_status TEXT DEFAULT 'OK'
);

CREATE TABLE IF NOT EXISTS dim_mapa_modelo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_book1 TEXT,
    nome_crono TEXT,
    nome_sap TEXT,
    status_mapeamento TEXT DEFAULT 'VALIDADO'
);

CREATE TABLE IF NOT EXISTS dim_mapa_operacao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crono_estacion TEXT NOT NULL,
    sap_codigo_op TEXT NOT NULL,
    sap_nome_op TEXT NOT NULL,
    escopo_equivalente TEXT DEFAULT 'Montaje Inicial'
);

CREATE TABLE IF NOT EXISTS dim_ot_mercado (
    id_orden_ot TEXT PRIMARY KEY,
    mercado TEXT DEFAULT 'Não Identificado',
    origem_detecao TEXT DEFAULT 'SAP Prefix'
);

CREATE TABLE IF NOT EXISTS dim_operacao (
    id_operacao INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_operacion TEXT UNIQUE NOT NULL,
    nome_operacion TEXT NOT NULL,
    centro_trabalho TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_centro_trabalho (
    id_centro INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_centro TEXT UNIQUE NOT NULL,
    nome_centro TEXT NOT NULL,
    tipo TEXT
);

CREATE TABLE IF NOT EXISTS dim_calendario (
    id_calendario INTEGER PRIMARY KEY AUTOINCREMENT,
    fy TEXT NOT NULL,
    mes TEXT NOT NULL,
    dias_uteis INTEGER NOT NULL DEFAULT 20
);

CREATE TABLE IF NOT EXISTS fato_medicion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_registro TEXT,
    id_orden_ot TEXT,
    modelo_disyuntor TEXT,
    familia_linea TEXT,
    codigo_operacion TEXT,
    nombre_operacion TEXT,
    nombre_estacion TEXT,
    fecha_medicion TEXT,
    duracion_minutos_real REAL,
    duracion_horas_real REAL,
    cantidad_operadores INTEGER,
    minutos_hombre REAL,
    horas_hombre REAL,
    codigo_clasificacion TEXT, -- VA / NNVA / NVA
    tipo_tiempo TEXT,
    categoria_tiempo TEXT,
    motivo_detalle TEXT,
    status_eficiencia TEXT
);

CREATE TABLE IF NOT EXISTS fato_tempo_estacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modelo TEXT NOT NULL,
    codigo_operacion TEXT NOT NULL,
    nombre_estacion TEXT NOT NULL,
    p50_ciclo_mins REAL NOT NULL,
    p80_ciclo_mins REAL NOT NULL,
    media_ciclo_mins REAL NOT NULL,
    hh_unidad_p50 REAL NOT NULL,
    operadores_promedio INTEGER DEFAULT 1,
    pct_va REAL DEFAULT 0.38,
    pct_nnva REAL DEFAULT 0.12,
    pct_nva REAL DEFAULT 0.50,
    amostra_count INTEGER DEFAULT 1,
    flag_confianca TEXT DEFAULT 'Baixa',
    UNIQUE(modelo, nombre_estacion)
);

CREATE TABLE IF NOT EXISTS fato_tempo_calibrado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modelo TEXT NOT NULL,
    codigo_operacion TEXT NOT NULL,
    horas_hombre_real_p50 REAL NOT NULL,
    horas_hombre_real_p80 REAL NOT NULL,
    horas_va REAL NOT NULL,
    horas_nnva REAL NOT NULL,
    horas_nva REAL NOT NULL,
    pct_va REAL NOT NULL,
    pct_nnva REAL NOT NULL,
    pct_nva REAL NOT NULL,
    eficiencia_real REAL NOT NULL,
    cantidad_operadores INTEGER DEFAULT 1,
    horas_sap REAL,
    fator_correcao_sap REAL,
    amostra_count INTEGER DEFAULT 0,
    amostra_status TEXT DEFAULT 'OK',
    data_calibracao TEXT NOT NULL,
    UNIQUE(modelo, codigo_operacion)
);

CREATE TABLE IF NOT EXISTS fato_tempo_sap (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modelo TEXT NOT NULL,
    codigo_operacion TEXT NOT NULL,
    nombre_operacion TEXT NOT NULL,
    std_horas_promedio REAL NOT NULL,
    real_horas_promedio REAL NOT NULL,
    fator_interno_real_vs_std REAL NOT NULL,
    total_ots_sap INTEGER DEFAULT 0,
    flag_confianca TEXT DEFAULT 'Alta',
    UNIQUE(modelo, codigo_operacion)
);

CREATE TABLE IF NOT EXISTS fato_comparativa_3capadas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modelo TEXT NOT NULL,
    codigo_operacion TEXT NOT NULL,
    nombre_operacion TEXT NOT NULL,
    camada1_std_sap_horas REAL NOT NULL,
    camada2_real_sap_horas REAL NOT NULL,
    fator_interno_sap REAL NOT NULL,
    camada3_crono_p50_horas REAL NOT NULL,
    camada3_crono_p80_horas REAL NOT NULL,
    UNIQUE(modelo, codigo_operacion)
);

CREATE TABLE IF NOT EXISTS fato_demanda_mercado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mercado TEXT NOT NULL, -- México, Jupiter, JXN, Export
    modelo TEXT NOT NULL,
    ano INTEGER NOT NULL, -- 2027, 2028, 2029, 2030, 2031
    quantidade INTEGER NOT NULL,
    modelo_original_book1 TEXT
);

CREATE TABLE IF NOT EXISTS fato_headcount (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_centro TEXT NOT NULL,
    trimestre TEXT NOT NULL,
    headcount INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_precedencia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modelo TEXT NOT NULL,
    op_predecessora TEXT NOT NULL,
    op_sucessora TEXT NOT NULL,
    tipo TEXT DEFAULT 'Série'
);

CREATE TABLE IF NOT EXISTS log_auditoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    tabela TEXT NOT NULL,
    campo TEXT NOT NULL,
    valor_anterior TEXT,
    valor_novo TEXT
);

CREATE TABLE IF NOT EXISTS dim_headcount_actual (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    operacion_original    TEXT NOT NULL,
    nombre_estacion_crono TEXT,               -- NULL if no chrono time exists
    area                  TEXT DEFAULT 'Electrical',
    n_estaciones          INTEGER,            -- number of physical work stations
    hc_total_workforce    INTEGER,            -- total HC in this operation (from the 46)
    mapeado_crono         INTEGER DEFAULT 0,  -- 1 = has measured chrono time; 0 = known HC, no time
    constraint_fisica     TEXT,               -- physical constraint note
    comentario            TEXT,
    fecha_actualizacion   TEXT DEFAULT (date('now'))
);

CREATE TABLE IF NOT EXISTS dim_control_frame_stations (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_estacion     TEXT NOT NULL,       -- 'small' or 'large'
    n_estaciones      INTEGER NOT NULL,    -- count of this type
    max_personas      INTEGER NOT NULL,    -- max simultaneous people per station
    mercados_validos  TEXT NOT NULL,       -- 'CFE+Jupiter' or 'All'
    comentario        TEXT
);

