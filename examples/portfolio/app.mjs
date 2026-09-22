import { colours, flatten } from "./live.mjs";
const $ = (s) => document.querySelector(s),
    esc = (s) =>
        String(s ?? "").replace(
            /[&<>"']/g,
            (c) =>
                ({
                    "&": "&amp;",
                    "<": "&lt;",
                    ">": "&gt;",
                    '"': "&quot;",
                    "'": "&#39;",
                })[c],
        ),
    stamp = (s) =>
        new Date(s).toLocaleString("en-GB", {
            timeZone: "Europe/London",
            day: "numeric",
            month: "short",
            hour: "2-digit",
            minute: "2-digit",
        }),
    clock = (s) =>
        new Date(s).toLocaleTimeString("en-GB", {
            timeZone: "Europe/London",
            hour: "2-digit",
            minute: "2-digit",
        });
const light = ["circle", "jubilee", "hammersmith-city", "waterloo-city"];
let live,
    archive,
    statuses = [],
    rows = [],
    series = [],
    selected = "central",
    view = "history",
    enabled = new Set(Object.keys(colours));
async function get(url) {
    const r = await fetch(url, {
        cache: "no-store",
        signal: AbortSignal.timeout(15000),
    });
    if (!r.ok) throw Error(r.status);
    return r.json();
}
function statusClass(s) {
    return s === 10 ? "good" : s >= 7 ? "minor" : s >= 5 ? "delay" : "bad";
}
function render() {
    const historical = $("#dataset").value === "archive";
    if (historical) {
        const latest = archive.snapshots.at(-1).snapshot_utc;
        rows = archive.snapshots
            .filter((r) => r.snapshot_utc === latest)
            .map((r) => ({
                id: r.line_id,
                name: r.line_name,
                elo: r.elo,
                on_time: r.on_time_arrivals,
                late: r.late_arrivals,
                cancelled: r.cancelled_trains,
            }));
        const times = [
            ...new Set(archive.snapshots.map((r) => r.snapshot_utc)),
        ];
        series = times.map((at) => ({
            at,
            ratings: Object.fromEntries(
                archive.snapshots
                    .filter((r) => r.snapshot_utc === at)
                    .map((r) => [r.line_id, r.elo]),
            ),
        }));
        $("#updated").textContent = "archive / " + stamp(latest) + " 2026";
        $("#notice").textContent =
            "Original 28 March 2026 hackathon records. These are historical ratings and inferred outcome counts, not current service. The original scoring model is preserved in this archive.";
    } else {
        rows = Object.values(live.lines);
        series = [
            {
                at: live.started,
                ratings: Object.fromEntries(rows.map((r) => [r.id, 1500])),
            },
            ...live.history,
        ];
        $("#updated").textContent =
            "train observations / " + stamp(live.updated);
        $("#notice").textContent =
            "* Sampled arrival estimates, not official totals. Late means a prediction slipped by over 60 seconds. Missing predictions are not counted as cancellations. Collection began " +
            stamp(live.started) +
            "." +
            (Date.now() - Date.parse(live.updated) > 1800000
                ? " Collection is over 30 minutes old."
                : "");
    }
    rows.sort((a, b) => b.elo - a.elo || a.name.localeCompare(b.name));
    $("#lines").innerHTML = rows
        .map((r, i) => {
            const st = statuses.find((s) => s.id === r.id);
            return `<button class="line" data-id="${r.id}" aria-pressed="${selected === r.id}" aria-label="${esc(r.name)}, Elo ${r.elo.toFixed(1)}"><span class="rank p${i + 1}"><b>${i + 1}</b></span><span class="line-name"><span class="badge" style="--line:${colours[r.id]};--fg:${light.includes(r.id) ? "#111" : "#fff"}">${esc(r.name)}</span><i class="status ${historical || !st ? "" : statusClass(st.severity)}" title="${historical ? "Historical service status unavailable" : esc(st?.status || "status unavailable")}"></i></span><span class="elo">${Math.round(r.elo)}</span><span>${r.on_time.toLocaleString()}</span><span>${r.late.toLocaleString()}</span><span>${r.cancelled.toLocaleString()}</span></button>`;
        })
        .join("");
    $("#lines").onclick = (e) => {
        const b = e.target.closest("[data-id]");
        if (b) {
            selected = b.dataset.id;
            $("#candle-line").value = selected;
            show("candles");
        }
    };
    $("#candle-line").innerHTML = rows
        .map(
            (r) =>
                `<option value="${r.id}" ${r.id === selected ? "selected" : ""}>${esc(r.name)}</option>`,
        )
        .join("");
    $("#line-toggles").innerHTML = rows
        .map(
            (r) =>
                `<label style="--line:${colours[r.id]}"><input type="checkbox" value="${r.id}" ${enabled.has(r.id) ? "checked" : ""}>${esc(r.name)}</label>`,
        )
        .join("");
    $("#line-toggles").onchange = (e) => {
        e.target.checked
            ? enabled.add(e.target.value)
            : enabled.delete(e.target.value);
        charts();
    };
    charts();
    events();
    window.__tfl = {
        ready: true,
        rows,
        live,
        series,
        dataset: historical ? "archive" : "live",
    };
}
function frame(body, min, max, times) {
    return `<svg viewBox="0 0 1100 380" role="img" aria-label="Recorded train-event Elo"><rect width="1100" height="380" fill="#0c1117"/>${Array.from(
        { length: 5 },
        (_, i) => {
            const y = 25 + i * 72,
                v = max - ((max - min) * i) / 4;
            return `<line x1="55" x2="1070" y1="${y}" y2="${y}" stroke="#262f38"/><text x="4" y="${y + 4}" fill="#9cabb8" font-size="11">${Math.round(v)}</text>`;
        },
    ).join(
        "",
    )}${body}<text x="55" y="350" fill="#9cabb8" font-size="12">${clock(times[0])}</text><text x="1070" y="350" text-anchor="end" fill="#9cabb8" font-size="12">${clock(times.at(-1))}</text></svg>`;
}
function charts() {
    if (series.length < 2) {
        $("#history-chart").innerHTML = $("#candle-chart").innerHTML =
            '<p class="note">The next collected observation will start the time series. The original hackathon archive already contains the recovered history.</p>';
        return;
    }
    const times = series.map((s) => s.at),
        first = Date.parse(times[0]),
        span = Math.max(1, Date.parse(times.at(-1)) - first),
        all = series.flatMap((s) =>
            Object.entries(s.ratings)
                .filter(([id]) => enabled.has(id))
                .map(([, v]) => v),
        ),
        min = all.length
            ? Math.floor((Math.min(...all) - 40) / 100) * 100
            : 100,
        max = all.length
            ? Math.ceil((Math.max(...all) + 40) / 100) * 100
            : 3500,
        x = (at) => 55 + ((Date.parse(at) - first) / span) * 1015,
        y = (v) => 313 - ((v - min) / (max - min)) * 288;
    $("#history-chart").innerHTML = frame(
        rows
            .filter((r) => enabled.has(r.id))
            .map(
                (r) =>
                    `<polyline points="${series
                        .filter((s) => s.ratings[r.id] !== undefined)
                        .map((s) => `${x(s.at)},${y(s.ratings[r.id])}`)
                        .join(
                            " ",
                        )}" fill="none" stroke="${colours[r.id] === "#303237" ? "#ddd" : colours[r.id]}" stroke-width="2"><title>${esc(r.name)}</title></polyline>`,
            )
            .join(""),
        min,
        max,
        times,
    );
    const id = $("#candle-line").value || selected,
        buckets = new Map();
    for (const s of series) {
        const v = s.ratings[id];
        if (v === undefined) continue;
        const key = Math.floor(Date.parse(s.at) / 300000);
        if (!buckets.has(key)) buckets.set(key, []);
        buckets.get(key).push(v);
    }
    const entries = [...buckets.entries()],
        vals = entries.flatMap(([, v]) => v),
        lo = Math.floor((Math.min(...vals) - 30) / 50) * 50,
        hi = Math.ceil((Math.max(...vals) + 30) / 50) * 50,
        cy = (v) => 313 - ((v - lo) / (hi - lo)) * 288,
        width = Math.min(70, 800 / entries.length);
    $("#candle-chart").innerHTML = frame(
        entries
            .map(([k, v], i) => {
                const xx = 75 + ((i + 0.5) / entries.length) * 970,
                    o = v[0],
                    cl = v.at(-1),
                    top = Math.max(o, cl),
                    bottom = Math.min(o, cl),
                    col = cl >= o ? "#28c077" : "#ec5159";
                return `<g><title>${clock(k * 300000)} / open ${o.toFixed(1)} high ${Math.max(...v).toFixed(1)} low ${Math.min(...v).toFixed(1)} close ${cl.toFixed(1)}</title><line x1="${xx}" x2="${xx}" y1="${cy(Math.max(...v))}" y2="${cy(Math.min(...v))}" stroke="#a4aeb7"/><rect x="${xx - width / 2}" y="${cy(top)}" width="${width}" height="${Math.max(2, cy(bottom) - cy(top))}" fill="${col}"/></g>`;
            })
            .join(""),
        lo,
        hi,
        times,
    );
}
function events() {
    const historical = $("#dataset").value === "archive";
    $("#event-list").innerHTML = historical
        ? '<p class="note">The recovered archive contains aggregate ratings and counts. Individual raw events remain in the original SQLite database linked under Why.</p>'
        : live.events
              .slice(-100)
              .reverse()
              .map(
                  (e) =>
                      `<div class="event"><span>${clock(e.at)}</span><span>${esc(e.line_id)}</span><span>${esc(e.station)}</span><span>${esc(e.outcome)}${e.delay_seconds ? " +" + e.delay_seconds + "s" : ""}</span></div>`,
              )
              .join("") ||
          '<p class="note">Waiting for repeated near-stop predictions. No events have been invented.</p>';
}
function show(next) {
    view = next;
    for (const el of document.querySelectorAll(".view"))
        el.hidden = !(
            el.id === next ||
            (next === "history" && el.id === "leaderboard")
        );
    for (const b of document.querySelectorAll("nav button"))
        b.classList.toggle("active", b.dataset.view === next);
    if (next === "candles") charts();
}
for (const b of document.querySelectorAll("nav button"))
    b.onclick = () => show(b.dataset.view);
$("#dataset").onchange = render;
$("#candle-line").onchange = charts;
async function refresh() {
    const b = $("#refresh");
    b.disabled = true;
    try {
        const results = await Promise.allSettled([
            get("data/events.json"),
            get("data/archive.json"),
            get("https://api.tfl.gov.uk/Line/Mode/tube/Status"),
        ]);
        if (results[0].status === "fulfilled") live = results[0].value;
        if (results[1].status === "fulfilled") archive = results[1].value;
        if (results[2].status === "fulfilled") {
            statuses = flatten(results[2].value);
            $("#connection").textContent = "live service connected";
        } else $("#connection").textContent = "service feed unavailable";
        if (!live || !archive) throw Error("Saved train data unavailable");
        render();
    } catch (e) {
        $("#notice").textContent =
            "Train observations could not load. Refresh to retry.";
        console.error(e);
    } finally {
        b.disabled = false;
    }
}
$("#refresh").onclick = refresh;
$("#download").onclick = () => {
    const text = [
            ["line", "elo", "on_time", "late", "cancelled"],
            ...rows.map((r) => [r.name, r.elo, r.on_time, r.late, r.cancelled]),
        ]
            .map((r) =>
                r
                    .map((v) => '"' + String(v).replaceAll('"', '""') + '"')
                    .join(","),
            )
            .join("\n"),
        url = URL.createObjectURL(new Blob([text], { type: "text/csv" })),
        a = document.createElement("a");
    a.href = url;
    a.download = "train-event-elo.csv";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
};
$("#history").after($("#leaderboard"));
show("history");
await refresh();
setInterval(() => {
    if (!document.hidden) refresh();
}, 60000);
