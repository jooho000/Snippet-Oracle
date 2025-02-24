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
});

/**
 * Start a search immediately, updating search results when complete.
 * Results are ignored if another search is started before this search completes.
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
  // Show loading spinner
  searchInput.parent().addClass("is-loading");

  // Send the query to the server via AJAX (using fetch)
  const searchUrl = `/search?q=${encodeURIComponent(query)}`;
  pendingSearchUrl = searchUrl;

  fetch(searchUrl, {
    headers: {
      "Search-Type": $("#search-icon").hasClass("fa-lock") ? false : true,
    },
  })
    .then((response) => response.json())
    .then((data) => {
      // Ignore results if another
      if (searchUrl !== pendingSearchUrl) return;

      resultsContainer.empty(); // Clear previous results
      descResultsContainer.empty();
      $(".search-disclaimer").remove();

      // If there are results, display them as buttons
      let anyDescMatches = false;
      for (const snippet of data.results) {
        // Add a disclaimer that these are only description matches
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

        // Add a snippet card to search results
        createSnippet(snippet).appendTo(
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

/**
 * Creates a snippet card from the given info.
 * @param {{id: number, user_id: number, name: string, description: string, code: string, tags: Array<string>}} snippet
 */
function createSnippet(snippet) {
  const elem = snippetTemplate.clone();
  const viewLink = elem.find(".snippet-card-link");

  // Update attributes
  elem.removeAttr("id");
  elem.data("code", snippet.code);
  elem.data("description", snippet.description);
  elem.find(".snippet-card-name").text(snippet.name);
  viewLink.attr("href", viewLink.attr("href").replace("-1", snippet.id));

  // Remove whichever public/private label isn't relevant
  if (snippet.is_public) elem.find(".snippet-card-private").remove();

  // Update edit/delete links, or remove them if not the owner
  const editButton = elem.find(".snippet-card-edit");
  const deleteButton = elem.find(".snippet-card-delete");
  if (snippet.user_id !== current_user_id) {
    editButton.remove();
    deleteButton.remove();
  } else {
    editButton.attr("href", editButton.attr("href").replace("-1", snippet.id));
    deleteButton.attr(
      "href",
      deleteButton.attr("href").replace("-1", snippet.id)
    );
  }

  // Update summary
  const summary = (snippet.description || "").trim();
  elem.find(".snippet-card-summary").text(summary);

  // Add tags
  const tagList = elem.find(".snippet-card-tags");
  for (const tagName of snippet.tags) {
    const tagElem = $(document.createElement("span"));
    tagElem.addClass("tag is-info");
    tagElem.text(tagName);
    tagElem.appendTo(tagList);
  }

  // Move spacer tag to the end of list
  const dummyTag = tagList.find(".is-invisible");
  dummyTag.remove().appendTo(tagList);

  return elem;
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

//helper funcs
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
