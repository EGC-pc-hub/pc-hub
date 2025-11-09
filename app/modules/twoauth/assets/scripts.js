document.addEventListener('DOMContentLoaded', () => {
  const codeInput = document.querySelector('input[name="code"]');
  if (codeInput) {
    codeInput.setAttribute('inputmode', 'numeric');
    codeInput.setAttribute('pattern', '\\d*');
    codeInput.addEventListener('input', (e) => {
      e.target.value = e.target.value.replace(/\D/g, '').slice(0, 6);
    });
  }
});
