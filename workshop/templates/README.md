# Templates

Αρχεία που χρειάζονται τα μέρη 4 και 5. Στο Μέρος 4 τα αντιγράφεις στη θέση τους (δες το `04-kanones-kritis.md`).

| Αρχείο εδώ | Πού το βάζεις στο project σου | Μέρος |
|---|---|---|
| `AGENTS.md` | `AGENTS.md` (στη ρίζα) | 4 |
| `add-study-mode/SKILL.md` | `.agents/skills/add-study-mode/SKILL.md` | 4 |
| `grounding-critic.md` | `.agents/agents/grounding-critic.md` | 4 |
| `rules/prompts.md` | `.agents/rules/prompts.md` | 4 (Boss level) |
| `mcp_config.json` | Settings → Customizations → Open MCP Config (`~/.gemini/config/mcp_config.json`) | 5 |

Στο `mcp_config.json` αντικατάστησε το `/ABSOLUTE/PATH` με το αποτέλεσμα του `pwd` μέσα στον φάκελο του project. Στα Windows: `C:\\Users\\...\\.venv\\Scripts\\python.exe` (διπλά backslashes).

Στον `grounding-critic.md`: αν το μοντέλο `pro` δεν είναι διαθέσιμο στο πλάνο σου, σβήσε τη γραμμή `model: pro`.
