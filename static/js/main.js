document.addEventListener('DOMContentLoaded', () => {
  // Mobile menu toggle
  const toggle = document.getElementById('navToggle');
  const links = document.getElementById('navLinks');
  if (toggle && links) {
    toggle.addEventListener('click', () => links.classList.toggle('open'));
  }

  // Enforce 5MB max file size on image upload
  const fileInput = document.querySelector('input[type="file"][name="image"]');
  if (fileInput) {
    fileInput.addEventListener('change', () => {
      if (!fileInput.files.length) return;
      const sizeMB = fileInput.files[0].size / (1024 * 1024);
      if (sizeMB > 5) {
        alert('Image must be smaller than 5MB.');
        fileInput.value = '';
      }
    });
  }
});