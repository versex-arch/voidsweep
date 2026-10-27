"use strict";

/* ------------------------------------------------------------------ i18n */
const STR = {
  ru: {
    "nav.clean": "Очистка", "nav.markers": "Маркеры", "nav.history": "Журнал",
    "start.title": "Найдём то, что только занимает место",
    "start.lede": "Voidsweep ищет временные файлы, кэш, битые ярлыки и остатки удалённых программ. Ничего не удаляется, пока вы не посмотрите список — у каждого файла написано, почему его можно убрать.",
    "start.deep": "Искать мусор по всем дискам",
    "start.deepHint": "Thumbs.db, .DS_Store, забытые *.tmp и незавершённые загрузки в любых папках. Дольше, но тщательнее.",
    "start.scan": "Начать сканирование", "start.cancel": "Остановить", "start.again": "Сканировать снова",
    "orb.ready": "готов к сканированию", "orb.scanning": "найдено, {n}", "orb.done": "можно освободить",
    "orb.nothing": "мусора не найдено",
    "phase.rules": "Проверяю: {d}", "phase.walk": "{d}", "phase.deep": "Диск {d}",
    "drive.free": "свободно {f} из {t}",
    "results.search": "Поиск по имени или пути", "results.selectRecommended": "Выбрать рекомендованное",
    "results.selectNone": "Снять всё", "results.rescan": "Новое сканирование",
    "results.clean": "Очистить", "results.summary": "{n} объектов в {g} категориях",
    "results.selected": "Выбрано <b>{n}</b> · <b>{s}</b>", "results.nothingSelected": "Ничего не выбрано",
    "results.more": "Показать ещё {n}", "results.empty": "По фильтру ничего не найдено.",
    "results.covered": "входит в выбранную папку выше",
    "risk.all": "Все", "risk.safe": "Безопасно", "risk.review": "Проверить", "risk.caution": "Осторожно",
    "riskLong.safe": "Безопасно — ничего нужного не теряется",
    "riskLong.review": "Проверить — безопасно, но есть побочный эффект",
    "riskLong.caution": "Осторожно — эвристика или заметный эффект, не выбрано по умолчанию",
    "mode.trash": "В корзину", "mode.permanent": "Удалить навсегда",
    "detail.pick": "Выберите файл слева — здесь будет написано, почему его можно удалить.",
    "detail.why": "Почему можно удалить", "detail.size": "Размер", "detail.files": "Файлов",
    "detail.changed": "Изменён", "detail.kind": "Тип", "detail.reveal": "Показать в папке",
    "detail.ignore": "Никогда не трогать", "detail.admin": "Нужны права администратора",
    "detail.ago": "{a} назад",
    "kind.file": "файл", "kind.dir": "папка", "kind.link": "ссылка",
    "dlg.title": "Очистить выбранное?",
    "dlg.trash": "{n} объектов ({s}) будут перемещены в корзину. Их можно восстановить, пока корзина не очищена.",
    "dlg.permanent": "{n} объектов ({s}) будут удалены навсегда. Восстановить их будет нельзя.",
    "dlg.cookies": "Выбраны cookies: вы выйдете из аккаунтов на сайтах. Закройте браузеры перед очисткой.",
    "dlg.caution": "Выбраны объекты с маркером «Осторожно» — убедитесь, что они вам не нужны.",
    "dlg.admin": "Часть объектов требует прав администратора — без них они будут пропущены.",
    "dlg.cancel": "Отмена", "dlg.go.trash": "Переместить в корзину", "dlg.go.permanent": "Удалить навсегда",
    "dlg.cleaning": "Очищаю…", "dlg.done": "Готово", "dlg.freed": "Освобождено {s}.",
    "dlg.skipped": "Пропущено: {n}", "dlg.close": "Закрыть",
    "status.missing": "уже удалён", "status.changed": "изменился после сканирования — не тронут",
    "status.protected": "защищённый путь", "status.permission": "нет прав",
    "status.in_use": "занят программой", "status.error": "ошибка",
    "markers.title": "Маркеры",
    "markers.lede": "Каждый найденный объект получает код. Код говорит, что это за мусор и насколько безопасно его удалять.",
    "history.title": "Журнал очисток", "history.empty": "Очисток ещё не было.",
    "history.row": "{n} объектов · {s}", "history.ignored": "Исключения",
    "history.noIgnored": "Исключений нет. Добавьте путь кнопкой «Никогда не трогать» в результатах.",
    "history.remove": "Убрать", "toast.ignored": "Больше не будет предлагаться",
    "toast.busy": "Подождите, идёт другая операция", "error.scan": "Сканирование прервалось: {e}",
    "demo": "демо-режим: файлы не удаляются",
  },
  en: {
    "nav.clean": "Clean", "nav.markers": "Markers", "nav.history": "History",
    "start.title": "Find what only takes up space",
    "start.lede": "Voidsweep looks for temp files, caches, broken shortcuts and leftovers of removed apps. Nothing is deleted until you review the list — every item says why it can go.",
    "start.deep": "Search all drives for junk",
    "start.deepHint": "Thumbs.db, .DS_Store, stray *.tmp and unfinished downloads in any folder. Slower, but thorough.",
    "start.scan": "Start scan", "start.cancel": "Stop", "start.again": "Scan again",
    "orb.ready": "ready to scan", "orb.scanning": "found, {n} items", "orb.done": "can be freed",
    "orb.nothing": "no junk found",
    "phase.rules": "Checking: {d}", "phase.walk": "{d}", "phase.deep": "Drive {d}",
    "drive.free": "{f} free of {t}",
    "results.search": "Search name or path", "results.selectRecommended": "Select recommended",
    "results.selectNone": "Select none", "results.rescan": "New scan",
    "results.clean": "Clean up", "results.summary": "{n} items in {g} categories",
    "results.selected": "Selected <b>{n}</b> · <b>{s}</b>", "results.nothingSelected": "Nothing selected",
    "results.more": "Show {n} more", "results.empty": "Nothing matches the filter.",
    "results.covered": "included in a selected folder above",
    "risk.all": "All", "risk.safe": "Safe", "risk.review": "Review", "risk.caution": "Caution",
    "riskLong.safe": "Safe — nothing you need is lost",
    "riskLong.review": "Review — safe, with a side effect",
    "riskLong.caution": "Caution — heuristic or visible effect, never preselected",
    "mode.trash": "To Trash", "mode.permanent": "Delete forever",
    "detail.pick": "Pick an item on the left to see why it can be removed.",
    "detail.why": "Why it can go", "detail.size": "Size", "detail.files": "Files",
    "detail.changed": "Modified", "detail.kind": "Type", "detail.reveal": "Show in folder",
    "detail.ignore": "Never touch this", "detail.admin": "Needs administrator rights",
    "detail.ago": "{a} ago",
    "kind.file": "file", "kind.dir": "folder", "kind.link": "link",
    "dlg.title": "Clean up the selection?",
    "dlg.trash": "{n} items ({s}) will be moved to the Trash. You can restore them until the Trash is emptied.",
    "dlg.permanent": "{n} items ({s}) will be deleted forever. They cannot be restored.",
    "dlg.cookies": "Cookies are selected: you will be signed out of websites. Close your browsers first.",
    "dlg.caution": "Items marked “Caution” are selected — make sure you do not need them.",
    "dlg.admin": "Some items need administrator rights and will be skipped without them.",
    "dlg.cancel": "Cancel", "dlg.go.trash": "Move to Trash", "dlg.go.permanent": "Delete forever",
    "dlg.cleaning": "Cleaning…", "dlg.done": "Done", "dlg.freed": "Freed {s}.",
    "dlg.skipped": "Skipped: {n}", "dlg.close": "Close",
    "status.missing": "already gone", "status.changed": "changed after the scan — left alone",
    "status.protected": "protected path", "status.permission": "no permission",
    "status.in_use": "in use by a program", "status.error": "error",
    "markers.title": "Markers",
    "markers.lede": "Every item found gets a code. The code says what kind of junk it is and how safe it is to remove.",
    "history.title": "Cleanup history", "history.empty": "No cleanups yet.",
    "history.row": "{n} items · {s}", "history.ignored": "Exclusions",
    "history.noIgnored": "No exclusions. Add one with “Never touch this” in the results.",
    "history.remove": "Remove", "toast.ignored": "Won't be offered again",
    "toast.busy": "Please wait, another operation is running", "error.scan": "The scan stopped: {e}",
    "demo": "demo mode: nothing is deleted",
  },
};

let lang = "ru";
function t(key, vars = {}) {
  const s = (STR[lang] && STR[lang][key]) || STR.en[key] || key;
  return s.replace(/\{(\w+)\}/g, (_, k) => (k in vars ? vars[k] : ""));
}

/* ---------------------------------------------------------------- helpers */
const $ = (sel) => document.querySelector(sel);
function h(tag, attrs = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "html") el.innerHTML = v; // only ever used with our own escaped strings
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat()) {
    if (kid == null || kid === false) continue;
    el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return el;
}
const SVGNS = "http://www.w3.org/2000/svg";
function s(tag, attrs = {}) {
  const el = document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  return el;
}
function esc(str) {
  return String(str).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function bytes(n) {
  const u = lang === "ru" ? ["Б", "КБ", "МБ", "ГБ", "ТБ"] : ["B", "KB", "MB", "GB", "TB"];
  let i = 0;
  while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
  const v = i === 0 ? n.toFixed(0) : n < 10 ? n.toFixed(1) : n.toFixed(0);
  return `${lang === "ru" ? v.replace(".", ",") : v} ${u[i]}`;
}
function plural(n, one, few, many) {
  const a = Math.abs(n) % 100, b = a % 10;
  if (a > 10 && a < 20) return many;
  if (b > 1 && b < 5) return few;
  if (b === 1) return one;
  return many;
}
function age(ts) {
  const d = Math.max(0, (Date.now() / 1000 - ts) / 86400);
  if (lang === "ru") {
    if (d < 1) return "сегодня";
    if (d < 60) { const n = Math.floor(d); return `${n} ${plural(n, "день", "дня", "дней")}`; }
    if (d < 730) { const n = Math.floor(d / 30); return `${n} ${plural(n, "месяц", "месяца", "месяцев")}`; }
    const n = Math.floor(d / 365); return `${n} ${plural(n, "год", "года", "лет")}`;
  }
  if (d < 1) return "today";
  if (d < 60) { const n = Math.floor(d); return `${n} day${n === 1 ? "" : "s"}`; }
  if (d < 730) { const n = Math.floor(d / 30); return `${n} month${n === 1 ? "" : "s"}`; }
  return `${Math.floor(d / 365)} years`;
}
function num(n) { return n.toLocaleString(lang === "ru" ? "ru-RU" : "en-US"); }
function fill(el, ...kids) {
  el.replaceChildren(...kids.flat().filter((k) => k != null && k !== false && k !== ""));
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/* -------------------------------------------------------------------- api */
const TOKEN = (() => {
  const m = location.hash.match(/t=([\w-]+)/);
  if (m) {
    try { sessionStorage.setItem("vs-token", m[1]); } catch (_) { /* private mode */ }
    history.replaceState(null, "", location.pathname);
    return m[1];
  }
  try { return sessionStorage.getItem("vs-token") || ""; } catch (_) { return ""; }
})();

async function api(path, body) {
  const opts = { headers: { "X-Voidsweep-Token": TOKEN } };
  if (body !== undefined) {
    opts.method = "POST";
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const r = await fetch(path, opts);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) { const e = new Error(data.error || r.statusText); e.status = r.status; throw e; }
  return data;
}

/* ------------------------------------------------------------------ state */
const st = {
  info: null, markers: {}, findings: [], byId: new Map(), selected: new Set(), open: new Set(),
  active: null, risk: "all", query: "", mode: "trash", shown: {}, drives: new Set(),
};
const RISK_COLOR = { safe: "#44d7c8", review: "#b9a2ff", caution: "#e58fb8" };

/* -------------------------------------------------------------------- orb */
function drawOrb(segments = [], scanning = false) {
  const svg = $("#orb");
  fill(svg);
  const defs = s("defs");
  const g = s("radialGradient", { id: "halo", cx: "50%", cy: "50%", r: "50%" });
  g.append(s("stop", { offset: "52%", "stop-color": "#5b34d6", "stop-opacity": "0" }),
           s("stop", { offset: "70%", "stop-color": "#5b34d6", "stop-opacity": ".55" }),
           s("stop", { offset: "100%", "stop-color": "#5b34d6", "stop-opacity": "0" }));
  const sw = s("linearGradient", { id: "sweepg", x1: "0", y1: "0", x2: "1", y2: "0" });
  sw.append(s("stop", { offset: "0%", "stop-color": "#44d7c8", "stop-opacity": "0" }),
            s("stop", { offset: "100%", "stop-color": "#44d7c8", "stop-opacity": "1" }));
  defs.append(g, sw);
  svg.append(defs);
  svg.append(s("circle", { class: "halo", cx: 160, cy: 160, r: 160, fill: "url(#halo)" }));
  const R = 128, C = 2 * Math.PI * R;
  svg.append(s("circle", { cx: 160, cy: 160, r: R, fill: "none", stroke: "#2b2140", "stroke-width": 10 }));
  const total = segments.reduce((a, x) => a + x.size, 0);
  if (total > 0) {
    let off = 0;
    const gap = segments.length > 1 ? 3 : 0;
    for (const seg of segments) {
      const len = Math.max(0, (seg.size / total) * C - gap);
      const c = s("circle", {
        class: "seg", cx: 160, cy: 160, r: R, fill: "none", stroke: RISK_COLOR[seg.risk],
        "stroke-width": 10, "stroke-dasharray": `${len} ${C - len}`, "stroke-dashoffset": -off,
        transform: "rotate(-90 160 160)", "stroke-linecap": "butt",
      });
      svg.append(c);
      off += (seg.size / total) * C;
    }
  }
  svg.append(s("circle", { cx: 160, cy: 160, r: 112, fill: "#050407", stroke: "#b9a2ff", "stroke-opacity": ".18" }));
  if (scanning) {
    const sweep = s("g", { class: "sweep" });
    sweep.append(s("path", { d: "M160 32 A128 128 0 0 1 288 160", fill: "none", stroke: "url(#sweepg)", "stroke-width": 10, "stroke-linecap": "round" }));
    svg.append(sweep);
  }
}

function segmentsOf(findings) {
  const by = {};
  for (const f of findings) {
    if (f.covered_by != null) continue;
    by[f.marker] = (by[f.marker] || 0) + f.size;
  }
  return Object.entries(by).sort((a, b) => b[1] - a[1])
    .map(([code, size]) => ({ code, size, risk: st.markers[code].risk }));
}

function miniRing(findings) {
  const svg = s("svg", { viewBox: "0 0 56 56", "aria-hidden": "true" });
  const R = 23, C = 2 * Math.PI * R, segs = segmentsOf(findings);
  const total = segs.reduce((a, x) => a + x.size, 0);
  svg.append(s("circle", { cx: 28, cy: 28, r: R, fill: "none", stroke: "#2b2140", "stroke-width": 6 }));
  let off = 0;
  for (const seg of segs) {
    const len = Math.max(0, (seg.size / total) * C - (segs.length > 1 ? 1.5 : 0));
    svg.append(s("circle", { cx: 28, cy: 28, r: R, fill: "none", stroke: RISK_COLOR[seg.risk],
      "stroke-width": 6, "stroke-dasharray": `${len} ${C - len}`, "stroke-dashoffset": -off,
      transform: "rotate(-90 28 28)" }));
    off += (seg.size / total) * C;
  }
  return svg;
}

/* ----------------------------------------------------------------- render */
function applyI18n() {
  document.documentElement.lang = lang;
  document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => { el.placeholder = t(el.dataset.i18nPlaceholder); });
  document.querySelectorAll(".lang button").forEach((b) => b.classList.toggle("is-on", b.dataset.lang === lang));
}

function renderDrives() {
  const box = $("#drives");
  fill(box);
  for (const d of st.info.drives) {
    const used = d.total ? (d.total - d.free) / d.total : 0;
    const bar = h("span", { class: "bar" }, h("i"));
    bar.firstChild.style.width = `${Math.round(used * 100)}%`;
    const b = h("button", {
      class: "drive" + (st.drives.has(d.path) ? " is-on" : ""), "aria-pressed": st.drives.has(d.path),
      onclick: () => { st.drives.has(d.path) ? st.drives.delete(d.path) : st.drives.add(d.path); renderDrives(); },
    }, h("b", {}, d.label || d.path), bar, h("small", {}, t("drive.free", { f: bytes(d.free), t: bytes(d.total) })));
    box.append(b);
  }
}

function setOrbIdle() {
  drawOrb([], false);
  $("#orb-value").textContent = "—";
  $("#orb-label").textContent = t("orb.ready");
}

function visibleGroups() {
  const q = st.query.trim().toLowerCase();
  const groups = new Map();
  for (const f of st.findings) {
    if (st.risk !== "all" && f.risk !== st.risk) continue;
    if (q && !f.path.toLowerCase().includes(q)) continue;
    if (!groups.has(f.marker)) groups.set(f.marker, []);
    groups.get(f.marker).push(f);
  }
  const list = [...groups.entries()].map(([code, items]) => ({
    code, items: items.sort((a, b) => b.size - a.size),
    size: items.reduce((a, f) => a + (f.covered_by == null ? f.size : 0), 0),
  }));
  list.sort((a, b) => b.size - a.size);
  return list;
}

function effectiveSelected() {
  let n = 0, size = 0;
  for (const id of st.selected) {
    const f = st.byId.get(id);
    if (!f) continue;
    if (f.covered_by != null && st.selected.has(f.covered_by)) continue;
    n++; size += f.size;
  }
  return { n, size };
}

function renderSummary() {
  const total = st.findings.reduce((a, f) => a + (f.covered_by == null ? f.size : 0), 0);
  const cats = new Set(st.findings.map((f) => f.marker)).size;
  const box = $("#summary");
  fill(box, miniRing(st.findings),
    h("div", {}, h("div", { class: "big" }, bytes(total)),
      h("div", { class: "sub" }, t("results.summary", { n: num(st.findings.length), g: cats }),
        st.info.demo ? h("span", { class: "muted" }, " — " + t("demo")) : null)));
}

function renderSelected() {
  const { n, size } = effectiveSelected();
  $("#selected").innerHTML = n ? t("results.selected", { n: esc(num(n)), s: esc(bytes(size)) }) : esc(t("results.nothingSelected"));
  $("#clean-btn").disabled = n === 0;
}

function groupState(items) {
  const sel = items.filter((f) => st.selected.has(f.id)).length;
  return sel === 0 ? "none" : sel === items.length ? "all" : "some";
}

function renderGroups() {
  const box = $("#groups");
  const scroll = box.scrollTop;
  fill(box);
  const groups = visibleGroups();
  if (!groups.length) { box.append(h("p", { class: "muted more" }, t("results.empty"))); return; }
  const max = Math.max(...groups.map((g) => g.size), 1);
  for (const g of groups) {
    const m = st.markers[g.code];
    const open = st.open.has(g.code);
    const state = groupState(g.items);
    const cb = h("input", { type: "checkbox", class: "box", "aria-label": m.title[lang] });
    cb.checked = state === "all";
    cb.indeterminate = state === "some";
    cb.addEventListener("click", (e) => {
      e.stopPropagation();
      const on = state !== "all";
      g.items.forEach((f) => (on ? st.selected.add(f.id) : st.selected.delete(f.id)));
      renderGroups(); renderSelected();
    });
    const bar = h("span", { class: "g-bar" }, h("i", { class: m.risk }));
    bar.firstChild.style.width = `${Math.max(2, (g.size / max) * 100)}%`;
    const head = h("div", {
      class: "g-head", role: "treeitem", "aria-expanded": open, tabindex: 0,
      onclick: () => { open ? st.open.delete(g.code) : st.open.add(g.code); showMarker(g.code); renderGroups(); },
      onkeydown: (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); head.click(); } },
    }, cb, h("span", { class: "chev" }, "›"), h("span", { class: `code ${m.risk}` }, g.code),
      h("span", { class: "g-title" }, m.title[lang], h("small", {}, num(g.items.length))),
      h("span", { class: "g-size" }, bytes(g.size)), bar);
    const group = h("div", { class: "group" + (open ? " open" : "") }, head);
    if (open) {
      const items = h("div", { class: "items", role: "group" });
      const limit = st.shown[g.code] || 200;
      for (const f of g.items.slice(0, limit)) items.append(itemRow(f));
      if (g.items.length > limit) {
        items.append(h("div", { class: "more" }, h("button", { class: "link", onclick: () => { st.shown[g.code] = limit + 500; renderGroups(); } },
          t("results.more", { n: num(Math.min(500, g.items.length - limit)) }))));
      }
      group.append(items);
    }
    box.append(group);
  }
  box.scrollTop = scroll;
}

function itemRow(f) {
  const cb = h("input", { type: "checkbox", class: "box", "aria-label": f.name });
  cb.checked = st.selected.has(f.id);
  cb.addEventListener("click", (e) => {
    e.stopPropagation();
    cb.checked ? st.selected.add(f.id) : st.selected.delete(f.id);
    renderGroups(); renderSelected();
  });
  const covered = f.covered_by != null && st.selected.has(f.covered_by);
  const row = h("div", {
    class: "item" + (st.active === f.id ? " is-active" : "") + (covered ? " covered" : ""),
    role: "treeitem", tabindex: 0, title: covered ? t("results.covered") : null,
    onclick: () => { st.active = f.id; showItem(f); renderGroups(); },
    onkeydown: (e) => { if (e.key === "Enter") row.click(); if (e.key === " ") { e.preventDefault(); cb.click(); } },
  }, cb, h("span", { class: "nm" }, h("b", {}, f.name), h("span", {}, "\u200E" + f.path + "\u200E")),
    h("span", { class: "age" }, age(f.mtime)), h("span", { class: "sz" }, bytes(f.size)));
  return row;
}

function markerHead(m) {
  return h("div", { class: "d-marker" }, h("span", { class: `code ${m.risk}` }, m.code),
    h("span", { class: "d-risk" }, t(`riskLong.${m.risk}`)));
}

