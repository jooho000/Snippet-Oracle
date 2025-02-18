const searchInput = $("#search-input");
const resultsContainer = $("#search-results");
const descResultsContainer = $("#search-results-desc");
const snippetTemplate = $("#snippet-template");
const searchDelayMs = 250;

let pendingSearchUrl = null;
let searchTimeout = null;

$(function () {
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
    descResultsContainer.empty();
    $(".search-disclaimer").remove();
    return;
  }

  // Show loading spinner
  searchInput.parent().addClass("is-loading");

  // Send the query to the server via AJAX (using fetch)
  const searchUrl = `/search?q=${encodeURIComponent(query)}`;
  pendingSearchUrl = searchUrl;

  fetch(searchUrl)
    .then((response) => response.json())
    .then((data) => {
      // Ignore results if another
      if (searchUrl !== pendingSearchUrl) return;

      resultsContainer.empty(); // Clear previous results
      descResultsContainer.empty();
      $(".search-disclaimer").remove();

      // If there are results, display them as buttons
      const baseHref =
        snippetTemplate.find(".snippet-card-link").attr("href") + "/../";
      let anyDescMatches = false;
      for (const snippet of data.results) {
        // Add a disclaimer that these are only description matches
        if (!anyDescMatches && snippet.is_description_match) {
          anyDescMatches = true;
          const disclaimer = $(document.createElement("h5"));
          disclaimer.addClass("subtitle mt-6 is-5 search-disclaimer");
          disclaimer.text("Similar public snippets");
          descResultsContainer.before(disclaimer);
        }

        // Create a blank snippet card
        const elem = snippetTemplate.clone();

        // Update attributes
        elem.removeAttr("id");
        elem.data("code", snippet.code);
        elem.data("description", snippet.description);
        elem.find(".snippet-card-name").text(snippet.name);
        elem
          .find(".snippet-card-link")
          .attr("href", new URL(baseHref + snippet.id, location.href).href);

        // Remove whichever public/private label isn't relevant
        if (snippet.is_public) elem.find(".snippet-card-private").remove();
        else elem.find(".snippet-card-public").remove();

        // Remove edit and delete buttons if the current user doesn't own this snippet
        if (snippet.user_id !== current_user_id) {
          elem.find(".snippet-card-edit, .snippet-card-delete").remove();
        }

        // Update summary
        let summary = (snippet.description || "").trim();
        if (summary.length > 100 - 3)
          summary = summary.substring(0, 100 - 3).trim() + "...";
        elem.find(".snippet-card-summary").text(summary);

        elem.appendTo(
          snippet.is_description_match ? descResultsContainer : resultsContainer
        );
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

// Global Set to track selected tags
let selectedTags = new Set();

function filterByTag(tag) {
  const selectedTagsContainer = document.getElementById("selected-tags");

  if (selectedTags.has(tag)) {
    return; // Avoid adding duplicates
  }

  selectedTags.add(tag);

  // Create a removable tag button
  const tagElement = document.createElement("span");
  tagElement.className = "tag is-primary is-rounded";
  tagElement.id = `selected-tag-${tag}`;
  tagElement.innerHTML = `${tag} <button class="delete is-small" onclick="removeTag('${tag}')"></button>`;

  // Append to the selected tags container
  selectedTagsContainer.appendChild(tagElement);

  updateSnippetGrid();
}

function removeTag(tag) {
  if (!selectedTags.has(tag)) return;

  selectedTags.delete(tag);

  // Remove the tag from the UI
  const tagElement = document.getElementById(`selected-tag-${tag}`);
  if (tagElement) tagElement.remove();

  // Ensure correct filtering happens after tag removal
  updateSnippetGrid();
}

function updateSnippetGrid() {
  const snippets = document.querySelectorAll(".box[data-snippet-id]");

  snippets.forEach((snippet) => {
    const tagsContainer = snippet.querySelector(".tags-container");
    const snippetTags = Array.from(
      tagsContainer.getElementsByClassName("tag")
    ).map((tagElement) => tagElement.textContent.trim());

    // Check if the snippet has all selected tags
    // chnage it to the parent element
    const matchesAllTags = [...selectedTags].every((tag) =>
      snippetTags.includes(tag)
    );

    if (matchesAllTags) {
      snippet.parentElement.style.display = "";
    } else {
      snippet.parentElement.style.display = "none";
    }
  });
}
