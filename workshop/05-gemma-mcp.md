# Μέρος 5 — Ιδιωτικό και ανοιχτό: Gemma και MCP

**Διάρκεια:** 25 λεπτά · **Project:** `study-copilot`

Πρώτα το app αποκτά **ιδιωτική λειτουργία** με το Gemma, που τρέχει μέσα στο laptop σου. Μετά γίνεται **εργαλείο που μπορούν να χρησιμοποιήσουν AI agents** (MCP server).

**Χρειάζεσαι:** το μικρό Gemma που ξεκίνησες να κατεβαίνει στην αρχή. Έλεγξε στο terminal με `ollama list` ότι φαίνεται το `gemma3:1b`. Αν το κατέβασμα δεν έχει τελειώσει, δούλεψε με τον διπλανό σου και συνέχισε κανονικά από το Β (MCP).

---

## Α. Ιδιωτική λειτουργία με Gemma

### Βήμα 1: Γνώρισε το Gemma

Στο terminal:

```bash
ollama run gemma3:1b "Πες μου σε μία πρόταση τι είναι το ΑΠΘ."
```

**Τι ελέγχεις:** ένα μοντέλο **μέσα στο laptop σου** απαντά στα ελληνικά.

> Το `gemma3:1b` είναι μικρό, οπότε οι απαντήσεις του είναι πιο απλές από του Gemini. Αυτό είναι το αντάλλαγμα για να τρέχει παντού. Έχεις καλή σύνδεση και 8 GB RAM ή περισσότερο; Στο σπίτι δοκίμασε και το `gemma4:e2b` (περίπου 7 GB).

### Βήμα 2: Ο agent προσθέτει ιδιωτική λειτουργία

```
Add a "private mode": llm_client.py with two backends behind one interface, Gemini and a local Gemma model through Ollama (LOCAL_MODEL, default gemma3:1b). Extract the PDF text with pypdf and reuse the same JSON schema via Ollama's format parameter. UI toggle "Ιδιωτική λειτουργία". Tests for both backends.
```

**Τι ελέγχεις:**
- [ ] Υπάρχει διακόπτης «Ιδιωτική λειτουργία» στη σελίδα.
- [ ] Τα tests περνάνε και για τα δύο backends.

### Βήμα 3: Σύγκρινε

Φτιάξε quiz για το ίδιο PDF με και χωρίς ιδιωτική λειτουργία και συμπλήρωσε:

| | Gemini | Gemma |
|---|---|---|
| Χρόνος για quiz | | |
| «Unsupported» από τον κριτή | | |
| Πού πάνε τα δεδομένα | Cloud | Laptop |
| Κόστος και όρια | Δωρεάν με όρια | Δωρεάν, χωρίς όρια |

Για τη μέτρηση με τον κριτή:

```
Generate a quiz for lecture3.pdf in private mode, then ask grounding-critic to check it and compare with the Gemini quiz from before.
```

### Βήμα 4: Το τεστ του Wi-Fi

1. **Κλείσε το Wi-Fi.**
2. Άνοιξε το app, ενεργοποίησε την **ιδιωτική λειτουργία** και ανέβασε το `sample_lectures/lecture4.pdf`. Είναι διάλεξη που δεν έχεις ξαναστείλει, άρα το quiz φτιάχνεται τώρα από το Gemma και όχι από το cache.
3. **Άνοιξε ξανά το Wi-Fi.**

> Με κλειστό Wi-Fi δουλεύει το **app** σου. Ο agent του Antigravity χρειάζεται internet για να σκεφτεί, γι' αυτό το Wi-Fi κλείνει μόνο για το τεστ.

---

## Β. Το app γίνεται MCP server

### Βήμα 1: Ο agent φτιάχνει τον server

```
Turn Study Copilot into an MCP server too. Create mcp_server.py with the official Python MCP SDK pinned to mcp<2 (from mcp.server.fastmcp import FastMCP), stdio transport, exposing three tools that reuse llm_client.py: summarize_lecture(pdf_path, private), make_flashcards(pdf_path, count, private), make_quiz(pdf_path, questions, private). Write clear tool descriptions, because agents choose tools from them. Load .env from the project folder. Add a test that lists the tools, and a README section with the config.
```

### Βήμα 2: Βρες το απόλυτο path

Στο terminal, μέσα στον φάκελο του project:

```bash
pwd
```

Σημείωσε αυτό που τυπώνει (π.χ. `/Users/maria/agy-101/study-copilot`).

### Βήμα 3: Δήλωσε τον server στο Antigravity

**Settings → Customizations → Open MCP Config** και πρόσθεσε το block από το [`templates/mcp_config.json`](templates/mcp_config.json), αντικαθιστώντας το path με το δικό σου.

**Mac / Linux:**
```json
{
  "mcpServers": {
    "study-copilot": {
      "command": "/Users/maria/agy-101/study-copilot/.venv/bin/python",
      "args": ["/Users/maria/agy-101/study-copilot/mcp_server.py"]
    }
  }
}
```

**Windows** (διπλά backslashes):
```json
{
  "mcpServers": {
    "study-copilot": {
      "command": "C:\\Users\\maria\\agy-101\\study-copilot\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\maria\\agy-101\\study-copilot\\mcp_server.py"]
    }
  }
}
```

### Βήμα 4: Χρησιμοποίησέ το από νέα συζήτηση, ΧΩΡΙΣ project

Ξεκίνα **New Conversation** χωρίς να διαλέξεις project, για να φανεί ότι ο agent χρησιμοποιεί το **εργαλείο** και όχι τον κώδικα.

Πρώτα έλεγχος:

```
Which tools does study-copilot expose?
```

Μετά:

```
Use study-copilot to quiz me with 3 questions on /ΑΠΟΛΥΤΟ/PATH/study-copilot/sample_lectures/lecture5.pdf, one at a time, in private mode, and grade my answers.
```

**Τι ελέγχεις:** στη συζήτηση φαίνεται κλήση στο `make_quiz` του `study-copilot`, και το quiz γίνεται ερώτηση-ερώτηση.

---

## Checkpoint

- [ ] Quiz με κλειστό Wi-Fi σε ιδιωτική λειτουργία.
- [ ] Κλήση στο `make_quiz` από νέα συζήτηση χωρίς project.
- [ ] Commit.

Έμεινες πίσω; `git checkout checkpoint-5`

## Boss levels

Δες το [`07-boss-levels.md`](07-boss-levels.md#μέρος-5).
