import io
import zipfile
from typing import Tuple

import matplotlib.pyplot as plt
import plotly.express as px
import streamlit as st
import hashlib

import backhand
import preprocessor


def _decode_chat_bytes(chat_bytes: bytes) -> str:
    """Decode WhatsApp chat bytes, trying common encodings."""
    tried_encodings = ["utf-8", "utf-16", "utf-16-le", "utf-16-be", "iso-8859-1"]
    for encoding in tried_encodings:
        try:
            return chat_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return chat_bytes.decode("utf-8", errors="replace")


ZIP_SIGNATURES = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")


def _extract_txt_from_zip(file_bytes: bytes) -> Tuple[bytes, str]:
    """Extract the largest .txt file from a WhatsApp export zip."""
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zipped:
            txt_members = [
                info for info in zipped.infolist()
                if not info.is_dir() and info.filename.lower().endswith(".txt")
            ]
            if not txt_members:
                raise ValueError("Zip archive does not contain a WhatsApp .txt export.")
            txt_members.sort(key=lambda info: info.file_size, reverse=True)
            chosen = txt_members[0]
            with zipped.open(chosen) as chat_file:
                return chat_file.read(), chosen.filename
    except zipfile.BadZipFile as exc:
        raise ValueError("Uploaded file is not a valid zip archive.") from exc


def _looks_like_zip(file_bytes: bytes) -> bool:
    """Check the magic number to infer zip archives even without .zip extension."""
    return len(file_bytes) >= 4 and file_bytes[:4] in ZIP_SIGNATURES


def load_chat_text(uploaded_file) -> Tuple[str, str]:
    """Accept .txt or .zip uploads and return decoded chat text + file label."""
    file_name = (uploaded_file.name or "").lower()
    file_bytes = uploaded_file.getvalue()

    if not file_bytes:
        raise ValueError("Uploaded file is empty.")

    extracted_label = uploaded_file.name or "uploaded file"

    if file_name.endswith(".zip") or _looks_like_zip(file_bytes):
        chat_bytes, extracted_label = _extract_txt_from_zip(file_bytes)
    else:
        chat_bytes = file_bytes

    return _decode_chat_bytes(chat_bytes), extracted_label


st.sidebar.title('WhatsApp Chat Analyzer')

uploaded_file = st.sidebar.file_uploader(
    'Upload exported chat (.txt or .zip)',
    type=['txt', 'zip'],
    help="Direct .txt exports or the zipped export WhatsApp emails to you are both supported."
)
if uploaded_file is not None:
    with st.spinner("Processing chat…"):
        try:
            data, source_name = load_chat_text(uploaded_file)
        except ValueError as err:
            st.error(f"File processing error: {err}")
            st.stop()

    st.caption(f"Analyzing: {source_name}")
    
    # Cache preprocessed dataframe based on file content hash
    file_hash = hashlib.md5(data.encode()).hexdigest()
    
    @st.cache_data
    def get_preprocessed_df(chat_data: str, _hash: str):
        return preprocessor.preprocess(chat_data)
    
    try:
        with st.spinner("Preprocessing chat data…"):
            df = get_preprocessed_df(data, file_hash)
    except ValueError as err:
        st.error(f"Parsing error: {err}")
        st.stop()

# fetch unique users
    user_list = df['user'].unique().tolist()

    # safely remove group_notification if present
    if 'group_notification' in user_list:
        user_list.remove('group_notification')

    user_list.sort()
    user_list.insert(0, 'Overall')

    selected_user = st.sidebar.selectbox('Show Analysis wrt', user_list)


    if st.sidebar.button('Show Analysis'):
        with st.spinner("Calculating statistics…"):
            num_messages, words, num_media_messages, num_links = backhand.user_stats(selected_user, df)
        st.title("Top Statistics")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Messages", num_messages)

        with col2:
            st.metric("Total Words", words)

        with col3:
            st.metric("Media Shared", num_media_messages)

        with col4:
            st.metric("Links Shared", num_links)
