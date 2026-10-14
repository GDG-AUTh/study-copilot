# Όταν κολλήσεις

Βρες το σύμπτωμα, κάνε ό,τι λέει ή αντίγραψε το prompt. Αν τίποτα δεν βοηθά: ρώτα στο κανάλι **#agy** στο Discord.

**Γενικό prompt για οτιδήποτε:**
```
Something is not working: <περίγραψε τι βλέπεις, π.χ. "the quiz tab stays empty">. Find the cause, explain it to me in one sentence, fix it, and show me proof that it works now.
```

---

## Στήσιμο και API key

| Σύμπτωμα | Τι κάνεις |
|---|---|
| Δεν έχω API key | aistudio.google.com → Get API key → Create. Δωρεάν, χωρίς κάρτα |
| «Missing API key» | Έλεγξε ότι το `.env` έχει `GEMINI_API_KEY=...` (χωρίς κενά, χωρίς εισαγωγικά). Σταμάτα και ξαναξεκίνα τον server |
| Το `.env` φαίνεται στο `git status` | Πρόσθεσε τη γραμμή `.env` στο `.gitignore` |
| Πολλά παράθυρα «Allow;» | Για εντολές μέσα στον φάκελο του project: «Always allow in this project» |
| Το `git clone` αποτυγχάνει | Κατέβασε το repo ως ZIP από το GitHub (Code → Download ZIP) |

## Gemini

| Σύμπτωμα | Τι κάνεις |
|---|---|
| Σφάλμα 429 / «quota exceeded» | Όριο ή ρυθμός κλήσεων του δωρεάν tier. Περίμενε λίγο, δοκίμασε ξανά αργότερα ή συνέχισε με τοπικό Gemma όταν είναι έτοιμο |
| Κενή περίληψη | Μάλλον σκαναρισμένο PDF (μόνο εικόνες). Χρησιμοποίησε τα PDF του `sample_lectures/` |

```
The app crashed when the model returned an unexpected response. Make it show a friendly Greek error instead of crashing, and add a test for this case with the mock.
```

## Tests

| Σύμπτωμα | Τι κάνεις |
|---|---|
| `pytest: command not found` | Τρέξε τα tests με την Python του venv: Windows `.\.venv\Scripts\python.exe -m pytest`, Mac/Linux `.venv/bin/python -m pytest`. |
| Τα tests αποτυγχάνουν χωρίς internet | Κάποιο test καλεί το πραγματικό API |

```
Make every test use the mock; no network in tests. Run pytest with Wi-Fi off in mind and show me the result.
```

## Browser agent

| Σύμπτωμα | Τι κάνεις |
|---|---|
| Το `/browser` δεν ανοίγει | Ο Chrome πρέπει να είναι ο προεπιλεγμένος browser. Πάτα Allow στο remote debugging |
| Ο agent δεν βρίσκει το app | Βεβαιώσου ότι ο server τρέχει. Πες του τη διεύθυνση, π.χ. `http://localhost:5000` |

## Rules, skills, subagents

| Σύμπτωμα | Τι κάνεις |
|---|---|
| Ο agent δεν χρησιμοποιεί το skill | Το αρχείο πρέπει να είναι στο `.agents/skills/add-study-mode/SKILL.md` |
| Ο κανόνας με glob αγνοείται | Έλεγξε το frontmatter: `trigger: glob` και `globs: "prompts/*.md"` |
| Ο grounding-critic «κρεμάει» | Χρησιμοποίησε το αρχείο από το `templates/` χωρίς αλλαγές |
| Ο κριτής λέει ότι το μοντέλο `pro` δεν είναι διαθέσιμο | Σβήσε τη γραμμή `model: pro`· θα τρέξει με το προεπιλεγμένο μοντέλο |

```
You did not follow the add-study-mode skill. Read .agents/skills/add-study-mode/SKILL.md and complete the missing steps.
```

## Gemma / Ollama

| Σύμπτωμα | Τι κάνεις |
|---|---|
| «connection refused» στο `localhost:11434` | Δεν τρέχει το Ollama. Άνοιξε την εφαρμογή Ollama, ή σε άλλο terminal: `ollama serve` |
| «model not found» | Τρέξε `ollama list` και έλεγξε ότι το όνομα είναι ακριβώς `gemma3:1b` (ή αυτό που έχεις στο `LOCAL_MODEL`) |
| `ollama: command not found` | Άνοιξε **νέο** terminal. Αν συνεχίζει, ξαναεγκατάστησε από το ollama.com/download |
| Πολύ αργό ή κλείνει | Κλείσε tabs και άλλα προγράμματα. Αλλιώς δούλεψε με τον διπλανό σου |
| Λείπουν πεδία στην απάντηση | Το PDF είναι μεγάλο για το μικρό μοντέλο |

