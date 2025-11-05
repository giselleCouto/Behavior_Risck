import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import altair as alt
import seaborn as sns

from data_pipeline import (
    UploadedArtifacts,
    available_file_sources,
    df_to_csv_bytes,
    df_to_excel_bytes,
    df_to_parquet_bytes,
    fetch_external_file,
    file_source_label,
    load_indicadores,
    load_relatorio,
    load_shap,
    load_behavior_model,
    sanitize_behavior_dataset,
    summarize_quality_events,
    FileSourceError,
    FileSourceOption,
)


def prepare_relatorio_for_analysis(relatorio: pd.DataFrame):
    """Return processed views required for the analytical tabs."""

    relatorio_processed = relatorio.copy()
    relatorio_processed['Reneg_aberto'] = np.where(
        relatorio_processed["data_reneg_aberto"].isna(),
        "NAO",
        "SIM",
    )

    df_selecao = relatorio_processed.drop(
        columns=[
            "cpf_cnpj",
            "data_processamento",
            "data_movimento",
            "data_ultima_alteracao_limite",
            "Modelo",
            "SCORE_ORIGEM",
            "data_reneg_aberto",
        ]
    ).copy()

    df_selecao['fx_Idade'] = pd.cut(
        df_selecao.idade,
        bins=[-np.inf, 29, 37, 44, 50, 57, 63, 70, np.inf],
        labels=[
            "Até 29",
            "De 29 a 37",
            "De 37 a 44",
            "De 44 a 50",
            "De 50 a 57",
            "De 57 a 63",
            "De 63 a 70",
            "Acima de 70",
        ],
    )
    df_selecao['fx_meses_ultimo_pagamento'] = pd.cut(
        df_selecao.meses_ultimo_pagamento,
        bins=[
            -0.99,
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            24,
            36,
            np.inf,
        ],
        labels=[
            "0",
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "10",
            "11",
            "12",
            "13",
            "14",
            "15",
            "16",
            "17",
            "18",
            "19 a 24",
            "3 anos",
            "+3 anos",
        ],
    )
    df_selecao['fx_relacionamento_meses'] = pd.cut(
        df_selecao.tempo_relacionamento_kredilig_meses,
        bins=[
            -0.99,
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            24,
            36,
            48,
            60,
            72,
            84,
            96,
            np.inf,
        ],
        labels=[
            "0",
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "10",
            "11",
            "12",
            "13",
            "14",
            "15",
            "16",
            "17",
            "18",
            "19 a 24",
            "3 anos",
            "4 anos",
            "5 anos",
            "6 anos",
            "7 anos",
            "8 anos",
            "+8 anos",
        ],
    )
    df_selecao['fx_Limite'] = pd.cut(
        df_selecao.limite_total,
        bins=[-0.99, 0, 1000, 5000, 10000, 20000, np.inf],
        labels=[
            "Sem Limite",
            "Até R$1 mil",
            "R$1 mil a R$5 mil",
            "R$5 mil a R$10mil",
            "R$10 mil a R$20mil",
            "Acima de R$20mil",
        ],
    )
    df_selecao["fx_renda_valida"] = pd.cut(
        df_selecao.renda_valida_new,
        bins=[0, 1518, 1518 * 1.25, 1518 * 1.5, 1518 * 2, 1518 * 3, np.inf],
        labels=[
            "Até 1 SM",
            "De 1 SM a 1,25 SM",
            "De 1,25 SM a 1,5 SM",
            "De 1,5 SM a 2 SM",
            "De 2 SM a 3 SM",
            "Acima de 3 SM",
        ],
    )
    df_selecao['tem_valor_da_parcela_aberto'] = np.where(
        df_selecao["valor_da_parcela_aberto"] > 0,
        "SIM",
        "NAO",
    )
    df_selecao['fx_dias_maior_atraso'] = pd.cut(
        df_selecao.dias_maior_atraso,
        bins=[-0.99, 0, 1, 2, 3, 7, 15, 30, 60, np.inf],
        labels=["0", "1", "2", "3", "4 a 7", "8 a 15", "16 a 30", "31 a 60", "Acima 60"],
    )
    df_selecao['fx_dias_maior_atraso_aberto'] = pd.cut(
        df_selecao.dias_maior_atraso_aberto,
        bins=[
            -0.99,
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            20,
            25,
            30,
            40,
            50,
            np.inf,
        ],
        labels=[
            "0",
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "10",
            "11",
            "12",
            "13",
            "14",
            "15",
            "16 a 20",
            "21 a 25",
            "26 a 30",
            "31 a 40",
            "41 a 50",
            "50+",
        ],
    )
    df_selecao['fx_dias_media_atraso'] = pd.cut(
        df_selecao.media_atraso_dias,
        bins=[-0.99, 0, 1, 2, 3, 7, 15, 30, 60, np.inf],
        labels=["0", "1", "2", "3", "4 a 7", "8 a 15", "16 a 30", "31 a 60", "Acima 60"],
    )
    df_selecao["fx_qtd_contratos"] = pd.cut(
        df_selecao.qtd_contratos,
        bins=[
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
            20,
            30,
            50,
            np.inf,
        ],
        labels=[
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "10",
            "11",
            "12",
            "13",
            "14",
            "15",
            "16",
            "17",
            "18",
            "19",
            "20",
            "21 a 30",
            "31 a 50",
            "Acima 50",
        ],
    )
    df_selecao["fx_qtd_contratos_nr"] = pd.cut(
        df_selecao.qtd_contratos_nr,
        bins=[
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
            20,
            30,
            50,
            np.inf,
        ],
        labels=[
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "10",
            "11",
            "12",
            "13",
            "14",
            "15",
            "16",
            "17",
            "18",
            "19",
            "20",
            "21 a 30",
            "31 a 50",
            "Acima 50",
        ],
    )
    df_selecao['fx_contratos_regular'] = pd.cut(
        df_selecao.qtd_contratos_regular,
        bins=[-0.99, 0, 1, 3, np.inf],
        labels=["0", "1", "2 a 3", "+3"],
    )
    df_selecao['fx_qtd_contratos_atraso'] = pd.cut(
        df_selecao.qtd_contratos_atraso,
        bins=[-0.99, 0, 1, 3, np.inf],
        labels=["0", "1", "2 a 3", "+3"],
    )
    df_selecao['fx_contratos_fechado_regular'] = pd.cut(
        df_selecao.qtd_contratos_fechado_regular,
        bins=[-0.99, 0, 1, 2, 3, 4, 5, 6, 10, np.inf],
        labels=["0", "1", "2", "3", "4", "5", "6", "7 a 10", "+10"],
    )
    df_selecao['fx_qtd_contratos_fechado_atraso'] = pd.cut(
        df_selecao.qtd_contratos_fechado_atraso,
        bins=[-0.99, 0, 1, 2, 3, 4, 5, 6, 10, np.inf],
        labels=["0", "1", "2", "3", "4", "5", "6", "7 a 10", "+10"],
    )
    df_selecao['fx_contratos_aberto_regular'] = pd.cut(
        df_selecao.qtd_contratos_aberto_regular,
        bins=[-0.99, 0, 1, 3, np.inf],
        labels=["0", "1", "2 a 3", "+3"],
    )
    df_selecao['fx_qtd_contratos_aberto_atraso'] = pd.cut(
        df_selecao.qtd_contratos_aberto_atraso,
        bins=[-0.99, 0, 1, 3, np.inf],
        labels=["0", "1", "2 a 3", "+3"],
    )
    df_selecao['fx_reneg_fechado_regular'] = pd.cut(
        df_selecao.qtd_reneg_fechado_regular,
        bins=[-0.99, 0, 1, 3, np.inf],
        labels=["0", "1", "2 a 3", "+3"],
    )
    df_selecao['fx_qtd_reneg_fechado_atraso'] = pd.cut(
        df_selecao.qtd_reneg_fechado_atraso,
        bins=[-0.99, 0, 1, 3, np.inf],
        labels=["0", "1", "2 a 3", "+3"],
    )
    df_selecao['fx_reneg_aberto_regular'] = pd.cut(
        df_selecao.qtd_reneg_aberto_regular,
        bins=[-0.99, 0, 1, 3, np.inf],
        labels=["0", "1", "2 a 3", "+3"],
    )
    df_selecao['fx_qtd_reneg_aberto_atraso'] = pd.cut(
        df_selecao.qtd_reneg_aberto_atraso,
        bins=[-0.99, 0, 1, 3, np.inf],
        labels=["0", "1", "2 a 3", "+3"],
    )
    df_selecao['med_meses_entre_contratos'] = pd.cut(
        df_selecao.media_meses_entre_contratos_combinado,
        bins=[-0.99, 0, 1, 2, 3, 4, 5, 6, 9, 12, np.inf],
        labels=[
            "0",
            "Até 1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7 a 9",
            "10 a 12",
            "12+",
        ],
    )
    df_selecao['fx_qtd_parcelas_pagas'] = pd.cut(
        df_selecao.qtd_parcelas_pagas,
        bins=[
            -0.99,
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
            20,
            30,
            50,
            100,
            np.inf,
        ],
        labels=[
            "0",
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "10",
            "11",
            "12",
            "13",
            "14",
            "15",
            "16",
            "17",
            "18",
            "19",
            "20",
            "21 a 30",
            "31 a 50",
            "51 a 100",
            "Acima 100",
        ],
    )
    df_selecao['fx_qtd_parcelas_pagas_nr'] = pd.cut(
        df_selecao.qtd_parcelas_pagas_nr,
        bins=[-0.99, 0, 5, 10, 15, 20, 30, 50, 100, np.inf],
        labels=[
            "0",
            "1-5",
            "6-10",
            "11-15",
            "16-20",
            "21 a 30",
            "31 a 50",
            "51 a 100",
            "Acima 100",
        ],
    )
    df_selecao['fx_qtd_parcelas_abertas'] = pd.cut(
        df_selecao.qtd_parcelas_aberta,
        bins=[-0.99, 0, 10, 20, 50, np.inf],
        labels=["0", "Até 10", "11 a 20", "21 a 50", "Acima 50"],
    )
    df_selecao['fx_principal_total'] = pd.cut(
        df_selecao.principal_total,
        bins=[-0.99, 0, 1000, 2500, 5000, 7500, 10000, 15000, 20000, np.inf],
        labels=[
            "Sem_Valor",
            "Até R$1 mil",
            "R$1 mil a R$2,5 mil",
            "R$2,5 mil a R$5 mil",
            "R$5 mil a R$7,5 mil",
            "R$7,5 mil a R$10mil",
            "R$10 mil a R$15mil",
            "R$15 mil a R$20mil",
            "Acima de R$20mil",
        ],
    )
    df_selecao["fx_valor_pago_nr"] = pd.cut(
        df_selecao.valor_pago_nr,
        bins=[-0.99, 0, 2000, 5000, 10000, 20000, np.inf],
        labels=[
            "0",
            "Até R$2 mil",
            "R$2 mil a R$5mil",
            "R$5 mil a R$10mil",
            "R$10 mil a R$20mil",
            "Acima de R$20mil",
        ],
    )
    df_selecao["fx_principal_total_nr"] = pd.cut(
        df_selecao.valor_principal_total_nr,
        bins=[-0.99, 0, 2000, 5000, 10000, 20000, np.inf],
        labels=[
            "0",
            "Até R$2 mil",
            "R$2 mil a R$5mil",
            "R$5 mil a R$10mil",
            "R$10 mil a R$20mil",
            "Acima de R$20mil",
        ],
    )
    df_selecao['fx_principal_total_fechado'] = pd.cut(
        df_selecao.principal_total_fechado,
        bins=[-0.99, 0, 1000, 2000, 3000, 5000, 10000, np.inf],
        labels=[
            "0",
            "Até R$1 mil",
            "R$1 mil a R$2 mil",
            "R$2 mil a R$3mil",
            "R$3 mil a R$4mil",
            "R$5 mil a R$10mil",
            "Acima de R$10mil",
        ],
    )
    df_selecao['fx_freq_atraso'] = pd.cut(
        df_selecao.freq_atraso,
        bins=[-0.99, 0, 0.05, 0.1, 0.2, 0.5, 1, 3, 10, np.inf],
        labels=[
            "0",
            "Até 0.05",
            "Até 0.1",
            "Até 0.2",
            "Até 0.5",
            "0.5 a 1",
            "1 a 3",
            "3 a 10",
            "Acima de 10",
        ],
    )
    df_selecao['fx_exposicao_ratio'] = pd.cut(
        df_selecao.exposicao_ratio,
        bins=[-0.99, 0, 0.1, 0.2, 0.4, 0.6, 0.8, 0.9, np.inf],
        labels=[
            "0",
            "Até 0.1",
            "0.1 a 0.2",
            "0.2 a 0.4",
            "0.4 a 0.6",
            "0.6 a 0.8",
            "0.8 a 0.9",
            "0.9 a 1",
        ],
    )
    df_selecao['fx_indice_instabilidade'] = pd.cut(
        df_selecao.indice_instabilidade,
        bins=[-0.99, 0, 5, 10, 15, 20, 40, 60, np.inf],
        labels=[
            "0",
            "Até 5",
            "5 a 10",
            "10 a 15",
            "15 a 20",
            "20 a 40",
            "40 a 60",
            "Acima de 60",
        ],
    )
    df_selecao['fx_indice_regularidade'] = pd.cut(
        df_selecao.indice_regularidade,
        bins=[-0.99, 0, 0.3, 0.4, 0.6, 0.8, 0.99999999, 1.01],
        labels=[
            "0",
            "Até 0.3",
            "0.3 a 0.4",
            "0.4 a 0.6",
            "0.6 a 0.8",
            "0.8 a 0.99",
            "1",
        ],
    )
    df_selecao['fx_prop_reneg'] = pd.cut(
        df_selecao.prop_reneg,
        bins=[-0.99, 0, 0.1, 0.3, 0.4, 0.7, 1.01],
        labels=[
            "0",
            "Até 0.1",
            "0.1 a 0.3",
            "0.3 a 0.4",
            "0.4 a 0.7",
            "Acima de 0.7",
        ],
    )
    df_selecao['fx_reneg_severity'] = pd.cut(
        df_selecao.reneg_severity,
        bins=[-0.99, 0, 0.1, 0.3, 0.4, 0.7, 1.01],
        labels=[
            "0",
            "Até 0.1",
            "0.1 a 0.3",
            "0.3 a 0.4",
            "0.4 a 0.7",
            "Acima de 0.7",
        ],
    )
    df_selecao['fx_reneg_vs_liq_ratio'] = pd.cut(
        df_selecao.reneg_vs_liq_ratio,
        bins=[-0.99, 0, 0.1, 0.5, 1, np.inf],
        labels=["0", "Até 0.1", "0.1 a 0.5", "0.5 a 1", "Acima de 1"],
    )
    df_selecao['fx_reneg_vs_liq_ratio_ponderado'] = pd.cut(
        df_selecao.reneg_vs_liq_ratio_ponderado,
        bins=[-0.99, 0, 0.1, 0.5, 1, np.inf],
        labels=["0", "Até 0.1", "0.1 a 0.5", "0.5 a 1", "Acima de 1"],
    )
    df_selecao['fx_tempo_ultimo_pagamento_pond'] = pd.cut(
        df_selecao.tempo_ultimo_pagamento_pond,
        bins=[-0.99, 0, 1, 5, 12, 24, 36, 48, 60, 120, np.inf],
        labels=[
            "0",
            "1",
            "1 a 5",
            "5 a 12",
            "12 a 24",
            "24 a 36",
            "36 a 48",
            "48 a 60",
            "60 a 120",
            "Acima de 120",
        ],
    )

    variaveis = df_selecao.select_dtypes(include=["category", "object"]).columns.tolist()
    return relatorio_processed, df_selecao, variaveis

