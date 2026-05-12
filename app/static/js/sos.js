/* =========================================================
   SocialHealth — SOS module client logic
   Vanilla JS, no dependencies.
   ========================================================= */

(function () {
    "use strict";

    /* =================================================================
       BREATHING 4-7-8
       ================================================================= */

    function initBreathing() {
        var circle      = document.getElementById("breathCircle");
        var phaseEl     = document.getElementById("breathPhase");
        var countEl     = document.getElementById("breathCount");
        var cycleEl     = document.getElementById("breathCycle");
        var btnToggle   = document.getElementById("breathToggle");
        var btnReset    = document.getElementById("breathReset");
        var soundToggle = document.getElementById("breathSound");

        if (!circle || !phaseEl || !countEl || !btnToggle) return;

        var PHASES = [
            { name: "inhale", label: "Вдох",             seconds: 4, freq: 440 },
            { name: "hold",   label: "Задержи дыхание",  seconds: 7, freq: 392 },
            { name: "exhale", label: "Выдох",            seconds: 8, freq: 330 }
        ];

        var state = {
            running:    false,
            phaseIdx:   0,
            secondsLeft: PHASES[0].seconds,
            cycle:      1,
            timerId:    null,
            soundOn:    false,
            audioCtx:   null
        };

        function applyPhaseClass(name) {
            circle.classList.remove("phase-inhale", "phase-hold", "phase-exhale");
            circle.classList.add("phase-" + name);
            circle.textContent = ""; // фаза показывается ниже, в круге только цвет/размер
        }

        function render() {
            var p = PHASES[state.phaseIdx];
            phaseEl.textContent = p.label;
            countEl.textContent = state.secondsLeft;
            cycleEl.textContent = "Цикл " + state.cycle + " из ∞";
            applyPhaseClass(p.name);
        }

        function beep(freq) {
            if (!state.soundOn) return;
            try {
                if (!state.audioCtx) {
                    var Ctx = window.AudioContext || window.webkitAudioContext;
                    if (!Ctx) return;
                    state.audioCtx = new Ctx();
                }
                var ctx = state.audioCtx;
                var osc = ctx.createOscillator();
                var gain = ctx.createGain();
                osc.type = "sine";
                osc.frequency.value = freq;
                gain.gain.setValueAtTime(0.0001, ctx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.06, ctx.currentTime + 0.04);
                gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.25);
                osc.connect(gain).connect(ctx.destination);
                osc.start();
                osc.stop(ctx.currentTime + 0.3);
            } catch (_) { /* ignore */ }
        }

        function tick() {
            state.secondsLeft -= 1;
            if (state.secondsLeft <= 0) {
                state.phaseIdx = (state.phaseIdx + 1) % PHASES.length;
                if (state.phaseIdx === 0) state.cycle += 1;
                state.secondsLeft = PHASES[state.phaseIdx].seconds;
                beep(PHASES[state.phaseIdx].freq);
            }
            render();
        }

        function start() {
            if (state.running) return;
            state.running = true;
            btnToggle.textContent = "Пауза";
            // первый тик «прямо сейчас» не нужен — обновим экран и через 1 сек сделаем шаг
            render();
            beep(PHASES[state.phaseIdx].freq);
            state.timerId = setInterval(tick, 1000);
        }

        function pause() {
            state.running = false;
            btnToggle.textContent = "Старт";
            if (state.timerId) { clearInterval(state.timerId); state.timerId = null; }
        }

        function reset() {
            pause();
            state.phaseIdx = 0;
            state.secondsLeft = PHASES[0].seconds;
            state.cycle = 1;
            render();
        }

        btnToggle.addEventListener("click", function () {
            if (state.running) pause(); else start();
        });
        if (btnReset) btnReset.addEventListener("click", reset);

        if (soundToggle) {
            soundToggle.addEventListener("change", function () {
                state.soundOn = !!soundToggle.checked;
            });
        }

        render();
    }

    /* =================================================================
       GROUNDING 5-4-3-2-1
       ================================================================= */

    function initGrounding() {
        var root = document.getElementById("groundRoot");
        if (!root) return;

        var STEPS = [
            { icon: "👁", count: 5, title: "5 вещей, которые ты ВИДИШЬ прямо сейчас",
              placeholder: "Что-то рядом..." },
            { icon: "👂", count: 4, title: "4 звука, которые ты СЛЫШИШЬ",
              placeholder: "Какой-то звук..." },
            { icon: "✋", count: 3, title: "3 вещи, которые ты можешь ПОТРОГАТЬ",
              placeholder: "Поверхность, ткань..." },
            { icon: "👃", count: 2, title: "2 запаха, которые ты ЧУВСТВУЕШЬ",
              placeholder: "Какой-то запах..." },
            { icon: "👅", count: 1, title: "1 вкус, который ты ОЩУЩАЕШЬ",
              placeholder: "Вкус во рту..." }
        ];

        var fill        = document.getElementById("groundProgressFill");
        var label       = document.getElementById("groundProgressLabel");
        var stepHost    = document.getElementById("groundStep");
        var finishHost  = document.getElementById("groundFinish");
        var helpLine    = document.getElementById("groundHelpLine");

        // данные не сохраняются на сервер — храним только в памяти на время сессии
        var answers = STEPS.map(function (s) { return new Array(s.count).fill(""); });
        var idx = 0;

        function renderProgress() {
            var pct = (idx / STEPS.length) * 100;
            if (fill)  fill.style.width = pct + "%";
            if (label) label.textContent = "Шаг " + Math.min(idx + 1, STEPS.length) + " из " + STEPS.length;
        }

        function buildStep() {
            var s = STEPS[idx];
            var inputs = "";
            for (var i = 0; i < s.count; i++) {
                var val = answers[idx][i] || "";
                inputs += '<input type="text" data-i="' + i + '" placeholder="' + s.placeholder + '" value="' +
                         val.replace(/"/g, "&quot;") + '" autocomplete="off" maxlength="120">';
            }

            var isLast = idx === STEPS.length - 1;
            var html = ''
                + '<div class="ground-step">'
                +   '<div class="step-icon">' + s.icon + '</div>'
                +   '<h2>' + s.title + '</h2>'
                +   '<div class="ground-inputs">' + inputs + '</div>'
                +   '<div class="ground-nav">'
                +     '<button type="button" class="btn-sos" id="groundBack" '
                +       (idx === 0 ? 'aria-disabled="true" disabled' : '') + '>← Назад</button>'
                +     '<div class="group">'
                +       '<button type="button" class="btn-sos" id="groundSkip">Пропустить шаг</button>'
                +       '<button type="button" class="btn-sos primary" id="groundNext">'
                +         (isLast ? "Завершить" : "Далее →") + '</button>'
                +     '</div>'
                +   '</div>'
                + '</div>';
            stepHost.innerHTML = html;

            // bind inputs
            var nodes = stepHost.querySelectorAll('input[type="text"]');
            nodes.forEach(function (n) {
                n.addEventListener("input", function () {
                    var i = parseInt(n.getAttribute("data-i"), 10);
                    answers[idx][i] = n.value;
                });
            });

            document.getElementById("groundNext").addEventListener("click", goNext);
            document.getElementById("groundSkip").addEventListener("click", goNext);
            var backBtn = document.getElementById("groundBack");
            if (backBtn && idx > 0) backBtn.addEventListener("click", goBack);
        }

        function goNext() {
            if (idx >= STEPS.length - 1) { finish(); return; }
            idx += 1;
            renderProgress();
            buildStep();
        }

        function goBack() {
            if (idx <= 0) return;
            idx -= 1;
            renderProgress();
            buildStep();
        }

        function finish() {
            stepHost.style.display = "none";
            if (fill)  fill.style.width = "100%";
            if (label) label.textContent = "Шаг " + STEPS.length + " из " + STEPS.length;
            finishHost.style.display = "block";
        }

        // feeling buttons
        var feelBtns = root.querySelectorAll("[data-feel]");
        feelBtns.forEach(function (b) {
            b.addEventListener("click", function () {
                if (b.getAttribute("data-feel") === "help" && helpLine) {
                    helpLine.classList.add("show");
                } else if (helpLine) {
                    helpLine.classList.remove("show");
                }
            });
        });

        renderProgress();
        buildStep();
    }

    /* ================================================================= */

    document.addEventListener("DOMContentLoaded", function () {
        initBreathing();
        initGrounding();
    });
})();
