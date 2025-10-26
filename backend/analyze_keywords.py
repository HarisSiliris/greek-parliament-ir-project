"""
analyze_keywords.py — Βελτιωμένη έκδοση
---------------------------------------
Αναλύει τα δεδομένα των ομιλιών της Βουλής:
1. Keywords ανά ομιλία
2. Keywords ανά βουλευτή
3. Keywords ανά κόμμα
4. Keywords ανά έτος (σχετικά με κόμμα & βουλευτή)
"""

from elasticsearch import Elasticsearch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction import text
import pandas as pd
import re
import unicodedata
from datetime import datetime
from tqdm import tqdm
import os

# --- Διαγραφή παλιών pkl ---
for f in ["party_keywords.pkl", "member_keywords.pkl", "speech_keywords.pkl",
          "yearly_party_keywords.pkl", "yearly_member_keywords.pkl", "yearly_keywords.pkl"]:
    if os.path.exists(f):
        os.remove(f)
        print(f"🧹 Διαγράφηκε παλιό αρχείο: {f}")

# --- Ελληνικά stopwords ---
greek_stopwords = text.ENGLISH_STOP_WORDS.union({
    "και", "να", "το", "η", "ο", "από", "με", "στο", "την", "της", "σε",
    "θα", "ως", "για", "των", "τις", "τον", "του", "προς", "δε", "δεν",
    "αν", "μια", "έχω", "είναι", "ήταν", "ότι", "όπως", "επίσης", "αλλά"
})
greek_stopwords = {unicodedata.normalize("NFC", w) for w in greek_stopwords}

# -----------------------------------------------------------
# 1. Σύνδεση με Elasticsearch
# -----------------------------------------------------------
es = Elasticsearch(
    [{"host": "localhost", "port": 9200, "scheme": "http"}],
    verify_certs=False,
    ssl_show_warn=False,
    request_timeout=300
)
INDEX_NAME = "greek_parliament_speeches"

# -----------------------------------------------------------
# 2. Καθαρισμός κειμένου
# -----------------------------------------------------------
def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFC", str(text))
    text = re.sub(r"[^Α-Ωα-ωA-Za-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    tokens = [w for w in text.lower().split() if len(w) > 2 and w not in greek_stopwords and re.match(r"^[α-ω]+$", w)]
    return " ".join(tokens)

# -----------------------------------------------------------
# 3. Ανάκτηση ομιλιών
# -----------------------------------------------------------
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
    print(f"Σύνολο ομιλιών προς ανάκτηση: {total_hits}")

    fetched = 0
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
                "party": src.get("party", "").strip(),
                "date": date,
                "year": year,
                "speech": clean_text(src.get("speech", "")),
            })

        fetched += len(hits)
        print(f"✅ Ανακτήθηκαν {fetched}/{total_hits} ομιλίες")
        res = es.scroll(scroll_id=scroll_id, scroll="5m")
        scroll_id = res["_scroll_id"]
        hits = res["hits"]["hits"]

    return pd.DataFrame(data)

# -----------------------------------------------------------
# 4. TF-IDF ανά ομάδα (κόμμα, βουλευτής)
# -----------------------------------------------------------
def compute_keywords(df: pd.DataFrame, group_col, top_n=10) -> dict:
    results = {}
    grouped = df.groupby(group_col)["speech"].apply(lambda x: " ".join(x))
    vectorizer = TfidfVectorizer(
        max_features=5000,
        stop_words=list(greek_stopwords),
        token_pattern=r"(?u)\b[α-ω]{3,}\b"
    )
    tfidf_matrix = vectorizer.fit_transform(grouped.values)
    feature_names = vectorizer.get_feature_names_out()
    for idx, name in enumerate(grouped.index):
        scores = tfidf_matrix[idx].toarray()[0]
        top_idx = scores.argsort()[-top_n:][::-1]
        results[name] = [(feature_names[i], round(scores[i], 3)) for i in top_idx]
    return results

