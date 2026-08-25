/**
 * dashboard.js
 * Fetches real-time incident statistics and logs from /api/stats and /api/incidents.
 */

async function fetchDashboardData() {
    try {
        // 1. Fetch Stats
        const statsRes = await fetch("/api/stats");
        const stats = await statsRes.json();

        document.getElementById("statTotal").textContent = stats.total_requests || 0;
        document.getElementById("statBlocked").textContent = stats.blocked_requests || 0;
        document.getElementById("statHighCritical").textContent = stats.high_critical_threats || 0;
        document.getElementById("statLayer2").textContent = stats.layer2_actions || 0;

        // 2. Fetch Incident Logs
        const incidentsRes = await fetch("/api/incidents");
        const incidents = await incidentsRes.json();

        const tbody = document.getElementById("incidentsTableBody");
        if (!incidents || incidents.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: #94a3b8; padding: 24px;">No security incidents recorded yet. Try sending prompts from the AI Assistant.</td></tr>`;
            return;
        }

        tbody.innerHTML = incidents.map(inc => {
            const isBlock = inc.final_decision === "BLOCK";
            const isMask = inc.final_decision === "MASK";
            const decisionTag = isBlock ? "tag block" : (isMask ? "tag mask" : "tag allow");
            const riskColor = inc.risk_score >= 80 ? "#ef4444" : (inc.risk_score >= 40 ? "#f59e0b" : "#10b981");
            const timeFormatted = new Date(inc.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

            return `
                <tr>
                    <td><code>${inc.request_id}</code></td>
                    <td>${timeFormatted}</td>
                    <td title="${escapeHTML(inc.prompt_snippet)}">${escapeHTML(inc.prompt_snippet.substring(0, 45))}...</td>
                    <td style="font-weight: 800; color: ${riskColor};">${inc.risk_score}%</td>
                    <td><span style="font-weight: 600;">${inc.attack_type}</span></td>
                    <td><span class="${inc.layer1_decision === 'BLOCK' ? 'tag block' : 'tag allow'}">${inc.layer1_decision}</span></td>
                    <td><span class="${inc.layer2_decision === 'BLOCK' ? 'tag block' : (inc.layer2_decision === 'MASK' ? 'tag mask' : 'tag allow')}">${inc.layer2_decision}</span></td>
                    <td><span class="${decisionTag}">${inc.final_decision}</span></td>
                    <td><span style="font-size: 11px; color: #94a3b8;">${inc.alert_status}</span></td>
                </tr>
            `;
        }).join("");

    } catch (err) {
        console.error("Failed to load dashboard data:", err);
    }
}

function escapeHTML(str) {
    if (!str) return "";
    return str.replace(/[&<>'"]/g, 
        tag => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[tag] || tag)
    );
}

document.addEventListener("DOMContentLoaded", () => {
    fetchDashboardData();
    // Auto-refresh every 5 seconds
    setInterval(fetchDashboardData, 5000);
});
