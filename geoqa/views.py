from flask import render_template, request, jsonify

from geoqa import app
from geoqa.service.orchestration import Orchestrator

orchestration_service = Orchestrator()


@app.route("/")
def index():
    qa()
    return render_template("index.html")


@app.route("/qa", methods=["POST", "GET"])
def qa():
    if request.method == "POST":
        query = request.form.get('query')
        lang = request.form.get('lang', 'en')
    else:
        query = request.args.get('query')
        lang = request.args.get('lang', 'en')

    orc = Orchestrator()
    answer = orc.answer_question(query, lang)
    return jsonify(get_qald_format_answer(answer))


def get_qald_format_answer(answer):
    return {
        "questions": [
            {
                "question": {
                    "answers": answer
                }
            }
        ]
    }
