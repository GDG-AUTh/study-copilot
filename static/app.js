// Study Copilot frontend: plain JavaScript, no libraries.

const form = document.getElementById("upload-form");
const statusEl = document.getElementById("status");
const results = document.getElementById("results");
const tabsEl = document.getElementById("tabs");
const panelsEl = document.getElementById("panels");
const submitBtn = document.getElementById("submit");
const titleEl = document.getElementById("lecture-title");

// One entry per tab. To add a study mode, add a renderer here.
const TABS = [
  { key: "summary", label: "Περίληψη", render: renderSummary },
  { key: "flashcards", label: "Flashcards", render: renderFlashcards },
  { key: "quiz", label: "Quiz", render: renderQuiz },
  { key: "definitions", label: "Ορισμοί", render: renderDefinitions },
];

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  }
  for (const child of children) node.append(child);
  return node;
}

function page(n) {
  return el("span", { class: "page" }, ` (σελ. ${n})`);
}

function setStatus(text, isError = false) {
  statusEl.textContent = text;
  statusEl.classList.toggle("error", isError);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = document.getElementById("pdf").files[0];
  if (!file) return setStatus("Διάλεξε ένα αρχείο PDF.", true);

  submitBtn.disabled = true;
  results.hidden = true;
  setStatus(document.getElementById("private").checked
    ? "Το Gemma διαβάζει τη διάλεξη στο laptop σου… (μπορεί να πάρει 1–2 λεπτά)"
    : "Το Gemini διαβάζει τις διαφάνειες σελίδα-σελίδα και μετά γράφει το υλικό… (συνήθως 20–60 δευτερόλεπτα)");

  try {
    const body = new FormData(form);
    const response = await fetch("/api/study", { method: "POST", body });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Κάτι πήγε στραβά.");
    show(data);
    const counts = `${data.flashcards.length} flashcards, ${data.quiz.length} ερωτήσεις, ${data.definitions.length} ορισμοί`;
    setStatus(`Έτοιμο! ${counts}. Μοντέλο: ${data.backend}${data.cached ? " (από την cache)" : ""}.`);
  } catch (err) {
    setStatus(err.message, true);
  } finally {
    submitBtn.disabled = false;
  }
});

let currentTitle = "";

function show(data) {
  currentTitle = data.title || "";
  titleEl.textContent = data.title ? `${data.title}${data.pages ? ` · ${data.pages} σελίδες` : ""}` : "";
  tabsEl.replaceChildren();
  panelsEl.replaceChildren();
  TABS.filter((t) => data[t.key]).forEach((tab, i) => {
    const button = el("button", {
      role: "tab", id: `tab-${tab.key}`, "aria-controls": `panel-${tab.key}`,
      "aria-selected": i === 0 ? "true" : "false", tabindex: i === 0 ? "0" : "-1",
      onclick: () => select(tab.key),
    }, tab.label);
    const panel = el("div", {
      role: "tabpanel", id: `panel-${tab.key}`, "aria-labelledby": `tab-${tab.key}`, class: "panel",
    }, tab.render(data[tab.key]));
    panel.hidden = i !== 0;
    tabsEl.append(button);
    panelsEl.append(panel);
  });
  results.hidden = false;
}

function select(key, freshContent) {
  if (freshContent) document.getElementById(`panel-${key}`).replaceChildren(freshContent);
  for (const tab of tabsEl.children) {
    const on = tab.id === `tab-${key}`;
    tab.setAttribute("aria-selected", on ? "true" : "false");
    tab.tabIndex = on ? 0 : -1;
  }
  for (const panel of panelsEl.children) panel.hidden = panel.id !== `panel-${key}`;
}

// Arrow keys move between tabs (accessibility).
tabsEl.addEventListener("keydown", (e) => {
  const tabs = [...tabsEl.children];
  const i = tabs.indexOf(document.activeElement);
  if (i < 0 || !["ArrowLeft", "ArrowRight"].includes(e.key)) return;
  const next = tabs[(i + (e.key === "ArrowRight" ? 1 : tabs.length - 1)) % tabs.length];
  next.focus();
  next.click();
});

