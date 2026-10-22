// Board sounds synthesised with Web Audio (no audio files needed offline),
// plus speech for the player greeting (Android TextToSpeech or Web Speech).
(function () {
  'use strict';
  var ctx = null, noiseBuf = null;
  var enabled = true;

  function audio() {
    if (!ctx) {
      var AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return null;
      ctx = new AC();
      noiseBuf = ctx.createBuffer(1, ctx.sampleRate * 0.25, ctx.sampleRate);
      var d = noiseBuf.getChannelData(0);
      for (var i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    }
    if (ctx.state === 'suspended') ctx.resume();
    return ctx;
  }

  // A wooden "tock": a filtered noise burst on top of a short low sine thump.
  function knock(at, gain, freq) {
    var c = ctx, t = c.currentTime + (at || 0);
    var src = c.createBufferSource(); src.buffer = noiseBuf;
    var bp = c.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = freq || 1700; bp.Q.value = 1.4;
    var g = c.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(gain, t + 0.003);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.07);
    src.connect(bp); bp.connect(g); g.connect(c.destination);
    src.start(t); src.stop(t + 0.1);
    tone(at, 150, 0.06, gain * 0.9, 'sine');
  }

  function tone(at, freq, dur, gain, type) {
    var c = ctx, t = c.currentTime + (at || 0);
    var o = c.createOscillator(); o.type = type || 'sine'; o.frequency.value = freq;
    var g = c.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(gain, t + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g); g.connect(c.destination);
    o.start(t); o.stop(t + dur + 0.02);
  }

  var SOUNDS = {
    move: function () { knock(0, 0.5, 1500); },
    capture: function () { knock(0, 0.8, 2300); knock(0.035, 0.35, 1200); },
    castle: function () { knock(0, 0.45, 1500); knock(0.11, 0.45, 1300); },
    check: function () { knock(0, 0.55, 1700); tone(0.02, 880, 0.18, 0.12, 'triangle'); },
    promote: function () { knock(0, 0.5, 1500); tone(0.03, 660, 0.12, 0.1, 'triangle'); tone(0.12, 990, 0.2, 0.1, 'triangle'); },
    illegal: function () { tone(0, 160, 0.16, 0.18, 'square'); },
    start: function () { tone(0, 523, 0.16, 0.12, 'triangle'); tone(0.12, 784, 0.3, 0.12, 'triangle'); },
    end: function () { tone(0, 784, 0.16, 0.12, 'triangle'); tone(0.13, 659, 0.16, 0.12, 'triangle'); tone(0.26, 523, 0.4, 0.12, 'triangle'); },
    lowtime: function () { tone(0, 1320, 0.08, 0.1, 'sine'); tone(0.14, 1320, 0.08, 0.1, 'sine'); }
  };

  window.Sound = {
    setEnabled: function (on) { enabled = !!on; },
    unlock: function () { audio(); },
    play: function (name) {
      if (!enabled || !SOUNDS[name]) return;
      try { if (audio()) SOUNDS[name](); } catch (e) { /* audio is optional */ }
    },
    speak: function (text) {
      if (!enabled) return;
      try {
        if (window.AndroidBridge && AndroidBridge.speak) { AndroidBridge.speak(text); return; }
        if ('speechSynthesis' in window) {
          window.speechSynthesis.cancel();
          var u = new SpeechSynthesisUtterance(text);
          u.rate = 1; u.pitch = 1;
          window.speechSynthesis.speak(u);
        }
      } catch (e) { /* speech is optional */ }
    }
  };
})();
