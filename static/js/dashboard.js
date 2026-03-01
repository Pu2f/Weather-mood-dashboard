const d = window.DASHBOARD_DATA;

const RAIN_THRESHOLD_MIN = 0;
const RAIN_THRESHOLD_MAX = 200;

function clampRainThresholdInput() {
  const input = document.querySelector('input[name="rain_threshold"]');
  if (!input) return;

  const clamp = (value) => {
    const n = Number(value);
    if (Number.isNaN(n)) return null;
    return Math.min(RAIN_THRESHOLD_MAX, Math.max(RAIN_THRESHOLD_MIN, n));
  };

  input.addEventListener("input", () => {
    if (input.value.trim() === "") return;
    const clamped = clamp(input.value);
    if (clamped === null) return;
    input.value = String(clamped);
  });

  const form = input.closest("form");
  if (form) {
    form.addEventListener("submit", () => {
      const clamped = clamp(input.value);
      if (clamped === null) {
        input.value = "1";
        return;
      }
      input.value = String(clamped);
    });
  }
}

clampRainThresholdInput();

function toPairs(xs, ys) {
  const out = [];
  for (let i = 0; i < Math.min(xs.length, ys.length); i++) {
    const x = xs[i];
    const y = ys[i];
    if (x === null || x === undefined) continue;
    if (y === null || y === undefined) continue;
    out.push({ x: Number(x), y: Number(y) });
  }
  return out;
}

function minMax(vals) {
  const nums = vals.filter(v => v !== null && v !== undefined).map(Number);
  if (nums.length === 0) return null;
  return { min: Math.min(...nums), max: Math.max(...nums) };
}

function xLabel(xvar) {
  if (xvar === "temp_max") return "Temp max (°C)";
  if (xvar === "rain_mm") return "Rain (mm)";
  return "Temp mean (°C)";
}

// Line chart (time)
new Chart(document.getElementById("lineChart"), {
  type: "line",
  data: {
    labels: d.labels,
    datasets: [
      {
        label: "Temp mean (°C)",
        data: d.temp_mean,
        borderColor: "#2563eb",
        backgroundColor: "rgba(37,99,235,0.15)",
        yAxisID: "yTemp",
        spanGaps: true,
      },
      {
        label: "Productivity (1–5)",
        data: d.productivity,
        borderColor: "#16a34a",
        backgroundColor: "rgba(22,163,74,0.15)",
        yAxisID: "yProd",
        spanGaps: true,
      },
    ],
  },
  options: {
    responsive: true,
    interaction: { mode: "index", intersect: false },
    scales: {
      yTemp: { type: "linear", position: "left", title: { display: true, text: "°C" } },
      yProd: { type: "linear", position: "right", min: 0, max: 5, grid: { drawOnChartArea: false } },
    },
  },
});

// Scatter + regression line
const xSeries =
  d.xvar === "temp_max" ? d.temp_max : d.xvar === "rain_mm" ? d.rain_mm : d.temp_mean;

const scatterPairs = toPairs(xSeries, d.productivity);

const reg = d.regression; // {a,b,n} or null
let regLine = [];
if (reg && scatterPairs.length >= 2) {
  const mm = minMax(xSeries);
  if (mm) {
    const x1 = mm.min;
    const x2 = mm.max;
    regLine = [
      { x: x1, y: reg.a + reg.b * x1 },
      { x: x2, y: reg.a + reg.b * x2 },
    ];
  }
}

new Chart(document.getElementById("scatterChart"), {
  type: "scatter",
  data: {
    datasets: [
      {
        label: `Productivity vs ${xLabel(d.xvar)}`,
        data: scatterPairs,
        backgroundColor: "rgba(147,51,234,0.55)",
      },
      {
        label: "Regression",
        type: "line",
        data: regLine,
        borderColor: "rgba(239,68,68,0.9)",
        borderWidth: 2,
        pointRadius: 0,
      },
    ],
  },
  options: {
    responsive: true,
    scales: {
      x: { title: { display: true, text: xLabel(d.xvar) } },
      y: { title: { display: true, text: "Productivity (1–5)" }, min: 0, max: 5 },
    },
  },
});

// Bar: rainy vs dry
// We'll compute from raw arrays on the client too (should match backend cards)
function avg(vals) {
  if (vals.length === 0) return null;
  return vals.reduce((a, b) => a + b, 0) / vals.length;
}
const rainy = [];
const dry = [];
for (let i = 0; i < d.labels.length; i++) {
  const r = d.rain_mm[i];
  const p = d.productivity[i];
  if (r === null || r === undefined) continue;
  if (p === null || p === undefined) continue;
  if (Number(r) >= Number(d.rain_threshold)) rainy.push(Number(p));
  else dry.push(Number(p));
}

new Chart(document.getElementById("barChart"), {
  type: "bar",
  data: {
    labels: ["Rainy", "Dry"],
    datasets: [
      {
        label: "Avg Productivity",
        data: [avg(rainy), avg(dry)],
        backgroundColor: ["rgba(59,130,246,0.6)", "rgba(34,197,94,0.6)"],
      },
    ],
  },
  options: {
    responsive: true,
    scales: {
      y: { min: 0, max: 5, title: { display: true, text: "Productivity (1–5)" } },
    },
  },
});