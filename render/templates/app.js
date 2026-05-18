// Theme toggle
const themeBtn = document.getElementById('theme-toggle');
const htmlEl   = document.documentElement;
const saved    = localStorage.getItem('cdc-theme') || 'light';
htmlEl.dataset.theme = saved;
themeBtn.textContent = saved === 'dark' ? '☀️ Light' : '🌙 Dark';
themeBtn.addEventListener('click', () => {
  const next = htmlEl.dataset.theme === 'dark' ? 'light' : 'dark';
  htmlEl.dataset.theme = next;
  localStorage.setItem('cdc-theme', next);
  themeBtn.textContent = next === 'dark' ? '☀️ Light' : '🌙 Dark';
});

// Zebra stripes
document.querySelectorAll('tbody .row-clickable').forEach((row, i) => {
  if (i % 2 === 1) row.classList.add('row-stripe');
});

// Generic row-expand — any element with .row-clickable + data-target
document.querySelectorAll('.row-clickable').forEach(row => {
  row.addEventListener('click', () => {
    const target = document.getElementById(row.dataset.target);
    if (!target) return;
    const isOpen = target.style.display !== 'none';
    target.style.display = isOpen ? 'none' : (target.tagName === 'TR' ? 'table-row' : 'block');
    row.classList.toggle('expanded', !isOpen);
  });
});
