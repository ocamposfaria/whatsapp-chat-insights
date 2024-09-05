import pandas as pd
import re
import plotly.express as px
import streamlit as st
from collections import Counter
import emoji

st.set_page_config(layout="wide")

def parse_message(line):
    # Tentando combinar com dois padrões diferentes de timestamp
    pattern = r'^\[(\d{1,2}/\d{1,2}/\d{4})([,\s]) (\d{2}:\d{2}:\d{2})\] (.*?): (.*)'
    match = re.match(pattern, line)
    if match:
        date_part = match.group(1)
        time_part = match.group(3)
        timestamp = f"{date_part} {time_part}"
        author = match.group(4)
        message = match.group(5)
        return timestamp, author, message
    return None, None, None

def is_system_event(message):
    # Detectar mensagens de eventos de sistema como "criou este grupo" ou "protegidas com a criptografia"
    system_events = [
        "criou este grupo", 
        "mudou o nome do grupo para", 
        "mudou a descrição do grupo", 
        "mudou a imagem do grupo",
        "são protegidas com a criptografia de ponta a ponta",
        "foi adicionado(a)",
        "‎"
    ]
    return any(event in message.lower() for event in system_events)

def process_chat(file):
    data = {"timestamp": [], "author": [], "message": []}

    for line in file:
        line = line.decode('utf-8').strip()

        if not line:
            continue
        
        # Separar timestamp, autor e mensagem usando parse_message
        timestamp, author, message = parse_message(line)
        
        if timestamp is None:
            # Mensagens sem autor, podem ser continuação de mensagem anterior
            if len(data["message"]) > 0:
                # Verifica se a linha faz parte de uma pesquisa ou similar
                if line.startswith("[") and ":" in line:
                    data["message"][-1] += f" {line}"
                else:
                    # Caso seja continuação normal de texto
                    data["message"][-1] += f" {line}"
            continue
        
        # Ignorar eventos de sistema
        if is_system_event(message):
            continue
        
        # Ignorar mensagens contendo "figurinha omitida"
        if "figurinha omitida" in message.lower():
            continue
        
        # Adicionar dados extraídos ao DataFrame
        data["timestamp"].append(timestamp)
        data["author"].append(author)
        data["message"].append(message)
    
    # Criação do DataFrame do Pandas
    df = pd.DataFrame(data)
    
    # Convertendo a coluna 'timestamp' para o tipo datetime
    try:
        df['timestamp'] = pd.to_datetime(df['timestamp'], format="%d/%m/%Y %H:%M:%S")
    except ValueError:
        df['timestamp'] = pd.to_datetime(df['timestamp'], format="%d/%m/%Y, %H:%M:%S")
    
    # Filtrar mensagens com conteúdo indesejado novamente, se necessário
    df = df[~df['message'].str.contains("figurinha omitida", case=False, na=False)]
    df = df[~df['author'].str.contains("você", case=False, na=False)]

    return df

def filter_covid_messages(df):
    covid_keywords = [
    "covid", "covid-19", "corona vírus", "coronavírus",
    "pandemia", "quarentena", "isolamento social", "lockdown",
    "distanciamento social", "máscara",
    "PCR", "variante", "OMS",
    "organização mundial da saúde", "OMS", 
    "UTI", "tratamento", "ventilação mecânica",
    "febre", "tosse", "falta de ar", "perda de olfato", 
    "paladar", "sars-cov-2", "epidemia"
]
    covid_df = df[df['message'].str.contains('|'.join(covid_keywords), case=False, na=False)]
    return covid_df

# Função para criar um gráfico de linha com o Plotly
def create_covid_trend_chart(covid_df):
    # Convertendo a coluna 'timestamp' para o formato 'yyyy-mm'
    covid_df['year_month'] = covid_df['timestamp'].dt.to_period('M').dt.to_timestamp()

    # Contando o número de mensagens por mês
    monthly_count = covid_df.groupby('year_month').size().reset_index(name='count')

    # Criando o gráfico de linha
    fig = px.line(
        monthly_count,
        x='year_month',
        y='count',
        # title='Quantidade de mensagens relacionadas à COVID-19 ao longo do tempo',
        labels={'year_month': 'Ano-Mês', 'count': 'Quantidade de Mensagens'},
    )

    return fig

def create_trend_chart(df):
    # Convertendo a coluna 'timestamp' para o formato 'yyyy-mm'
    df['year_month'] = df['timestamp'].dt.to_period('M').dt.to_timestamp()

    # Contando o número de mensagens por mês
    monthly_count = df.groupby('year_month').size().reset_index(name='count')

    # Criando o gráfico de dispersão com linha de tendência
    fig = px.scatter(
        monthly_count,
        x='year_month',
        y='count',
        # title='Quantidade de mensagens ao longo do tempo',
        labels={'year_month': 'Ano-Mês', 'count': 'Quantidade de Mensagens'},
        trendline='ols'  # Adicionando a linha de tendência
    )

    # Convertendo para um gráfico de linha
    fig.update_traces(mode='lines+markers')

    return fig

