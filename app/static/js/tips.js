/* =========================================================
   SocialHealth — tips category filter
   Vanilla JS, без библиотек.
   ========================================================= */

(function () {
    "use strict";

    function initFilters() {
        var filters = document.querySelectorAll(".tip-filter");
        var cards   = document.querySelectorAll(".tip-card");
        var grid    = document.getElementById("tipsGrid");
        var empty   = document.getElementById("tipsEmpty");
        if (!filters.length || !cards.length) return;

        function applyFilter(category) {
            var visibleCount = 0;

            cards.forEach(function (card) {
                var cat = card.getAttribute("data-category");
                var match = category === "all" || cat === category;

                if (match) {
                    card.classList.remove("hidden");
                    // мини-перезапуск анимации, чтобы карточки появились снова
                    card.style.animation = "none";
                    void card.offsetWidth; // force reflow
                    card.style.animation = "";
                    visibleCount += 1;
                } else {
                    card.classList.add("hidden");
                }
            });

            if (empty) {
                empty.style.display = visibleCount === 0 ? "block" : "none";
            }
        }

        filters.forEach(function (btn) {
            btn.addEventListener("click", function () {
                filters.forEach(function (b) { b.classList.remove("active"); });
                btn.classList.add("active");

                var category = btn.getAttribute("data-category") || "all";

                if (grid) {
                    grid.classList.add("fading-out");
                    setTimeout(function () {
                        applyFilter(category);
                        grid.classList.remove("fading-out");
                    }, 180);
                } else {
                    applyFilter(category);
                }

                // Не трогаем URL — фильтрация чисто на клиенте.
                // Серверный fallback (?category=...) тоже работает.
            });
        });
    }

    document.addEventListener("DOMContentLoaded", initFilters);
})();
