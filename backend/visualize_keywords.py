import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

party_keywords = pd.read_pickle(os.path.join(BASE_DIR, "party_keywords.pkl"))
member_keywords = pd.read_pickle(os.path.join(BASE_DIR, "member_keywords.pkl"))
speech_keywords = pd.read_pickle(os.path.join(BASE_DIR, "speech_keywords.pkl"))


def show_list_options(options):
    """
    Εμφανίζει τις επιλογές αριθμημένα το ένα κάτω από το άλλο.
    Επιστρέφει ένα dict που συνδέει αριθμό -> όνομα.
    """
    mapping = {}
    for i, name in enumerate(options, start=1):
        print(f"{i}. {name}")
        mapping[str(i)] = name
    return mapping


def show_party_keywords():
    print("\n📋 Διαθέσιμα κόμματα:")
    mapping = show_list_options(list(party_keywords.keys()))
    
    choice = input("Εισάγετε όνομα κόμματος ή αριθμό: ").strip()
    party = mapping.get(choice, choice)  # Αν δώσει αριθμό, το αντιστοιχεί στο όνομα
    
    if party in party_keywords:
        print(f"\n🏛️ Top keywords για το κόμμα {party.upper()}:")
        print("-" * 50)
        for term, score in party_keywords[party]:
            print(f"{term:<20} | TF-IDF: {score}")
        print("-" * 50)
    else:
        print("Το κόμμα δεν βρέθηκε!")


def show_member_keywords():
    print("\n📋 Διαθέσιμοι βουλευτές:")
    mapping = show_list_options(list(member_keywords.keys()))
    
    choice = input("Εισάγετε όνομα βουλευτή ή αριθμό: ").strip()
    member = mapping.get(choice, choice)
    
    if member in member_keywords:
        print(f"\n🧑‍💼 Top keywords για τον βουλευτή {member.upper()}:")
        print("-" * 50)
        for term, score in member_keywords[member]:
            print(f"{term:<20} | TF-IDF: {score}")
        print("-" * 50)
    else:
        print("Ο βουλευτής δεν βρέθηκε!")


def show_speech_keywords():
    idx = input("Εισάγετε index ομιλίας: ").strip()
    try:
        idx = int(idx)
        if idx in speech_keywords:
            print(f"\n📝 Top keywords για την ομιλία {idx}:")
            print("-" * 50)
            for term, score in speech_keywords[idx]:
                print(f"{term:<20} | TF-IDF: {score}")
            print("-" * 50)
        else:
            print("Index ομιλίας δεν βρέθηκε!")
    except ValueError:
        print("Το index πρέπει να είναι αριθμός!")


def main():
    while True:
        print("\n===================================")
        print("  🔍 Ανάλυση Keywords Ελληνικής Βουλής")
        print("===================================")
        print("1️⃣  Keywords ανά κόμμα")
        print("2️⃣  Keywords ανά βουλευτή")
        print("3️⃣  Keywords ανά ομιλία")
        print("4️⃣  Έξοδος")
        
        choice = input("Επιλογή: ").strip()
        if choice == "1":
            show_party_keywords()
        elif choice == "2":
            show_member_keywords()
        elif choice == "3":
            show_speech_keywords()
        elif choice == "4":
            print("Έξοδος...")
            break
        else:
            print("Μη έγκυρη επιλογή!")


if __name__ == "__main__":
    main()