def create_day_of_week_chart(df):
    df['day_of_week'] = df['timestamp'].dt.day_name()
    day_count = df.groupby('day_of_week').size().reset_index(name='count')
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_count['day_of_week'] = pd.Categorical(day_count['day_of_week'], categories=day_order, ordered=True)
    day_count = day_count.sort_values('day_of_week')

    fig = px.bar(
        day_count,
        x='day_of_week',
        y='count',
        labels={'day_of_week': 'Dia da Semana', 'count': 'Quantidade de Mensagens'},
        # title='Quantidade de mensagens por dia da semana'
    )
    return fig

def create_author_chart(df):
    author_count = df.groupby('author').size().reset_index(name='count').sort_values(by='count', ascending=False)

    fig = px.bar(
        author_count,
        x='author',
        y='count',
        labels={'author': 'Autor', 'count': 'Quantidade de Mensagens'},
        # title='Quantidade de mensagens por autor'
    )
    return fig

def find_longest_message(df):
    # Encontra a mensagem com o maior número de caracteres
    df['message_length'] = df['message'].str.len()
    longest_message_row = df.loc[df['message_length'].idxmax()]
    return longest_message_row['author'], longest_message_row['message']

def count_messages(df):
    return len(df)

def extract_emojis(text):
    return [char for char in text if char in emoji.EMOJI_DATA]

def is_valid_emoji(emoji_char):
    # Verifica se o caractere é um emoji válido
    return emoji_char in emoji.EMOJI_DATA

def get_emoji_name(emoji_char):
    # Obtém o nome do emoji
    return emoji.demojize(emoji_char).replace(":", "").replace("_", " ").title()

def get_emoji_list(df):
    # Extrair todos os emojis das mensagens
    all_emojis = []
    for message in df['message']:
        all_emojis.extend(extract_emojis(message))
    
    # Filtrar apenas emojis válidos
    valid_emojis = [e for e in all_emojis if is_valid_emoji(e)]
    
    # Contar a frequência de cada emoji
    emoji_counts = Counter(valid_emojis)
    
    # Ordenar emojis pelo número de ocorrências (do mais usado para o menos usado)
    sorted_emojis = [emoji for emoji, count in emoji_counts.most_common()]
    
    return sorted_emojis

def filter_profanity_messages(df):
    profanity_keywords = [
        "caralho", "porra", "fude", "foder", "fuder",
        "puta que pariu", "filho da puta", "tomar no cu",
        "merda", "desgraça", "bosta", "arrombado",
        "crlh", "pqp", "vsf", "corno",
        "maldito", "cacete"
    ]
    
    profanity_df = df[df['message'].str.contains('|'.join(profanity_keywords), case=False, na=False)]
    return profanity_df

def create_profanity_chart(profanity_df):
    author_profanity_count = profanity_df.groupby('author').size().reset_index(name='count').sort_values(by='count', ascending=False)

    fig = px.bar(
        author_profanity_count,
        x='author',
        y='count',
        labels={'author': 'Autor', 'count': 'Quantidade de Palavrões'},
        # title='Quantidade de Palavrões por Autor'
    )
    return fig

def create_profanity_ratio_chart(df, profanity_df):
    # Contagem de mensagens por autor
    author_message_count = df.groupby('author').size().reset_index(name='message_count')
    
    # Contagem de palavrões por autor
    author_profanity_count = profanity_df.groupby('author').size().reset_index(name='profanity_count')
    
    # Mesclar os dois dataframes
    merged_df = pd.merge(author_message_count, author_profanity_count, on='author', how='left')
    
    # Substituir NaN por 0 (caso algum autor não tenha palavrões)
    merged_df['profanity_count'] = merged_df['profanity_count'].fillna(0)
    
    # Calcular a razão de palavrões por mensagem
    merged_df['profanity_ratio'] = merged_df['profanity_count'] / merged_df['message_count']
    
    # Ordenar os autores pela razão de palavrões
    merged_df = merged_df.sort_values(by='profanity_ratio', ascending=False)

    # Criar o gráfico
    fig = px.bar(
        merged_df,
        x='author',
        y='profanity_ratio',
        labels={'author': 'Autor', 'profanity_ratio': 'Razão de Palavrões/Mensagens'},
        # title='Razão de Palavrões por Mensagem por Autor'
    )
    
    return fig