function renderSummary(items) {
  return el("ul", { class: "summary" }, ...items.map((b) => el("li", {}, b.text, page(b.page))));
}

const KIND_LABELS = {
  definition: "Ορισμός", concept: "Έννοια", process: "Διαδικασία",
  comparison: "Σύγκριση", application: "Εφαρμογή", code: "Κώδικας",
};
const DIFFICULTY_LABELS = { easy: "Εύκολη", medium: "Μέτρια", hard: "Δύσκολη" };

// Flashcards: study one card at a time. "Ξανά" puts the card back later in the deck,
// "Το ήξερα" removes it, until the deck is empty (simple spaced repetition).
function renderFlashcards(cards) {
  let queue = [];
  let known = 0;
  let firstTry = new Set();
  let missed = new Set();
  let flipped = false;

  const counter = el("span", { class: "counter" });
  const bar = el("div", { class: "progress" }, el("div"));
  const kind = el("span", { class: "badge" });
  const text = el("p", { class: "study-text" });
  const meta = el("span", { class: "hint" });
  const card = el("button", { class: "study-card", "aria-live": "polite", onclick: flip }, kind, text, meta);
  const again = el("button", { class: "again", onclick: () => answer(false) }, "✗ Ξανά (1)");
  const good = el("button", { class: "good", onclick: () => answer(true) }, "✓ Το ήξερα (2)");
  const grade = el("div", { class: "grade" }, again, good);
  const done = el("div", { class: "done" });
  const study = el("div", { class: "study" }, card, grade, done);

  function start(deck) {
    queue = deck.slice();
    known = 0;
    firstTry = new Set(deck);
    missed = new Set();
    showCard();
  }

  function showCard() {
    const total = known + new Set(queue).size;
    counter.textContent = `Ξέρεις ${known} / ${total}`;
    bar.firstChild.style.width = `${total ? (100 * known) / total : 100}%`;
    const finished = queue.length === 0;
    card.hidden = grade.hidden = finished;
    done.hidden = !finished;
    if (finished) return showDone();
    const c = queue[0];
    flipped = false;
    card.setAttribute("aria-pressed", "false");
    kind.textContent = KIND_LABELS[c.kind] || "Κάρτα";
    text.textContent = c.front;
    meta.textContent = "Πάτα την κάρτα ή Space για την απάντηση";
    grade.classList.add("invisible");
  }

  function flip() {
    if (!queue.length) return;
    const c = queue[0];
    flipped = !flipped;
    card.setAttribute("aria-pressed", flipped ? "true" : "false");
    text.textContent = flipped ? c.back : c.front;
    meta.textContent = flipped ? `Σελίδα ${c.page} · πάτα για την ερώτηση` : "Πάτα την κάρτα ή Space για την απάντηση";
    grade.classList.toggle("invisible", !flipped);
    if (flipped) good.focus();
  }

  function answer(knewIt) {
    if (!flipped) return;
    const c = queue.shift();
    if (knewIt) {
      known++;
    } else {
      firstTry.delete(c);
      missed.add(c);
      queue.splice(Math.min(3, queue.length), 0, c); // see it again in a few cards
    }
    showCard();
    card.focus();
  }

  function showDone() {
    const retry = cards.filter((c) => missed.has(c));
    done.replaceChildren(
      el("p", { class: "score" }, `Τέλος! Ήξερες ${firstTry.size} από ${cards.length} με την πρώτη.`),
      ...(retry.length ? [el("button", { onclick: () => start(shuffle(retry)) }, `Μόνο όσες δεν ήξερα (${retry.length})`)] : []),
      el("button", { onclick: () => start(shuffle(cards)) }, "Από την αρχή"),
    );
  }

  // Keyboard: Space/Enter flips, 1 = again, 2 = knew it (only while this tab is visible).
  document.addEventListener("keydown", (e) => {
    if (study.offsetParent === null || e.target.closest?.("input, textarea, [role=tab]")) return;
    if (e.key === "1") answer(false);
    else if (e.key === "2") answer(true);
    else if ((e.key === " " || e.key === "Enter") && e.target === document.body) { e.preventDefault(); flip(); }
  });

  const list = el("ol", { class: "card-list" }, ...cards.map((c) =>
    el("li", {}, el("strong", {}, c.front), el("br"), c.back, page(c.page))));
  const listBox = el("details", {}, el("summary", {}, `Όλες οι κάρτες (${cards.length})`), list);

  const toolbar = el("div", { class: "toolbar" }, counter,
    el("button", { onclick: () => start(shuffle(cards)) }, "Ανακάτεμα"),
    el("button", { onclick: () => downloadAnki(cards) }, "Εξαγωγή για Anki"));

  start(cards);
  return el("div", {}, toolbar, bar, study, listBox);
}

