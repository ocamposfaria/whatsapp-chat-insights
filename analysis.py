import polars as pl
import plotly.express as px

# Função para filtrar mensagens relacionadas ao "covid" e suas variações
def filter_covid_messages(df):
    covid_keywords = ["covid", "covid-19", "corona vírus", "coronavírus", "corona"]
    covid_df = df.filter(
        pl.col("message").str.contains("|".join(covid_keywords), case=False)
    )
    return covid_df

# Função para criar um gráfico de linha com o Plotly
def create_covid_trend_chart(covid_df):
    # Contando o número de mensagens por dia
    covid_df = covid_df.with_column(pl.col("timestamp").dt.truncate("1d").alias("date"))
    daily_count = covid_df.groupby("date").agg(pl.count("message").alias("count"))

    # Criando o gráfico de linha
    fig = px.line(
        daily_count.to_pandas(),  # Convertendo para pandas para usar com Plotly
        x="date",
        y="count",
        title="Número de mensagens relacionadas ao COVID-19 ao longo do tempo",
        labels={"date": "Data", "count": "Quantidade de Mensagens"},
    )

    fig.show()

# Processar o chat e obter o DataFrame
df = process_chat(file_path)

# Filtrar as mensagens relacionadas ao "covid"
covid_df = filter_covid_messages(df)

# Criar o gráfico de linha
create_covid_trend_chart(covid_df)
