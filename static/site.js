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
  const tags = card.find(".snippet-card-tags");
  const modal = $("#snippet-modal");

  // Close currently opened snippet card
  closeSnippet();

  // Code block
  const codeDiv = $(document.createElement("div")).insertBefore(tags);
  const pre = $(document.createElement("pre")).appendTo(codeDiv);
  const code = $(document.createElement("code")).appendTo(pre);
  codeDiv.addClass("snippet-card-code mt-3");
  code.text(card.data("code"));
  hljs.highlightElement(code[0]);

  // Description
  const desc = $(document.createElement("p")).appendTo(codeDiv);
  desc.addClass("mt-4 mb-4");
  desc.text(card.data("description") || "No description available.");
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
 * @param {JQuery | undefined} card 
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

async function confirmDelete(snippetID) {
  if (window.confirm("Confirm Deletion")) {
    await fetch(`/deleteSnippet/${snippetID}`);
    window.location.reload();
  }
}
