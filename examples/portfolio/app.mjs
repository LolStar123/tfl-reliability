import { colours, eventSeries, flatten } from "./live.mjs";
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
$("#download").disabled = true;
const light = ["circle", "jubilee", "hammersmith-city", "waterloo-city"];
const observationFeed =
    "https://raw.githubusercontent.com/LolStar123/tfl-reliability/observations/feed.json";
let timeframeHours = 24;
let observationSource = "durable feed";
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
function syncSelection() {
    for (const button of document.querySelectorAll('#lines .line'))
        button.setAttribute('aria-pressed', String(enabled.size === 1 && enabled.has(button.dataset.id)));
    for (const input of document.querySelectorAll('#line-toggles input'))
        input.checked = enabled.has(input.value);
    $('#all-lines').hidden = enabled.size === Object.keys(colours).length;
}
function render() {
    const historical = $("#dataset").value === "archive";
    if (historical ? !archive : !live) return;
    $("#download").disabled = false;
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
        $("#notice").textContent = "hackathon archive · 28 march 2026";
    } else {
        rows = Object.values(live.lines);
        series = eventSeries(live);
        $("#updated").textContent =
            (observationSource === "bundled snapshot" ? "bundled snapshot / " : "train observations / ") + stamp(live.updated);
        $("#notice").textContent = "sampled predictions · ratings bounded from 100 to 3,500";
    }
    rows.sort((a, b) => b.elo - a.elo || a.name.localeCompare(b.name));
    $("#lines").innerHTML = rows
        .map((r, i) => {
            const st = statuses.find((s) => s.id === r.id);
            return `<button class="line" data-id="${r.id}" aria-pressed="${selected === r.id}" aria-label="${esc(r.name)}, Elo ${r.elo.toFixed(1)}, ${historical ? "archive" : esc(st?.status || "status unavailable")}"><span class="rank p${i + 1}"><b>${i + 1}</b></span><span class="line-name"><span class="badge" style="--line:${colours[r.id]};--fg:${light.includes(r.id) ? "#111" : "#fff"}">${esc(r.name)}<small>${historical ? "Archive" : esc(st?.status || "Status unavailable")}</small></span><i class="status ${historical || !st ? "" : statusClass(st.severity)}" title="${historical ? "Historical service status unavailable" : esc(st?.status || "status unavailable")}"></i></span><span class="elo">${Math.round(r.elo)}</span><span>${r.on_time.toLocaleString()}</span><span>${r.late.toLocaleString()}</span><span>${r.cancelled.toLocaleString()}</span></button>`;
        })
        .join("");
    $("#lines").onclick = (e) => {
        const b = e.target.closest("[data-id]");
        if (b) {
            selected = b.dataset.id;
            enabled = enabled.size === 1 && enabled.has(selected)
                ? new Set(Object.keys(colours))
                : new Set([selected]);
            syncSelection();
            charts();
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
        if (!e.target.checked && enabled.size === 1) {
            e.target.checked = true;
            return;
        }
        e.target.checked
            ? enabled.add(e.target.value)
            : enabled.delete(e.target.value);
        syncSelection();
        charts();
    };
    syncSelection();
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
    const {width,height,left,right,bottom,range} = chartDimensions();
    return `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Recorded train-event Elo"><rect width="${width}" height="${height}" fill="#0c1117"/>${Array.from(
        { length: 5 },
        (_, i) => {
            const y = 25 + i * range / 4,
                v = max - ((max - min) * i) / 4;
            return `<line x1="${left}" x2="${right}" y1="${y}" y2="${y}" stroke="#262f38"/><text x="4" y="${y + 4}" fill="#9cabb8" font-size="11">${Math.round(v)}</text>`;
        },
    ).join(
        "",
    )}${body}<text x="${left}" y="${height-30}" fill="#9cabb8" font-size="12">${Date.parse(times.at(-1))-Date.parse(times[0])>86400000?stamp(times[0]):clock(times[0])}</text><text x="${right}" y="${height-30}" text-anchor="end" fill="#9cabb8" font-size="12">${Date.parse(times.at(-1))-Date.parse(times[0])>86400000?stamp(times.at(-1)):clock(times.at(-1))}</text></svg>`;
}
function chartDimensions() {
    const mobile = innerWidth <= 650;
    const width = Math.max(290, $('#history-chart').clientWidth);
    const height = mobile ? 300 : 400;
    return {width,height,left:mobile?42:55,right:width-(mobile?12:30),bottom:height-67,range:height-92};
}
function charts() {
    const dimensions = chartDimensions();
    $('#history h2').textContent = enabled.size === 11 ? 'All eleven lines'
        : enabled.size === 1 ? rows.find(row => enabled.has(row.id))?.name || 'line history'
        : `${enabled.size} lines`;
    const historical = $("#dataset").value === "archive",
        end = Math.max(...series.map(s => Date.parse(s.at)));
    const cutoff = timeframeHours ? end - timeframeHours * 3600000 : -Infinity;
    const visibleSeries = series.filter(s => Date.parse(s.at) >= cutoff);
    for (const b of document.querySelectorAll('[data-hours]')) b.setAttribute('aria-pressed', String(Number(b.dataset.hours) === timeframeHours));
    const trainObservations = visibleSeries.reduce(
        (total, point) => total + (point.eventCount || 0),
        0,
    );
    for (const label of document.querySelectorAll(".range-summary"))
        label.textContent = visibleSeries.length
            ? stamp(visibleSeries[0].at) +
              " to " +
              stamp(visibleSeries.at(-1).at) +
              " / " +
              (historical
                  ? visibleSeries.length + " observations"
                  : trainObservations.toLocaleString("en-GB") +
                    " train observations")
            : "No observations in this window.";
    window.__tflRange = {
        hours: timeframeHours,
        count: visibleSeries.length,
        events: trainObservations,
        start: visibleSeries[0]?.at,
        end: visibleSeries.at(-1)?.at,
    };
    if (visibleSeries.length < 2) {
        $("#history-chart").innerHTML = $("#candle-chart").innerHTML =
            '<p class="note">Not enough observations in this window yet. Choose a wider timeframe.</p>';
        return;
    }
    const times = visibleSeries.map((s) => s.at),
        first = Date.parse(times[0]),
        span = Math.max(1, Date.parse(times.at(-1)) - first),
        all = visibleSeries.flatMap((s) =>
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
        x = (at) => dimensions.left + ((Date.parse(at) - first) / span) * (dimensions.right-dimensions.left),
        y = (v) => dimensions.bottom - ((v - min) / (max - min)) * dimensions.range;
    $("#history-chart").innerHTML = frame(
        rows
            .filter((r) => enabled.has(r.id))
            .map((r) => {
                const colour =
                        colours[r.id] === "#303237"
                            ? "#ddd"
                            : colours[r.id],
                    points = visibleSeries.filter(
                        (s) => s.ratings[r.id] !== undefined,
                    ),
                    line = points
                        .map((s) => `${x(s.at)},${y(s.ratings[r.id])}`)
                        .join(" "),
                    blips = points
                        .filter(
                            (s) =>
                                !s.observed || s.observed.includes(r.id),
                        )
                        .map(
                            (s) =>
                                `<circle class="data-blip" cx="${x(s.at)}" cy="${y(s.ratings[r.id])}" r="2.6" fill="${colour}" stroke="#0c1117" stroke-width="1"><title>${esc(r.name)} / ${clock(s.at)} / ${Math.round(s.ratings[r.id])}</title></circle>`,
                        )
                        .join("");
                return `<polyline class="rating-line" points="${line}" fill="none" stroke="${colour}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><title>${esc(r.name)}</title></polyline>${blips}`;
            })
            .join(""),
        min,
        max,
        times,
    );
    const id = $("#candle-line").value || selected,
        buckets = new Map();
    for (const s of visibleSeries) {
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
        cy = (v) => dimensions.bottom - ((v - lo) / (hi - lo)) * dimensions.range,
        width = Math.min(70, (dimensions.right-dimensions.left)*.8 / entries.length);
    $("#candle-chart").innerHTML = frame(
        entries
            .map(([k, v], i) => {
                const xx = dimensions.left + ((i + 0.5) / entries.length) * (dimensions.right-dimensions.left),
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
        ? '<p class="note">The recovered archive contains aggregate ratings and counts. Individual raw events remain in the original SQLite database linked in the repository provenance.</p>'
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
for (const button of document.querySelectorAll('[data-hours]')) button.onclick = () => {timeframeHours = Number(button.dataset.hours); charts();};
$("#dataset").onchange = async () => {
    if ($('#dataset').value === 'archive' && !archive) {
        $('#updated').textContent = 'loading archive...';
        try { archive = await get('data/archive.json'); }
        catch {
            $('#dataset').value = 'live';
            render();
            $('#notice').textContent = 'Archive unavailable. Try again from data tools.';
            return;
        }
    }
    render();
};
$('#all-lines').onclick = () => {
    enabled = new Set(Object.keys(colours));
    syncSelection();
    charts();
};
$("#candle-line").onchange = charts;
async function refresh() {
    const b = $("#refresh");
    b.disabled = true;
    try {
        const liveFeed = get(
            observationFeed +
                "?bucket=" +
                Math.floor(Date.now() / 300000),
        ).then(value => {
            observationSource = "durable feed";
            return value;
        }).catch(() => {
            observationSource = "bundled snapshot";
            return get("data/events.json");
        });
        const serviceFeed = get('https://api.tfl.gov.uk/Line/Mode/tube/Status');
        const serviceResult = serviceFeed.then(value => ({value}), () => ({value:null}));
        live = await liveFeed;
        render();
        const result = await serviceResult;
        if (result.value) {
            try {
                statuses = flatten(result.value);
                $("#connection").textContent = "live service connected";
            } catch {
                statuses = [];
                $('#connection').textContent = 'service feed unavailable';
            }
        } else {
            statuses = [];
            $("#connection").textContent = "Service feed unavailable";
        }
        render();
    } catch (e) {
        $("#notice").textContent =
            "Train observations could not load. Refresh to retry or choose the archive.";
        $("#updated").textContent = live ? "Showing last loaded observations" : "Observation feed unavailable";
        if (!live && !archive) {
            $("#download").disabled = true;
            $("#history-chart").innerHTML = '<p class="note">No observations loaded. Refresh to retry.</p>';
        }
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
// Ranking precedes history in the DOM and on narrow screens.
let resizeFrame;
addEventListener('resize', () => {
    cancelAnimationFrame(resizeFrame);
    resizeFrame = requestAnimationFrame(() => { if (series.length) charts(); });
});
show("history");
await refresh();
setInterval(() => {
    if (!document.hidden) refresh();
}, 300000);
