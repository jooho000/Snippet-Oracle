$(function () {
  const tagInput = document.getElementById("tag-input");
  const tagsContainer = document.getElementById("tags-container");
  const hiddenTags = document.getElementById("hidden-tags");
  const presetTags = document.querySelectorAll(".preset-tag");
  const dropdown = document.getElementById("tag-dropdown");
  const dropdownButton = document.getElementById("dropdown-button");
  let tags = [];

  function addTag(tagText) {
    tagText = tagText.trim();
    if (tagText.length > 0 && !tags.includes(tagText)) {
      tags.push(tagText);

      let tag = document.createElement("span");
      tag.classList.add("tag", "is-info", "is-medium", "mr-2");
      tag.textContent = tagText;

      let deleteBtn = document.createElement("button");
      deleteBtn.className = "delete is-small";
      deleteBtn.addEventListener("click", function () {
        tag.remove();
        tags = tags.filter((t) => t !== tagText);
        hiddenTags.value = tags.join(",");
      });

      tag.appendChild(deleteBtn);
      tagsContainer.insertBefore(tag, tagInput);
      tagInput.innerText = "";
      hiddenTags.value = tags.join(",");
    }
  }

  tagInput.addEventListener("keydown", function (event) {
    if (event.key === "Enter" || event.key === ",") {
      event.preventDefault();
      addTag(tagInput.innerText);
    }
  });

  presetTags.forEach(function (tag) {
    tag.addEventListener("click", function (event) {
      event.preventDefault();
      addTag(tag.innerText);
    });
  });

  dropdownButton.addEventListener("click", function (event) {
    event.preventDefault();
    event.stopPropagation();
    dropdown.classList.toggle("is-active");
  });

  document.addEventListener("click", function (event) {
    if (
      !dropdown.contains(event.target) &&
      !dropdownButton.contains(event.target)
    ) {
      dropdown.classList.remove("is-active");
    }
  });

  if (document.getElementById("edit")) {
    const existingTags = JSON.parse(
      document.getElementById("tags").textContent
    );
    existingTags.forEach((tag) => addTag(tag));
  }
});
