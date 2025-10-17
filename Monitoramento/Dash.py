import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import altair as alt
import seaborn as sns
import plotly.graph_objects as go

#.venv\Scripts\python.exe -m streamlit run Monitoramento\Dash.py  

st.set_page_config(
    page_title="Dashboard - Predição de Risco de Crédito",
    layout="wide",   # <- isso deixa o dashboard ocupar a largura total
    initial_sidebar_state="expanded"
)

st.title("Dashboard - Predição de Risco de Crédito")
st.markdown("Este painel apresenta um relatório do Behavior Score - KAB.")

aba,aba1,aba11, aba2, aba3 = st.tabs(["carregar dados","Análise Exploratória (EDA)","Análise Exploratória (EDA)","Relatório","Indicadores"])

with aba:
    # ==============================
    # Carregar dados
    # ==============================
    relatorio_file = st.file_uploader("Carregue o arquivo do Relatório de Behavior", type=["csv"])
    relatorio_shap_file = st.file_uploader("Carregue o arquivo do Shap", type=["parquet"])
    relatorio_ind_file = st.file_uploader("Carregue o arquivo de Indicadores", type=["xlsx"])

    # Lendo os arquivos apenas se foram carregados
    if relatorio_file is not None:
        relatorio = pd.read_csv(relatorio_file, sep=",")
        st.success("Relatório carregado com sucesso!")


    if relatorio_shap_file is not None:
        relatorio_shap = pd.read_parquet(relatorio_shap_file)
        st.success("Shap carregado com sucesso!")

    if relatorio_ind_file is not None:
        indicadores = pd.read_excel(relatorio_ind_file)
        st.success("Indicadores carregado com sucesso!")

