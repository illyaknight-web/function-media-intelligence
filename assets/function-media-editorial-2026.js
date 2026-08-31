/* Progressive editorial enhancement for Function Media LLC. */
(() => {
  const labels = {
    company: 'FUNCTION MEDIA / COMPANY',
    platforms: 'FUNCTION MEDIA / PLATFORMS',
    principles: 'FUNCTION MEDIA / PRINCIPLES',
    capability: 'VERISCOPE CYBER / CAPABILITY',
    about: 'FUNCTION MEDIA / PROFILE',
    contact: 'FUNCTION MEDIA / CONTACT'
  };
  Object.entries(labels).forEach(([id,label]) => {
    const el = document.getElementById(id);
    if (el) el.dataset.editorialMark = label;
  });

  // Add restrained depth only to existing hero media. No content is replaced.
  const heroVisual = document.querySelector('.hero-visual');
  if (!heroVisual || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  let raf = 0;
  const update = () => {
    raf = 0;
    const r = heroVisual.getBoundingClientRect();
    const center = r.top + r.height / 2;
    const delta = (center - innerHeight / 2) / innerHeight;
    heroVisual.style.transform = `translate3d(0,${Math.max(-12,Math.min(12,-delta*18))}px,0)`;
  };
  addEventListener('scroll', () => { if (!raf) raf = requestAnimationFrame(update); }, {passive:true});
  update();
})();
