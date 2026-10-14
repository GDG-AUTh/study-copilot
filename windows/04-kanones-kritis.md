[Ευρετήριο](README.md) · Οδηγός για Windows · Σελίδα 5 από 8

# Μέρος 4: Μάθε στον agent, έλεγξε το AI (Windows)

**Χρόνος:** περίπου 30 λεπτά · **Project:** `study-copilot`

Δύο προβλήματα και οι λύσεις τους:

- **Ο agent δεν θυμάται** τι του είπες σε παλιότερες συζητήσεις. Λύση: **κανόνες** (rules) και **skills**, δηλαδή αρχεία μέσα στο project που ο agent διαβάζει μόνος του.
- **Το AI μπορεί να γράψει πράγματα που δεν υπάρχουν στο PDF.** Λύση: ένας δεύτερος agent, ο **κριτής** (`grounding-critic`), που ελέγχει κάθε ερώτηση του quiz απέναντι στο PDF.

Σε αυτό το σημείο η εφαρμογή έχει μόνο Gemini. Το Gemma μπαίνει στο Μέρος 5.

---

## Α. Κανόνες και skills

Αν σου μένει λίγος χρόνος, κάνε τα Βήματα 1 και 2. Τα 3 και 4 είναι επιπλέον.

### Βήμα 1: Αντίγραψε τα αρχεία στη θέση τους

Τα αρχεία βρίσκονται στο [`../workshop/templates/`](../workshop/templates/). Εντολές στο terminal, μέσα στο `study-copilot`, μία μία:

```powershell
New-Item -ItemType Directory -Force .agents\skills\add-study-mode | Out-Null
New-Item -ItemType Directory -Force .agents\agents | Out-Null
Copy-Item workshop\templates\AGENTS.md AGENTS.md
Copy-Item workshop\templates\add-study-mode\SKILL.md .agents\skills\add-study-mode\SKILL.md
Copy-Item workshop\templates\grounding-critic.md .agents\agents\grounding-critic.md
```

Έλεγχος:

```powershell
dir AGENTS.md, .agents\skills\add-study-mode, .agents\agents
```

**Τι πρέπει να δεις:** τα `AGENTS.md`, `SKILL.md` και `grounding-critic.md`.

Τι είναι το καθένα:

- `AGENTS.md`: οι κανόνες του project. Ο agent τους διαβάζει σε κάθε μήνυμα.
- `.agents/skills/add-study-mode/SKILL.md`: μια «συνταγή» έξι βημάτων για το πώς προστίθεται νέα καρτέλα μελέτης.
- `.agents/agents/grounding-critic.md`: ο κριτής, που θα χρησιμοποιήσεις στο Β.

### Βήμα 2: Μία γραμμή, έξι βήματα

Ξεκίνα **νέα συζήτηση** στο project. Έτσι φαίνεται ότι ο agent δεν θυμάται τίποτα από πριν, αλλά διαβάζει τα αρχεία. Prompt για τον agent:

```
Add a study mode "Ορισμοί": every key term with a one-line definition and its page.
```

**Τι πρέπει να δεις:** μέτρα πόσα από τα 6 βήματα του skill έκανε ο agent χωρίς να του τα πεις:

- [ ] 1. Το prompt σε αρχείο `prompts/definitions.md` (ή παρόμοιο)
- [ ] 2. Επέκταση του JSON schema
- [ ] 3. Ενημέρωση του mock
- [ ] 4. Νέα καρτέλα «Ορισμοί»
- [ ] 5. Test
- [ ] 6. Screenshot

Έλεγξε επίσης αν τήρησε τους κανόνες του `AGENTS.md` χωρίς να του τους πεις, π.χ. κείμενα στα ελληνικά και κλήσεις στο μοντέλο μόνο από το `llm_client.py`.


### Βήμα 3: Ποια skills ξέρει;

Prompt για τον agent:

```
Which skills are installed?
```

**Τι πρέπει να δεις:** ο agent απαριθμεί τα skills με μια σύντομη περιγραφή. Δεν χρειάζεται να ανοίξει ολόκληρα τα αρχεία για να τα βρει.

### Βήμα 4: Αν παρέλειψε βήματα

Prompt για τον agent:

```
You skipped steps of the add-study-mode skill. Follow it fully.
```

Και, αν η έκδοσή σου έχει την εντολή `/learn`, για να μην το ξανακάνει:

```
/learn
```

Αν το `/learn` δεν υπάρχει, παράλειψέ το.

---

## Β. Ο κριτής

### Βήμα 1: Το μοντέλο του κριτή

Ο κριτής ορίζεται στο `.agents/agents/grounding-critic.md`. Αν σε επόμενο βήμα δεις μήνυμα ότι το μοντέλο `pro` δεν είναι διαθέσιμο, άνοιξε αυτό το αρχείο στο Antigravity, σβήσε τη γραμμή `model: pro` και αποθήκευσε.

### Βήμα 2: Φτιάξε ένα quiz

Prompt για τον agent:

```
Generate a quiz for sample_lectures/lecture3.pdf using the app's quiz function and save the result to out/quiz_lecture3.json.
```

### Βήμα 3: Ο κριτής το ελέγχει

Prompt για τον agent:

```
Ask grounding-critic to check out/quiz_lecture3.json against sample_lectures/lecture3.pdf. For each question give the verdict (supported / partly / unsupported), the page and the supporting quote.
```

**Τι πρέπει να δεις:** για κάθε ερώτηση μια ετυμηγορία: `supported` (υπάρχει στο PDF), `partly` (εν μέρει) ή `unsupported` (δεν υπάρχει). **Σημείωσε πόσα `unsupported` βρήκε.**


### Βήμα 4: Διόρθωσε το prompt του quiz

Prompt για τον agent:

```
Update prompts/quiz.md so the model asks only about facts stated in the PDF, and includes the source page and a short supporting quote for every question. Update the quiz JSON schema, mocked response fixture, and relevant tests to include and validate the quote too. Keep the UI and existing quiz behavior working.
```

### Βήμα 5: Ξαναφτιάξε και σύγκρινε

Prompt για τον agent:

```
Regenerate the quiz for lecture3.pdf, run grounding-critic again, and show me a before/after table with the number of supported, partly and unsupported questions.
```

**Τι πρέπει να δεις:** ένα πίνακα πριν/μετά, με λιγότερα `unsupported` μετά τη διόρθωση.Ουσιαστικά το πρόβλημα στην ερώτηση τέσσερα ήταν ότι για πάνω από 0,7 δεν συνεπάγεται αναδιάταξη.

### Βήμα 6 (επιπλέον): Ρώτα τον κριτή

```
Ask grounding-critic: which question was the worst and why?
```

---

## Checkpoint

Τρέξε τα tests. Εντολή στο terminal:

```
.\.venv\Scripts\python.exe -m pytest
```

- [ ] Η καρτέλα «Ορισμοί» υπάρχει στο app και τα tests περνάνε.
- [ ] Λιγότερα `unsupported` μετά τη διόρθωση του prompt.
- [ ] Commit (`Commit all changes with a clear message.`).

Αν έμεινες πίσω, η έτοιμη λύση είναι στο `checkpoint-4`. Δες το [`08-otan-kolliseis.md`](08-otan-kolliseis.md#έμεινα-πίσω).

Περισσότερες ασκήσεις: [`07-boss-levels.md`](07-boss-levels.md#μέρος-4)


---

[← Προηγούμενο: Χτίζουμε και αποδεικνύουμε](02-xtizoume.md) · [Ευρετήριο](README.md) · [Επόμενο: Gemma και MCP →](05-gemma-mcp.md)