with aba1:
    st.title("Análise Exploratória (EDA)")
    # ==============================
    # Distribuição das variáveis
    # ==============================
    relatorio['Reneg_aberto']=np.where(relatorio["data_reneg_aberto"].isna(),"NAO","SIM")
    df_selecao=relatorio.drop(columns=["cpf_cnpj","data_processamento","data_movimento","data_ultima_alteracao_limite","Modelo","SCORE_ORIGEM","data_reneg_aberto"]).copy()

    # Categorizando as variáveis numéricas
    df_selecao['fx_Idade']=pd.cut(df_selecao.idade, bins=[-np.inf,29,37,44,50,57,63,70,np.inf],labels=["Até 29","De 29 a 37","De 37 a 44","De 44 a 50","De 50 a 57","De 57 a 63","De 63 a 70","Acima de 70"])# categorização por quantil
    df_selecao['fx_meses_ultimo_pagamento']=pd.cut(df_selecao.meses_ultimo_pagamento,bins=[-0.99,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,24,36,np.inf],labels=["0","1", "2", "3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19 a 24","3 anos", "+3 anos",])
    df_selecao['fx_relacionamento_meses']=pd.cut(df_selecao.tempo_relacionamento_kredilig_meses,bins=[-0.99,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,24,36,48,60,72,84,96,np.inf],labels=["0","1", "2", "3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19 a 24","3 anos","4 anos","5 anos","6 anos","7 anos","8 anos", "+8 anos",])
    #df_selecao['fx_meses_entre_prim_ult_pag']=pd.cut(df_selecao.meses_entre_primeiro_e_ultimo_pagamento,bins=[-0.99,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,24,36,np.inf],labels=["0","1", "2", "3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19 a 24","3 anos", "+3 anos",])
    df_selecao['fx_Limite']=pd.cut(df_selecao.limite_total,bins=[-0.99,0,1000,5000,10000,20000,np.inf],labels=["Sem Limite","Até R$1 mil","R$1 mil a R$5 mil","R$5 mil a R$10mil","R$10 mil a R$20mil","Acima de R$20mil"])
    df_selecao["fx_renda_valida"]=pd.cut(df_selecao.renda_valida_new, bins=[0,1518,1518*1.25,1518*1.5,1518*2,1518*3,np.inf],labels=["Até 1 SM","De 1 SM a 1,25 SM","De 1,25 SM a 1,5 SM", "De 1,5 SM a 2 SM", "De 2 SM a 3 SM", "Acima de 3 SM"])
    df_selecao['tem_valor_da_parcela_aberto']=np.where(df_selecao["valor_da_parcela_aberto"]>0,"SIM","NAO")
    df_selecao['fx_dias_maior_atraso']=pd.cut(df_selecao.dias_maior_atraso,bins=[-0.99,0,1,2,3,7,15,30,60,np.inf],labels=["0","1","2","3","4 a 7","8 a 15","16 a 30","31 a 60","Acima 60"])
    df_selecao['fx_dias_maior_atraso_aberto']=pd.cut(df_selecao.dias_maior_atraso_aberto,bins=[-0.99,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,20,25,30,40,50,np.inf],labels=["0","1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16 a 20","21 a 25","26 a 30","31 a 40","41 a 50","50+"])
    df_selecao['fx_dias_media_atraso']=pd.cut(df_selecao.media_atraso_dias,bins=[-0.99,0,1,2,3,7,15,30,60,np.inf],labels=["0","1","2","3","4 a 7","8 a 15","16 a 30","31 a 60","Acima 60"])
    df_selecao["fx_qtd_contratos"]=pd.cut(df_selecao.qtd_contratos,bins=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,30,50,np.inf],labels=["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21 a 30","31 a 50", "Acima 50"])
    df_selecao["fx_qtd_contratos_nr"]=pd.cut(df_selecao.qtd_contratos_nr,bins=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,30,50,np.inf],labels=["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21 a 30","31 a 50", "Acima 50"])
    df_selecao['fx_contratos_regular']=pd.cut(df_selecao.qtd_contratos_regular,bins=[-0.99,0,1,3,np.inf],labels=["0","1","2 a 3","+3"])
    df_selecao['fx_qtd_contratos_atraso']=pd.cut(df_selecao.qtd_contratos_atraso,bins=[-0.99,0,1,3,np.inf],labels=["0","1","2 a 3","+3"])
    df_selecao['fx_contratos_fechado_regular']=pd.cut(df_selecao.qtd_contratos_fechado_regular,bins=[-0.99,0,1,2,3,4,5,6,10,np.inf],labels=["0","1","2","3","4","5","6","7 a 10","+10"])
    df_selecao['fx_qtd_contratos_fechado_atraso']=pd.cut(df_selecao.qtd_contratos_fechado_atraso,bins=[-0.99,0,1,2,3,4,5,6,10,np.inf],labels=["0","1","2","3","4","5","6","7 a 10","+10"])
    df_selecao['fx_contratos_aberto_regular']=pd.cut(df_selecao.qtd_contratos_aberto_regular,bins=[-0.99,0,1,3,np.inf],labels=["0","1","2 a 3","+3"])
    df_selecao['fx_qtd_contratos_aberto_atraso']=pd.cut(df_selecao.qtd_contratos_aberto_atraso,bins=[-0.99,0,1,3,np.inf],labels=["0","1","2 a 3","+3"])
    df_selecao['fx_reneg_fechado_regular']=pd.cut(df_selecao.qtd_reneg_fechado_regular,bins=[-0.99,0,1,3,np.inf],labels=["0","1","2 a 3","+3"])
    df_selecao['fx_qtd_reneg_fechado_atraso']=pd.cut(df_selecao.qtd_reneg_fechado_atraso,bins=[-0.99,0,1,3,np.inf],labels=["0","1","2 a 3","+3"])
    df_selecao['fx_reneg_aberto_regular']=pd.cut(df_selecao.qtd_reneg_aberto_regular,bins=[-0.99,0,1,3,np.inf],labels=["0","1","2 a 3","+3"])
    df_selecao['fx_qtd_reneg_aberto_atraso']=pd.cut(df_selecao.qtd_reneg_aberto_atraso,bins=[-0.99,0,1,3,np.inf],labels=["0","1","2 a 3","+3"])
    df_selecao['med_meses_entre_contratos']=pd.cut(df_selecao.media_meses_entre_contratos_combinado,bins=[-0.99,0,1,2,3,4,5,6,9,12,np.inf],labels=["0","Até 1","2","3","4","5","6","7 a 9", "10 a 12","12+"])
    #df_selecao['med_meses_entre_contratos_reneg']=pd.cut(df_selecao.media_meses_entre_contratos_reneg,bins=[-0.99,0,1,2,3,4,5,6,9,12,np.inf],labels=["0","Até 1","2","3","4","5","6","7 a 9", "10 a 12","12+"])
    df_selecao['fx_qtd_parcelas_pagas']=pd.cut(df_selecao.qtd_parcelas_pagas,bins=[-0.99,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,30,50,100,np.inf],labels=["0","1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21 a 30","31 a 50","51 a 100", "Acima 100"])
    df_selecao['fx_qtd_parcelas_pagas_nr']=pd.cut(df_selecao.qtd_parcelas_pagas_nr,bins=[-0.99,0,5,10,15,20,30,50,100,np.inf],labels=["0","1-5","6-10","11-15","16-20","21 a 30","31 a 50","51 a 100", "Acima 100"])
    df_selecao['fx_qtd_parcelas_abertas']=pd.cut(df_selecao.qtd_parcelas_aberta,bins=[-0.99,0,10,20,50,np.inf],labels=["0","Até 10","11 a 20","21 a 50", "Acima 50"])
    df_selecao['fx_principal_total']=pd.cut(df_selecao.principal_total,bins=[-0.99,0,1000,2500,5000,7500,10000,15000,20000,np.inf],labels=["Sem_Valor","Até R$1 mil","R$1 mil a R$2,5 mil","R$2,5 mil a R$5 mil","R$5 mil a R$7,5 mil","R$7,5 mil a R$10mil","R$10 mil a R$15mil","R$15 mil a R$20mil","Acima de R$20mil"])
    df_selecao["fx_valor_pago_nr"]=pd.cut(df_selecao.valor_pago_nr,bins=[-0.99,0,2000,5000,10000,20000,np.inf],labels=["0","Até R$2 mil","R$2 mil a R$5mil","R$5 mil a R$10mil","R$10 mil a R$20mil","Acima de R$20mil"])
    df_selecao["fx_principal_total_nr"]=pd.cut(df_selecao.valor_principal_total_nr,bins=[-0.99,0,2000,5000,10000,20000,np.inf],labels=["0","Até R$2 mil","R$2 mil a R$5mil","R$5 mil a R$10mil","R$10 mil a R$20mil","Acima de R$20mil"])
    df_selecao['fx_principal_total_fechado']=pd.cut(df_selecao.principal_total_fechado,bins=[-0.99,0,1000,2000,3000,5000,10000,np.inf],labels=["0","Até R$1 mil","R$1 mil a R$2 mil","R$2 mil a R$3mil","R$3 mil a R$4mil","R$5 mil a R$10mil","Acima de R$10mil"])
    df_selecao['fx_principal_total_aberto']=pd.cut(df_selecao.principal_total_aberto,bins=[-0.99,0,1000,2000,3000,5000,10000,np.inf],labels=["0","Até R$1 mil","R$1 mil a R$2 mil","R$2 mil a R$3mil","R$3 mil a R$4mil","R$5 mil a R$10mil","Acima de R$10mil"])
    df_selecao['fx_creditos_a_vencer']=pd.cut(df_selecao.creditos_a_vencer,bins=[-0.99,0,1000,2000,3000,5000,np.inf],labels=["0","Até R$1 mil","R$1 mil a R$2 mil","R$2 mil a R$3mil","R$3 mil a R$5mil","Acima de R$5mil"])
    df_selecao['fx_creditos_vencidos']=pd.cut(df_selecao.creditos_vencidos,bins=[-0.99,0,1000,2000,3000,5000,np.inf],labels=["0","Até R$1 mil","R$1 mil a R$2 mil","R$2 mil a R$3mil","R$3 mil a R$5mil","Acima de R$5mil"])
    df_selecao['fx_ratio_contratos_atraso']=pd.cut(df_selecao.ratio_contratos_atraso,bins=[-0.99,0,0.05,.1,.2,.4,.6,.8,.9,np.inf],labels=["0","Até 0.05","0.05 a 0.1","0.1 a 0.2","0.2 a 0.4","0.4 a 0.6","0.6 a 0.8","0.8 a 0.9","0.9 a 1"])
    df_selecao['fx_freq_atraso']=pd.cut(df_selecao.freq_atraso,bins=[-0.99,0,0.05,0.1,0.2,0.5,1,3,10,np.inf],labels=["0","Até 0.05","Até 0.1","Até 0.2","Até 0.5","0.5 a 1","1 a 3","3 a 10","Acima de 10"])
    df_selecao['fx_exposicao_ratio']=pd.cut(df_selecao.exposicao_ratio,bins=[-0.99,0,.1,.2,.4,.6,.8,.9,np.inf],labels=["0","Até 0.1","0.1 a 0.2","0.2 a 0.4","0.4 a 0.6","0.6 a 0.8","0.8 a 0.9","0.9 a 1"])
    df_selecao['fx_indice_instabilidade']=pd.cut(df_selecao.indice_instabilidade,bins=[-0.99,0,5,10,15,20,40,60,np.inf],labels=["0","Até 5","5 a 10","10 a 15","15 a 20","20 a 40","40 a 60","Acima de 60"])
    df_selecao['fx_indice_regularidade']=pd.cut(df_selecao.indice_regularidade,bins=[-0.99,0,.3,.4,.6,.8,0.99999999,1.01],labels=["0","Até 0.3","0.3 a 0.4","0.4 a 0.6","0.6 a 0.8","0.8 a 0.99","1"])
    df_selecao['fx_prop_reneg']=pd.cut(df_selecao.prop_reneg,bins=[-0.99,0,.1,.3,.4,.7,1.01],labels=["0","Até 0.1","0.1 a 0.3","0.3 a 0.4","0.4 a 0.7","Acima de 0.7"])
    df_selecao['fx_reneg_severity']=pd.cut(df_selecao.reneg_severity,bins=[-0.99,0,.1,.3,.4,.7,1.01],labels=["0","Até 0.1","0.1 a 0.3","0.3 a 0.4","0.4 a 0.7","Acima de 0.7"])
    df_selecao['fx_reneg_vs_liq_ratio']=pd.cut(df_selecao.reneg_vs_liq_ratio,bins=[-0.99,0,.1,.5,1,np.inf],labels=["0","Até 0.1","0.1 a 0.5","0.5 a 1","Acima de 1"])
    df_selecao['fx_reneg_vs_liq_ratio_ponderado']=pd.cut(df_selecao.reneg_vs_liq_ratio_ponderado,bins=[-0.99,0,.1,.5,1,np.inf],labels=["0","Até 0.1","0.1 a 0.5","0.5 a 1","Acima de 1"])
    df_selecao['fx_tempo_ultimo_pagamento_pond']=pd.cut(df_selecao.tempo_ultimo_pagamento_pond,bins=[-0.99,0,1,5,12,24,36,48,60,120,np.inf],labels=["0","1","1 a 5","5 a 12","12 a 24", "24 a 36","36 a 48","48 a 60", "60 a 120", "Acima de 120"])

    variaveis = df_selecao.select_dtypes(include=["category", "object"]).columns.tolist()

    var_escolhida = st.selectbox("Selecione a variável para visualizar:", variaveis)
    # Conta ocorrências da variável escolhida
    counts = df_selecao[var_escolhida].value_counts().reset_index()
    counts.columns = [var_escolhida, "count"]

    # Mostra gráfico
    st.subheader("Gráfico de frequência:")

    chart = alt.Chart(counts).mark_bar().encode(
        x=alt.X(f'{var_escolhida}:N', title=var_escolhida),
        y=alt.Y('count:Q', title='Quantidade')
    ).properties(
        width=600,   # largura
        height=400   # altura
        )
    
    # Cria 3 colunas, coloca o gráfico na do meio
    col1, col2, col3 = st.columns([1, 2, 1])  # largura relativa
    with col2:
        st.altair_chart(chart, use_container_width=False)

    # ===========================================================
    #    Distribuição das variáveis com a variável alvo
    # ===========================================================
    st.subheader("Tabela cruzada com variável target (inad_e_reneg):")
    st.write(""" 1 = Indica que possui algum contrato com mais de 60 dias de atraso ou com renegociação em aberto (Mau pagador)        
                 0 = Indica que é adimplente (Bom pagador)""")
    # Tabela cruzada com totais
    ct = pd.crosstab(df_selecao[var_escolhida], df_selecao["inad_e_reneg"], margins=True, margins_name="Total")

    #Percentual por linha (sem incluir a linha Total)
    ct_percent = pd.crosstab(df_selecao[var_escolhida], df_selecao["inad_e_reneg"],margins=True,margins_name="Total", normalize="index") * 100
    ct_percent = ct_percent.round(2)

    # Combinar totais e percentuais
    ct_combined = ct.copy()

    for col in df_selecao["inad_e_reneg"].unique():
        ct_combined[f"{col} %"] = ct_percent[col]

    #st.write(ct_combined)

    # Paleta de cores
    cm = sns.light_palette("green", as_cmap=True)

    
    # Criar uma cópia sem a última linha
    subset_df = ct_combined.iloc[:-1]

    ct_styled = ct_combined.style.format("{:.2f}")
    ct_styled = ct_styled.background_gradient(cmap=cm, subset=pd.IndexSlice[subset_df.index, ['1 %']])
    ct_styled = ct_styled.background_gradient(cmap=cm, subset=pd.IndexSlice[subset_df.index, ['0 %']])

    # Mostrar no Streamlit
    st.dataframe(ct_styled)

    # ===========================================================
    #    Gráfico variáveis com a variável alvo
    # ===========================================================

    # Crosstab
    tab_cruz_sem_total = pd.crosstab(
        df_selecao[var_escolhida],
        df_selecao["inad_e_reneg"],
        normalize="index"   # <- percentual por linha
    ).reset_index()

    # Formato longo (necessário p/ Altair)
    tab_long = tab_cruz_sem_total.melt(
        id_vars=var_escolhida,
        var_name="inad_e_reneg",
        value_name="frequencia"
    )

    # Gráfico de barras lado a lado
    chart = (
        alt.Chart(tab_long)
        .mark_bar()
        .encode(
            x=alt.X(f"{var_escolhida}:N", title=var_escolhida),
            y=alt.Y("frequencia:Q", title="Frequência"),
            color="inad_e_reneg:N",
            xOffset="inad_e_reneg:N"   # <- deixa lado a lado
        )
    )

    st.subheader("Gráfico de frequencia por inad_e_reneg:")
    st.altair_chart(chart, use_container_width=True)
