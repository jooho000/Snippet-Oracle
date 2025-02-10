$(function () {
    console.log("Script 1!");
    if (document.getElementById("edit")){
        console.log("hello there")
    }
    console.log(!(document.getElementById("edit")))
    const preUsers = JSON.parse(document.getElementById("shared-users").textContent);
    const selectedUsersContainer = document.getElementById("selected-users");
    console.log(preUsers);
    function selected() {
        selectedUsersContainer.innerHTML = ""; // Clear old selected users

        // Remove old hidden inputs
        document.querySelectorAll(".hidden-user-input").forEach(input => input.remove());

        preUsers.forEach(user => {
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

        console.log("Selected Users for Submission:", Array.from(users).map(u => u.id));
    }
    selected();
});