$(function () {
  const preUsers = JSON.parse(
    document.getElementById("shared-users").textContent
  );
  const selectedUsersContainer = document.getElementById("selected-users");
  selectedUsersContainer.innerHTML = ""; // Clear old selected users

  // Remove old hidden inputs
  document
    .querySelectorAll(".hidden-user-input")
    .forEach((input) => input.remove());

  preUsers.forEach((user) => {
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
  });
});