################################################################################################    
with aba11:
    st.title("Análise Exploratória (EDA)")

    var_escolhida = st.selectbox("Selecione a variável Linha :", variaveis)
    # Seleciona a variável da coluna, removendo a já escolhida
    opcoes_coluna = [v for v in variaveis if v != var_escolhida]
    var_escolhida_2 = st.selectbox("Selecione a variável Coluna:", opcoes_coluna)

    # ===========================================================
    #    Filtros por categoria
    # ===========================================================
    categorias_linha = df_selecao[var_escolhida].dropna().unique()
    filtro_linha = st.multiselect(
        f"Filtrar categorias de {var_escolhida}:",
        options=sorted(categorias_linha),
        default=sorted(categorias_linha)
    )

    categorias_coluna = df_selecao[var_escolhida_2].dropna().unique()
    filtro_coluna = st.multiselect(
        f"Filtrar categorias de {var_escolhida_2}:",
        options=sorted(categorias_coluna),
        default=sorted(categorias_coluna)
    )

    # Aplica filtros
    df_filtrado = df_selecao[
        df_selecao[var_escolhida].isin(filtro_linha) &
        df_selecao[var_escolhida_2].isin(filtro_coluna)
    ]

    # ===========================================================
    #    Tabela de contingência
    # ===========================================================
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

    # Combina totais e percentuais
    ct_combined = ct.copy()
    for col in df_filtrado[var_escolhida_2].unique():
        ct_combined[f"{col} %"] = ct_percent[col]

    st.write(ct_combined)

    # ===========================================================
    #    Gráfico de frequência
    # ===========================================================
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
        dy=-8,  # posição acima da barra
        dx=24,
        size=16
        ).encode(
            text=alt.Text('frequencia:Q', format='.2%')
            )

    st.subheader(f"Gráfico de frequência {var_escolhida} vs {var_escolhida_2}:")
    st.altair_chart(chart+text, use_container_width=True)
    

