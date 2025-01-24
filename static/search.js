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