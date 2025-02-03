const searchInput = $("#search-input");
const resultsContainer = $("#search-results");
const searchDelayMs = 250;

let pendingSearchUrl = null;
let searchTimeout = null;

$(function() {
  searchInput.on("input", function () {
    if (searchTimeout !== null) {
      clearTimeout(searchTimeout);
    }
    searchTimeout = setTimeout(doSearch, searchDelayMs);
  });
});

async function doSearch() {
  const query = searchInput.val();
  searchTimeout = null;

  // Don't search if input is empty
  if (!query.trim()) {
    resultsContainer.empty();
    return;
  }

  // Show loading spinner
  searchInput.parent().addClass("is-loading");

  // Send the query to the server via AJAX (using fetch)
  const searchUrl = `/search?q=${query}`;
  pendingSearchUrl = searchUrl;

  fetch(searchUrl)
    .then((response) => response.json())
    .then((data) => {
      // Ignore results if another
      if (searchUrl !== pendingSearchUrl) return;

      resultsContainer.empty(); // Clear previous results

      // If there are results, display them as buttons
      for (const snippet of data.results) {
        $("<a/>", {
          href: `/snippet/${snippet.id}`,
          class: "button is-primary is-large mt-2 mr-2",
        })
          .text(snippet.name)
          .appendTo(resultsContainer);
      }
      if (data.results.length === 0) {
        resultsContainer.text("No snippets found.");
      }
    })
    .catch((error) => {
      console.error("Error fetching search results:", error);
      resultsContainer.text("Error occurred while searching.");
    })
    .finally(() => {
      if (searchUrl === pendingSearchUrl) {
        pendingSearchUrl = null;
        searchInput.parent().removeClass("is-loading");
      }
    });
}

function toggleSnippet(id, button, snippetContent, snippetDescription) {
  const container = document.getElementById(id);
  const icon = button.querySelector("svg");

  if (!container.hasChildNodes()) {
    // Create snippet content dynamically
    const contentDiv = document.createElement("div");
    contentDiv.className = "mt-3";

    // Add snippet content and description (no Copy button)
    contentDiv.innerHTML = `
            <hr>
            <pre class="code-snippet">${snippetContent}</pre>
            <p><strong>Description:</strong> ${
              snippetDescription || "No description available."
            }</p>
        `;
    container.appendChild(contentDiv);

    // Show the container
    container.style.display = "block";

    // Update icon to up arrow
    icon.setAttribute("d", "M5 15l7-7 7 7");
  } else {
    // Destroy snippet content dynamically
    container.innerHTML = ""; // Remove child nodes
    container.style.display = "none"; // Hide the container

    // Update icon to down arrow
    icon.setAttribute("d", "M19 9l-7 7-7-7");
  }
}

function copySnippet(code) {
  navigator.clipboard
    .writeText(code)
    .then(() => {
      alert("Code snippet copied to clipboard!");
    })
    .catch((err) => {
      console.error("Failed to copy text: ", err);
    });
}
