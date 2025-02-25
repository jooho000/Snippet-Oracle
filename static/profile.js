let cropper;

function openEditModal() {
  document.getElementById("edit-modal").classList.add("is-active");
}

function closeEditModal() {
  document.getElementById("edit-modal").classList.remove("is-active");
}

function addSocialLink() {
  const container = document.getElementById("social-links-container");
  const newField = document.createElement("div");
  newField.className = "control mt-2";
  newField.innerHTML =
    '<input class="input" type="text" name="links" placeholder="Enter a new URL">';
  container.appendChild(newField);
}

function previewImage(event) {
  const file = event.target.files[0];
  const reader = new FileReader();

  reader.onload = function (e) {
    const previewContainer = document.getElementById("image-preview-container");
    const previewImage = document.getElementById("image-preview");

    previewImage.src = e.target.result;
    previewContainer.style.display = "block"; // Show the image preview

    if (cropper) {
      cropper.destroy();
    }

    const img = document.getElementById("image-preview");
    cropper = new Cropper(img, {
      aspectRatio: 1, // 1:1 aspect ratio
      viewMode: 2, // Restrict the crop box within the canvas
      autoCropArea: 0.8,
      responsive: true,
      scalable: false,
      zoomable: false,
      ready() {
        // Apply circular appearance to the crop box and preview
        const cropBox = document.querySelector(".cropper-crop-box");
        const viewBox = document.querySelector(".cropper-view-box");

        if (cropBox && viewBox) {
          cropBox.style.borderRadius = "50%"; // Circular crop area
          viewBox.style.borderRadius = "50%"; // Circular preview
        }
      },
    });
  };

  if (file) {
    reader.readAsDataURL(file);
  }
}

function submitProfileForm(event) {
  event.preventDefault(); // Prevent the default form submission

  // If there's a cropped image, compress and add it to the form as base64
  const form = document.getElementById("edit-profile-form");

  if (cropper) {
    // Get the cropped canvas
    const croppedCanvas = cropper.getCroppedCanvas();

    // Compress the image (e.g., 50% quality for JPEG)
    const compressedImage = croppedCanvas.toDataURL("image/jpeg", 0.5); // 0.5 is the quality factor (0 to 1)

    // Only add the hidden input with base64 if an image was cropped
    const hiddenInput = document.createElement("input");
    hiddenInput.type = "hidden";
    hiddenInput.name = "profile_picture_base64";
    hiddenInput.value = compressedImage;
    form.appendChild(hiddenInput);
  }

  // Submit the form
  form.submit();
}
