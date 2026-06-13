/* ================================================
   BCMS PWA — Install Prompt
   ================================================ */
(function () {
  'use strict';

  var DISMISS_KEY  = 'bcms_pwa_dismissed_until';
  var INSTALLED_KEY = 'bcms_pwa_installed';
  var SHOW_DELAY   = 3000;  // ms after page load

  var deferredPrompt = null;
  var banner = null;

  /* ── helpers ───────────────────────────────── */
  function isDismissed() {
    var until = localStorage.getItem(DISMISS_KEY);
    return until && Date.now() < parseInt(until, 10);
  }
  function dismiss(days) {
    var ms = (days || 7) * 24 * 60 * 60 * 1000;
    localStorage.setItem(DISMISS_KEY, Date.now() + ms);
  }
  function isInstalled() {
    return localStorage.getItem(INSTALLED_KEY) === '1'
      || window.matchMedia('(display-mode: standalone)').matches
      || window.navigator.standalone === true;
  }
  function isIOS() {
    return /iphone|ipad|ipod/i.test(navigator.userAgent) && !window.MSStream;
  }
  function isInStandaloneMode() {
    return window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone;
  }

  /* ── register service worker ───────────────── */
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('/sw.js', { scope: '/' })
        .then(function (reg) { console.log('[PWA] SW registered, scope:', reg.scope); })
        .catch(function (err) { console.warn('[PWA] SW error:', err); });
    });
  }

  /* ── catch install prompt ───────────────────── */
  window.addEventListener('beforeinstallprompt', function (e) {
    e.preventDefault();
    deferredPrompt = e;
    if (!isDismissed() && !isInstalled()) {
      setTimeout(showBanner, SHOW_DELAY);
    }
  });

  window.addEventListener('appinstalled', function () {
    localStorage.setItem(INSTALLED_KEY, '1');
    hideBanner();
  });

  /* ── iOS: show after delay if not standalone ─ */
  window.addEventListener('DOMContentLoaded', function () {
    if (isIOS() && !isInStandaloneMode() && !isDismissed() && !isInstalled()) {
      setTimeout(showIOSBanner, SHOW_DELAY);
    }
  });

  /* ── build & show banner ────────────────────── */
  function showBanner() {
    if (banner || isDismissed() || isInstalled()) return;
    banner = buildBanner(false);
    document.body.appendChild(banner);
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        banner.classList.add('pwa-banner--visible');
      });
    });
  }

  function showIOSBanner() {
    if (banner || isDismissed() || isInstalled()) return;
    banner = buildBanner(true);
    document.body.appendChild(banner);
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        banner.classList.add('pwa-banner--visible');
      });
    });
  }

  function hideBanner() {
    if (!banner) return;
    banner.classList.remove('pwa-banner--visible');
    setTimeout(function () {
      if (banner && banner.parentNode) banner.parentNode.removeChild(banner);
      banner = null;
    }, 380);
  }

  function buildBanner(ios) {
    var el = document.createElement('div');
    el.className = 'pwa-banner';
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-label', 'تثبيت التطبيق');

    var appName = document.title.split('—')[1] || 'BCMS';
    appName = appName.trim() || 'BCMS';

    if (ios) {
      el.innerHTML = [
        '<div class="pwa-banner__inner">',
        '  <div class="pwa-banner__icon">',
        '    <i class="fas fa-mobile-alt"></i>',
        '  </div>',
        '  <div class="pwa-banner__body">',
        '    <div class="pwa-banner__title">أضف التطبيق للشاشة الرئيسية</div>',
        '    <div class="pwa-banner__ios-steps">',
        '      <span class="pwa-ios-step"><i class="fas fa-share-from-square"></i> اضغط زر المشاركة</span>',
        '      <span class="pwa-ios-arrow"><i class="fas fa-arrow-left"></i></span>',
        '      <span class="pwa-ios-step"><i class="fas fa-plus-square"></i> أضف إلى الشاشة الرئيسية</span>',
        '    </div>',
        '  </div>',
        '  <button class="pwa-banner__close" aria-label="إغلاق"><i class="fas fa-times"></i></button>',
        '</div>',
      ].join('');

      el.querySelector('.pwa-banner__close').addEventListener('click', function () {
        dismiss(7);
        hideBanner();
      });

    } else {
      el.innerHTML = [
        '<div class="pwa-banner__inner">',
        '  <div class="pwa-banner__icon">',
        '    <i class="fas fa-spa"></i>',
        '  </div>',
        '  <div class="pwa-banner__body">',
        '    <div class="pwa-banner__title">ثبّت التطبيق</div>',
        '    <div class="pwa-banner__desc">وصول سريع بدون متصفح · يعمل بدون إنترنت</div>',
        '  </div>',
        '  <div class="pwa-banner__actions">',
        '    <button class="pwa-banner__btn pwa-banner__btn--install">',
        '      <i class="fas fa-download"></i> تثبيت',
        '    </button>',
        '    <button class="pwa-banner__btn pwa-banner__btn--later">لاحقاً</button>',
        '  </div>',
        '  <button class="pwa-banner__close" aria-label="إغلاق"><i class="fas fa-times"></i></button>',
        '</div>',
      ].join('');

      el.querySelector('.pwa-banner__btn--install').addEventListener('click', function () {
        if (!deferredPrompt) return;
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then(function (result) {
          if (result.outcome === 'accepted') {
            localStorage.setItem(INSTALLED_KEY, '1');
          } else {
            dismiss(3);
          }
          deferredPrompt = null;
          hideBanner();
        });
      });

      el.querySelector('.pwa-banner__btn--later').addEventListener('click', function () {
        dismiss(7);
        hideBanner();
      });

      el.querySelector('.pwa-banner__close').addEventListener('click', function () {
        dismiss(30);
        hideBanner();
      });
    }

    return el;
  }

})();
