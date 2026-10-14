# Study Copilot — starter για το Antigravity 101

Καλώς ήρθες στο workshop **Antigravity 101** του GDG on Campus AUTH!

Σε αυτό το repo θα χτίσεις, μαζί με τον agent του Antigravity, το **Study Copilot**: μια web εφαρμογή που παίρνει τις διαφάνειες ενός μαθήματος σε PDF και βγάζει **περίληψη, flashcards και quiz**, με το Gemini στο cloud ή με το Gemma μέσα στο laptop σου.

**Κόστος: 0 €.** Δεν χρειάζεσαι κάρτα, cloud credits ή συνδρομή.

## Τι υπάρχει εδώ

```
study-copilot/
├── README.md              ← είσαι εδώ
├── sample_lectures/       ← οκτώ διαλέξεις σε PDF, μία για κάθε βήμα του workshop
│   ├── lecture1.pdf       (Αλγόριθμοι ταξινόμησης)
│   ├── lecture2.pdf       (Γράφοι, BFS και DFS)
│   └── lecture3–8.pdf     (κατακερματισμός, ΔΠ, BST, σωροί, Dijkstra, πολυπλοκότητα)
├── tests/fixtures/
│   └── tiny.pdf           ← μικρό PDF για τα tests
└── workshop/              ← ΟΛΑ τα prompts του workshop, με τη σειρά
    ├── README.md
    ├── 00-egkatastaseis.md … 08-otan-kolliseis.md
    └── templates/         ← κανόνες, skill, subagent, MCP config
```

> Βρίσκεσαι σε **checkpoint branch**: εδώ υπάρχει ήδη η έτοιμη λύση. Δες «Τρέξε το app» πιο κάτω.

## Τρέξε το app

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # και βάλε το GEMINI_API_KEY σου μέσα στο .env
python app.py                      # άνοιξε http://127.0.0.1:8000
pytest                             # τα tests τρέχουν και χωρίς internet
python cli.py sample_lectures/lecture2.pdf out/lecture2.json   # υλικό σε JSON, π.χ. για τον grounding-critic
```

Σε αυτό το checkpoint υπάρχουν επίσης:
- `AGENTS.md`: οι κανόνες που διαβάζει ο agent σε κάθε μήνυμα.
- `.agents/skills/add-study-mode/`: η «συνταγή» για νέο study mode.
- `.agents/agents/grounding-critic.md`: ο subagent που ελέγχει αν το υλικό στηρίζεται στο PDF.
- Η καρτέλα «Ορισμοί» και ερωτήσεις quiz με απόσπασμα από τη διάλεξη.

## Στην αρχή του workshop: εγκαταστάσεις

Δεν χρειάζεται να έχεις ετοιμάσει τίποτα από πριν. Στην αρχή του workshop, όσο ακούς την εισαγωγή, κατεβάζεις και εγκαθιστάς:

- [ ] **Antigravity**: antigravity.google/download, login με προσωπικό Gmail
- [ ] **Ollama** (ollama.com/download) και σε νέο terminal `ollama pull gemma3:1b` (περίπου 0,8 GB, το αφήνεις να τρέχει)
- [ ] **Python 3.10+** και **Git**
- [ ] **Gemini API key**: aistudio.google.com → Get API key (δωρεάν, χωρίς κάρτα)
- [ ] **Chrome** ως προεπιλεγμένος browser

Αναλυτικά, για κάθε λειτουργικό: [`workshop/00-egkatastaseis.md`](workshop/00-egkatastaseis.md). Λογαριασμό GitHub θα χρειαστείς μόνο στο Μέρος 6 και τον φτιάχνεις σε ένα λεπτό.

## Ξεκίνα εδώ

1. Κάνε clone αυτό το repo:
   ```bash
   git clone <URL αυτού του repo> ~/agy-101/study-copilot
   ```
2. Στο Antigravity: **Create New Project** → διάλεξε τον φάκελο → **Security Preset: Default**.
3. Άνοιξε το [`workshop/README.md`](workshop/README.md) και ακολούθησε τα prompts με τη σειρά.

## Checkpoint branches

Αν μείνεις πίσω, μην αγχώνεσαι: κάθε branch έχει την έτοιμη λύση στο τέλος ενός μέρους.

| Branch | Τι έχει |
|---|---|
| `main` | Η αφετηρία (αυτό που βλέπεις τώρα) |
| `checkpoint-3` | Το Study Copilot με Gemini, τρεις καρτέλες, cache και tests με mock |
| `checkpoint-4` | + κανόνες (`AGENTS.md`), skill, κριτής, καρτέλα «Ορισμοί», `cli.py` |
| `checkpoint-5` | + ιδιωτική λειτουργία με Gemma και `mcp_server.py` |

```bash
git stash
git fetch origin
git checkout checkpoint-3
```

## Τρεις κανόνες για όλη τη μέρα

1. **Ποτέ API key μέσα σε prompt, screenshot ή commit.** Το γράφεις μόνο εσύ, στο αρχείο `.env`.
2. **Πρώτα διαβάζεις το πλάνο, μετά πατάς Proceed.**
3. **Όταν ο agent λέει «έτοιμο», ζητάς απόδειξη.**

Κόλλησες; Δες το [`workshop/08-otan-kolliseis.md`](workshop/08-otan-kolliseis.md) ή σήκωσε χέρι.

---

Οι διαλέξεις στο `sample_lectures/` είναι πρωτότυπο υλικό του GDG on Campus AUTH (CC BY 4.0), φτιαγμένο μόνο για το workshop.
