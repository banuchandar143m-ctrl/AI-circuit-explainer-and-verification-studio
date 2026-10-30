const circuitConfig = {
  rc_lowpass: [['R','Resistance (Ω)',10000],['C','Capacitance (F)',0.000001],['Vin','Input voltage (V)',5]],
  voltage_divider: [['Vin','Input voltage (V)',12],['R1','R1 resistance (Ω)',10000],['R2','R2 resistance (Ω)',10000]],
  bjt_amplifier: [['Rc','Collector resistance Rc (Ω)',2200],['re','Emitter resistance re (Ω)',25]],
  inverting_opamp: [['Rin','Input resistance Rin (Ω)',10000],['Rf','Feedback resistance Rf (Ω)',47000],['Vin','Input voltage (V)',0.2]],
  half_wave_rectifier: [['Vrms','AC RMS voltage (V)',12],['Vd','Diode forward drop (V)',0.7]],
  led_resistor: [['Vs','Supply voltage (V)',5],['Vf','LED forward voltage (V)',2],['I','LED current (A)',0.01]],
  rc_highpass: [['R','Resistance (Ω)',10000],['C','Capacitance (F)',0.000001],['Vin','Input voltage (V)',5]],
  zener_regulator: [['Vin','Input voltage (V)',12],['Vz','Zener voltage (V)',5.1],['Rs','Series resistance Rs (Ω)',330],['RL','Load resistance RL (Ω)',1000]]
};

const circuitSelect = document.getElementById('circuit');
const fields = document.getElementById('fields');
const results = document.getElementById('results');
let latestResults = {};

function renderFields() {
  fields.innerHTML = circuitConfig[circuitSelect.value].map(([key, label, value]) =>
    `<label>${label}<input class="value-input" name="${key}" type="number" step="any" value="${value}"></label>`
  ).join('');
  results.className = 'empty';
  results.textContent = 'Select a circuit and calculate its values.';
}

async function calculate() {
  const payload = { circuit: circuitSelect.value };
  document.querySelectorAll('.value-input').forEach(input => payload[input.name] = input.value);
  try {
    const response = await fetch('/api/calculate', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    const data = await response.json();
    if (!data.ok) throw new Error(data.error);
    latestResults = data.results;
    renderResults(data.results);
  } catch (error) {
    results.className = 'error';
    results.textContent = error.message;
  }
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;','"':'&quot;'}[char]));
}

function formatValue(value) {
  if (typeof value !== 'number') return escapeHtml(value);
  if (value !== 0 && (Math.abs(value) >= 100000 || Math.abs(value) < 0.001)) return value.toExponential(5);
  return Number(value.toPrecision(6)).toString();
}

function renderResults(values) {
  const entries = Object.entries(values).filter(([key]) => !['Beginner','Advanced'].includes(key));
  const quantity = document.getElementById('quantity');
  quantity.innerHTML = '<option value="">Select from calculation</option>' + entries.map(([key]) => `<option value="${escapeHtml(key)}">${escapeHtml(key)}</option>`).join('');
  results.className = '';
  results.innerHTML = `<dl>${entries.map(([key,value]) => `<dt>${escapeHtml(key)}</dt><dd>${formatValue(value)}</dd>`).join('')}</dl>
    <div class="explanation"><h3>Beginner explanation</h3><p>${escapeHtml(values.Beginner)}</p><h3>Advanced explanation</h3><p>${escapeHtml(values.Advanced)}</p></div>`;
}

async function saveVerification() {
  const quantity = document.getElementById('quantity').value;
  const calculated = document.getElementById('calculated').value;
  const simulation = document.getElementById('simulation').value;
  const message = document.getElementById('verification-message');
  if (!quantity || calculated === '' || simulation === '') {
    message.textContent = 'Select a quantity and enter calculated and simulation values.';
    return;
  }
  const circuitName = circuitSelect.options[circuitSelect.selectedIndex].text;
  const payload = {circuit:circuitName, quantity, calculated, simulation,
    aiResult:document.getElementById('ai-result').value, status:document.getElementById('status').value,
    notes:document.getElementById('notes').value};
  const response = await fetch('/api/verify', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
  const data = await response.json();
  message.textContent = data.ok ? 'Verification record saved in this server session.' : data.error;
}

circuitSelect.addEventListener('change', renderFields);
document.getElementById('calculate').addEventListener('click', calculate);
document.getElementById('save').addEventListener('click', saveVerification);
document.getElementById('quantity').addEventListener('change', event => {
  const value = latestResults[event.target.value];
  if (typeof value === 'number') document.getElementById('calculated').value = value;
});
renderFields();
