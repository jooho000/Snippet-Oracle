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

function filterByTag(tag) {
  const searchInput = document.getElementById("search-input");
  const selectedTagsContainer = document.getElementById("selected-tags");

  // Get the current query
  let currentQuery = searchInput.value.trim();

  // Check if the tag is already selected
  if (currentQuery.includes(`:${tag}`)) {
      // Remove the tag from the search query
      currentQuery = currentQuery.replace(new RegExp(`:?${tag}`, "g"), "").trim();

      // Remove the tag from the selected tags section
      const tagElement = document.getElementById(`selected-tag-${tag}`);
      if (tagElement) tagElement.remove();
  } else {
      // Add the tag to the search query
      currentQuery += ` :${tag}`;

      // Create a removable tag button
      const tagElement = document.createElement("span");
      tagElement.className = "tag is-primary is-rounded";
      tagElement.id = `selected-tag-${tag}`;
      tagElement.innerHTML = `${tag} <button class="delete is-small" onclick="removeTag('${tag}')"></button>`;

      // Append to the selected tags container
      selectedTagsContainer.appendChild(tagElement);
  }

  // Update the search input field
  searchInput.value = currentQuery.trim();

  // If no tags or search text, clear results
  if (!searchInput.value) {
      document.getElementById("search-results").innerHTML = "";
      return;
  }

  // Trigger search
  fetch(`/search?q=${encodeURIComponent(searchInput.value)}`)
      .then(response => response.json())
      .then(data => {
          displaySearchResults(data.results);
      })
      .catch(error => console.error("Error:", error));
}

// Function to remove a tag and update results
function removeTag(tag) {
  const searchInput = document.getElementById("search-input");
  let currentQuery = searchInput.value.trim();

  // Remove the tag from the search query
  currentQuery = currentQuery.replace(new RegExp(`:?${tag}`, "g"), "").trim();

  // Update search input
  searchInput.value = currentQuery;

  // Remove the tag from the selected tags section
  const tagElement = document.getElementById(`selected-tag-${tag}`);
  if (tagElement) tagElement.remove();

  // If no tags or search text, clear results
  if (!searchInput.value) {
      document.getElementById("search-results").innerHTML = "";
      return;
  }

  // Re-run the search
  fetch(`/search?q=${encodeURIComponent(searchInput.value)}`)
      .then(response => response.json())
      .then(data => {
          displaySearchResults(data.results);
      })
      .catch(error => console.error("Error:", error));
}


function displaySearchResults(snippets) {
  let resultsContainer = document.getElementById("search-results");
  resultsContainer.innerHTML = ""; // Clear previous results

  if (snippets.length === 0) {
      resultsContainer.innerHTML = "<p class='has-text-centered'>No snippets found.</p>";
      return;
  }

  let uniqueSnippets = new Map(); // Store snippets by ID to avoid duplicates

  snippets.forEach((snippet) => {
      if (!uniqueSnippets.has(snippet.id)) {
          uniqueSnippets.set(snippet.id, snippet); // Add to Map if not already present
      }
  });

  let gridHtml = '<div class="columns is-multiline">';

  uniqueSnippets.forEach((snippet) => {
      // Try to find the snippet in the existing page content
      let existingSnippet = document.querySelector(`[data-snippet-id="${snippet.id}"]`);

      let description = existingSnippet 
          ? existingSnippet.querySelector(".snippet-description").textContent.trim()
          : "No description available.";

      let visibilityTag = existingSnippet 
          ? existingSnippet.querySelector(".snippet-visibility").outerHTML
          : '<span class="tag is-danger"><i class="fas fa-lock"></i> Private</span>';

      gridHtml += `
          <div class="column is-4-desktop is-6-tablet is-12-mobile">
              <div class="box">
                  <!-- Top Section: Name (Left) + Copy & Visibility (Right) -->
                  <div class="columns is-vcentered">
                      <div class="column has-text-left">
                          <h2 class="title is-5">${snippet.name}</h2>
                      </div>
                      <div class="column has-text-right">
                          <!-- Visibility Tag (Top Right) -->
                          ${visibilityTag}

                          <!-- Copy Button (Top Right) -->
                          <button class="button is-small is-info ml-2" onclick="copySnippet(\`${snippet.code}\`)">
                              <span class="icon">
                                  <i class="fas fa-copy"></i>
                              </span>
                          </button>
                      </div>
                  </div>

                  <!-- Snippet Description -->
                  <p class="is-italic snippet-description">${description}</p>

                  <!-- View Snippet Button (Bottom Left) -->
                  <div class="buttons mt-3">
                      <a href="/snippet/${snippet.id}" class="button is-link">View</a>
                  </div>
              </div>
          </div>`;
  });

  gridHtml += '</div>';
  resultsContainer.innerHTML = gridHtml;
}

