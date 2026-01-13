document.addEventListener('DOMContentLoaded', () => {
  const priceInput = document.querySelector('input[name="price"]');
  const priceHelp = document.getElementById('priceHelp');

  const titleInput = document.querySelector('input[name="title"]');
  const titleCounter = document.getElementById('titleCounter');

  const contentInput = document.querySelector('textarea[name="content"]');
  const contentCounter = document.getElementById('contentCounter');

  const contactsInput = document.querySelector('input[name="contacts"]');
  const contactsCounter = document.getElementById('contactsCounter');

  const fileInputs = document.querySelectorAll('input[type="file"]');

  function setupCounter(input, counterElem, max) {
    if (!input || !counterElem) return;
    const update = () => {
      const len = input.value.length;
      counterElem.textContent = len;
      counterElem.classList.toggle('text-danger', len > max);
    };
    input.addEventListener('input', update);
    update();
  }

  function getExt(filename) {
    const idx = filename.lastIndexOf('.');
    return idx === -1 ? '' : filename.slice(idx).toLowerCase();
  }

  function isLikelyAllowedImage(file) {
    // MIME у HEIC бывает нестабильным, поэтому проверяем и расширение
    const allowedMimes = new Set([
      'image/jpeg',
      'image/png',
      'image/webp',
      'image/heic',
      'image/heif'
    ]);
    const allowedExts = new Set(['.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif']);

    const extOk = allowedExts.has(getExt(file.name));
    const mimeOk = file.type ? allowedMimes.has(file.type) : true; // если type пустой — не режем на клиенте
    return extOk && mimeOk;
  }

  function renderPreview(previewEl, file) {
    if (!previewEl) return;
    previewEl.innerHTML = '';

    const reader = new FileReader();
    reader.onload = ev => {
      const img = document.createElement('img');
      img.src = ev.target.result;
      img.className = 'img-thumbnail';
      img.style.maxWidth = '160px';
      img.style.maxHeight = '160px';
      previewEl.appendChild(img);
    };
    reader.readAsDataURL(file);
  }

  // counters
  setupCounter(titleInput, titleCounter, 50);
  setupCounter(contentInput, contentCounter, 600);
  setupCounter(contactsInput, contactsCounter, 50);

  // price validation
  if (priceInput && priceHelp) {
    const defaultText = priceHelp.dataset.defaultText || priceHelp.textContent || '';
    priceInput.addEventListener('input', () => {
      const value = parseFloat(priceInput.value);

      if (priceInput.value.trim() === '' || Number.isNaN(value)) {
        priceInput.classList.remove('is-invalid');
        priceHelp.classList.remove('text-danger');
        priceHelp.textContent = defaultText;
        return;
      }

      if (value > 999999999999.99) {
        priceInput.classList.add('is-invalid');
        priceHelp.classList.add('text-danger');
        priceHelp.textContent = 'Максимальная цена — 999 999 999 999.99 ₽';
      } else if (value < 0) {
        priceInput.classList.add('is-invalid');
        priceHelp.classList.add('text-danger');
        priceHelp.textContent = 'Цена не может быть отрицательной';
      } else {
        priceInput.classList.remove('is-invalid');
        priceHelp.classList.remove('text-danger');
        priceHelp.textContent = defaultText;
      }
    });
  }

  // file validation + preview
  fileInputs.forEach(input => {
    input.addEventListener('change', function () {
      const file = this.files && this.files[0] ? this.files[0] : null;

      // preview id = preview-<input.id>
      const previewEl = this.id ? document.getElementById(`preview-${this.id}`) : null;

      if (!file) {
        if (previewEl) previewEl.innerHTML = '';
        return;
      }

      const maxSize = parseInt(this.dataset.maxSize || '10485760', 10);

      if (file.size > maxSize) {
        alert(
          `Файл слишком большой.\n` +
          `Максимум: ${(maxSize / 1024 / 1024).toFixed(1)}MB\n` +
          `Ваш файл: ${(file.size / 1024 / 1024).toFixed(1)}MB`
        );
        this.value = '';
        if (previewEl) previewEl.innerHTML = '';
        return;
      }

      if (!isLikelyAllowedImage(file)) {
        alert('Неподдерживаемый формат. Разрешены: JPG, PNG, WebP, HEIC/HEIF.');
        this.value = '';
        if (previewEl) previewEl.innerHTML = '';
        return;
      }

      renderPreview(previewEl, file);
    });
  });
});
