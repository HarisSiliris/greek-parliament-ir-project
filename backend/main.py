from fastapi import FastAPI, Query, HTTPException
from elasticsearch import Elasticsearch
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

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
