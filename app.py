from flask import Flask, jsonify, render_template, request, Response
import io
import csv
import math

app = Flask(__name__)
verification_records = []

CIRCUITS = {
    "rc_lowpass": {
        "name": "RC Low-Pass Filter",
        "fields": [("R", "Resistance (Ω)", 10000), ("C", "Capacitance (F)", 1e-6), ("Vin", "Input voltage (V)", 5)],
    },
    "voltage_divider": {
        "name": "Voltage Divider",
        "fields": [("Vin", "Input voltage (V)", 12), ("R1", "R1 resistance (Ω)", 10000), ("R2", "R2 resistance (Ω)", 10000)],
    },
    "bjt_amplifier": {
        "name": "BJT Amplifier",
        "fields": [("Rc", "Collector resistance Rc (Ω)", 2200), ("re", "Emitter resistance / AC resistance re (Ω)", 25), ("sign", "Voltage gain sign (1 for magnitude)", 1)],
    },
    "inverting_opamp": {
        "name": "Inverting Op-Amp",
        "fields": [("Rin", "Input resistance Rin (Ω)", 10000), ("Rf", "Feedback resistance Rf (Ω)", 47000), ("Vin", "Input voltage (V)", 0.2)],
    },
    "half_wave_rectifier": {
        "name": "Half-Wave Rectifier",
        "fields": [("Vrms", "AC RMS voltage (V)", 12), ("Vd", "Diode forward drop (V)", 0.7)],
    },
    "led_resistor": {
        "name": "LED Series Resistor",
        "fields": [("Vs", "Supply voltage (V)", 5), ("Vf", "LED forward voltage (V)", 2), ("I", "LED current (A)", 0.01)],
    },
    "rc_highpass": {
        "name": "RC High-Pass Filter",
        "fields": [("R", "Resistance (Ω)", 10000), ("C", "Capacitance (F)", 1e-6), ("Vin", "Input voltage (V)", 5)],
    },
    "zener_regulator": {
        "name": "Zener Regulator",
        "fields": [("Vin", "Input voltage (V)", 12), ("Vz", "Zener voltage (V)", 5.1), ("Rs", "Series resistance Rs (Ω)", 330), ("RL", "Load resistance RL (Ω)", 1000)],
    },
}


def number(data, key, default=0.0):
    try:
        value = float(data.get(key, default))
    except (TypeError, ValueError):
        value = float(default)
    return value


