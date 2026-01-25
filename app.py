import pickle
import streamlit as st
import pandas as pd
import requests
import os
import gdown

# ---------------- CONFIG ----------------
OMDB_API_KEY = "e46ecace"

st.set_page_config(
    page_title="CineMatch",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- CINEMATCH STYLING ----------------
st.markdown("""
<style>
body, .main {
    background: radial-gradient(circle at top, #1f1f1f, #0b0b0b);
    color: white;
}
a, a:visited, a:hover, a:active {
    color: inherit !important;
    text-decoration: none !important;
}
h1 {
    font-size: 64px;
    font-weight: 800;
    letter-spacing: -2px;
}
.tagline {
    font-size: 20px;
    color: #b3b3b3;
    margin-top: -10px;
}
.accent {
    background: linear-gradient(90deg, #ff512f, #dd2476);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.section-title {
    font-size: 28px;
    margin-top: 40px;
}
.movie-name {
    text-align: center;
    font-size: 15px;
    margin-top: 6px;
    color: #e5e5e5;
}
.rating {
    font-size: 15px;
    margin-top: 6px;
}
.imdb { color: #f5c518; }
.rt { color: #FF4C4C; }
.plot {
    font-size: 15px;
    color: #cccccc;
    margin-top: 12px;
    line-height: 1.4;
}
img {
    border-radius: 12px;
    transition: transform 0.3s ease;
}
img:hover {
    transform: scale(1.06);
}
</style>
""", unsafe_allow_html=True)

# ---------------- PATH HANDLING ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- Load small file from repo ----
movies = pd.DataFrame(
    pickle.load(open(os.path.join(BASE_DIR, "movie_dict.pkl"), "rb"))
)

# ---- Google Drive similarity model ----
SIMILARITY_FILE = os.path.join(BASE_DIR, "similarity.pkl")
GDRIVE_FILE_ID = "1L7RZ6skgpYHU3_xEq0QElrOFZUjahQ5Y"
GDRIVE_URL = f"https://drive.google.com/uc?id={GDRIVE_FILE_ID}"

@st.cache_resource(show_spinner="Loading recommendation model...")
def load_similarity():
    if not os.path.exists(SIMILARITY_FILE):
        gdown.download(GDRIVE_URL, SIMILARITY_FILE, quiet=False)

    with open(SIMILARITY_FILE, "rb") as f:
        return pickle.load(f)

similarity = load_similarity()

# ---------------- HELPERS ----------------
def fetch_movie_details(title):
    url = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}&plot=short"
    data = requests.get(url).json()

    poster = data.get("Poster")
    plot = data.get("Plot")
    imdb_rating = data.get("imdbRating")
    rt_rating = None

    for r in data.get("Ratings", []):
        if r["Source"] == "Rotten Tomatoes":
            rt_rating = r["Value"]

    if poster == "N/A": poster = None
    if plot == "N/A": plot = None
    if imdb_rating == "N/A": imdb_rating = None

    return poster, imdb_rating, rt_rating, plot

def google_search_url(title):
    return f"https://www.google.com/search?q={title.replace(' ', '+')}+film"

def recommend(movie):
    idx = movies[movies["title"] == movie].index[0]
    distances = similarity[idx]
    recs = sorted(
        list(enumerate(distances)),
        key=lambda x: x[1],
        reverse=True
    )[1:6]
    return [movies.iloc[i[0]].title for i in recs]

# ---------------- HERO ----------------
st.markdown("<h1><span class='accent'>Cine</span>Match</h1>", unsafe_allow_html=True)
st.markdown(
    "<div class='tagline'>Match your <b>mood</b>. Find your <b>cinema</b>.</div>",
    unsafe_allow_html=True
)
st.markdown("<br><br>", unsafe_allow_html=True)

# ---------------- SEARCH ----------------
selected_movie = st.selectbox(
    "What are you in the mood to watch?",
    movies["title"].values
)

# ---------------- SELECTED MOVIE ----------------
poster, imdb_rating, rt_rating, plot = fetch_movie_details(selected_movie)

if poster:
    col1, col2 = st.columns([1, 3], gap="large")

    with col1:
        st.markdown(
            f"""
            <a href="{google_search_url(selected_movie)}" target="_blank">
                <img src="{poster}" style="width:100%;">
            </a>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <h2>
                <a href="{google_search_url(selected_movie)}" target="_blank">
                    {selected_movie}
                </a>
            </h2>
            """,
            unsafe_allow_html=True
        )

        if imdb_rating:
            st.markdown(
                f"<p class='rating imdb'>⭐ IMDb Rating: <b>{imdb_rating}</b></p>",
                unsafe_allow_html=True
            )

        if rt_rating:
            st.markdown(
                f"<p class='rating rt'>🍅 Rotten Tomatoes: <b>{rt_rating}</b></p>",
                unsafe_allow_html=True
            )

        if plot:
            st.markdown(
                f"<div class='plot'>{plot}</div>",
                unsafe_allow_html=True
            )

# ---------------- RECOMMENDATIONS ----------------
st.markdown(
    """
    <div class="section-title">
        <span style="color:white;">The following films</span>
        <span style="color:#E50914;"> match your taste</span>
    </div>
    <br>
    """,
    unsafe_allow_html=True
)

cols = st.columns(5)
for col, movie in zip(cols, recommend(selected_movie)):
    with col:
        p, imdb_r, rt_r, _ = fetch_movie_details(movie)

        if p:
            st.markdown(
                f"""
                <a href="{google_search_url(movie)}" target="_blank">
                    <img src="{p}" style="width:100%;">
                </a>
                """,
                unsafe_allow_html=True
            )

        if imdb_r:
            st.markdown(
                f"<div class='rating imdb'>⭐ {imdb_r}</div>",
                unsafe_allow_html=True
            )

        if rt_r:
            st.markdown(
                f"<div class='rating rt'>🍅 {rt_r}</div>",
                unsafe_allow_html=True
            )

        st.markdown(
            f"""
            <div class="movie-name">
                <a href="{google_search_url(movie)}" target="_blank">
                    {movie}
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )
