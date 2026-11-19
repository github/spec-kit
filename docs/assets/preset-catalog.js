(() => {
  const catalog = document.querySelector("[data-preset-catalog]");
  if (!catalog) return;

  const form = catalog.querySelector("[data-preset-controls]");
  const query = form.elements.namedItem("q");
  const tag = form.elements.namedItem("tag");
  const sort = form.elements.namedItem("sort");
  const list = catalog.querySelector(".preset-results");
  const entries = Array.from(list.children);
  const status = catalog.querySelector("[data-preset-status]");
  const empty = catalog.querySelector("[data-preset-empty]");
  const searchable = entries.map((entry) => ({
    entry,
    text: entry.dataset.presetSearch.toLocaleLowerCase(),
    tags: JSON.parse(entry.dataset.presetTags),
  }));
  const params = new URLSearchParams(window.location.search);
  query.value = params.get("q") || "";
  tag.value = params.get("tag") || "";
  if (!tag.value) tag.value = "";
  sort.value = params.get("sort") === "za" ? "za" : "az";

  function update() {
    const words = query.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    let visible = 0;
    for (const item of searchable) {
      const matches = words.every((word) => item.text.includes(word))
        && (!tag.value || item.tags.includes(tag.value));
      item.entry.hidden = !matches;
      if (matches) visible += 1;
    }
    const ordered = sort.value === "za" ? [...entries].reverse() : entries;
    for (const entry of ordered) list.append(entry);
    status.textContent = `${visible} of ${entries.length} presets`;
    empty.hidden = visible !== 0;

    const next = new URL(window.location.href);
    for (const [key, value] of [["q", query.value], ["tag", tag.value], ["sort", sort.value === "za" ? "za" : ""]]) {
      if (value) next.searchParams.set(key, value);
      else next.searchParams.delete(key);
    }
    window.history.replaceState(null, "", next);
  }

  form.addEventListener("input", update);
  form.addEventListener("change", update);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    update();
  });
  form.addEventListener("reset", () => {
    query.value = "";
    tag.value = "";
    sort.value = "az";
    update();
  });
  update();
  form.hidden = false;
})();
