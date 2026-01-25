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

# ---------------- AUTO LIGHT / DARK STYLING ----------------
st.markdown("""
<style>
/* ===== DEFAULT (Light Mode) ===== */
html, body, [class*="css"] {
    background-color: #ffffff !important;
    color: #000000 !important;
}

.main {
    background-color: #ffffff !important;
}

section[data-testid="stSidebar"] {
    background-color: #ffffff !important;
}

/* ===== DARK MODE ===== */
@media (prefers-color-scheme: dark) {
    html, body, [class*="css"] {
        background-color: #000000 !important;
        color: #ffffff !important;
    }

    .main {
        background-color: #000000 !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #000000 !important;
    }
}

/* Remove link styling */
a, a:visited, a:hover, a:active {
    color: inherit !important;
    text-decoration: none !important;
}

/* Typography */
h1 {
    font-size: 64px;
    font-weight: 800;
    letter-spacing: -2px;
}

.tagline {
    font-size: 20px;
    color: #777777;
}

@media (prefers-color-scheme: dark) {
    .tagline {
        color: #b3b3b3;
    }
}

.accent {
    color: #E50914;
}

.section-title {
    font-size: 28px;
    margin-top: 40px;
}

/* Always-red Netflix accent */
.always-red {
    color: #E50914 !important;
    font-weight: 600;
}

/* Movie cards */
.movie-name {
    text-align: center;
    font-size: 15px;
    margin-top: 6px;
}

/* Ratings */
.rating {
    font-size: 15px;
    margin-top: 6px;
}
.imdb { color: #f5c518; }
.rt { color: #E50914; }

/* Plot */
.plot {
    font-size: 15px;
    color: #555555;
    margin-top: 12px;
    line-height: 1.4;
}

@media (prefers-color-scheme: dark) {
    .plot {
        color: #cccccc;
    }
}

/* Images */
img {
    border-radius: 12px;
    transition: transform 0.3s ease;
}
img:hover {
    transform: scale(1.06);
}

/* Footer */
.footer {
    margin-top: 60px;
    padding-top: 20px;
    border-top: 1px solid #e0e0e0;
    font-size: 14px;
    text-align: center;
    color: #666666;
}

@media (prefers-color-scheme: dark) {
    .footer {
        border-top: 1px solid #333333;
        color: #aaaaaa;
    }
}
</style>
""", unsafe_allow_html=True)

# ---------------- PATH HANDLING ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

movies = pd.DataFrame(
    pickle.load(open(os.path.join(BASE_DIR, "movie_dict.pkl"), "rb"))
)

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
        st.markdown(f"<h2>{selected_movie}</h2>", unsafe_allow_html=True)

        if imdb_rating:
            st.markdown(f"<p class='rating imdb'>⭐ IMDb Rating: <b>{imdb_rating}</b></p>", unsafe_allow_html=True)
        if rt_rating:
            st.markdown(f"<p class='rating rt'>🍅 Rotten Tomatoes: <b>{rt_rating}</b></p>", unsafe_allow_html=True)
        if plot:
            st.markdown(f"<div class='plot'>{plot}</div>", unsafe_allow_html=True)

# ---------------- RECOMMENDATIONS ----------------
st.markdown(
    """
    <div class="section-title">
        The following films
        <span class="always-red"> match your taste</span>
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
            st.markdown(f"<div class='rating imdb'>⭐ {imdb_r}</div>", unsafe_allow_html=True)
        if rt_r:
            st.markdown(f"<div class='rating rt'>🍅 {rt_r}</div>", unsafe_allow_html=True)

        st.markdown(f"<div class='movie-name'>{movie}</div>", unsafe_allow_html=True)

# ---------------- FOOTER ----------------
st.markdown(
    """
    <div class="footer">
        Created by <b>Soham Mondal</b><br>
        For any query contact <b>
        <a href="mailto:sohammondal29@gmail.com">sohammondal29@gmail.com</a>
        </b>
    </div>
    """,
    unsafe_allow_html=True
)
