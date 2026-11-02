// Study Copilot frontend: plain JavaScript, no libraries.

const $ = (id) => document.getElementById(id);
const screens = { start: $("start"), working: $("working"), results: $("results") };
const form = $("upload-form");
const fileInput = $("pdf");
const tabsEl = $("tabs");
const panelsEl = $("panels");

const MAX_MB = 20;
const RECENT_KEY = "study-copilot-recent";
const THEME_KEY = "study-copilot-theme";

// One entry per tab. To add a study mode, add a renderer here.
const TABS = [
  { key: "flashcards", label: "Flashcards", stat: "flashcards", render: renderFlashcards },
  { key: "quiz", label: "Quiz", stat: "ερωτήσεις", render: renderQuiz },
  { key: "summary", label: "Περίληψη", stat: "βασικές ιδέες", render: renderSummary },
  { key: "definitions", label: "Ορισμοί", stat: "ορισμοί", render: renderDefinitions },
];

const KIND_LABELS = {
  definition: "Ορισμός", concept: "Έννοια", process: "Διαδικασία",
  comparison: "Σύγκριση", application: "Εφαρμογή", code: "Κώδικας",
};
const DIFFICULTY_LABELS = { easy: "Εύκολη", medium: "Μέτρια", hard: "Δύσκολη" };
const LETTERS = "ΑΒΓΔ";

let currentTitle = "";
let pdfUrl = null; // lets page numbers open the uploaded PDF at that page
let deckKeys = null; // keyboard handler of the current flashcard deck
let status = null;

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

function show(name) {
  for (const [key, screen] of Object.entries(screens)) screen.hidden = key !== name;
  window.scrollTo(0, 0);
}

function store(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch { /* private window or full storage: the app works without it */ }
}

function load(key) {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

// Theme

function applyTheme(theme) {
  if (theme) document.documentElement.dataset.theme = theme;
}
applyTheme(load(THEME_KEY));
$("theme").addEventListener("click", () => {
  const dark = document.documentElement.dataset.theme
    ? document.documentElement.dataset.theme === "dark"
    : matchMedia("(prefers-color-scheme: dark)").matches;
  const next = dark ? "light" : "dark";
  applyTheme(next);
  store(THEME_KEY, next);
});

// Engine status

async function refreshStatus() {
  try {
    status = await (await fetch("/api/status")).json();
  } catch {
    return;
  }
  renderChip();
  renderEngineHint();
}

function renderChip() {
  const chip = $("engine-chip");
  const { gemini, local } = status;
  const geminiOk = gemini.has_key && !gemini.down;
  const localOk = local.state === "ready";
  chip.hidden = false;
  chip.className = `chip ${geminiOk ? "ok" : localOk ? "warn" : "bad"}`;
  // We only learn whether Gemini has credits by using it, so this never promises it works.
  chip.textContent = geminiOk && localOk ? "Gemini και τοπικό μοντέλο"
    : geminiOk ? "Gemini" : localOk ? `Τοπικά · ${local.model}` : "Χρειάζεται ρύθμιση";
}

function renderEngineHint() {
  if (!status) return;
  const hint = $("engine-hint");
  const engine = form.elements.engine.value;
  const { gemini, local } = status;
  const code = (text) => el("code", {}, text);
  hint.replaceChildren();
  const localProblem = () => {
    if (local.state === "not_installed") hint.append("Το τοπικό μοντέλο δεν έχει εγκατασταθεί. Τρέξε ", code(`ollama pull ${local.model}`));
    else if (local.state === "not_running") hint.append("Δεν τρέχει το Ollama. Άνοιξε την εφαρμογή Ollama ή τρέξε ", code("ollama serve"));
  };
  if (engine === "local") {
    if (local.state === "ready") hint.append(`Θα δουλέψει το ${local.model} στον υπολογιστή σου. Διαβάζει μόνο το κείμενο του PDF.`);
    else localProblem();
  } else if (engine === "cloud") {
    if (!gemini.has_key) hint.append("Το Gemini δεν έχει ρυθμιστεί στο .env.");
    else if (gemini.problem) hint.append(gemini.problem);
    else hint.append("Το PDF στέλνεται στο Gemini, που διαβάζει και τα διαγράμματα.");
  } else if (gemini.has_key && !gemini.down) {
    hint.append("Ξεκινά με το Gemini. Αν δεν απαντήσει, συνεχίζει μόνο του με το τοπικό μοντέλο.");
  } else if (local.state === "ready") {
    hint.append(`Το Gemini δεν είναι διαθέσιμο τώρα, οπότε θα δουλέψει το ${local.model} στον υπολογιστή σου.`);
  } else {
    localProblem();
  }
}
form.addEventListener("change", (e) => {
  if (e.target.name === "engine") renderEngineHint();
});

// Choosing a file

fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) generate(fileInput.files[0]);
});

