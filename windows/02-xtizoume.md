[Ευρετήριο](README.md) · Οδηγός για Windows · Σελίδα 3 από 8

# Μέρος 3: Χτίζουμε και αποδεικνύουμε (Windows)

**Χρόνος:** περίπου 40 λεπτά · **Project:** `study-copilot`

Ο agent φτιάχνει ολόκληρο το Study Copilot. Η σειρά είναι πάντα η ίδια: ο agent γράφει **πλάνο**, εσύ το διαβάζεις και αφήνεις **σχόλιο**, και μετά πατάς **Proceed** για να ξεκινήσει η **εκτέλεση**. Στο τέλος ελέγχεις ότι η εφαρμογή δουλεύει.

---

## Α. Το μεγάλο prompt

Το prompt έχει πέντε κομμάτια: **στόχο** (τι φτιάχνουμε), **χρήστες** (για ποιον), **λειτουργίες και περιορισμούς**, **τεχνολογίες** (Flask, HTML/CSS/JS) και **κριτήριο επιτυχίας** (η γραμμή `Done when`). Όσο πιο σαφή είναι αυτά, τόσο καλύτερο είναι το αποτέλεσμα.

Ξεκίνα **νέα συζήτηση** στο project `study-copilot`. Prompt για τον agent:

```
/plan Build "Study Copilot", a web app that turns lecture slides into study material.
Users: AUTH students preparing for exams. UI text in Greek.
Features:
1. Upload a lecture PDF (max 20 MB).
2. Call the Gemini API (google-genai SDK) with a JSON schema and get back:
   6-8 summary bullets with pages, 10 flashcards, a 5-question quiz with answer,
   explanation, source page.
3. Tabs: Summary, Flashcards (click to flip), Quiz (score at the end). Cache per PDF and backend/model, so switching between Gemini and Gemma never reuses results from the other model.
Constraints: Flask, plain HTML/CSS/JS, no JS libraries. Create requirements.txt.
Use the existing project virtual environment at .venv (do not create a different
environment). Install all requirements with that venv's Python. Free-tier Flash
model in ONE constant. Key only from GEMINI_API_KEY; never print, log or commit it.
All model calls in llm_client.py.
Done when: it runs on sample_lectures/lecture1.pdf, 6+ tests pass with a mocked LLM
client (no real API calls in tests), and you show me a screenshot of the Quiz tab.
```

Αν το `/plan` δεν αναγνωρίζεται, σβήσε το `/plan ` από την αρχή και πρόσθεσε στο τέλος: `First show me an implementation plan and wait for my approval.`

---

## Β. Διάβασε το πλάνο και άφησε σχόλιο

Μετά από λίγο εμφανίζεται ένα έγγραφο με τίτλο **Implementation Plan**. **Μην πατήσεις ακόμα Proceed.**


Διάβασέ το και έλεγξε:

- [ ] Αναφέρει **JSON schema** για την απάντηση του Gemini;
- [ ] Το cache ξεχωρίζει αποτελέσματα ανά PDF **και** ανά backend/model;
- [ ] Τα tests χρησιμοποιούν **mock**, δηλαδή ψεύτικες απαντήσεις αντί για πραγματικές κλήσεις στο Gemini;

Αν λείπει κάτι από αυτά, γράψε το ως σχόλιο στο πλάνο. Αν τα έχει όλα, διάλεξε ένα από τα παρακάτω και πρόσθεσέ το ως σχόλιο:

```
Show a friendly Greek error when the PDF is scanned and has no text.
```

```
Add a difficulty selector (easy / medium / hard) for the quiz.
```

```
Show the source page next to every flashcard.
```

Για να αφήσεις σχόλιο, επίλεξε ένα κομμάτι κειμένου στο πλάνο και γράψε στο πεδίο σχολίου που εμφανίζεται, ή γράψε το σχόλιο στο πεδίο μηνύματος της συζήτησης.


Μετά πάτα **Proceed**.

### Οι άδειες που θα σου ζητήσει

Κατά την εκτέλεση ο agent θα ζητήσει άδεια για εντολές όπως `pip install` και `pytest`. Έλεγξε ότι η εντολή χρησιμοποιεί την Python του `.venv` (περιέχει `.\.venv\Scripts\python.exe` ή παρόμοιο) και πάτα **Allow**. Αν ρωτήσει πολλές φορές για εντολές μέσα στον φάκελο του project, μπορείς να διαλέξεις **Always allow in this project**.

Η εκτέλεση παίρνει μερικά λεπτά. Μην κλείσεις το Antigravity.

---

## Γ. Δοκίμασέ το εσύ

Όταν τελειώσει, ο agent δείχνει ένα **Walkthrough** με ό,τι έκανε και μια διεύθυνση όπως `http://localhost:5000` ή `http://127.0.0.1:5000`.

