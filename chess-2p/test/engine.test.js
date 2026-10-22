// Engine tests: perft move counts on the standard positions from
// https://www.chessprogramming.org/Perft_Results, plus the game-ending rules.
// Run: node chess-2p/test/engine.test.js   (add --deep for the slow depths)
'use strict';
const Chess = require('../www/js/chess.js');
const assert = require('assert');
const deep = process.argv.includes('--deep');

const PERFT = [
  ['rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', [20, 400, 8902, 197281], 4865609],
  ['r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1', [48, 2039, 97862], 4085603],
  ['8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1', [14, 191, 2812, 43238], 674624],
  ['r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1', [6, 264, 9467], 422333],
  ['rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8', [44, 1486, 62379], 2103487],
  ['r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10', [46, 2079, 89890], 3894594],
];

let passed = 0;
function check(name, fn) {
  try { fn(); passed++; console.log('ok   ' + name); }
  catch (e) { console.log('FAIL ' + name + '\n     ' + e.message); process.exitCode = 1; }
}

PERFT.forEach(([fen, counts, deepCount], i) => {
  check('perft position ' + (i + 1), () => {
    const c = new Chess(fen);
    counts.forEach((n, d) => assert.strictEqual(c.perft(d + 1), n, 'depth ' + (d + 1)));
    assert.strictEqual(c.fen(), new Chess(fen).fen(), 'make/unmake restores the position');
    if (deep) assert.strictEqual(c.perft(counts.length + 1), deepCount, 'depth ' + (counts.length + 1));
  });
});

function play(moves, fen) {
  const c = new Chess(fen);
  moves.split(/\s+/).filter(Boolean).forEach(m => assert.ok(c.move(m), 'illegal: ' + m));
  return c;
}

check("fool's mate is checkmate, SAN ends in #", () => {
  const c = play('f3 e5 g4 Qh4');
  assert.strictEqual(c.history[3].san, 'Qh4#');
  assert.deepStrictEqual(c.outcome(), { result: '0-1', winner: 'b', reason: 'checkmate' });
});

check('stalemate', () => {
  const c = new Chess('7k/5Q2/6K1/8/8/8/8/8 b - - 0 1');
  assert.strictEqual(c.outcome().reason, 'stalemate');
});

check('threefold repetition (non-consecutive allowed)', () => {
  const c = play('Nf3 Nf6 Ng1 Ng8 Nf3 Nf6 Ng1');
  assert.strictEqual(c.outcome(), null);
  c.move('Ng8');
  assert.strictEqual(c.outcome().reason, 'repetition');
});

check('repetition ignores an en-passant square with no legal capture', () => {
  // After 1.e4 the ep square e3 exists in FEN but no black pawn can take, so
  // the position counts the same as later identical positions.
  const c = play('e4 Nf6 Nf3 Ng8 Ng1 Nf6 Nf3 Ng8 Ng1');
  assert.strictEqual(c.outcome().reason, 'repetition');
});

check('50-move rule', () => {
  const c = new Chess('8/8/4k3/8/8/4K3/8/R7 w - - 99 80');
  c.move('Ra2');
  assert.strictEqual(c.outcome().reason, 'fifty');
});

check('checkmate on the 100th half-move beats the 50-move rule', () => {
  const c = new Chess('7k/8/6K1/8/8/8/8/R7 w - - 99 80');
  c.move('Ra8');
  assert.strictEqual(c.outcome().reason, 'checkmate');
});

check('insufficient material: K v K, K+B v K, K+N v K+B, K+B v K+B', () => {
  ['8/8/4k3/8/8/4K3/8/8 w - - 0 1', '8/8/4k3/8/8/4K3/8/5B2 w - - 0 1',
    '8/8/4k1n1/8/8/4K3/8/5B2 w - - 0 1', '8/8/2b1k3/8/8/4K3/8/5B2 w - - 0 1', '8/8/3bk3/8/8/4K3/8/5B2 w - - 0 1']
    .forEach(f => assert.ok(new Chess(f).isInsufficientMaterial(), f));
  ['8/8/4k3/8/8/4K3/8/4NN2 w - - 0 1', '8/8/4k3/8/8/4K3/4P3/8 w - - 0 1']
    .forEach(f => assert.ok(!new Chess(f).isInsufficientMaterial(), f));
});

check('timeout material rule: K+N+N can still win on time, K+B cannot', () => {
  assert.ok(!new Chess('8/8/4k3/8/8/4K3/8/4NN2 w - - 0 1').insufficientFor('w', true));
  assert.ok(new Chess('8/8/4k3/8/8/4K3/8/5B2 w - - 0 1').insufficientFor('w', true));
  assert.ok(new Chess('8/8/4k3/8/8/4K3/8/5B2 w - - 0 1').insufficientFor('b', true));
});

check('castling rules', () => {
  // Cannot castle through an attacked square (f1 attacked by the bishop on c4).
  let c = new Chess('4k3/8/8/8/2b5/8/8/4K2R w K - 0 1');
  assert.ok(!c.move('O-O'));
  // Queenside: b1 attacked is fine, d1 attacked is not.
  c = new Chess('1r2k3/8/8/8/8/8/8/R3K3 w Q - 0 1');
  assert.ok(c.move('O-O-O'), 'b1 attacked does not stop O-O-O');
  c = new Chess('3rk3/8/8/8/8/8/8/R3K3 w Q - 0 1');
  assert.ok(!c.move('O-O-O'), 'd1 attacked stops O-O-O');
  // Rights are lost when the rook is captured.
  c = play('e4 b6 d4 Bb7 Nc3 Bxe4 Nxe4 Nc6 Nf3 Nxd4 Nxd4 Qc8 Bb5 Qb7 Nd2 Qxg2 Nf5 Qxh1');
  assert.ok(!/K/.test(c.fen().split(' ')[2]));
});

check('en passant, including the pinned-pawn case', () => {
  let c = play('e4 a6 e5 d5');
  assert.strictEqual(c.move('exd6').san, 'exd6');
  // Capturing en passant would expose the king along the rank: illegal.
  c = new Chess('8/8/8/K2pP2r/8/8/8/7k w - d6 0 1');
  assert.ok(!c.move('exd6'));
});

check('promotion and SAN disambiguation', () => {
  let c = new Chess('8/P7/8/8/8/8/8/k6K w - - 0 1');
  assert.strictEqual(c.move({ from: 'a7', to: 'a8', promotion: 'n' }).san, 'a8=N');
  c = new Chess('k7/8/8/8/8/8/4K3/R6R w - - 0 1');
  assert.strictEqual(c.move({ from: 'a1', to: 'd1' }).san, 'Rad1');
  c = new Chess('7k/8/8/8/R7/8/8/R3K3 w - - 0 1');
  assert.strictEqual(c.move({ from: 'a4', to: 'a3' }).san, 'R4a3');
});

check('undo restores the exact position and repetition counts', () => {
  const c = play('e4 e5 Nf3 Nc6 Bb5 a6 Bxc6 dxc6 O-O');
  const fen = c.fen();
  c.move('Bg4'); c.undo();
  assert.strictEqual(c.fen(), fen);
  while (c.undo());
  assert.strictEqual(c.fen(), Chess.START_FEN);
  assert.deepStrictEqual(Object.values(c.positionCounts), [1]);
});

console.log('\n' + passed + ' passed' + (process.exitCode ? ', some FAILED' : ''));
