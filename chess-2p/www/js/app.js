/*
 * Pass & Play Chess: two players, one device, fully offline.
 * UI, clocks, saving and the game flow; the rules live in chess.js.
 */
(function () {
  'use strict';

  var $ = function (id) { return document.getElementById(id); };
  var other = function (c) { return c === 'w' ? 'b' : 'w'; };
  var COLOR_NAME = { w: 'White', b: 'Black' };

  // ---------------------------------------------------------------- icons
  function svg(body, fill) {
    return '<svg viewBox="0 0 24 24" fill="' + (fill ? 'currentColor' : 'none') +
      '" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">' + body + '</svg>';
  }
  var ICON = {
    plus: svg('<path d="M12 5v14M5 12h14"/>'),
    undo: svg('<path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/>'),
    flag: svg('<path d="M5 21V4"/><path d="M5 4h13l-2.5 4.5L18 13H5"/>'),
    flip: svg('<path d="M7 20V5M3.5 8.5 7 5l3.5 3.5"/><path d="M17 4v15M13.5 15.5 17 19l3.5-3.5"/>'),
    prev: svg('<path d="m15 5-7 7 7 7"/>'),
    next: svg('<path d="m9 5 7 7-7 7"/>'),
    pause: svg('<path d="M8.5 5v14M15.5 5v14"/>'),
    play: svg('<path d="M7 4.5v15l12.5-7.5z"/>', true),
    settings: svg('<path d="M4 7h9M17 7h3M4 17h3M11 17h9"/><circle cx="15" cy="7" r="2"/><circle cx="9" cy="17" r="2"/>'),
    share: svg('<circle cx="18" cy="5" r="2.5"/><circle cx="6" cy="12" r="2.5"/><circle cx="18" cy="19" r="2.5"/><path d="m8.2 10.8 7.6-4.4M8.2 13.2l7.6 4.4"/>'),
    clock: svg('<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>'),
    trophy: svg('<path d="M8 4h8v5a4 4 0 0 1-8 0z"/><path d="M8 6H5a3 3 0 0 0 3.5 4M16 6h3a3 3 0 0 1-3.5 4M12 13v4M8 20h8M10 17h4"/>'),
    swap: svg('<path d="M7 20V4M3.5 7.5 7 4l3.5 3.5"/><path d="M17 4v16M13.5 16.5 17 20l3.5-3.5"/>'),
    bullet: svg('<path d="M5 19 15 9l3-1 1-3-3 1-1 3L5 19z"/><path d="m4 20 2-2"/>'),
    bolt: svg('<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>'),
    timer: svg('<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2.5 2.5M9.5 2h5"/>'),
    infinity: svg('<path d="M7 9a3 3 0 1 0 0 6c3 0 7-6 10-6a3 3 0 1 1 0 6c-3 0-7-6-10-6z"/>'),
    half: svg('<circle cx="12" cy="12" r="8.5"/><path d="M12 3.5v17" /><path d="M12 3.5a8.5 8.5 0 0 1 0 17z" fill="currentColor"/>'),
    user: svg('<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>'),
    camera: svg('<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>')
  };

  // -------------------------------------------------------------- storage
  function load(key, fallback) {
    try { var v = localStorage.getItem(key); return v ? JSON.parse(v) : fallback; } catch (e) { return fallback; }
  }
  function store(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* storage full or blocked */ }
  }

  var DEFAULT_SETTINGS = {
    sound: true, vibrate: true, showLegal: true, coords: true, animations: true,
    orientation: 'auto', theme: 'green', autoQueen: false, allowUndo: true, greeting: true
  };
  var DEFAULT_PHOTO = 'img/ayman.jpg';
  var settings = Object.assign({}, DEFAULT_SETTINGS, load('p2p.settings', {}));
  var profiles = Object.assign({
    p1: { name: 'Ayman', photo: DEFAULT_PHOTO },
    p2: { name: 'Player 2', photo: null }
  }, load('p2p.profiles', {}));
  var defaultPhotoOk = true;

  function saveSettings() { store('p2p.settings', settings); }
  function saveProfiles() { store('p2p.profiles', profiles); }

  var TIME_CONTROLS = [
    { group: 'Bullet', icon: 'bullet', items: [[60, 0], [60, 1], [120, 1]] },
    { group: 'Blitz', icon: 'bolt', items: [[180, 0], [180, 2], [300, 0]] },
    { group: 'Rapid', icon: 'timer', items: [[600, 0], [900, 10], [1800, 0]] }
  ];
  function tcLabel(tc) {
    if (!tc) return 'No clock';
    var m = tc.base / 60000;
    var mins = m >= 1 ? String(Math.round(m * 100) / 100) : String(Math.round(tc.base / 1000)) + 's';
    return tc.inc ? mins + ' | ' + Math.round(tc.inc / 1000) : (m >= 1 ? mins + ' min' : mins);
  }

  // ----------------------------------------------------------- game state
  var chess = new Chess();
  var game = null;
  var clock = { w: 0, b: 0, active: null, stamp: 0, running: false };
  var paused = false;
  var view = null;          // null = live position, otherwise ply being reviewed
  var manualFlip = false;
  var bottom = 'w';         // colour shown at the bottom of the board
  var selected = -1;
  var selectedMoves = [];
  var drag = null;
  var promoPending = null;
  var animMove = null;
  var lowWarned = { w: false, b: false };
  var flagTimer = 0, flipTimer = 0;

  function newGameState(tc, white, black) {
    return {
      tc: tc, white: white, black: black, records: [], started: false, result: null,
      clock: tc ? { w: tc.base, b: tc.base } : null, date: new Date().toISOString()
    };
  }

  function saveGame() {
    if (!game) return;
    if (game.tc) game.clock = { w: Math.max(0, timeLeft('w')), b: Math.max(0, timeLeft('b')) };
    game.active = clock.active;
    store('p2p.game', game);
  }

  function restoreGame(saved) {
    try {
      var c = new Chess();
      saved.records.forEach(function (r) { if (!c.move(r.uci)) throw new Error('bad move ' + r.uci); });
      chess = c;
      game = saved;
      clock = { w: 0, b: 0, active: null, stamp: 0, running: false };
      if (game.tc) {
        clock.w = game.clock.w; clock.b = game.clock.b;
        if (game.started && !game.result) { clock.active = chess.turn; paused = true; }
      }
      return true;
    } catch (e) {
      return false;
    }
  }

  // ---------------------------------------------------------------- clock
  // Remaining time is always derived from a monotonic timestamp, never from
  // counting timer ticks, so a slow or throttled UI cannot make a clock drift.
  function now() { return performance.now(); }
  function timeLeft(c) {
    var t = clock[c];
    if (clock.running && clock.active === c) t -= now() - clock.stamp;
    return t;
  }
  function commitClock() {
    if (!clock.running) return;
    var n = now();
    clock[clock.active] -= n - clock.stamp;
    clock.stamp = n;
  }
  function runClock(c) {
    commitClock();
    clock.active = c;
    clock.stamp = now();
    clock.running = !!(game && game.tc && game.started && !game.result && !paused);
    scheduleFlag();
  }
  function stopClock() {
    commitClock();
    clock.running = false;
    clearTimeout(flagTimer);
  }
  function scheduleFlag() {
    clearTimeout(flagTimer);
    if (clock.running) flagTimer = setTimeout(checkFlag, Math.max(0, timeLeft(clock.active)) + 5);
  }
  function checkFlag() {
    if (!clock.running) return false;
    var c = clock.active;
    if (timeLeft(c) > 0) { scheduleFlag(); return false; }
    stopClock();
    clock[c] = 0;
    // chess.com rule: a flag-fall is only a loss if the opponent could still mate.
    if (chess.insufficientFor(other(c), true)) endGame({ result: '1/2-1/2', winner: null, reason: 'timeout-insufficient' });
    else endGame({ result: c === 'w' ? '0-1' : '1-0', winner: other(c), reason: 'timeout' });
    return true;
  }

  function lowThreshold() {
    return game && game.tc ? Math.min(20000, Math.max(10000, game.tc.base * 0.1)) : 0;
  }

  function fmt(ms) {
    var t = Math.max(0, ms);
    if (t < 20000) {
      var tenths = Math.floor(t / 100);
      return '0:' + pad(Math.floor(tenths / 10)) + '.' + (tenths % 10);
    }
    var s = Math.floor(t / 1000);
    var h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60);
    return h ? h + ':' + pad(m) + ':' + pad(s % 60) : m + ':' + pad(s % 60);
  }
  function pad(n) { return (n < 10 ? '0' : '') + n; }

  function pause() {
    if (!game || !game.tc || !game.started || game.result || paused) return;
    stopClock();
    paused = true;
    clearSelection();
    saveGame();
    render();
  }
  function resume() {
    if (!paused) return;
    paused = false;
    Sound.unlock();
    runClock(chess.turn);
    render();
  }

  // ---------------------------------------------------------------- moves
  function isLive() {
    return game && !game.result && view === null && !paused && !promoPending;
  }

  function attemptMove(from, to, animate) {
    var cands = selectedMoves.filter(function (m) { return m.from === from && m.to === to; });
    if (!cands.length) cands = chess.legalMoves(from).filter(function (m) { return m.to === to; });
    if (!cands.length) return false;
    if (cands[0].promotion && !settings.autoQueen) {
      showPromotion(from, to, animate);
      return true;
    }
    return playMove(from, to, cands[0].promotion ? 'q' : null, animate);
  }

  function playMove(from, to, promo, animate) {
    if (!isLive() && !promoPending) return false;
    if (game.tc && clock.running && checkFlag()) return false;
    var mover = chess.turn;
    var rec = chess.move({ from: from, to: to, promotion: promo });
    if (!rec) { Sound.play('illegal'); return false; }
    var inc = 0;
    if (game.tc) {
      if (game.started) {
        commitClock();
        inc = game.tc.inc;
        clock[mover] += inc;
        if (clock[mover] > lowThreshold()) lowWarned[mover] = false;
      }
      game.started = true;
      runClock(other(mover));
    } else {
      game.started = true;
    }
    game.records.push({ uci: rec.uci, san: rec.san, color: mover, clk: game.tc ? clock[mover] : null, inc: inc });
    clearSelection();
    animMove = animate ? rec : null;

    var outcome = chess.outcome();
    playMoveSound(rec);
    buzz(12);
    if (outcome) endGame(outcome);
    else scheduleAutoFlip();
    saveGame();
    render();
    return true;
  }

  function playMoveSound(rec) {
    if (/[+#]/.test(rec.san)) Sound.play('check');
    else if (rec.promotion) Sound.play('promote');
    else if (rec.flag === 'k' || rec.flag === 'q') Sound.play('castle');
    else if (rec.captured) Sound.play('capture');
    else Sound.play('move');
  }

  function scheduleAutoFlip() {
    clearTimeout(flipTimer);
    if (settings.orientation !== 'auto') return;
    flipTimer = setTimeout(function () {
      var want = desiredBottom();
      if (want !== bottom) { bottom = want; render(); }
    }, settings.animations ? 380 : 120);
  }

  function desiredBottom() {
    var base = settings.orientation === 'auto' && game && !game.result ? chess.turn : 'w';
    return manualFlip ? other(base) : base;
  }

  function undoMove() {
    if (!game || game.result || !game.records.length || !settings.allowUndo) return;
    if (paused) resume();
    view = null;
    var r = game.records.pop();
    chess.undo();
    if (game.tc) {
      commitClock();
      // The mover gets back exactly the time they had when they played the move.
      clock[r.color] = Math.max(100, clock[r.color] - r.inc);
      if (!game.records.length) {
        game.started = false;
        clock.running = false;
        clock.active = null;
        clearTimeout(flagTimer);
      } else {
        runClock(r.color);
      }
      lowWarned[r.color] = clock[r.color] <= lowThreshold();
    }
    clearSelection();
    Sound.play('move');
    toast('Move taken back');
    bottom = desiredBottom();
    saveGame();
    render();
  }

  function endGame(outcome) {
    stopClock();
    paused = false;
    game.result = outcome;
    clearSelection();
    clearTimeout(flipTimer);
    saveGame();
    setTimeout(function () { Sound.play('end'); buzz([40, 60, 40]); }, 250);
    setTimeout(showGameOver, 700);
    render();
  }

  var REASONS = {
    checkmate: 'by checkmate', stalemate: 'by stalemate', insufficient: 'by insufficient material',
    repetition: 'by repetition', fifty: 'by 50-move rule', timeout: 'on time',
    'timeout-insufficient': 'timeout vs insufficient material', resign: 'by resignation', agreement: 'by agreement'
  };

  function profileOf(color) { return profiles[color === 'w' ? game.white : game.black]; }

  // --------------------------------------------------------------- render
  var boardEl = $('board');

  function displayedChess() {
    if (view === null) return chess;
    return new Chess(view === 0 ? chess.startFen : chess.history[view - 1].fen);
  }
  function displayedPly() { return view === null ? game.records.length : view; }

  function xy(sq) {
    var r = sq >> 3, f = sq & 7;
    return bottom === 'w' ? [f, r] : [7 - f, 7 - r];
  }
  function sqAt(col, row) {
    return bottom === 'w' ? row * 8 + col : (7 - row) * 8 + (7 - col);
  }
  function place(el, sq) {
    var p = xy(sq);
    el.style.transform = 'translate(' + p[0] * 100 + '%,' + p[1] * 100 + '%)';
  }

  function render() {
    if (!game) return;
    document.body.className = 'theme-' + settings.theme;
    var pos = displayedChess();
    var ply = displayedPly();
    var last = ply ? chess.history[ply - 1] : null;
    var html = '';

    for (var sq = 0; sq < 64; sq++) {
      var p = xy(sq), cls = ((sq >> 3) + (sq & 7)) % 2 ? 'dark' : 'light';
      if (last && (sq === last.fromSq || sq === last.toSq)) cls += ' hl';
      if (sq === selected && view === null) cls += ' sel';
      if (pos.board[sq] && pos.board[sq].toLowerCase() === 'k' && Chess.colorOf(pos.board[sq]) === pos.turn && pos.inCheck()) cls += ' check';
      var coords = '';
      if (settings.coords) {
        if (p[0] === 0) coords += '<span class="coord rank">' + (8 - (sq >> 3)) + '</span>';
        if (p[1] === 7) coords += '<span class="coord file">' + 'abcdefgh'[sq & 7] + '</span>';
      }
      html += '<div class="sq ' + cls + '" data-sq="' + sq + '" style="transform:translate(' + p[0] * 100 + '%,' + p[1] * 100 + '%)">' + coords + '</div>';
    }
    if (view === null && selected >= 0 && settings.showLegal) {
      selectedMoves.forEach(function (m, i) {
        if (i && selectedMoves[i - 1].to === m.to) return; // promotions share a square
        var q = xy(m.to);
        html += '<div class="hint' + (m.captured ? ' cap' : '') + '" style="transform:translate(' + q[0] * 100 + '%,' + q[1] * 100 + '%)"></div>';
      });
    }
    boardEl.innerHTML = html;

    var moving = [];
    for (sq = 0; sq < 64; sq++) {
      var piece = pos.board[sq];
      if (!piece) continue;
      var el = document.createElement('div');
      el.className = 'piece p-' + Chess.colorOf(piece) + piece.toUpperCase();
      el.dataset.sq = sq;
      if (animMove && settings.animations && view === null) {
        var a = animMove;
        if (sq === a.toSq) moving.push([el, a.fromSq, sq]);
        else if (a.flag === 'k' && sq === a.toSq - 1) moving.push([el, a.toSq + 1, sq]);
        else if (a.flag === 'q' && sq === a.toSq + 1) moving.push([el, a.toSq - 2, sq]);
      }
      place(el, sq);
      boardEl.appendChild(el);
    }
    moving.forEach(function (mv) {
      mv[0].classList.remove('anim');
      place(mv[0], mv[1]);
    });
    if (moving.length) {
      void boardEl.offsetWidth; // commit the start position before transitioning
      moving.forEach(function (mv) { mv[0].classList.add('anim'); place(mv[0], mv[2]); });
    }
    animMove = null;

    renderBars(pos, ply);
    renderMoves();
    renderToolbar();
    $('pause-overlay').hidden = !paused;
    $('btn-pause').hidden = !(game.tc && game.started && !game.result);
    $('btn-pause').innerHTML = paused ? ICON.play : ICON.pause;
  }

  function renderBars(pos, ply) {
    var topColor = other(bottom);
    var captured = { w: [], b: [] };
    for (var i = 0; i < ply; i++) {
      var h = chess.history[i];
      if (h.captured) captured[h.color].push(h.captured.toLowerCase());
    }
    var mat = pos.material();
    fillBar($('bar-top'), topColor, captured[topColor], mat[topColor] - mat[bottom]);
    fillBar($('bar-bottom'), bottom, captured[bottom], mat[bottom] - mat[topColor]);
    $('bar-top').classList.toggle('rotated', settings.orientation === 'tabletop');
    updateClocks();
  }

  var ORDER = { p: 0, n: 1, b: 2, r: 3, q: 4 };
  function fillBar(el, color, caps, adv) {
    var prof = profileOf(color);
    var oppColor = other(color) === 'w' ? 'w' : 'b';
    caps.sort(function (a, b) { return ORDER[a] - ORDER[b]; });
    var capHtml = caps.map(function (t, i) {
      return '<span class="cp p-' + oppColor + t.toUpperCase() + (i && caps[i - 1] !== t ? ' gap' : '') + '"></span>';
    }).join('');
    if (adv > 0) capHtml += '<span class="adv">+' + adv + '</span>';
    var toMove = game && !game.result && chess.turn === color && view === null ? '<span class="to-move">• to move</span>' : '';
    el.innerHTML = avatarHtml(prof, color) +
      '<div class="pinfo"><div class="pname">' + esc(prof.name) + toMove + '</div><div class="captured">' + capHtml + '</div></div>' +
      '<div class="clock' + (game.tc ? '' : ' none') + '" data-c="' + color + '"><span class="clock-ico">' + ICON.clock + '</span><span class="t"></span></div>';
  }

  function updateClocks() {
    if (!game || !game.tc) return;
    var low = lowThreshold();
    ['w', 'b'].forEach(function (c) {
      var el = document.querySelector('.clock[data-c="' + c + '"]');
      if (!el) return;
      var t = timeLeft(c);
      el.querySelector('.t').textContent = fmt(t);
      var active = !game.result && game.started && clock.active === c;
      el.classList.toggle('active', active);
      el.classList.toggle('low', t < low && t > 0);
      el.classList.toggle('flagged', t <= 0 && !!game.result);
      if (active && clock.running && t < low && !lowWarned[c] && game.tc.base >= 60000) {
        lowWarned[c] = true;
        Sound.play('lowtime');
        buzz([30, 80, 30]);
      }
    });
  }

  function figurine(san, color) {
    var m = /^([KQRBN])(.*)$/.exec(san);
    if (!m) return esc(san);
    return '<span class="fig p-w' + m[1] + '"></span>' + esc(m[2]);
  }

  function renderMoves() {
    var el = $('moves');
    var recs = game.records;
    if (!recs.length) {
      el.innerHTML = '<span class="empty">' + (game.tc ? 'White to move. Clocks start after the first move.' : 'White to move.') + '</span>';
      return;
    }
    var cur = displayedPly();
    var html = '';
    for (var i = 0; i < recs.length; i += 2) {
      var alt = (i / 2) % 2 ? ' mv-row-alt' : '';
      html += '<span class="mv-no' + alt + '">' + (i / 2 + 1) + '.</span>';
      html += '<button class="mv' + alt + (cur === i + 1 ? ' cur' : '') + '" data-ply="' + (i + 1) + '">' + figurine(recs[i].san, 'w') + '</button>';
      if (recs[i + 1]) html += '<button class="mv' + alt + (cur === i + 2 ? ' cur' : '') + '" data-ply="' + (i + 2) + '">' + figurine(recs[i + 1].san, 'b') + '</button>';
      else html += '<span class="' + alt + '"></span>';
    }
    if (game.result) html += '<span class="mv-result">' + game.result.result + '</span>';
    el.innerHTML = html;
    var curEl = el.querySelector('.mv.cur');
    if (curEl) curEl.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    else el.scrollLeft = el.scrollWidth;
  }

  function renderToolbar() {
    $('btn-undo').disabled = !(settings.allowUndo && game.records.length && !game.result);
    $('btn-end').disabled = !!game.result;
    $('btn-prev').disabled = displayedPly() === 0;
    $('btn-next').disabled = view === null;
  }

  function avatarHtml(prof, color, extraClass) {
    var photo = photoOf(prof);
    var style = photo ? ' style="background-image:url(\'' + photo + '\')"' : '';
    var initial = photo ? '' : esc((prof.name || '?').trim().charAt(0).toUpperCase() || '?');
    var dot = color ? '<span class="side-dot ' + color + '"></span>' : '';
    return '<div class="avatar' + (extraClass ? ' ' + extraClass : '') + '"' + style + '>' + initial + dot + '</div>';
  }
  function photoOf(prof) {
    if (!prof || !prof.photo) return null;
    if (prof.photo === DEFAULT_PHOTO && !defaultPhotoOk) return null;
    return prof.photo;
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  // ---------------------------------------------------------- interaction
  function clearSelection() { selected = -1; selectedMoves = []; }

  function select(sq) {
    selected = sq;
    selectedMoves = chess.legalMoves(sq);
  }

  function pointToSq(e) {
    var r = boardEl.getBoundingClientRect();
    var col = Math.floor((e.clientX - r.left) / r.width * 8);
    var row = Math.floor((e.clientY - r.top) / r.height * 8);
    if (col < 0 || col > 7 || row < 0 || row > 7) return -1;
    return sqAt(col, row);
  }

  boardEl.addEventListener('pointerdown', function (e) {
    if (e.button !== undefined && e.button > 0) return;
    Sound.unlock();
    if (!game) return;
    if (promoPending) { cancelPromotion(); return; }
    if (view !== null) { view = null; render(); return; }
    if (!isLive()) return;
    var sq = pointToSq(e);
    if (sq < 0) return;
    var piece = chess.board[sq];

    if (selected >= 0 && selected !== sq && selectedMoves.some(function (m) { return m.to === sq; })) {
      attemptMove(selected, sq, true);
      return;
    }
    if (piece && Chess.colorOf(piece) === chess.turn) {
      var wasSelected = selected === sq;
      select(sq);
      render();
      var el = boardEl.querySelector('.piece[data-sq="' + sq + '"]');
      drag = { sq: sq, el: el, x: e.clientX, y: e.clientY, moved: false, wasSelected: wasSelected, over: -1 };
      try { boardEl.setPointerCapture(e.pointerId); } catch (err) { /* ignore */ }
      e.preventDefault();
    } else {
      if (selected >= 0) { clearSelection(); render(); }
    }
  });

  boardEl.addEventListener('pointermove', function (e) {
    if (!drag || !drag.el) return;
    if (!drag.moved && Math.hypot(e.clientX - drag.x, e.clientY - drag.y) < 5) return;
    drag.moved = true;
    var r = boardEl.getBoundingClientRect(), s = r.width / 8;
    drag.el.classList.add('drag');
    drag.el.style.transform = 'translate(' + (e.clientX - r.left - s / 2) + 'px,' + (e.clientY - r.top - s / 2) + 'px) scale(1.12)';
    var over = pointToSq(e);
    if (over !== drag.over) {
      var prev = boardEl.querySelector('.sq.hover');
      if (prev) prev.classList.remove('hover');
      var cur = over >= 0 ? boardEl.querySelector('.sq[data-sq="' + over + '"]') : null;
      if (cur) cur.classList.add('hover');
      drag.over = over;
    }
  });

  function endDrag(e, cancelled) {
    if (!drag) return;
    var d = drag;
    drag = null;
    if (d.moved && !cancelled) {
      var to = pointToSq(e);
      if (to >= 0 && to !== d.sq && selectedMoves.some(function (m) { return m.to === to; })) {
        attemptMove(d.sq, to, false);
        return;
      }
      if (to >= 0 && to !== d.sq) Sound.play('illegal');
      render();
      return;
    }
    if (!d.moved && d.wasSelected) { clearSelection(); render(); }
    else if (cancelled) render();
  }
  boardEl.addEventListener('pointerup', function (e) { endDrag(e, false); });
  boardEl.addEventListener('pointercancel', function (e) { endDrag(e, true); });
  boardEl.addEventListener('contextmenu', function (e) { e.preventDefault(); });

  // ------------------------------------------------------------ promotion
  function showPromotion(from, to, animate) {
    promoPending = { from: from, to: to, animate: animate };
    var color = chess.turn;
    var p = xy(to);
    var el = document.createElement('div');
    el.className = 'promo' + (p[1] === 0 ? '' : ' up');
    el.style.left = (p[0] * 12.5) + '%';
    if (p[1] === 0) el.style.top = '0';
    else el.style.bottom = '0';
    ['Q', 'N', 'R', 'B'].forEach(function (t) {
      var b = document.createElement('button');
      b.className = 'p-' + color + t;
      b.setAttribute('aria-label', t);
      b.addEventListener('pointerdown', function (e) {
        e.stopPropagation();
        var pp = promoPending;
        el.remove();
        playMove(pp.from, pp.to, t.toLowerCase(), pp.animate);
        promoPending = null;
        render();
      });
      el.appendChild(b);
    });
    var x = document.createElement('button');
    x.className = 'promo-x';
    x.textContent = '✕';
    x.addEventListener('pointerdown', function (e) { e.stopPropagation(); cancelPromotion(); });
    el.appendChild(x);
    $('board-wrap').appendChild(el);
  }
  function cancelPromotion() {
    var el = document.querySelector('.promo');
    if (el) el.remove();
    promoPending = null;
    clearSelection();
    render();
  }

  // --------------------------------------------------------------- sheets
  var sheetEl = $('sheet'), scrimEl = $('scrim');
  var sheetOnClose = null;

  function openSheet(html, opts) {
    opts = opts || {};
    sheetEl.className = 'sheet' + (opts.center ? ' center' : '');
    sheetEl.innerHTML = (opts.center ? '<button class="close-x" data-act="close">✕</button>' : '<div class="sheet-grab"></div>') + html;
    sheetEl.hidden = false;
    scrimEl.hidden = false;
    sheetOnClose = opts.onClose || null;
    sheetEl.scrollTop = 0;
  }
  function closeSheet() {
    if (sheetEl.hidden) return;
    sheetEl.hidden = true;
    scrimEl.hidden = true;
    sheetEl.innerHTML = '';
    var cb = sheetOnClose;
    sheetOnClose = null;
    if (cb) cb();
  }
  scrimEl.addEventListener('click', closeSheet);
  sheetEl.addEventListener('click', function (e) {
    var t = e.target.closest('[data-act="close"]');
    if (t) closeSheet();
  });

  function confirmSheet(title, text, okLabel, onOk, danger) {
    openSheet('<h2>' + title + '</h2><p style="text-align:center;color:var(--muted);margin:-4px 0 20px">' + text +
      '</p><div class="row2"><button class="btn" data-act="close">Cancel</button><button class="btn ' +
      (danger ? 'btn-danger' : 'btn-primary') + '" id="confirm-ok">' + okLabel + '</button></div>', { center: true });
    $('confirm-ok').addEventListener('click', function () { closeSheet(); onOk(); });
  }

  // ------------------------------------------------------------- new game
  var draft = null;

  function showNewGame() {
    var last = load('p2p.lastSetup', null);
    draft = {
      white: game ? game.white : 'p1',
      black: game ? game.black : 'p2',
      tc: last && 'tc' in last ? last.tc : { base: 600000, inc: 0 },
      names: { p1: profiles.p1.name, p2: profiles.p2.name }
    };
    renderNewGame();
  }

  function renderNewGame() {
    var tcKey = draft.tc ? draft.tc.base + '+' + draft.tc.inc : 'none';
    var html = '<h2>Play a Friend</h2><div class="stack">' +
      playerCard('w', draft.white) +
      '<button class="swap-btn" id="ng-swap">' + ICON.swap + 'Swap colours</button>' +
      playerCard('b', draft.black) + '</div>';
    TIME_CONTROLS.forEach(function (g) {
      html += '<h3>' + ICON[g.icon] + g.group + '</h3><div class="tc-grid">';
      g.items.forEach(function (it) {
        var key = it[0] * 1000 + '+' + it[1] * 1000;
        html += '<button class="tc' + (key === tcKey ? ' on' : '') + '" data-tc="' + key + '">' + tcLabel({ base: it[0] * 1000, inc: it[1] * 1000 }) + '</button>';
      });
      html += '</div>';
    });
    var isPreset = tcKey === 'none' || TIME_CONTROLS.some(function (g) {
      return g.items.some(function (it) { return it[0] * 1000 + '+' + it[1] * 1000 === tcKey; });
    });
    html += '<h3>' + ICON.clock + 'Other</h3><div class="tc-grid">' +
      '<button class="tc' + (tcKey === 'none' ? ' on' : '') + '" data-tc="none">No clock</button>' +
      '<button class="tc' + (!isPreset ? ' on' : '') + '" data-tc="custom" style="grid-column:span 2">Custom' + (!isPreset ? ': ' + tcLabel(draft.tc) : '') + '</button></div>';
    html += '<div class="custom-tc" id="ng-custom"' + (isPreset ? ' hidden' : '') + '>' +
      '<label class="field">Minutes per player<input id="ng-min" type="number" inputmode="decimal" min="0.25" max="300" step="any" value="' + (draft.tc ? draft.tc.base / 60000 : 10) + '"></label>' +
      '<label class="field">Increment (sec)<input id="ng-inc" type="number" inputmode="numeric" min="0" max="180" step="1" value="' + (draft.tc ? draft.tc.inc / 1000 : 0) + '"></label></div>';
    html += '<div style="margin-top:22px"><button class="btn btn-primary btn-block" id="ng-start">Play</button></div>';
    openSheet(html);

    sheetEl.querySelectorAll('.pcard input').forEach(function (inp) {
      inp.addEventListener('input', function () { draft.names[inp.dataset.p] = inp.value; });
    });
    sheetEl.querySelectorAll('.pcard .avatar').forEach(function (av) {
      av.addEventListener('click', function () { pickPhoto(av.dataset.p, renderNewGame); });
    });
    $('ng-swap').addEventListener('click', function () {
      var t = draft.white; draft.white = draft.black; draft.black = t;
      renderNewGame();
    });
    sheetEl.querySelectorAll('.tc').forEach(function (b) {
      b.addEventListener('click', function () {
        var v = b.dataset.tc;
        if (v === 'none') draft.tc = null;
        else if (v === 'custom') {
          draft.tc = draft.tc || { base: 600000, inc: 0 };
          renderNewGame();
          $('ng-custom').hidden = false;
          sheetEl.querySelector('[data-tc="custom"]').classList.add('on');
          sheetEl.querySelectorAll('.tc.on').forEach(function (x) { if (x.dataset.tc !== 'custom') x.classList.remove('on'); });
          return;
        } else {
          var parts = v.split('+');
          draft.tc = { base: +parts[0], inc: +parts[1] };
        }
        renderNewGame();
      });
    });
    $('ng-start').addEventListener('click', function () {
      if (!$('ng-custom').hidden) {
        var mins = parseFloat($('ng-min').value), inc = parseInt($('ng-inc').value, 10);
        if (!(mins > 0) || mins > 300 || !(inc >= 0) || inc > 180) { toast('Enter 0.25 to 300 minutes and 0 to 180 s increment'); return; }
        draft.tc = { base: Math.round(Math.max(0.25, mins) * 60000), inc: inc * 1000 };
      }
      ['p1', 'p2'].forEach(function (p) {
        var n = (draft.names[p] || '').trim();
        profiles[p].name = n || (p === 'p1' ? 'Ayman' : 'Player 2');
      });
      saveProfiles();
      store('p2p.lastSetup', { tc: draft.tc });
      closeSheet();
      startNewGame(draft.tc, draft.white, draft.black);
    });
  }

  function playerCard(color, pid) {
    var prof = profiles[pid];
    return '<div class="pcard"><div class="avatar-edit">' + avatarHtml(prof, null).replace('class="avatar"', 'class="avatar" data-p="' + pid + '"') +
      '</div><label class="field"><span class="color-tag"><i style="background:' + (color === 'w' ? '#fff' : '#000;border:1px solid #777') + '"></i>' + COLOR_NAME[color] +
      '</span><input data-p="' + pid + '" maxlength="24" value="' + esc(draft.names[pid]) + '"></label></div>';
  }

  function startNewGame(tc, white, black) {
    stopClock();
    clearTimeout(flipTimer);
    chess = new Chess();
    game = newGameState(tc, white, black);
    clock = { w: tc ? tc.base : 0, b: tc ? tc.base : 0, active: null, stamp: 0, running: false };
    lowWarned = { w: false, b: false };
    paused = false; view = null; manualFlip = false; promoPending = null;
    clearSelection();
    bottom = desiredBottom();
    saveGame();
    render();
    if (settings.greeting) showGreeting('new');
    else Sound.play('start');
  }

  // ------------------------------------------------------ Ayman's greeting
  function showGreeting(kind) {
    var me = profiles.p1;
    var meColor = game && game.white === 'p1' ? 'w' : 'b';
    var opp = profiles.p2.name;
    var photo = photoOf(me);
    var title = 'Hello! I\'m ' + me.name + ' <span class="wave">👋</span>';
    var line, speech;
    if (kind === 'resume') {
      line = 'Welcome back! Our game is saved right where we left it. Tap resume when you are both ready.';
      speech = 'Hello! I\'m ' + me.name + '. Welcome back! Let\'s finish our game.';
    } else {
      line = 'Welcome to the board. I\'m playing ' + COLOR_NAME[meColor] + (opp ? ' against ' + opp : '') + ' today. Good luck, and may the best move win!';
      speech = 'Hello! I\'m ' + me.name + '. Welcome to the board. Let\'s play chess! Good luck, ' + opp + '.';
    }
    var wrap = document.createElement('div');
    wrap.className = 'greet';
    wrap.id = 'greet';
    wrap.innerHTML = '<div class="greet-card">' +
      '<div class="greet-photo"' + (photo ? ' style="background-image:url(\'' + photo + '\')"' : '') + '>' + (photo ? '' : esc(me.name.charAt(0))) + '</div>' +
      '<div class="greet-name">' + esc(me.name) + ' · Pass &amp; Play</div>' +
      '<div class="bubble"><b>' + title + '</b><span class="typed"></span><span class="caret"></span></div>' +
      '<button class="btn btn-primary" id="greet-go">' + (kind === 'resume' ? 'Continue' : 'Let\'s play!') + '</button></div>';
    document.body.appendChild(wrap);

    var typed = wrap.querySelector('.typed'), i = 0;
    var typer = setInterval(function () {
      i++;
      typed.textContent = line.slice(0, i);
      if (i >= line.length) { clearInterval(typer); var c = wrap.querySelector('.caret'); if (c) c.remove(); }
    }, 28);
    setTimeout(function () { Sound.speak(speech); }, 450);
    wrap.querySelector('#greet-go').addEventListener('click', function () {
      clearInterval(typer);
      Sound.unlock();
      Sound.play('start');
      wrap.remove();
    });
  }
  function greetingOpen() { return !!$('greet'); }

  // ----------------------------------------------------------- game over
  function showGameOver() {
    if (!game || !game.result || !sheetEl.hidden) return;
    var r = game.result;
    var title = r.winner ? esc(profileOf(r.winner).name) + ' Won!' : 'Draw';
    var sub = r.winner ? COLOR_NAME[r.winner] + ' wins ' + REASONS[r.reason] : REASONS[r.reason].replace(/^by /, 'By ');
    if (!r.winner && r.reason === 'timeout-insufficient') sub = 'Timeout vs insufficient material';
    var score = r.result === '1/2-1/2' ? ['½', '½'] : r.result.split('-');
    var face = function (color, s) {
      var prof = profileOf(color);
      return '<div class="face' + (r.winner === color ? ' win' : '') + '">' + avatarHtml(prof, color) +
        '<span>' + esc(prof.name) + '</span><span class="score">' + s + '</span></div>';
    };
    openSheet('<div class="result"><div class="trophy">' + (r.winner ? ICON.trophy : ICON.half) + '</div><h2>' + title + '</h2>' +
      '<div class="reason">' + sub + '</div><div class="faces">' + face('w', score[0]) + '<span class="vs">vs</span>' + face('b', score[1]) + '</div>' +
      '<div class="stack"><button class="btn btn-primary btn-block" id="go-rematch">Rematch</button>' +
      '<div class="row2"><button class="btn" id="go-new">New Game</button><button class="btn" id="go-share">' + ICON.share + 'PGN</button></div>' +
      '<button class="btn btn-block" data-act="close">Review game</button></div></div>', { center: true });
    $('go-rematch').addEventListener('click', function () { closeSheet(); startNewGame(game.tc, game.black, game.white); });
    $('go-new').addEventListener('click', function () { closeSheet(); showNewGame(); });
    $('go-share').addEventListener('click', sharePgn);
  }

  // ------------------------------------------------------- draw / resign
  function showEndMenu() {
    if (!game || game.result) return;
    var w = profileOf('w').name, b = profileOf('b').name;
    openSheet('<h2>Draw or Resign</h2><div class="menu-list">' +
      '<button class="menu-item" id="em-draw">' + ICON.half + 'Agree to a draw</button>' +
      '<button class="menu-item" id="em-rw">' + ICON.flag + esc(w) + ' resigns (White)</button>' +
      '<button class="menu-item" id="em-rb">' + ICON.flag + esc(b) + ' resigns (Black)</button></div>');
    $('em-draw').addEventListener('click', function () {
      confirmSheet('Draw by agreement?', 'Both players agree to end the game as a draw.', 'Agree', function () {
        endGame({ result: '1/2-1/2', winner: null, reason: 'agreement' });
      });
    });
    [['em-rw', 'w', w], ['em-rb', 'b', b]].forEach(function (x) {
      $(x[0]).addEventListener('click', function () {
        confirmSheet('Resign?', esc(x[2]) + ' (' + COLOR_NAME[x[1]] + ') resigns the game.', 'Resign', function () {
          endGame({ result: x[1] === 'w' ? '0-1' : '1-0', winner: other(x[1]), reason: 'resign' });
        }, true);
      });
    });
  }

  // ------------------------------------------------------------ settings
  function showSettings() {
    var sw = function (k, label, hint) {
      return '<div class="opt"><div>' + label + (hint ? '<small>' + hint + '</small>' : '') + '</div><button class="switch' + (settings[k] ? ' on' : '') + '" data-k="' + k + '" aria-label="' + label + '"></button></div>';
    };
    var themes = { green: ['#ebecd0', '#739552'], brown: ['#f0d9b5', '#b58863'], blue: ['#dee3e6', '#8ca2ad'], purple: ['#efeff5', '#8877b7'], wood: ['#e8c99b', '#a5713f'] };
    var themeHtml = Object.keys(themes).map(function (t) {
      var c = themes[t];
      return '<button class="theme-chip' + (settings.theme === t ? ' on' : '') + '" data-theme="' + t + '"><i style="background:' + c[0] + '"></i><i style="background:' + c[1] + '"></i><i style="background:' + c[1] + '"></i><i style="background:' + c[0] + '"></i></button>';
    }).join('');
    var orient = [['auto', 'Auto-flip'], ['white', 'White below'], ['tabletop', 'Tabletop']];
    var html = '<h2>Settings</h2>' +
      '<h3>' + ICON.user + 'Players</h3><div class="menu-list">' +
      ['p1', 'p2'].map(function (p) {
        return '<button class="menu-item" data-photo="' + p + '">' + avatarHtml(profiles[p], null) + '<span style="flex:1">' + esc(profiles[p].name) + '</span>' + ICON.camera + '</button>';
      }).join('') + '</div>' +
      '<h3>Board</h3><div class="opt"><div>Board orientation<small>Tabletop turns the top player\'s panel to face them</small></div></div>' +
      '<div class="seg" id="seg-orient">' + orient.map(function (o) {
        return '<button class="' + (settings.orientation === o[0] ? 'on' : '') + '" data-o="' + o[0] + '">' + o[1] + '</button>';
      }).join('') + '</div>' +
      '<div class="opt"><div>Board colours</div><div class="themes">' + themeHtml + '</div></div>' +
      sw('showLegal', 'Show legal moves') + sw('coords', 'Show coordinates') + sw('animations', 'Piece animation') +
      '<h3>Game</h3>' + sw('autoQueen', 'Always promote to queen') + sw('allowUndo', 'Allow takebacks') +
      sw('greeting', 'Ayman\'s greeting', 'Say hello at the start of each game') +
      '<h3>Sound &amp; feel</h3>' + sw('sound', 'Sounds and voice') + sw('vibrate', 'Vibration') +
      '<p style="color:var(--dim);font-size:12px;font-weight:500;margin-top:18px">Pieces: cburnett set (CC BY-SA 3.0). Works fully offline.</p>';
    openSheet(html);
    sheetEl.querySelectorAll('.switch').forEach(function (b) {
      b.addEventListener('click', function () {
        var k = b.dataset.k;
        settings[k] = !settings[k];
        b.classList.toggle('on', settings[k]);
        applySettings();
      });
    });
    sheetEl.querySelectorAll('[data-theme]').forEach(function (b) {
      b.addEventListener('click', function () {
        settings.theme = b.dataset.theme;
        sheetEl.querySelectorAll('[data-theme]').forEach(function (x) { x.classList.toggle('on', x === b); });
        applySettings();
      });
    });
    sheetEl.querySelectorAll('[data-o]').forEach(function (b) {
      b.addEventListener('click', function () {
        settings.orientation = b.dataset.o;
        manualFlip = false;
        sheetEl.querySelectorAll('[data-o]').forEach(function (x) { x.classList.toggle('on', x === b); });
        applySettings();
      });
    });
    sheetEl.querySelectorAll('[data-photo]').forEach(function (b) {
      b.addEventListener('click', function () { showProfileEditor(b.dataset.photo); });
    });
  }

  function showProfileEditor(pid) {
    var prof = profiles[pid];
    openSheet('<h2>Player profile</h2><div class="stack" style="justify-items:center">' +
      '<div class="avatar-edit" style="position:relative">' + avatarHtml(prof, null, 'big').replace('class="avatar big"', 'class="avatar big" id="pe-photo" style="width:120px;height:120px;border-radius:12px;font-size:48px;' + (photoOf(prof) ? 'background-image:url(\'' + photoOf(prof) + '\')' : '') + '"') + '</div>' +
      '<label class="field" style="width:100%">Name<input id="pe-name" maxlength="24" value="' + esc(prof.name) + '"></label>' +
      '<div class="row2" style="width:100%"><button class="btn" id="pe-pick">' + ICON.camera + 'Photo</button><button class="btn" id="pe-clear">Remove photo</button></div>' +
      (pid === 'p1' ? '<button class="btn btn-block" id="pe-hello" style="width:100%">Play greeting</button>' : '') +
      '<button class="btn btn-primary btn-block" id="pe-save" style="width:100%">Save</button></div>', { center: true });
    $('pe-pick').addEventListener('click', function () {
      saveName();
      pickPhoto(pid, function () { showProfileEditor(pid); });
    });
    $('pe-clear').addEventListener('click', function () { saveName(); prof.photo = null; saveProfiles(); showProfileEditor(pid); render(); });
    if ($('pe-hello')) $('pe-hello').addEventListener('click', function () { saveName(); closeSheet(); render(); showGreeting('new'); });
    $('pe-save').addEventListener('click', function () { saveName(); closeSheet(); render(); });
    function saveName() {
      var n = $('pe-name').value.trim();
      if (n) prof.name = n;
      saveProfiles();
    }
  }

  function applySettings() {
    saveSettings();
    Sound.setEnabled(settings.sound);
    bottom = desiredBottom();
    render();
  }

  // --------------------------------------------------------------- photos
  var photoTarget = null, photoDone = null;
  function pickPhoto(pid, done) {
    photoTarget = pid;
    photoDone = done;
    var inp = $('photo-input');
    inp.value = '';
    inp.click();
  }
  $('photo-input').addEventListener('change', function () {
    var file = this.files && this.files[0];
    if (!file || !photoTarget) return;
    var reader = new FileReader();
    reader.onload = function () {
      var img = new Image();
      img.onload = function () {
        // Centre-crop to a square (biased slightly up, where faces usually are) and shrink to 256 px.
        var s = Math.min(img.width, img.height);
        var sx = (img.width - s) / 2, sy = Math.max(0, (img.height - s) * 0.3);
        var cv = document.createElement('canvas');
        cv.width = cv.height = 256;
        cv.getContext('2d').drawImage(img, sx, sy, s, s, 0, 0, 256, 256);
        profiles[photoTarget].photo = cv.toDataURL('image/jpeg', 0.85);
        saveProfiles();
        render();
        if (photoDone) photoDone();
      };
      img.onerror = function () { toast('Could not read that image'); };
      img.src = reader.result;
    };
    reader.readAsDataURL(file);
  });

  // ------------------------------------------------------------------ PGN
  function clk(ms) {
    var tenths = Math.floor(Math.max(0, ms) / 100), s = Math.floor(tenths / 10);
    return Math.floor(s / 3600) + ':' + pad(Math.floor((s % 3600) / 60)) + ':' + pad(s % 60) + '.' + (tenths % 10);
  }
  function pgn() {
    var d = new Date(game.date);
    var res = game.result ? game.result.result : '*';
    var term = '';
    if (game.result) {
      var r = game.result;
      term = r.winner ? profileOf(r.winner).name + ' won ' + REASONS[r.reason] : 'Game drawn ' + REASONS[r.reason].replace('timeout vs', 'by timeout vs');
    }
    var tags = [
      ['Event', 'Pass & Play'], ['Site', 'Local'],
      ['Date', d.getFullYear() + '.' + pad(d.getMonth() + 1) + '.' + pad(d.getDate())],
      ['White', profileOf('w').name], ['Black', profileOf('b').name], ['Result', res],
      ['TimeControl', game.tc ? game.tc.base / 1000 + (game.tc.inc ? '+' + game.tc.inc / 1000 : '') : '-']
    ];
    if (term) tags.push(['Termination', term]);
    var out = tags.map(function (t) { return '[' + t[0] + ' "' + String(t[1]).replace(/"/g, "'") + '"]'; }).join('\n') + '\n\n';
    var body = game.records.map(function (r, i) {
      return (i % 2 ? '' : (i / 2 + 1) + '. ') + r.san + (game.tc ? ' {[%clk ' + clk(r.clk) + ']}' : '');
    }).join(' ');
    return out + (body ? body + ' ' : '') + res + '\n';
  }
  function sharePgn() {
    var text = pgn();
    try {
      if (window.AndroidBridge && AndroidBridge.share) { AndroidBridge.share(text); return; }
    } catch (e) { /* fall through */ }
    if (navigator.share) { navigator.share({ title: 'Chess game', text: text }).catch(function () {}); return; }
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(function () { toast('PGN copied'); }, function () { downloadPgn(text); });
      return;
    }
    downloadPgn(text);
  }
  function downloadPgn(text) {
    var a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([text], { type: 'application/x-chess-pgn' }));
    a.download = 'game.pgn';
    a.click();
  }

  // ------------------------------------------------------------- helpers
  var toastTimer = 0;
  function toast(msg) {
    var t = $('toast');
    t.textContent = msg;
    t.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.hidden = true; }, 1800);
  }
  function buzz(pattern) {
    if (!settings.vibrate) return;
    try { if (navigator.vibrate) navigator.vibrate(pattern); } catch (e) { /* no vibration */ }
  }
  function setView(ply) {
    if (!game) return;
    if (promoPending) cancelPromotion();
    clearSelection();
    var n = game.records.length;
    ply = Math.max(0, Math.min(n, ply));
    var before = displayedPly();
    view = ply >= n ? null : ply;
    if (ply !== before) {
      if (ply === before + 1) playMoveSound(chess.history[ply - 1]);
      else Sound.play('move');
    }
    render();
  }

  // ------------------------------------------------------------- toolbar
  function setIcon(id, icon) { $(id).querySelector('.ti').innerHTML = icon; }
  setIcon('btn-new', ICON.plus);
  setIcon('btn-undo', ICON.undo);
  setIcon('btn-end', ICON.flag);
  setIcon('btn-flip', ICON.flip);
  setIcon('btn-prev', ICON.prev);
  setIcon('btn-next', ICON.next);
  $('btn-settings').innerHTML = ICON.settings;

  $('btn-new').addEventListener('click', function () {
    if (game && game.started && !game.result) {
      confirmSheet('Start a new game?', 'The current game will be abandoned.', 'New game', showNewGame, true);
    } else showNewGame();
  });
  $('btn-undo').addEventListener('click', undoMove);
  $('btn-end').addEventListener('click', showEndMenu);
  $('btn-flip').addEventListener('click', function () { manualFlip = !manualFlip; bottom = desiredBottom(); render(); });
  $('btn-prev').addEventListener('click', function () { setView(displayedPly() - 1); });
  $('btn-next').addEventListener('click', function () { setView(displayedPly() + 1); });
  $('btn-settings').addEventListener('click', showSettings);
  $('btn-pause').addEventListener('click', function () { if (paused) resume(); else pause(); });
  $('btn-resume').addEventListener('click', resume);
  $('moves').addEventListener('click', function (e) {
    var b = e.target.closest('[data-ply]');
    if (b) setView(+b.dataset.ply);
  });
  document.addEventListener('keydown', function (e) {
    if (e.target.tagName === 'INPUT') return;
    if (e.key === 'ArrowLeft') setView(displayedPly() - 1);
    else if (e.key === 'ArrowRight') setView(displayedPly() + 1);
    else if (e.key === 'Escape') closeSheet();
  });

  // --------------------------------------------- app lifecycle (Android)
  // Called by the Android wrapper; returns "true" when the back press was handled.
  window.onAndroidBack = function () {
    if (greetingOpen()) { $('greet').remove(); return true; }
    if (!sheetEl.hidden) { closeSheet(); return true; }
    if (promoPending) { cancelPromotion(); return true; }
    if (view !== null) { view = null; render(); return true; }
    if (selected >= 0) { clearSelection(); render(); return true; }
    return false;
  };
  window.onAppPause = function () { pause(); saveGame(); };
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) { pause(); saveGame(); }
  });
  window.addEventListener('pagehide', saveGame);

  setInterval(function () {
    if (!clock.running) return;
    updateClocks();
    checkFlag();
  }, 50);
  setInterval(function () { if (clock.running) saveGame(); }, 2000);
  window.addEventListener('resize', function () { render(); });

  // ------------------------------------------------------------------ boot
  (function injectPieceCss() {
    var css = Object.keys(window.PIECE_SVG).map(function (k) {
      return '.p-' + k + '{background-image:url("data:image/svg+xml;charset=utf-8,' + encodeURIComponent(window.PIECE_SVG[k]) + '")}';
    }).join('\n');
    var st = document.createElement('style');
    st.textContent = css;
    document.head.appendChild(st);
    document.querySelector('.brand-mark').classList.add('p-wN');
  })();

  function boot() {
    Sound.setEnabled(settings.sound);
    var saved = load('p2p.game', null);
    var resumed = !!(saved && !saved.result && saved.records && saved.records.length && restoreGame(saved));
    if (!resumed) {
      // Fresh game, keeping the last players and time control.
      var tc = saved && 'tc' in saved ? saved.tc : { base: 600000, inc: 0 };
      game = newGameState(tc, saved ? saved.white : 'p1', saved ? saved.black : 'p2');
      clock = { w: tc ? tc.base : 0, b: tc ? tc.base : 0, active: null, stamp: 0, running: false };
    }
    bottom = desiredBottom();
    render();
    if (settings.greeting) showGreeting(resumed ? 'resume' : 'new');
  }

  var probe = new Image();
  probe.onload = function () { defaultPhotoOk = true; boot(); };
  probe.onerror = function () { defaultPhotoOk = false; boot(); };
  probe.src = DEFAULT_PHOTO;

  if ('serviceWorker' in navigator && /^https?:$/.test(location.protocol)) {
    navigator.serviceWorker.register('sw.js').catch(function () {});
  }

  // Exposed for automated tests.
  window.__chessApp = {
    get chess() { return chess; }, get game() { return game; }, get clock() { return clock; },
    timeLeft: timeLeft, playMove: function (f, t, p) { return playMove(f, t, p || null, false); },
    startNewGame: startNewGame, pgn: pgn, pause: pause, resume: resume, undo: undoMove
  };
})();
