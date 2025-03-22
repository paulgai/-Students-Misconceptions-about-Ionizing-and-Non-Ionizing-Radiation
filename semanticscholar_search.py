import json
import time
import re
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Σύνδεση στο υπάρχον JSON αρχείο ή δημιουργία κενής λίστας αν δεν υπάρχει
json_filename = "semanticscholar_papers_data.json"
if os.path.exists(json_filename):
    with open(json_filename, "r", encoding="utf-8") as f:
        papers_data = json.load(f)
    print(f"Φορτώθηκαν {len(papers_data)} εγγραφές από το {json_filename}.")
else:
    papers_data = []
    print("Δεν βρέθηκε υπάρχον JSON, ξεκινάμε με κενή λίστα.")

# Ρυθμίσεις για να μοιάζει με πραγματικό browser
chrome_options = Options()
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/105.0.0.0 Safari/537.36")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Άνοιγμα της σελίδας αποτελεσμάτων
target_url = ("https://www.semanticscholar.org/search?"
              "year%5B0%5D=2010&year%5B1%5D=2025&fos%5B0%5D=education&"
              "q=Misconceptions%20Ionizing%20Radiation%20students&sort=relevance")
driver.get(target_url)

# Περιμένετε χειροκίνητα να αποδεχτείτε τα cookies και να φορτώσει πλήρως η σελίδα
input("Πατήστε Enter μόλις αποδεχτείτε τα cookies χειροκίνητα και φορτώσει πλήρως η σελίδα...")

# (Προαιρετικά) Αποθήκευση των cookies σε αρχείο JSON
cookies = driver.get_cookies()
with open("cookies.json", "w") as f:
    json.dump(cookies, f)
print("Cookies αποθηκεύτηκαν στο cookies.json.")
input("Πατήστε Enter μόλις φορτώσει η σελίδα...")

# Ορίζουμε τον selector για τα paper rows
paper_rows_selector = 'div.cl-paper-row.serp-papers__paper-row.paper-v2-cue.paper-row-normal'