function showMarker(code) {
  const m = st.markers[code];
  st.active = null;
  fill($("#detail"), markerHead(m), h("h3", {}, m.title[lang]), h("p", { class: "d-desc" }, m.description[lang]),
    h("p", { class: "muted" }, t("detail.pick")));
}

function showItem(f) {
  const m = st.markers[f.marker];
  const facts = h("dl", { class: "facts" },
    h("dt", {}, t("detail.size")), h("dd", {}, bytes(f.size)),
    f.kind === "dir" ? [h("dt", {}, t("detail.files")), h("dd", {}, num(f.files))] : null,
    h("dt", {}, t("detail.changed")), h("dd", {}, Date.now() / 1000 - f.mtime < 86400 ? age(f.mtime) : t("detail.ago", { a: age(f.mtime) })),
    h("dt", {}, t("detail.kind")), h("dd", {}, t(`kind.${f.kind}`)));
  fill($("#detail"), 
    markerHead(m), h("h3", {}, f.name), h("p", { class: "d-desc" }, m.title[lang]),
    h("div", { class: `why ${m.risk}` }, h("small", {}, t("detail.why")), f.reason[lang]),
    f.needs_admin ? h("span", { class: "badge" }, t("detail.admin")) : null,
    facts, h("div", { class: "path" }, f.path),
    h("div", { class: "d-actions" },
      h("button", { class: "btn", onclick: () => api("/api/reveal", { id: f.id }).catch(() => {}) }, t("detail.reveal")),
      h("button", { class: "btn ghost", onclick: () => ignore(f) }, t("detail.ignore"))));
}

