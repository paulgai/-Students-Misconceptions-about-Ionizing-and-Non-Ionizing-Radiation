"""
Αυτό το script αυτοματοποιεί την αναζήτηση στο Google Scholar χρησιμοποιώντας λέξεις-κλειδιά που σχετίζονται 
με τις παρανοήσεις σχετικά με την ιοντίζουσα και μη ιοντίζουσα ακτινοβολία. Μέσω του Selenium WebDriver, 
εκτελεί αναζήτηση, επεξεργάζεται τα αποτελέσματα, εξάγει τίτλους άρθρων, συγγραφείς, έτος, περιοδικό, 
σελίδες και συνδέσμους open access (εφόσον υπάρχουν) και τα αποθηκεύει σε αρχείο JSON. 
Ο χρήστης καλείται να επιλύσει χειροκίνητα CAPTCHA όταν εμφανιστεί. Το script υποστηρίζει πλοήγηση σε 
πολλαπλές σελίδες αποτελεσμάτων, διατηρεί τα ήδη αποθηκευμένα δεδομένα και ενημερώνει το αρχείο με νέα άρθρα.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import json
import os

# Ορισμός λέξεων-κλειδιών για αναζήτηση
keywords = "Misconceptions conceptions Ionizing Non-Ionizing Radiation"

# Ρύθμιση του webdriver (χρησιμοποιούμε Chrome σε αυτό το παράδειγμα)
driver = webdriver.Chrome()


def load_existing_data(filename):
    """Φορτώνει τα ήδη αποθηκευμένα δεδομένα από το JSON αρχείο."""
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def search_scholar():
    try:
        # Άνοιγμα του Google Scholar
        driver.get("https://scholar.google.com/")
        time.sleep(2)  # Αναμονή για τη φόρτωση της σελίδας

        # Εντοπισμός του πεδίου αναζήτησης και εισαγωγή των λέξεων-κλειδιών
        search_box = driver.find_element(By.ID, "gs_hdr_tsi")
        search_box.send_keys(keywords)
        time.sleep(1)  # Αναμονή

        # Πάτημα του κουμπιού αναζήτησης
        search_button = driver.find_element(By.ID, "gs_hdr_tsb")
        search_button.click()

        # Αναμονή για την εμφάνιση των αποτελεσμάτων
        time.sleep(3)

        # Σταματά εδώ και περιμένει να λυθεί το CAPTCHA
        input(
            "🚨 Παρακαλώ επιλύστε το CAPTCHA στο πρόγραμμα περιήγησης και πατήστε Enter για να συνεχίσετε..."
        )

        filename = "articles.json"
        articles = load_existing_data(filename)  # Φόρτωση υπαρχόντων δεδομένων

        # Προσδιορισμός της επόμενης διαθέσιμης σελίδας
        page_index = max([item.get("index", 0) for item in articles], default=0) + 1

        while True:
            try:
                # Περιμένει να εμφανιστεί το στοιχείο των αποτελεσμάτων
                results_container = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "gs_res_ccl_mid"))
                )
                results = results_container.find_elements(By.CLASS_NAME, "gs_r")
            except Exception:
                print("Δεν βρέθηκαν αποτελέσματα, τερματισμός αναζήτησης.")
                break

            for result in results:
                try:
                    # Εξαγωγή του data-cid
                    data_cid = result.get_attribute("data-cid")

                    # Εντοπισμός του τίτλου χρησιμοποιώντας το id ως data-cid
                    title_element = result.find_element(
                        By.CSS_SELECTOR, f'a[id="{data_cid}"]'
                    )
                    clean_title = title_element.text  # Λήψη καθαρού κειμένου

                    # Εύρεση και άνοιγμα του κουμπιού "Παράθεση"
                    authors = year = journal = pages = ""
                    try:
                        citation_button = result.find_element(
                            By.CLASS_NAME, "gs_or_cit"
                        )
                        citation_button.click()
                        time.sleep(2)  # Αναμονή για να εμφανιστεί το παράθυρο

                        # Εντοπισμός του APA citation
                        citation_div = driver.find_element(By.ID, "gs_citd")
                        apa_citation = citation_div.find_element(
                            By.XPATH, "//th[text()='APA']/following-sibling::td/div"
                        ).text

                        # Ανάλυση δεδομένων από το APA citation
                        match = re.search(
                            r"(.*?) \((\d{4})\)\. (.*?)\. (.*)", apa_citation
                        )
                        if match:
                            authors = match.group(1).strip()
                            year = match.group(2).strip()
                            remaining_text = match.group(4).strip()

                            # Αφαίρεση του τίτλου από το υπόλοιπο κείμενο
                            remaining_text = remaining_text.replace(
                                clean_title, ""
                            ).strip()

                            # Διαχωρισμός Journal και Pages στο πρώτο κόμμα
                            if "," in remaining_text:
                                split_text = remaining_text.split(",", 1)
                                journal = split_text[0].strip().rstrip(",")
                                pages = split_text[1].strip()
                            else:
                                journal = remaining_text.strip()
                                pages = ""

                        # Κλείσιμο του παράθυρου παραπομπής
                        close_citation_button = driver.find_element(By.ID, "gs_cit-x")
                        close_citation_button.click()
                        time.sleep(1)  # Αναμονή για το κλείσιμο του παραθύρου
                    except Exception:
                        authors = year = journal = pages = ""

                    # Έλεγχος για open access link
                    open_access_element = None
                    url = ""
                    open_access = False
                    try:
                        open_access_element = result.find_element(
                            By.CLASS_NAME, "gs_or_ggsm"
                        ).find_element(By.TAG_NAME, "a")
                        url = open_access_element.get_attribute("href")
                        open_access = True
                    except Exception:
                        open_access = False

                    # Αποθήκευση στον πίνακα
                    articles.append(
                        {
                            "index": page_index,
                            "data_cid": data_cid,
                            "title": clean_title,
                            "authors": authors,
                            "year": year,
                            "journal": journal,
                            "pages": pages,
                            "open_access": open_access,
                            "url": url,
                        }
                    )

                    # Εκτύπωση στην κονσόλα
                    print(
                        f"[{page_index}] [{data_cid}] {clean_title} (Open Access: {open_access}, URL: {url}, Authors: {authors}, Year: {year}, Journal: {journal}, Pages: {pages})"
                    )
                except Exception as e:
                    print(f"Σφάλμα κατά την επεξεργασία άρθρου: {e}")

            # Αποθήκευση σε JSON αρχείο
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(articles, f, ensure_ascii=False, indent=4)

            # Αναζήτηση του κουμπιού "Επόμενη" και κλικ αν υπάρχει
            try:
                next_button = driver.find_element(By.LINK_TEXT, "Επόμενη")
                next_button.click()
                page_index += 1  # Αύξηση του δείκτη σελίδας
                time.sleep(3)  # Αναμονή για τη φόρτωση της νέας σελίδας
            except Exception:
                print("Δεν βρέθηκε το κουμπί 'Επόμενη', τερματισμός αναζήτησης.")
                break

    except Exception as e:
        print(f"Σφάλμα: {e}")


# Εκτέλεση της αναζήτησης
search_scholar()
