// Study Copilot frontend: plain JavaScript, no libraries.

const form = document.getElementById("upload-form");
const statusEl = document.getElementById("status");
const results = document.getElementById("results");
const tabsEl = document.getElementById("tabs");
const panelsEl = document.getElementById("panels");
const submitBtn = document.getElementById("submit");

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
    : "Διαβάζω τη διάλεξη… (μπορεί να πάρει λίγα δευτερόλεπτα)");

  try {
    const body = new FormData(form);
    const response = await fetch("/api/study", { method: "POST", body });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Κάτι πήγε στραβά.");
    show(data);
    setStatus(`Έτοιμο! Μοντέλο: ${data.backend}${data.cached ? " (από την cache)" : ""}.`);
  } catch (err) {
    setStatus(err.message, true);
  } finally {
    submitBtn.disabled = false;
  }
});

function show(data) {
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

function select(key) {
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

function renderFlashcards(cards) {
  return el("div", { class: "cards" }, ...cards.map((c) => {
    const text = el("span", {}, c.front);
    const hint = el("span", { class: "hint" }, "Πάτα για την απάντηση");
    const card = el("button", { class: "card", "aria-pressed": "false" }, text, hint);
    card.addEventListener("click", () => {
      const flipped = card.getAttribute("aria-pressed") !== "true";
      card.setAttribute("aria-pressed", flipped ? "true" : "false");
      text.textContent = flipped ? c.back : c.front;
      hint.textContent = flipped ? `Σελίδα ${c.page} · πάτα για την ερώτηση` : "Πάτα για την απάντηση";
    });
    return card;
  }));
}

function renderQuiz(questions) {
  const container = el("div");
  questions.forEach((q, qi) => {
    const options = q.options.map((opt, oi) =>
      el("label", {}, el("input", { type: "radio", name: `q${qi}`, value: String(oi) }), ` ${opt}`));
    container.append(el("div", { class: "question" },
      el("fieldset", {}, el("legend", {}, `${qi + 1}. ${q.question}`), ...options),
      el("div", { class: "feedback", id: `fb${qi}`, "aria-live": "polite" })));
  });
  const score = el("p", { class: "score", "aria-live": "polite" });
  const check = el("button", {
    onclick: () => {
      let correct = 0;
      questions.forEach((q, qi) => {
        const picked = container.querySelector(`input[name="q${qi}"]:checked`);
        const fb = container.querySelector(`#fb${qi}`);
        const ok = picked && Number(picked.value) === q.answer_index;
        if (ok) correct++;
        fb.className = `feedback ${ok ? "ok" : "bad"}`;
        fb.textContent = `${ok ? "✓ Σωστό." : `✗ Σωστή απάντηση: ${q.options[q.answer_index]}.`} ${q.explanation} «${q.source_quote}» (σελ. ${q.page})`;
      });
      score.textContent = `Σκορ: ${correct} / ${questions.length}`;
    },
  }, "Έλεγξε τις απαντήσεις");
  container.append(check, score);
  return container;
}

function renderDefinitions(items) {
  return el("dl", { class: "definitions" }, ...items.flatMap((d) => [
    el("dt", {}, d.term, page(d.page)),
    el("dd", {}, d.definition),
  ]));
}
