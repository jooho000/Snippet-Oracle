document.addEventListener('DOMContentLoaded', () => {
    const message = document.getElementById('warningMessage');
    const closeMessageButton = document.getElementById('closeMessageButton');
    const deleteButton = message.querySelector('.delete');
  
    // Check if there are warning messages
    if (message.querySelector('.help')) {
      message.classList.add('is-active'); // Show Message if messages exist
    }
  
    // Close Message on button click
    const closeMessage = () => message.remove();
    deleteButton.addEventListener('click', closeMessage);
  });
  