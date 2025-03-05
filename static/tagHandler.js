$(function () {
  const MAX_TAGS = 15;
  const tagInput = $("#tag-input");
  const hiddenInput = $("#hidden-tags");
  const tagsContainer = $("#tags-container");
  const presetTags = $(".preset-tag");
  const dropdown = $("#tag-dropdown");
  const dropdownButton = $("#dropdown-button");
  const tagCounter = $("#tag-count");
  const charCounter = $("#tag-char-count");
  let tags = [];

  /**
   * Update the tag count display
   */
  function updateTagCount() {
    if (tagCounter.length) {
      tagCounter.text(`${tags.length}/${MAX_TAGS}`);
    }

    // Disable input if the tag limit is reached
    if (tags.length >= MAX_TAGS) {
      tagInput.prop("disabled", true).attr("placeholder", "Tag limit reached");
    } else {
      tagInput.prop("disabled", false).attr("placeholder", "Type tags and press Enter");
    }
  }

  /**
   * Reset tag character counter
   */
  function resetTagCharCounter() {
    if (charCounter.length) {
      charCounter.text(`0/20`);
    }
  }

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
    updateTagCount();
    updatePresetTags();
  }

  /**
   * Add a new tag to presets
   * @param {string} tagText
   */
  function addTag(tagText) {
    tagText = tagText.trim();

    if (tagText === "") return;

    if (tags.length >= MAX_TAGS) {
      alert(`You can only add up to ${MAX_TAGS} tags.`);
      return;
    }

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

      resetTagCharCounter();

      tagsChanged();
    } else {
      tagInput.val("").attr("placeholder", "Already Tagged");
    }
  }

  tagInput.on("keydown", function (event) {
    if ((event.key === "Enter" || event.key === ",") && tags.length < MAX_TAGS) {
      event.preventDefault();
      if (tagInput.val().trim() === "") {
        tagInput.attr("placeholder", "Cannot add an empty tag");
        return;
      }

      addTag(tagInput.val());
      dropdown.removeClass("is-active");
    }
  });

  tagInput.on("input", function () {
    if (tagInput.val()) {
      dropdown.addClass("is-active");
    } else {
      tagInput.attr("placeholder", "Type tags and press Enter");
      dropdown.removeClass("is-active");
      resetTagCharCounter();
    }

    updatePresetTags();
  });

  for (const tag of presetTags) {
    $(tag).on("click", function () {
      if (tags.length < MAX_TAGS) {
        addTag($(tag).text());
        dropdown.removeClass("is-active");
      }
    });
  }

  dropdownButton.on("click", function (event) {
    event.preventDefault();
    event.stopPropagation();
    dropdown.toggleClass("is-active");
  });

  updateTagCount();
  resetTagCharCounter();

  tagInput.closest("form").on("keydown", function (event) {
    if (event.key === "Enter" && tagInput.is(":focus")) {
      event.preventDefault();
    }
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
