// Pantry overview (S2-10). Counts the packages in the pantry per Nutri-Score
// grade, from GET /pantry, and shows the share graded A or B.
//
// - Loads when the page opens and on "Refresh". When pantry.js reports a change
//   with "pantry:changed", it reuses the items that came with the event.
// - Only reads. Nothing here changes the pantry.
// - API values are put on the page with textContent only, never innerHTML.

(function () {
  const REQUEST_TIMEOUT_MS = 15000;
  const GRADES = ["a", "b", "c", "d", "e"];

  const list = document.getElementById("summary-list");
  const share = document.getElementById("summary-share");
  const message = document.getElementById("summary-message");
  const refresh = document.getElementById("refresh-summary");

  let latestLoad = 0; // only the newest result is drawn

  function showMessage(text, isError) {
    message.textContent = text;
    message.className = isError ? "message error" : "message";
  }

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  // Packages per grade. Quantity counts, so 3 × one product is 3 packages.
  function countByGrade(items) {
    const counts = { a: 0, b: 0, c: 0, d: 0, e: 0, unknown: 0 };
    items.forEach((item) => {
      const grade = String(item.nutri_score || "").trim().toLowerCase();
      const key = GRADES.includes(grade) ? grade : "unknown";
      counts[key] += Number(item.quantity) || 0;
    });
    return counts;
  }

  function row(className, label, count) {
    const li = element("li", "summary-row");
    li.append(element("span", `nutri-badge ${className}`, label), element("span", "summary-count", String(count)));
    return li;
  }

  function render(items) {
    const counts = countByGrade(items);
    const total = Object.values(counts).reduce((sum, n) => sum + n, 0);

    if (total === 0) {
      list.replaceChildren();
      share.textContent = "";
      showMessage("Add products to see your overview.", false);
      return;
    }

    list.replaceChildren(
      ...GRADES.map((grade) => row(`nutri-${grade}`, grade.toUpperCase(), counts[grade])),
      row("nutri-unknown", "Not available", counts.unknown)
    );
    const good = counts.a + counts.b;
    const percent = Math.round((good / total) * 100);
    const noun = total === 1 ? "package" : "packages";
    share.textContent = `${good} of ${total} ${noun} (${percent}%) are A or B`;
    showMessage("", false);
  }

  async function loadSummary() {
    const load = ++latestLoad;
    refresh.disabled = true;
    if (list.children.length === 0) showMessage("Loading...", false);

    try {
      let response;
      try {
        response = await fetch(`${window.API_CONFIG.pantryUrl}/pantry`, {
          signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
        });
      } catch (error) {
        console.error("Pantry overview request failed:", error);
        throw new Error("Can't reach the pantry right now, try again");
      }
      if (!response.ok) {
        throw new Error(`Couldn't load the overview (error ${response.status})`);
      }
      const items = await response.json();

      if (load !== latestLoad) return;
      render(items);
    } catch (error) {
      if (load !== latestLoad) return;
      showMessage(error.message, true);
    } finally {
      if (load === latestLoad) refresh.disabled = false;
    }
  }

  refresh.addEventListener("click", () => loadSummary());
  document.addEventListener("pantry:changed", ({ detail: items }) => {
    if (!Array.isArray(items)) {
      loadSummary();
      return;
    }
    latestLoad++; // a newer list than any request still in flight
    refresh.disabled = false;
    render(items);
  });

  loadSummary();
})();