with aba2:
    st.title("Relatório")
    # ==============================
    # Relatório
    # ==============================
    relatorio_view = relatorio

    # Entrada do CPF
    cpf_input = st.text_input("Digite o CPF:")

    # Filtro
    if cpf_input:
        try:
            cpf_num = int(cpf_input)  # converte a entrada para número inteiro
            relatorio_filtrado = relatorio_view[relatorio_view["cpf_cnpj"] == cpf_num]
            relatorio_filtrado_shap = relatorio_shap[relatorio_shap["cpf_cnpj"] == cpf_num]
            #st.write("Relatório Behavior")
            st.dataframe(relatorio_filtrado)
            st.write("Relatório Shap")
            st.dataframe(relatorio_filtrado_shap)
            import plotly.express as px
            # Colunas Shap
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

            # (.mean() simples se quiser manter o sinal)
            df_shap = relatorio_filtrado_shap[cols_shap].mean().sort_values(ascending=True)

            # DataFrame para plotagem
            df_plot = pd.DataFrame({
                "Feature": df_shap.index,
                "SHAP value": df_shap.values
            })

            # Gráfico interativo com Plotly
            fig = px.bar(
                df_plot,
                x="SHAP value",
                y="Feature",
                orientation="h",
                color="SHAP value",                     # <–– usa o próprio valor para colorir
                color_continuous_scale="RdBu_r",        # <–– azul = negativo, vermelho = positivo
                range_color=[-abs(df_plot["SHAP value"]).max(), abs(df_plot["SHAP value"]).max()],
                title="Importância média dos valores SHAP",
            )

            fig.update_layout(
                yaxis=dict(title="Variável"),
                xaxis=dict(title="Valor do SHAP"),
                template="simple_white",
                height=500
            )

            # Mostrar no Streamlit
            st.plotly_chart(fig, use_container_width=True)
        except ValueError:
            st.error("Digite apenas números válidos para o CPF.")
    else:
        #st.write("Relatório Behavior")
        st.dataframe(relatorio_view)
        st.write(''' # Relatório Shap ''')
        st.write(''' Digite o CPF para visualizar relatório SHAP.''')

with aba3:
    st.title("Indicadores")
    # ==============================
    # Indicadores
    # ==============================
    st.subheader("Evolução dos Indicadores")
    st.dataframe(indicadores)

    # Seleção do indicador
    indicador = st.selectbox("Escolha o indicador", indicadores.columns[4:])
    # Plotando a série temporal
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(indicadores['INDICE'], indicadores[indicador], marker='o')
    ax.set_xlabel("Índice")
    ax.set_ylabel(indicador)
    ax.set_title(f"Série Temporal de {indicador}")
    ax.legend()
    ax.grid(True)
    plt.xticks(rotation=45)
    st.pyplot(fig)
   