const searchInput = $("#search-input");
const resultsContainer = $("#search-results");
const snippetTemplate = $("#snippet-template");
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
      const baseHref = snippetTemplate.find(".snippet-card-link").attr("href") + "/../"
      for (const snippet of data.results) {
        const url = new URL(baseHref + snippet.id, location.href);

        const elem = snippetTemplate.clone();
        elem.find(".snippet-card-public, .snippet-card-private, .snippet-card-copy, .snippet-card-expand").remove();
        elem.removeAttr("id");
        elem.find(".snippet-card-name").text(snippet.name);
        elem.find(".snippet-card-link").attr("href", url.href);
        elem.appendTo(resultsContainer);
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

  console.log("Selected Tags:", Array.from(selectedTags));
  updateSnippetGrid();
  console.log("reached updateSnippetGrid intial");
}


function removeTag(tag) {
  if (!selectedTags.has(tag)) return;

  selectedTags.delete(tag);

  // Remove the tag from the UI
  const tagElement = document.getElementById(`selected-tag-${tag}`);
  if (tagElement) tagElement.remove();

  // Ensure correct filtering happens after tag removal
  updateSnippetGrid();
  console.log("reached updateSnippetGrid remove");
}


function updateSnippetGrid() {
  const snippets = document.querySelectorAll(".box[data-snippet-id]");

  snippets.forEach(snippet => {
      const tagsContainer = snippet.querySelector(".tags-container");
      const snippetTags = Array.from(tagsContainer.getElementsByClassName("tag"))
                              .map(tagElement => tagElement.textContent.trim());

      // Check if the snippet has all selected tags
      // chnage it to the parent element
      const matchesAllTags = [...selectedTags].every(tag => snippetTags.includes(tag));

      if (matchesAllTags) {
        snippet.parentElement.style.display = "";
    } else {
        snippet.parentElement.style.display = "none";
    }
    
  });
}
