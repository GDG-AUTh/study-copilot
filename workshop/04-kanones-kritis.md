# Μέρος 4 — Μάθε στον agent, έλεγξε το AI

**Διάρκεια:** 25 λεπτά · **Project:** `study-copilot`

Δύο προβλήματα, δύο λύσεις:
- **Ο agent ξεχνάει** όσα του είπες σε προηγούμενες συζητήσεις → **rules** και **skills**.
- **Το AI μπορεί να βγάζει πράγματα από το μυαλό του** → ένας **subagent-κριτής**.

---

## Α. Rules και skills

### Βήμα 1: Βάλε τους κανόνες, το skill και τον κριτή στη θέση τους

Τα αρχεία είναι στο [`templates/`](templates/). Στο terminal, στη ρίζα του project (Mac / Linux):

```bash
mkdir -p .agents/skills/add-study-mode .agents/agents
cp workshop/templates/AGENTS.md AGENTS.md
cp workshop/templates/add-study-mode/SKILL.md .agents/skills/add-study-mode/SKILL.md
cp workshop/templates/grounding-critic.md .agents/agents/grounding-critic.md
```

Σε Windows, ή αν προτιμάς, ζήτα το από τον agent:

```
Copy AGENTS.md, the add-study-mode skill and the grounding-critic subagent from workshop/templates into the places listed in workshop/templates/README.md. Do not change their contents.
```

Τι είναι το καθένα:
- `AGENTS.md`: οι κανόνες, που ο agent διαβάζει σε κάθε μήνυμα.
- `.agents/skills/add-study-mode/SKILL.md`: η συνταγή για νέο study mode.
- `.agents/agents/grounding-critic.md`: ο κριτής (θα τον χρησιμοποιήσεις στο Β).

### Βήμα 2: Μία γραμμή, έξι βήματα

**Πότε:** σε **νέα συζήτηση** στο project (για να φανεί ότι ο agent δεν θυμάται τίποτα από πριν, αλλά διαβάζει τα αρχεία).

```
Add a study mode "Ορισμοί": every key term with a one-line definition and its page.
```

**Τι ελέγχεις:** μέτρα πόσα από τα 6 βήματα του skill έκανε ο agent μόνος του:

- [ ] 1. Prompt σε αρχείο `prompts/definitions.md` (ή παρόμοιο)
- [ ] 2. Επέκταση του JSON schema
- [ ] 3. Ενημέρωση του mock
- [ ] 4. Νέα καρτέλα
- [ ] 5. Test
- [ ] 6. Screenshot

Και αν τήρησε τους κανόνες του `AGENTS.md` (π.χ. UI στα ελληνικά, κλήσεις μόνο από το `llm_client.py`) χωρίς να του τους πεις.

### Βήμα 3: Ποια skills ξέρει;

```
Which skills are installed?
```

**Τι ελέγχεις:** τα απαριθμεί χωρίς να τα έχει ανοίξει ολόκληρα (progressive disclosure).

### Βήμα 4: Αν έκανε λάθος, μάθε του

Αν παρέλειψε βήματα:

```
You skipped steps of the add-study-mode skill. Follow it fully.
```

Και μετά, για να μην το ξανακάνει:

```
/learn
```

---

## Β. Ο κριτής

### Βήμα 1: Ο subagent

Τον έβαλες ήδη στο Α, βήμα 1: `.agents/agents/grounding-critic.md` (δες το [`templates/grounding-critic.md`](templates/grounding-critic.md)). Αν το μοντέλο `pro` δεν είναι διαθέσιμο στο πλάνο σου, σβήσε τη γραμμή `model: pro`.

### Βήμα 2: Παράγε

```
Generate a quiz for sample_lectures/lecture3.pdf using the app's quiz function and save the result to out/quiz_lecture3.json.
```

### Βήμα 3: Έλεγξε

```
Ask grounding-critic to check out/quiz_lecture3.json against sample_lectures/lecture3.pdf. For each question give the verdict (supported / partly / unsupported), the page and the supporting quote.
```

**Τι ελέγχεις:** πόσα «unsupported» βρήκε. **Σημείωσέ το.**

### Βήμα 4: Διόρθωσε το prompt του quiz

```
Update prompts/quiz.md so the model asks only about facts stated in the PDF, and includes the source page and a short supporting quote for every question.
```

### Βήμα 5: Ξαναπαράγε και σύγκρινε

```
Regenerate the quiz for lecture3.pdf, run grounding-critic again, and show me a before/after table with the number of supported, partly and unsupported questions.
```

### Βήμα 6 (bonus): Μίλα απευθείας στον κριτή

```
Ask grounding-critic: which question was the worst and why?
```

---

## Checkpoint

- [ ] Καρτέλα «Ορισμοί» στο app, με test που περνά.
- [ ] Λιγότερα «unsupported» μετά τη διόρθωση του prompt.
- [ ] Commit.

Έμεινες πίσω; `git checkout checkpoint-4`

## Boss levels

Δες το [`07-boss-levels.md`](07-boss-levels.md#μέρος-4).