const drop = $("drop");
["dragenter", "dragover"].forEach((type) => drop.addEventListener(type, (e) => {
  e.preventDefault();
  drop.classList.add("over");
}));
["dragleave", "drop"].forEach((type) => drop.addEventListener(type, (e) => {
  e.preventDefault();
  drop.classList.remove("over");
}));
drop.addEventListener("drop", (e) => {
  if (e.dataTransfer.files[0]) generate(e.dataTransfer.files[0]);
});

function showError(message) {
  $("error").textContent = message;
  $("error").hidden = !message;
}

// Generating

async function generate(file) {
  showError("");
  if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
    return showError("Το αρχείο δεν είναι PDF.");
  }
  if (file.size > MAX_MB * 1024 * 1024) {
    return showError(`Το αρχείο είναι μεγαλύτερο από ${MAX_MB} MB.`);
  }

  const body = new FormData();
  body.append("pdf", file);
  body.append("engine", form.elements.engine.value);

  show("working");
  const stopProgress = startProgress();
  try {
    const response = await fetch("/api/study", { method: "POST", body });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Κάτι πήγε στραβά.");
    if (pdfUrl) URL.revokeObjectURL(pdfUrl);
    pdfUrl = URL.createObjectURL(file);
    saveRecent(data);
    showResults(data);
  } catch (err) {
    show("start");
    showError(err instanceof TypeError ? "Δεν ήταν δυνατή η σύνδεση με την εφαρμογή. Τρέχει ακόμα;" : err.message);
  } finally {
    stopProgress();
    fileInput.value = "";
    refreshStatus();
  }
}

// The screen says which engine is really working, by asking the server.
function startProgress() {
  const started = Date.now();
  const render = (working) => {
    const local = working === "local";
    $("working-title").textContent = local ? "Το τοπικό μοντέλο γράφει το υλικό" : "Το Gemini διαβάζει τις διαφάνειες";
    $("working-text").textContent = local
      ? "Δουλεύει στον υπολογιστή σου, οπότε μπορεί να πάρει μερικά λεπτά. Κράτα αυτή τη σελίδα ανοιχτή."
      : "Πρώτα σημειώσεις για κάθε σελίδα, μετά κάρτες και ερωτήσεις. Συνήθως 1 με 3 λεπτά.";
  };
  render(form.elements.engine.value === "local" ? "local" : "cloud");
  const tick = () => {
    const seconds = Math.floor((Date.now() - started) / 1000);
    $("elapsed").textContent = `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
  };
  tick();
  const clock = setInterval(tick, 1000);
  const poll = setInterval(async () => {
    try {
      const state = await (await fetch("/api/status")).json();
      if (state.working) render(state.working);
    } catch { /* the result or the error will tell */ }
  }, 2000);
  return () => {
    clearInterval(clock);
    clearInterval(poll);
  };
}

// Recent lectures, kept only in this browser

function recentItems() {
  try {
    return JSON.parse(load(RECENT_KEY)) || [];
  } catch {
    return [];
  }
}

function saveRecent(data) {
  const items = recentItems().filter((item) => item.data.title !== data.title);
  items.unshift({ when: Date.now(), data });
  store(RECENT_KEY, JSON.stringify(items.slice(0, 6)));
}

function renderRecent() {
  const items = recentItems();
  $("recent").hidden = !items.length;
  $("recent-list").replaceChildren(...items.map((item) => el("li", {},
    el("button", { type: "button", onclick: () => {
      if (pdfUrl) URL.revokeObjectURL(pdfUrl);
      pdfUrl = null;
      showResults(item.data, true);
    } },
    el("span", {}, item.data.title || "Διάλεξη"),
    el("small", {}, `${item.data.flashcards.length} κάρτες · ${new Date(item.when).toLocaleDateString("el-GR")}`)))));
}

function goHome() {
  deckKeys = null;
  renderRecent();
  show("start");
}
$("home").addEventListener("click", goHome);
$("new-lecture").addEventListener("click", goHome);

// Results

function showResults(data, fromRecent = false) {
  currentTitle = data.title || "";
  $("lecture-title").textContent = data.title || "Η διάλεξή σου";
  const pages = data.pages ? `${data.pages} σελίδες · ` : "";
  const source = fromRecent ? "από τις πρόσφατες" : data.cached ? "από την cache" : "";
  $("status").textContent = `${pages}${data.backend}${source ? ` · ${source}` : ""}`;
  const notice = !fromRecent && data.notice ? `Δούλεψε το τοπικό μοντέλο, γιατί δεν απάντησε το Gemini. ${data.notice}` : "";
  $("notice").textContent = notice;
  $("notice").hidden = !notice;

  const tabs = TABS.filter((t) => data[t.key]?.length);
  $("stats").replaceChildren(...tabs.map((t) => el("div", {}, el("b", {}, String(data[t.key].length)), el("span", {}, t.stat))));
  tabsEl.replaceChildren();
  panelsEl.replaceChildren();
  tabs.forEach((tab, i) => {
    tabsEl.append(el("button", {
      role: "tab", id: `tab-${tab.key}`, "aria-controls": `panel-${tab.key}`,
      "aria-selected": i === 0 ? "true" : "false", tabindex: i === 0 ? "0" : "-1",
      onclick: () => select(tab.key),
    }, tab.label));
    const panel = el("div", {
      role: "tabpanel", id: `panel-${tab.key}`, "aria-labelledby": `tab-${tab.key}`, class: "panel",
    }, tab.render(data[tab.key]));
    panel.hidden = i !== 0;
    panelsEl.append(panel);
  });
  show("results");
}

function select(key, freshContent) {
  if (freshContent) $(`panel-${key}`).replaceChildren(freshContent);
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

// A page number opens the PDF at that page, when we still have the file.
function page(n) {
  const label = `σελ. ${n}`;
  if (!pdfUrl) return el("span", { class: "page" }, label);
  return el("a", {
    class: "page", href: `${pdfUrl}#page=${n}`, target: "_blank", rel: "noopener",
    title: "Άνοιγμα του PDF σε αυτή τη σελίδα", onclick: (e) => e.stopPropagation(),
  }, label);
}

