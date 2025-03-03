const searchInput = $("#search-input");
const allResults = $("#results");
const snippetTemplate = $("#snippet-template");
const userCardTemplate = $("#user-card-template");
const title = $("#title");
const searchDelayMs = 250;

// Containers for search results
const tagResults = $("#results-tags");
const tagCount = $("#results-tags-count");
const userResults = $("#results-users");
const userCount = $("#results-users-count");
const snippetResults = $("#results-snippets");
const snippetCount = $("#results-snippets-count");
const similarResults = $("#results-similar");
const similarCount = $("#results-similar-count");
const sharedResults = $("#results-shared");
const sharedCount = $("#results-shared-count");

let popValues;

let pendingSearchUrl = null;
let searchTimeout = null;

toggleResults("results-tags", true);
toggleResults("results-users", true);
toggleResults("results-snippets", true);
toggleResults("results-similar", false);
toggleResults("results-shared", true);

$(function () {
  // Start search after the user stops typing
  searchInput.on("input", function () {
    if (searchTimeout !== null) {
      clearTimeout(searchTimeout);
    }
    searchTimeout = setTimeout(doSearch, searchDelayMs);
  });
});

$(async function () {
  try {
    const searchUrl = new URL(script_root + "/defaultView", location.href);
    popValues = await fetch(searchUrl).then((response) => response.json());
    populateResults(popValues);
    popText();
  } catch (error) {
    console.error("Error fetching search results:", error);
    snippetResults.text("Error occurred while searching.");
  }
});

$(function () {
  attachTagListeners(); // Ensure initial tags are clickable

  // Start a search if present in URL
  const query = new URLSearchParams(window.location.search).get("q");
  if (query) {
    // Hide similar results when linked to a specific tag
    if (query.includes("+") || query.includes("-") || query.includes("@"))
      toggleResults("results-similar", false);

    $("#search-input").val(query);
    doSearch();
  }
});

$(".results-section > .level").on("click", function (event) {
  const id = $(event.currentTarget).parent().find(".results-container")[0].id;
  toggleResults(id);
});

/**
 * Start a search immediately, updating search results when complete.
 */
async function doSearch() {
  const query = searchInput.val();
  searchTimeout = null;

  // Don't search if input is empty
  if (!query.trim()) {
    populateResults(popValues);
    history.pushState(null, "", "/");
    popText();
    return;
  }

  searchInput.parent().addClass("is-loading");

  // Send the query to the server via AJAX (using fetch)
  const searchUrl = new URL(script_root + "/search", location.href);
  searchUrl.searchParams.append("q", query);
  searchUrl.searchParams.append("public", 1);
  pendingSearchUrl = searchUrl;

  //update url to match current search
  const newUrl = new URL(script_root + "/", location.href);
  newUrl.searchParams.append("q", query);
  newUrl.searchParams.append("public", 1);
  history.pushState(null, "", newUrl);

  try {
    const json = await fetch(searchUrl).then((response) => response.json());
    allResults.show();

    // Ignore results if another search is pending
    if (searchUrl !== pendingSearchUrl) return;

    populateResults(json);

    attachTagListeners(); // Ensure tags are clickable after search results update
  } catch (error) {
    console.error("Error fetching search results:", error);
    snippetResults.text("Error occurred while searching.");
  }

  if (searchUrl === pendingSearchUrl) {
    pendingSearchUrl = null;
    searchInput.parent().removeClass("is-loading");
  }
}

/**
 * Creates a tag button from the given text.
 */
function createTag(tag) {
  const elem = $(document.createElement("a"));
  elem.text(tag);
  elem.addClass("tag is-info searhc-tag");

  // Update link
  const url = new URL(script_root, location.href);
  url.searchParams.append("q", "+" + tag);
  elem.attr("href", url.href);

  return elem;
}

/**
 * Creates a User Card.
 * @param {*} user name, profile pic
 * @returns {*} returns dom user card
 */
function createUserCard(user) {
  const elem = userCardTemplate.clone();
  const pic = elem.find(".user-card-picture");
  const name = elem.find(".user-card-name");

  elem.removeAttr("id");
  elem.on("click", function () {
    location.href = new URL(
      script_root + "/profile/" + user.name,
      location.href
    ).href;
  });

  name.text(user.name);
  if (user.profile_picture) {
    pic.attr(
      "src",
      script_root + "/static/profile_pictures/" + user.profile_picture
    );
  }

  return elem;
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
 * Show or hide a category of search results.
 * @param {string} name
 */
function toggleResults(id, visible) {
  const container = $("#" + id).closest(".results-collapse-wrapper");
  const showAll = container
    .closest(".results-section")
    .find(".results-show-all");

  if (visible == undefined) {
    visible = container.is(":hidden");
  }

  if (visible) {
    container.show();
    showAll.text("hide");
  } else {
    container.hide();
    showAll.text("show");
  }
}

/**
 * Ensures event listeners are attached to dynamically created tags.
 */
function attachTagListeners() {
  $(".search-tag")
    .off("click")
    .on("click", function (event) {
      event.preventDefault();
      const tag = $(this).text().trim();
      window.location.href = "/?q=" + encodeURIComponent("+" + tag);
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

function toggleSearch() {
  $("#search-icon").toggleClass("fa-lock fa-globe");
  $("#search-type").toggleClass("is-danger is-success");
  doSearch();
  changeTitle();
}

/**
 * Populates Search Categories w/ Results
 * @param {*} json Takes in search results
 */
function populateResults(json) {
  $(".results-container").empty();

  // Tag text matches
  tagCount.text(json.tags.length);
  for (const tag of json.tags) createTag(tag).appendTo(tagResults);
  if (!json.tags.length) tagResults.hide();
  else tagResults.show();

  // Username matches
  userCount.text(json.users.length);
  for (const user of json.users) createUserCard(user).appendTo(userResults);
  if (!json.users.length) userResults.hide();
  else userResults.show();

  // Name match snippet cards
  snippetCount.text(json.snippets.length);
  for (const snippet of json.snippets)
    createSnippet(snippet).appendTo(snippetResults);
  if (!json.snippets.length) snippetResults.hide();
  else snippetResults.show();

  // Similar description snippet cards
  if (json.similar && json.similar.length) {
    similarResults.show();
    similarCount.text(json.similar.length);
    for (const snippet of json.similar)
      createSnippet(snippet).appendTo(similarResults);
  } else {
    similarResults.hide();
  }

  if (json.shared && json.shared.length) {
    sharedResults.show();
    sharedResults.text(json.shared.length);
    for (const snippet of json.shared)
      createSnippet(snippet).appendTo(sharedResults);
  } else sharedResults.hide();
}

/**
 * Change Default Category Display
 */
function popText() {
  tagCount.text("Popular Tags");
  userCount.text("Most Liked Users");
  snippetCount.text("Most Liked Snippets");
}