def calculate(circuit, data):
    if circuit == "rc_lowpass":
        R, C, Vin = number(data, "R", 10000), number(data, "C", 1e-6), number(data, "Vin", 5)
        if R <= 0 or C <= 0:
            raise ValueError("Resistance and capacitance must be greater than zero")
        fc = 1 / (2 * math.pi * R * C)
        return {"Cutoff frequency (Hz)": fc, "Output at DC (V, ideal)": Vin, "Time constant (s)": R * C,
                "Beginner": "Low-frequency signals pass through, while higher-frequency signals are increasingly attenuated.",
                "Advanced": "The first-order real pole is at ωc = 1/(RC). The ideal unloaded magnitude response is |H(jω)| = 1/√(1+(ωRC)^2)."}

    if circuit == "voltage_divider":
        Vin, R1, R2 = number(data, "Vin", 12), number(data, "R1", 10000), number(data, "R2", 10000)
        if R1 + R2 <= 0:
            raise ValueError("The sum of R1 and R2 must be greater than zero")
        Vout = Vin * R2 / (R1 + R2)
        return {"Output voltage (V)": Vout,
                "Beginner": "R1 and R2 share the supply voltage in proportion to their resistances.",
                "Advanced": "For no load, Vout = Vin·R2/(R1+R2). A connected load appears in parallel with R2 and changes the result."}

    if circuit == "bjt_amplifier":
        Rc, re = number(data, "Rc", 2200), number(data, "re", 25)
        if re <= 0:
            raise ValueError("Emitter resistance must be greater than zero")
        gain = -Rc / re
        return {"Approximate voltage gain (V/V)": gain, "Gain magnitude": abs(gain),
                "Beginner": "The circuit has an inverted output: an increase at the input generally makes the output decrease.",
                "Advanced": "This simplified common-emitter gain is Av ≈ -Rc/re. Real gain depends on biasing, transistor parameters, coupling, and loading."}

    if circuit == "inverting_opamp":
        Rin, Rf, Vin = number(data, "Rin", 10000), number(data, "Rf", 47000), number(data, "Vin", 0.2)
        if Rin <= 0:
            raise ValueError("Rin must be greater than zero")
        gain = -Rf / Rin
        return {"Gain (V/V)": gain, "Output voltage (V)": gain * Vin,
                "Beginner": "The output is opposite in polarity and amplified by the ratio of feedback to input resistance.",
                "Advanced": "For an ideal op-amp operated within linear range, Av = -Rf/Rin and Vout = AvVin."}

    if circuit == "half_wave_rectifier":
        Vrms, Vd = number(data, "Vrms", 12), number(data, "Vd", 0.7)
        Vpeak_ac = Vrms * math.sqrt(2)
        Vpeak_out = max(0, Vpeak_ac - Vd)
        avg_out = max(0, Vpeak_ac / math.pi - Vd / math.pi)
        return {"AC peak voltage (V)": Vpeak_ac, "Output peak voltage (V)": Vpeak_out, "Average output voltage (V, ideal half-wave conduction)": avg_out,
                "Beginner": "The diode conducts only on one polarity and removes the voltage drop across the diode.",
                "Advanced": "Using a constant diode-drop model, Vpk,out = √2Vrms − Vd. The average is approximated as Vpk,out/π only when diode conduction is idealized."}

    if circuit == "led_resistor":
        Vs, Vf, I = number(data, "Vs", 5), number(data, "Vf", 2), number(data, "I", 0.01)
        if I <= 0:
            raise ValueError("LED current must be greater than zero")
        R = (Vs - Vf) / I
        return {"Series resistance (Ω)": R, "LED current (A)": I, "Resistor power (W)": I * I * R,
                "Beginner": "Choose a resistor that drops the remaining supply voltage at the desired LED current.",
                "Advanced": "R = (Vs−Vf)/I, subject to LED-current-tolerance and resistor-power requirements. This ignores dynamic LED resistance and supply tolerance."}

    if circuit == "rc_highpass":
        R, C, Vin = number(data, "R", 10000), number(data, "C", 1e-6), number(data, "Vin", 5)
        if R <= 0 or C <= 0:
            raise ValueError("Resistance and capacitance must be greater than zero")
        fc = 1 / (2 * math.pi * R * C)
        return {"Cutoff frequency (Hz)": fc, "Time constant (s)": R * C, "Output at DC (V, ideal)": 0,
                "Beginner": "High-frequency signals pass through, while low-frequency signals are increasingly attenuated.",
                "Advanced": "The first-order real zero/pole pair gives ωc = 1/(RC). Ideal magnitude is |H(jω)| = ωRC/√(1+(ωRC)^2)."}

    if circuit == "zener_regulator":
        Vin, Vz, Rs, RL = number(data, "Vin", 12), number(data, "Vz", 5.1), number(data, "Rs", 330), number(data, "RL", 1000)
        if Rs <= 0 or RL <= 0:
            raise ValueError("Series and load resistance must be greater than zero")
        source_current = (Vin - Vz) / Rs
        load_current = Vz / RL
        zener_current = source_current - load_current
        if Vin <= Vz or zener_current < 0:
            Vout = Vin * RL / (Rs + RL)
            state = "Not regulating"
        else:
            Vout = Vz
            state = "Regulating under this ideal approximation"
        return {"Estimated load voltage (V)": Vout, "Source current (A)": source_current, "Load current (A)": load_current,
                "Estimated Zener current (A)": max(0, zener_current), "Regulation state": state,
                "Beginner": "The resistor drops the excess voltage; the Zener and load share the supply current when regulation is established.",
                "Advanced": "IZ = (Vin−Vz)/Rs − Vz/RL under a regulated ideal-Zener approximation. Verify minimum and maximum load/current limits, diode knee behavior, and power."}

    raise ValueError("Unknown circuit")


@app.route("/")
def index():
    return render_template("index.html", circuits=CIRCUITS)


@app.route("/api/circuits")
def api_circuits():
    return jsonify({key: {"name": value["name"]} for key, value in CIRCUITS.items()})


@app.route("/api/calculate", methods=["POST"])
def api_calculate():
    data = request.get_json(silent=True) or {}
    circuit = data.pop("circuit", "")
    try:
        return jsonify({"ok": True, "circuit": CIRCUITS[circuit]["name"], "results": calculate(circuit, data)})
    except (KeyError, ValueError) as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.route("/api/verify", methods=["POST"])
def api_verify():
    data = request.get_json(silent=True) or {}
    for key in ("circuit", "quantity", "calculated", "simulation"):
        if key not in data:
            return jsonify({"ok": False, "error": f"Missing field: {key}"}), 400
    try:
        calculated = float(data["calculated"])
        simulation = float(data["simulation"])
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Calculated and simulation values must be numbers"}), 400
    error = abs(calculated - simulation) / abs(simulation) * 100 if simulation != 0 else (0 if calculated == 0 else None)
    record = {"Circuit": data["circuit"], "Quantity": data["quantity"], "Hand calculation": calculated,
              "AI result": data.get("aiResult", ""), "Simulation result": simulation,
              "Percentage error": "" if error is None else round(error, 6),
              "Status": data.get("status", "Pending"), "Notes": data.get("notes", "")}
    verification_records.append(record)
    return jsonify({"ok": True, "record": record})


@app.route("/api/verify.csv")
def download_csv():
    output = io.StringIO()
    if verification_records:
        writer = csv.DictWriter(output, fieldnames=verification_records[0].keys())
        writer.writeheader()
        writer.writerows(verification_records)
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=verification_error_log.csv"})


if __name__ == "__main__":
    app.run(debug=True)
