(function () {
  const list = document.getElementById("restock-list");
  const empty = document.getElementById("restock-empty");
  const message = document.getElementById("restock-message");
  const pending = new Set();
  let latestLoad = 0;

  function showMessage(text, error = false) {
    message.textContent = text;
    message.classList.toggle("error", error);
  }

  async function request(path, options) {
    let response;
    try {
      response = await fetch(`${window.API_CONFIG.pantryUrl}${path}`, {
        ...options,
        signal: AbortSignal.timeout(15000),
      });
    } catch {
      throw new Error("Can't reach the pantry right now. Try again.");
    }

    if (response.ok) return response;

    const body = await response.json().catch(() => null);
    const detail = body?.detail;
    throw new Error(typeof detail === "string" ? detail : `Request failed (${response.status}).`);
  }

  function button(text, label) {
    const control = document.createElement("button");
    control.type = "button";
    control.className = "secondary small";
    control.textContent = text;
    control.setAttribute("aria-label", label);
    return control;
  }

  async function changeTarget(barcode, options, controls, successMessage, onSuccess) {
    if (pending.has(barcode)) return;
    pending.add(barcode);
    controls.forEach((control) => { control.disabled = true; });
    showMessage("");
    try {
      await request(`/stock-targets/${encodeURIComponent(barcode)}`, options);
      onSuccess?.();
      await loadRestock(successMessage);
    } catch (error) {
      showMessage(error.message, true);
    } finally {
      controls.forEach((control) => { control.disabled = false; });
      pending.delete(barcode);
    }
  }

  async function loadRestock(successMessage = "") {
    const load = ++latestLoad;
    try {
      const response = await request("/restock");
      const shortages = await response.json();
      if (load !== latestLoad) return;
      list.replaceChildren(...shortages.map(renderShortage));
      empty.hidden = shortages.length > 0;
      showMessage(successMessage);
    } catch {
      if (load !== latestLoad) return;
      empty.hidden = true;
      showMessage("Couldn't load the restock list. Select Refresh to try again.", true);
    }
  }

  function renderShortage(item) {
    const row = document.createElement("li");
    row.className = "restock-item";
    const text = document.createElement("span");
    text.textContent = `${item.name} — Buy ${item.missing}`;
    row.append(text);

    if (item.quantity === 0) {
      const clear = button("Clear", `Clear minimum for ${item.name}`);
      clear.addEventListener("click", () => {
        changeTarget(item.barcode, { method: "DELETE" }, [clear], "Minimum cleared.");
      });
      row.append(clear);
    }
    return row;
  }

  function addTargetControls(row, item) {
    const group = document.createElement("span");
    group.dataset.restock = "";
    const name = item.name || "this product";

    const label = document.createElement("label");
    label.textContent = "Min";
    const input = document.createElement("input");
    input.type = "number";
    input.min = "1";
    input.max = "999";
    input.step = "1";
    input.id = `stock-target-${item.barcode}`;
    input.setAttribute("aria-label", `Minimum stock for ${name}`);
    label.htmlFor = input.id;

    const set = button("Set", `Set minimum for ${name}`);
    const clear = button("Clear", `Clear minimum for ${name}`);
    const controls = [input, set, clear];

    set.addEventListener("click", () => {
      if (!input.value || !input.checkValidity()) {
        showMessage("Enter a whole number from 1 to 999.", true);
        input.focus();
        return;
      }
      changeTarget(item.barcode, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: input.valueAsNumber }),
      }, controls, "Minimum saved.");
    });

    clear.addEventListener("click", () => {
      changeTarget(item.barcode, { method: "DELETE" }, controls, "Minimum cleared.", () => {
        input.value = "";
      });
    });

    group.append(label, input, set, clear);
    row.append(group);
  }

  document.addEventListener("pantry:changed", ({ detail: items }) => {
    const rows = document.getElementById("pantry-list").children;
    if (Array.isArray(items)) {
      items.forEach((item, index) => addTargetControls(rows[index], item));
    }
    loadRestock();
  });

  document.getElementById("refresh-restock").addEventListener("click", () => loadRestock());
  loadRestock();
})();
