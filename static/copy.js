// static/copy.js

document.addEventListener("DOMContentLoaded", function() {
    // Get the copy button and snippet code element
    const copyButton = document.getElementById("copyButton");
    const snippetCode = document.getElementById("snippet-code");
    
    copyButton.addEventListener("click", function() {
        const textarea = document.createElement("textarea");
        textarea.value = snippetCode.innerText;  // Get the snippet code text
        document.body.appendChild(textarea);

        // Select and copy the content
        textarea.select();
        document.execCommand("copy");

        document.body.removeChild(textarea);

        alert("Snippet code copied to clipboard!");
    });
});