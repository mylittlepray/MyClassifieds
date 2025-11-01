(function () {
    const toNumber = (value) => {
        const parsed = Number(value);
        return Number.isFinite(parsed) ? parsed : 0;
    };

    document.addEventListener('DOMContentLoaded', () => {
        const ratingControl = document.querySelector('[data-rating-control]');
        const ratingInput = document.querySelector('[data-rating-input]');

        if (ratingControl && ratingInput) {
            const ratingButtons = Array.from(ratingControl.querySelectorAll('[data-rating-star]'));
            const maxValue = ratingButtons.length;
            let selectedValue = Math.min(maxValue, Math.max(0, toNumber(ratingInput.value)));

            const renderSelection = () => {
                ratingButtons.forEach((button) => {
                    const starValue = toNumber(button.dataset.ratingStar);
                    const icon = button.querySelector('i');
                    const isActive = starValue <= selectedValue;
                    button.classList.toggle('is-active', isActive && selectedValue > 0);
                    button.classList.remove('is-hover');
                    if (icon) {
                        icon.classList.toggle('fas', isActive);
                        icon.classList.toggle('far', !isActive);
                    }
                    button.setAttribute('aria-checked', starValue === selectedValue ? 'true' : 'false');
                });
            };

            const renderPreview = (value) => {
                ratingButtons.forEach((button) => {
                    const starValue = toNumber(button.dataset.ratingStar);
                    const icon = button.querySelector('i');
                    const isHover = starValue <= value;
                    button.classList.toggle('is-hover', isHover);
                    if (icon) {
                        icon.classList.toggle('fas', isHover);
                        icon.classList.toggle('far', !isHover);
                    }
                });
            };

            const clearPreview = () => {
                renderSelection();
            };

            const commitRating = (value) => {
                selectedValue = value;
                ratingInput.value = value;
                renderSelection();
            };

            const focusButton = (value) => {
                const target = ratingButtons.find((button) => toNumber(button.dataset.ratingStar) === value);
                if (target) {
                    target.focus();
                }
            };

            ratingButtons.forEach((button) => {
                const starValue = toNumber(button.dataset.ratingStar);

                button.addEventListener('click', () => {
                    commitRating(starValue);
                });

                button.addEventListener('mouseenter', () => {
                    renderPreview(starValue);
                });

                button.addEventListener('mouseleave', clearPreview);
                button.addEventListener('focus', () => {
                    renderPreview(starValue);
                });

                button.addEventListener('blur', clearPreview);

                button.addEventListener('keydown', (event) => {
                    let nextValue = null;
                    switch (event.key) {
                        case 'ArrowRight':
                        case 'ArrowUp':
                            nextValue = selectedValue >= 1 ? Math.min(maxValue, selectedValue + 1) : 1;
                            break;
                        case 'ArrowLeft':
                        case 'ArrowDown':
                            nextValue = selectedValue > 1 ? selectedValue - 1 : 1;
                            break;
                        case 'Home':
                            nextValue = 1;
                            break;
                        case 'End':
                            nextValue = maxValue;
                            break;
                        case ' ':
                        case 'Enter':
                            nextValue = starValue;
                            break;
                        default:
                            break;
                    }

                    if (nextValue !== null) {
                        event.preventDefault();
                        commitRating(nextValue);
                        focusButton(nextValue);
                    }
                });
            });

            ratingControl.addEventListener('mouseleave', clearPreview);
            renderSelection();
        }

        const imageModal = document.getElementById('imageModal');
        if (imageModal) {
            imageModal.addEventListener('show.bs.modal', (event) => {
                const trigger = event.relatedTarget;
                if (!trigger) {
                    return;
                }
                const targetUrl = trigger.getAttribute('data-img');
                const modalImage = imageModal.querySelector('#modalImage');
                if (modalImage && targetUrl) {
                    modalImage.src = targetUrl;
                }
            });
        }
    });
})();
