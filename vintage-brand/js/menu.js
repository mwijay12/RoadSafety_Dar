/* ============================================================
   Full menu page — renders categories from the same content the site
   and the admin panel use, so a price changed in /admin.html changes
   here too. Falls back to js/content.js defaults if nothing is saved.
   ============================================================ */

import { load } from './content.js';

const host = document.getElementById('menu-cats');
if (host) {
  const { menu } = load();
  host.textContent = '';
  menu.forEach((cat) => {
    const section = document.createElement('section');
    section.className = 'print-category';
    const h2 = document.createElement('h2');
    h2.textContent = cat.title;
    section.appendChild(h2);
    cat.items.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'print-item';
      const left = document.createElement('div');
      const h3 = document.createElement('h3');
      h3.textContent = item.english ? `${item.name} / ${item.english}` : item.name;
      const note = document.createElement('div');
      note.className = 'ingredients';
      note.textContent = cat.subtitle;
      left.append(h3, note);
      const price = document.createElement('div');
      price.className = 'price';
      price.textContent = item.price;
      row.append(left, price);
      section.appendChild(row);
    });
    host.appendChild(section);
  });
}
