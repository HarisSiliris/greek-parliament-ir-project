import os
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

party_keywords = pd.read_pickle(os.path.join(BASE_DIR, "party_keywords.pkl"))
member_keywords = pd.read_pickle(os.path.join(BASE_DIR, "member_keywords.pkl"))
speech_keywords = pd.read_pickle(os.path.join(BASE_DIR, "speech_keywords.pkl"))


def show_party_keywords():
    print("\nΔιαθέσιμα κόμματα:", list(party_keywords.keys())[:20], "...")
    party = input("Εισάγετε όνομα κόμματος: ")
    if party in party_keywords:
        print(f"\nTop keywords για το κόμμα {party}:")
        for term, score in party_keywords[party]:
            print(f"{term}: {score}")
    else:
        print("Το κόμμα δεν βρέθηκε!")

def show_member_keywords():
    print("\nΔιαθέσιμοι βουλευτές:", list(member_keywords.keys())[:20], "...")
    member = input("Εισάγετε όνομα βουλευτή: ")
    if member in member_keywords:
        print(f"\nTop keywords για τον βουλευτή {member}:")
        for term, score in member_keywords[member]:
            print(f"{term}: {score}")
    else:
        print("Ο βουλευτής δεν βρέθηκε!")

def show_speech_keywords():
    idx = input("Εισάγετε index ομιλίας: ")
    try:
        idx = int(idx)
        if idx in speech_keywords:
            print(f"\nTop keywords για την ομιλία {idx}:")
            for term, score in speech_keywords[idx]:
                print(f"{term}: {score}")
        else:
            print("Index ομιλίας δεν βρέθηκε!")
    except ValueError:
        print("Το index πρέπει να είναι αριθμός!")

def main():
    while True:
        print("\nΕπιλέξτε τι θέλετε να δείτε:")
        print("1. Keywords ανά κόμμα")
        print("2. Keywords ανά βουλευτή")
        print("3. Keywords ανά ομιλία")
        print("4. Έξοδος")
        choice = input("Επιλογή: ")
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
