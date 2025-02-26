$(function () {
  const tagInput = $("#tag-input");
  const tagsContainer = $("#tags-container");
  const presetTags = $(".preset-tag");
  const dropdown = $("#tag-dropdown");
  const dropdownButton = $("#dropdown-button");
  let tags = [];

  function addTag(tagText) {
    tagText = tagText.trim();

    if (tagText.length > 0 && !tags.includes(tagText)) {
      tags.push(tagText);

      const tag = $(document.createElement("span"))
        .attr("id", tagText)
        .addClass("tag is-info is-medium mr-2")
        .text(tagText);

      const deleteBtn = $(document.createElement("button"))
        .addClass("delete is-small")
        .click(function () {
          tag.remove();
          tags = tags.filter((t) => t !== tagText);
          $(`#preset-${tagText}`).show();
        });

      tag.append(deleteBtn).insertBefore(tagInput);
      tagInput.val("");
    } else tagInput.val("").attr("placeholder", "Already Tagged");
  }

  tagInput.on({
    keydown: function (event) {
      if (event.key === "Enter" || event.key === ",") {
        event.preventDefault();
        addTag(tagInput.val());
      }
      else if (!tagInput.val()){
        tagInput.attr("placeholder", "Type tags and press Enter");
      }tags
    },
  });

  for (const tag of presetTags){
    $(tag).click(function () {
      addTag($(tag).text());
      $(tag).hide()
    });
  }

  dropdownButton.click(function (event) {
    event.preventDefault();
    event.stopPropagation();
    dropdown.toggleClass("is-active");
  });

  $(document).click(function () {
    dropdown.removeClass("is-active");
  });

  if (document.getElementById("edit")) {
    const existingTags = JSON.parse(
      document.getElementById("tags").textContent
    );
    existingTags.forEach((tag) => addTag(tag));
  }

  if ($("#edit").length) {
    const existingTags = JSON.parse($("#tags").text());
    existingTags.map((tag) => addTag(tag));
  }
});
