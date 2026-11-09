
async function checkHealth(baseUrl, elementId) {
  const statusElement = document.getElementById(elementId);

  statusElement.textContent = "Checking...";
  statusElement.className = "";

  try {
    const response = await fetch(`${baseUrl}/health`, {
      signal: AbortSignal.timeout(5000)
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    statusElement.textContent = "Healthy";
    statusElement.className = "healthy";
  } catch (error) {
    statusElement.textContent = "Unavailable";
    statusElement.className = "unavailable";
    console.error("Health check failed:", error);
  }
}

async function checkServices() {
  await Promise.all([
    checkHealth(window.API_CONFIG.pantryUrl, "pantry-status"),
    checkHealth(window.API_CONFIG.catalogUrl, "catalog-status")
  ]);
}

document
  .getElementById("refresh-status")
  .addEventListener("click", checkServices);

checkServices();
