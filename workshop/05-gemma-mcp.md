# Μέρος 5 — Ιδιωτικό και ανοιχτό: Gemma και MCP

**Διάρκεια:** 25 λεπτά · **Project:** `study-copilot`

**Αν ο χρόνος πιέζει:** προτεραιότητα έχει η ιδιωτική λειτουργία και το τεστ με κλειστό Wi-Fi. Το MCP setup μπορείς να το κάνεις αργότερα· μην βιαστείς στις ρυθμίσεις διαδρομών.

Πρώτα το app αποκτά **ιδιωτική λειτουργία** με το Gemma, που τρέχει μέσα στο laptop σου. Μετά γίνεται **εργαλείο που μπορούν να χρησιμοποιήσουν AI agents** (MCP server).

**Χρειάζεσαι:** το μικρό Gemma που ξεκίνησες να κατεβαίνει στην αρχή. Έλεγξε στο terminal με `ollama list` ότι φαίνεται το `gemma3:1b`. Αν το κατέβασμα δεν έχει τελειώσει, δούλεψε με τον διπλανό σου και συνέχισε κανονικά από το Β (MCP).

---

## Α. Ιδιωτική λειτουργία με Gemma

> Η ιδιωτική λειτουργία σημαίνει ότι το **app** στέλνει το PDF στο Ollama που τρέχει τοπικά, αντί στο Gemini. Αν όμως ανεβάσεις το ίδιο PDF ή επικολλήσεις το αποτέλεσμα σε συνομιλία με τον Antigravity agent ή τον `grounding-critic`, αυτό το περιεχόμενο μπορεί να σταλεί στο cloud μοντέλο. Μην χρησιμοποιήσεις πραγματικά ευαίσθητα αρχεία σε αυτά τα βήματα.

### Βήμα 1: Γνώρισε το Gemma

Στο terminal:

```bash
ollama run gemma3:1b "Whats the difference between computer science and computer engineering?"
```


> Το `gemma3:1b` είναι μικρό, οπότε οι απαντήσεις του είναι πιο απλές από του Gemini. Αυτό είναι το αντάλλαγμα για να τρέχει παντού. Έχεις καλή σύνδεση και 8 GB RAM ή περισσότερο; Στο σπίτι δοκίμασε και το `gemma4:e2b` (περίπου 7 GB).

### Βήμα 2: Ο agent προσθέτει ιδιωτική λειτουργία

```
Add a "private mode": llm_client.py with two backends behind one interface, Gemini and a local Gemma model through Ollama (LOCAL_MODEL, default gemma3:1b). Extract the PDF text with pypdf and reuse the same JSON schema via Ollama's format parameter. UI toggle "Ιδιωτική λειτουργία". Keep the cache key specific to the PDF content and backend/model so cached Gemini results are never shown as Gemma results (or vice versa). Tests for both backends and for cache separation.
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
| Κόστος και όρια | Χωρίς χρέωση στο workshop, με quota/rate limits | Χωρίς API χρέωση ή cloud quota, αλλά περιορισμένο από laptop, μνήμη και χρόνο |

Χρησιμοποίησε `lecture3.pdf` για τη σύγκριση και δημιούργησε αποτέλεσμα με κάθε backend. Το cache πρέπει να ξεχωρίζει backend/model· έλεγξε ότι η ένδειξη του μοντέλου είναι σωστή και ότι η εναλλαγή λειτουργίας δεν εμφανίζει το προηγούμενο αποτέλεσμα. Αν υπάρχουν αποτελέσματα από παλιότερη έκδοση που δεν ξεχώριζε τα backends, καθάρισε το τοπικό cache πριν από τη σύγκριση.

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
Turn Study Copilot into an MCP server too. Create mcp_server.py with the official Python MCP SDK (requirement mcp>=1.20,<2; import FastMCP from mcp.server.fastmcp), stdio transport, and three tools that reuse llm_client.py: summarize_lecture(pdf_path, private), make_flashcards(pdf_path, count, private), make_quiz(pdf_path, questions, private). Add mcp>=1.20,<2 to requirements.txt and make sure the project's .venv installs it. Write clear tool descriptions. Load .env from the folder containing mcp_server.py, regardless of the process working directory. Keep stdout free for the MCP protocol (send diagnostics to stderr). Add a test that lists the tools, run the tests with the project's .venv Python, and add a README section with the config.
```

> **Τι σημαίνει «ιδιωτική λειτουργία» μέσω MCP:** το Study Copilot στέλνει το PDF στο τοπικό Gemma αντί στο Gemini. Όμως το αποτέλεσμα του εργαλείου (π.χ. quiz και απαντήσεις) επιστρέφεται στο Antigravity, και ο agent μπορεί να το στείλει στο cloud μοντέλο του για να συνεχίσει τη συζήτηση. Άρα το PDF δεν στέλνεται από το app στο Gemini, αλλά η χρήση MCP δεν είναι πλήρως offline ή end-to-end ιδιωτική.

### Βήμα 2: Ενημέρωσε και έλεγξε το venv

Το venv δημιουργήθηκε στο Μέρος 2 και χρησιμοποιήθηκε από το app στο Μέρος 3. Δεν το κατεβάζεις, δεν το κάν commit, και δεν χρειάζεται να το ξαναφτιάχνεις αν υπάρχει. Μείνε στο terminal, μέσα στον φάκελο `study-copilot`. Χρησιμοποίησε τις εντολές για το δικό σου λειτουργικό. Έτσι βεβαιώνεσαι ότι οι βιβλιοθήκες εγκαθίστανται **στο ίδιο venv που θα χρησιμοποιήσει ο MCP server**, όχι σε κάποια άλλη Python.

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -c "from mcp.server.fastmcp import FastMCP; print('MCP SDK OK')"
.\.venv\Scripts\python.exe -m pytest
```

**Mac / Linux:**

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -c "from mcp.server.fastmcp import FastMCP; print('MCP SDK OK')"
.venv/bin/python -m pytest
```

