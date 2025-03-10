$(function () {
  // Get all necessary elements
  const visibilityToggle = document.getElementById("visibilityToggle");
  const visibilityIcon = document.getElementById("visibilityIcon");
  const permittedUsersField = document.getElementById("permittedUsersField");
  const toggleText = document.getElementById("toggleText");
  const isPublicField = document.getElementById("isPublic");

  const userSearch = document.getElementById("userSearch");
  const userSelection = document.getElementById("user-selection");
  const selectedUsersContainer = document.getElementById("selected-users");
  const form = document.querySelector("form");

  // Load user data from Flask JSON
  const users = JSON.parse(document.getElementById("user-data").textContent);
  let selectedUsers = new Set(); // Store selected users

  if (document.getElementById("edit")) {
    const existingUsers = JSON.parse(
      document.getElementById("shared-users").textContent
    );
    existingUsers.forEach((user) => selectedUsers.add(user));
  }

  function updateVisibility() {
    if (isPublicField.value === "1") {
      // Public
      permittedUsersField.style.display = "none";
      toggleText.innerText = "Public";
      visibilityToggle.classList.remove("is-light");
      visibilityToggle.classList.add("is-success");
      visibilityIcon.classList.remove("fa-lock");
      visibilityIcon.classList.add("fa-globe");
    } else {
      // Private
      permittedUsersField.style.display = "block";
      toggleText.innerText = "Private";
      visibilityToggle.classList.remove("is-success");
      visibilityToggle.classList.add("is-light");
      visibilityIcon.classList.remove("fa-globe");
      visibilityIcon.classList.add("fa-lock");
    }
  }

  // Toggle button click event
  visibilityToggle.addEventListener("click", function () {
    isPublicField.value = isPublicField.value === "1" ? "0" : "1";
    updateVisibility();
  });

  updateVisibility(); // Ensure the UI reflects the correct initial state

  /**
   * Updates the selected users container
   */
  function updateSelectedUsers() {
    selectedUsersContainer.innerHTML = ""; // Clear old selected users

    // Remove old hidden inputs
    document
      .querySelectorAll(".hidden-user-input")
      .forEach((input) => input.remove());
    selectedUsers.forEach((user) => {
      const tag = document.createElement("span");
      tag.classList.add("tag", "is-info", "is-medium", "mr-2");
      tag.textContent = user.name;

      // Add remove button
      const removeBtn = document.createElement("button");
      removeBtn.classList.add("delete", "is-small");
      removeBtn.addEventListener("click", function () {
        selectedUsers.delete(user);
        updateSelectedUsers();
        renderUserList(userSearch.value.trim());
      });

      tag.appendChild(removeBtn);
      selectedUsersContainer.appendChild(tag);

      // Create hidden input to send selected users
      const hiddenInput = document.createElement("input");
      hiddenInput.type = "hidden";
      hiddenInput.name = "permitted_users[]"; // Ensuring multiple values are sent
      hiddenInput.value = user.id;
      hiddenInput.classList.add("hidden-user-input");
      form.appendChild(hiddenInput);
    });
  }

  /**
   * Renders the user list based on search input
   */
  function renderUserList(filter = "") {
    userSelection.innerHTML = ""; // Clear previous results
    updateCharacterCount('userSearch', 'userSearch-char-count');
    
    if (filter.length === 0) {
      userSelection.style.display = "none"; // Hide list if search is empty
      return;
    }

    userSelection.style.display = "block"; // Show list when searching

    const filteredUsers = users.filter(
      (user) =>
        user.name.toLowerCase().includes(filter.toLowerCase()) &&
        !Array.from(selectedUsers).some((selected) => selected.id === user.id)
    );

    if (filteredUsers.length === 0) {
      userSelection.innerHTML =
        "<p class='has-text-centered has-text-grey'>No users found</p>";
      return;
    }

    filteredUsers.forEach((user) => {
      const label = document.createElement("div");
      label.classList.add(
        "box",
        "is-clickable",
        "user-checkbox",
        "p-2",
        "mb-2"
      );
      label.textContent = user.name;

      label.addEventListener("click", function () {
        selectedUsers.add(user);
        updateSelectedUsers();
        userSearch.value = "";
        renderUserList();
      });

      userSelection.appendChild(label);
    });
  }

  userSearch.addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
      event.preventDefault();
    }
  });

  // Listen to search input
  userSearch.addEventListener("input", function () {
    renderUserList(userSearch.value.trim());
  });

  // Ensure users are correctly sent before form submission
  form.addEventListener("submit", function () {
    updateSelectedUsers();
  });

  updateSelectedUsers();
});