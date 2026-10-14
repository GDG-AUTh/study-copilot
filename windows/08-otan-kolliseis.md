[Ευρετήριο](README.md) · Οδηγός για Windows

# Όταν κολλήσεις (Windows)

Βρες τον πίνακα που ταιριάζει με το πρόβλημα, μετά τη γραμμή με αυτό που βλέπεις, και κάνε ό,τι γράφει. Αν τίποτα δεν βοηθά, γράψε στο κανάλι **#agy** στο Discord (δες στο τέλος).

**Γενικό prompt για οτιδήποτε δεν δουλεύει**, για τον agent:

```
Something is not working: <describe what you see, e.g. "the quiz tab stays empty">. Find the cause, explain it to me in one sentence, fix it, and show me proof that it works now.
```

---

## Εγκαταστάσεις στο Windows

| Τι βλέπεις | Τι κάνεις |
|---|---|
| `py : The term 'py' is not recognized` | Η Python δεν εγκαταστάθηκε ή δεν άνοιξες νέο PowerShell. Κλείσε και άνοιξε ξανά το PowerShell. Αν συνεχίζει, ξανατρέξε τον installer της Python και τσέκαρε **Add python.exe to PATH**. |
| Γράφεις `python` και ανοίγει το Microsoft Store | Χρησιμοποίησε `py` αντί για `python`. |
| `git : The term 'git' is not recognized` | Άνοιξε νέο PowerShell. Αν συνεχίζει, εγκατάστησε το Git από το git-scm.com/downloads/win. |
| `ollama : The term 'ollama' is not recognized` | Άνοιξε νέο PowerShell. Αν συνεχίζει, ξανατρέξε το `OllamaSetup.exe`. |
| **Windows protected your PC** όταν ανοίγεις installer | **More info** → **Run anyway**. Μόνο για αρχεία που κατέβασες από τις σελίδες αυτού του οδηγού. |
| `mkdir : An item with the specified name ... already exists` | Ο φάκελος υπάρχει ήδη. Αγνόησέ το και συνέχισε με την επόμενη εντολή. |
| Το `.env` αποθηκεύτηκε ως `.env.txt` | Στον File Explorer ενεργοποίησε **View → Show → File name extensions** και μετονόμασε το αρχείο σε `.env`. |

## Στήσιμο και API key

| Τι βλέπεις | Τι κάνεις |
|---|---|
| Δεν έχω API key | aistudio.google.com → **Get API key** → **Create API key**. Δωρεάν, χωρίς κάρτα. |
| `Missing API key` ή παρόμοιο | Άνοιξε το `.env` (`notepad .env`) και έλεγξε ότι η γραμμή είναι `GEMINI_API_KEY=...` χωρίς κενά και χωρίς εισαγωγικά. Μετά σταμάτα τον server (`Ctrl + C` στο terminal όπου τρέχει) και ξεκίνα τον ξανά. |
| Το `.env` εμφανίζεται στο `git status` | Στο `.gitignore` πρέπει να υπάρχει μια γραμμή που γράφει μόνο `.env`. Πρόσθεσέ τη και αποθήκευσε. |
| Συνέχεια παράθυρα «Allow;» | Για εντολές μέσα στον φάκελο του project διάλεξε **Always allow in this project**. |
| Το `git clone` αποτυγχάνει | Κατέβασε το repo ως ZIP: στη σελίδα του repo **Code → Download ZIP**. |

## Gemini

| Τι βλέπεις | Τι κάνεις |
|---|---|
| Σφάλμα `429` ή `quota exceeded` | Έφτασες το όριο του δωρεάν Gemini. Περίμενε 1-2 λεπτά και ξαναδοκίμασε, ή χρησιμοποίησε την ιδιωτική λειτουργία με Gemma. |
| Κενή περίληψη | Το PDF είναι μάλλον σκαναρισμένο (μόνο εικόνες, χωρίς κείμενο). Χρησιμοποίησε τα PDF του `sample_lectures/`. |
| Το app «σκάει» με περίεργη απάντηση του μοντέλου | Prompt παρακάτω. |

```
The app crashed when the model returned an unexpected response. Make it show a friendly Greek error instead of crashing, and add a test for this case with the mock.
```

## Tests

