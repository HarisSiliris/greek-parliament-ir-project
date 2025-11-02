import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
import numpy as np
import pickle
from elasticsearch import Elasticsearch
from datetime import datetime
import os

"""
compute_member_similarities.py
------------------------------
Computes similarities between parliament members based on their speeches
using TF–IDF, optional LSI (Latent Semantic Indexing), and cosine similarity.
"""

# Import stopwords and text cleaning function from analyze_keywords.py
from analyze_keywords import greek_stopwords, clean_text

# -----------------------------------------------------------
# 1. Load speech data (from pickle or directly from Elasticsearch)
# -----------------------------------------------------------
try:
    # Try loading previously saved speech data
    member_texts = pd.read_pickle("member_texts.pkl")
    print(f"✅ Loaded {len(member_texts)} members from pickle.")
except FileNotFoundError:
    print("⚠️ member_texts.pkl not found — fetching speeches from Elasticsearch...")

    # Elasticsearch setup
    es = Elasticsearch(
        [{"host": "localhost", "port": 9200, "scheme": "http"}],
        verify_certs=False,
        ssl_show_warn=False,
        request_timeout=300
    )
    INDEX_NAME = "greek_parliament_speeches"

    # Fetch all speeches in batches using the scroll API
    # Uses Elasticsearch's scroll API for efficient pagination of large result sets
    # Processes documents in batches to manage memory usage
    # Cleans and normalizes the data before returning
    # Handles errors gracefully (e.g., invalid dates)
    # Returns structured data as a pandas DataFrame
    def fetch_all_speeches(batch_size=5000):
        data = []
        res = es.search(
            index=INDEX_NAME,
            body={"query": {"match_all": {}}},
            scroll="5m",
            size=batch_size
        )
        scroll_id = res["_scroll_id"]
        total_hits = res["hits"]["total"]["value"]
        print(f"Total speeches to retrieve: {total_hits}")

        hits = res["hits"]["hits"]
        while hits:
            for hit in hits:
                src = hit["_source"]
                date = src.get("date", "")
                try:
                    year = datetime.strptime(date, "%d/%m/%Y").year
                except Exception:
                    year = None

                data.append({
                    "member_name": src.get("member_name", "").strip(),
                    "speech": clean_text(src.get("speech", "")),
                })
            res = es.scroll(scroll_id=scroll_id, scroll="5m")
            scroll_id = res["_scroll_id"]
            hits = res["hits"]["hits"]
        return pd.DataFrame(data)

    # Retrieve and process data
    df = fetch_all_speeches()
    print(f"📊 Retrieved {len(df)} speeches from Elasticsearch.")

    # Combine all speeches per member into a single text
    member_texts = df.groupby("member_name")["speech"].apply(lambda x: " ".join(x))

    # Save to pickle for future runs
    pd.to_pickle(member_texts, "member_texts.pkl")
    print(f"✅ Created and saved member_texts.pkl with {len(member_texts)} members.")

# -----------------------------------------------------------
# 2. TF–IDF Vectorization
# -----------------------------------------------------------
print("🧠 Creating TF–IDF representation...")

vectorizer = TfidfVectorizer(
    max_features=5000,                  # Limit vocabulary to 5000 most important words
    stop_words=list(greek_stopwords),   # Use Greek stopwords to ignore common words
    token_pattern=r"(?u)\b[α-ω]{3,}\b"  # Use only Greek lowercase words (3+ letters)
)

X = vectorizer.fit_transform(member_texts.values)

# -----------------------------------------------------------
# 3. Optional: Apply LSI (TruncatedSVD) for dimensionality reduction
# -----------------------------------------------------------
use_lsi = True
if use_lsi:
    print("🔻 Applying LSI (TruncatedSVD) dimensionality reduction...")
    svd = TruncatedSVD(n_components=100, random_state=42)
    X = svd.fit_transform(X)
else:
    X = X.toarray()

# -----------------------------------------------------------
# 4. Compute cosine similarity between members
# -----------------------------------------------------------
print("📈 Computing cosine similarity matrix...")
similarity_matrix = cosine_similarity(X)

# -----------------------------------------------------------
# 5. Find top-k most similar member pairs
# -----------------------------------------------------------
k = 10
names = member_texts.index.tolist()
pairs = []

# Compute pairwise similarities (upper triangular matrix only)
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        sim = similarity_matrix[i, j]
        pairs.append((names[i], names[j], sim))

# Sort by similarity (highest first)
top_k_pairs = sorted(pairs, key=lambda x: x[2], reverse=True)[:k]

# Display top results
print(f"\n🏆 Top-{k} most similar pairs of members:")
for a, b, s in top_k_pairs:
    print(f"{a} — {b}: {s:.3f}")

# -----------------------------------------------------------
# 6. Save results to file
# -----------------------------------------------------------
pd.DataFrame(top_k_pairs, columns=["member_1", "member_2", "similarity"]).to_pickle("member_similarities.pkl")
print("\n💾 Results saved to member_similarities.pkl")