function resetDetail() {
  fill($("#detail"), h("p", { class: "empty" }, t("detail.pick")));
}

async function ignore(f) {
  await api("/api/ignore", { path: f.path });
  st.findings = st.findings.filter((x) => !(x.path === f.path || x.path.startsWith(f.path + "/") || x.path.startsWith(f.path + "\\")));
  st.byId = new Map(st.findings.map((x) => [x.id, x]));
  [...st.selected].forEach((id) => { if (!st.byId.has(id)) st.selected.delete(id); });
  st.info.ignore = (await api("/api/info")).ignore;
  resetDetail(); renderResults(); toast(t("toast.ignored"));
}

function renderResults() { renderSummary(); renderGroups(); renderSelected(); }

/* ------------------------------------------------------------------ views */
function show(view) {
  for (const v of ["start", "results", "markers", "history"]) $(`#view-${v}`).hidden = v !== view;
  const tab = view === "start" || view === "results" ? "clean" : view;
  document.querySelectorAll(".tab").forEach((b) => b.classList.toggle("is-on", b.dataset.view === tab));
  if (view === "markers") renderMarkers();
  if (view === "history") renderHistory();
}

function renderMarkers() {
  const box = $("#marker-table");
  fill(box, ...Object.values(st.markers).map((m) =>
    h("div", { class: "m-row" }, h("div", {}, h("span", { class: `code ${m.risk}` }, m.code)),
      h("div", {}, h("b", {}, m.title[lang]), h("span", { class: "d-risk" }, t(`risk.${m.risk}`)), h("p", {}, m.description[lang])))));
}

