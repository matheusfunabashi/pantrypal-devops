// Product lookup (S1-12). Calls the Catalog Service and shows the result.
//
// window.lookupProduct(barcode) returns the product from the Catalog Service
// or throws an Error whose .kind is "invalid", "notfound" or "unavailable".
// After every successful lookup the page also dispatches a "product:found"
// event on document, with the product in event.detail, so the pantry UI can
// offer "Add to pantry" for it.
//
// API values are only ever put on the page with textContent (or as an image
// URL after a scheme check), never innerHTML.

(function () {
  const LOOKUP_TIMEOUT_MS = 10000;
  const BARCODE_PATTERN = /^\d{8,14}$/;

  const MESSAGES = {
    invalid: "Please enter 8 to 14 digits",
    notfound: "Product not found",
    unavailable: "Lookup is temporarily unavailable, try again",
  };

  function lookupError(kind) {
    const error = new Error(MESSAGES[kind]);
    error.kind = kind;
    return error;
  }

  async function lookupProduct(barcode) {
    const code = String(barcode).trim();

    if (!BARCODE_PATTERN.test(code)) {
      throw lookupError("invalid");
    }

    let response;
    try {
      response = await fetch(
        `${window.API_CONFIG.catalogUrl}/products/${encodeURIComponent(code)}`,
        { signal: AbortSignal.timeout(LOOKUP_TIMEOUT_MS) }
      );
    } catch (error) {
      console.error("Lookup failed:", error);
      throw lookupError("unavailable"); // network error or timeout
    }

    if (response.status === 404) throw lookupError("notfound");
    if (response.status === 422) throw lookupError("invalid");
    if (!response.ok) throw lookupError("unavailable");

    try {
      return await response.json();
    } catch (error) {
      console.error("Lookup returned invalid JSON:", error);
      throw lookupError("unavailable");
    }
  }

  window.lookupProduct = lookupProduct;

  // Only show images served over http(s).
  function isHttpUrl(value) {
    try {
      const url = new URL(value);
      return url.protocol === "https:" || url.protocol === "http:";
    } catch (error) {
      return false;
    }
  }

  function showMessage(text, isError) {
    const message = document.getElementById("lookup-message");
    message.textContent = text;
    message.className = isError ? "message error" : "message";
  }

  function showProduct(product) {
    const image = document.getElementById("product-image");
    if (product.image_url && isHttpUrl(product.image_url)) {
      image.src = product.image_url;
      image.alt = product.name ? `Photo of ${product.name}` : "Product photo";
      image.hidden = false;
    } else {
      image.removeAttribute("src");
      image.alt = "";
      image.hidden = true;
    }

    document.getElementById("product-name").textContent =
      product.name || "Not available";
    document.getElementById("product-brand").textContent =
      product.brand || "Not available";
    document.getElementById("product-nutriscore").textContent =
      product.nutri_score ? product.nutri_score.toUpperCase() : "Not available";

    document.getElementById("lookup-result").hidden = false;
  }

  function hideProduct() {
    document.getElementById("lookup-result").hidden = true;
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const input = document.getElementById("barcode");
    const button = document.getElementById("lookup-button");

    hideProduct();
    showMessage("", false);
    button.disabled = true;
    showMessage("Looking up...", false);

    try {
      const product = await lookupProduct(input.value);
      showMessage("", false);
      showProduct(product);
      document.dispatchEvent(new CustomEvent("product:found", { detail: product }));
    } catch (error) {
      showMessage(error.kind ? error.message : MESSAGES.unavailable, true);
    } finally {
      button.disabled = false;
    }
  }

  document.getElementById("lookup-form").addEventListener("submit", handleSubmit);
})();