| Τι βλέπεις | Τι κάνεις |
|---|---|
| `pytest` δεν αναγνωρίζεται | Τρέξε τα tests πάντα με την Python του venv: `.\.venv\Scripts\python.exe -m pytest` |
| `No module named pytest` | `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` και ξανά. Αν δεν υπάρχει `pytest` στο `requirements.txt`, ζήτα από τον agent να το προσθέσει. |
| Τα tests αποτυγχάνουν χωρίς internet | Κάποιο test καλεί το πραγματικό Gemini. Prompt παρακάτω. |

```
Make every test use the mock; no network in tests. Run pytest with Wi-Fi off in mind and show me the result.
```

## Browser agent

| Τι βλέπεις | Τι κάνεις |
|---|---|
| Το `/browser` δεν ανοίγει τον Chrome | Ο Chrome πρέπει να είναι ο προεπιλεγμένος browser (Μέρος 1, βήμα 2). Πάτα **Allow** στο remote debugging. |
| Ο agent δεν βρίσκει το app | Ο server πρέπει να τρέχει. Γράψε στον agent τη διεύθυνση, π.χ. `http://localhost:5000`. |

## Rules, skills, subagents

| Τι βλέπεις | Τι κάνεις |
|---|---|
| Ο agent δεν χρησιμοποιεί το skill | Το αρχείο πρέπει να είναι ακριβώς στο `.agents/skills/add-study-mode/SKILL.md`. Ξανατρέξε τις εντολές αντιγραφής του Μέρους 4. |
| Ο κανόνας για τα prompts αγνοείται | Έλεγξε το frontmatter στην αρχή του αρχείου: `trigger: glob` και `globs: "prompts/*.md"`. |
| Ο `grounding-critic` κολλάει | Αντίγραψε ξανά το αρχείο από το `workshop/templates/` χωρίς αλλαγές. |
| Το μοντέλο `pro` δεν είναι διαθέσιμο | Σβήσε τη γραμμή `model: pro` από το `.agents/agents/grounding-critic.md`. |

```
You did not follow the add-study-mode skill. Read .agents/skills/add-study-mode/SKILL.md and complete the missing steps.
```

## Gemma και Ollama

| Τι βλέπεις | Τι κάνεις |
|---|---|
| `connection refused` στο `localhost:11434` | Το Ollama δεν τρέχει. Άνοιξε την εφαρμογή Ollama από το Start. |
| `model not found` | Τρέξε `ollama list` και έλεγξε ότι το όνομα είναι ακριβώς `gemma3:1b`. Αν λείπει: `ollama pull gemma3:1b`. |
| Πολύ αργό ή κολλάει | Κλείσε καρτέλες του browser και άλλα προγράμματα. Το μικρό μοντέλο θέλει περίπου 2 GB ελεύθερης μνήμης. |
| Λείπουν πεδία στην απάντηση | Το PDF είναι μεγάλο για το μικρό μοντέλο. Prompt παρακάτω. |

```
In private mode the model sometimes returns incomplete JSON for long PDFs. Limit the text sent to Gemma to the first 15 pages and retry once if the JSON does not match the schema. Add a test.
```

## MCP server