async function renderHistory() {
  const { history } = await api("/api/history");
  const box = $("#history");
  fill(box, history.length ? "" : h("p", { class: "muted" }, t("history.empty")));
  for (const e of history) {
    const when = new Date(e.time * 1000).toLocaleString(lang === "ru" ? "ru-RU" : "en-US");
    box.append(h("div", { class: "h-row" }, h("span", {}, when), h("b", {}, t("history.row", { n: num(e.ok || 0), s: bytes(e.freed || 0) })),
      h("span", {}, t(`mode.${e.mode === "permanent" ? "permanent" : "trash"}`))));
  }
  const ig = $("#ignored");
  const items = st.info.ignore || [];
  fill(ig, items.length ? "" : h("p", { class: "muted" }, t("history.noIgnored")));
  for (const p of items) {
    ig.append(h("div", { class: "ig-row" }, h("code", {}, p), h("button", { class: "link", onclick: async () => {
      st.info.ignore = (await api("/api/ignore", { path: p, remove: true })).ignore; renderHistory();
    } }, t("history.remove"))));
  }
}

/* ------------------------------------------------------------------- scan */
async function loadResults() {
  const { findings } = await api("/api/results");
  st.findings = findings;
  st.byId = new Map(findings.map((f) => [f.id, f]));
  st.selected = new Set(findings.filter((f) => f.preselect).map((f) => f.id));
  st.open = new Set();
  st.shown = {};
  resetDetail();
}

