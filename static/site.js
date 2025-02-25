/**
 * Toggles the contents of a snippet.
 * @param {JQuery} card
 */
function toggleSnippet(card) {
  const codeDiv = card.find(".snippet-card-code");

  if (!codeDiv.length) {
    openSnippet(card);
  } else {
    closeSnippet();
  }
}

/**
 * Show the contents of a snippet card.
 * @param {JQuery} card
 */
function openSnippet(card) {
  const summary = card.find(".snippet-card-summary");
  const header = card.find(".snippet-card-header");
  const modal = $("#snippet-modal");

  // Close currently opened snippet card
  closeSnippet();

  // Code block
  const codeDiv = $(document.createElement("div")).insertAfter(header);
  const pre = $(document.createElement("pre")).appendTo(codeDiv);
  const code = $(document.createElement("code")).appendTo(pre);
  codeDiv.addClass("snippet-card-code mt-3");
  code.text(card.data("code"));
  hljs.highlightElement(code[0]);

  // Description
  const desc = $(document.createElement("p")).appendTo(codeDiv);
  desc.addClass("mt-4 mb-4");
  desc.text(summary.text() || "No description available.");
  const strong = $(document.createElement("strong")).prependTo(desc);
  strong.text("Description: ");

  // Update style
  card.addClass("snippet-card-open");
  summary.addClass("is-hidden");
  modal.addClass("is-active");
}

/**
 * Close the current open snippet card.
 * No action is taken if there is not an open card.
 */
function closeSnippet() {
  const card = $(".snippet-card-open");
  card.removeClass("snippet-card-open");
  card.find(".snippet-card-code").remove();
  card.find(".snippet-card-summary").removeClass("is-hidden");
  $("#snippet-modal").removeClass("is-active");
}

/**
 * Copies the snippet's code to clipboard.
 * @param {JQuery} card
 */
function copySnippet(card) {
  navigator.clipboard
    .writeText(card.data("code"))
    .then(() => {
      alert("Code snippet copied to clipboard!");
    })
    .catch((err) => {
      console.error("Failed to copy text: ", err);
    });
}

/**
 * Likes or unlikes a snippet.
 * @param {JQuery} card
 */
async function likeSnippet(card) {
  const id = card.data("snippet-id");
  const button = card.find(".snippet-card-like-button");
  const likes = card.find(".snippet-card-likes");
  const wasLiked = button.hasClass("has-text-link");

  // Update text and color locally
  const allCards = $(".snippet-card").filter((i, card) => $(card).data("snippet-id") == id);
  const allButtons = allCards.find(".snippet-card-like-button");
  allCards.find(".snippet-card-likes").text(parseInt(likes.text()) + (wasLiked ? -1 : 1));
  if (wasLiked) allButtons.removeClass("has-text-link");
  else allButtons.addClass("has-text-link");

  // Update likes on server
  const options = {
    method: wasLiked ? "DELETE" : "POST",
  };

  fetch(script_root + `/likes/${id}`, options).catch(console.error);
}

/**
 * Navigates to the view snippet page.
 * @param {JQuery} card
 */
function goToSnippet(card) {
  const id = card.data("snippet-id");
  window.location = script_root + `/snippet/${id}`;
}

/**
 * Navigates to the edit snippet page.
 * @param {JQuery} card
 */
function editSnippet(card) {
  const id = card.data("snippet-id");
  window.location = script_root + `/editSnippet/${id}`;
}

/**
 * Bring up a confirm dialogue for snippet deletion.
 * @param {JQuery} card
 */
async function confirmDeleteSnippet(card) {
  const title = card.find(".snippet-card-name").text();
  const message = 'Are you sure you want to delete "' + title + '"?';
  if (window.confirm(message)) {
    await fetch(`/deleteSnippet/${snippetID}`);
    window.location.reload();
  }
}

$(function () {
  // Apply code highlighting
  hljs.highlightAll();

  // Manage dark and light themes
  const themeButton = $("#theme-button");
  const themeIcon = themeButton.children("span");
  let theme = null;

  function setTheme(newTheme) {
    theme = newTheme;
    sessionStorage.setItem("theme", theme);
    $("html").removeClass("theme-dark theme-light");
    if (theme !== null) $("html").addClass("theme-" + theme);

    themeIcon.removeClass("fa-sun fa-moon fa-lightbulb");
    switch (theme) {
      case "dark":
        themeIcon.addClass("fa-moon");
        break;
      case "light":
        themeIcon.addClass("fa-sun");
        break;
      default:
        themeIcon.addClass("fa-lightbulb");
        break;
    }
  }

  setTheme(sessionStorage.getItem("theme"));

  themeButton.on("click", (_) => {
    switch (theme) {
      case "dark":
        setTheme("light");
        break;
      case "light":
        setTheme(null);
        break;
      default:
        setTheme("dark");
        break;
    }
  });
});
