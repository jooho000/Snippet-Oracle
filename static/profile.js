let cropper;

const MAX_FILE_SIZE = 5 * 1024 * 1024;
const MAX_CROP_SIZE = 1024;

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

function isValidURL(url) {
  try {
    const parsedURL = new URL(url);
    return parsedURL.protocol === "http:" || parsedURL.protocol === "https:";
  } catch (e) {
    return false;
  }
}

function previewImage(event) {
  const file = event.target.files[0];

  if (file.size > MAX_FILE_SIZE) {
    alert("File is too large! Please upload an image smaller than 5MB.");
    return;
  }

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
      cropmove(event) {
        const cropBoxData = cropper.getCropBoxData();
        if (cropBoxData.width > MAX_CROP_SIZE) cropper.setCropBoxData({ width: MAX_CROP_SIZE });
        if (cropBoxData.height > MAX_CROP_SIZE) cropper.setCropBoxData({ height: MAX_CROP_SIZE });
      },
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
  event.preventDefault();
  const form = document.getElementById("edit-profile-form");
  const socialLinks = document.getElementsByName("links");

  for (let linkInput of socialLinks) {
    let url = linkInput.value.trim();
    if (url && !isValidURL(url)) {
      alert(`Invalid URL: ${url}. Ensure it starts with http:// or https://`);
      return;
    }
  }

  if (cropper) {
    const croppedCanvas = cropper.getCroppedCanvas({
      maxWidth: MAX_CROP_SIZE,
      maxHeight: MAX_CROP_SIZE,
    });

    const compressedImage = croppedCanvas.toDataURL("image/jpeg", 0.5);

    const hiddenInput = document.createElement("input");
    hiddenInput.type = "hidden";
    hiddenInput.name = "profile_picture_base64";
    hiddenInput.value = compressedImage;
    form.appendChild(hiddenInput);
  }

  form.submit();
}