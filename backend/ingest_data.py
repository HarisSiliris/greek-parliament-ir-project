from elasticsearch import Elasticsearch
import pandas as pd
from elasticsearch import helpers
import os

# Σωστό path για CSV
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
csv_path = os.path.join(base_dir, "Greek_Parliament_Proceedings_1989_2020", "Greek_Parliament_Proceedings_1989_2020.csv")

# Σύνδεση στο Elasticsearch
es = Elasticsearch(
    [{"host": "localhost", "port": 9200, "scheme": "http"}],
    verify_certs=False,
    ssl_show_warn=False
)

print("🟢 Connected to Elasticsearch:", es.info()['version']['number'])

# Παράδειγμα ingestion (μικρό chunk)
chunksize = 5000
index_name = "greek_parliament_speeches"

# Διαγραφή υπάρχοντος index (αν υπάρχει) για καθαρό ingestion
if es.indices.exists(index=index_name):
    print(f"🗑️ Deleting existing index '{index_name}'...")
    es.indices.delete(index=index_name)

# Δημιουργία νέου index με custom mapping
mapping = {
    "mappings": {
        "properties": {
            "member_name": {"type": "text"},
            "party": {"type": "text"},
            "date": {"type": "date", "format": "dd/MM/yyyy"},
            "speech": {"type": "text"}
        }
    }
}

es.indices.create(index=index_name, body=mapping)
print("🆕 Created index with proper date mapping.")

def generate_actions(df_chunk):
    for _, row in df_chunk.iterrows():
        yield {
            "_index": index_name,
            "_source": {
                "member_name": str(row.get("member_name", "")),
                "party": str(row.get("political_party", "")),
                "date": str(row.get("sitting_date", "")),
                "speech": str(row.get("speech", "")),
            }
        }

for i, chunk in enumerate(pd.read_csv(csv_path, chunksize=chunksize)):
    print(f"📦 Processing chunk {i + 1}...")
    helpers.bulk(es, generate_actions(chunk))
    print(f"✅ Finished chunk {i + 1}")
print("🎉 Data ingestion completed!")