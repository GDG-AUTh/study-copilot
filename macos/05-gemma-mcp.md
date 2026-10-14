[Ευρετήριο](README.md) · Οδηγός για macOS · Σελίδα 6 από 8

# Μέρος 5: Ιδιωτικό και ανοιχτό, Gemma και MCP (macOS)

**Χρόνος:** περίπου 35 λεπτά · **Project:** `study-copilot`

Δύο αλλαγές στο app:

1. **Ιδιωτική λειτουργία:** το PDF πηγαίνει στο Gemma, που τρέχει μέσα στον υπολογιστή σου, αντί για το Gemini στο cloud.
2. **MCP server:** το app γίνεται εργαλείο που μπορεί να χρησιμοποιήσει οποιοσδήποτε AI agent, και από άλλες συζητήσεις.

Αν σου μένει λίγος χρόνος, κάνε το Α. Το Β μπορείς να το κάνεις άλλη μέρα.

---

## Πριν ξεκινήσεις

Εντολή στο terminal:

```
ollama list
```

Πρέπει να βλέπεις το `gemma3:1b`. Αν όχι, τρέξε `ollama pull gemma3:1b` και περίμενε να γράψει `success`.

Το Ollama πρέπει να τρέχει. Αν δεν βλέπεις το εικονίδιό του πάνω δεξιά, άνοιξέ το από το Applications.
> **Τι είναι ιδιωτικό και τι όχι.** Στην ιδιωτική λειτουργία το **app** στέλνει το PDF στο Gemma, στον υπολογιστή σου. Ο agent του Antigravity όμως δουλεύει στο cloud. Αν ανεβάσεις ένα PDF ή επικολλήσεις αποτελέσματα σε συζήτηση με τον agent, αυτά φεύγουν από τον υπολογιστή σου. Γι' αυτό σε αυτό το μέρος χρησιμοποίησε μόνο τα PDF του `sample_lectures/`.

---

## Α. Ιδιωτική λειτουργία με Gemma

### Βήμα 1: Γνώρισε το Gemma

Εντολή στο terminal:

```
ollama run gemma3:1b "Whats the difference between computer science and computer engineering?"
```

**Τι πρέπει να δεις:** μια απάντηση που γράφεται σιγά σιγά. Την πρώτη φορά μπορεί να αργήσει λίγα δευτερόλεπτα να ξεκινήσει.


Το `gemma3:1b` είναι μικρό μοντέλο, οπότε οι απαντήσεις του είναι πιο απλές από του Gemini. Σε αντάλλαγμα, τρέχει σχεδόν σε κάθε laptop. Αν έχεις 8 GB RAM ή περισσότερο, μπορείς αργότερα να δοκιμάσεις και το `gemma4:e2b` (περίπου 7 GB).

### Βήμα 2: Ο agent προσθέτει ιδιωτική λειτουργία

Prompt για τον agent:

```
Add a "private mode": llm_client.py with two backends behind one interface, Gemini and a local Gemma model through Ollama (LOCAL_MODEL, default gemma3:1b). Extract the PDF text with pypdf and reuse the same JSON schema via Ollama's format parameter. UI toggle "Ιδιωτική λειτουργία". Keep the cache key specific to the PDF content and backend/model so cached Gemini results are never shown as Gemma results (or vice versa). Tests for both backends and for cache separation.
```

**Τι πρέπει να δεις:**

- [ ] Στη σελίδα του app υπάρχει διακόπτης «Ιδιωτική λειτουργία».
- [ ] Τα tests περνάνε για τα δύο backends (`.venv/bin/python -m pytest`).


### Βήμα 3: Σύγκρινε Gemini και Gemma

Στο app, ανέβασε το `lecture3.pdf` μία φορά **χωρίς** και μία **με** ιδιωτική λειτουργία. Έλεγξε ότι η ένδειξη μοντέλου αλλάζει και ότι δεν εμφανίζεται το προηγούμενο αποτέλεσμα από το άλλο μοντέλο. Συμπλήρωσε:

