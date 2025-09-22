// static/js/main.js

document.addEventListener('DOMContentLoaded', () => {
  // ===== Transactions page: Live search, toolbar & edit-modal =====
  const form = document.getElementById('transactionsSearchForm');
  if (form) {
    const input = form.querySelector('input[name="q"]');
    const clearBtn = document.getElementById('clearSearchBtn');
    let timer;

    // Автофокус
    input.focus();

    // Показать/скрыть кнопку очистки
    function toggleClearBtn() {
      clearBtn.style.display = input.value ? 'inline-flex' : 'none';
    }
    toggleClearBtn();

    input.addEventListener('input', () => {
      toggleClearBtn();
      clearTimeout(timer);
      timer = setTimeout(doSearch, 350);
    });

    input.addEventListener('keyup', e => {
      if (e.key === 'Escape') {
        input.value = '';
        toggleClearBtn();
        doSearch();
      }
    });

    clearBtn.addEventListener('click', () => {
      input.value = '';
      input.focus();
      toggleClearBtn();
      doSearch();
    });

    form.addEventListener('submit', e => {
      e.preventDefault();
      doSearch();
    });

    function doSearch() {
      const url = new URL(window.location.href);
      url.searchParams.set('q', input.value);

      fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(r => r.text())
        .then(html => {
          document.getElementById('transactionsRows').innerHTML = html;
          initRowToolbar();
          bindEditModal();
        })
        .catch(console.error);
    }

    // ===== Toolbar (hover buttons) =====
    function initRowToolbar() {
      document.querySelectorAll('.table-row-with-toolbar').forEach(row => {
        const tb = row.querySelector('.action-toolbar');
        row.addEventListener('mouseenter', () => {
          tb.style.opacity = '1';
          tb.style.pointerEvents = 'auto';
        });
        row.addEventListener('mouseleave', () => {
          tb.style.opacity = '0';
          tb.style.pointerEvents = 'none';
        });
      });
      // re-init Bootstrap tooltips inside rows
      document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el =>
        new bootstrap.Tooltip(el)
      );
    }
    window.initRowToolbar = initRowToolbar;

    // ===== Edit-modal data binding =====
    function bindEditModal() {
      const modal = document.getElementById('editTransactionModal');
      if (!modal) return;
      modal.removeEventListener('show.bs.modal', onShowEditModal);
      modal.addEventListener('show.bs.modal', onShowEditModal);
    }

    function onShowEditModal(event) {
      const btn = event.relatedTarget;
      document.getElementById('editTransactionId').value   = btn.getAttribute('data-id')   || '';
      document.getElementById('editTransactionItem').value = btn.getAttribute('data-item') || '';
      document.getElementById('editTransactionType').value = btn.getAttribute('data-type') || 'sale';
      document.getElementById('editTransactionQty').value  = btn.getAttribute('data-qty')  || '1';
    }

    // Автоинициализация поискового тулбара и модалки при загрузке
    initRowToolbar();
    bindEditModal();

    // Авто-открытие любых модалей по data-bs-toggle
    document.querySelectorAll('[data-bs-toggle="modal"]').forEach(btn => {
      btn.addEventListener('click', () => {
        const sel = btn.getAttribute('data-bs-target');
        const modalEl = document.querySelector(sel);
        if (modalEl) bootstrap.Modal.getOrCreateInstance(modalEl).show();
      });
    });
  }

  // ===== Theme toggle (runs on every page) =====
  function updateThemeIcon() {
    const icon = document.getElementById('themeIcon');
    if (!icon) return;
    icon.className = document.body.classList.contains('dark') ? 'bi bi-sun' : 'bi bi-moon';
  }

  function setTheme(mode) {
    if (mode === 'dark') document.body.classList.add('dark');
    else document.body.classList.remove('dark');
    updateThemeIcon();
    localStorage.setItem('theme', mode);
  }

  const toggler = document.getElementById('toggleNightMode');
  if (toggler) {
    toggler.addEventListener('click', () => {
      const isDark = document.body.classList.contains('dark');
      setTheme(isDark ? 'light' : 'dark');
    });
  }

  const preferDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const userTheme = localStorage.getItem('theme');
  setTheme(userTheme || (preferDark ? 'dark' : 'light'));
});
