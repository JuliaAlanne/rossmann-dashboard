import streamlit as st
import pandas as pd
import plotly.express as px

# Carregar os dados
@st.cache_data
def load_data():
    df_train = pd.read_csv("train.csv", parse_dates=['Date'])
    df_store =  pd.read_csv("store.csv")
    df = pd.merge(df_train, df_store, on="Store", how="left")
    return df

df = load_data()

# Título do app
st.title("📊 Dashboard de Vendas - Rossmann")

# Criar abas
aba_vendas, aba_lojas, aba_correlacao = st.tabs(["📈 Vendas", "🏪 Lojas", "🔗 Vendas vs Lojas"])

# Pré-processamento
df['Year'] = df['Date'].dt.year
df['Month'] = df['Date'].dt.month
df['Day'] = df['Date'].dt.day

# --- Aba de Vendas ---
with aba_vendas:
    st.header("Análise de Vendas")

    lojas = df['Store'].unique()
    loja_selecionada = st.selectbox("🏪 Selecione uma loja", options=sorted(lojas))

    dias_semana = sorted(df['DayOfWeek'].unique())
    selected_days = st.multiselect("📅 Dias da Semana", dias_semana, default=dias_semana)

    min_data = df["Date"].min().date()
    max_data = df["Date"].max().date()
    intervalo_datas = st.date_input("📅 Intervalo de Datas", [min_data, max_data])

    # Filtrar dados
    df_filtrado = df[
        (df["Store"] == loja_selecionada) &
        (df["DayOfWeek"].isin(selected_days)) &
        (df["Date"].dt.date.between(intervalo_datas[0], intervalo_datas[1]))
    ]

    # KPIs
    st.subheader("📌 Resumo de Vendas")
    st.metric("💰 Vendas Totais no Período", f"€ {df_filtrado['Sales'].sum():,.2f}")
    st.metric("📈 Média de Vendas Diárias", f"€ {df_filtrado['Sales'].mean():,.2f}")

    # Vendas por mês
    df_filtrado["AnoMes"] = df_filtrado["Date"].dt.to_period("M").astype(str)
    vendas_mes = df_filtrado.groupby("AnoMes")["Sales"].sum().reset_index()

    st.subheader("🗓️ Vendas por Mês")
    st.line_chart(vendas_mes.set_index("AnoMes"))

    # Vendas por Dia (detalhado)
    st.subheader("📅 Vendas Diárias")
    st.bar_chart(df_filtrado.set_index("Date")["Sales"])

    # Gráfico interativo de vendas por dia (Plotly)
    fig_vendas = px.line(
        df_filtrado, x='Date', y='Sales', color=px.Constant(f'Loja {loja_selecionada}'),
        title='Vendas Diárias da Loja Selecionada',
        labels={'Sales': 'Vendas', 'Date': 'Data'}
    )
    st.plotly_chart(fig_vendas, use_container_width=True)

    # Impacto de promoções
    promo_impacto = df_filtrado.groupby('Promo')['Sales'].mean().reset_index()
    promo_impacto['Promo'] = promo_impacto['Promo'].map({0: 'Sem Promoção', 1: 'Com Promoção'})

    fig_promo = px.bar(
        promo_impacto, x='Promo', y='Sales',
        title='Impacto das Promoções na Média de Vendas',
        labels={'Sales': 'Média de Vendas'}
    )
    st.plotly_chart(fig_promo, use_container_width=True)

# --- Aba de Lojas ---
with aba_lojas:
    st.header("Análise por Loja")

    selected_stores_lojas = st.multiselect("Selecione as lojas", lojas, default=list(lojas[:2]), key="lojas_aba2")
    df_lojas = df[df['Store'].isin(selected_stores_lojas)]

    # Média de clientes por dia
    media_clientes_dia = df_lojas.groupby('Date')['Customers'].mean().reset_index()
    fig_clientes_dia = px.line(
        media_clientes_dia, x='Date', y='Customers',
        title='📅 Média de Clientes por Dia'
    )
    st.plotly_chart(fig_clientes_dia, use_container_width=True)

    # Média de clientes por mês (considerando ano e mês)
    df_lojas['AnoMes'] = df_lojas['Date'].dt.to_period('M').astype(str)
    media_clientes_mes = df_lojas.groupby('AnoMes')['Customers'].mean().reset_index()
    fig_clientes_mes = px.bar(
        media_clientes_mes, x='AnoMes', y='Customers',
        title='📆 Média de Clientes por Mês'
    )
    st.plotly_chart(fig_clientes_mes, use_container_width=True)
# --- Aba de Correlação Vendas x Lojas ---
with aba_correlacao:
    st.header("Vendas em Relação às Características das Lojas")
    st.markdown("""
    **Ticket Médio** representa o valor médio gasto por cliente em uma loja.
    Ele é calculado pela fórmula:

    **Ticket Médio = Vendas Totais / Número de Clientes**

    Essa métrica ajuda a entender a eficiência de vendas de cada loja.
    Uma loja com ticket médio alto indica que, mesmo com menos clientes, os consumidores estão comprando mais por visita.
    """)
    # Vendas por tipo de loja
    vendas_tipo = df.groupby("StoreType")["Sales"].mean().reset_index()
    fig_tipo = px.bar(vendas_tipo, x="StoreType", y="Sales", title="Média de Vendas por Tipo de Loja")
    st.plotly_chart(fig_tipo, use_container_width=True)

    # Vendas vs Promoções prolongadas
    st.subheader("⏱️ Tempo de Promoção (Promo2) e Vendas")
    df_promo2 = df[df["Promo2"] == 1].copy()
    df_promo2["Promo2Since"] = df_promo2["Promo2SinceWeek"].fillna(0) + df_promo2["Promo2SinceYear"].fillna(0)
    fig_promo2 = px.scatter(df_promo2, x="Promo2SinceYear", y="Sales", title="Vendas vs Ano de Início da Promoção 2")
    st.plotly_chart(fig_promo2, use_container_width=True)

    # Clientes x Vendas (eficiência)
    st.subheader("👥 Clientes vs Vendas")
    fig_ticket = px.scatter(
        df, x="Customers", y="Sales",
        title="Correlação entre Clientes e Vendas"
    )
    st.plotly_chart(fig_ticket, use_container_width=True)

    # Ticket médio por loja (TOP 10)
    st.subheader("🏆 TOP 10 Lojas com Maior Ticket Médio")
    st.markdown("""
    O **Ticket Médio** representa o valor médio gasto por cliente em uma loja.
    
    **Ticket Médio = Vendas Totais / Número de Clientes**

    Essa métrica ajuda a entender a eficiência de vendas de cada loja.
    Uma loja com ticket médio alto indica que, mesmo com menos clientes, os consumidores estão comprando mais por visita. """
    )
    ticket_medio = df.groupby("Store")[["Sales", "Customers"]].sum().reset_index()
    ticket_medio["TicketMedio"] = ticket_medio["Sales"] / ticket_medio["Customers"]
    top_lojas = ticket_medio.sort_values(by="TicketMedio", ascending=False).head(10)

    fig_ticket_top = px.bar(top_lojas, x="Store", y="TicketMedio", title="Top 10 Lojas - Ticket Médio")
    st.plotly_chart(fig_ticket_top, use_container_width=True)
