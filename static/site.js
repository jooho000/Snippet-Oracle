/**
 * Toggles the contents of a snippet.
 * @param {JQuery} card
 */
function toggleSnippet(card) {
  let code = card.children(".snippet-card-code");
  const icon = card.find(".snippet-card-arrow");
  const summary = card.find(".snippet-card-summary");

  if (!code.length) {
    // Create snippet content dynamically
    code = $(document.createElement("div"));
    code.addClass("snippet-card-code mt-3");

    // Add snippet content and description (no Copy button)
    const content = card.data("code");
    const desc = card.data("description") || "No description available.";
    code.html(`
              <pre class="code-snippet mb-4">${content}</pre>
              <p><strong>Description:</strong> ${desc}</p>
          `);
    card.append(code);

    // Update icon to up arrow
    icon.addClass("snippet-card-arrow-open");
    summary.addClass("is-invisible");
  } else {
    // Destroy snippet content dynamically
    code.remove();
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

// Manage dark and light themes
$(function () {
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