def list_most_common_profanities(profanity_df):
    profanity_keywords = [
        "caralho", "porra", "foder", "fuder",
        "puta que pariu", "filho da puta", "tomar no cu",
        "merda", "desgraça", " cu", "bosta", "arrombado",
        "crlh", "pqp", "vsf",
        "maldito", "cacete"
    ]

    profanity_count = profanity_df['message'].str.extractall(f"({'|'.join(profanity_keywords)})")[0].value_counts()
    return profanity_count



st.title('Análise de Mensagens do Grupo de WhatsApp')

st.markdown('##### Como usar?')
st.markdown('Exporte a conversa de um grupo de WhatsApp, extraia o arquivo e suba o _chat.txt aqui!')

uploaded_file = st.file_uploader("Choose a file")
if uploaded_file is not None:

    lines = uploaded_file.readlines()

    df = process_chat(lines)
    
    covid_df = filter_covid_messages(df)
    
    fig_covid_trend = create_covid_trend_chart(covid_df)

    fig_trend = create_trend_chart(df)
    
    fig_day_of_week = create_day_of_week_chart(df)
    
    fig_author = create_author_chart(df)
    
    st.subheader("Quantidade de mensagens ao longo do tempo")
    st.plotly_chart(fig_trend)

    st.subheader("Quantidade de mensagens relacionadas à COVID-19 ao longo do tempo")
    st.plotly_chart(fig_covid_trend)

    st.subheader("Quantidade de mensagens por dia da semana")
    st.plotly_chart(fig_day_of_week)

    st.subheader("Quantidade de mensagens por autor")
    st.plotly_chart(fig_author)


    # Análise de palavrões
    profanity_df = filter_profanity_messages(df)
    fig_profanity = create_profanity_chart(profanity_df)
    fig_profanity_ratio = create_profanity_ratio_chart(df, profanity_df)

    st.subheader("Quantidade de palavrões por autor")
    st.plotly_chart(fig_profanity)

    st.subheader("Razão entre quantidade palavrões e quantidade de mensagens por autor")
    st.plotly_chart(fig_profanity_ratio)
    
    # Mostrar o autor que mais fala palavrões
    top_profanity_author = profanity_df['author'].value_counts().idxmax()
    top_profanity_count = profanity_df['author'].value_counts().max()
    st.subheader("Autor que mais fala palavrões")

    with st.expander(label='Clique aqui para exibir', expanded=False):
        st.write(f"**Autor:** {top_profanity_author}")
        st.write(f"**Quantidade de palavrões:** {top_profanity_count}")

    # Listar palavrões mais falados
    most_common_profanities = list_most_common_profanities(profanity_df)
    st.subheader("Palavrões mais falados")
    # Supondo que 'most_common_profanities' seja um dicionário com palavrões como chaves e contagens como valores
    most_common_profanities = list_most_common_profanities(profanity_df)

    # Convertendo o dicionário para um DataFrame
    profanities_df = pd.DataFrame(list(most_common_profanities.items()), columns=["Palavrão", "Quantidade"])

    col01, col02 = st.columns(2)

    with col01:

        # Exibindo o DataFrame no Streamlit
        profanities_df.index = profanities_df.index + 1
        st.dataframe(profanities_df, use_container_width=True)

    # Encontra e exibe a maior mensagem em quantidade de caracteres
    author, longest_message = find_longest_message(df)
    st.subheader("Maior mensagem já enviada")
    with st.expander(label='Clique aqui para exibir', expanded=False):
        st.write(f"**Autor:** {author}")
        st.write(f"**Mensagem:** {longest_message}")

    # Exibir a quantidade total de mensagens
    total_messages = count_messages(df)
    st.subheader("Quantidade total de mensagens")
    with st.expander(label='Clique aqui para exibir', expanded=False):
        st.write(f"**Total de Mensagens:** {total_messages:,}")

    # Exibir os emojis mais usados e seus nomes
    sorted_emojis = get_emoji_list(df)
    st.subheader("Top 10 emojis mais usados")

    with st.expander(label='Clique aqui para exibir', expanded=False):

        col1, col2, col3, col4, col5, col6, col7, col8, col9, col10 = st.columns(10)
        columns = [col1, col2, col3, col4, col5, col6, col7, col8, col9, col10]

        # Contador para controlar as colunas
        column_index = 0

        for emoji_char in sorted_emojis:
            emoji_name = get_emoji_name(emoji_char)
            if "skin tone" not in emoji_name.lower():
                columns[column_index].markdown(f"## {emoji_char}")
                column_index += 1
                # Se atingiu o número máximo de colunas, sair do loop
                if column_index >= 10:
                    break
