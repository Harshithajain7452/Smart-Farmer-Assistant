/* Dark-mode toggle with persistence + OS preference fallback. */
(function () {
  const KEY = 'sfa-theme';
  const root = document.documentElement;

  function apply(theme) {
    root.setAttribute('data-theme', theme);
    document.querySelectorAll('#themeToggle i').forEach(function (icon) {
      icon.className = theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon-stars';
    });
    document.dispatchEvent(new CustomEvent('themechange', { detail: { theme: theme } }));
  }

  const stored = localStorage.getItem(KEY);
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  apply(stored || (prefersDark ? 'dark' : 'light'));

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('#themeToggle').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        localStorage.setItem(KEY, next);
        apply(next);
      });
    });
  });
})();
