// static/cancel.js

document.addEventListener("DOMContentLoaded", function() {
    // Get the cancel button
    const editButton = document.getElementById("cancel");
    editButton.addEventListener("click", function() {
        console.log(window.location);
        history.back();
        console.log(window.location);
    });
});
