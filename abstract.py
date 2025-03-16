import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Φόρτωση των δεδομένων από το αρχείο JSON
with open("articles.json", "r", encoding="utf-8") as f:
    records = json.load(f)

# Προσπάθεια ανοίγματος του output.json για συνέχιση των δεδομένων
output_file = "output_new_withclosed.json"
try:
    with open(output_file, "r", encoding="utf-8") as f:
        existing_records = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    existing_records = []

# Μετατρέπουμε τα υπάρχοντα δεδομένα σε λεξικό για γρήγορη αναζήτηση
existing_records_dict = {record["title"]: record for record in existing_records}

# Ρύθμιση του Selenium WebDriver
options = webdriver.ChromeOptions()
# options.add_argument("--headless")  # Αφαιρέθηκε για να είναι ορατό το Chrome
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Εκκίνηση του WebDriver
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), options=options
)

def get_abstract(title, authors):
    # Δημιουργούμε το ερώτημα ενσωματώνοντας και τα δύο πεδία
    query = f"{title} {authors}"
    driver.get("https://scholar.google.com/")

    # Εύρεση του πεδίου αναζήτησης και εισαγωγή του ερωτήματος
    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)

    # Αναμονή για επίλυση CAPTCHA πριν συνεχίσουμε
    input(
        "Αν εμφανιστεί CAPTCHA μετά την αναζήτηση, παρακαλώ λύστε το και πατήστε Enter για να συνεχίσουμε..."
    )

    time.sleep(2)  # Δίνουμε περισσότερο χρόνο να φορτώσει η σελίδα

    try:
        # Εύρεση του κουμπιού "show more" και κλικ για εμφάνιση του abstract
        show_more_button = driver.find_element(By.CSS_SELECTOR, "a.gs_fma_sml_a")
        show_more_button.click()
        time.sleep(1)  # Επιπλέον χρόνος για να φορτώσει το abstract

        # Αναζήτηση του πρώτου div με κείμενο άνω των 100 χαρακτήρων
        abstract_divs = driver.find_elements(By.CSS_SELECTOR, "div.gs_fma_abs div")
        for div in abstract_divs:
            text = div.text.strip()
            if len(text) > 100:
                return text

        return ""
    except Exception as e:
        print(f"Σφάλμα κατά την εξαγωγή του abstract για '{title}': {e}")
        return ""

# Ενημέρωση των εγγραφών και προσθήκη του abstract
updated_records = []
for record in records:
    title = record.get("title", "")
    authors = record.get("authors", "")

    if title in existing_records_dict and existing_records_dict[title].get("abstract"):
        print(
            f"Η εγγραφή με τίτλο '{title}' υπάρχει ήδη στο output.json με abstract. Παραλείπεται..."
        )
        updated_records.append(existing_records_dict[title])
        continue

    print(f"Αναζήτηση για: {title} - {authors}")
    abstract = get_abstract(title, authors)
    record["abstract"] = abstract
    updated_records.append(record)

    # Ενημέρωση του output.json μόνο αφού ολοκληρωθεί η εγγραφή με το abstract
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(updated_records, f, indent=4, ensure_ascii=False)

# Τερματισμός του WebDriver
driver.quit()

print("Η διαδικασία ολοκληρώθηκε. Το αρχείο output.json ενημερώνεται συνεχώς, αποφεύγοντας διπλότυπα και ενημερώνοντας τις εγγραφές χωρίς abstract.")
