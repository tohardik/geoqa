from flask import render_template, request

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
        query = request.form.get('core')
        lang = request.form.get('lang', 'en')
    else:
        query = request.args.get('core')
        lang = request.args.get('lang', 'en')

    orc = Orchestrator()
    orc.hello()
    return None

