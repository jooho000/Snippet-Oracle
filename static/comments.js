function toggleReplyForm(commentId) {
  const replyForm = document.getElementById(`reply-form-${commentId}`);
  if (replyForm) {
    replyForm.classList.toggle("is-hidden");
  }
}

function parseDate(dateString) {
  // Convert "YYYY-MM-DD HH:mm:ss" to "YYYY-MM-DDTHH:mm:ssZ" (ISO format)
  let dateParts = dateString.split(" ");
  let formattedDate = dateParts[0] + "T" + dateParts[1] + "Z"; // Append 'Z' for UTC

  return new Date(formattedDate);
}

function timeAgo(dateString) {
  const now = new Date();
  const pastDate = parseDate(dateString);

  if (isNaN(pastDate)) {
    console.error("Invalid Date:", dateString);
    return "Unknown time";
  }

  const seconds = Math.floor((now - pastDate) / 1000);
  const intervals = {
    year: 31536000,
    month: 2592000,
    week: 604800,
    day: 86400,
    hour: 3600,
    minute: 60,
    second: 1,
  };

  for (const [unit, value] of Object.entries(intervals)) {
    const count = Math.floor(seconds / value);
    if (count >= 1) {
      return new Intl.RelativeTimeFormat("en", { numeric: "auto" }).format(
        -count,
        unit
      );
    }
  }
  return "just now";
}

/**
   * Bring up a confirm dialogue for Comment/Reply deletion.
   * @param {JQuery} card
   */
async function confirmCommentDelete(id) {
  const message = 'Are you sure you want to delete this comment?';
  if (window.confirm(message)) {
    await fetch(`/comment/${id}/delete`, {
      method: 'POST',
    });
    window.location.reload();
  }
}

// Format all timestamps on the page
$(function () {
  for (const element of $(".timestamp")) {
    let timestamp = element.dataset.timestamp;
    element.textContent = timeAgo(timestamp);
    element.title = parseDate(timestamp).toLocaleString();
  }
});

function updateCharacterCount(inputId, countDisplayId) {
  const input = document.getElementById(inputId);
  const countDisplay = document.getElementById(countDisplayId);

  if (input && countDisplay) {
    countDisplay.textContent = `${input.value.length}/500`;
  }
}


function toggleReplies(commentId) {
  const replySection = document.getElementById(`replies-${commentId}`);
  const arrowIcon = document.getElementById(`toggle-arrow-${commentId}`).querySelector("i");

  if (replySection) {
    replySection.classList.toggle("is-hidden");
    arrowIcon.classList.toggle("fa-chevron-right");
    arrowIcon.classList.toggle("fa-chevron-down"); // Rotates arrow when expanded
  }
}


