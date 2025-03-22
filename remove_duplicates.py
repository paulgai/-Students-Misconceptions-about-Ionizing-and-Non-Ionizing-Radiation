import json
import re

def preprocess_title(title):
    """
    Αφαιρεί σημεία στίξης, απόστροφους, παύλες κ.λπ.
    Μετατρέπει σε πεζά και αφαιρεί περιττά κενά.
    """
    # Αφαιρεί όλους τους χαρακτήρες που δεν είναι γράμματα, αριθμοί ή κενά
    title_no_punct = re.sub(r"[^\w\s]", "", title)
    # Μετατρέπει σε πεζά και αφαιρεί περιττά κενά
    return title_no_punct.strip().lower()

# Φόρτωση δεδομένων από το αρχείο A
with open('articles_with_abstracts.json', 'r', encoding='utf-8') as file_a:
    data_a = json.load(file_a)

# Φόρτωση δεδομένων από το αρχείο B
with open('semanticscholar_papers_data.json', 'r', encoding='utf-8') as file_b:
    data_b = json.load(file_b)

# Δημιουργία ενός συνόλου με τους προεπεξεργασμένους τίτλους του αρχείου A
titles_a = {preprocess_title(entry['title']) for entry in data_a if 'title' in entry}

# Λίστα για αποθήκευση των διπλοτύπων που βρίσκονται
duplicates = []

# Φιλτράρισμα του αρχείου B: διατηρούνται μόνο οι εγγραφές των οποίων ο προεπεξεργασμένος τίτλος δεν υπάρχει στο A
filtered_b = []
for entry in data_b:
    title_b = entry.get('title', '')
    processed_title_b = preprocess_title(title_b)
    if processed_title_b in titles_a:
        duplicates.append(entry)
    else:
        filtered_b.append(entry)

# Αποθήκευση του νέου αρχείου B χωρίς τα διπλότυπα
with open('semanticscholar_papers_data_duplicates_removed.json', 'w', encoding='utf-8') as file_b_new:
    json.dump(filtered_b, file_b_new, ensure_ascii=False, indent=4)

# Εκτύπωση των διπλοτύπων που βρέθηκαν
print("Τα διπλότυπα που βρέθηκαν:")
for dup in duplicates:
    print(dup.get('title', ''))

print("Το νέο αρχείο B με τα διπλότυπα να έχει αφαιρεθεί δημιουργήθηκε ως 'semanticscholar_papers_data_duplicates_removed.json'.")
