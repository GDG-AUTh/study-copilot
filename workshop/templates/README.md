# Templates

Αρχεία που χρειάζονται τα μέρη 4 και 5. Στο Μέρος 4 τα αντιγράφεις στη θέση τους (δες το `04-kanones-kritis.md`).

| Αρχείο εδώ | Πού το βάζεις στο project σου | Μέρος |
|---|---|---|
| `AGENTS.md` | `AGENTS.md` (στη ρίζα) | 4 |
| `add-study-mode/SKILL.md` | `.agents/skills/add-study-mode/SKILL.md` | 4 |
| `grounding-critic.md` | `.agents/agents/grounding-critic.md` | 4 |
| `rules/prompts.md` | `.agents/rules/prompts.md` | 4 (Boss level) |
| `mcp_config.json` | Settings → Customizations → Open MCP Config | 5 |

Το `mcp_config.json` είναι παράδειγμα για **Mac / Linux**. Είναι φυσιολογικό να χρειάζεται αλλαγή: ο global MCP config είναι στον δικό σου υπολογιστή και πρέπει να δείχνει στα δικά σου αρχεία. Στο Μέρος 5 θα αντικαταστήσεις το `<PROJECT_ROOT>` και στα τρία σημεία με την πλήρη διαδρομή του φακέλου `study-copilot` (εκεί όπου βρίσκονται τα `mcp_server.py` και `.venv`). Δεν αλλάζεις αυτό το template μέσα στο repo· κάνεις την αλλαγή στο global MCP config. **Μην** προσθέσεις δεύτερη φορά το `study-copilot`. Στα Windows, χρησιμοποίησε το Windows block του οδηγού και γράψε τα backslashes διπλά.

Το `.venv` είναι τοπικός φάκελος μέσα στο project, δημιουργείται από κάθε συμμετέχοντα και δεν ανεβαίνει στο Git. Το δημιουργείς στο Μέρος 2 και εγκαθιστάς μέσα του τις βιβλιοθήκες του project στο Μέρος 3. Το config δείχνει ρητά στη Python αυτού του venv.

Στον `grounding-critic.md`: αν το μοντέλο `pro` δεν είναι διαθέσιμο στο πλάνο σου, σβήσε τη γραμμή `model: pro`.
