// static/edit.js

document.addEventListener("DOMContentLoaded", function() {
    // Get the edit button and url element
    const editButton = document.getElementById("editButton");
    editButton.addEventListener("click", function() {
        let curLoc = window.location.href;
        let newLoc = curLoc.replace("snippet", "editSnippet");
        window.location.assign(newLoc);
    });
});