| Τι βλέπεις | Τι κάνεις |
|---|---|
| Ο server δεν εμφανίζεται | Το `mcp_config.json` πρέπει να είναι έγκυρο JSON. Συνηθισμένα λάθη: κόμμα που λείπει ανάμεσα σε δύο servers, κόμμα στο τέλος του τελευταίου, ή το `study-copilot` γραμμένο δύο φορές. Αποθήκευσε, πάτα ανανέωση αν υπάρχει, και άνοιξε νέα συζήτηση. |
| Ο server δεν ξεκινά | Ξανατρέξε την εντολή του Μέρους 5, Β, Βήμα 3 **μέσα στο `study-copilot`** και αντικατάστησε το block με αυτό που τυπώνει. Στο JSON τα `\` πρέπει να είναι διπλά (`\\`). |
| `No module named 'mcp.server.fastmcp'` | `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`. Το `requirements.txt` πρέπει να περιέχει `mcp>=1.20,<2`. |
| Δεν υπάρχει ο φάκελος `.venv` | Μέσα στο `study-copilot`: `py -3 -m venv .venv`, μετά εγκατάσταση με την εντολή από πάνω. |
| Έλεγχος ότι το MCP SDK είναι στο venv | `.\.venv\Scripts\python.exe -c "from mcp.server.fastmcp import FastMCP; print('MCP SDK OK')"` |
| Ο agent δεν καλεί το εργαλείο | Οι περιγραφές των εργαλείων είναι ασαφείς. Prompt παρακάτω. |

```
Improve the tool descriptions in mcp_server.py so an agent clearly knows when to use each tool and what arguments to pass. Then run the test that lists the tools.
```

## GitHub

| Τι βλέπεις | Τι κάνεις |
|---|---|
| Το push ζητά login | Πάτα **Sign in with your browser** στο παράθυρο που ανοίγει και **Authorize** στον Chrome. |
| `remote: Repository not found` | Λάθος username στο `git remote set-url`. Έλεγξε με `git remote -v`. |
| `rejected ... fetch first` | Το repo στο GitHub δεν είναι άδειο (π.χ. τσέκαρες «Add a README»). Σβήσε το repo στο GitHub και φτιάξ' το ξανά άδειο. |
| Το GIF είναι πολύ μεγάλο | Prompt: `Make docs/demo.gif smaller than 5 MB.` |
| Ανέβηκε κλειδί κατά λάθος | **Σβήσε το κλειδί αμέσως** στο aistudio.google.com και φτιάξε νέο. Μετά prompt παρακάτω. |

```
An API key was committed by mistake. Remove it from the repo and from the git history, make sure .env is ignored, and tell me exactly what I need to push.
```

## Έμεινα πίσω

Υπάρχουν έτοιμες λύσεις για το τέλος κάθε μέρους: `checkpoint-3`, `checkpoint-4` και `checkpoint-5`. Το `checkpoint-N` είναι το project όπως πρέπει να είναι στο τέλος του Μέρους N.

1. Έλεγξε ότι το `.env` και το `.venv` **δεν** εμφανίζονται στο `git status`.
2. Σημείωσε σε ποιο branch είσαι. Εντολή:
   ```
   git branch --show-current
   ```
3. Φύλαξε τη δουλειά σου και πήγαινε στο checkpoint. Εντολές, μία μία (το `checkpoint-3` είναι παράδειγμα: διάλεξε αυτό που χρειάζεσαι):
   ```
   git stash push --include-untracked -m "workshop checkpoint"
   git fetch origin
   git switch checkpoint-3
   ```
4. Εγκατάστησε τις βιβλιοθήκες του checkpoint στο venv σου:
   ```
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

Μην χρησιμοποιήσεις `git stash --all`: θα έβαζε μέσα και το `.env` και ολόκληρο το `.venv`. Μην κάνεις `git stash pop` όσο είσαι στο checkpoint.

Για να γυρίσεις στη δική σου δουλειά: `git switch` και το όνομα του branch από το βήμα 2, μετά `git stash list` για να βρεις τη σωστή εγγραφή και `git stash apply 'stash@{0}'` (άλλαξε το `0` αν η εγγραφή σου είναι σε άλλη θέση). Έλεγξε ότι τα αρχεία σου επέστρεψαν πριν σβήσεις το stash.

---

## Βοήθεια: κανάλι #agy στο Discord

Για το workshop υπάρχει το κανάλι **#agy** στον Discord server του GDG on Campus AUTH. Εκεί μπορείς να κάνεις ερωτήσεις, να στείλεις screenshot από ένα σφάλμα ή να δείξεις τι έφτιαξες. Απαντάνε οι διοργανωτές και οι υπόλοιποι συμμετέχοντες.

Link πρόσκλησης για τον server: **θα προστεθεί εδώ σύντομα.**

Για να πάρεις γρήγορα απάντηση, γράψε στο μήνυμά σου:

1. Το λειτουργικό σου (Windows και έκδοση).
2. Σε ποιο αρχείο και ποιο βήμα είσαι (π.χ. «03-xtizoume, Βήμα Γ»).
3. Την εντολή ή το prompt που έτρεξες.
4. Το μήνυμα σφάλματος, αντιγραμμένο ως κείμενο ή σε screenshot.

Μη στέλνεις ποτέ το API key σου, ούτε screenshot όπου φαίνεται το αρχείο `.env`.


---

[← Πίσω στο ευρετήριο](README.md)