#.venv\Scripts\python.exe -m streamlit run Monitoramento\Dash.py

st.set_page_config(
    page_title="Dashboard - Predição de Risco de Crédito",
    layout="wide",   # <- isso deixa o dashboard ocupar a largura total
    initial_sidebar_state="expanded"
)

st.title("Dashboard - Predição de Risco de Crédito")
st.markdown("Este painel apresenta um relatório do Behavior Score - KAB.")

if "artifacts" not in st.session_state:
    st.session_state["artifacts"] = UploadedArtifacts()

artifacts: UploadedArtifacts = st.session_state["artifacts"]

aba,aba1,aba11, aba2, aba3 = st.tabs(["carregar dados","Análise Exploratória (EDA)","Análise Exploratória (EDA)","Relatório","Indicadores"])

with aba:
    # ==============================
    # Carregar dados
    # ==============================
    st.markdown(
        "Forneça os arquivos diretamente pelo upload ou, se preferir, informe um link compartilhado do Google Drive ou OneDrive."
    )

    def _render_artifact_loader(
        *,
        title: str,
        key_prefix: str,
        loader,
        accepted_types: list[str],
        default_remote_name: str,
        data_attr: str,
        name_attr: str,
        postprocess=None,
    ):
        source = st.selectbox(
            f"Como deseja carregar o {title}?",
            options=available_file_sources(),
            format_func=lambda option: file_source_label(option),
            key=f"{key_prefix}_source",
        )

        def _persist_artifact(file_like, file_name: str):
            try:
                dataframe = loader(file_like)
                extra_payload = {}
                if postprocess is not None:
                    normalized, features, quality = postprocess(dataframe)
                    dataframe = normalized
                    extra_payload[f"{data_attr}_features"] = features
                    extra_payload[f"{data_attr}_quality"] = summarize_quality_events(quality)

                setattr(artifacts, data_attr, dataframe)
                setattr(artifacts, name_attr, file_name)
                for attr_name, value in extra_payload.items():
                    if hasattr(artifacts, attr_name):
                        setattr(artifacts, attr_name, value)
                st.success(f"{title} '{file_name}' carregado com sucesso!")
            except Exception as exc:  # noqa: BLE001 - surface full context to the user
                st.error(f"Falha ao carregar {title.lower()}: {exc}")

        if source is FileSourceOption.UPLOAD:
            uploaded_file = st.file_uploader(
                f"Carregue o arquivo do {title}",
                type=accepted_types,
                key=f"{key_prefix}_upload",
            )
            if uploaded_file is not None:
                _persist_artifact(uploaded_file, uploaded_file.name)
        else:
            url = st.text_input(
                f"Informe o link compartilhado do {title}",
                key=f"{key_prefix}_url",
            )
            trigger_label = file_source_label(source)
            if st.button(
                f"Carregar {title} a partir do {trigger_label}",
                key=f"{key_prefix}_load",
            ):
                try:
                    buffer, resolved_name = fetch_external_file(
                        source=source,
                        reference=url,
                        default_name=default_remote_name,
                    )
                    _persist_artifact(buffer, resolved_name)
                except FileSourceError as exc:
                    st.error(str(exc))

    _render_artifact_loader(
        title="Relatório de Behavior",
        key_prefix="relatorio",
        loader=load_relatorio,
        accepted_types=["csv"],
        default_remote_name="relatorio_behavior.csv",
        data_attr="relatorio",
        name_attr="relatorio_name",
        postprocess=lambda frame: sanitize_behavior_dataset(frame, model=load_behavior_model()),
    )

    _render_artifact_loader(
        title="arquivo de SHAP",
        key_prefix="relatorio_shap",
        loader=load_shap,
        accepted_types=["parquet"],
        default_remote_name="relatorio_shap.parquet",
        data_attr="shap_values",
        name_attr="shap_name",
    )

    _render_artifact_loader(
        title="arquivo de Indicadores",
        key_prefix="relatorio_ind",
        loader=load_indicadores,
        accepted_types=["xlsx"],
        default_remote_name="indicadores.xlsx",
        data_attr="indicadores",
        name_attr="indicadores_name",
    )

    if st.button("Limpar arquivos carregados"):
        st.session_state["artifacts"] = UploadedArtifacts()
        artifacts = st.session_state["artifacts"]
        st.info("Arquivos removidos da sessão.")

    if artifacts.has_relatorio():
        st.download_button(
            "Baixar relatório carregado",
            data=df_to_csv_bytes(artifacts.relatorio),
            file_name=artifacts.relatorio_name or "relatorio_behavior.csv",
            mime="text/csv",
        )

    if artifacts.relatorio_features is not None:
        st.download_button(
            "Baixar dataset preparado para scoring",
            data=df_to_parquet_bytes(artifacts.relatorio_features),
            file_name="relatorio_behavior_features.parquet",
            mime="application/octet-stream",
        )

    if artifacts.relatorio_quality is not None:
        st.markdown("### Relatório de qualidade dos dados")
        st.dataframe(artifacts.relatorio_quality)

    if artifacts.has_shap():
        st.download_button(
            "Baixar SHAP carregado",
            data=df_to_parquet_bytes(artifacts.shap_values),
            file_name=artifacts.shap_name or "relatorio_shap.parquet",
            mime="application/octet-stream",
        )

    if artifacts.has_indicadores():
        st.download_button(
            "Baixar indicadores carregados",
            data=df_to_excel_bytes(artifacts.indicadores),
            file_name=artifacts.indicadores_name or "indicadores.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

with tab_eda:
    st.title("Análise Exploratória (EDA)")
    # ==============================
    # Distribuição das variáveis
    # ==============================
    if not artifacts.has_relatorio():
        st.info("Carregue o Relatório de Behavior na aba 'carregar dados'.")
    else:
        relatorio, df_selecao, variaveis = prepare_relatorio_for_analysis(artifacts.relatorio)

        var_escolhida = st.selectbox("Selecione a variável para visualizar:", variaveis, key="var_escolhida_aba1")
        counts = df_selecao[var_escolhida].value_counts().reset_index()
        counts.columns = [var_escolhida, "count"]

        st.subheader("Gráfico de frequência:")
        chart = alt.Chart(counts).mark_bar().encode(
            x=alt.X(f'{var_escolhida}:N', title=var_escolhida),
            y=alt.Y('count:Q', title='Quantidade')
        ).properties(
            width=600,
            height=400
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.altair_chart(chart, use_container_width=False)

        st.subheader("Tabela cruzada com variável target (inad_e_reneg):")
        st.write(""" 1 = Indica que possui algum contrato com mais de 60 dias de atraso ou com renegociação em aberto (Mau pagador)

                     0 = Indica que é adimplente (Bom pagador)""")
        ct = pd.crosstab(df_selecao[var_escolhida], df_selecao["inad_e_reneg"], margins=True, margins_name="Total")
        ct_percent = pd.crosstab(df_selecao[var_escolhida], df_selecao["inad_e_reneg"], margins=True, margins_name="Total", normalize="index") * 100
        ct_percent = ct_percent.round(2)

        ct_combined = ct.copy()
        for col in df_selecao["inad_e_reneg"].unique():
            ct_combined[f"{col} %"] = ct_percent[col]

        cm = sns.light_palette("green", as_cmap=True)
        subset_df = ct_combined.iloc[:-1]

        ct_styled = ct_combined.style.format("{:.2f}")
        ct_styled = ct_styled.background_gradient(cmap=cm, subset=pd.IndexSlice[subset_df.index, ['1 %']])
        ct_styled = ct_styled.background_gradient(cmap=cm, subset=pd.IndexSlice[subset_df.index, ['0 %']])
        st.dataframe(ct_styled)

        tab_cruz_sem_total = pd.crosstab(
            df_selecao[var_escolhida],
            df_selecao["inad_e_reneg"],
            normalize="index"
        ).reset_index()
        tab_long = tab_cruz_sem_total.melt(
            id_vars=var_escolhida,
            var_name="inad_e_reneg",
            value_name="frequencia"
        )

        chart = (
            alt.Chart(tab_long)
            .mark_bar()
            .encode(
                x=alt.X(f"{var_escolhida}:N", title=var_escolhida),
                y=alt.Y("frequencia:Q", title="Frequência"),
                color="inad_e_reneg:N",
                xOffset="inad_e_reneg:N"
            )
        )

        st.subheader("Gráfico de frequencia por inad_e_reneg:")
        st.altair_chart(chart, use_container_width=True)

        st.download_button(
            "Baixar base preparada (CSV)",
            data=df_to_csv_bytes(df_selecao),
            file_name="relatorio_preparado_eda.csv",
            mime="text/csv",
        )

with aba11:
    st.title("Análise Exploratória (EDA)")

    if not artifacts.has_relatorio():
        st.info("Carregue o Relatório de Behavior na aba 'carregar dados'.")
    else:
        _, df_selecao, variaveis = prepare_relatorio_for_analysis(artifacts.relatorio)

        var_escolhida = st.selectbox("Selecione a variável Linha :", variaveis, key="var_escolhida_linha")
        opcoes_coluna = [v for v in variaveis if v != var_escolhida]
        var_escolhida_2 = st.selectbox("Selecione a variável Coluna:", opcoes_coluna, key="var_escolhida_coluna")

        categorias_linha = df_selecao[var_escolhida].dropna().unique()
        filtro_linha = st.multiselect(
            f"Filtrar categorias de {var_escolhida}:",
            options=sorted(categorias_linha),
            default=sorted(categorias_linha),
            key="filtro_linha"
        )

        categorias_coluna = df_selecao[var_escolhida_2].dropna().unique()
        filtro_coluna = st.multiselect(
            f"Filtrar categorias de {var_escolhida_2}:",
            options=sorted(categorias_coluna),
            default=sorted(categorias_coluna),
            key="filtro_coluna"
        )

        df_filtrado = df_selecao[
            df_selecao[var_escolhida].isin(filtro_linha) &
            df_selecao[var_escolhida_2].isin(filtro_coluna)
        ]

        st.subheader(f"Tabela de contingência {var_escolhida} vs {var_escolhida_2}:")
        ct = pd.crosstab(
            df_filtrado[var_escolhida],
            df_filtrado[var_escolhida_2],
            margins=True, margins_name="Total"
        )

        ct_percent = pd.crosstab(
            df_filtrado[var_escolhida],
            df_filtrado[var_escolhida_2],
            margins=True, margins_name="Total",
            normalize="index"
        ) * 100
        ct_percent = ct_percent.round(2)

        ct_combined = ct.copy()
        for col in df_filtrado[var_escolhida_2].unique():
            ct_combined[f"{col} %"] = ct_percent[col]

        st.write(ct_combined)

        tab_cruz_sem_total = pd.crosstab(
            df_filtrado[var_escolhida],
            df_filtrado[var_escolhida_2],
            normalize="index"
        ).reset_index()

        tab_long = tab_cruz_sem_total.melt(
            id_vars=var_escolhida,
            var_name=var_escolhida_2,
            value_name="frequencia"
        )

        chart = (
            alt.Chart(tab_long)
            .mark_bar()
            .encode(
                x=alt.X(f"{var_escolhida}:N", title=var_escolhida),
                y=alt.Y("frequencia:Q", title="Frequência"),
                color=f"{var_escolhida_2}:N",
                xOffset=f"{var_escolhida_2}:N"
            )
        )

        text = chart.mark_text(
            dy=-8,
            dx=24,
            size=16
        ).encode(
            text=alt.Text('frequencia:Q', format='.2%')
        )

        st.subheader(f"Gráfico de frequência {var_escolhida} vs {var_escolhida_2}:")
        st.altair_chart(chart + text, use_container_width=True)

        st.download_button(
            "Baixar tabela de contingência (CSV)",
            data=df_to_csv_bytes(ct_combined.reset_index()),
            file_name="tabela_contingencia.csv",
            mime="text/csv",
        )

with tab_relatorio:
    st.title("Relatório")
    # ==============================
    # Relatório
    # ==============================
    if not artifacts.has_relatorio():
        st.info("Carregue o Relatório de Behavior na aba 'carregar dados'.")
    else:
        relatorio_view = artifacts.relatorio
        relatorio_shap = artifacts.shap_values if artifacts.has_shap() else None

        cpf_input = st.text_input("Digite o CPF:", key="cpf_input")

        if cpf_input:
            try:
                cpf_num = int(cpf_input)
                relatorio_filtrado = relatorio_view[relatorio_view["cpf_cnpj"] == cpf_num]
                st.dataframe(relatorio_filtrado)
                st.download_button(
                    "Baixar relatório filtrado (CSV)",
                    data=df_to_csv_bytes(relatorio_filtrado),
                    file_name=f"relatorio_{cpf_num}.csv",
                    mime="text/csv",
                )

                if relatorio_shap is not None:
                    relatorio_filtrado_shap = relatorio_shap[relatorio_shap["cpf_cnpj"] == cpf_num]
                    st.write("Relatório Shap")
                    st.dataframe(relatorio_filtrado_shap)
                    st.download_button(
                        "Baixar SHAP filtrado (Parquet)",
                        data=df_to_parquet_bytes(relatorio_filtrado_shap),
                        file_name=f"shap_{cpf_num}.parquet",
                        mime="application/octet-stream",
                    )

                    import plotly.express as px

                    cols_shap = [
                        'valor_pago_nr_shap',
                        'produtos_FINANCIAMENTO_shap',
                        'indice_instabilidade_shap',
                        'qtd_parcelas_pagas_nr_shap',
                        'reneg_vs_liq_ratio_ponderado_shap',
                        'valor_principal_total_nr_shap',
                        'produtos_EMPRESTIMO/FINANCIAMENTO_shap',
                        'idade_shap',
                        'qtd_contratos_nr_shap',
                        'tempo_relacionamento_kredilig_meses_shap',
                        'ocupacao_APOSENTADO_shap',
                        'ocupacao_EMPREGADO_PRIVADO_AUTONOMO_shap',
                        'canal_origem_Fisico_shap',
                        'produtos_EMPRESTIMO_shap',
                        'possui_contratos_a_vista_SIM_shap'
                    ]

                    df_shap = relatorio_filtrado_shap[cols_shap].mean().sort_values(ascending=True)
                    df_plot = pd.DataFrame({
                        "Feature": df_shap.index,
                        "SHAP value": df_shap.values
                    })

                    fig = px.bar(
                        df_plot,
                        x="SHAP value",
                        y="Feature",
                        orientation="h",
                        color="SHAP value",
                        color_continuous_scale="RdBu_r",
                        range_color=[-abs(df_plot["SHAP value"]).max(), abs(df_plot["SHAP value"]).max()],
                        title="Importância média dos valores SHAP",
                    )

                    fig.update_layout(
                        yaxis=dict(title="Variável"),
                        xaxis=dict(title="Valor do SHAP"),
                        template="simple_white",
                        height=500
                    )

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Arquivo de SHAP não foi carregado.")
            except ValueError:
                st.error("Digite apenas números válidos para o CPF.")
        else:
            st.dataframe(relatorio_view)
            st.download_button(
                "Baixar relatório completo (CSV)",
                data=df_to_csv_bytes(relatorio_view),
                file_name=artifacts.relatorio_name or "relatorio_behavior.csv",
                mime="text/csv",
            )
            if relatorio_shap is None:
                st.warning("Arquivo de SHAP não foi carregado.")
            else:
                st.write(''' Digite o CPF para visualizar relatório SHAP.''')

with tab_indicadores:
    st.title("Indicadores")
    # ==============================
    # Indicadores
    # ==============================
    if not artifacts.has_indicadores():
        st.info("Carregue o arquivo de indicadores na aba 'carregar dados'.")
    else:
        st.subheader("Evolução dos Indicadores")
        st.dataframe(artifacts.indicadores)
        st.download_button(
            "Baixar indicadores (Excel)",
            data=df_to_excel_bytes(artifacts.indicadores),
            file_name=artifacts.indicadores_name or "indicadores.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        indicador = st.selectbox("Escolha o indicador", artifacts.indicadores.columns[4:], key="indicador_select")
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(artifacts.indicadores['INDICE'], artifacts.indicadores[indicador], marker='o')
        ax.set_xlabel("Índice")
        ax.set_ylabel(indicador)
        ax.set_title(f"Série Temporal de {indicador}")
        ax.legend()
        ax.grid(True)
        plt.xticks(rotation=45)
        st.pyplot(fig)