const searchInput = $("#search-input");
const resultsContainer = $("#search-results");
const descResultsContainer = $("#search-results-desc");
const snippetTemplate = $("#snippet-template");
const searchDelayMs = 250;

const title = $("#title");

let pendingSearchUrl = null;
let searchTimeout = null;

// Start search after the user stops typing
$(function () {
  searchInput.on("input", function () {
    if (searchTimeout !== null) {
      clearTimeout(searchTimeout);
    }
    searchTimeout = setTimeout(doSearch, searchDelayMs);
  });

  // Attach event listener for tag clicks
  $(document).on("click", ".search-tag", function (event) {
    event.preventDefault();
    const tag = $(this).data("tag");

    // Update search input with the clicked tag and trigger search
    searchInput.val(`:${tag}`);
    doSearch();
  });
});

/**
 * Start a search immediately, updating search results when complete.
 */
async function doSearch() {
  const query = searchInput.val();
  searchTimeout = null;

  // Don't search if input is empty
  if (!query.trim()) {
    resultsContainer.empty();
    descResultsContainer.empty();
    changeTitle();
    $("#search-type").removeClass("is-success");
    $("#search-icon").removeClass("fa-globe");
    $("#search-icon").addClass("fa-lock");
    $("#search-type").addClass("is-danger");
    $(".search-disclaimer").remove();
    $("#show-similar-snippets").hide();
    $("#snippets").show();
    $("#search-results-desc").hide();
    return;
  }

  $("#snippets").hide();
  searchInput.parent().addClass("is-loading");

  const searchUrl = `/search?q=${encodeURIComponent(query)}&format=json`;
  pendingSearchUrl = searchUrl;

  fetch(searchUrl, {
    headers: { "Search-Type": $("#search-icon").hasClass("fa-lock") ? false : true }
  })
    .then(response => response.json())
    .then(data => {
      if (searchUrl !== pendingSearchUrl) return;

      resultsContainer.empty();
      descResultsContainer.empty();
      $(".search-disclaimer").remove();

      let anyDescMatches = false;
      for (const snippet of data.results) {
        if (!anyDescMatches && snippet.is_description_match) {
          anyDescMatches = true;
          const disclaimer = $(document.createElement("h5"));
          disclaimer.addClass("subtitle mt-6 is-5 search-disclaimer");
          disclaimer.text("Similar public snippets");
          descResultsContainer.before(disclaimer);

          if ($("#search-icon").hasClass("fa-lock")) {
            $("#show-similar-snippets").show();
            $("#search-results-desc").hide();
          } else {
            $("#show-similar-snippets").hide();
            $("#search-results-desc").show();
            disclaimer.hide();
          }
        }

        createSnippet(snippet).appendTo(
          snippet.is_description_match ? descResultsContainer : resultsContainer
        );
      }

      if (data.results.length === 0) {
        resultsContainer.text("No snippets found.");
      }

      attachTagListeners();
    })
    .catch(error => {
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

/**
 * Creates a snippet card from the given info.
 */
function createSnippet(snippet) {

  const card = snippetTemplate.clone();
  card.removeAttr("id");
  card.attr("data-snippet-id", snippet.id);
  card.attr("data-code", snippet.code);
  card.find(".snippet-card-name").text(snippet.name);

  // Remove irrelevant public/private labels
  if (snippet.is_public) card.find(".snippet-card-private").remove();

  const editButton = card.find(".snippet-card-edit");
  const deleteButton = card.find(".snippet-card-delete");
  if (!snippet.editable) {
    editButton.remove();
    deleteButton.remove();
  }

  // Update description
  card.find(".snippet-card-summary").text((snippet.description || "").trim());

  // Add tags
  const tagList = card.find(".snippet-card-tags");
  tagList.empty();
  for (const tagName of snippet.tags) {
    const tagElem = $(document.createElement("a"));
    tagElem.addClass("tag is-info search-tag");
    tagElem.attr("href", "#");
    tagElem.attr("data-tag", tagName);
    tagElem.text(tagName);
    tagElem.appendTo(tagList);
  }

  return card;
}

/**
 * Ensures event listeners are attached to dynamically created tags.
 */
function attachTagListeners() {
  $(document).off("click", ".search-tag").on("click", ".search-tag", function (event) {
    event.preventDefault();
    const tag = $(this).data("tag");
    searchInput.val(`:${tag}`);
    doSearch();
  });
}

// Helper Functions
addEventListener("keydown", function (event) {
  if (event.ctrlKey && event.key === "k") {
    event.preventDefault();
    $("#search-input").focus();
  } else if (event.key === "Tab" && searchInput.val()) {
    event.preventDefault();
    toggleSearch();
    changeTitle();
  }
});

function changeTitle() {
  if ($("#search-input").val().trim()) {
    if ($("#search-icon").hasClass("fa-globe")) title.text("Global Search");
    else title.text("Local Search");
    doSearch();
  } else title.text("Your Snippets");
}

function toggleSearch() {
  if ($("#search-icon").hasClass("fa-lock")) {
    $("#search-icon").removeClass("fa-lock");
    $("#search-type").removeClass("is-danger");
    $("#search-type").addClass("is-success");
    $("#search-icon").addClass("fa-globe");
  } else {
    $("#search-type").removeClass("is-success");
    $("#search-icon").removeClass("fa-globe");
    $("#search-icon").addClass("fa-lock");
    $("#search-type").addClass("is-danger");
  }
  doSearch();
  changeTitle();
}

$(function () {
  changeTitle();
});
