import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from textblob import TextBlob
from datetime import datetime
import praw
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import re
from collections import Counter


class RedditAPI:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id="r5GQv88da18DrrazsXBJ3A",
            client_secret="Hv861u1_Z7JxPQnjBQqO-W5hE3_O_A",
            user_agent="Streamlit Analytics v1.0",
        )

    def get_posts(self, subreddit: str, limit: int = 100):
        try:
            subreddit = self.reddit.subreddit(subreddit)
            posts = []

            for post in subreddit.hot(limit=limit):
                posts.append(
                    {
                        "date": datetime.fromtimestamp(post.created_utc),
                        "title": post.title,
                        "text": post.selftext,
                        "score": post.score,
                        "comments": post.num_comments,
                        "url": f"https://reddit.com{post.permalink}",
                    }
                )
            return pd.DataFrame(posts)
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")
            return pd.DataFrame()


class Analytics:
    @staticmethod
    def get_sentiment(text: str) -> float:
        return TextBlob(str(text)).sentiment.polarity

    @staticmethod
    def extract_keywords(text: str) -> list:
        words = re.findall(r"\w+", str(text).lower())
        return [w for w in words if len(w) > 3]

    @staticmethod
    def create_engagement_plot(df: pd.DataFrame) -> go.Figure:
        daily = (
            df.groupby(df["date"].dt.date)
            .agg({"score": "sum", "comments": "sum"})
            .reset_index()
        )

        fig = go.Figure()
        metrics = ["score", "comments"]
        colors = ["#1f77b4", "#ff7f0e"]

        for metric, color in zip(metrics, colors):
            fig.add_trace(
                go.Scatter(
                    x=daily["date"],
                    y=daily[metric],
                    name=metric.capitalize(),
                    line=dict(color=color),
                )
            )

        fig.update_layout(
            title="Daily Engagement",
            xaxis_title="Date",
            yaxis_title="Count",
            template="plotly_white",
        )
        return fig


def main():
    st.set_page_config(page_title="Reddit Analytics", layout="wide")

    st.title("Reddit Content Analytics")

    api = RedditAPI()
    analytics = Analytics()

    with st.sidebar:
        st.header("Controls")
        subreddit = st.text_input("Enter subreddit", value="python")
        post_limit = st.slider("Number of posts", 10, 500, 100)

        if st.button("Analyze"):
            with st.spinner("Fetching data..."):
                df = api.get_posts(subreddit, post_limit)
                if not df.empty:
                    st.session_state.df = df
                    st.success("Data fetched successfully!")

    with st.sidebar:
        st.header("Add Custom Post")
        custom_title = st.text_area("Post Title")
        custom_score = st.number_input("Score", min_value=0)
        custom_comments = st.number_input("Comments", min_value=0)

        if st.button("Add Post"):
            if "df" not in st.session_state:
                st.session_state.df = pd.DataFrame()

            new_post = pd.DataFrame(
                [
                    {
                        "date": datetime.now(),
                        "title": custom_title,
                        "text": "",
                        "score": custom_score,
                        "comments": custom_comments,
                        "url": "",
                    }
                ]
            )

            st.session_state.df = pd.concat(
                [st.session_state.df, new_post], ignore_index=True
            )
            st.success("Post added!")

    if "df" in st.session_state and not st.session_state.df.empty:
        df = st.session_state.df

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Posts", len(df))
        with col2:
            st.metric("Total Score", df["score"].sum())
        with col3:
            st.metric("Total Comments", df["comments"].sum())

        st.subheader("Engagement Trends")
        engagement_plot = analytics.create_engagement_plot(df)
        st.plotly_chart(engagement_plot, use_container_width=True)

        df["sentiment"] = df["title"].apply(analytics.get_sentiment)

        st.subheader("Sentiment Distribution")
        fig_sentiment = px.histogram(
            df, x="sentiment", nbins=20, title="Post Sentiment Distribution"
        )
        st.plotly_chart(fig_sentiment, use_container_width=True)

        st.subheader("Common Words")
        all_words = []
        for text in df["title"]:
            all_words.extend(analytics.extract_keywords(text))

        if all_words:
            word_freq = Counter(all_words)
            wordcloud = WordCloud(
                width=800, height=400, background_color="white"
            ).generate_from_frequencies(word_freq)

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wordcloud, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)

        st.subheader("Recent Posts")
        recent = df.sort_values("date", ascending=False)[
            ["date", "title", "score", "comments", "sentiment", "url"]
        ].head(10)
        st.dataframe(recent)

        if st.button("Export Data"):
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "reddit_data.csv", "text/csv")


if __name__ == "__main__":
    main()

# SINCE I KEEP DELETING MY TERMINAL HISTORY AND FORGETTING: python3 -m streamlit run social_media.py
