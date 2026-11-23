import socket
from datetime import date, datetime

from flask import Flask, jsonify, request, send_from_directory

from risk import age_to_weight, risk_tier
from weather import get_hourly_readings

app = Flask(__name__, static_folder="static")
HOSTNAME = socket.gethostname()

@app.after_request
def add_server_header(response):
    # Lets you prove in the demo which server answered each reuest.
    response.headers["X-Served-By"] = HOSTNAME
    return response

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/forecast")
def forecast():
    weight_arg = request.args.get("weight")
    hatch_arg = request.args.get("hatch_date")
    age_days = None

    try:
        if weight_arg:
            weight = float(weight_arg)
        elif hatch_arg:
            hatched = datetime.strptime(hatch_arg, "%Y-%m-%d").date()
            age_days = (date.today() - hatched).days
            if age_days < 0 or age_days > 70:
                return jsonify(error="Hatch date must be within the last 70 days."), 400
            weight = age_to_weight(age_days)
        else:
            return jsonify(error="Provide hatch_date (YYYY-MM-DD) or weight in kg."), 400
    except ValueError:
        return jsonify(error="Invalid weight or hatch date format."), 400

    if not 0.03 <= weight <= 5:
        return jsonify(error="Weight must be between 0.03 and 5kg."), 400

    try:
        readings = get_hourly_readings()
    except RuntimeError as error:
        return jsonify(error=str(error)), 502

    results = []
    for r in readings:
        if r["temp_c"] is None or r["humidity"] is None:
            continue
        results.append({**r, **risk_tier(r["temp_c"], r["humidity"], weight)})

    return jsonify(
        server=HOSTNAME,
        age_days=age_days,
        weight_kg=round(weight, 3),
        readings=results,
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)