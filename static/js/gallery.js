/* ============================================================
   RAMBLING ROVER — Gallery, Nav, Tabs, Filters
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {

  /* ---- MOBILE NAV --------------------------------------- */
  const toggle = document.querySelector('.nav-toggle');
  const links  = document.querySelector('.nav-links');
  if (toggle && links) {
    toggle.addEventListener('click', function () {
      links.classList.toggle('open');
      document.body.style.overflow = links.classList.contains('open') ? 'hidden' : '';
    });
    // Close on link click
    links.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () {
        links.classList.remove('open');
        document.body.style.overflow = '';
      });
    });
  }

  /* ---- ACTIVE NAV LINK ---------------------------------- */
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-links a').forEach(function (a) {
    if (a.getAttribute('href') && currentPath.startsWith(a.getAttribute('href')) && a.getAttribute('href') !== '/') {
      a.classList.add('active');
    } else if (currentPath === '/' && a.getAttribute('href') === '/') {
      a.classList.add('active');
    }
  });

  /* ---- LIGHTBOX ----------------------------------------- */
  const lightbox = document.querySelector('.lightbox');
  const lbImg    = document.querySelector('.lightbox__img');
  const lbCap    = document.querySelector('.lightbox__caption');
  const lbClose  = document.querySelector('.lightbox__close');
  const lbPrev   = document.querySelector('.lightbox__prev');
  const lbNext   = document.querySelector('.lightbox__next');

  let galleryItems = [];
  let currentIdx = 0;

  function openLightbox(idx) {
    currentIdx = idx;
    const item = galleryItems[idx];
    if (!item) return;
    const img = item.querySelector('img');
    const cap = item.querySelector('.gallery-caption');
    lbImg.src = img.dataset.full || img.src;
    lbImg.alt = img.alt;
    if (lbCap) lbCap.textContent = cap ? cap.textContent : img.alt;
    lightbox.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeLightbox() {
    lightbox.classList.remove('open');
    document.body.style.overflow = '';
    lbImg.src = '';
  }

  function navigate(dir) {
    currentIdx = (currentIdx + dir + galleryItems.length) % galleryItems.length;
    openLightbox(currentIdx);
  }

  if (lightbox) {
    galleryItems = Array.from(document.querySelectorAll('.gallery-item'));
    galleryItems.forEach(function (item, idx) {
      item.addEventListener('click', function () { openLightbox(idx); });
    });
    if (lbClose) lbClose.addEventListener('click', closeLightbox);
    lightbox.addEventListener('click', function (e) {
      if (e.target === lightbox) closeLightbox();
    });
    if (lbPrev) lbPrev.addEventListener('click', function () { navigate(-1); });
    if (lbNext) lbNext.addEventListener('click', function () { navigate(1); });
    document.addEventListener('keydown', function (e) {
      if (!lightbox.classList.contains('open')) return;
      if (e.key === 'Escape') closeLightbox();
      if (e.key === 'ArrowLeft')  navigate(-1);
      if (e.key === 'ArrowRight') navigate(1);
    });
  }

  /* ---- LOCATION TABS ------------------------------------ */
  document.querySelectorAll('.location-tab').forEach(function (tab) {
    tab.addEventListener('click', function () {
      const target = this.dataset.tab;
      document.querySelectorAll('.location-tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      this.classList.add('active');
      const panel = document.getElementById('tab-' + target);
      if (panel) panel.classList.add('active');
    });
  });

  /* ---- POST FILTER (blog list page) --------------------- */
  const filterBtns = document.querySelectorAll('.filter-btn[data-filter]');
  const postRows   = document.querySelectorAll('.post-row[data-cats]');

  filterBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      const filter = this.dataset.filter;
      filterBtns.forEach(b => b.classList.remove('active'));
      this.classList.add('active');

      postRows.forEach(function (row) {
        if (filter === 'all') {
          row.style.display = '';
        } else {
          const cats = (row.dataset.cats || '').toLowerCase();
          row.style.display = cats.includes(filter.toLowerCase()) ? '' : 'none';
        }
      });
    });
  });

  /* ---- LOCATION CONTINENT FILTER ----------------------- */
  const contBtns = document.querySelectorAll('.filter-btn[data-continent]');
  const locCards = document.querySelectorAll('.location-card[data-continent]');

  contBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      const filter = this.dataset.continent;
      contBtns.forEach(b => b.classList.remove('active'));
      this.classList.add('active');

      locCards.forEach(function (card) {
        if (filter === 'all') {
          card.style.display = '';
        } else {
          card.style.display = card.dataset.continent === filter ? '' : 'none';
        }
      });
    });
  });

  /* ---- LAZY-LOAD IMAGES --------------------------------- */
  if ('IntersectionObserver' in window) {
    const lazyImgs = document.querySelectorAll('img[data-src]');
    const imgObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          if (img.dataset.srcset) img.srcset = img.dataset.srcset;
          imgObserver.unobserve(img);
        }
      });
    }, { rootMargin: '200px' });
    lazyImgs.forEach(function (img) { imgObserver.observe(img); });
  }

  /* ---- SCROLL PROGRESS BAR ------------------------------ */
  const progressBar = document.getElementById('reading-progress');
  if (progressBar) {
    window.addEventListener('scroll', function () {
      const el   = document.documentElement;
      const top  = el.scrollTop  || document.body.scrollTop;
      const h    = el.scrollHeight - el.clientHeight;
      const pct  = h > 0 ? (top / h) * 100 : 0;
      progressBar.style.width = Math.min(pct, 100) + '%';
    });
  }

});
