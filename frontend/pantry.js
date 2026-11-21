// Pantry UI (S1-13, S1-10b). Lists the pantry, adds the looked-up product to it,
// and changes or removes items.
//
// - The list loads when the page opens and again after every change.
// - + and - set the quantity with PUT /pantry/{id} (- is disabled at 1).
//   "Remove" asks for confirmation, then sends DELETE /pantry/{id}.
// - "Add to pantry" appears after a successful lookup. lookup.js tells us about
//   it with the "product:found" event (the product is in event.detail).
// - API errors show the API's own "detail" message. Network errors and timeouts
//   show a generic message.
//
// API values are only ever put on the page with textContent (or as an image
// URL after a scheme check), never innerHTML.

(function () {
  const REQUEST_TIMEOUT_MS = 15000;
  const MAX_QUANTITY = 999;
  const NETWORK_ERROR = "Can't reach the pantry right now, try again";

  let currentBarcode = null; // barcode of the product shown by the last lookup

  function pantryUrl(path) {
    return `${window.API_CONFIG.pantryUrl}${path}`;
  }

  // The message the user sees for a failed response. FastAPI sends
  // {"detail": "..."} for our own errors and {"detail": [{msg: ...}]} when
  // validation fails.
  async function errorMessage(response) {
    try {
      const body = await response.json();
      if (typeof body.detail === "string") return body.detail;
      if (Array.isArray(body.detail) && body.detail[0] && body.detail[0].msg) {
        return body.detail[0].msg;
      }
    } catch (error) {
      // Not JSON, fall through to the generic message.
    }
    return `Something went wrong (error ${response.status})`;
  }

  // fetch() with a timeout. Returns the parsed JSON body, or throws an Error
  // whose message can be shown to the user as it is.
  async function request(path, options) {
    let response;
    try {
      response = await fetch(pantryUrl(path), {
        ...options,
        signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
      });
    } catch (error) {
      console.error("Pantry request failed:", error);
      throw new Error(NETWORK_ERROR); // offline, CORS, DNS or timeout
    }

    if (!response.ok) {
      throw new Error(await errorMessage(response));
    }

    if (response.status === 204) {
      return { status: 204, body: null }; // DELETE answers with no body
    }

    try {
      return { status: response.status, body: await response.json() };
    } catch (error) {
      console.error("Pantry returned invalid JSON:", error);
      throw new Error(NETWORK_ERROR);
    }
  }

  // Only show images served over http(s).
  function isHttpUrl(value) {
    try {
      const url = new URL(value);
      return url.protocol === "https:" || url.protocol === "http:";
    } catch (error) {
      return false;
    }
  }

  function showMessage(elementId, text, isError) {
    const message = document.getElementById(elementId);
    message.textContent = text;
    message.className = isError ? "message error" : "message";
  }

  function renderItem(item) {
    const row = document.createElement("li");
    row.className = "pantry-item";

    if (item.image_url && isHttpUrl(item.image_url)) {
      const image = document.createElement("img");
      image.src = item.image_url;
      image.alt = item.name ? `Photo of ${item.name}` : "Product photo";
      image.loading = "lazy";
      row.appendChild(image);
    } else {
      const placeholder = document.createElement("div");
      placeholder.className = "no-image";
      placeholder.textContent = "No image";
      row.appendChild(placeholder);
    }

    const details = document.createElement("div");
    details.className = "pantry-details";

    const name = document.createElement("p");
    name.className = "pantry-name";
    name.textContent = item.name || "Unknown product";

    const brand = document.createElement("p");
    brand.className = "pantry-brand";
    brand.textContent = item.brand || "Brand not available";

    const nutri = document.createElement("p");
    nutri.className = "pantry-nutri";
    nutri.textContent = `Nutri-Score: ${
      item.nutri_score ? item.nutri_score.toUpperCase() : "Not available"
    }`;

    details.append(name, brand, nutri);

    const label = item.name || "this product";

    const decrease = document.createElement("button");
    decrease.type = "button";
    decrease.className = "secondary small";
    decrease.textContent = "−";
    decrease.setAttribute("aria-label", `Decrease quantity of ${label}`);
    decrease.disabled = item.quantity <= 1;
    decrease.addEventListener("click", () => changeQuantity(row, item, item.quantity - 1));

    const quantity = document.createElement("span");
    quantity.className = "pantry-quantity";
    quantity.textContent = String(item.quantity);
    quantity.setAttribute("aria-label", `Quantity ${item.quantity}`);

    const increase = document.createElement("button");
    increase.type = "button";
    increase.className = "secondary small";
    increase.textContent = "+";
    increase.setAttribute("aria-label", `Increase quantity of ${label}`);
    increase.disabled = item.quantity >= MAX_QUANTITY;
    increase.addEventListener("click", () => changeQuantity(row, item, item.quantity + 1));

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "danger small";
    remove.textContent = "Remove";
    remove.setAttribute("aria-label", `Remove ${label} from your pantry`);
    remove.addEventListener("click", () => removeItem(row, item));

    const controls = document.createElement("div");
    controls.className = "pantry-controls";
    controls.append(decrease, quantity, increase, remove);

    row.append(details, controls);
    return row;
  }

  // While a change is being saved, the row's buttons are disabled so a double
  // click doesn't send it twice. loadPantry() redraws the row afterwards.
  function setRowBusy(row, busy) {
    row.querySelectorAll("button").forEach((button) => {
      button.disabled = busy;
    });
  }

  async function changeQuantity(row, item, quantity) {
    setRowBusy(row, true);
    showMessage("pantry-message", "Saving...", false);
    try {
      await request(`/pantry/${item.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ quantity }),
      });
      await loadPantry();
    } catch (error) {
      showMessage("pantry-message", error.message, true);
      // The item may have changed or been removed elsewhere: show the real state.
      await loadPantry({ keepMessage: true });
    }
  }

  async function removeItem(row, item) {
    const name = item.name || "this product";
    if (!window.confirm(`Remove ${name} from your pantry?`)) return;

    setRowBusy(row, true);
    showMessage("pantry-message", "Removing...", false);
    try {
      await request(`/pantry/${item.id}`, { method: "DELETE" });
      await loadPantry();
    } catch (error) {
      showMessage("pantry-message", error.message, true);
      await loadPantry({ keepMessage: true });
    }
  }

  // keepMessage: leave an error from a failed change on screen while reloading.
  async function loadPantry({ keepMessage = false } = {}) {
    const list = document.getElementById("pantry-list");
    const empty = document.getElementById("pantry-empty");

    if (!keepMessage) showMessage("pantry-message", "Loading...", false);
    try {
      const { body: items } = await request("/pantry");
      list.replaceChildren(...items.map(renderItem));
      empty.hidden = items.length > 0;
      if (!keepMessage) showMessage("pantry-message", "", false);
      document.dispatchEvent(new CustomEvent("pantry:changed", { detail: items }));
    } catch (error) {
      // Keep the first error if there is one: it explains what went wrong.
      if (!keepMessage) showMessage("pantry-message", error.message, true);
    }
  }

  function showAddForm(product) {
    currentBarcode = product.barcode;
    document.getElementById("add-quantity").value = "1";
    showMessage("add-message", "", false);
    document.getElementById("add-form").hidden = false;
  }

  function hideAddForm() {
    currentBarcode = null;
    document.getElementById("add-form").hidden = true;
    showMessage("add-message", "", false);
  }

  async function handleAdd(event) {
    event.preventDefault();
    if (!currentBarcode) return;

    const input = document.getElementById("add-quantity");
    const button = document.getElementById("add-button");
    const cancel = document.getElementById("cancel-product");
    const text = input.value.trim();
    const quantity = Number(text);

    if (!/^\d+$/.test(text) || quantity < 1 || quantity > MAX_QUANTITY) {
      showMessage("add-message", `Please enter a quantity from 1 to ${MAX_QUANTITY}`, true);
      return;
    }

    button.disabled = true;
    cancel.disabled = true;
    showMessage("add-message", "Adding...", false);
    try {
      const { status, body: item } = await request("/pantry", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ barcode: currentBarcode, quantity }),
      });
      const name = item.name || "Product";
      // 201 = new item, 200 = the barcode was already there and its quantity went up.
      showMessage(
        "add-message",
        status === 201
          ? `Added ${name} to your pantry`
          : `${name} is now × ${item.quantity} in your pantry`,
        false
      );
      await loadPantry();
    } catch (error) {
      showMessage("add-message", error.message, true);
    } finally {
      button.disabled = false;
      cancel.disabled = false;
    }
  }

  document.addEventListener("product:found", (event) => showAddForm(event.detail));
  document.addEventListener("product:cleared", hideAddForm);
  document.getElementById("add-form").addEventListener("submit", handleAdd);
  document.getElementById("refresh-pantry").addEventListener("click", () => loadPantry());

  document.addEventListener("DOMContentLoaded", () => loadPantry());
})();
