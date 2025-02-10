$(function () {
    console.log("Script 1!");
    const users = JSON.parse(document.getElementById("shared-users").textContent);
    console.log(users);
});