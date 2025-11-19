from urlextract import URLExtract
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
from collections import Counter
import emoji

extract = URLExtract()


# ---------------------- USER STATS ----------------------
def user_stats(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    num_messages = df.shape[0]

    # total words
    words = []
    for msg in df['message']:
        words.extend(msg.split())

    # total media
    num_media_messages = df[df['message'] == '<Media omitted>\n'].shape[0]

    # total links
    extractor = URLExtract()
    links = []
    for msg in df['message']:
        links.extend(extractor.find_urls(msg))

    return num_messages, len(words), num_media_messages, len(links)


# ---------------------- MOST BUSY USERS CHART ----------------------
def most_busy_person(df):

    s = df[df['user'] != "Group Notification"]['user'].value_counts().head()

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
    
    # Hinglish stopwords file load
    with open('stop_hinglish.txt', 'r') as f:
        stop_words = set(f.read().split())

    # Specific user filter
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    # Remove group notifications + media msgs
    temp = df[df['user'] != 'group_notification']
    temp = temp[temp['message'] != '<Media omitted>\n']

    # Remove stopwords function
    def remove_stop_words(message):
        y = []
        for word in message.lower().split():
            if word not in stop_words:
                y.append(word)
        return " ".join(y)

    # Apply stopword cleaning
    temp['message'] = temp['message'].apply(remove_stop_words)
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

    # read stopwords
    with open("stop_hinglish.txt", "r", encoding="utf-8") as f:
        stop_words = set(f.read().split())

    # filter chats if needed
    if selected_user != "Overall":
        df = df[df['user'] == selected_user]

    # remove group notifications + media messages
    temp = df[df['user'] != "group_notification"]
    temp = temp[temp['message'] != "<Media omitted>\n"]

    words = []

    # extract clean words
    for message in temp['message']:
        for word in message.lower().split():
            if word not in stop_words:
                words.append(word)

    # top 20 most common
    most_common_df = pd.DataFrame(
        Counter(words).most_common(20),
        columns=["word", "count"]
    )

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
        df = df[df['user'] == selected_user]

    emojis = []
    for message in df['message']:
        emojis.extend([c for c in message if c in emoji.EMOJI_DATA])

    # Convert to DataFrame
    emoji_df = pd.DataFrame(Counter(emojis).most_common())

    # Rename columns for plotly
    emoji_df = emoji_df.rename(columns={0: 'emoji', 1: 'count'})

    return emoji_df

def monthly_timeline(selected_user,df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    timeline = df.groupby(['year', 'month_num', 'month']).count()['message'].reset_index()

    time = []
    for i in range(timeline.shape[0]):
        time.append(timeline['month'][i] + "-" + str(timeline['year'][i]))

    timeline['time'] = time

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
        df = df[df["user"] == selected_user]

    df['hour'] = df['date'].dt.hour
    active = df['hour'].value_counts().sort_index()

    return active

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


