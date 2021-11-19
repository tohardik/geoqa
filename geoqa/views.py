from flask import render_template, request, jsonify

from geoqa import app
from geoqa.service.orchestration import Orchestrator

from geoqa import app as flask_app


@app.route("/")
def index():
    qa()
    return render_template("index.html")


@app.route("/qa", methods=["POST", "GET"])
def qa():
    try:
        if request.method == "POST":
            query = request.form.get('query')
            lang = request.form.get('lang', 'en')
        else:
            query = request.args.get('query')
            lang = request.args.get('lang', 'en')

        flask_app.logger.info(f"{request.method} /qa {query}")

        orchestration_service = Orchestrator()
        answer = orchestration_service.answer_question(query, lang)
        return jsonify(get_qald_format_answer(answer))
    except Exception as e:
        flask_app.logger.error(f"Error: {str(e)}")
        return jsonify({
            "head": {
                "vars": ["x"]
            },
            "results": {
                "bindings": []
            }
        })


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
