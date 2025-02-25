$(() => {
  // Get the copy button and snippet code element
  const copyButton = $("#copyButton");
  const snippetCode = $("#snippet-code");

  copyButton.on("click", () => {
    const textarea = document.createElement("textarea");
    textarea.value = snippetCode.innerText; // Get the snippet code text
    document.body.appendChild(textarea);

    // Select and copy the content
    textarea.select();
    document.execCommand("copy");

    document.body.removeChild(textarea);

    alert("Snippet code copied to clipboard!");
  });
});
