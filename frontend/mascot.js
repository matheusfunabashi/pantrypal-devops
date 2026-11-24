// Pixel mascot. Decorative only: it never calls the APIs or changes the pantry.
// - Hops when pantry.js reports a change ("pantry:changed").
// - Wiggles when a recipe card turns "Ready".
// - Click it for a tip.

(function () {
  // 16 × 16 jar with a face. Each letter is a colour, "." is transparent.
  const SPRITE = [
    "....kkkkkkkk....",
    "...krrrrrrrrk...",
    "...krrwrrwrrk...",
    "...kkkkkkkkkk...",
    "....kggggggk....",
    "...kgggggggkk...",
    "..kggggggggggk..",
    "..kgwwggggwwgk..",
    "..kgwkggggwkgk..",
    "..kggggggggggk..",
    "..kgpggggggpgk..",
    "..kgggkkkkgggk..",
    "..kggggkkggggk..",
    "..kggggggggggk..",
    "...kggggggggk...",
    "....kkkkkkkk....",
  ];
  const COLOURS = { k: "#1f2a24", r: "#c8423b", w: "#ffffff", g: "#7cc47f", p: "#f29bb0" };

  const TIPS = [
    "Scan a barcode to check its Nutri-Score!",
    "A and B are the healthiest grades.",
    "Set a Min to get a restock reminder.",
    "Got spaghetti and pesto? That's dinner!",
    "Checking a product doesn't add it.",
  ];

  const header = document.querySelector("header");
  if (!header) return;

  const button = document.createElement("button");
  button.type = "button";
  button.className = "mascot";
  button.setAttribute("aria-label", "PantryPal mascot, click for a tip");

  const canvas = document.createElement("canvas");
  canvas.width = 16;
  canvas.height = 16;
  const ctx = canvas.getContext("2d");
  SPRITE.forEach((row, y) => {
    [...row].forEach((cell, x) => {
      if (COLOURS[cell]) {
        ctx.fillStyle = COLOURS[cell];
        ctx.fillRect(x, y, 1, 1);
      }
    });
  });

  const bubble = document.createElement("span");
  bubble.className = "mascot-bubble";
  bubble.setAttribute("role", "status");

  button.append(canvas, bubble);
  header.prepend(button);

  let bubbleTimer;
  function say(text) {
    bubble.textContent = text;
    bubble.classList.add("show");
    clearTimeout(bubbleTimer);
    bubbleTimer = setTimeout(() => bubble.classList.remove("show"), 2500);
  }

  function play(name) {
    button.classList.remove("hop", "happy");
    void button.offsetWidth; // restart the animation
    button.classList.add(name);
  }
  button.addEventListener("animationend", () => button.classList.remove("hop", "happy"));

  let tip = 0;
  button.addEventListener("click", () => {
    play("hop");
    say(TIPS[tip]);
    tip = (tip + 1) % TIPS.length;
  });

  // The first "pantry:changed" is the page load, so stay quiet for that one.
  let loaded = false;
  document.addEventListener("pantry:changed", () => {
    if (!loaded) {
      loaded = true;
      return;
    }
    play("hop");
    say("Pantry updated!");
  });

  // Celebrate when the number of ready recipes goes up.
  const recipes = document.getElementById("recipes-list");
  if (recipes) {
    let ready = null;
    new MutationObserver(() => {
      const now = recipes.querySelectorAll(".recipe.ready").length;
      if (ready !== null && now > ready) {
        play("happy");
        say("A recipe is ready to cook!");
      }
      ready = now;
    }).observe(recipes, { childList: true });
  }
})();
