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
      // Ignore results if another search is pending
      if (searchUrl !== pendingSearchUrl) return;

      resultsContainer.empty();
      descResultsContainer.empty();
      $(".search-disclaimer").remove();

      // If there are results, display them as snippet cards
      let anyDescMatches = false;
      let seenSnippetIds = new Set();

      for (const snippet of data.results) {
        if (seenSnippetIds.has(snippet.id)) continue;

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

        seenSnippetIds.add(snippet.id);

        // Add snippet to results
        createSnippet(snippet).appendTo(
          snippet.is_description_match ? descResultsContainer : resultsContainer
        );
      }

      if (data.results.length === 0) {
        resultsContainer.text("No snippets found.");
      }

      attachTagListeners(); // Ensure tags are clickable after search results update
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
 */
function createSnippet(snippet) {
  const card = snippetTemplate.clone();

  // Update attributes
  card.removeAttr("id");
  card.attr("data-snippet-id", snippet.id);
  card.attr("data-code", snippet.code);
  card.find(".snippet-card-name").text(snippet.name);

  if (snippet.author && snippet.author.name) {
    const profileContainer = $(`
      <div class="is-flex is-align-items-center">
        <figure class="image is-32x32">
          <a href="/profile/${snippet.author.name}">
            <img class="is-rounded" 
                 src="/static/profile_pictures/${snippet.author.profile_picture}"
                 alt="${snippet.author.name}'s profile picture">
          </a>
        </figure>
        <p class="ml-2 title is-6">
          <a href="/profile/${snippet.author.name}" 
             class="white-icon has-text-light has-text-weight-medium">
            ${snippet.author.name}
          </a>
        </p>
      </div>
    `);

    card.find(".snippet-card-name").after(profileContainer);
  }

  // Remove irrelevant public/private labels
  if (snippet.is_public) card.find(".snippet-card-private").remove();

  // Remove edit/delete links if not the owner
  const editButton = card.find(".snippet-card-edit");
  const deleteButton = card.find(".snippet-card-delete");
  if (snippet.user_id !== current_user_id) {
    editButton.remove();
    deleteButton.remove();
  }

  // Update description
  card.find(".snippet-card-summary").text((snippet.description || "").trim());

  // Add tags with clickable links
  const tagList = card.find(".snippet-card-tags");
  tagList.empty();
  for (const tagName of snippet.tags) {
    const tagElem = $(document.createElement("a"));
    tagElem.addClass("tag is-info search-tag");
    tagElem.attr("href", "/?q=:" + encodeURIComponent(tagName));
    tagElem.text(tagName);
    tagElem.appendTo(tagList);
  }

  // Update likes
  const likesButton = card.find(".snippet-card-like-button");
  const likes = card.find(".snippet-card-likes");
  if (snippet.is_liked) likesButton.addClass("has-text-link");
  likes.text(snippet.likes);

  return card;
}

/**
 * Ensures event listeners are attached to dynamically created tags.
 */
function attachTagListeners() {
  $(".search-tag").off("click").on("click", function (event) {
    event.preventDefault();
    const tag = $(this).text().trim();
    window.location.href = "/?q=:" + encodeURIComponent(tag);
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
    const matchesAllTags = [...selectedTags].every((tag) =>
      snippetTags.includes(tag)
    );

    snippet.parentElement.style.display = matchesAllTags ? "" : "none";
  });
}

// Helper functions
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
    title.text($("#search-icon").hasClass("fa-globe") ? "Global Search" : "Local Search");
    doSearch();
  } else title.text("Your Snippets");
}

function toggleSearch() {
  $("#search-icon").toggleClass("fa-lock fa-globe");
  $("#search-type").toggleClass("is-danger is-success");
  doSearch();
  changeTitle();
}

$(document).ready(function () {
  attachTagListeners(); // Ensure initial tags are clickable

  const query = new URLSearchParams(window.location.search).get("q");
  if (query) {
    $("#search-input").val(query);  
    doSearch();  
  }
});