function renderSummary(items) {
  return el("ol", { class: "summary" }, ...items.map((b) => el("li", {}, el("div", {}, b.text, page(b.page)))));
}

// Flashcards: study one card at a time. "Ξανά" puts the card back later in the deck,
// "Το ήξερα" removes it, until the deck is empty (simple spaced repetition).
function renderFlashcards(cards) {
  let queue = [];
  let known = 0;
  let missed = new Set();
  let flipped = false;

  const counter = el("span", { class: "counter", "aria-live": "polite" });
  const bar = el("div", { class: "progress" }, el("div"));
  const kind = el("span", { class: "badge" });
  const frontText = el("p", { class: "study-text" });
  const backText = el("p", { class: "study-text" });
  const backMeta = el("span", { class: "hint" });
  const inner = el("span", { class: "flip-inner" },
    el("span", { class: "face front" }, kind, frontText, el("span", { class: "hint" }, "Πάτα ή Space για την απάντηση")),
    el("span", { class: "face back" }, backText, backMeta));
  const card = el("button", { class: "flip", type: "button", "aria-pressed": "false", "aria-live": "polite", onclick: flip }, inner);
  const again = el("button", { class: "again", type: "button", onclick: () => answer(false) }, "✗ Ξανά", el("kbd", {}, "1"));
  const good = el("button", { class: "good", type: "button", onclick: () => answer(true) }, "✓ Το ήξερα", el("kbd", {}, "2"));
  const grade = el("div", { class: "grade" }, again, good);
  const done = el("div", { class: "done" });
  const study = el("div", { class: "study" }, card, grade, done);

  function start(deck) {
    queue = deck.slice();
    known = 0;
    missed = new Set();
    showCard();
  }

  function setFlipped(value) {
    flipped = value;
    card.setAttribute("aria-pressed", value ? "true" : "false");
    grade.classList.toggle("invisible", !value);
  }

  function showCard() {
    const total = known + queue.length;
    counter.textContent = `Ξέρεις ${known} από ${total}`;
    bar.firstChild.style.width = `${total ? (100 * known) / total : 100}%`;
    const finished = queue.length === 0;
    card.hidden = grade.hidden = finished;
    done.hidden = !finished;
    if (finished) return showDone();
    const c = queue[0];
    // Turn back without animation, so the next answer is never seen in passing.
    inner.classList.add("instant");
    setFlipped(false);
    kind.textContent = KIND_LABELS[c.kind] || "Κάρτα";
    frontText.textContent = c.front;
    backText.textContent = c.back;
    backMeta.replaceChildren(page(c.page));
    void inner.offsetWidth;
    inner.classList.remove("instant");
  }

  function flip() {
    if (queue.length) setFlipped(!flipped);
  }

  function answer(knewIt) {
    if (!flipped) return;
    const c = queue.shift();
    if (knewIt) {
      known++;
    } else {
      missed.add(c);
      queue.splice(Math.min(3, queue.length), 0, c); // see it again in a few cards
    }
    showCard();
    card.focus();
  }

  function showDone() {
    const retry = cards.filter((c) => missed.has(c));
    done.replaceChildren(
      el("p", { class: "score" }, `Τέλος! Ήξερες ${cards.length - retry.length} από τις ${cards.length} με την πρώτη.`),
      ...(retry.length ? [el("button", { type: "button", onclick: () => start(shuffle(retry)) }, `Μόνο όσες δεν ήξερα (${retry.length})`)] : []),
      el("button", { type: "button", onclick: () => start(shuffle(cards)) }, "Από την αρχή"),
    );
  }

  // Keyboard: Space flips, 1 = again, 2 = knew it (only while this tab is visible).
  deckKeys = (e) => {
    if (study.offsetParent === null || e.target.closest?.("input, textarea, a, [role=tab]")) return;
    if (e.key === "1") answer(false);
    else if (e.key === "2") answer(true);
    else if (e.key === " " && e.target !== card) {
      e.preventDefault();
      flip();
    }
  };

  const list = el("ol", { class: "card-list" }, ...cards.map((c) =>
    el("li", {}, el("strong", {}, c.front), el("br"), c.back, page(c.page))));
  const listBox = el("details", {}, el("summary", {}, `Όλες οι κάρτες (${cards.length})`), list);

  const toolbar = el("div", { class: "toolbar" }, counter,
    el("button", { type: "button", onclick: () => start(shuffle(cards)) }, "Ανακάτεμα"),
    el("button", { type: "button", onclick: () => downloadAnki(cards) }, "Εξαγωγή για Anki"));

  start(cards);
  return el("div", {}, toolbar, bar, study, listBox);
}

