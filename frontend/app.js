
async function checkHealth(baseUrl, elementId) {
  const element = document.getElementById(elementId);

  element.textContent = "Checking...";
  element.className = "";

  try {
    const response = await fetch(`${baseUrl}/health`, {
      signal: AbortSignal.timeout(5000)
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    element.textContent = "Healthy";
    element.className = "healthy";

  } catch (error) {
    element.textContent = "Unavailable";
    element.className = "unavailable";

    console.error("Health check failed:", error);
  }
}

async function checkServices() {
  await Promise.all([
    checkHealth(
      window.API_CONFIG.pantryUrl,
      "pantry-status"
    ),

    checkHealth(
      window.API_CONFIG.catalogUrl,
      "catalog-status"
    )
  ]);
}

document
  .getElementById("refresh-status")
  .addEventListener("click", checkServices);

checkServices();
