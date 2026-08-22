import os

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

FLAG_PATH = "/flag/flag.txt"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()
    submitted = data.get("flag", "").strip()

    if not submitted:
        return jsonify({"valid": False, "message": "Nenhuma flag enviada."})

    if not os.path.exists(FLAG_PATH):
        return jsonify({
            "valid": False,
            "message": (
                "Ainda nao ha flag gerada. "
                "Execute o ataque primeiro para gerar a flag."
            ),
        })

    with open(FLAG_PATH, "r") as f:
        expected = f.read().strip()

    if submitted == expected:
        return jsonify({
            "valid": True,
            "message": "Flag correta! Desafio 01 concluido.",
        })
    else:
        return jsonify({
            "valid": False,
            "message": "Flag incorreta. Tente novamente.",
        })


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