# -----------------------------------------------------------
# 5. TF-IDF ανά ομιλία (batching)
# -----------------------------------------------------------
def compute_keywords_per_speech(df: pd.DataFrame, top_n=10, batch_size=5000) -> dict:
    results = {}
    vectorizer = TfidfVectorizer(
        max_features=5000,
        stop_words=list(greek_stopwords),
        token_pattern=r"(?u)\b[α-ω]{3,}\b"
    )
    speeches = df["speech"].tolist()
    indices = df.index.tolist()
    for start in tqdm(range(0, len(speeches), batch_size), desc="Υπολογισμός keywords ανά ομιλία"):
        batch = [(i, s) for i, s in zip(indices[start:start+batch_size], speeches[start:start+batch_size]) if s.strip()]
        if not batch:
            continue
        idxs, texts = zip(*batch)
        tfidf_matrix = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()
        for i, row in zip(idxs, tfidf_matrix.toarray()):
            top_idx = row.argsort()[-top_n:][::-1]
            results[i] = [(feature_names[j], round(row[j], 3)) for j in top_idx]
    return results

# -----------------------------------------------------------
# 6. TF-IDF ανά έτος + σχέση (κόμμα/βουλευτής)
# -----------------------------------------------------------
def compute_keywords_over_time(df: pd.DataFrame, group_col="year", related_col=None, top_n=10) -> dict:
    results = {}
    if related_col:
        df = df.dropna(subset=[group_col, related_col])
        grouped = df.groupby([group_col, related_col])["speech"].apply(lambda x: " ".join(x))
    else:
        df = df.dropna(subset=[group_col])
        grouped = df.groupby(group_col)["speech"].apply(lambda x: " ".join(x))
    vectorizer = TfidfVectorizer(
        max_features=5000,
        stop_words=list(greek_stopwords),
        token_pattern=r"(?u)\b[α-ω]{3,}\b"
    )
    tfidf_matrix = vectorizer.fit_transform(grouped.values)
    feature_names = vectorizer.get_feature_names_out()
    for idx, name in enumerate(grouped.index):
        scores = tfidf_matrix[idx].toarray()[0]
        top_idx = scores.argsort()[-top_n:][::-1]
        results[name] = [(feature_names[i], round(scores[i], 3)) for i in top_idx]
    return results

# -----------------------------------------------------------
# 7. Κύρια ροή
# -----------------------------------------------------------
if __name__ == "__main__":
    print("🔹 Ανάκτηση ομιλιών από τον Elasticsearch...")
    df = fetch_all_speeches()
    print(f"🔸 Ανακτήθηκαν {len(df)} ομιλίες")

    print("\n🧠 Υπολογισμός keywords ανά κόμμα...")
    party_keywords = compute_keywords(df, "party")

    print("\n🧠 Υπολογισμός keywords ανά βουλευτή...")
    member_keywords = compute_keywords(df, "member_name")

    print("\n📝 Υπολογισμός keywords ανά ομιλία...")
    speech_keywords = compute_keywords_per_speech(df)

    print("\n📅 Ανάλυση keywords ανά έτος ανά κόμμα...")
    yearly_party_keywords = compute_keywords_over_time(df, group_col="year", related_col="party")

    print("\n📅 Ανάλυση keywords ανά έτος ανά βουλευτή...")
    yearly_member_keywords = compute_keywords_over_time(df, group_col="year", related_col="member_name")

    pd.to_pickle(party_keywords, "party_keywords.pkl")
    pd.to_pickle(member_keywords, "member_keywords.pkl")
    pd.to_pickle(speech_keywords, "speech_keywords.pkl")
    pd.to_pickle(yearly_party_keywords, "yearly_party_keywords.pkl")
    pd.to_pickle(yearly_member_keywords, "yearly_member_keywords.pkl")

    print("\n📦 Αποθηκεύτηκαν τα αποτελέσματα σε .pkl αρχεία")
    print("✅ Ολοκληρώθηκε επιτυχώς!")