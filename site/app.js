/* ============================================================
   蛮吉 · manji — GitHub Pages 首页脚本
   源文件；由 scripts/build-site.py 内联进 _site/index.html
   无依赖，纯 DOM API。
   ============================================================ */
(function () {
  'use strict';

  /* ---------- 主题：light / dark / system ---------- */
  var STORE_KEY = 'manji-theme';
  var mql = window.matchMedia('(prefers-color-scheme: dark)');

  function readPref() {
    try {
      var v = localStorage.getItem(STORE_KEY);
      return v === 'light' || v === 'dark' || v === 'system' ? v : 'system';
    } catch (e) {
      return 'system';
    }
  }

  function applyTheme(pref) {
    var resolved = pref === 'system' ? (mql.matches ? 'dark' : 'light') : pref;
    document.documentElement.setAttribute('data-theme', resolved);
    document.documentElement.setAttribute('data-theme-pref', pref);
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', resolved === 'dark' ? '#100e0d' : '#fbf9f7');
    document.querySelectorAll('.theme-switch button').forEach(function (b) {
      b.setAttribute('aria-pressed', String(b.dataset.theme === pref));
    });
  }

  function setTheme(pref) {
    try { localStorage.setItem(STORE_KEY, pref); } catch (e) { /* 无痕模式：仅本次生效 */ }
    applyTheme(pref);
  }

  applyTheme(readPref());
  (mql.addEventListener ? mql.addEventListener.bind(mql, 'change') : mql.addListener.bind(mql))(
    function () { if (readPref() === 'system') applyTheme('system'); }
  );

  document.querySelectorAll('.theme-switch button').forEach(function (btn) {
    btn.addEventListener('click', function () { setTheme(btn.dataset.theme); });
  });

  /* ---------- 复制命令 ---------- */
  function fallbackCopy(text) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.cssText = 'position:fixed;top:-1000px;opacity:0';
    document.body.appendChild(ta);
    ta.select();
    var ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    return ok;
  }

  document.querySelectorAll('.copy').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var text = btn.getAttribute('data-copy') || '';
      var done = function (ok) {
        if (!ok) return;
        btn.setAttribute('data-copied', 'true');
        btn.setAttribute('aria-label', '已复制');
        setTimeout(function () {
          btn.removeAttribute('data-copied');
          btn.setAttribute('aria-label', '复制命令');
        }, 1800);
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(function () { done(true); }, function () {
          done(fallbackCopy(text));
        });
      } else {
        done(fallbackCopy(text));
      }
    });
  });

  /* ---------- 安装方式 Tab ---------- */
  document.querySelectorAll('[role="tablist"]').forEach(function (list) {
    var tabs = Array.prototype.slice.call(list.querySelectorAll('[role="tab"]'));
    function select(tab) {
      tabs.forEach(function (t) {
        var on = t === tab;
        t.setAttribute('aria-selected', String(on));
        t.tabIndex = on ? 0 : -1;
        var panel = document.getElementById(t.getAttribute('aria-controls'));
        if (panel) panel.hidden = !on;
      });
    }
    tabs.forEach(function (tab, i) {
      tab.addEventListener('click', function () { select(tab); });
      tab.addEventListener('keydown', function (e) {
        var d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
        if (!d) return;
        e.preventDefault();
        var next = tabs[(i + d + tabs.length) % tabs.length];
        select(next);
        next.focus();
      });
    });
  });

  /* ---------- 插件搜索 + 分类过滤 ---------- */
  var input = document.getElementById('plugin-search');
  var cards = Array.prototype.slice.call(document.querySelectorAll('.card[data-haystack]'));
  var chips = Array.prototype.slice.call(document.querySelectorAll('.filters button'));
  var empty = document.getElementById('catalog-empty');
  var count = document.getElementById('catalog-count');
  var activeCat = 'all';

  function applyFilter() {
    var q = (input ? input.value : '').trim().toLowerCase();
    var shown = 0;
    cards.forEach(function (card) {
      var okCat = activeCat === 'all' || card.dataset.category === activeCat;
      var okQ = !q || card.dataset.haystack.indexOf(q) !== -1;
      var visible = okCat && okQ;
      card.hidden = !visible;
      if (visible) shown++;
    });
    if (empty) empty.hidden = shown !== 0;
    if (count) count.textContent = String(shown);
  }

  if (input) {
    input.addEventListener('input', applyFilter);
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { input.value = ''; applyFilter(); }
    });
  }
  chips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      activeCat = chip.dataset.category;
      chips.forEach(function (c) { c.setAttribute('aria-pressed', String(c === chip)); });
      applyFilter();
    });
  });
  applyFilter();

  /* ---------- 导航吸顶阴影 ---------- */
  var nav = document.querySelector('.nav');
  if (nav) {
    var onScroll = function () {
      nav.setAttribute('data-stuck', String(window.scrollY > 8));
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ---------- 滚动渐入 ---------- */
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var targets = document.querySelectorAll('.reveal');
  if (reduce || !('IntersectionObserver' in window)) {
    targets.forEach(function (el) { el.classList.add('in'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('in');
        io.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.05 });
    targets.forEach(function (el) { io.observe(el); });
  }
})();