function shuffle(items) {
  const a = items.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

// Anki imports a text file with one "front<TAB>back<TAB>tags" line per card.
function downloadAnki(cards) {
  const clean = (s) => String(s).replace(/[\t\r\n]+/g, " ");
  const tag = (currentTitle || "study-copilot").replace(/\s+/g, "_");
  const lines = ["#separator:tab", "#html:false", "#tags column:3",
    ...cards.map((c) => [clean(c.front), clean(`${c.back} (σελ. ${c.page})`), `${tag} ${c.kind || ""}`.trim()].join("\t"))];
  const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" });
  const link = el("a", { href: URL.createObjectURL(blob), download: `${tag}-flashcards.txt` });
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(link.href);
}

// Quiz: instant feedback on every answer, score at the end.
function renderQuiz(questions) {
  const container = el("div");
  const score = el("p", { class: "score", "aria-live": "polite" });
  let answered = 0;
  let correct = 0;
  questions.forEach((q, qi) => {
    const fb = el("div", { class: "feedback", "aria-live": "polite" });
    const badges = el("div", { class: "badges" },
      el("span", { class: `badge ${q.difficulty || ""}` }, DIFFICULTY_LABELS[q.difficulty] || "Ερώτηση"),
      el("span", { class: "page" }, `σελ. ${q.page}`));
    const fieldset = el("fieldset", {}, el("legend", {}, `${qi + 1}. ${q.question}`));
    const labels = q.options.map((opt, oi) => {
      const input = el("input", { type: "radio", name: `q${qi}`, value: String(oi) });
      const label = el("label", {}, input, ` ${"ΑΒΓΔ"[oi]}. ${opt}`);
      input.addEventListener("change", () => {
        const ok = oi === q.answer_index;
        answered++;
        if (ok) correct++;
        fieldset.disabled = true;
        labels[q.answer_index].classList.add("right");
        if (!ok) label.classList.add("wrong");
        fb.className = `feedback ${ok ? "ok" : "bad"}`;
        const check = q.verified === false ? " ⚠ Το παράθεμα δεν βρέθηκε αυτούσιο στο PDF: έλεγξέ το." : "";
        fb.replaceChildren(
          el("strong", {}, ok ? "✓ Σωστό. " : `✗ Σωστή απάντηση: ${"ΑΒΓΔ"[q.answer_index]}. `), q.explanation,
          el("blockquote", {}, `«${q.source_quote}» (σελ. ${q.page})${check}`));
        score.textContent = answered === questions.length
          ? `Σκορ: ${correct} / ${questions.length}`
          : `Σωστές μέχρι τώρα: ${correct} / ${answered}`;
      });
      return label;
    });
    fieldset.append(...labels);
    container.append(el("div", { class: "question" }, badges, fieldset, fb));
  });
  const reset = el("button", { onclick: () => select("quiz", renderQuiz(questions)) }, "Ξανά από την αρχή");
  container.append(score, reset);
  return container;
}

function renderDefinitions(items) {
  return el("dl", { class: "definitions" }, ...items.flatMap((d) => [
    el("dt", {}, d.term, page(d.page)),
    el("dd", {}, d.definition),
  ]));
}
