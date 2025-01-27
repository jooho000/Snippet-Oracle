const searchInput = document.getElementById('search-input');
const resultsContainer = document.getElementById('search-results');

searchInput.addEventListener('input', function () {
    const query = searchInput.value;

    // Don't search if input is empty
    if (!query.trim()) {
        resultsContainer.innerHTML = '';
        return;
    }

    // Send the query to the server via AJAX (using fetch)
    fetch(`/search?q=${query}`)
        .then(response => response.json())
        .then(data => {
            resultsContainer.innerHTML = '';  // Clear previous results

            // If there are results, display them as buttons
            if (data.results.length > 0) {
                data.results.forEach(snippet => {
                    const button = document.createElement('a');
                    button.href = `/snippet/${snippet.id}`;
                    button.className = 'button is-primary is-large mt-2';
                    button.textContent = snippet.name;
                    resultsContainer.appendChild(button);
                });
            } else {
                resultsContainer.innerHTML = 'No snippets found.';
            }
        })
        .catch(error => {
            console.error('Error fetching search results:', error);
            resultsContainer.innerHTML = 'Error occurred while searching.';
        });
});

function toggleSnippet(id, button, snippetContent, snippetDescription) {
    const container = document.getElementById(id);
    const icon = button.querySelector("svg");

    if (!container.hasChildNodes()) {
        // Create snippet content dynamically
        const contentDiv = document.createElement('div');
        contentDiv.className = 'mt-3';

        // Add snippet content and description (no Copy button)
        contentDiv.innerHTML = `
            <hr>
            <pre class="code-snippet">${snippetContent}</pre>
            <p><strong>Description:</strong> ${snippetDescription || "No description available."}</p>
        `;
        container.appendChild(contentDiv);

        // Show the container
        container.style.display = "block";

        // Update icon to up arrow
        icon.setAttribute("d", "M5 15l7-7 7 7");
    } else {
        // Destroy snippet content dynamically
        container.innerHTML = '';  // Remove child nodes
        container.style.display = "none";  // Hide the container

        // Update icon to down arrow
        icon.setAttribute("d", "M19 9l-7 7-7-7");
    }
}

function copySnippet(code) {
    navigator.clipboard.writeText(code)
        .then(() => {
            alert("Code snippet copied to clipboard!");
        })
        .catch(err => {
            console.error("Failed to copy text: ", err);
        });
}