```
In private mode the model sometimes returns incomplete JSON for long PDFs. Limit the text sent to Gemma to the first 15 pages and retry once if the JSON does not match the schema. Add a test.
```

## MCP server

| Σύμπτωμα | Τι κάνεις |
|---|---|
| Ο server δεν εμφανίζεται | Έλεγξε ότι το config είναι έγκυρο JSON, ότι το block βρίσκεται μέσα στο `mcpServers` και ότι όλες οι διαδρομές δείχνουν στο project σου. Μην προσθέσεις δεύτερη φορά το `study-copilot`. Αποθήκευσε, ανανέωσε τους MCP servers αν υπάρχει επιλογή και άνοιξε νέα συζήτηση. |
| Ο server δεν ξεκινά | Το `command` πρέπει να είναι η Python **του project venv** και τα `args` να δείχνουν στο `mcp_server.py`. Στο Windows config τα `\` γράφονται `\\`. |
| `No module named 'mcp.server.fastmcp'` | Εγκατέστησε τις απαιτήσεις με την Python του venv (όχι με σκέτο `pip`): Windows `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`, Mac/Linux `.venv/bin/python -m pip install -r requirements.txt`. Το `requirements.txt` πρέπει να περιέχει `mcp>=1.20,<2`. |
| Δεν υπάρχει ο φάκελος `.venv` | Από τη ρίζα του project: Windows `py -3 -m venv .venv`, Mac/Linux `python3 -m venv .venv`. Μετά εγκατέστησε τις απαιτήσεις με την εντολή παραπάνω. |
| Θέλω να ελέγξω το MCP SDK στο venv | Windows: `.\.venv\Scripts\python.exe -c "from mcp.server.fastmcp import FastMCP; print('MCP SDK OK')"` · Mac/Linux: `.venv/bin/python -c "from mcp.server.fastmcp import FastMCP; print('MCP SDK OK')"` |
| Άλλαξα το config αλλά τίποτα | Αποθήκευσε το αρχείο, ανανέωσε τους MCP servers αν υπάρχει επιλογή και άνοιξε νέα συζήτηση. |
| Ο agent δεν καλεί το εργαλείο | Η περιγραφή του εργαλείου είναι αόριστη |

```
Improve the tool descriptions in mcp_server.py so an agent clearly knows when to use each tool and what arguments to pass. Then run the test that lists the tools.
```

## GitHub

| Σύμπτωμα | Τι κάνεις |
|---|---|
| Το push ζητά κωδικό | Το GitHub θέλει login από τον browser ή token. Ζήτα οδηγίες από τον agent |
| Το GIF είναι τεράστιο | «Make docs/demo.gif smaller than 5 MB» |
| Ανέβηκε κλειδί κατά λάθος | **Σβήσ' το αμέσως** στο aistudio.google.com και φτιάξε νέο. Μετά: |

```
An API key was committed by mistake. Remove it from the repo and from the git history, make sure .env is ignored, and tell me exactly what I need to push.
```

## Έμεινα πίσω

Κάθε `checkpoint-N` είναι η **έτοιμη λύση στο τέλος του Μέρους N** (υπάρχουν `checkpoint-3`, `checkpoint-4`, `checkpoint-5`).

Πρώτα βεβαιώσου ότι το `.env` και το `.venv` είναι στο `.gitignore` (δεν πρέπει να εμφανίζονται ως αρχεία προς commit). Κατέγραψε το αρχικό branch (`git branch --show-current`). Έπειτα, από τη ρίζα του project:

```bash
git stash push --include-untracked -m "workshop checkpoint"
git fetch origin
git switch checkpoint-3   # π.χ. αν ξεκινάμε το Μέρος 4 και δεν έχεις τελειώσει το 3
```

Το `--include-untracked` κρατά και τα νέα, μη tracked αρχεία σου στο stash. Τα αγνοημένα `.env` και `.venv` μένουν τοπικά και δεν μπαίνουν στο stash· μην χρησιμοποιήσεις `git stash --all`, γιατί μπορεί να συμπεριλάβει μυστικά και ολόκληρο το venv. Μετά την αλλαγή checkpoint, εγκατέστησε τις απαιτήσεις στο υπάρχον venv: Windows `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`, Mac/Linux `.venv/bin/python -m pip install -r requirements.txt`. Μην κάνεις `git stash pop` πάνω στο checkpoint. Για να επιστρέψεις, γύρνα στο branch που κατέγραψες, έλεγξε τη σωστή εγγραφή με `git stash list` και χρησιμοποίησε `git stash apply 'stash@{0}'` (προσαρμόζοντας το `0` αν χρειάζεται). Έλεγξε ότι η εργασία επανήλθε πριν αφαιρέσεις το stash.
