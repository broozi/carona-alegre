(() => {
  'use strict';

  const digits = (value) => value.replace(/\D/g, '');

  document.querySelectorAll('.cpf-mask').forEach((input) => {
    input.addEventListener('input', () => {
      const value = digits(input.value).slice(0, 11);
      input.value = value
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
    });
  });

  document.querySelectorAll('.phone-mask').forEach((input) => {
    input.addEventListener('input', () => {
      const value = digits(input.value).slice(0, 11);
      input.value = value.length > 10
        ? value.replace(/(\d{2})(\d{5})(\d{1,4})/, '($1) $2-$3')
        : value.replace(/(\d{2})(\d{4})(\d{1,4})/, '($1) $2-$3');
    });
  });

  document.querySelectorAll('.plate-mask').forEach((input) => {
    input.addEventListener('input', () => {
      input.value = input.value.replace(/[^a-zA-Z0-9]/g, '').slice(0, 7).toUpperCase();
    });
  });

  window.setTimeout(() => {
    document.querySelectorAll('.alert').forEach((alertElement) => {
      bootstrap.Alert.getOrCreateInstance(alertElement).close();
    });
  }, 6000);
})();
