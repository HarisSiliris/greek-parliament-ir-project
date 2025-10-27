# Greek Parliament IR Project

Αυτό το project είναι ένα Information Retrieval σύστημα για τα πρακτικά της Ελληνικής Βουλής (1989-2020).  
Περιλαμβάνει backend σε FastAPI, frontend σε React, και χρήση Elasticsearch για indexing και αναζήτηση.

---

## ⚠️ Dataset

Το dataset είναι **πολύ μεγάλο (~2.3GB)**, οπότε **δεν περιλαμβάνεται στο repository**.  
Για να δουλέψει το project:

1. Κατεβάστε το CSV dataset από [εδώ](https://zenodo.org/records/4311577#.X8-yMdgzaUk).  
2. Τοποθετήστε το στον φάκελο `backend/data/` με το όνομα:
backend/data/Greek_Parliament_Proceedings_1989_2020.csv
3. Επιβεβαιώστε ότι ο φάκελος `data` περιλαμβάνεται στο `.gitignore` για να μην ανέβει στο GitHub.

---

## 🐳 Docker Setup

Το project μπορεί να τρέξει με Docker Compose:

```bash
# Στον root φάκελο του project
docker-compose up --build 
```

Αυτό θα δημιουργήσει και θα ξεκινήσει:

Backend (FastAPI + Uvicorn) στο http://localhost:8000

Frontend (React) στο http://localhost:3000

Elasticsearch στο http://localhost:9200

Kibana στο http://localhost:5601

## Ingest Dataset στο Elasticsearch

Πριν χρησιμοποιήσετε το frontend, τρέξτε το ingestion script μια φορά για να γεμίσετε το Elasticsearch με τα δεδομένα:
```bash
python ingest_data.py
```
Μετά το αρχικό docker-compose up --build, το backend και Elasticsearch είναι persistent μέσω volumes. Δεν χρειάζεται ξανά ingestion αν δεν αλλάξει το dataset.
