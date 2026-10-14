# Μέρος 1 — Εγκαταστάσεις

**Πότε:** με το που κάθεσαι, πριν από οτιδήποτε άλλο. Οι εγκαταστάσεις τρέχουν στο παρασκήνιο όσο ακούς την εισαγωγή.

Δεν χρειάζεται να έχεις ετοιμάσει τίποτα από πριν. Χρειάζεσαι μόνο laptop, φορτιστή και τον κωδικό του προσωπικού σου Gmail. Ξεκίνα τα παρακάτω με τη σειρά και άφησέ τα να τρέχουν. Αν κολλήσεις κάπου, σήκωσε χέρι και θα έρθει κάποιος να βοηθήσει.

---

## 1. Antigravity

1. Άνοιξε το **antigravity.google/download** και κατέβασε την έκδοση για το λειτουργικό σου.
2. Εγκατάστησέ το και άνοιξέ το.
3. Κάνε login με το **προσωπικό σου Gmail** (όχι τον λογαριασμό του πανεπιστημίου).

## 2. Ollama και το μικρό Gemma

Το Gemma είναι ένα μοντέλο AI που τρέχει μέσα στο laptop σου. Το θέλουμε στο Μέρος 5, οπότε το ξεκινάμε τώρα για να έχει χρόνο να κατέβει.

1. Εγκατάστησε το Ollama:
   - **macOS / Windows:** ollama.com/download, κατέβασε και άνοιξε το installer.
   - **Linux:**
     ```bash
     curl -fsSL https://ollama.com/install.sh | sh
     ```
2. Άνοιξε ένα **νέο** terminal (στα Windows: PowerShell) και γράψε:
   ```bash
   ollama pull gemma3:1b
   ```
   Είναι περίπου 0,8 GB.
3. **Άφησέ το να τρέχει.** Μην κλείσεις το παράθυρο ούτε το laptop.

## 3. Python και Git

Έλεγξε αν τα έχεις ήδη. Στο terminal, διάλεξε την εντολή για το λειτουργικό σου:

- **Windows (PowerShell):** `py --version` και `git --version`
- **macOS / Linux:** `python3 --version` και `git --version`

Χρειάζεσαι Python 3.10 ή νεότερη. Αν κάτι λείπει:

- **Windows:** Python από το python.org (στον installer τσέκαρε **«Add python.exe to PATH»**) και Git από το git-scm.com. Μετά άνοιξε νέο terminal.
- **macOS:** εγκατέστησε Python 3.10+ από το python.org. Αν το `git --version` αποτύχει, το Mac θα προτείνει τα **Command Line Tools**· πάτα **Install** για το Git.
- **Linux (Ubuntu/Debian):**
  ```bash
  sudo apt install python3 python3-venv git
  ```
  Μετά έλεγξε ξανά ότι το `python3 --version` είναι 3.10 ή νεότερο. Αν είναι παλαιότερο, δες τη σελίδα «Όταν κολλήσεις» ή ρώτα στο κανάλι **#agy** στο Discord.

## 4. Το δικό σου Gemini API key

1. Άνοιξε το **aistudio.google.com** και κάνε login με το ίδιο Gmail.
2. Πάτα **Get API key** → **Create API key**. Είναι δωρεάν και δεν θέλει κάρτα.
3. Κράτα το κλειδί κάπου ιδιωτικά (π.χ. σε ένα σημείωμα στο laptop). **Μην το στείλεις σε κανέναν και μην το επικολλήσεις σε chat.** Θα το βάλουμε σε ασφαλές αρχείο στο Μέρος 2.

## 5. Chrome

Βάλε τον **Chrome** ως προεπιλεγμένο browser. Ο agent τον ανοίγει για να δοκιμάζει το app.

---

## Checkpoint (στο 0:20)

- [ ] Το Antigravity είναι ανοιχτό και έχεις κάνει login.
- [ ] Η Python είναι 3.10 ή νεότερη (`py --version` στα Windows, `python3 --version` σε macOS / Linux) και το `git --version` απαντά.
- [ ] Έχεις API key.
- [ ] Το `ollama pull gemma3:1b` τρέχει ή έχει τελειώσει.

Αν το Ollama δεν έχει τελειώσει, δεν πειράζει: συνεχίζει μόνο του μέχρι το Μέρος 5.
