/*
 * Chess rules engine: legal move generation, SAN, FEN, PGN and every way a
 * game can end (checkmate, stalemate, threefold repetition, 50-move rule,
 * insufficient material). Squares are 0..63 in FEN order: 0 = a8, 63 = h1.
 * Works in the browser (window.Chess) and in Node (module.exports) for tests.
 */
(function (root) {
  'use strict';

  var START_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
  var FILES = 'abcdefgh';
  var VALUES = { p: 1, n: 3, b: 3, r: 5, q: 9, k: 0 };

  // Castling rights bitmask: 1 = K, 2 = Q, 4 = k, 8 = q.
  var CASTLE_MASK = new Array(64).fill(0);
  CASTLE_MASK[63] = 1; CASTLE_MASK[56] = 2; CASTLE_MASK[60] = 3;
  CASTLE_MASK[7] = 4; CASTLE_MASK[0] = 8; CASTLE_MASK[4] = 12;

  // Precomputed jump targets and sliding rays for every square.
  var KNIGHT = [], KING = [], RAYS = { b: [], r: [] };
  (function precompute() {
    var n = [[-2, -1], [-2, 1], [-1, -2], [-1, 2], [1, -2], [1, 2], [2, -1], [2, 1]];
    var k = [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]];
    var dirs = { b: [[-1, -1], [-1, 1], [1, -1], [1, 1]], r: [[-1, 0], [1, 0], [0, -1], [0, 1]] };
    for (var sq = 0; sq < 64; sq++) {
      var r = sq >> 3, f = sq & 7;
      KNIGHT[sq] = jumps(r, f, n);
      KING[sq] = jumps(r, f, k);
      for (var t in dirs) {
        RAYS[t][sq] = dirs[t].map(function (d) {
          var ray = [], rr = r + d[0], ff = f + d[1];
          while (rr >= 0 && rr < 8 && ff >= 0 && ff < 8) { ray.push(rr * 8 + ff); rr += d[0]; ff += d[1]; }
          return ray;
        });
      }
    }
    function jumps(r, f, offs) {
      var out = [];
      offs.forEach(function (o) {
        var rr = r + o[0], ff = f + o[1];
        if (rr >= 0 && rr < 8 && ff >= 0 && ff < 8) out.push(rr * 8 + ff);
      });
      return out;
    }
  })();

  function colorOf(p) { return p === p.toUpperCase() ? 'w' : 'b'; }
  function typeOf(p) { return p.toLowerCase(); }
  function other(c) { return c === 'w' ? 'b' : 'w'; }
  function sqName(sq) { return FILES[sq & 7] + (8 - (sq >> 3)); }
  function sqIndex(name) { return (8 - parseInt(name[1], 10)) * 8 + FILES.indexOf(name[0]); }
  function squareColor(sq) { return ((sq >> 3) + (sq & 7)) % 2 === 0 ? 'light' : 'dark'; }

  function Chess(fen) {
    this.load(fen || START_FEN);
  }

  Chess.START_FEN = START_FEN;
  Chess.VALUES = VALUES;
  Chess.sqName = sqName;
  Chess.sqIndex = sqIndex;
  Chess.colorOf = colorOf;

  Chess.prototype.load = function (fen) {
    var parts = fen.trim().split(/\s+/);
    if (parts.length < 4) throw new Error('Bad FEN: ' + fen);
    this.board = new Array(64).fill(null);
    this.kings = { w: -1, b: -1 };
    var sq = 0;
    for (var i = 0; i < parts[0].length; i++) {
      var ch = parts[0][i];
      if (ch === '/') continue;
      if (/\d/.test(ch)) { sq += parseInt(ch, 10); continue; }
      this.board[sq] = ch;
      if (ch === 'K') this.kings.w = sq;
      if (ch === 'k') this.kings.b = sq;
      sq++;
    }
    if (sq !== 64 || this.kings.w < 0 || this.kings.b < 0) throw new Error('Bad FEN: ' + fen);
    this.turn = parts[1] === 'b' ? 'b' : 'w';
    this.castling = 0;
    if (parts[2].indexOf('K') >= 0) this.castling |= 1;
    if (parts[2].indexOf('Q') >= 0) this.castling |= 2;
    if (parts[2].indexOf('k') >= 0) this.castling |= 4;
    if (parts[2].indexOf('q') >= 0) this.castling |= 8;
    this.ep = parts[3] === '-' ? -1 : sqIndex(parts[3]);
    this.halfmove = parts[4] ? parseInt(parts[4], 10) : 0;
    this.fullmove = parts[5] ? parseInt(parts[5], 10) : 1;
    this.stack = [];
    this.history = [];
    this.startFen = this.fen();
    this.positionCounts = {};
    this.positionCounts[this.positionKey()] = 1;
  };

  Chess.prototype.fen = function () {
    var out = '';
    for (var r = 0; r < 8; r++) {
      var empty = 0;
      for (var f = 0; f < 8; f++) {
        var p = this.board[r * 8 + f];
        if (!p) { empty++; continue; }
        if (empty) { out += empty; empty = 0; }
        out += p;
      }
      if (empty) out += empty;
      if (r < 7) out += '/';
    }
    var c = '';
    if (this.castling & 1) c += 'K';
    if (this.castling & 2) c += 'Q';
    if (this.castling & 4) c += 'k';
    if (this.castling & 8) c += 'q';
    return out + ' ' + this.turn + ' ' + (c || '-') + ' ' + (this.ep >= 0 ? sqName(this.ep) : '-') +
      ' ' + this.halfmove + ' ' + this.fullmove;
  };

  // Identity of a position for the repetition rule: placement, side to move,
  // castling rights, and the en-passant square only when a capture there is legal.
  Chess.prototype.positionKey = function () {
    var f = this.fen().split(' ');
    var ep = '-';
    if (this.ep >= 0) {
      var self = this;
      if (this.legalMoves().some(function (m) { return m.flag === 'ep'; })) ep = f[3];
      void self;
    }
    return f[0] + ' ' + f[1] + ' ' + f[2] + ' ' + ep;
  };

  Chess.prototype.isAttacked = function (sq, by) {
    var b = this.board, i, t, p;
    // Pawns: a white pawn attacks diagonally upward (towards row 0).
    var r = sq >> 3, f = sq & 7;
    if (by === 'w') {
      if (r < 7) {
        if (f > 0 && b[sq + 7] === 'P') return true;
        if (f < 7 && b[sq + 9] === 'P') return true;
      }
    } else if (r > 0) {
      if (f > 0 && b[sq - 9] === 'p') return true;
      if (f < 7 && b[sq - 7] === 'p') return true;
    }
    var N = by === 'w' ? 'N' : 'n', K = by === 'w' ? 'K' : 'k';
    var B = by === 'w' ? 'B' : 'b', R = by === 'w' ? 'R' : 'r', Q = by === 'w' ? 'Q' : 'q';
    var kn = KNIGHT[sq];
    for (i = 0; i < kn.length; i++) if (b[kn[i]] === N) return true;
    var kg = KING[sq];
    for (i = 0; i < kg.length; i++) if (b[kg[i]] === K) return true;
    var rays = RAYS.b[sq];
    for (t = 0; t < 4; t++) {
      var ray = rays[t];
      for (i = 0; i < ray.length; i++) {
        p = b[ray[i]];
        if (p) { if (p === B || p === Q) return true; break; }
      }
    }
    rays = RAYS.r[sq];
    for (t = 0; t < 4; t++) {
      ray = rays[t];
      for (i = 0; i < ray.length; i++) {
        p = b[ray[i]];
        if (p) { if (p === R || p === Q) return true; break; }
      }
    }
    return false;
  };

  Chess.prototype.inCheck = function (color) {
    color = color || this.turn;
    return this.isAttacked(this.kings[color], other(color));
  };

  Chess.prototype.pseudoMoves = function () {
    var b = this.board, us = this.turn, them = other(us), out = [];
    var white = us === 'w';
    for (var sq = 0; sq < 64; sq++) {
      var p = b[sq];
      if (!p || colorOf(p) !== us) continue;
      var t = typeOf(p), i, to, q;
      if (t === 'p') {
        var dir = white ? -8 : 8, r = sq >> 3, f = sq & 7;
        var startRow = white ? 6 : 1, lastRow = white ? 1 : 6;
        to = sq + dir;
        if (!b[to]) {
          addPawn(sq, to, null, r === lastRow, null);
          if (r === startRow && !b[to + dir]) out.push({ from: sq, to: to + dir, piece: p, captured: null, promotion: null, flag: 'd' });
        }
        var caps = [];
        if (f > 0) caps.push(to - 1);
        if (f < 7) caps.push(to + 1);
        for (i = 0; i < caps.length; i++) {
          var c = caps[i];
          if (b[c] && colorOf(b[c]) === them) addPawn(sq, c, b[c], r === lastRow, null);
          else if (c === this.ep) out.push({ from: sq, to: c, piece: p, captured: white ? 'p' : 'P', promotion: null, flag: 'ep' });
        }
      } else if (t === 'n' || t === 'k') {
        var targets = t === 'n' ? KNIGHT[sq] : KING[sq];
        for (i = 0; i < targets.length; i++) {
          to = targets[i];
          if (!b[to] || colorOf(b[to]) === them) out.push({ from: sq, to: to, piece: p, captured: b[to], promotion: null, flag: null });
        }
      } else {
        var sets = t === 'b' ? [RAYS.b[sq]] : t === 'r' ? [RAYS.r[sq]] : [RAYS.b[sq], RAYS.r[sq]];
        for (var s = 0; s < sets.length; s++) {
          for (var d = 0; d < 4; d++) {
            var ray = sets[s][d];
            for (q = 0; q < ray.length; q++) {
              to = ray[q];
              if (!b[to]) { out.push({ from: sq, to: to, piece: p, captured: null, promotion: null, flag: null }); continue; }
              if (colorOf(b[to]) === them) out.push({ from: sq, to: to, piece: p, captured: b[to], promotion: null, flag: null });
              break;
            }
          }
        }
      }
    }
    // Castling: the king may not be in check, pass through or land on an attacked square.
    if (white && this.kings.w === 60 && !this.isAttacked(60, 'b')) {
      if ((this.castling & 1) && b[63] === 'R' && !b[61] && !b[62] && !this.isAttacked(61, 'b') && !this.isAttacked(62, 'b'))
        out.push({ from: 60, to: 62, piece: 'K', captured: null, promotion: null, flag: 'k' });
      if ((this.castling & 2) && b[56] === 'R' && !b[59] && !b[58] && !b[57] && !this.isAttacked(59, 'b') && !this.isAttacked(58, 'b'))
        out.push({ from: 60, to: 58, piece: 'K', captured: null, promotion: null, flag: 'q' });
    }
    if (!white && this.kings.b === 4 && !this.isAttacked(4, 'w')) {
      if ((this.castling & 4) && b[7] === 'r' && !b[5] && !b[6] && !this.isAttacked(5, 'w') && !this.isAttacked(6, 'w'))
        out.push({ from: 4, to: 6, piece: 'k', captured: null, promotion: null, flag: 'k' });
      if ((this.castling & 8) && b[0] === 'r' && !b[3] && !b[2] && !b[1] && !this.isAttacked(3, 'w') && !this.isAttacked(2, 'w'))
        out.push({ from: 4, to: 2, piece: 'k', captured: null, promotion: null, flag: 'q' });
    }
    return out;

    function addPawn(from, to, captured, promo) {
      var piece = b[from];
      if (promo) {
        ['q', 'r', 'b', 'n'].forEach(function (pp) {
          out.push({ from: from, to: to, piece: piece, captured: captured, promotion: white ? pp.toUpperCase() : pp, flag: null });
        });
      } else {
        out.push({ from: from, to: to, piece: piece, captured: captured, promotion: null, flag: null });
      }
    }
  };

  // Low-level make/unmake used by both legality checks and real moves.
  Chess.prototype._make = function (m) {
    var b = this.board;
    this.stack.push({ castling: this.castling, ep: this.ep, halfmove: this.halfmove, fullmove: this.fullmove });
    b[m.from] = null;
    b[m.to] = m.promotion || m.piece;
    if (m.flag === 'ep') b[this.turn === 'w' ? m.to + 8 : m.to - 8] = null;
    else if (m.flag === 'k') { b[m.to - 1] = b[m.to + 1]; b[m.to + 1] = null; }
    else if (m.flag === 'q') { b[m.to + 1] = b[m.to - 2]; b[m.to - 2] = null; }
    if (m.piece === 'K') this.kings.w = m.to;
    else if (m.piece === 'k') this.kings.b = m.to;
    this.castling &= ~(CASTLE_MASK[m.from] | CASTLE_MASK[m.to]);
    this.ep = m.flag === 'd' ? (m.from + m.to) >> 1 : -1;
    this.halfmove = (typeOf(m.piece) === 'p' || m.captured) ? 0 : this.halfmove + 1;
    if (this.turn === 'b') this.fullmove++;
    this.turn = other(this.turn);
  };

  Chess.prototype._unmake = function (m) {
    var b = this.board, s = this.stack.pop();
    this.turn = other(this.turn);
    this.castling = s.castling; this.ep = s.ep; this.halfmove = s.halfmove; this.fullmove = s.fullmove;
    b[m.from] = m.piece;
    if (m.flag === 'ep') { b[m.to] = null; b[this.turn === 'w' ? m.to + 8 : m.to - 8] = m.captured; }
    else b[m.to] = m.captured;
    if (m.flag === 'k') { b[m.to + 1] = b[m.to - 1]; b[m.to - 1] = null; }
    else if (m.flag === 'q') { b[m.to - 2] = b[m.to + 1]; b[m.to + 1] = null; }
    if (m.piece === 'K') this.kings.w = m.from;
    else if (m.piece === 'k') this.kings.b = m.from;
  };

  Chess.prototype.legalMoves = function (fromSq) {
    var us = this.turn, legal = [], pseudo = this.pseudoMoves();
    for (var i = 0; i < pseudo.length; i++) {
      var m = pseudo[i];
      if (fromSq !== undefined && m.from !== fromSq) continue;
      this._make(m);
      if (!this.isAttacked(this.kings[us], other(us))) legal.push(m);
      this._unmake(m);
    }
    return legal;
  };

  Chess.prototype.san = function (m, legal) {
    var s;
    if (m.flag === 'k') s = 'O-O';
    else if (m.flag === 'q') s = 'O-O-O';
    else {
      var t = typeOf(m.piece);
      var dest = sqName(m.to);
      if (t === 'p') {
        s = (m.captured ? FILES[m.from & 7] + 'x' : '') + dest;
        if (m.promotion) s += '=' + m.promotion.toUpperCase();
      } else {
        var rivals = (legal || this.legalMoves()).filter(function (o) {
          return o.piece === m.piece && o.to === m.to && o.from !== m.from;
        });
        var dis = '';
        if (rivals.length) {
          var sameFile = rivals.some(function (o) { return (o.from & 7) === (m.from & 7); });
          var sameRank = rivals.some(function (o) { return (o.from >> 3) === (m.from >> 3); });
          if (!sameFile) dis = FILES[m.from & 7];
          else if (!sameRank) dis = String(8 - (m.from >> 3));
          else dis = sqName(m.from);
        }
        s = t.toUpperCase() + dis + (m.captured ? 'x' : '') + dest;
      }
    }
    this._make(m);
    if (this.inCheck()) s += this.legalMoves().length ? '+' : '#';
    this._unmake(m);
    return s;
  };

  // Plays a legal move given {from, to, promotion} (squares as indexes or names),
  // a SAN string or a UCI string. Returns the full move record or null if illegal.
  Chess.prototype.move = function (input) {
    var legal = this.legalMoves(), m = null, i;
    if (typeof input === 'string') {
      var clean = input.replace(/[+#!?]/g, '');
      for (i = 0; i < legal.length && !m; i++) {
        var cand = legal[i];
        if (this.uci(cand) === input || this.san(cand, legal).replace(/[+#]/g, '') === clean) m = cand;
      }
    } else {
      var from = typeof input.from === 'string' ? sqIndex(input.from) : input.from;
      var to = typeof input.to === 'string' ? sqIndex(input.to) : input.to;
      var promo = input.promotion ? input.promotion.toLowerCase() : 'q';
      for (i = 0; i < legal.length && !m; i++) {
        var l = legal[i];
        if (l.from === from && l.to === to && (!l.promotion || l.promotion.toLowerCase() === promo)) m = l;
      }
    }
    if (!m) return null;
    var san = this.san(m, legal);
    var fenBefore = this.fen();
    this._make(m);
    var key = this.positionKey();
    this.positionCounts[key] = (this.positionCounts[key] || 0) + 1;
    var rec = {
      from: sqName(m.from), to: sqName(m.to), fromSq: m.from, toSq: m.to,
      piece: m.piece, captured: m.captured, promotion: m.promotion, flag: m.flag,
      san: san, uci: this.uci(m), color: colorOf(m.piece), fenBefore: fenBefore, fen: this.fen(), key: key, _m: m
    };
    this.history.push(rec);
    return rec;
  };

  Chess.prototype.undo = function () {
    var rec = this.history.pop();
    if (!rec) return null;
    this.positionCounts[rec.key]--;
    if (!this.positionCounts[rec.key]) delete this.positionCounts[rec.key];
    this._unmake(rec._m);
    return rec;
  };

  Chess.prototype.uci = function (m) {
    return sqName(m.from) + sqName(m.to) + (m.promotion ? m.promotion.toLowerCase() : '');
  };

  // chess.com treats a side as unable to mate when it has a lone king or a king
  // plus one minor piece. For flag-falls, K+N+N still counts as able to win.
  Chess.prototype.insufficientFor = function (color, forTimeout) {
    var minors = [], b = this.board;
    for (var sq = 0; sq < 64; sq++) {
      var p = b[sq];
      if (!p || colorOf(p) !== color) continue;
      var t = typeOf(p);
      if (t === 'k') continue;
      if (t === 'p' || t === 'r' || t === 'q') return false;
      minors.push(t);
    }
    if (minors.length === 0) return true;
    if (minors.length === 1) return true;
    if (!forTimeout && minors.length === 2 && minors[0] === 'n' && minors[1] === 'n') return true;
    return false;
  };

  // Dead position: neither side can ever deliver mate.
  Chess.prototype.isInsufficientMaterial = function () {
    var b = this.board, pieces = { w: [], b: [] }, bishopColors = {};
    for (var sq = 0; sq < 64; sq++) {
      var p = b[sq];
      if (!p || typeOf(p) === 'k') continue;
      var t = typeOf(p);
      if (t === 'p' || t === 'r' || t === 'q') return false;
      pieces[colorOf(p)].push(t);
      if (t === 'b') bishopColors[squareColor(sq)] = true;
    }
    var w = pieces.w, bl = pieces.b;
    // K vs K, K+minor vs K, K+minor vs K+minor (chess.com auto-draws these).
    if (w.length <= 1 && bl.length <= 1) return true;
    // Only bishops left, all on squares of one colour: mate is impossible.
    var all = w.concat(bl);
    if (all.every(function (t) { return t === 'b'; }) && Object.keys(bishopColors).length === 1) return true;
    return false;
  };

  Chess.prototype.isThreefold = function () {
    return (this.positionCounts[this.positionKey()] || 0) >= 3;
  };

  // Returns null while the game goes on, else { result: '1-0'|'0-1'|'1/2-1/2', winner, reason }.
  Chess.prototype.outcome = function () {
    var legal = this.legalMoves();
    if (!legal.length) {
      if (this.inCheck()) {
        var winner = other(this.turn);
        return { result: winner === 'w' ? '1-0' : '0-1', winner: winner, reason: 'checkmate' };
      }
      return { result: '1/2-1/2', winner: null, reason: 'stalemate' };
    }
    if (this.isInsufficientMaterial()) return { result: '1/2-1/2', winner: null, reason: 'insufficient' };
    if (this.isThreefold()) return { result: '1/2-1/2', winner: null, reason: 'repetition' };
    if (this.halfmove >= 100) return { result: '1/2-1/2', winner: null, reason: 'fifty' };
    return null;
  };

  Chess.prototype.get = function (sq) {
    return this.board[typeof sq === 'string' ? sqIndex(sq) : sq];
  };

  // Material on the board per side, in pawn units.
  Chess.prototype.material = function () {
    var out = { w: 0, b: 0 };
    for (var sq = 0; sq < 64; sq++) {
      var p = this.board[sq];
      if (p) out[colorOf(p)] += VALUES[typeOf(p)];
    }
    return out;
  };

  Chess.prototype.perft = function (depth) {
    if (depth === 0) return 1;
    var moves = this.legalMoves();
    if (depth === 1) return moves.length;
    var n = 0;
    for (var i = 0; i < moves.length; i++) {
      this._make(moves[i]);
      n += this.perft(depth - 1);
      this._unmake(moves[i]);
    }
    return n;
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = Chess;
  else root.Chess = Chess;
})(typeof window !== 'undefined' ? window : this);
