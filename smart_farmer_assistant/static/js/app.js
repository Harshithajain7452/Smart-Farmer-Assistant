/* Shared dashboard behaviour: sidebar, loaders, upload preview, chart theming. */
(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    // ---- Mobile sidebar -----------------------------------------------
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.getElementById('sidebarBackdrop');
    const toggle = document.getElementById('sidebarToggle');
    if (toggle) {
      toggle.addEventListener('click', function () {
        sidebar.classList.add('open');
        backdrop.classList.add('show');
      });
      backdrop.addEventListener('click', function () {
        sidebar.classList.remove('open');
        backdrop.classList.remove('show');
      });
    }

    // ---- Loading overlay on slow forms --------------------------------
    document.querySelectorAll('form[data-loading]').forEach(function (form) {
      form.addEventListener('submit', function () {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) overlay.classList.add('show');
      });
    });

    // ---- Image upload: drag & drop + instant preview -------------------
    document.querySelectorAll('[data-upload-zone]').forEach(function (zone) {
      const input = zone.querySelector('input[type=file]');
      const preview = document.querySelector(zone.dataset.preview);
      if (!input) return;

      zone.addEventListener('click', function (e) {
        if (e.target !== input) input.click();
      });
      ['dragenter', 'dragover'].forEach(function (ev) {
        zone.addEventListener(ev, function (e) { e.preventDefault(); zone.classList.add('dragover'); });
      });
      ['dragleave', 'drop'].forEach(function (ev) {
        zone.addEventListener(ev, function (e) { e.preventDefault(); zone.classList.remove('dragover'); });
      });
      zone.addEventListener('drop', function (e) {
        if (e.dataTransfer.files.length) { input.files = e.dataTransfer.files; showPreview(); }
      });
      input.addEventListener('change', showPreview);

      function showPreview() {
        const file = input.files && input.files[0];
        if (!file || !preview) return;
        if (file.size > 8 * 1024 * 1024) {
          alert('Please choose an image under 8 MB.');
          input.value = '';
          return;
        }
        const reader = new FileReader();
        reader.onload = function (ev) {
          preview.src = ev.target.result;
          preview.classList.remove('d-none');
          const hint = zone.querySelector('[data-upload-hint]');
          if (hint) hint.textContent = file.name;
        };
        reader.readAsDataURL(file);
      }
    });

    // ---- Dependent state -> district selects --------------------------
    document.querySelectorAll('[data-state-select]').forEach(function (stateSel) {
      const target = document.querySelector(stateSel.dataset.districtTarget);
      if (!target) return;
      stateSel.addEventListener('change', function () {
        const preset = target.dataset.selected || '';
        target.innerHTML = '<option value="">All districts</option>';
        if (!stateSel.value) return;
        fetch('/api/v1/districts/' + encodeURIComponent(stateSel.value))
          .then(function (r) { return r.json(); })
          .then(function (data) {
            (data.districts || []).forEach(function (d) {
              const opt = document.createElement('option');
              opt.value = d; opt.textContent = d;
              if (d === preset) opt.selected = true;
              target.appendChild(opt);
            });
          });
      });
    });

    // ---- Auto-dismiss flash messages ----------------------------------
    setTimeout(function () {
      document.querySelectorAll('.alert-dismissible').forEach(function (el) {
        const inst = bootstrap.Alert.getOrCreateInstance(el);
        if (inst) inst.close();
      });
    }, 8000);
  });

  // ---- Chart.js helpers ------------------------------------------------
  window.SFA = {
    colors: function () {
      const s = getComputedStyle(document.documentElement);
      return {
        brand: s.getPropertyValue('--green-600').trim() || '#228b4a',
        brandLight: s.getPropertyValue('--green-500').trim() || '#2fa35c',
        accent: s.getPropertyValue('--amber-500').trim() || '#e8a020',
        sky: s.getPropertyValue('--sky-600').trim() || '#1f7ba8',
        clay: s.getPropertyValue('--clay-600').trim() || '#a4562c',
        text: s.getPropertyValue('--text-muted').trim() || '#5f6f64',
        grid: s.getPropertyValue('--border').trim() || '#e3e7dd'
      };
    },

    baseOptions: function () {
      const c = this.colors();
      return {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { labels: { color: c.text, usePointStyle: true, boxWidth: 8, font: { size: 11 } } },
          tooltip: {
            backgroundColor: 'rgba(18,51,29,.94)', padding: 10, cornerRadius: 8,
            titleFont: { size: 12 }, bodyFont: { size: 12 }
          }
        },
        scales: {
          x: { ticks: { color: c.text, font: { size: 11 } }, grid: { color: c.grid, drawBorder: false } },
          y: { ticks: { color: c.text, font: { size: 11 } }, grid: { color: c.grid, drawBorder: false } }
        }
      };
    },

    /* Re-tint every chart when the theme flips. */
    register: function (chart) {
      (this._charts = this._charts || []).push(chart);
      return chart;
    }
  };

  document.addEventListener('themechange', function () {
    (window.SFA._charts || []).forEach(function (chart) {
      const c = window.SFA.colors();
      if (chart.options.scales) {
        Object.values(chart.options.scales).forEach(function (axis) {
          axis.ticks.color = c.text;
          axis.grid.color = c.grid;
        });
      }
      if (chart.options.plugins && chart.options.plugins.legend) {
        chart.options.plugins.legend.labels.color = c.text;
      }
      chart.update('none');
    });
  });
})();