| | Gemini | Gemma |
|---|---|---|
| Χρόνος για το quiz | | |
| `unsupported` από τον κριτή | | |
| Πού πηγαίνουν τα δεδομένα | Cloud | Ο υπολογιστής σου |
| Κόστος και όρια | Δωρεάν, με όριο κλήσεων | Χωρίς χρέωση, περιορίζεται από τη μνήμη και την ταχύτητα του υπολογιστή |

Για τη μέτρηση με τον κριτή, prompt για τον agent:

```
Generate a quiz for lecture3.pdf in private mode, then ask grounding-critic to check it and compare with the Gemini quiz from before.
```

### Βήμα 4: Το τεστ χωρίς internet

1. **Κλείσε το Wi-Fi.** 2. Στο app, ενεργοποίησε την **Ιδιωτική λειτουργία** και ανέβασε το `sample_lectures/lecture4.pdf`. Είναι διάλεξη που δεν έχεις στείλει ξανά, οπότε το αποτέλεσμα φτιάχνεται τώρα από το Gemma και όχι από το cache.
3. **Τι πρέπει να δεις:** το quiz εμφανίζεται, ενώ δεν έχεις internet.
4. **Άνοιξε ξανά το Wi-Fi.** 
Με κλειστό Wi-Fi δουλεύει το **app**. Ο agent του Antigravity χρειάζεται internet, γι' αυτό κλείνεις το Wi-Fi μόνο για αυτό το τεστ.

Κάνε commit πριν προχωρήσεις: `Commit all changes with a clear message.`

---

## Β. Το app γίνεται MCP server

Το MCP (Model Context Protocol) είναι ένας κοινός τρόπος με τον οποίο οι AI agents χρησιμοποιούν εξωτερικά εργαλεία. Στο τέλος αυτού του μέρους, θα μπορείς να ανοίξεις μια οποιαδήποτε συζήτηση στο Antigravity και να ζητήσεις quiz από ένα PDF, χωρίς να ανοίξεις το app.

### Βήμα 1: Ο agent φτιάχνει τον server

Prompt για τον agent:

```
Turn Study Copilot into an MCP server too. Create mcp_server.py with the official Python MCP SDK (requirement mcp>=1.20,<2; import FastMCP from mcp.server.fastmcp), stdio transport, and three tools that reuse llm_client.py: summarize_lecture(pdf_path, private), make_flashcards(pdf_path, count, private), make_quiz(pdf_path, questions, private). Add mcp>=1.20,<2 to requirements.txt and make sure the project's .venv installs it. Write clear tool descriptions. Load .env from the folder containing mcp_server.py, regardless of the process working directory. Keep stdout free for the MCP protocol (send diagnostics to stderr). Add a test that lists the tools, run the tests with the project's .venv Python, and add a README section with the config.
```

> Στην ιδιωτική λειτουργία μέσω MCP, το app στέλνει το PDF στο Gemma. Το αποτέλεσμα όμως (π.χ. το quiz) επιστρέφει στη συζήτηση του Antigravity, και ο agent μπορεί να το στείλει στο cloud μοντέλο του. Άρα δεν είναι πλήρως offline.

### Βήμα 2: Έλεγξε ότι το venv έχει όσα χρειάζονται

Εντολές στο terminal, μέσα στο `study-copilot`, μία μία:

```
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -c "from mcp.server.fastmcp import FastMCP; print('MCP SDK OK')"
.venv/bin/python -m pytest
```

**Τι πρέπει να δεις:** `MCP SDK OK` και όλα τα tests `passed`.

Αν γράψει ότι δεν υπάρχει το `.venv`, φτιάξ' το με `python3 -m venv .venv` και ξανατρέξε τις τρεις εντολές.

### Βήμα 3: Φτιάξε το κομμάτι ρυθμίσεων

Το Antigravity πρέπει να ξέρει πού βρίσκεται ο server στον δικό σου υπολογιστή. Αντί να γράψεις τις διαδρομές με το χέρι, η παρακάτω εντολή τις τυπώνει έτοιμες. Τρέξ' την στο terminal, **μέσα στο `study-copilot`**:

