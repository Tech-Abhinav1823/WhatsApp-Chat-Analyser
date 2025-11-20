import streamlit as st
import preprocessor,backhand
import matplotlib.pyplot as plt
import plotly.express as px
st.sidebar.title('WhatsApp Chat Analyzer')

uploaded_file = st.sidebar.file_uploader('Choose a File')
if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    data = bytes_data.decode('utf-8', errors='replace')
    df = preprocessor.preprocess(data)
# fetch unique users
    user_list = df['user'].unique().tolist()

    # safely remove group_notification if present
    if 'group_notification' in user_list:
        user_list.remove('group_notification')

    user_list.sort()
    user_list.insert(0, 'Overall')

    selected_user = st.sidebar.selectbox('Show Analysis wrt', user_list)


    if st.sidebar.button('Show Analysis'):
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

            fig,new_df = backhand.most_busy_person(df)
            
            with col1 :
                st.plotly_chart(fig, use_container_width=True)

            with col2 :
                st.dataframe(new_df)
           # monthly timeline
            st.title("Monthly Timeline")
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

                longest, current = backhand.chat_streak(selected_user, df)

                st.metric("🔥 Longest Streak", f"{longest} Days")
                st.metric("⚡ Current Streak", f"{current} Days")
                    
# WordCloud
            st.title("Wordcloud")
            df_wc = backhand.wordcloud(selected_user,df)
            fig,ax = plt.subplots()
            ax.imshow(df_wc)
            st.pyplot(fig)
    # most common words
        most_common_df, fig = backhand.most_common_words(selected_user, df)

        st.title("Most Common Words")
        st.plotly_chart(fig, use_container_width=True)

        emoji_df = backhand.emoji_helper(selected_user,df)

        st.title("Emoji Analysis")

        fig = px.pie(
            emoji_df.head(10),
            names='emoji',
            values='count',
            title="Top Emojis"
        )

        st.plotly_chart(fig)

