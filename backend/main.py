from fastapi import FastAPI, Query, HTTPException
from elasticsearch import Elasticsearch
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

es = Elasticsearch([{"host": "elasticsearch", "port": 9200, "scheme": "http"}], verify_certs=False, ssl_show_warn=False)

app = FastAPI(title="Greek Parliament Search")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

INDEX_NAME = "greek_parliament_speeches"

def validate_date(date_str: str) -> str:
    try:
        datetime.strptime(date_str, "%d/%m/%Y")
        return date_str
    except ValueError:
        raise HTTPException(status_code=400, detail="Οι ημερομηνίες πρέπει να είναι στη μορφή DD/MM/YYYY")

@app.get("/search")
def search(
    q: str = Query(None, description="Λέξη/φράση για αναζήτηση"),
    from_date: str = Query(None, description="Αρχική ημερομηνία (DD/MM/YYYY)"),
    to_date: str = Query(None, description="Τελική ημερομηνία (DD/MM/YYYY)"),
    page: int = Query(1, ge=1, description="Αριθμός σελίδας"),
    size: int = Query(10, ge=1, le=100, description="Πλήθος αποτελεσμάτων ανά σελίδα"),
):
    must_clauses = []
    filter_clauses = []

    # Validate dates
    if from_date:
        from_date = validate_date(from_date)
    if to_date:
        to_date = validate_date(to_date)

    # Search string
    if q:
        must_clauses.append({
            "multi_match": {
                "query": q,
                "fields": ["speech", "member_name", "party"]
            }
        })

    # Date filtering
    if from_date and to_date:
        filter_clauses.append({
            "range": {
                "date": {
                    "gte": from_date,
                    "lte": to_date,
                    "format": "dd/MM/yyyy"
                }
            }
        })
    elif from_date:
        # Αν υπάρχει μόνο από ημερομηνία
        filter_clauses.append({
            "term": {
                "date": from_date
            }
        })

    # Compose bool query
    if must_clauses or filter_clauses:
        bool_query = {"bool": {}}
        if must_clauses:
            bool_query["bool"]["must"] = must_clauses
        if filter_clauses:
            bool_query["bool"]["filter"] = filter_clauses
    else:
        bool_query = {"match_all": {}}

    from_offset = (page - 1) * size  # Υπολογισμός offset για pagination
    query_body = {
        "from": from_offset,
        "size": size,
        "query": bool_query
    }

    res = es.search(index=INDEX_NAME, body=query_body)
    total_hits = res["hits"]["total"]["value"]
    hits = [
        {
            "member_name": hit["_source"]["member_name"],
            "party": hit["_source"]["party"],
            "date": hit["_source"]["date"],
            "speech": hit["_source"]["speech"]
        }
        for hit in res["hits"]["hits"]
    ]

    return {
        "query": q,
        "from": from_date,
        "to": to_date,
        "page": page,
        "size": size,
        "total_results": total_hits,
        "total_pages": (total_hits + size - 1) // size,
        "results": hits
    }

@app.get("/keywords/trends")
def get_keywords_trends(entity_type: str, name: str):
    """
    Επιστρέφει keywords ανά έτος για κόμμα ή βουλευτή.
    entity_type: 'party' ή 'member'
    name: όνομα κόμματος ή βουλευτή
    """
    yearly_file = {
        "party": "yearly_party_keywords.pkl",
        "member": "yearly_member_keywords.pkl"
    }.get(entity_type)

    if not yearly_file or not os.path.exists(yearly_file):
        return {
            "error": f"❗Το αρχείο {yearly_file} δεν βρέθηκε. "
                     f"Παρακαλώ εκτελέστε πρώτα το analyze_keywords.py."
        }

    data = pd.read_pickle(yearly_file)

    result = []
    for (year, entity), keywords in data.items():
        if entity.lower() == name.lower():
            result.append({
                "year": year,
                "keywords": [kw for kw, _ in keywords]
            })

    if not result:
        return {"message": f"Δεν βρέθηκαν δεδομένα για {name}."}

    return sorted(result, key=lambda x: x["year"])

@app.get("/keywords/speech/{speech_id}")
def get_speech_keywords(speech_id: int):
    speech_keywords = None
    if os.path.exists("speech_keywords.pkl"):
        speech_keywords = pd.read_pickle("speech_keywords.pkl")
    if speech_keywords is None:
        return {"error": "speech_keywords.pkl not found. Run analyze_keywords.py first."}
    if speech_id not in speech_keywords:
        return {"error": f"Speech {speech_id} not found."}
    return {"speech_id": speech_id, "keywords": speech_keywords[speech_id]}

@app.get("/autocomplete")
def autocomplete(entity_type: str = Query(..., description="party ή member"),
                 q: str = Query(..., description="Το query string")):
    """
    Επιστρέφει λίστα από parties ή members που ταιριάζουν με το query.
    """
    yearly_file = {
        "party": "yearly_party_keywords.pkl",
        "member": "yearly_member_keywords.pkl"
    }.get(entity_type.lower())

    if not yearly_file or not os.path.exists(yearly_file):
        return []

    data = pd.read_pickle(yearly_file)

    entities_set = {entity for (_, entity) in data.keys()}

    q_lower = q.lower()
    matches = [e for e in entities_set if q_lower in e.lower()]

    return sorted(matches)[:20]  # ✅ Return plain list
