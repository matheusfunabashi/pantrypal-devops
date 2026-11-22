// Compare two products (S2-09). Puts the looked-up product next to an
// alternative and says which has the better Nutri-Score.
//
// - Both products come from window.lookupProduct (lookup.js).
// - The badge is window.createNutriScoreBadge (lookup.js), same as the lookup.
// - Only reads. It never writes to the pantry.
//
// API values are only put on the page with textContent (or as an image URL
// after a scheme check), never innerHTML.

(function () {
  const GRADES = ["a", "b", "c", "d", "e"];

  let firstBarcode = null; // barcode of the product from the last lookup

  let selectionVersion = 0;

  function showMessage(text, isError) {
    const message = document.getElementById("compare-message");
    message.textContent = text;
    message.className = isError ? "message error" : "message";
  }

  function isHttpUrl(value) {
    try {
      const url = new URL(value);
      return url.protocol === "https:" || url.protocol === "http:";
    } catch (error) {
      return false;
    }
  }

  function grade(product) {
    const value = typeof product.nutri_score === "string" ? product.nutri_score.trim().toLowerCase() : "";
    return GRADES.includes(value) ? value : null;
  }

  function renderCard(product, isBetter) {
    const card = document.createElement("div");
    card.className = "compare-card";

    if (product.image_url && isHttpUrl(product.image_url)) {
      const image = document.createElement("img");
      image.src = product.image_url;
      image.alt = product.name ? `Photo of ${product.name}` : "Product photo";
      card.appendChild(image);
    }

    const name = document.createElement("p");
    name.className = "compare-name";
    name.textContent = product.name || "Not available";

    const brand = document.createElement("p");
    brand.className = "compare-brand";
    brand.textContent = product.brand || "Not available";

    const badge = document.createElement("p");
    badge.appendChild(window.createNutriScoreBadge(product.nutri_score));

    card.append(name, brand, badge);

    if (isBetter) {
      const better = document.createElement("p");
      better.className = "compare-better";
      better.textContent = "Better Nutri-Score";
      card.appendChild(better);
    }
    return card;
  }

  // "first", "second", "same" or "missing".
  function verdict(first, second) {
    const a = grade(first);
    const b = grade(second);
    if (!a || !b) return "missing";
    if (a === b) return "same";
    return GRADES.indexOf(a) < GRADES.indexOf(b) ? "first" : "second";
  }

  async function handleCompare(event) {
    event.preventDefault();
    const result = document.getElementById("compare-result");
    const button = document.getElementById("compare-button");
    result.replaceChildren();

    if (!firstBarcode) {
      showMessage("Look up a product above first", true);
      return;
    }

    const version = selectionVersion;
    button.disabled = true;
    showMessage("Comparing...", false);
    try {
      const secondBarcode = document.getElementById("compare-barcode").value;
      const [first, second] = await Promise.all([
        window.lookupProduct(firstBarcode),
        window.lookupProduct(secondBarcode),
      ]);
      if (version !== selectionVersion) return;
      const outcome = verdict(first, second);
      result.append(
        renderCard(first, outcome === "first"),
        renderCard(second, outcome === "second")
      );
      if (outcome === "same") showMessage("Same Nutri-Score", false);
      else if (outcome === "missing") showMessage("Can't compare: Nutri-Score not available", false);
      else showMessage("", false);
    } catch (error) {
      if (version !== selectionVersion) return;
      showMessage(error.kind ? error.message : "Lookup is temporarily unavailable, try again", true);
    } finally {
      if (version === selectionVersion) button.disabled = false;
    }
  }

  function setFirst(barcode) {
    selectionVersion += 1;
    firstBarcode = barcode;
    document.getElementById("compare-button").disabled = false;
    document.getElementById("compare-first").textContent = barcode
      ? `Comparing with ${barcode}`
      : "Look up a product above, then enter a second barcode.";
    document.getElementById("compare-result").replaceChildren();
    showMessage("", false);
  }

  document.addEventListener("product:found", (event) => setFirst(String(event.detail.barcode)));
  document.addEventListener("product:cleared", () => setFirst(null));
  document.getElementById("compare-form").addEventListener("submit", handleCompare);
})();