```bash
.venv/bin/python -c 'import json,os; r=os.getcwd(); print(json.dumps({"mcpServers":{"study-copilot":{"command":r+"/.venv/bin/python","args":[r+"/mcp_server.py"],"cwd":r}}}, indent=2))'
```

**Τι πρέπει να δεις:** κάτι σαν το παρακάτω, με το δικό σου όνομα χρήστη:

```json
{
  "mcpServers": {
    "study-copilot": {
      "command": "/Users/maria/agy-101/study-copilot/.venv/bin/python",
      "args": [
        "/Users/maria/agy-101/study-copilot/mcp_server.py"
      ],
      "cwd": "/Users/maria/agy-101/study-copilot"
    }
  }
}
```

Αντίγραψε όλο αυτό που τύπωσε.


### Βήμα 4: Δήλωσε τον server στο Antigravity

1. Στο Antigravity άνοιξε τις ρυθμίσεις MCP. Ανάλογα με την έκδοση: **Settings → Customizations → Open MCP Config**, ή από το μενού **…** → **MCP Servers** → **Manage MCP Servers** → **View raw config**.
2. Ανοίγει το αρχείο `mcp_config.json` (βρίσκεται στο `~/.gemini/config/mcp_config.json`).
3. Αν το αρχείο είναι **άδειο** ή έχει μόνο `{}` ή `{"mcpServers": {}}`: σβήσε ό,τι έχει και επικόλλησε αυτό που αντέγραψες.
4. Αν έχει **ήδη άλλους servers** μέσα στο `"mcpServers"`: μην σβήσεις τίποτα. Πρόσθεσε μόνο το κομμάτι `"study-copilot": { ... }` μέσα στο υπάρχον `"mcpServers"`, με κόμμα ανάμεσα σε αυτό και τον προηγούμενο server.
5. Αποθήκευσε (`Cmd + S`).
6. Αν υπάρχει κουμπί ανανέωσης (refresh) των MCP servers, πάτησέ το.


**Τι πρέπει να δεις:** στη λίστα των MCP servers εμφανίζεται το `study-copilot`, χωρίς κόκκινο σφάλμα.

### Βήμα 5: Δοκίμασέ το από συζήτηση χωρίς project

Ξεκίνα **New Conversation** χωρίς να διαλέξεις project. Έτσι φαίνεται ότι ο agent χρησιμοποιεί το εργαλείο και όχι τον κώδικα του project.

Prompt για τον agent:

```
Which tools does study-copilot expose?
```

**Τι πρέπει να δεις:** τα `summarize_lecture`, `make_flashcards` και `make_quiz`.

Μετά, prompt για τον agent, βάζοντας τη δική σου διαδρομή:

```
Use study-copilot to quiz me with 3 questions on /Users/maria/agy-101/study-copilot/sample_lectures/lecture5.pdf, one at a time, in private mode, and grade my answers.
```

Άλλαξε το `/Users/maria` με τον δικό σου φάκελο (αυτό που έδειξε το `pwd` στο Μέρος 1).

**Τι πρέπει να δεις:** στη συζήτηση εμφανίζεται κλήση στο `make_quiz` του `study-copilot` και ο agent σού κάνει τις ερωτήσεις μία μία.


---

## Checkpoint

- [ ] Quiz σε ιδιωτική λειτουργία με κλειστό Wi-Fi.
- [ ] Κλήση στο `make_quiz` από νέα συζήτηση χωρίς project.
- [ ] Commit.

Αν έμεινες πίσω, η έτοιμη λύση είναι στο `checkpoint-5`. Δες το [`08-otan-kolliseis.md`](08-otan-kolliseis.md#έμεινα-πίσω). Αν ο MCP server δεν εμφανίζεται, δες το [`08-otan-kolliseis.md`](08-otan-kolliseis.md#mcp-server).

Περισσότερες ασκήσεις: [`07-boss-levels.md`](07-boss-levels.md#μέρος-5)


---

[← Προηγούμενο: Κανόνες και κριτής](04-kanones-kritis.md) · [Ευρετήριο](README.md) · [Επόμενο: Ship it →](06-ship-it.md)
