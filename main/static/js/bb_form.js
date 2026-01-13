document.addEventListener('DOMContentLoaded', () => {
  const priceInput = document.querySelector('input[name="price"]');
  const priceHelp = document.getElementById('priceHelp');

  const titleInput = document.querySelector('input[name="title"]');
  const titleCounter = document.getElementById('titleCounter');

  const contentInput = document.querySelector('textarea[name="content"]');
  const contentCounter = document.getElementById('contentCounter');

  const contactsInput = document.querySelector('input[name="contacts"]');
  const contactsCounter = document.getElementById('contactsCounter');

  // Все file-input'ы, где задан data-max-size (мы их проставили в шаблоне)
  const fileInputs = document.querySelectorAll('input[type="file"][data-max-size]');

  // ===== helpers =====
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
    if (idx === -1) return '';
    return filename.slice(idx).toLowerCase();
  }

  function isLikelyAllowedImage(file) {
    // MIME иногда пустой/нестабильный для HEIC, поэтому проверяем и расширение
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

  function renderPreview(targetEl, file) {
    if (!targetEl) return;
    targetEl.innerHTML = '';

    // Превью через dataURL (для больших файлов может быть тяжело, но на 5MB терпимо)
    const reader = new FileReader();
    reader.onload = ev => {
      const img = document.createElement('img');
      img.src = ev.target.result;
      img.className = 'img-thumbnail';
      img.style.maxWidth = '160px';
      img.style.maxHeight = '160px';
      targetEl.appendChild(img);
    };
    reader.readAsDataURL(file);
  }

  // ===== counters =====
  setupCounter(titleInput, titleCounter, 50);
  setupCounter(contentInput, contentCounter, 600);
  setupCounter(contactsInput, contactsCounter, 50);

  // ===== price validation =====
  if (priceInput && priceHelp) {
    const defaultText = priceHelp.dataset.defaultText || priceHelp.textContent || '';
    priceInput.addEventListener('input', () => {
      const value = parseFloat(priceInput.value);

      // Если пусто — вернём дефолтный текст
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

  // ===== file validation + previews =====
  fileInputs.forEach(input => {
    input.addEventListener('change', function () {
      const file = this.files && this.files[0] ? this.files[0] : null;

      // очистка превью если файл сняли
      const targetId = this.dataset.previewTarget;
      const targetEl = targetId ? document.getElementById(targetId) : null;
      if (!file) {
        if (targetEl) targetEl.innerHTML = '';
        return;
      }

      const maxSize = parseInt(this.dataset.maxSize || '5242880', 10);

      if (file.size > maxSize) {
        alert(
          `Файл слишком большой.\n` +
          `Максимум: ${(maxSize / 1024 / 1024).toFixed(1)}MB\n` +
          `Ваш файл: ${(file.size / 1024 / 1024).toFixed(1)}MB`
        );
        this.value = '';
        if (targetEl) targetEl.innerHTML = '';
        return;
      }

      if (!isLikelyAllowedImage(file)) {
        alert('Неподдерживаемый формат. Разрешены: JPG, PNG, WebP, HEIC/HEIF.');
        this.value = '';
        if (targetEl) targetEl.innerHTML = '';
        return;
      }

      // превью
      renderPreview(targetEl, file);
    });
  });
});
