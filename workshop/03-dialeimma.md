# Διάλειμμα — οι agents δουλεύουν για σένα

**Διάρκεια:** 10 λεπτά · **Project:** `study-copilot`

**Στείλ' το πριν σηκωθείς.** Ο κύριος agent μοιράζει τη δουλειά σε τρεις **subagents** που δουλεύουν παράλληλα, ο καθένας στο δικό του αντίγραφο του repo (worktree). Όταν γυρίσεις, θα βρεις έτοιμα tests, διορθώσεις και README.

```
While I take a break, use subagents in parallel.
One adds tests for bad model output (invalid JSON, missing fields, a quiz with 4 questions) and for scanned PDFs, and makes the app handle them.
One audits accessibility of the flashcards and quiz and fixes it.
One writes a README in Greek with screenshots and how to get a free Gemini API key.
Report back with a summary of each.
```

## Τι κάνει ο καθένας

| Subagent | Τι φτιάχνει | Γιατί μετράει |
|---|---|---|
| 1 | Tests για «κακή» απάντηση του μοντέλου και σκαναρισμένα PDF | Τα LLMs μερικές φορές επιστρέφουν χαλασμένο JSON· ένα σοβαρό app πρέπει να το αντέχει |
| 2 | Accessibility: labels, πλοήγηση με πληκτρολόγιο, αντίθεση χρωμάτων | Το app να το χρησιμοποιεί και κάποιος με screen reader |
| 3 | README στα ελληνικά | Θα το χρειαστείς στο Μέρος 6, για το CV |

## Όταν γυρίσεις

- [ ] Δες τις κάρτες των τριών subagents: έχουν ολοκληρωθεί;
- [ ] Τρέξε `pytest`: περνάνε όλα;
- [ ] Κάνε commit.

## Αν έχεις πρόβλημα με το όριο του Gemini (σφάλμα 429)

Στείλε μόνο το κομμάτι του README:

```
Write a README in Greek with screenshots and how to get a free Gemini API key.
```

## Το Gemma κατέβηκε;

Έλεγξε με `ollama list` αν φαίνεται το `gemma3:1b`. Αν όχι, τρέξε ξανά `ollama pull gemma3:1b`: συνεχίζει από εκεί που σταμάτησε. Θα το χρειαστείς στο Μέρος 5.