Πρέπει να δεις `MCP SDK OK` και τα tests να περάσουν. Αν γράψει ότι δεν υπάρχει το `.venv`, δημιούργησέ το μία φορά από τη ρίζα του project:

**Windows (PowerShell):** `py -3 -m venv .venv`

**Mac / Linux:** `python3 -m venv .venv`

Μετά ξανατρέξε τις εντολές εγκατάστασης και ελέγχου παραπάνω.

### Βήμα 3: Βρες τη ρίζα του project

Έλεγξε ότι το terminal είναι ακόμη μέσα στο `study-copilot`.

**Windows (PowerShell):** γράψε `(Get-Location).Path` και κράτα την τιμή που εμφανίζεται.

**Mac / Linux:** γράψε `pwd` και κράτα την τιμή που εμφανίζεται.

Αυτό είναι το **PROJECT_ROOT**, δηλαδή ο πλήρης φάκελος που περιέχει τα `mcp_server.py`, `requirements.txt` και `sample_lectures/`. Μην προσθέσεις ξανά το `study-copilot` στο τέλος του path.

### Βήμα 4: Δήλωσε τον server στο Antigravity

**Ναι, εδώ χρειάζεται να αλλάξεις τις διαδρομές.** Είναι μία φορά ανά υπολογιστή: το global config είναι δικό σου αρχείο ρυθμίσεων και πρέπει να δείχνει στο δικό σου project και venv. Δεν αλλάζεις το template ή αρχεία του repo· αλλάζεις τα paths στο global MCP config.

Άνοιξε τον raw MCP config editor. Ανάλογα με την έκδοση: **Settings → Customizations → Open MCP Config** ή από το μενού **… → MCP Servers → Manage MCP Servers → View raw config**. Το global αρχείο είναι `~/.gemini/config/mcp_config.json`. Πρόσθεσε το παρακάτω block ή κάνε merge το `study-copilot` μέσα στο υπάρχον `mcpServers` object. **Μην αντικαταστήσεις όλο το αρχείο** αν έχεις ήδη άλλους MCP servers. Αντικατάστησε το παράδειγμα path και στα τρία σημεία (`command`, `args`, `cwd`) με το PROJECT_ROOT που μόλις βρήκες. Το [template](templates/mcp_config.json) είναι για Mac / Linux· εδώ υπάρχουν και οι δύο έτοιμες μορφές.

**Mac / Linux:**

```json
{
  "mcpServers": {
    "study-copilot": {
      "command": "/Users/maria/agy-101/study-copilot/.venv/bin/python",
      "args": ["/Users/maria/agy-101/study-copilot/mcp_server.py"],
      "cwd": "/Users/maria/agy-101/study-copilot"
    }
  }
}
```

**Windows (PowerShell)** — στο JSON κάθε `\` γράφεται ως `\\`:

```json
{
  "mcpServers": {
    "study-copilot": {
      "command": "C:\\Users\\maria\\agy-101\\study-copilot\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\maria\\agy-101\\study-copilot\\mcp_server.py"],
      "cwd": "C:\\Users\\maria\\agy-101\\study-copilot"
    }
  }
}
```

Παράδειγμα: αν το PROJECT_ROOT σου είναι `C:\Users\alex\study-copilot`, τότε το `command` γίνεται `C:\\Users\\alex\\study-copilot\\.venv\\Scripts\\python.exe`. Μην αφήσεις τα παραδείγματα `maria` ή `Users` στο config σου· βάλε τη δική σου διαδρομή.

### Βήμα 5: Δοκίμασέ το από νέα συζήτηση, ΧΩΡΙΣ project

Αποθήκευσε το config και, αν υπάρχει κουμπί ανανέωσης MCP servers, πάτησέ το. Μετά ξεκίνα **New Conversation** χωρίς να διαλέξεις project, για να φανεί ότι ο agent χρησιμοποιεί το **εργαλείο** και όχι τον κώδικα.

Πρώτα έλεγχος:

```
Which tools does study-copilot expose?
```

Μετά:

```
Use study-copilot to quiz me with 3 questions on <PROJECT_ROOT>/sample_lectures/lecture5.pdf, one at a time, in private mode, and grade my answers.
```

Αντικατάστησε το `<PROJECT_ROOT>` με την πραγματική διαδρομή σου. Στα Windows, χρησιμοποίησε την κανονική διαδρομή με μονά backslash, π.χ. `C:\Users\alex\study-copilot\sample_lectures\lecture5.pdf`.

**Τι ελέγχεις:** εμφανίζεται κλήση στο `make_quiz` του `study-copilot` και το quiz γίνεται ερώτηση-ερώτηση.

---

## Checkpoint

- [ ] Quiz με κλειστό Wi-Fi σε ιδιωτική λειτουργία.
- [ ] Κλήση στο `make_quiz` από νέα συζήτηση χωρίς project.
- [ ] Commit.

Έμεινες πίσω; ακολούθησε την ασφαλή διαδικασία checkpoint στο [`08-otan-kolliseis.md`](08-otan-kolliseis.md).

## Boss levels

Δες το [`07-boss-levels.md`](07-boss-levels.md#μέρος-5).
