from urlextract import URLExtract
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
from collections import Counter
import emoji
import streamlit as st

extract = URLExtract()

# Cache stopwords loading
@st.cache_data
def _load_stopwords():
    with open('stop_hinglish.txt', 'r', encoding='utf-8') as f:
        return set(f.read().split())


# ---------------------- USER STATS ----------------------
def user_stats(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user].copy()

    num_messages = df.shape[0]

    # total words - vectorized
    words = df['message'].str.split().explode()
    num_words = words.shape[0]

    # total media - vectorized
    num_media_messages = (df['message'] == '<Media omitted>\n').sum()

    # total links - optimized
    extractor = URLExtract()
    all_messages = ' '.join(df['message'].astype(str))
    links = extractor.find_urls(all_messages)

    return num_messages, num_words, num_media_messages, len(links)


# ---------------------- MOST BUSY USERS CHART ----------------------
def most_busy_person(df):

    s = df[df['user'] != "group_notification"]['user'].value_counts().head()

    data = pd.DataFrame({"user": s.index, "count": s.values})

    fig = px.bar(
        data,
        x="user",
        y="count",
        text="count",
        title="Top 5 Most Active Users"
    )

    fig.update_traces(textposition="outside", marker=dict(color="#7BA4FF"))
    fig.update_layout(template="plotly_dark", title_x=0.5)

    df = round((df['user'].value_counts() / df.shape[0]) * 100, 2).reset_index().rename(
    columns={'index': 'name', 'user': 'percent'})
    return fig,df

def wordcloud(selected_user, df):
    # Load stopwords from cache
    stop_words = _load_stopwords()

    # Specific user filter
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user].copy()

    # Remove group notifications + media msgs
    temp = df[(df['user'] != 'group_notification') & (df['message'] != '<Media omitted>\n')].copy()

    # Remove stopwords - optimized vectorized approach
    def remove_stop_words_vectorized(messages):
        words_list = messages.str.lower().str.split()
        filtered = words_list.apply(lambda words: [w for w in words if w not in stop_words])
        return filtered.str.join(' ')

    temp['message'] = remove_stop_words_vectorized(temp['message'])
    
    # WordCloud
    wc = WordCloud(
        width=500,
        height=400,
        min_font_size=10,
        background_color='white'
    )

    df_wc = wc.generate(temp['message'].str.cat(sep=" "))
    return df_wc


def most_common_words(selected_user, df):
    # Load stopwords from cache
    stop_words = _load_stopwords()

    # filter chats if needed
    if selected_user != "Overall":
        df = df[df['user'] == selected_user].copy()

    # remove group notifications + media messages
    temp = df[(df['user'] != "group_notification") & (df['message'] != "<Media omitted>\n")].copy()

    # extract clean words - vectorized approach
    words_series = temp['message'].str.lower().str.split().explode()
    words_series = words_series[~words_series.isin(stop_words)]
    words_series = words_series[words_series.str.len() > 0]  # Remove empty strings

    # top 20 most common
    word_counts = words_series.value_counts().head(20)
    most_common_df = pd.DataFrame({
        "word": word_counts.index,
        "count": word_counts.values
    })

    # Plotly Express bar chart
    fig = px.bar(
        most_common_df,
        x="count",
        y="word",
        orientation="h",
        text="count",
        title="Most Common Words"
    )

    fig.update_traces(textposition="outside")
    fig.update_layout(
        template="plotly_dark",
        title_x=0.5,
        yaxis={'categoryorder': 'total ascending'}
    )

    return most_common_df, fig

def emoji_helper(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user].copy()

    # Vectorized emoji extraction
    emojis = df['message'].apply(
        lambda msg: [c for c in str(msg) if c in emoji.EMOJI_DATA]
    ).explode().dropna()

    # Convert to DataFrame
    emoji_counts = emojis.value_counts()
    emoji_df = pd.DataFrame({
        'emoji': emoji_counts.index,
        'count': emoji_counts.values
    })

    return emoji_df

def monthly_timeline(selected_user,df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user].copy()

    timeline = df.groupby(['year', 'month_num', 'month']).size().reset_index(name='message')

    # Vectorized string concatenation
    timeline['time'] = timeline['month'] + "-" + timeline['year'].astype(str)

    return timeline

def daily_timeline(selected_user,df):
    
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    daily_timeline = df.groupby('only_date').count()['message'].reset_index()
    
    return daily_timeline

    

def week_activity_map(selected_user,df):

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    return df['day_name'].value_counts()

def month_activity_map(selected_user,df):

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    return df['month'].value_counts()

def active_hours(selected_user, df):
    if selected_user != "Overall":
        df = df[df["user"] == selected_user].copy()
    else:
        df = df.copy()

    # Ensure hour column exists (should already be there from preprocessing)
    if 'hour' not in df.columns:
        df['hour'] = df['date'].dt.hour
    
    active = df['hour'].value_counts().sort_index()

    return active
def longest_paragraph_by_user(df):
    """Find the longest paragraph/message for each user."""
    # Filter out group notifications and media messages
    filtered_df = df[
        (df['user'] != 'group_notification') & 
        (df['message'] != '<Media omitted>\n')
    ].copy()
    
    if filtered_df.empty:
        return pd.DataFrame(columns=['user', 'longest_message', 'char_count', 'word_count', 'date'])
    
    # Calculate message lengths
    filtered_df['char_count'] = filtered_df['message'].str.len()
    filtered_df['word_count'] = filtered_df['message'].str.split().str.len()
    
    # Find longest message for each user (by character count)
    longest_messages = filtered_df.loc[
        filtered_df.groupby('user')['char_count'].idxmax()
    ][['user', 'message', 'char_count', 'word_count', 'date']].copy()
    
    longest_messages = longest_messages.rename(columns={'message': 'longest_message'})
    longest_messages = longest_messages.sort_values('char_count', ascending=False)
    
    return longest_messages



def chat_streak(selected_user, df):
    if selected_user != "Overall":
        df = df[df["user"] == selected_user]

    df['only_date'] = df['date'].dt.date
    unique_days = sorted(df['only_date'].unique())

    longest = 1
    current = 1

    for i in range(1, len(unique_days)):
        if (unique_days[i] - unique_days[i-1]).days == 1:
            current += 1
            longest = max(longest, current)
        else:
            current = 1

    return longest, current


