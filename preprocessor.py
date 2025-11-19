import re
import pandas as pd

def preprocess(data):
    pattern = r"(\d{1,2}\/\d{1,2}\/\d{2,4},\s+\d{1,2}:\d{2}\s(?:in the morning|in the evening|in the afternoon|at night))\s-\s"
    
    parts = re.split(pattern, data)[1:]  
    dates = parts[0::2]
    messages = parts[1::2]

    replacements = {
    "in the morning": "AM",
    "in the afternoon": "PM",
    "in the evening": "PM",
    "at night": "PM"
        }

    clean = []

    for d in dates:
        d2 = d
        for old,new in replacements.items():
            d2  = d2.replace(old,new)
        clean.append(d2)
    df = pd.DataFrame({
    'user_message': messages,
    'message_date': clean
    })
    df.rename(columns={'message_date': 'date'}, inplace=True)
    df['date'] = pd.to_datetime(df['date'], format="%m/%d/%y, %I:%M %p")
    # separate users and messages
    users = []
    messages = []
    for message in df['user_message']:
        entry = re.split('([\w\W]+?):\s', message)
        if entry[1:]:# user name
            users.append(entry[1])
            messages.append(entry[2])
        else:
            users. append('group_notification' )
            messages. append(entry[0])

    df['user' ] = users
    df['message' ] = messages
    df.drop(columns=['user_message'], inplace=True)

    df['only_date'] = df['date'].dt.date
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute

    return df                

    