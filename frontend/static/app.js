(function () {
    "use strict";

    var TOTAL_LABS = 3;

    function getDone(lab) {
        return localStorage.getItem("probatio_done_" + lab) === "1";
    }

    function setDone(lab) {
        localStorage.setItem("probatio_done_" + lab, "1");
    }

    function highestDone() {
        var highest = 0;
        for (var i = 1; i <= TOTAL_LABS; i++) {
            if (getDone(i)) highest = i;
        }
        return highest;
    }

    function isUnlocked(lab) {
        if (lab === 1) return true;
        return getDone(lab - 1);
    }

    function updateSelector() {
        for (var i = 1; i <= TOTAL_LABS; i++) {
            var card = document.querySelector('.lab-card[data-lab="' + i + '"]');
            if (!card) continue;
            var btn = document.getElementById("btn-" + i);
            var status = document.getElementById("status-" + i);

            card.classList.remove("is-unlocked", "is-done");

            if (getDone(i)) {
                card.classList.add("is-done");
                if (status) status.textContent = "Concluído";
                if (btn) {
                    btn.classList.remove("is-disabled");
                    btn.textContent = "Revisitar";
                }
            } else if (isUnlocked(i)) {
                card.classList.add("is-unlocked");
                if (status) status.textContent = "Disponível";
                if (btn) {
                    btn.classList.remove("is-disabled");
                    btn.textContent = "Acessar";
                }
            } else {
                if (status) status.textContent = "Bloqueado";
                if (btn) {
                    btn.classList.add("is-disabled");
                    btn.textContent = "Conclua o anterior";
                }
            }
        }
    }

    function guardCurrentLab() {
        var match = window.location.pathname.match(/^\/lab\/(\d+)$/);
        if (!match) return;
        var lab = parseInt(match[1], 10);
        if (!isUnlocked(lab)) {
            window.location.replace("/");
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        updateSelector();
        guardCurrentLab();

        document.querySelectorAll(".lab__hints-btn").forEach(function (btn) {
            btn.addEventListener("click", function () {
                var id = "hints-" + btn.getAttribute("data-hints");
                var panel = document.getElementById(id);
                if (panel) panel.hidden = !panel.hidden;
            });
        });

        document.querySelectorAll(".flag-form").forEach(function (form) {
            form.addEventListener("submit", function (e) {
                e.preventDefault();
                var lab = form.getAttribute("data-lab");
                var input = form.querySelector(".flag-form__input");
                var msg = form.querySelector(".flag-form__msg");

                fetch("/submit", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ lab: parseInt(lab, 10), flag: input.value }),
                })
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                        msg.textContent = data.message;
                        msg.classList.toggle("is-success", data.valid);
                        msg.classList.toggle("is-error", !data.valid);
                        if (data.valid) {
                            setDone(parseInt(lab, 10));
                            updateSelector();
                        }
                    })
                    .catch(function () {
                        msg.textContent = "Erro de comunicação com o servidor.";
                        msg.classList.remove("is-success");
                        msg.classList.add("is-error");
                    });
            });
        });
    });
})();