# busy person in the group 
        if selected_user == 'Overall':
            st.title('Most Busy Person')
            col1,col2 = st.columns(2)

            with st.spinner("Analyzing user activity…"):
                fig,new_df = backhand.most_busy_person(df)
            
            with col1 :
                st.plotly_chart(fig, use_container_width=True)

            with col2 :
                st.dataframe(new_df)
           # monthly timeline
            st.title("Monthly Timeline")
            with st.spinner("Generating timeline…"):
                timeline = backhand.monthly_timeline(selected_user,df)
            fig = px.area(
            timeline,
            x='time',
            y='message',
            title='Monthly Timeline',
              )

            fig.update_layout(
            template="plotly_dark",
            title_x=0.5,
            xaxis_title="Time",
            yaxis_title="Messages Count"
            )

            st.plotly_chart(fig, use_container_width=True)
            # ------------------------ DAILY TIMELINE ------------------------
            st.title("Daily Timeline")

            with st.spinner("Generating daily timeline…"):
                daily_timeline = backhand.daily_timeline(selected_user, df)

            fig = px.area(
                daily_timeline,
                x="only_date",
                y="message",
                title="Daily Timeline",
            )
            fig.update_layout(title_x=0.5)

            st.plotly_chart(fig, use_container_width=True)


            # ------------------------ ACTIVITY MAP ------------------------
            st.title("Activity Map")
            col1, col2 = st.columns(2)

            # ---------- BUSIEST DAY ----------
            with col1:
                st.header("Most Busy Day")

                with st.spinner("Analyzing weekly activity…"):
                    busy_day = backhand.week_activity_map(selected_user, df)
                busy_day = busy_day.reset_index()
                busy_day.columns = ["day", "messages"]

                fig = px.bar(
                    busy_day,
                    x="day",
                    y="messages",
                    title="Most Busy Day",
                    text="messages"
                )
                fig.update_traces(textposition="outside")
                fig.update_layout(title_x=0.5)

                st.plotly_chart(fig, use_container_width=True)


            # ---------- BUSIEST MONTH ----------
            with col2:
                st.header("Most Busy Month")

                with st.spinner("Analyzing monthly activity…"):
                    busy_month = backhand.month_activity_map(selected_user, df)
                busy_month = busy_month.reset_index()
                busy_month.columns = ["month", "messages"]

                fig = px.bar(
                    busy_month,
                    x="month",
                    y="messages",
                    title="Most Busy Month",
                    text="messages"
                )
                fig.update_traces(textposition="outside")
                fig.update_layout(title_x=0.5)

                st.plotly_chart(fig, use_container_width=True)

            # Create two side-by-side columns for both sections
            colA, colB = st.columns([2, 1], gap="large")

            with colA:
     
                st.title("Most Active Hours")

                with st.spinner("Analyzing active hours…"):
                    active_hours = backhand.active_hours(selected_user, df)

                # Convert 24-hour → 12-hour format
                def hour_to_12h(hour):
                    if hour == 0:
                        return "12 AM"
                    elif hour < 12:
                        return f"{hour} AM"
                    elif hour == 12:
                        return "12 PM"
                    else:
                        return f"{hour - 12} PM"
                
                active_hours.index = active_hours.index.map(hour_to_12h)

                fig = px.bar(
                    x=active_hours.index,
                    y=active_hours.values,
                    title="Active Hours (12-Hour Format)",
                    labels={"x": "Hour", "y": "Number of Messages"},
                    template="plotly_dark"
                )

                fig.update_layout(
                    title_x=0.5,
                    xaxis_tickangle=45
                )

                st.plotly_chart(fig, use_container_width=True)

            # ========================
            # RIGHT SIDE — Chat Streak
            # ========================
            with colB:
                st.title("Chat Streak Analysis")

                with st.spinner("Calculating streaks…"):
                    longest, current = backhand.chat_streak(selected_user, df)

                st.metric("🔥 Longest Streak", f"{longest} Days")
                st.metric("⚡ Current Streak", f"{current} Days")

            # longest paragraph
            st.title("Longest Paragraph by User")
            
            with st.spinner("Finding longest paragraphs…"):
                longest_paragraphs = backhand.longest_paragraph_by_user(df)
            
            if not longest_paragraphs.empty:
                # Display in expandable sections for each user
                for idx, row in longest_paragraphs.iterrows():
                    with st.expander(f"👤 {row['user']} - {row['char_count']} characters, {row['word_count']} words", expanded=False):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write("**Longest Message:**")
                            st.text_area(
                                "Message content",
                                value=row['longest_message'],
                                height=150,
                                disabled=True,
                                key=f"msg_{row['user']}"
                            )
                        with col2:
                            st.metric("Characters", f"{row['char_count']:,}")
                            st.metric("Words", f"{row['word_count']:,}")
                            st.caption(f"Date: {row['date'].strftime('%Y-%m-%d %H:%M')}")
            else:
                st.info("No messages found to analyze.")
        
        # WordCloud - visible for all users (Overall and individual)
        st.title("Wordcloud")
        with st.spinner("Generating wordcloud…"):
            df_wc = backhand.wordcloud(selected_user, df)
        fig, ax = plt.subplots()
        ax.imshow(df_wc)
        ax.axis('off')  # Remove axes for cleaner look
        st.pyplot(fig)
        
        # most common words
        with st.spinner("Analyzing common words…"):
            most_common_df, fig = backhand.most_common_words(selected_user, df)

        st.title("Most Common Words")
        st.plotly_chart(fig, use_container_width=True)

        with st.spinner("Analyzing emojis…"):
            emoji_df = backhand.emoji_helper(selected_user,df)

        st.title("Emoji Analysis")

        fig = px.pie(
            emoji_df.head(10),
            names='emoji',
            values='count',
            title="Top Emojis"
        )

        st.plotly_chart(fig)

        # Longest Paragraph by User

