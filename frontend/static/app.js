(function () {
    "use strict";

    var TOTAL_LABS = 3;

    var START_CMD = {
        1: "docker compose up -d --build",
        2: "docker compose -f docker-compose.lab2.yml up -d --build",
        3: "docker compose -f docker-compose.lab3.yml up -d --build",
    };

    function pollActive() {
        var el = document.getElementById("lab-status");
        if (!el) return;
        fetch("/active")
            .then(function (r) { return r.json(); })
            .then(function (data) {
                var running = data.active || [];
                var match = window.location.pathname.match(/^\/lab\/(\d+)$/);
                if (match) {
                    var lab = parseInt(match[1], 10);
                    if (running.indexOf(lab) === -1) {
                        el.hidden = false;
                        el.className = "lab-status lab-status--warn";
                        el.innerHTML =
                            "ATENÇÃO: o laboratório deste desafio não está ativo. " +
                            "Pare o laboratório atual e inicie este: <code>" +
                            START_CMD[lab] + "</code>";
                    } else {
                        el.hidden = true;
                    }
                } else {
                    if (running.length === 1) {
                        el.hidden = false;
                        el.className = "lab-status lab-status--info";
                        el.textContent =
                            "Terminal conectado ao Desafio " + running[0] +
                            " (http://localhost:7681).";
                    } else if (running.length === 0) {
                        el.hidden = false;
                        el.className = "lab-status lab-status--warn";
                        el.innerHTML =
                            "Nenhum laboratório ativo. Inicie o Desafio 01: <code>" +
                            START_CMD[1] + "</code>";
                    } else {
                        el.hidden = false;
                        el.className = "lab-status lab-status--warn";
                        el.textContent =
                            "Vários laboratórios ativos ao mesmo tempo — " +
                            "derrube os demais: " +
                            running.map(function (n) { return "Desafio " + n; }).join(", ");
                    }
                }
            })
            .catch(function () { /* sem rede, ignora */ });
    }

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
        pollActive();
        setInterval(pollActive, 5000);

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
