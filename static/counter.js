function updateCharacterCount(inputId, countId) {
    let input = document.getElementById(inputId);
    let countDisplay = document.getElementById(countId);
    
    if (input && countDisplay) {
      let remaining = input.maxLength - input.value.length;
      countDisplay.textContent = input.value.length + "/" + input.maxLength;
  
      countDisplay.setAttribute("title", remaining + " characters remaining");
    }
  }
  
  // Initialize character counts on page load
  document.addEventListener("DOMContentLoaded", function() {
    updateCharacterCount('snippet-name', 'name-char-count');
    updateCharacterCount('snippet-description', 'desc-char-count');
    updateCharacterCount('snippet-code', 'code-char-count');
    updateCharacterCount('tag-input', 'tag-char-count');
    updateCharacterCount('userSearch', 'userSearch-char-count');
  
    // Add character limits for profile bio
    updateCharacterCount('bio-input', 'bio-char-count');
  });