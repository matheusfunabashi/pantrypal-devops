// What can I cook? (S2-05). Shows which sample recipes the pantry can make now
// and what is missing for the others, from GET /recipes.
//
// - Loads when the page opens, on "Refresh", and again whenever pantry.js
//   reports a change with the "pantry:changed" event.
// - Only reads. Nothing here changes the pantry.
// - API values are put on the page with textContent only, never innerHTML.

(function () {
  const REQUEST_TIMEOUT_MS = 15000;

  const list = document.getElementById("recipes-list");
  const message = document.getElementById("recipes-message");
  const refresh = document.getElementById("refresh-recipes");

  let latestLoad = 0; // only the newest response is drawn

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

  function renderRecipe(recipe) {
    const card = element("li", recipe.ready ? "recipe ready" : "recipe");

    const header = element("div", "recipe-header");
    header.append(
      element("h3", "recipe-name", recipe.name),
      element("span", recipe.ready ? "recipe-status ready" : "recipe-status", recipe.ready ? "Ready" : "Not yet")
    );
    card.appendChild(header);

    const stock = recipe.ingredients.map((i) => `${i.name} (${i.have} on hand, ${i.needed} needed)`);
    card.appendChild(element("p", "recipe-needs", stock.join(", ")));

    const missing = recipe.ingredients.filter((i) => i.missing > 0);
    if (missing.length > 0) {
      const missingList = element("ul", "recipe-missing");
      missing.forEach((i) => {
        missingList.appendChild(element("li", null, `Missing ${i.missing} × ${i.name}`));
      });
      card.appendChild(missingList);
    }
    return card;
  }

  async function loadRecipes() {
    const load = ++latestLoad;
    refresh.disabled = true;
    if (list.children.length === 0) showMessage("Loading...", false);

    try {
      let response;
      try {
        response = await fetch(`${window.API_CONFIG.pantryUrl}/recipes`, {
          signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
        });
      } catch (error) {
        console.error("Recipes request failed:", error);
        throw new Error("Can't reach the pantry right now, try again");
      }
      if (!response.ok) {
        throw new Error(`Couldn't load the recipes (error ${response.status})`);
      }
      const recipes = await response.json();

      if (load !== latestLoad) return;
      list.replaceChildren(...recipes.map(renderRecipe));
      showMessage("", false);
    } catch (error) {
      if (load !== latestLoad) return;
      showMessage(error.message, true);
    } finally {
      if (load === latestLoad) refresh.disabled = false;
    }
  }

  refresh.addEventListener("click", () => loadRecipes());
  document.addEventListener("pantry:changed", () => loadRecipes());

  loadRecipes();
})();
