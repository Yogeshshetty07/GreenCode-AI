document.addEventListener('DOMContentLoaded', () => {
    // Navigation Tabs
    const navButtons = document.querySelectorAll('.nav-btn');
    const tabPages = document.querySelectorAll('.tab-page');

    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            navButtons.forEach(b => b.classList.remove('active'));
            tabPages.forEach(p => p.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(targetTab).classList.add('active');

            if (targetTab === 'analytics-tab') {
                renderAnalyticsCharts();
            } else if (targetTab === 'history-tab') {
                loadAuditHistory();
            }
        });
    });

    // Run Audit Event Listener
    const runBtn = document.getElementById('run-audit-btn');
    if (runBtn) {
        runBtn.addEventListener('click', runEcoAudit);
    }

    // Initial Sustainability Stats load
    loadGlobalStats();
});

let currentAuditData = null;
let charts = {};

async function loadSamplePreset(sampleName) {
    try {
        const resp = await fetch(`/api/sample/${sampleName}`);
        const data = await resp.json();
        if (data.code) {
            document.getElementById('code-input').value = data.code;
            document.getElementById('project-name-input').value = `Preset: ${sampleName.replace('_', ' ').toUpperCase()}`;
        }
    } catch (e) {
        console.error("Failed to load sample preset", e);
    }
}

async function runEcoAudit() {
    const code = document.getElementById('code-input').value;
    const projectName = document.getElementById('project-name-input').value || 'Green Code Audit';
    const runBtn = document.getElementById('run-audit-btn');

    if (!code.trim()) {
        alert("Please enter or paste Python code to analyze.");
        return;
    }

    runBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Profiling Energy & CO2e...';
    runBtn.disabled = true;

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code: code,
                project_name: projectName,
                language: 'python'
            })
        });

        const data = await response.json();
        if (response.ok) {
            currentAuditData = data;
            renderScorecard(data);
            renderCodeComparison(data);
            loadGlobalStats();
        } else {
            alert(data.error || "Failed to complete eco-audit.");
        }
    } catch (err) {
        console.error("Audit request error:", err);
        alert("An error occurred while connecting to GreenCode server.");
    } finally {
        runBtn.innerHTML = '<i class="fa-solid fa-bolt"></i> Run Eco-Audit & Refactor';
        runBtn.disabled = false;
    }
}

function renderScorecard(data) {
    const body = document.getElementById('scorecard-body');
    const origDyn = data.original_dynamic;
    const optDyn = data.optimized_dynamic;
    const comp = data.comparison;
    const origStat = data.original_static;
    const optStat = data.optimized_static;

    const energySavedJ = comp.joules_saved;
    const carbonSavedPct = comp.carbon_reduced_pct;

    body.innerHTML = `
        <div class="eco-grade-banner">
            <div>
                <h3>Grade: ${origDyn.eco_grade}</h3>
                <span style="font-size: 0.85rem; color: #cbd5e1;">Target Eco-Grade after AI Refactoring: <strong>A+ Ultra Eco</strong></span>
            </div>
            <span class="badge badge-success">+${optStat.eco_score - origStat.eco_score} Score Gain</span>
        </div>

        <div class="metrics-summary-grid">
            <div class="metric-box">
                <div class="label">Original Energy Consumed</div>
                <div class="val" style="color: #ef4444;">${origDyn.energy_joules} J</div>
                <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 2px;">~ ${origDyn.carbon_gco2e} gCO2e</div>
            </div>
            <div class="metric-box">
                <div class="label">Eco-Optimized Energy</div>
                <div class="val" style="color: #10b981;">${optDyn.energy_joules} J</div>
                <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 2px;">~ ${optDyn.carbon_gco2e} gCO2e</div>
            </div>
            <div class="metric-box">
                <div class="label">Carbon Footprint Reduction</div>
                <div class="val" style="color: #10b981;">${carbonSavedPct}%</div>
                <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 2px;">${energySavedJ} Joules Saved</div>
            </div>
            <div class="metric-box">
                <div class="label">Execution Speedup Factor</div>
                <div class="val" style="color: #3b82f6;">${comp.speedup_factor}x Faster</div>
                <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 2px;">Latency: ${origDyn.execution_time_ms}ms -> ${optDyn.execution_time_ms}ms</div>
            </div>
        </div>

        <div class="issues-list" style="margin-top: 1rem;">
            <h4 style="font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem;">Detected Carbon Code Vulnerabilities (${origStat.issue_count}):</h4>
            ${origStat.issues.length === 0 ? '<p style="font-size: 0.85rem; color: #10b981;">No structural energy issues detected!</p>' : ''}
            ${origStat.issues.map(iss => `
                <div style="background: rgba(239, 68, 68, 0.08); border-left: 3px solid #ef4444; padding: 0.6rem 0.85rem; margin-bottom: 0.5rem; border-radius: 4px; font-size: 0.85rem;">
                    <strong>[Line ${iss.line}] ${iss.type} (${iss.severity})</strong>: ${iss.message}<br>
                    <span style="color: #10b981;">💡 Recommendation: ${iss.recommendation}</span>
                </div>
            `).join('')}
        </div>
    `;
}

