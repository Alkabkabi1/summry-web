(function () {
  const bar = document.createElement('div');
  bar.className = 'progress-bar';
  document.body.prepend(bar);

  window.addEventListener('scroll', () => {
    const h = document.documentElement;
    const pct = (h.scrollTop / (h.scrollHeight - h.clientHeight)) * 100;
    bar.style.width = pct + '%';
  });

  const navLinks = document.querySelectorAll('.nav-list a');
  const sections = [...navLinks].map(a => document.querySelector(a.getAttribute('href'))).filter(Boolean);

  const observer = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          navLinks.forEach(l => l.classList.remove('active'));
          const link = document.querySelector('.nav-list a[href="#' + entry.target.id + '"]');
          if (link) link.classList.add('active');
        }
      });
    },
    { rootMargin: '-30% 0px -60% 0px' }
  );
  sections.forEach(s => observer.observe(s));

  document.querySelectorAll('.flashcard').forEach(card => {
    card.addEventListener('click', () => card.classList.toggle('flipped'));
  });

  document.querySelectorAll('.reveal-answers').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.answer-key.hidden').forEach(el => el.classList.remove('hidden'));
      btn.textContent = 'Answers visible';
      btn.disabled = true;
    });
  });
})();