# Χρησιμοποιούμε while loop για σελιδοποίηση
while True:
    try:
        results_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-test-id="result-page"]'))
        )
    except Exception as e:
        print("Δεν βρέθηκε το container αποτελεσμάτων:", e)
        break

    paper_rows = results_container.find_elements(By.CSS_SELECTOR, paper_rows_selector)
    total = len(paper_rows)
    print(f"Τρέχουσα σελίδα: Βρέθηκαν {total} αποτελέσματα.")
    
    if total == 0:
        break

    # Διατρέχουμε κάθε paper στη σελίδα
    for i in range(total):
        # Επαναφόρτωση container και λίστας για αποφυγή stale element references
        results_container = driver.find_element(By.CSS_SELECTOR, 'div[data-test-id="result-page"]')
        paper_rows = results_container.find_elements(By.CSS_SELECTOR, paper_rows_selector)
        current_row = paper_rows[i]
        
        # Εντοπισμός του συνδέσμου του paper και του προεπισκόπηση τίτλου
        link = current_row.find_element(By.CSS_SELECTOR, 'a[data-test-id="title-link"]')
        preview_title = link.find_element(By.TAG_NAME, 'h2').text.strip()
        print(f"Τίτλος (preview): {preview_title}")
        
        # Έλεγχος αν ο τίτλος υπάρχει ήδη στο JSON
        existing_paper = None
        for paper in papers_data:
            if paper.get("title", "").strip() == preview_title:
                existing_paper = paper
                break
        
        if existing_paper:
            if existing_paper.get("venue", "").strip() == "":
                print("Ο τίτλος υπάρχει ήδη αλλά το 'journal' είναι κενό, ενημέρωση...")
                link.click()
                time.sleep(3)
                try:
                    journal_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "span[data-heap-id='paper-meta-journal']"))
                    )
                    journal = journal_element.text.strip()
                except Exception as e:
                    print("Δεν βρέθηκε το στοιχείο για το journal:", e)
                    journal = ""
                existing_paper["venue"] = journal
                with open(json_filename, "w", encoding="utf-8") as f:
                    json.dump(papers_data, f, ensure_ascii=False, indent=4)
                print(f"Journal ενημερώθηκε: {journal}")
                driver.back()
                time.sleep(3)
            else:
                print("Ο τίτλος υπάρχει ήδη και το journal δεν είναι κενό, παραλείπεται.")
            continue  # Προχωράμε στο επόμενο paper
        
        # Αν δεν υπάρχει το paper, προχωράμε στην εξαγωγή δεδομένων
        link.click()
        time.sleep(3)
        
        # Εξαγωγή του πλήρους τίτλου
        try:
            paper_title_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1[data-test-id='paper-detail-title']"))
            )
            paper_title = paper_title_element.text.strip()
            print(f"Αποθηκευμένος τίτλος: {paper_title}")
        except Exception as e:
            print("Δεν βρέθηκε το στοιχείο τίτλου:", e)
            paper_title = ""
        
        # Εξαγωγή συγγραφέων
        try:
            author_list_element = driver.find_element(By.CSS_SELECTOR, "span.author-list")
            author_links = author_list_element.find_elements(By.CSS_SELECTOR, "a.author-list__link.author-list__author-name")
            authors = ", ".join([author.text.strip() for author in author_links])
            print(f"Συγγραφείς: {authors}")
        except Exception as e:
            print("Δεν βρέθηκαν συγγραφείς:", e)
            authors = ""
        
        # Εξαγωγή ονόματος περιοδικού (venue)
        try:
            venue_element = driver.find_element(By.CSS_SELECTOR, "span[data-test-id='venue-metadata'] a")
            venue = venue_element.text.strip()
            print(f"Περιοδικό: {venue}")
        except Exception as e:
            print("Δεν βρέθηκε το στοιχείο του περιοδικού:", e)
            venue = ""
        
        # Εξαγωγή έτους (paper-year)
        try:
            year_element = driver.find_element(By.CSS_SELECTOR, "span[data-test-id='paper-year']")
            year_text = year_element.text
            year_match = re.search(r'\b(19|20)\d{2}\b', year_text)
            year = year_match.group(0) if year_match else ""
            print(f"Έτος: {year}")
        except Exception as e:
            print("Δεν βρέθηκε το στοιχείο έτους:", e)
            year = ""
        
        # Εξαγωγή abstract
        abstract = ""
        try:
            expand_button = driver.find_element(By.XPATH, "//button[.//span[contains(text(),'Expand')]]")
            expand_button.click()
            time.sleep(1)
            abstract_element = driver.find_element(By.CSS_SELECTOR, "div.tldr-abstract-replacement.paper-detail-page__tldr-abstract[data-test-id='no-highlight-abstract-text']")
            abstract = abstract_element.text.strip()
        except Exception as e:
            print("Κουμπί 'Expand' δεν υπάρχει ή δεν λειτούργησε, προσπαθούμε εναλλακτικά:", e)
            try:
                abstract_element = driver.find_element(By.CSS_SELECTOR, "div.tldr-abstract-replacement.text-truncator.paper-detail-page__tldr-abstract")
                abstract = abstract_element.text.strip()
            except Exception as e2:
                print("Δεν βρέθηκε το abstract:", e2)
                abstract = ""
        print(f"Abstract: {abstract[:100]}...")
        
        # Εξαγωγή DOI
        try:
            doi_element = driver.find_element(By.CSS_SELECTOR, "li[data-test-id='paper-doi'] a.doi__link")
            doi = doi_element.text.strip()
            print(f"DOI: {doi}")
        except Exception as e:
            print("Δεν βρέθηκε το στοιχείο DOI:", e)
            doi = ""
        
        # Δημιουργία λεξικού για το paper και προσθήκη στο papers_data
        paper_dict = {
            "title": paper_title,
            "authors": authors,
            "venue": venue,
            "year": year,
            "abstract": abstract,
            "doi": doi
        }
        papers_data.append(paper_dict)
        
        # Ενημέρωση του JSON αρχείου
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(papers_data, f, ensure_ascii=False, indent=4)
        print(f"Εγγραφή αποθηκεύτηκε στο {json_filename}.")
        
        # Επιστροφή στην αρχική σελίδα αποτελεσμάτων
        driver.back()
        time.sleep(3)
    
    # Προσπάθεια μετάβασης στην επόμενη σελίδα
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, "button[data-test-id='next-page']")
        print("Πατήθηκε το κουμπί επόμενης σελίδας.")
        next_button.click()
        time.sleep(3)
    except Exception as e:
        print("Δεν βρέθηκε το κουμπί για επόμενη σελίδα, τερματίζεται η διαδικασία:", e)
        break

print("Η διαδικασία ολοκληρώθηκε. Τα δεδομένα αποθηκεύτηκαν στο", json_filename)
driver.quit()
