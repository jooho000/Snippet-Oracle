/**
 * Toggles the contents of a snippet.
 * @param {JQuery} card
 */
function toggleSnippet(card) {
  let codeDiv = card.children(".snippet-card-code");
  const icon = card.find(".snippet-card-arrow");
  const summary = card.find(".snippet-card-summary");

  if (!codeDiv.length) {
    // Create snippet content dynamically
    codeDiv = $(document.createElement("div")).appendTo(card);
    const pre = $(document.createElement("pre")).appendTo(codeDiv);
    const code = $(document.createElement("code")).appendTo(pre);
    const desc = $(document.createElement("p")).appendTo(codeDiv);
    desc.text(card.data("description") || "No description available.");
    const strong = $(document.createElement("strong")).prependTo(desc);

    codeDiv.addClass("snippet-card-code mt-3");

    code.text(card.data("code"));
    strong.text("Description: ");
    hljs.highlightElement(pre[0]);

    // Update icon to up arrow
    icon.addClass("snippet-card-arrow-open");
    summary.addClass("is-invisible");
  } else {
    // Destroy snippet content dynamically
    codeDiv.remove();
    icon.removeClass("snippet-card-arrow-open");
    summary.removeClass("is-invisible");
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
