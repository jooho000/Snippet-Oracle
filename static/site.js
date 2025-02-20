/**
 * Toggles the contents of a snippet.
 * @param {JQuery} card
 */
function toggleSnippet(card) {
  let codeDiv = card.find(".snippet-card-code");
  const icon = card.find(".snippet-card-arrow");
  const summary = card.find(".snippet-card-summary");
  const tags = card.find(".snippet-card-tags");

  if (!codeDiv.length) {
    // Create snippet content dynamically
    codeDiv = $(document.createElement("div")).insertBefore(tags);
    const code = $(document.createElement("pre")).appendTo(codeDiv);
    const desc = $(document.createElement("p")).appendTo(codeDiv);
    desc.text(card.data("description") || "No description available.");
    const strong = $(document.createElement("strong")).prependTo(desc);

    codeDiv.addClass("snippet-card-code mt-3");

    desc.addClass("mt-4 mb-4");
    code.text(card.data("code"));
    strong.text("Description: ");
    hljs.highlightElement(code[0]);

    // Update icon to up arrow
    icon.addClass("snippet-card-arrow-open");
    summary.addClass("is-hidden");
  } else {
    // Destroy snippet content dynamically
    codeDiv.remove();
    icon.removeClass("snippet-card-arrow-open");
    summary.removeClass("is-hidden");
  }
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
    await fetch (`/deleteSnippet/${snippetID}`);
    window.location.reload();
  }
}
