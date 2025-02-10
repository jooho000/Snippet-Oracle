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
