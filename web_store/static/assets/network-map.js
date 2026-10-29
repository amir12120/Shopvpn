(function () {
  'use strict';

  /* نقشه‌ی زنده‌ی شبکه — نسخه‌ی فروشگاه (هم‌شکل با «نقشه زنده شبکه» پنل ادمین).
     نکته CSP: style-src 'self' است؛ پس هیچ style="" داخل HTML نمی‌نویسیم و
     موقعیت‌ها را با el.style (CSSOM) ست می‌کنیم. */

  var LS_SET = 'sv-netmap-settings-v1';
  var LS_LAND = 'sv-netmap-land-v1';
  var W = 1000;
  var B = { L: -120, R: 162, T: 76, B: -58 };
  var MOBILE_MQ = '(max-width:720px)';

  /* ------------------------------------------------------------ flags --- */
  var FLAGS = {
    ir: '<rect width="24" height="8" fill="#239f40"/><rect y="8" width="24" height="8" fill="#fff"/><rect y="16" width="24" height="8" fill="#da0000"/><circle cx="12" cy="12" r="2.2" fill="none" stroke="#da0000" stroke-width="1.2"/>',
    tr: '<rect width="24" height="24" fill="#e30a17"/><circle cx="10" cy="12" r="5.6" fill="#fff"/><circle cx="11.8" cy="12" r="4.5" fill="#e30a17"/><circle cx="15.6" cy="12" r="1.5" fill="#fff"/>',
    ae: '<rect width="24" height="8" fill="#00732f"/><rect y="8" width="24" height="8" fill="#fff"/><rect y="16" width="24" height="8" fill="#000"/><rect width="7" height="24" fill="#f00"/>',
    de: '<rect width="24" height="8" fill="#000"/><rect y="8" width="24" height="8" fill="#d00"/><rect y="16" width="24" height="8" fill="#ffce00"/>',
    nl: '<rect width="24" height="8" fill="#ae1c28"/><rect y="8" width="24" height="8" fill="#fff"/><rect y="16" width="24" height="8" fill="#21468b"/>',
    gb: '<rect width="24" height="24" fill="#012169"/><path d="M0 0l24 24M24 0L0 24" stroke="#fff" stroke-width="4.5"/><path d="M0 0l24 24M24 0L0 24" stroke="#c8102e" stroke-width="1.6"/><path d="M12 0v24M0 12h24" stroke="#fff" stroke-width="7"/><path d="M12 0v24M0 12h24" stroke="#c8102e" stroke-width="4"/>',
    us: '<rect width="24" height="24" fill="#fff"/><g fill="#b22234"><rect y="0" width="24" height="3.4"/><rect y="6.9" width="24" height="3.4"/><rect y="13.7" width="24" height="3.4"/><rect y="20.6" width="24" height="3.4"/></g><rect width="12" height="13.7" fill="#3c3b6e"/>',
    jp: '<rect width="24" height="24" fill="#fff"/><circle cx="12" cy="12" r="6.6" fill="#bc002d"/>',
    sg: '<rect width="24" height="12" fill="#ef3340"/><rect y="12" width="24" height="12" fill="#fff"/><circle cx="8.2" cy="6" r="3.6" fill="#fff"/><circle cx="9.8" cy="6" r="3.2" fill="#ef3340"/>',
    br: '<rect width="24" height="24" fill="#009c3b"/><path d="M12 3l10 9-10 9L2 12z" fill="#ffdf00"/><circle cx="12" cy="12" r="4.6" fill="#002776"/><path d="M7.6 11.2q4.4-1.6 8.8 1.6" fill="none" stroke="#fff" stroke-width="1"/>'
  };
  function flag(cc) {
    return '<span class="nm-flag"><svg viewBox="0 0 24 24" aria-hidden="true">' + (FLAGS[cc] || '') + '</svg></span>';
  }

  /* ------------------------------------------------------------ icons --- */
  var ICON = {
    globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.6 2.8 3.9 5.8 3.9 9s-1.3 6.2-3.9 9c-2.6-2.8-3.9-5.8-3.9-9S9.4 5.8 12 3z"/>',
    cloudUp: '<path d="M7 18a4.5 4.5 0 0 1-.6-8.96A6 6 0 0 1 18 8.5a4 4 0 0 1 .5 7.97"/><path d="M12 20v-7m0 0-3 3m3-3 3 3"/>',
    cloudOff: '<path d="M7 18a4.5 4.5 0 0 1-.6-8.96A6 6 0 0 1 18 8.5a4 4 0 0 1 .5 7.97"/><path d="m10 12 4 4m0-4-4 4"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    swap: '<path d="M7 7h12m0 0-3-3m3 3-3 3M17 17H5m0 0 3-3m-3 3 3 3"/>',
    search: '<circle cx="11" cy="11" r="6.5"/><path d="m16 16 4 4"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    minus: '<path d="M5 12h14"/>',
    locate: '<circle cx="12" cy="12" r="3.2"/><circle cx="12" cy="12" r="7.5"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>',
    refresh: '<path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4v7h-7"/>',
    save: '<path d="M5 4h11l3 3v13H5z"/><path d="M8 4v5h7V4M8 20v-6h8v6"/>',
    arrow: '<path d="M5 12h14m0 0-5-5m5 5-5 5"/>'
  };
  function icon(n) {
    return '<svg class="nm-i" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + ICON[n] + '</svg>';
  }

  /* ------------------------------------------------------------- data --- */
  // st: ok | warn  — a: جهت برچسب روی نقشه — end: رنگ انتهای مسیر (اختیاری)
  var SERVERS = [
    { id: 'tehran', cc: 'ir', city: 'Tehran', fa: 'تهران', lat: 35.69, lon: 51.39, ping: 12, loss: 0.1, thr: 2400, st: 'ok', a: 'tr', hub: true },
    { id: 'istanbul', cc: 'tr', city: 'Istanbul', fa: 'استانبول', lat: 41.01, lon: 28.98, ping: 34, loss: 0.1, thr: 900, st: 'ok', a: '' },
    { id: 'dubai', cc: 'ae', city: 'Dubai', fa: 'دبی', lat: 25.2, lon: 55.27, ping: 48, loss: 0.2, thr: 950, st: 'ok', a: 'br' },
    { id: 'frankfurt', cc: 'de', city: 'Frankfurt', fa: 'فرانکفورت', lat: 50.11, lon: 8.68, ping: 52, loss: 0.2, thr: 1200, st: 'ok', a: 'tr' },
    { id: 'amsterdam', cc: 'nl', city: 'Amsterdam', fa: 'آمستردام', lat: 52.37, lon: 4.9, ping: 56, loss: 0.3, thr: 1100, st: 'ok', a: 'bl' },
    { id: 'london', cc: 'gb', city: 'London', fa: 'لندن', lat: 51.51, lon: -0.13, ping: 68, loss: 0.4, thr: 800, st: 'ok', a: 'tl' },
    { id: 'newyork', cc: 'us', city: 'New York', fa: 'نیویورک', lat: 40.71, lon: -74.0, ping: 82, loss: 0.5, thr: 700, st: 'ok', a: 'r' },
    { id: 'tokyo', cc: 'jp', city: 'Tokyo', fa: 'توکیو', lat: 35.68, lon: 139.69, ping: 112, loss: 1.1, thr: 400, st: 'warn', a: 't', end: '#ff4d5e' },
    { id: 'singapore', cc: 'sg', city: 'Singapore', fa: 'سنگاپور', lat: 1.35, lon: 103.82, ping: 96, loss: 0.8, thr: 520, st: 'warn', a: 'tr' },
    { id: 'saopaulo', cc: 'br', city: 'São Paulo', fa: 'سائوپائولو', lat: -23.55, lon: -46.63, ping: 138, loss: 1.4, thr: 350, st: 'warn', a: 'r' }
  ];
  SERVERS.forEach(function (s) { s.base = s.ping; });
  var BY = {};
  SERVERS.forEach(function (s) { BY[s.id] = s; });
  var HUB = BY.tehran;
  var ROUTE_IDS = ['frankfurt', 'amsterdam', 'istanbul', 'london'];
  var BACKUP = [['istanbul', 'frankfurt'], ['frankfurt', 'london'], ['dubai', 'singapore'], ['london', 'newyork']];

  /* ------------------------------------------------------------- text --- */
  var TXT = {
    fa: {
      title: 'نقشه زنده شبکه', sub: 'مسیرهای واقعی از ایران به سرورهای خارج | پینگ زنده و وضعیت گره‌ها',
      upd: 'آخرین بروزرسانی', sec: 'ثانیه', min: 'دقیقه', traffic: 'ترافیک کل', avg: 'میانگین پینگ', off: 'گره‌های آفلاین', on: 'گره‌های آنلاین',
      list: 'لیست سرورها', search: 'جستجوی سرور...', empty: 'سروری پیدا نشد',
      lgOk: 'مسیر فعال', lgWarn: 'مسیر با تأخیر', lgDown: 'مسیر قطع شده', lgOn: 'گره آنلاین', lgOff: 'گره آفلاین',
      zin: 'بزرگ‌نمایی', zout: 'کوچک‌نمایی', zhome: 'مرکز نقشه',
      det: 'جزئیات مسیر انتخابی', active: 'فعال', slow: 'با تأخیر', ping: 'پینگ', lat: 'تأخیر (Latency)', loss: 'افت بسته', speed: 'سرعت فعلی',
      chart: 'نمودار پینگ (آخرین ۵ دقیقه)', routes: 'مسیرهای موجود', rec: 'پیشنهادی', cap: 'ظرفیت',
      set: 'تنظیمات نمایش', sPing: 'نمایش پینگ', sTraf: 'نمایش ترافیک', sBack: 'نمایش مسیرهای پشتیبان', sAnim: 'سرعت انیمیشن بسته‌ها',
      speeds: ['کند', 'متوسط', 'سریع'], auto: 'بروزرسانی خودکار', save: 'ذخیره تنظیمات', saved: 'ذخیره شد',
      note: 'اعداد این بخش نمایشی هستند و برای نمایش حالت زنده به‌صورت دوره‌ای تغییر می‌کنند.'
    },
    en: {
      title: 'Live Network Map', sub: 'Real routes from Iran to overseas servers | Live ping and node status',
      upd: 'Last update', sec: 's', min: 'min', traffic: 'Total traffic', avg: 'Average ping', off: 'Offline nodes', on: 'Online nodes',
      list: 'Servers', search: 'Search servers...', empty: 'No server found',
      lgOk: 'Active route', lgWarn: 'Delayed route', lgDown: 'Disconnected route', lgOn: 'Online node', lgOff: 'Offline node',
      zin: 'Zoom in', zout: 'Zoom out', zhome: 'Center map',
      det: 'Selected route', active: 'Active', slow: 'Delayed', ping: 'Ping', lat: 'Latency', loss: 'Packet loss', speed: 'Current speed',
      chart: 'Ping chart (last 5 minutes)', routes: 'Available routes', rec: 'Recommended', cap: 'Capacity',
      set: 'Display settings', sPing: 'Show ping', sTraf: 'Show traffic', sBack: 'Show backup routes', sAnim: 'Packet animation speed',
      speeds: ['Slow', 'Medium', 'Fast'], auto: 'Auto refresh', save: 'Save settings', saved: 'Saved',
      note: 'Figures here are illustrative and change periodically to show the live view.'
    }
  };

  /* ---------------------------------------------------------- helpers --- */
  var rnd = Math.random;
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function hm(d) { return pad(d.getHours()) + ':' + pad(d.getMinutes()); }
  function fmtThr(mbps) { return mbps >= 1000 ? (mbps / 1000).toFixed(1).replace(/\.0$/, '') + ' Gbps' : Math.round(mbps) + ' Mbps'; }
  function mX(lon) { return lon * Math.PI / 180; }
  function mY(lat) { return 1.25 * Math.log(Math.tan(Math.PI / 4 + 0.4 * lat * Math.PI / 180)); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  function loadSettings() {
    var d = { ping: true, traffic: true, backup: true, speed: 2, refresh: 30 };
    try {
      var o = JSON.parse(localStorage.getItem(LS_SET) || 'null');
      if (o && typeof o === 'object') {
        if (typeof o.ping === 'boolean') d.ping = o.ping;
        if (typeof o.traffic === 'boolean') d.traffic = o.traffic;
        if (typeof o.backup === 'boolean') d.backup = o.backup;
        if (o.speed >= 1 && o.speed <= 3) d.speed = o.speed | 0;
        if ([15, 30, 60, 120].indexOf(o.refresh) > -1) d.refresh = o.refresh;
      }
    } catch (e) {}
    return d;
  }

  /* -------------------------------------------------------- land (geo) --- */
  var LAND = null;
  var landPromise = null;
  function parseLand(d) {
    var rings = [], re = /([MLZ])([^MLZ]*)/g, m, cur = null;
    while ((m = re.exec(d))) {
      if (m[1] === 'M') { cur = []; rings.push(cur); }
      if (m[1] === 'Z' || !cur) continue;
      var p = m[2].split(',');
      if (p.length >= 2) cur.push([parseFloat(p[0]) * 0.36 - 180, 90 - parseFloat(p[1]) * 0.36]);
    }
    return rings;
  }
  function ensureLand() {
    if (LAND) return Promise.resolve(LAND);
    if (landPromise) return landPromise;
    landPromise = new Promise(function (resolve) {
      try {
        var c = localStorage.getItem(LS_LAND);
        if (c) { LAND = parseLand(c); resolve(LAND); return; }
      } catch (e) {}
      function get(retry) {
        fetch('/api/web/world-map', { credentials: 'same-origin' }).then(function (r) { return r.json(); }).then(function (j) {
          if (j && j.ok && j.land_path) {
            try { localStorage.setItem(LS_LAND, j.land_path); } catch (e) {}
            LAND = parseLand(j.land_path);
            resolve(LAND);
          } else if (retry) { setTimeout(function () { get(false); }, 4000); } else { resolve(null); }
        }).catch(function () {
          if (retry) { setTimeout(function () { get(false); }, 4000); } else { resolve(null); }
        });
      }
      get(true);
    });
    return landPromise;
  }

  /* ----------------------------------------------------------- widget --- */
  function createNetworkMap() {
    var fa = document.documentElement.lang !== 'en';
    var T = fa ? TXT.fa : TXT.en;
    var set = loadSettings();
    var state = { sel: 'frankfurt', q: '', z: 1, tx: 0, ty: 0, series: [], H: 625, k: 0.8, last: new Date() };
    var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var mq = window.matchMedia ? window.matchMedia(MOBILE_MQ) : { matches: false };
    var timer = null;
    var pkCircles = [];

    var root = document.createElement('section');
    root.id = 'shopvpn-network-map';
    root.className = 'network-map-wrap home-network-map';
    root.setAttribute('aria-labelledby', 'network-map-title');

    function name(s) { return fa ? s.fa : s.city; }
    var MOB_A = { amsterdam: 'b', newyork: 'br', singapore: 'b' };
    function anchor(s) { return (mq.matches && MOB_A[s.id]) || s.a; }
    function tag(s) { return s.city + ' (' + s.cc.toUpperCase() + ')'; }

    root.innerHTML =
      '<div class="nm-app">' +
        '<header class="nm-head"><span class="nm-globe">' + icon('globe') + '</span><div><h2 id="network-map-title">' + T.title + '</h2><p>' + T.sub + '</p></div></header>' +
        '<div class="nm-stats">' +
          '<div class="nm-upd"><button class="nm-refresh" type="button" data-act="refresh">' + icon('refresh') + '<span data-k="interval"></span></button>' +
            '<div class="nm-upd-t"><small>' + T.upd + '</small><b data-k="time">--:--</b></div></div>' +
          '<div class="nm-stat s-blue" data-k="trafCard"><div class="nm-stat-t"><small>' + T.traffic + '</small><b data-k="traffic"></b></div><span class="nm-ico">' + icon('swap') + '</span></div>' +
          '<div class="nm-stat s-purple"><div class="nm-stat-t"><small>' + T.avg + '</small><b data-k="avg"></b></div><span class="nm-ico">' + icon('clock') + '</span></div>' +
          '<div class="nm-stat s-red"><div class="nm-stat-t"><small>' + T.off + '</small><b>2</b></div><span class="nm-ico">' + icon('cloudOff') + '</span></div>' +
          '<div class="nm-stat s-green"><div class="nm-stat-t"><small>' + T.on + '</small><b>12 / 14</b></div><span class="nm-ico">' + icon('cloudUp') + '</span></div>' +
        '</div>' +
        '<div class="nm-main">' +
          '<aside class="nm-card nm-list"><h3>' + T.list + '</h3>' +
            '<label class="nm-search"><input type="search" data-k="q" placeholder="' + T.search + '" autocomplete="off" aria-label="' + T.search + '">' + icon('search') + '</label>' +
            '<div class="nm-list-scroll"><ul data-k="list"></ul></div></aside>' +
          '<div class="nm-card nm-mapcard"><div class="nm-map" data-k="map">' +
            '<div class="nm-stage" data-k="stage"><svg class="nm-svg" data-k="svg" preserveAspectRatio="none" aria-hidden="true"></svg><div class="nm-nodes" data-k="nodes"></div></div>' +
            '<div class="nm-zoom"><button type="button" data-act="zin" aria-label="' + T.zin + '">' + icon('plus') + '</button><button type="button" data-act="zout" aria-label="' + T.zout + '">' + icon('minus') + '</button>' +
              '<button type="button" class="loc" data-act="zhome" aria-label="' + T.zhome + '">' + icon('locate') + '</button></div>' +
          '</div>' +
          '<div class="nm-legend"><span><i class="lg l-ok"></i>' + T.lgOk + '</span><span><i class="lg l-warn"></i>' + T.lgWarn + '</span><span><i class="lg l-down"></i>' + T.lgDown + '</span>' +
              '<span><i class="lg n-on"></i>' + T.lgOn + '</span><span><i class="lg n-off"></i>' + T.lgOff + '</span></div>' +
          '</div>' +
        '</div>' +
        '<div class="nm-bottom">' +
          '<section class="nm-card nm-settings"><h3>' + T.set + '</h3>' +
            '<label class="nm-srow"><span>' + T.sPing + '</span><span class="nm-switch"><input type="checkbox" data-set="ping"><i></i></span></label>' +
            '<label class="nm-srow"><span>' + T.sTraf + '</span><span class="nm-switch"><input type="checkbox" data-set="traffic"><i></i></span></label>' +
            '<label class="nm-srow"><span>' + T.sBack + '</span><span class="nm-switch"><input type="checkbox" data-set="backup"><i></i></span></label>' +
            '<div class="nm-slide"><div class="nm-slide-h"><span>' + T.sAnim + '</span><em data-k="speedLbl"></em></div><input type="range" min="1" max="3" step="1" data-set="speed" aria-label="' + T.sAnim + '"></div>' +
            '<label class="nm-srow nm-sel"><span>' + T.auto + '</span><select data-set="refresh">' +
              [15, 30, 60, 120].map(function (n) { return '<option value="' + n + '">' + (n < 120 ? n + ' ' + T.sec : '2 ' + T.min) + '</option>'; }).join('') +
            '</select></label>' +
            '<button class="nm-save" type="button" data-act="save">' + icon('save') + '<span data-k="saveTxt">' + T.save + '</span></button></section>' +
          '<section class="nm-card nm-routes"><h3>' + T.routes + '</h3><div data-k="routes"></div></section>' +
          '<section class="nm-card nm-details"><div class="nm-det-h"><h3>' + T.det + '</h3><span class="nm-badge" data-k="badge"></span></div>' +
            '<div class="nm-chip" data-k="chip"></div>' +
            '<div class="nm-metrics" data-k="metrics"></div>' +
            '<div class="nm-chart"><small>' + T.chart + '</small><div class="nm-plot"><div class="nm-yax"><span>120</span><span>80</span><span>40</span><span>0</span></div>' +
              '<div class="nm-plot-in"><svg viewBox="0 0 300 100" preserveAspectRatio="none" aria-hidden="true" data-k="chartSvg"></svg></div></div>' +
              '<div class="nm-xax" data-k="xax"></div></div></section>' +
        '</div>' +
        '<p class="nm-note">' + T.note + '</p>' +
      '</div>';

    function $(k) { return root.querySelector('[data-k="' + k + '"]'); }
    var el = {
      map: $('map'), stage: $('stage'), svg: $('svg'), nodes: $('nodes'), list: $('list'), q: $('q'), routes: $('routes'),
      badge: $('badge'), chip: $('chip'), metrics: $('metrics'), chartSvg: $('chartSvg'), xax: $('xax'), time: $('time'),
      traffic: $('traffic'), avg: $('avg'), trafCard: $('trafCard'), interval: $('interval'), speedLbl: $('speedLbl'), saveTxt: $('saveTxt')
    };

    /* ------------------------------------------------- projection --- */
    var mxL = mX(B.L), mxR = mX(B.R), myT = mY(B.T), myB = mY(B.B);
    function proj(lon, lat) {
      return [(mX(lon) - mxL) / (mxR - mxL) * W, (myT - mY(lat)) / (myT - myB) * state.H];
    }
    function ctrl(a, b) {
      var mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2, dx = b[0] - a[0], dy = b[1] - a[1];
      var len = Math.sqrt(dx * dx + dy * dy) || 1, nx = -dy / len, ny = dx / len;
      if (ny > 0) { nx = -nx; ny = -ny; }
      var off = len * 0.22;
      return [mx + nx * off, my + ny * off];
    }
    function arc(a, b) {
      var c = ctrl(a, b);
      return 'M' + a[0].toFixed(1) + ',' + a[1].toFixed(1) + ' Q' + c[0].toFixed(1) + ',' + c[1].toFixed(1) + ' ' + b[0].toFixed(1) + ',' + b[1].toFixed(1);
    }

    /* ---------------------------------------------------- map layer --- */
    function landPathD() {
      if (!LAND) return '';
      var out = [], i, j, ring, pts, x, y, keep;
      for (i = 0; i < LAND.length; i++) {
        ring = LAND[i]; keep = false; pts = [];
        for (j = 0; j < ring.length; j++) {
          var lon = ring[j][0], lat = ring[j][1];
          if (lon > B.L - 12 && lon < B.R + 12 && lat > B.B - 12 && lat < B.T + 12) keep = true;
          var p = proj(lon, lat); x = p[0]; y = p[1];
          pts.push((j ? 'L' : 'M') + x.toFixed(1) + ',' + y.toFixed(1));
        }
        if (keep && pts.length > 2) out.push(pts.join('') + 'Z');
      }
      return out.join('');
    }

    function drawMap() {
      state.H = mq.matches ? 760 : 625;
      el.svg.setAttribute('viewBox', '0 0 ' + W + ' ' + state.H);
      var hub = proj(HUB.lon, HUB.lat);
      var h = '<defs>' +
        '<pattern id="nm-dots" patternUnits="userSpaceOnUse" width="7" height="7"><circle cx="3.5" cy="3.5" r="1" fill="#3f7ad8" fill-opacity=".5"/></pattern>' +
        '<filter id="nm-glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>';
      SERVERS.forEach(function (s) {
        if (s.hub) return;
        var p = proj(s.lon, s.lat);
        var stops = s.end ? '<stop offset="0" stop-color="#2de2a6"/><stop offset=".55" stop-color="#ffb23f"/><stop offset="1" stop-color="' + s.end + '"/>'
          : s.st === 'warn' ? '<stop offset="0" stop-color="#2de2a6"/><stop offset=".6" stop-color="#7fe27a"/><stop offset="1" stop-color="#ffb23f"/>'
          : '<stop offset="0" stop-color="#2de2a6"/><stop offset="1" stop-color="#3ff0c0"/>';
        h += '<linearGradient id="nm-g-' + s.id + '" gradientUnits="userSpaceOnUse" x1="' + hub[0].toFixed(1) + '" y1="' + hub[1].toFixed(1) + '" x2="' + p[0].toFixed(1) + '" y2="' + p[1].toFixed(1) + '">' + stops + '</linearGradient>';
      });
      h += '</defs><g class="nm-grid">';
      var lon, lat, p0, p1;
      for (lon = -120; lon <= 160; lon += 20) { p0 = proj(lon, B.T); p1 = proj(lon, B.B); h += '<line x1="' + p0[0].toFixed(1) + '" y1="0" x2="' + p1[0].toFixed(1) + '" y2="' + state.H + '"/>'; }
      for (lat = -40; lat <= 70; lat += 20) { p0 = proj(B.L, lat); h += '<line x1="0" y1="' + p0[1].toFixed(1) + '" x2="' + W + '" y2="' + p0[1].toFixed(1) + '"/>'; }
      h += '</g>';
      var d = landPathD();
      if (d) h += '<g class="nm-land"><path class="land-fill" d="' + d + '"/><path class="land-dots" d="' + d + '" fill="url(#nm-dots)"/></g>';
      h += '<g class="nm-backup" data-k="backupG">';
      BACKUP.forEach(function (pr) {
        var a = BY[pr[0]], b = BY[pr[1]];
        h += '<path d="' + arc(proj(a.lon, a.lat), proj(b.lon, b.lat)) + '"/>';
      });
      h += '</g><g class="nm-routes-g">';
      SERVERS.forEach(function (s) {
        if (s.hub) return;
        var p = proj(s.lon, s.lat), dd = arc(hub, p);
        h += '<path class="nm-route' + (s.id === state.sel ? ' sel' : '') + '" data-rid="' + s.id + '" d="' + dd + '" stroke="url(#nm-g-' + s.id + ')"/>';
      });
      h += '</g><g class="nm-packets" data-k="pkG">';
      if (!reduce) {
        var mul = [1.7, 1, 0.55][set.speed - 1];
        SERVERS.forEach(function (s, idx) {
          if (s.hub) return;
          var p = proj(s.lon, s.lat), dd = arc(hub, p), dur = (3.4 + (idx % 4) * 0.6) * mul;
          for (var n = 0; n < 3; n++) {
            h += '<circle class="nm-pk" r="3" fill="' + (s.st === 'warn' ? '#ffd089' : '#ffffff') + '" filter="url(#nm-glow)"><animateMotion dur="' + dur.toFixed(2) + 's" begin="-' + (n * dur / 3 + idx * 0.37).toFixed(2) + 's" repeatCount="indefinite" path="' + dd + '"/></circle>';
          }
        });
      }
      h += '</g>';
      el.svg.innerHTML = h;
      pkCircles = Array.prototype.slice.call(el.svg.querySelectorAll('.nm-pk'));
      applySvgPrefs();
      drawNodes();
    }

    function applySvgPrefs() {
      var b = el.svg.querySelector('.nm-backup'), pk = el.svg.querySelector('.nm-packets');
      if (b) b.style.display = set.backup ? '' : 'none';
      if (pk) pk.style.display = set.traffic ? '' : 'none';
      el.trafCard.style.display = set.traffic ? '' : 'none';
      sizePackets();
    }
    function sizePackets() {
      var w = el.map.clientWidth || 800;
      state.k = w / W;
      var r = (3.1 / state.k / state.z).toFixed(2);
      pkCircles.forEach(function (c) { c.setAttribute('r', r); });
    }

    function drawNodes() {
      var h = '';
      SERVERS.forEach(function (s) {
        var cls = 'nm-node' + (s.hub ? ' hub' : '') + (s.end ? ' bad' : s.st === 'warn' ? ' warn' : '') + (s.id === state.sel ? ' sel' : '');
        var an = anchor(s);
        var lab = an ? '<span class="nm-label a-' + an + '">' + flag(s.cc) + '<span class="nm-lt"><b>' + s.city + '</b><small data-ping="' + s.id + '"></small></span></span>' : '';
        h += '<button type="button" class="' + cls + '" data-node="' + s.id + '" data-lon="' + s.lon + '" data-lat="' + s.lat + '" aria-label="' + tag(s) + '">' +
          '<i class="nm-dot"></i>' + (s.hub ? '<i class="nm-ring r1"></i><i class="nm-ring r2"></i>' : '') + lab + '</button>';
      });
      el.nodes.innerHTML = h;
      Array.prototype.forEach.call(el.nodes.querySelectorAll('.nm-node'), function (n) {
        var p = proj(parseFloat(n.getAttribute('data-lon')), parseFloat(n.getAttribute('data-lat')));
        n.style.left = (p[0] / W * 100).toFixed(3) + '%';
        n.style.top = (p[1] / state.H * 100).toFixed(3) + '%';
      });
      paintLabels();
    }
    function paintLabels() {
      Array.prototype.forEach.call(el.nodes.querySelectorAll('small[data-ping]'), function (sm) {
        var s = BY[sm.getAttribute('data-ping')];
        sm.textContent = set.ping ? Math.round(s.ping) + ' ms' : '';
        sm.className = s.end ? 'c-bad' : s.st === 'warn' ? 'c-warn' : 'c-ok';
      });
    }

    /* ----------------------------------------------- zoom and pan --- */
    function applyView() {
      var w = el.map.clientWidth, hh = el.map.clientHeight;
      state.tx = Math.min(0, Math.max(w - w * state.z, state.tx));
      state.ty = Math.min(0, Math.max(hh - hh * state.z, state.ty));
      el.stage.style.transform = 'translate(' + state.tx.toFixed(1) + 'px,' + state.ty.toFixed(1) + 'px) scale(' + state.z.toFixed(3) + ')';
      el.stage.style.setProperty('--iz', (1 / state.z).toFixed(4));
      sizePackets();
    }
    function zoomTo(z2, cx, cy) {
      z2 = Math.max(1, Math.min(3.2, z2));
      var r = z2 / state.z;
      state.tx = cx - (cx - state.tx) * r;
      state.ty = cy - (cy - state.ty) * r;
      state.z = z2;
      applyView();
    }
    function zoomHome() {
      var w = el.map.clientWidth, hh = el.map.clientHeight, p = proj(HUB.lon, HUB.lat);
      var z = Math.max(state.z, 1.7);
      state.z = z;
      state.tx = w / 2 - (p[0] / W * w) * z;
      state.ty = hh / 2 - (p[1] / state.H * hh) * z;
      applyView();
    }
    var drag = null;
    el.map.addEventListener('pointerdown', function (e) {
      if (state.z <= 1 || e.target.closest('.nm-zoom,.nm-node,.nm-legend')) return;
      drag = { x: e.clientX, y: e.clientY, tx: state.tx, ty: state.ty, id: e.pointerId };
      try { el.map.setPointerCapture(e.pointerId); } catch (err) {}
      el.map.classList.add('drag');
    });
    el.map.addEventListener('pointermove', function (e) {
      if (!drag || e.pointerId !== drag.id) return;
      state.tx = drag.tx + (e.clientX - drag.x);
      state.ty = drag.ty + (e.clientY - drag.y);
      applyView();
    });
    function endDrag(e) { if (drag && (!e || e.pointerId === drag.id)) { drag = null; el.map.classList.remove('drag'); } }
    el.map.addEventListener('pointerup', endDrag);
    el.map.addEventListener('pointercancel', endDrag);

    /* ------------------------------------------------- list, routes --- */
    function cl(s) { return s.end ? 'bad' : s.st; }
    function renderList() {
      var q = state.q.trim().toLowerCase();
      var rows = SERVERS.filter(function (s) { return !q || (s.city + ' ' + s.cc + ' ' + s.fa).toLowerCase().indexOf(q) > -1; });
      el.list.innerHTML = rows.length ? rows.map(function (s) {
        return '<li><button type="button" class="nm-row' + (s.id === state.sel ? ' on' : '') + '" data-sel="' + s.id + '">' + flag(s.cc) +
          '<span class="nm-rn">' + esc(tag(s)) + '</span>' + (set.ping ? '<em class="c-' + (s.st === 'warn' ? 'warn' : 'ok') + '">' + Math.round(s.ping) + ' ms</em>' : '') +
          '<i class="dot d-' + (s.st === 'warn' ? 'warn' : 'ok') + '"></i></button></li>';
      }).join('') : '<li class="nm-none">' + T.empty + '</li>';
    }
    function renderRoutes() {
      el.routes.innerHTML = ROUTE_IDS.map(function (id, i) {
        var s = BY[id], on = id === state.sel;
        return '<button type="button" class="nm-route-i' + (on ? ' on' : '') + '" data-sel="' + id + '" role="radio" aria-checked="' + on + '">' +
          '<span class="nm-rr-top">' + flag(s.cc) + '<span class="nm-rr-name">' + (fa ? HUB.fa : HUB.city) + '<span class="nm-arr">' + icon('arrow') + '</span>' + name(s) + '</span>' +
          (i === 0 ? '<span class="nm-rec">' + T.rec + '</span>' : '') + '<span class="nm-radio"></span></span>' +
          '<span class="nm-rr-m"><span><b>' + (set.ping ? Math.round(s.ping) + ' ms' : '—') + '</b><small>' + T.ping + '</small></span>' +
          '<span><b>' + s.loss.toFixed(1) + '%</b><small>' + T.loss + '</small></span>' +
          '<span><b>' + (set.traffic ? fmtThr(s.thr) : '—') + '</b><small>' + T.cap + '</small></span></span></button>';
      }).join('');
    }

    /* ---------------------------------------------- details + chart --- */
    function genSeries(s) {
      var arr = [], i;
      for (i = 0; i < 31; i++) arr.push(Math.max(2, s.ping + Math.sin(i / 3.2) * 2.5 + (rnd() - 0.5) * 5));
      state.series = arr;
    }
    function smooth(pts) {
      var d = 'M' + pts[0][0].toFixed(1) + ',' + pts[0][1].toFixed(1), i;
      for (i = 0; i < pts.length - 1; i++) {
        var p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2;
        d += ' C' + (p1[0] + (p2[0] - p0[0]) / 6).toFixed(1) + ',' + (p1[1] + (p2[1] - p0[1]) / 6).toFixed(1) + ' ' +
          (p2[0] - (p3[0] - p1[0]) / 6).toFixed(1) + ',' + (p2[1] - (p3[1] - p1[1]) / 6).toFixed(1) + ' ' + p2[0].toFixed(1) + ',' + p2[1].toFixed(1);
      }
      return d;
    }
    function drawChart() {
      var n = state.series.length, pts = state.series.map(function (v, i) {
        return [i / (n - 1) * 300, 100 - Math.min(120, v) / 120 * 100];
      });
      var line = smooth(pts);
      el.chartSvg.innerHTML = '<defs><linearGradient id="nm-area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2de2a6" stop-opacity=".38"/><stop offset="1" stop-color="#2de2a6" stop-opacity="0"/></linearGradient></defs>' +
        '<g class="nm-gl"><line x1="0" y1="0" x2="300" y2="0"/><line x1="0" y1="33.3" x2="300" y2="33.3"/><line x1="0" y1="66.7" x2="300" y2="66.7"/><line x1="0" y1="100" x2="300" y2="100"/></g>' +
        '<path d="' + line + ' L300,100 L0,100 Z" fill="url(#nm-area)"/><path class="nm-ln" d="' + line + '"/>';
      var now = state.last, xs = [], i;
      for (i = 5; i >= 0; i--) xs.push('<span>' + hm(new Date(now.getTime() - i * 60000)) + '</span>');
      el.xax.innerHTML = xs.join('');
    }
    function renderDetails() {
      var s = BY[state.sel] || BY.frankfurt, warn = s.st === 'warn';
      el.badge.className = 'nm-badge ' + (warn ? 'warn' : 'ok');
      el.badge.innerHTML = '<i></i>' + (warn ? T.slow : T.active);
      el.chip.innerHTML = '<span>' + flag(HUB.cc) + '<b>' + (fa ? HUB.fa : HUB.city) + ' (IR)</b></span><span class="nm-arr">' + icon('arrow') + '</span><span>' + flag(s.cc) + '<b>' + (fa ? s.fa : s.city) + ' (' + s.cc.toUpperCase() + ')</b></span>';
      var c = warn ? 'c-warn' : 'c-ok', p = Math.round(s.ping);
      el.metrics.innerHTML =
        '<div><small>' + T.speed + '</small><b class="' + c + '">' + (set.traffic ? fmtThr(s.thr) : '—') + '</b></div>' +
        '<div><small>' + T.loss + '</small><b class="' + c + '">' + s.loss.toFixed(1) + '%</b></div>' +
        '<div><small>' + T.lat + '</small><b class="' + c + '">' + (set.ping ? p + ' ms' : '—') + '</b></div>' +
        '<div><small>' + T.ping + '</small><b class="' + c + '">' + (set.ping ? p + ' ms' : '—') + '</b></div>';
      drawChart();
    }

    function select(id) {
      if (!BY[id] || BY[id].hub) return;
      state.sel = id;
      genSeries(BY[id]);
      Array.prototype.forEach.call(root.querySelectorAll('[data-node]'), function (n) { n.classList.toggle('sel', n.getAttribute('data-node') === id); });
      Array.prototype.forEach.call(root.querySelectorAll('.nm-route'), function (r) { r.classList.toggle('sel', r.getAttribute('data-rid') === id); });
      renderList(); renderRoutes(); renderDetails();
    }

    /* ------------------------------------------------------ stats --- */
    function setStats() {
      var avg = 48 + Math.round((rnd() - 0.5) * 6), tr = (2.4 + (rnd() - 0.5) * 0.4).toFixed(1);
      el.avg.textContent = set.ping ? avg + ' ms' : '—';
      el.traffic.textContent = tr + ' Gbps';
      el.time.textContent = hm(state.last);
    }
    function labelInterval() { el.interval.textContent = set.refresh >= 120 ? '2 ' + T.min : set.refresh + ' ' + T.sec; }

    function tick() {
      if (!root.isConnected) { clearInterval(timer); timer = null; return; }
      state.last = new Date();
      SERVERS.forEach(function (s) { if (!s.hub) s.ping = Math.max(4, s.base + (rnd() - 0.5) * 8); });
      var sel = BY[state.sel];
      state.series.push(Math.max(2, sel.ping + (rnd() - 0.5) * 3));
      if (state.series.length > 31) state.series.shift();
      setStats(); paintLabels(); renderList(); renderRoutes(); renderDetails();
    }
    function schedule() {
      if (timer) clearInterval(timer);
      timer = setInterval(tick, set.refresh * 1000);
    }

    /* -------------------------------------------------- settings UI --- */
    function syncSettings() {
      Array.prototype.forEach.call(root.querySelectorAll('[data-set]'), function (inp) {
        var k = inp.getAttribute('data-set');
        if (inp.type === 'checkbox') inp.checked = !!set[k];
        else inp.value = String(set[k]);
      });
      el.speedLbl.textContent = T.speeds[set.speed - 1];
      var rg = root.querySelector('input[data-set="speed"]');
      rg.style.setProperty('--p', ((set.speed - 1) / 2 * 100) + '%');
      labelInterval();
    }
    root.addEventListener('input', function (e) {
      var inp = e.target.closest ? e.target.closest('[data-set]') : null;
      if (!inp) return;
      var k = inp.getAttribute('data-set'), redraw = false;
      if (inp.type === 'checkbox') set[k] = inp.checked;
      else if (k === 'speed') { set.speed = parseInt(inp.value, 10) || 2; redraw = true; }
      else if (k === 'refresh') { set.refresh = parseInt(inp.value, 10) || 30; schedule(); }
      syncSettings();
      if (redraw) drawMap();
      else applySvgPrefs();
      paintLabels(); setStats(); renderList(); renderRoutes(); renderDetails();
    });
    el.q.addEventListener('input', function () { state.q = el.q.value; renderList(); });

    root.addEventListener('click', function (e) {
      var t = e.target;
      var node = t.closest('[data-node]');
      if (node) { select(node.getAttribute('data-node')); return; }
      var sel = t.closest('[data-sel]');
      if (sel) { select(sel.getAttribute('data-sel')); return; }
      var act = t.closest('[data-act]');
      if (!act) return;
      var a = act.getAttribute('data-act'), w = el.map.clientWidth, hh = el.map.clientHeight;
      if (a === 'zin') zoomTo(state.z * 1.4, w / 2, hh / 2);
      else if (a === 'zout') zoomTo(state.z / 1.4, w / 2, hh / 2);
      else if (a === 'zhome') zoomHome();
      else if (a === 'refresh') { tick(); schedule(); }
      else if (a === 'save') {
        try { localStorage.setItem(LS_SET, JSON.stringify(set)); } catch (err) {}
        el.saveTxt.textContent = T.saved + ' ✓';
        setTimeout(function () { el.saveTxt.textContent = T.save; }, 1600);
      }
    });

    /* ------------------------------------------------------- boot --- */
    syncSettings();
    setStats();
    genSeries(BY[state.sel]);
    drawMap();
    renderList(); renderRoutes(); renderDetails();
    schedule();
    applyView();

    ensureLand().then(function (land) { if (land) drawMap(); });
    if (mq.addEventListener) mq.addEventListener('change', function () { drawMap(); applyView(); });
    if (window.ResizeObserver) {
      var lastW = 0;
      new ResizeObserver(function () {
        var w = el.map.clientWidth;
        if (w && Math.abs(w - lastW) > 2) { lastW = w; applyView(); }
      }).observe(el.map);
    }
    return root;
  }

  window.ShopVPNNetworkMap = { create: createNetworkMap };
})();
