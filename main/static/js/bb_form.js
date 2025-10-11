document.addEventListener('DOMContentLoaded', () => {
  const priceInput = document.querySelector('input[name="price"]');
  const priceHelp = document.getElementById('priceHelp');
  const titleInput = document.querySelector('input[name="title"]');
  const titleCounter = document.getElementById('titleCounter');
  const contentInput = document.querySelector('textarea[name="content"]');
  const contentCounter = document.getElementById('contentCounter');
  const contactsInput = document.querySelector('input[name="contacts"]');
  const contactsCounter = document.getElementById('contactsCounter');
  const mainImageInput = document.querySelector('input[name="image"]');
  const mainImagePreview = document.getElementById('mainImagePreview');
  const extraInputs = document.querySelectorAll('input[type="file"][id*="additionalimage"]');
  const extraPreviews = document.getElementById('extraPreviews');

  // Валидация цены
  if (priceInput) {
    priceInput.addEventListener('input', () => {
      const value = parseFloat(priceInput.value);
      if (isNaN(value)) return;
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
        priceHelp.textContent = '';
      }
    });
  }

  // Счётчики символов
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

  setupCounter(titleInput, titleCounter, 50);
  setupCounter(contentInput, contentCounter, 600);
  setupCounter(contactsInput, contactsCounter, 50);

  // Превью главного изображения
  if (mainImageInput && mainImagePreview) {
    mainImageInput.addEventListener('change', e => {
      mainImagePreview.innerHTML = '';
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = ev => {
        const img = document.createElement('img');
        img.src = ev.target.result;
        img.className = 'img-thumbnail mt-2';
        img.style.maxWidth = '150px';
        mainImagePreview.appendChild(img);
      };
      reader.readAsDataURL(file);
    });
  }

  // Превью дополнительных изображений
  extraInputs.forEach(input => {
    input.addEventListener('change', e => {
      extraPreviews.innerHTML = '';
      Array.from(e.target.files).forEach(file => {
        const reader = new FileReader();
        reader.onload = ev => {
          const img = document.createElement('img');
          img.src = ev.target.result;
          img.className = 'img-thumbnail';
          img.style.maxWidth = '120px';
          extraPreviews.appendChild(img);
        };
        reader.readAsDataURL(file);
      });
    });
  });
});
