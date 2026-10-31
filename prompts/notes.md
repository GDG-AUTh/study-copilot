You are reading the slides of one university lecture, so that a second step can write study material from your notes.

The PDF has {{n_pages}} pages. Go through EVERY page, in order, and write one entry per page.

For each page:
- `page`: the page number in the PDF, counting from 1. Use the "--- Σελίδα N ---" markers of the extracted text when they are given; never use a slide number printed on the slide if it differs.
- `title`: the title of the slide (or a short title if it has none).
- `content`: faithful, complete notes of everything the page teaches, in the language of the lecture. Include every definition, rule, property, step of an algorithm, complexity, formula, number and example. Describe what diagrams, tables, figures and code on the slide show (e.g. "the code implements BFS with a deque; dist[v] = dist[u] + 1"). Keep formulas and code identifiers exactly as written. Do not add anything that is not on the page.
- `key_terms`: the technical terms that appear on the page.

Skip only empty pages and repeated footers (course name, licence, "Σελίδα x / y").
`title` at the top level: the title of the lecture.
Answer only with JSON that matches the given schema.
