$(function () {
  const tagInput = $("#tag-input");
  const hiddenInput = $("#hidden-tags");
  const tagsContainer = $("#tags-container");
  const presetTags = $(".preset-tag");
  const dropdown = $("#tag-dropdown");
  const dropdownButton = $("#dropdown-button");
  let tags = [];

  /**
   * Hide tags that are already on post or do not match current input.
   */
  function updatePresetTags() {
    const search = tagInput.val().toUpperCase();
    let anyVisible = false;
    for (const presetTag of presetTags) {
      const tagText = presetTag.innerText;

      if (
        tags.includes(tagText) ||
        (search && !tagText.toUpperCase().includes(search))
      ) {
        $(presetTag).hide();
      } else {
        $(presetTag).show();
        anyVisible = true;
      }
    }

    if (!anyVisible) dropdown.removeClass("is-active");
  }

  /**
   * Update tags in form.
   */
  function tagsChanged() {
    hiddenInput.val(tags.join(","));
    updatePresetTags();
  }

  /**
   * Add a new tag to presets
   * @param {string} tagText
   */
  function addTag(tagText) {
    tagText = tagText.trim();

    // Apply canonical capitalization
    for (const presetTag of presetTags) {
      if (presetTag.innerText.toUpperCase() === tagText.toUpperCase()) {
        tagText = presetTag.innerText;
        break;
      }
    }

    if (tagText.length > 0 && !tags.includes(tagText)) {
      tags.push(tagText);

      // Create new tag element
      const tag = $(document.createElement("span"))
        .attr("id", tagText)
        .addClass("tag is-info is-medium mr-2")
        .text(tagText);

      const deleteBtn = $(document.createElement("button"))
        .addClass("delete is-small")
        .on("click", function () {
          tag.remove();
          tags = tags.filter((t) => t !== tagText);
          $(`#preset-${tagText}`).show();
          tagsChanged();
        });

      tag.append(deleteBtn).insertBefore(tagInput);
      tagInput.val("");

      tagsChanged();
    } else {
      tagInput.val("").attr("placeholder", "Already Tagged");
    }
  }

  tagInput.on("keydown", function (event) {
    if (event.key === "Enter" || event.key === ",") {
      event.preventDefault();
      addTag(tagInput.val());
      dropdown.removeClass("is-active");
    }
  });

  tagInput.on("input", function (event) {
    if (tagInput.val()) {
      dropdown.addClass("is-active");
    } else {
      tagInput.attr("placeholder", "Type tags and press Enter");
      dropdown.removeClass("is-active");
    }

    updatePresetTags();
  });

  for (const tag of presetTags) {
    $(tag).on("click", function () {
      addTag($(tag).text());
      dropdown.removeClass("is-active");
    });
  }

  dropdownButton.on("click", function (event) {
    event.preventDefault();
    event.stopPropagation();
    dropdown.toggleClass("is-active");
  });

  // $(document).on("click", function () {
  //   dropdown.removeClass("is-active");
  // });

  // Populate tag buttons on page load
  if ($("#edit").length) {
    const existingTags = JSON.parse($("#tags").text());
    existingTags.map((tag) => addTag(tag));
  }
});
