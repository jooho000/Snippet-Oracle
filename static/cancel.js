// static/cancel.js

document.addEventListener("DOMContentLoaded", function () {
  // Get the cancel button
  const editButton = document.getElementById("cancel");
  editButton.addEventListener("click", function () {
    history.back();
  });
});