document.addEventListener("keydown", (e) => deckKeys?.(e));

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
  const scoreBox = el("div", { class: "score-box", "aria-live": "polite" });
  let answered = 0;
  let correct = 0;
  const missedPages = new Set();

  function renderScore() {
    const percent = Math.round((100 * correct) / questions.length);
    const finished = answered === questions.length;
    const pages = [...missedPages].sort((a, b) => a - b).join(", ");
    scoreBox.replaceChildren(
      el("div", { class: "ring", style: `--p:${percent}` }, el("span", {}, `${percent}%`)),
      el("div", {},
        el("p", { class: "score" }, `${correct} σωστές από ${questions.length}`),
        el("p", { class: "hint" }, !finished ? `Απομένουν ${questions.length - answered}.`
          : pages ? `Ξαναδές τις σελίδες ${pages}.` : "Τα έπιασες όλα!")));
  }

  questions.forEach((q, qi) => {
    const fb = el("div", { class: "feedback" });
    const badges = el("div", { class: "badges" },
      el("span", { class: `badge ${q.difficulty || ""}` }, DIFFICULTY_LABELS[q.difficulty] || "Ερώτηση"));
    const fieldset = el("fieldset", {}, el("legend", {}, `${qi + 1}. ${q.question}`));
    const labels = q.options.map((opt, oi) => {
      const input = el("input", { type: "radio", name: `q${qi}`, value: String(oi) });
      const label = el("label", {}, input, el("span", {}, `${LETTERS[oi]}. ${opt}`));
      input.addEventListener("change", () => {
        const ok = oi === q.answer_index;
        answered++;
        if (ok) correct++;
        else missedPages.add(q.page);
        fieldset.disabled = true;
        labels[q.answer_index].classList.add("right");
        if (!ok) label.classList.add("wrong");
        fb.className = `feedback ${ok ? "ok" : "bad"}`;
        const check = q.verified === false ? " ⚠ Το παράθεμα δεν βρέθηκε αυτούσιο στο PDF: έλεγξέ το." : "";
        fb.replaceChildren(
          el("strong", {}, ok ? "✓ Σωστό. " : `✗ Σωστή απάντηση: ${LETTERS[q.answer_index]}. `), q.explanation,
          el("blockquote", {}, `«${q.source_quote}»`, page(q.page), check));
        renderScore();
      });
      return label;
    });
    fieldset.append(...labels);
    container.append(el("div", { class: "question" }, badges, fieldset, fb));
  });
  renderScore();
  const reset = el("button", { type: "button", onclick: () => select("quiz", renderQuiz(questions)) }, "Ξανά από την αρχή");
  container.append(scoreBox, reset);
  return container;
}

function renderDefinitions(items) {
  const rows = items.map((d) => ({
    text: `${d.term} ${d.definition}`.toLowerCase(),
    node: el("div", {}, el("dt", {}, d.term, page(d.page)), el("dd", {}, d.definition)),
  }));
  const search = el("input", {
    class: "search", type: "search", placeholder: "Αναζήτηση όρου…", "aria-label": "Αναζήτηση όρου",
    oninput: () => {
      const query = search.value.trim().toLowerCase();
      for (const row of rows) row.node.hidden = !row.text.includes(query);
    },
  });
  return el("div", {}, search, el("dl", { class: "definitions" }, ...rows.map((r) => r.node)));
}

renderRecent();
refreshStatus();
