'use strict';
(() => {
  const slides = Array.from(document.querySelectorAll('.slide'));
  const select = document.getElementById('slide-select');
  const previous = document.getElementById('previous');
  const next = document.getElementById('next');
  let index = 0;
  slides.forEach((slide, i) => {
    const option = document.createElement('option');
    option.value = String(i);
    option.textContent = `${i + 1}. ${slide.dataset.label}`;
    select.append(option);
  });
  function render(focus = false) {
    const match = slides.findIndex(slide => `#${slide.id}` === location.hash);
    index = match >= 0 ? match : 0;
    slides.forEach((slide, i) => { slide.hidden = i !== index; });
    select.value = String(index);
    previous.disabled = index === 0;
    next.disabled = index === slides.length - 1;
    document.getElementById('slide-counter').textContent = `${index + 1} / ${slides.length}`;
    document.title = `${slides[index].dataset.label} · Workshop abierto`;
    if (focus) {
      slides[index].querySelector('h1,h2').focus({preventScroll: true});
      window.scrollTo({top: 0, behavior: 'instant'});
    }
  }
  function go(i) { if (i >= 0 && i < slides.length) location.hash = slides[i].id; }
  previous.addEventListener('click', () => go(index - 1));
  next.addEventListener('click', () => go(index + 1));
  select.addEventListener('change', () => go(Number(select.value)));
  document.getElementById('print').addEventListener('click', () => window.print());
  window.addEventListener('hashchange', () => render(true));
  document.addEventListener('keydown', event => {
    if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey || /INPUT|TEXTAREA|SELECT|BUTTON/.test(event.target.tagName) || event.target.isContentEditable) return;
    if (event.key === 'ArrowRight') { event.preventDefault(); go(index + 1); }
    if (event.key === 'ArrowLeft') { event.preventDefault(); go(index - 1); }
  });
  document.querySelector('.deck-controls').hidden = false;
  document.body.classList.add('js-deck');
  render();
})();