async function startScan() {
  try {
    await api("/api/scan", { deep: $("#deep").checked, drives: [...st.drives] });
  } catch (e) {
    if (e.status === 409) return toast(t("toast.busy"));
    throw e;
  }
  await followScan();
}

async function followScan() {
  document.body.classList.add("is-scanning");
  $("#scan-btn").hidden = true;
  $("#cancel-btn").hidden = false;
  drawOrb([], true);
  let job;
  for (;;) {
    job = await api("/api/job");
    const p = job.progress || {};
    $("#orb-value").textContent = bytes(p.bytes || 0);
    $("#orb-label").textContent = t("orb.scanning", { n: num(p.found || 0) });
    if (p.phase && p.detail) $("#scan-path").textContent = t(`phase.${p.phase}`, { d: p.detail });
    if (job.state !== "running") break;
    await sleep(220);
  }
  document.body.classList.remove("is-scanning");
  $("#scan-btn").hidden = false;
  $("#cancel-btn").hidden = true;
  $("#scan-path").textContent = "";
  if (job.state === "error") { setOrbIdle(); toast(t("error.scan", { e: job.error })); return; }
  await loadResults();
  const segs = segmentsOf(st.findings);
  const total = segs.reduce((a, x) => a + x.size, 0);
  drawOrb(segs, false);
  $("#orb-value").textContent = bytes(total);
  $("#orb-label").textContent = st.findings.length ? t("orb.done") : t("orb.nothing");
  $("#scan-btn").textContent = t("start.again");
  if (st.findings.length) {
    await sleep(1100);
    renderResults();
    show("results");
  }
}

/* ------------------------------------------------------------------ clean */
const dialog = $("#dialog");

function confirmClean() {
  const { n, size } = effectiveSelected();
  const chosen = [...st.selected].map((id) => st.byId.get(id)).filter(Boolean);
  const by = {};
  for (const f of chosen) {
    if (f.covered_by != null && st.selected.has(f.covered_by)) continue;
    by[f.marker] = by[f.marker] || { n: 0, s: 0 };
    by[f.marker].n++; by[f.marker].s += f.size;
  }
  const perm = st.mode === "permanent";
  const list = h("ul", { class: "dl-list" }, ...Object.entries(by).sort((a, b) => b[1].s - a[1].s).map(([code, v]) =>
    h("li", {}, h("span", { class: `code ${st.markers[code].risk}` }, code), h("span", {}, st.markers[code].title[lang], h("small", { class: "muted" }, " · " + num(v.n))), h("em", {}, bytes(v.s)))));
  const warns = [];
  if (by["CKE-01"]) warns.push(t("dlg.cookies"));
  if (chosen.some((f) => f.risk === "caution" && f.marker !== "CKE-01")) warns.push(t("dlg.caution"));
  if (chosen.some((f) => f.needs_admin) && !st.info.admin) warns.push(t("dlg.admin"));
  const go = h("button", { class: perm ? "btn danger" : "btn primary", onclick: () => runClean() }, t(perm ? "dlg.go.permanent" : "dlg.go.trash"));
  fill(dialog, h("h2", {}, t("dlg.title")), h("p", {}, t(perm ? "dlg.permanent" : "dlg.trash", { n: num(n), s: bytes(size) })),
    list, ...warns.map((w) => h("p", { class: "warn" }, w)),
    h("div", { class: "dl-actions" }, h("button", { class: "btn ghost", onclick: () => dialog.close() }, t("dlg.cancel")), go));
  dialog.showModal();
  go.focus();
}