1. Αν ο server δεν τρέχει ήδη, ζήτησέ το: `Start the app and give me the URL.`
2. Άνοιξε τη διεύθυνση στον Chrome.
3. Ανέβασε το αρχείο `sample_lectures/lecture1.pdf`. Θα το βρεις στο `C:\Users\<το-όνομά-σου>\agy-101\study-copilot\sample_lectures`.
4. Περίμενε μερικά δευτερόλεπτα.

**Τι πρέπει να δεις:** γεμίζουν **και οι τρεις καρτέλες**: Περίληψη, Flashcards, Quiz.


Αν δεις μήνυμα για API key, δες το [`08-otan-kolliseis.md`](08-otan-kolliseis.md#στήσιμο-και-api-key).

### Έλεγχος του venv

Εντολή στο terminal, μέσα στο `study-copilot`:

```
.\.venv\Scripts\python.exe --version
```

Πρέπει να δεις Python 3.10 ή νεότερη. Αν γράψει ότι το αρχείο δεν υπάρχει, γύρνα στο Μέρος 2, Β, Βήμα 2 και φτιάξε το `.venv`. Μετά γράψε στον agent: `Install requirements.txt into the project .venv.`

---

## Δ. Απόδειξη ότι δουλεύει

### 1. Ο agent χρησιμοποιεί το app σαν φοιτητής

Prompt για τον agent:

```
/browser Open the running Study Copilot, upload sample_lectures/lecture2.pdf, check that all three tabs fill in, flip two flashcards, answer the whole quiz and confirm a score is shown. Record the session and report anything broken.
```

**Τι πρέπει να δεις:** ο Chrome ανοίγει και ο agent κάνει τα βήματα μόνος του. Στο τέλος, στα artifacts υπάρχει ένα **βίντεο** της συνεδρίας. Κράτα το: στο Μέρος 6 γίνεται GIF για το README σου.

Αν το `/browser` ή η εγγραφή δεν δουλεύουν, κάνε εσύ τα ίδια βήματα στον Chrome. Το βίντεο δεν είναι απαραίτητο για να συνεχίσεις.

Αν ο agent βρήκε πρόβλημα, prompt:

```
Fix the issues you found and run the browser check again.
```

### 2. Τα tests χωρίς internet

Αυτό το βήμα αποδεικνύει ότι τα tests δεν καλούν πραγματικά το Gemini.

1. **Κλείσε το Wi-Fi.** Κάνε κλικ στο εικονίδιο δικτύου κάτω δεξιά στη γραμμή εργασιών και πάτα το κουμπί **Wi-Fi** ώστε να γίνει γκρι.2. Εντολή στο terminal, μέσα στο `study-copilot`:
   ```
   .\.venv\Scripts\python.exe -m pytest
   ```
3. **Τι πρέπει να δεις:** στο τέλος μια πράσινη γραμμή όπως `6 passed`. Αν βλέπεις `failed`, κάποιο test καλεί το internet.
4. **Άνοιξε ξανά το Wi-Fi.** 5. Αν κάποιο test απέτυχε, prompt για τον agent:
   ```
   Make every test use the mock; no network in tests. Run pytest again.
   ```


### 3. Αποθήκευση (commit)

Το commit αποθηκεύει μια «φωτογραφία» του project στο ιστορικό του Git. Αν κάτι χαλάσει αργότερα, μπορείς να γυρίσεις εδώ.

Prompt για τον agent:

```
Commit all changes with a clear message describing what was built.
```

Πριν πατήσεις Allow στην εντολή του commit, έλεγξε ότι το `.env` **δεν** είναι στη λίστα αρχείων.

Εναλλακτικά, άνοιξε το **Review panel** του Antigravity, δες τις αλλαγές (diffs) και κάνε commit από εκεί.

---

## Checkpoint

- [ ] Το app δείχνει και τις τρεις καρτέλες για το `lecture1.pdf`.
- [ ] Έχεις βίντεο από τον browser agent (ή έκανες τον έλεγχο μόνος σου).
- [ ] Τα tests περνάνε **χωρίς internet**.
- [ ] Έχεις κάνει ένα commit.

Αν κάτι από αυτά δεν δουλεύει και δεν βρίσκεις λύση, μπορείς να συνεχίσεις από την έτοιμη λύση `checkpoint-3`. Δες το [`08-otan-kolliseis.md`](08-otan-kolliseis.md#έμεινα-πίσω).

Περισσότερες ασκήσεις: [`07-boss-levels.md`](07-boss-levels.md#μέρος-3)


---

[← Προηγούμενο: Γνωριμία με το Antigravity](01-gnorimia.md) · [Ευρετήριο](README.md) · [Επόμενο: Κανόνες και κριτής →](04-kanones-kritis.md)