function renderCodeComparison(data) {
    const compSection = document.getElementById('comparison-section');
    compSection.classList.remove('hidden');

    document.getElementById('savings-badge').innerText = `${data.comparison.carbon_reduced_pct}% Carbon Saved`;
    document.getElementById('orig-score-pill').innerText = `Eco Score: ${data.original_static.eco_score}/100`;
    document.getElementById('opt-score-pill').innerText = `Eco Score: ${data.optimized_static.eco_score}/100`;

    document.getElementById('orig-code-display').innerText = data.original_code;
    document.getElementById('opt-code-display').innerText = data.optimized_code;

    const transList = document.getElementById('transformations-list');
    transList.innerHTML = data.transformations.map(t => `<li><i class="fa-solid fa-check-circle" style="color: #10b981;"></i> ${t}</li>`).join('');
}

async function loadGlobalStats() {
    try {
        const resp = await fetch('/api/history');
        const data = await resp.json();
        if (data.stats) {
            document.getElementById('total-co2-saved').innerText = `${data.stats.total_gco2e_saved} gCO2e`;
            document.getElementById('total-audits-count').innerText = `${data.stats.total_audits} Audits Completed`;
        }
    } catch (e) {
        console.error("Stats load failed", e);
    }
}

async function loadAuditHistory() {
    try {
        const resp = await fetch('/api/history');
        const data = await resp.json();
        const tbody = document.getElementById('history-table-body');

        if (!data.audits || data.audits.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center">No audit history recorded yet.</td></tr>';
            return;
        }

        tbody.innerHTML = data.audits.map(a => `
            <tr id="audit-row-${a.id}">
                <td>#${a.id}</td>
                <td><strong>${a.project_name}</strong></td>
                <td><span class="badge badge-warning">${a.original_eco_score}</span></td>
                <td><span class="badge badge-success">${a.optimized_eco_score}</span></td>
                <td>${roundVal(a.original_joules - a.optimized_joules, 4)} J</td>
                <td><span class="badge badge-success">${a.carbon_saved_pct}%</span></td>
                <td>${a.speedup_factor}x</td>
                <td>${a.created_at}</td>
                <td>
                    <div style="display: flex; gap: 0.4rem;">
                        <a href="/api/export/${a.id}" target="_blank" class="btn btn-outline" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" title="Download Report">
                            <i class="fa-solid fa-download"></i> MD
                        </a>
                        <button onclick="deleteAudit(${a.id})" class="btn btn-outline" style="padding: 0.25rem 0.5rem; font-size: 0.75rem; color: #ef4444; border-color: rgba(239, 68, 68, 0.4);" title="Delete Audit">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    } catch (e) {
        console.error("Audit history load error:", e);
    }
}

async function deleteAudit(auditId) {
    if (!confirm(`Are you sure you want to delete audit #${auditId}?`)) return;

    try {
        const response = await fetch(`/api/audit/${auditId}`, { method: 'DELETE' });
        const data = await response.json();
        if (response.ok && data.success) {
            loadAuditHistory();
            loadGlobalStats();
        } else {
            alert(data.error || "Failed to delete audit.");
        }
    } catch (e) {
        console.error("Failed to delete audit:", e);
        alert("An error occurred while communicating with the server.");
    }
}

async function clearAllHistory() {
    if (!confirm("Are you sure you want to delete ALL recorded audit history? This action cannot be undone.")) return;

    try {
        const response = await fetch('/api/history/clear', { method: 'DELETE' });
        const data = await response.json();
        if (response.ok && data.success) {
            loadAuditHistory();
            loadGlobalStats();
        } else {
            alert(data.error || "Failed to clear history.");
        }
    } catch (e) {
        console.error("Failed to clear history:", e);
        alert("An error occurred while communicating with the server.");
    }
}

function renderAnalyticsCharts() {
    if (!currentAuditData) return;

    const origDyn = currentAuditData.original_dynamic;
    const optDyn = currentAuditData.optimized_dynamic;

    createOrUpdateChart('energyChart', 'bar', ['Original Code', 'Green AI Optimized'], [origDyn.energy_joules, optDyn.energy_joules], 'Joules (J)', ['#ef4444', '#10b981']);
    createOrUpdateChart('carbonChart', 'bar', ['Original Code', 'Green AI Optimized'], [origDyn.carbon_gco2e, optDyn.carbon_gco2e], 'gCO2e', ['#f59e0b', '#10b981']);
    createOrUpdateChart('latencyChart', 'bar', ['Original Code', 'Green AI Optimized'], [origDyn.execution_time_ms, optDyn.execution_time_ms], 'Latency (ms)', ['#ef4444', '#3b82f6']);
    createOrUpdateChart('memoryChart', 'bar', ['Original Code', 'Green AI Optimized'], [origDyn.peak_memory_mb, optDyn.peak_memory_mb], 'RAM (MB)', ['#f59e0b', '#10b981']);
}

function createOrUpdateChart(canvasId, type, labels, dataPoints, datasetLabel, colors) {
    const ctx = document.getElementById(canvasId).getContext('2d');

    if (charts[canvasId]) {
        charts[canvasId].destroy();
    }

    charts[canvasId] = new Chart(ctx, {
        type: type,
        data: {
            labels: labels,
            datasets: [{
                label: datasetLabel,
                data: dataPoints,
                backgroundColor: colors,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                }
            }
        }
    });
}

function roundVal(val, decimals) {
    return Math.round(val * Math.pow(10, decimals)) / Math.pow(10, decimals);
}