async function runClean() {
  const ids = [...st.selected].filter((id) => {
    const f = st.byId.get(id);
    return f && !(f.covered_by != null && st.selected.has(f.covered_by));
  });
  const bar = h("div", { class: "progress" }, h("i"));
  const path = h("p", { class: "scan-path" });
  fill(dialog, h("h2", {}, t("dlg.cleaning")), bar, path);
  try { await api("/api/clean", { ids, mode: st.mode }); } catch (e) { dialog.close(); toast(t("toast.busy")); return; }
  let job;
  for (;;) {
    job = await api("/api/job");
    const p = job.progress || {};
    if (p.total) bar.firstChild.style.width = `${(p.step / p.total) * 100}%`;
    path.textContent = p.detail || "";
    if (job.state !== "running") break;
    await sleep(150);
  }
  const res = await api("/api/clean/result");
  const failed = (res.results || []).filter((r) => !["ok", "missing"].includes(r.status));
  const failList = failed.length ? h("ul", { class: "dl-list" }, ...failed.slice(0, 200).map((r) =>
    h("li", {}, h("span", {}, r.path.split(/[\\/]/).pop()), h("em", {}, t(`status.${r.status}`))))) : null;
  fill(dialog, h("h2", {}, t("dlg.done")), h("p", {}, t("dlg.freed", { s: bytes(res.freed || 0) })),
    failed.length ? h("p", {}, t("dlg.skipped", { n: num(failed.length) })) : null, failList,
    h("div", { class: "dl-actions" }, h("button", { class: "btn primary", onclick: () => dialog.close() }, t("dlg.close"))));
  const done = new Set((res.results || []).filter((r) => ["ok", "missing"].includes(r.status)).map((r) => r.id));
  const keep = new Set(st.selected);
  await loadResults();
  st.selected = new Set([...keep].filter((id) => st.byId.has(id) && !done.has(id)));
  renderResults();
}

/* ------------------------------------------------------------------- misc */
let toastTimer;
function toast(msg) {
  const el = $("#toast");
  el.textContent = msg;
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (el.hidden = true), 2600);
}

function bind() {
  document.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => {
    const v = b.dataset.view;
    show(v === "clean" ? (st.findings.length ? "results" : "start") : v);
  }));
  document.querySelectorAll(".lang button").forEach((b) => b.addEventListener("click", async () => {
    lang = b.dataset.lang;
    applyI18n();
    api("/api/settings", { lang }).catch(() => {});
    if (!$("#view-results").hidden) { renderResults(); resetDetail(); }
    if (!$("#view-markers").hidden) renderMarkers();
    if (!$("#view-history").hidden) renderHistory();
    if (!$("#view-start").hidden) {
      renderDrives();
      if (!document.body.classList.contains("is-scanning")) {
        if (st.findings.length) { $("#orb-label").textContent = t("orb.done"); $("#scan-btn").textContent = t("start.again"); }
        else setOrbIdle();
      }
    }
  }));
  $("#scan-btn").addEventListener("click", () => startScan().catch((e) => toast(e.message)));
  $("#cancel-btn").addEventListener("click", () => api("/api/cancel", {}));
  $("#rescan").addEventListener("click", () => { show("start"); startScan().catch((e) => toast(e.message)); });
  $("#sel-rec").addEventListener("click", () => {
    st.selected = new Set(st.findings.filter((f) => f.preselect).map((f) => f.id)); renderGroups(); renderSelected();
  });
  $("#sel-none").addEventListener("click", () => { st.selected.clear(); renderGroups(); renderSelected(); });
  $("#search").addEventListener("input", (e) => { st.query = e.target.value; renderGroups(); });
  document.querySelectorAll("#risk-filter button").forEach((b) => b.addEventListener("click", () => {
    st.risk = b.dataset.risk;
    document.querySelectorAll("#risk-filter button").forEach((x) => x.classList.toggle("is-on", x === b));
    renderGroups();
  }));
  document.querySelectorAll("#mode button").forEach((b) => b.addEventListener("click", () => {
    st.mode = b.dataset.mode;
    document.querySelectorAll("#mode button").forEach((x) => x.classList.toggle("is-on", x === b));
  }));
  $("#clean-btn").addEventListener("click", confirmClean);
  setInterval(() => api("/api/ping", {}).catch(() => {}), 10000);
}

async function boot() {
  st.info = await api("/api/info");
  st.markers = Object.fromEntries(st.info.markers.map((m) => [m.code, m]));
  const saved = st.info.settings && st.info.settings.lang;
  lang = saved || ((navigator.language || "en").toLowerCase().match(/^(ru|kk|be|uk)/) ? "ru" : "en");
  st.drives = new Set(st.info.drives.map((d) => d.path));
  applyI18n();
  bind();
  renderDrives();
  setOrbIdle();
  resetDetail();
  const job = await api("/api/job");
  if (job.state === "running" && job.kind === "scan") return followScan();
  if (job.kind === "scan" && job.state === "done") {
    await loadResults();
    if (st.findings.length) { renderResults(); show("results"); }
  }
}

boot().catch((e) => {
  fill(document.body, h("p", { class: "empty" }, "Voidsweep: " + e.message));
});
