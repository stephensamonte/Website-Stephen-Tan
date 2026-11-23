/* Navigation drawer — replaces the stacked mobile nav at <=768px.
   Injects #nav-toggle, #nav-drawer (flat, accessible list rebuilt from the
   existing <nav aria-label="Primary">), and .nav-scrim. The desktop nav and
   its CSS-only dropdowns are left untouched. */
(function () {
  'use strict';

  var header = document.querySelector('.site-header');
  var source = header ? header.querySelector('nav[aria-label="Primary"] ul.nav') : null;
  if (!header || !source) return;

  /* ---------------- build the drawer list from the existing nav ---------------- */

  var drawer = document.createElement('div');
  drawer.id = 'nav-drawer';
  drawer.className = 'nav-drawer';
  drawer.setAttribute('role', 'dialog');
  drawer.setAttribute('aria-modal', 'true');
  drawer.setAttribute('aria-label', 'Site navigation');

  function linkFrom(a) {
    var el = document.createElement('a');
    el.className = 'nav-drawer-link';
    el.href = a.getAttribute('href');
    el.textContent = a.textContent.trim();
    return el;
  }

  function headingFrom(text) {
    var el = document.createElement('p');
    el.className = 'nav-drawer-group';
    el.textContent = text.replace(/\u2026+$/, '').trim();
    return el;
  }

  /* Flatten one <ul> (a .dropdown or a nested group list) into drawer rows. */
  function appendList(ul, dest) {
    var lis = Array.prototype.slice.call(ul.children);
    for (var i = 0; i < lis.length; i++) {
      var li = lis[i];
      if (li.tagName !== 'LI') continue;
      var a = null;
      var label = null;
      var nested = null;
      var kids = Array.prototype.slice.call(li.children);
      for (var j = 0; j < kids.length; j++) {
        var c = kids[j];
        if (c.tagName === 'A' && !a) a = c;
        else if (c.classList.contains('group-label') && !label) label = c;
        else if (c.tagName === 'UL' && !nested) nested = c;
      }
      if (a) dest.appendChild(linkFrom(a));
      if (label) dest.appendChild(headingFrom(label.textContent));
      if (nested) appendList(nested, dest);
    }
  }

  Array.prototype.slice.call(source.children).forEach(function (li) {
    var a = null;
    var label = null;
    var dropdown = null;
    var kids = Array.prototype.slice.call(li.children);
    for (var j = 0; j < kids.length; j++) {
      var c = kids[j];
      if (c.tagName === 'A' && !a) a = c;
      else if (c.classList.contains('nav-label') && !label) label = c;
      else if (c.classList.contains('dropdown') && !dropdown) dropdown = c;
    }
    if (a) drawer.appendChild(linkFrom(a));
    if (dropdown) {
      if (label) drawer.appendChild(headingFrom(label.textContent));
      appendList(dropdown, drawer);
    }
  });

  /* ---------------- toggle button, scrim, mount ---------------- */

  var toggle = document.createElement('button');
  toggle.type = 'button';
  toggle.id = 'nav-toggle';
  toggle.className = 'nav-toggle';
  toggle.setAttribute('aria-expanded', 'false');
  toggle.setAttribute('aria-controls', 'nav-drawer');
  toggle.setAttribute('aria-label', 'Open menu');
  var bars = document.createElement('span');
  bars.className = 'nav-toggle-bars';
  bars.setAttribute('aria-hidden', 'true');
  toggle.appendChild(bars);
  header.appendChild(toggle);

  var scrim = document.createElement('div');
  scrim.className = 'nav-scrim';
  scrim.setAttribute('aria-hidden', 'true');

  document.body.appendChild(scrim);
  document.body.appendChild(drawer);

  /* ---------------- open / close behavior ---------------- */

  function isOpen() {
    return toggle.getAttribute('aria-expanded') === 'true';
  }

  function setOpen(open) {
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    drawer.classList.toggle('open', open);
    scrim.classList.toggle('open', open);
    document.body.classList.toggle('nav-open', open);
    if (open) {
      var first = drawer.querySelector('a[href]');
      if (first) first.focus();
    } else {
      toggle.focus();
    }
  }

  toggle.addEventListener('click', function () {
    setOpen(!isOpen());
  });

  scrim.addEventListener('click', function () {
    setOpen(false);
  });

  drawer.addEventListener('click', function (e) {
    var t = e.target;
    if (t && t.closest && t.closest('a')) setOpen(false); /* navigation proceeds */
  });

  document.addEventListener('keydown', function (e) {
    if (!isOpen()) return;
    if (e.key === 'Escape') {
      setOpen(false);
      return;
    }
    if (e.key === 'Tab') { /* keep keyboard focus cycling inside the drawer */
      var focusables = drawer.querySelectorAll('a[href]');
      if (!focusables.length) return;
      var first = focusables[0];
      var last = focusables[focusables.length - 1];
      var active = document.activeElement;
      if (e.shiftKey && (active === first || !drawer.contains(active))) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && active === last) {
        e.preventDefault();
        first.focus();
      }
    }
  });
})();
