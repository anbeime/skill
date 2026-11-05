// Keep local gallery navigation in the browser that is displaying the page.
if (location.protocol === 'file:') {
  document.querySelectorAll('.site-nav a[href]').forEach(link => {
    const destination = new URL(link.href);
    if (destination.protocol !== 'file:' || !destination.pathname.endsWith('.html')) return;

    // A file href can be intercepted by the host and opened as a source preview.
    link.removeAttribute('href');
    link.setAttribute('role', 'link');
    link.tabIndex = 0;
    link.style.cursor = 'pointer';
    link.addEventListener('click', () => location.assign(destination.href));
    link.addEventListener('keydown', event => {
      if (event.key === 'Enter') location.assign(destination.href);
    });
  });
}
