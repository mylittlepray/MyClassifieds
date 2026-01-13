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

  function setupPricePrettyInput(input) {
    if (!input) return;

    const nfLive = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 });
    const nf2 = new Intl.NumberFormat('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    const normalize = (s) => {
      s = (s || '')
        .replace(/\./g, ',')
        .replace(/[^\d,]/g, '');  

      const parts = s.split(',');
      const intPart = (parts[0] || '').replace(/^0+(?=\d)/, ''); 
      const fracPart = (parts[1] || '').slice(0, 2);
      const hasComma = s.includes(',');
      return { intPart, fracPart, hasComma };
    };

    const format = (intPart, fracPart, hasComma, force2) => {
      const n = Number((intPart || '0') + '.' + (fracPart || ''));
      let out = (force2 ? nf2 : nfLive).format(n);

      out = out.replace(/\u00A0|\u202F/g, ' ');

      if (!force2) {
        const left = out.split(',')[0];
        if (hasComma) return left + ',' + fracPart;
        return left;
      }

      return out;
    };

    input.addEventListener('input', () => {
      const { intPart, fracPart, hasComma } = normalize(input.value);
      input.value = format(intPart, fracPart, hasComma, false);
    });

    input.addEventListener('blur', () => {
      const { intPart, fracPart, hasComma } = normalize(input.value);

      if (!intPart && !fracPart) {
        input.value = '';
        return;
      }

      input.value = format(intPart, fracPart, hasComma, true);
    });

    if (input.value.trim() !== '') {
      const { intPart, fracPart, hasComma } = normalize(input.value);
      input.value = format(intPart, fracPart, hasComma, true);
    }
  }

  setupPricePrettyInput(priceInput);

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
    const allowedMimes = new Set([
      'image/jpeg',
      'image/png',
      'image/webp',
      'image/heic',
      'image/heif',
      'image/mpo'
    ]);
    const allowedExts = new Set(['.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif', '.mpo']);

    const extOk = allowedExts.has(getExt(file.name));
    const mimeOk = file.type ? allowedMimes.has(file.type) : true;
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

  setupCounter(titleInput, titleCounter, 50);
  setupCounter(contentInput, contentCounter, 600);
  setupCounter(contactsInput, contactsCounter, 50);

  if (priceInput) {
    const nfLive = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 });
    const nf2 = new Intl.NumberFormat('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    priceInput.addEventListener('beforeinput', (e) => {
      if (typeof e.data !== 'string' || e.data.length !== 1) return;
      if (!/[0-9\s.,]/.test(e.data)) e.preventDefault();
    });

    const normalize = (s) => {
      s = (s || '')
        .replace(/\./g, ',')
        .replace(/[^\d,]/g, '');

      const [a, b = ''] = s.split(',');
      return { intPart: a, fracPart: b.slice(0, 2), hasComma: s.includes(',') };
    };

    const format = (force2) => {
      const { intPart, fracPart, hasComma } = normalize(priceInput.value);

      if (!intPart && !fracPart) {
        priceInput.value = '';
        return;
      }

      const n = Number((intPart || '0') + '.' + (fracPart || ''));
      let out = (force2 ? nf2 : nfLive).format(n).replace(/\u00A0|\u202F/g, ' ');

      if (!force2) {
        const left = out.split(',')[0];
        priceInput.value = hasComma ? (left + ',' + fracPart) : left;
      } else {
        priceInput.value = out;
      }
    };

    priceInput.addEventListener('input', () => format(false));
    priceInput.addEventListener('blur',  () => format(true));
  }

  if (priceInput && priceHelp) {
      const defaultText = priceHelp.dataset.defaultText || priceHelp.textContent || '';

      const parseRuMoney = (s) => {
        s = (s || '').replace('₽', '').trim();
        if (!s) return NaN;
        s = s.replace(/\u00A0|\u202F/g, ' ').replace(/ /g, '');
        s = s.replace(',', '.');
        return Number(s);
      };

      priceInput.addEventListener('input', () => {
        const value = parseRuMoney(priceInput.value);

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

  fileInputs.forEach(input => {
    input.addEventListener('change', function () {
      const file = this.files && this.files[0] ? this.files[0] : null;

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
