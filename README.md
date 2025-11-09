# Greek Parliament IR Project

Αυτό το project είναι ένα Information Retrieval σύστημα για τα πρακτικά της Ελληνικής Βουλής (1989-2020).  
Περιλαμβάνει backend σε FastAPI, frontend σε React, και χρήση Elasticsearch για indexing και αναζήτηση.

---

## 🗃️ Dataset

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

```bash
python analyze_keywords.py
```
Πραγματοποιεί σύνδεση με Elasticsearch, καθαρίζει το κείμενο (clean_text), εκτελεί TF–IDF ανά βουλευτή, κόμμα, ομιλία και ανά έτος για κάθε βουλευτή και κόμμα και τελικά αποθηκεύει όλα τα αποτελέσματα σε pickle αρχεία:
```bash
party_keywords.pkl → ανά κόμμα

member_keywords.pkl → ανά βουλευτή

speech_keywords.pkl → ανά ομιλία

yearly_party_keywords.pkl → ανά έτος και κόμμα

yearly_member_keywords.pkl → ανά έτος και βουλευτή
```
Επίσης το visualize_keywords.py βοηθάει στην οπτικοποίηση των αποτελεσμάτων παρά το ότι γίνεται να τα δούμε και στο frontend

```bash
python compute_similarities.py
```
Πραγματοποιεί φόρτωση όλων των ομιλιών ανά βουλευτή (είτε από το αρχείο member_texts.pkl, είτε απευθείας από το Elasticsearch), καθαρίζει το κείμενο μέσω της clean_text, και εξάγει ένα διάνυσμα χαρακτηριστικών (TF–IDF) για κάθε μέλος του κοινοβουλίου.

Προαιρετικά εφαρμόζει LSI (TruncatedSVD) για μείωση διάστασης και στη συνέχεια υπολογίζει τις ομοιότητες cosine μεταξύ όλων των ζευγών βουλευτών.

Τέλος, εντοπίζει τα top-k πιο όμοια ζεύγη βουλευτών και αποθηκεύει τα αποτελέσματα σε pickle αρχεία:
```bash
member_texts.pkl → όλες οι ομιλίες ανά βουλευτή (αν δεν υπάρχει, δημιουργείται)

member_similarities.pkl → top-k ζεύγη βουλευτών με τη μεγαλύτερη ομοιότητα
```