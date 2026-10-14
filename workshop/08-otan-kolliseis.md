# Όταν κολλήσεις

Βρες το σύμπτωμα, κάνε ό,τι λέει ή αντίγραψε το prompt. Αν τίποτα δεν βοηθά: σήκωσε χέρι.

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
| Σφάλμα 429 / «quota exceeded» | Όριο του δωρεάν tier. Περίμενε ένα λεπτό και ξαναδοκίμασε |
| Κενή περίληψη | Μάλλον σκαναρισμένο PDF (μόνο εικόνες). Χρησιμοποίησε τα PDF του `sample_lectures/` |

```
The app crashed when the model returned an unexpected response. Make it show a friendly Greek error instead of crashing, and add a test for this case with the mock.
```

## Tests

| Σύμπτωμα | Τι κάνεις |
|---|---|
| `pytest: command not found` | Ενεργοποίησε το venv: `source .venv/bin/activate` (Windows: `.venv\Scripts\activate`) |
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
| Ο server δεν εμφανίζεται | Στο config πρέπει **απόλυτα paths** (βρίσκεις με `pwd` μέσα στον φάκελο) |
| Ο server δεν ξεκινά | Στο `command` η Python **του venv**: `.venv/bin/python` (Windows: `.venv\\Scripts\\python.exe`) |
| `No module named 'mcp.server.fastmcp'` | Εγκατεστάθηκε το mcp 2.x, όπου το FastMCP μετονομάστηκε. Τρέξε `pip install "mcp<2"` |
| Άλλαξα το config αλλά τίποτα | Άνοιξε νέα συζήτηση |
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

```bash
git stash          # κρατάει στην άκρη ό,τι έχεις αλλάξει
git fetch origin
git checkout checkpoint-3   # π.χ. αν ξεκινάμε το Μέρος 4 και δεν έχεις τελειώσει το 3
```

Μετά ξαναβάλε το `.env` σου αν χρειαστεί (δεν είναι στο Git) και τρέξε `pip install -r requirements.txt`.
