import os
import time

import markdown
from flask import Flask, abort, jsonify, render_template, request

app = Flask(__name__)

FLAG_DIR = "/flags"
HINTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hints")
VALID_LABS = (1, 2, 3)


def render_hints(lab):
    path = os.path.join(HINTS_DIR, f"hints-lab{lab}.md")
    try:
        with open(path, "r") as f:
            return markdown.markdown(f.read(), extensions=["fenced_code", "tables"])
    except OSError:
        return "<p>Dicas não disponíveis.</p>"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/lab/<int:lab>")
def lab(lab):
    if lab not in VALID_LABS:
        abort(404)
    return render_template(f"lab{lab}.html", hints_html=render_hints(lab))


@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json(silent=True) or {}

    try:
        lab = int(data.get("lab"))
    except (TypeError, ValueError):
        return jsonify({"valid": False, "message": "Desafio inválido."})

    if lab not in VALID_LABS:
        return jsonify({"valid": False, "message": "Desafio inválido."})

    submitted = (data.get("flag") or "").strip()
    if not submitted:
        return jsonify({"valid": False, "message": "Cole a flag no campo acima."})

    flag_path = os.path.join(FLAG_DIR, f"lab{lab}", "flag.txt")
    if not os.path.exists(flag_path):
        return jsonify({
            "valid": False,
            "message": (
                f"A flag do desafio {lab} ainda não foi gerada. "
                "Verifique se o laboratório está rodando e se o ataque "
                "foi executado."
            ),
        })

    with open(flag_path, "r") as f:
        expected = f.read().strip()

    if submitted == expected:
        return jsonify({
            "valid": True,
            "message": f"Flag correta! Desafio {lab} concluído.",
        })
    return jsonify({
        "valid": False,
        "message": f"Flag incorreta para o desafio {lab}. Tente novamente.",
    })


@app.route("/active")
def active():
    now = time.time()
    running = []
    for n in VALID_LABS:
        heartbeat = os.path.join(FLAG_DIR, f"lab{n}", ".heartbeat")
        try:
            if now - os.path.getmtime(heartbeat) < 10:
                running.append(n)
        except OSError:
            pass
    return jsonify({"active": running})


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
