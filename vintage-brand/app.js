document.addEventListener('DOMContentLoaded', () => {
  // Menu category tabs
  const tabs = Array.from(document.querySelectorAll('[data-menu-tab]'));
  const panels = Array.from(document.querySelectorAll('[data-menu-panel]'));

  const activate = (id) => {
    tabs.forEach((tab) => {
      const isActive = tab.dataset.menuTab === id;
      tab.classList.toggle('active', isActive);
      tab.setAttribute('aria-selected', String(isActive));
    });
    panels.forEach((panel) => {
      const isActive = panel.dataset.menuPanel === id;
      panel.classList.toggle('active', isActive);
      panel.hidden = !isActive;
    });
  };

  tabs.forEach((tab) => {
    tab.setAttribute('role', 'tab');
    tab.addEventListener('click', () => activate(tab.dataset.menuTab));
  });

  if (tabs.length) activate(tabs[0].dataset.menuTab);

  // Copy-to-clipboard buttons for Flow prompts
  document.querySelectorAll('.copy-btn[data-target]').forEach((button) => {
    button.addEventListener('click', async () => {
      const target = document.getElementById(button.dataset.target);
      if (!target) return;
      const text = target.innerText || target.textContent || '';
      try {
        await navigator.clipboard.writeText(text);
        const original = button.textContent;
        button.textContent = 'Copied';
        setTimeout(() => { button.textContent = original; }, 1400);
      } catch (err) {
        button.textContent = 'Select & copy';
        setTimeout(() => { button.textContent = 'Copy prompt'; }, 1800);
      }
    });
  });

  // Footer year
  document.querySelectorAll('[data-year]').forEach((el) => {
    el.textContent = new Date().getFullYear();
  });
});
