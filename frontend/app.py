import os

from flask import Flask, abort, jsonify, render_template, request

app = Flask(__name__)

FLAG_DIR = "/flags"
VALID_LABS = (1, 2, 3)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/lab/<int:lab>")
def lab(lab):
    if lab not in VALID_LABS:
        abort(404)
    return render_template(f"lab{lab}.html")


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


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
