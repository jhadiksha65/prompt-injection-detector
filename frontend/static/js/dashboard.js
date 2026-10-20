/**
 * dashboard.js
 * Real-time Incident Analytics & Security KPI Telemetry Controller
 * Integrates with /api/stats and /api/incidents with full admin authentication support.
 */

let isFetching = false;

function getAdminAuthToken() {
    try {
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has('auth')) {
            const authVal = urlParams.get('auth');
            return authVal.includes(':') ? btoa(authVal) : authVal;
        }
        return sessionStorage.getItem('prompt_security_admin_token') || null;
    } catch (e) {
        return null;
    }
}

function setAdminAuthToken(token) {
    try {
        if (token) {
            sessionStorage.setItem('prompt_security_admin_token', token);
        } else {
            sessionStorage.removeItem('prompt_security_admin_token');
        }
    } catch (e) {}
}

async function fetchDashboardData() {
    if (isFetching) return;
    isFetching = true;

    const btnRefresh = document.getElementById('btnRefreshDashboard');
    if (btnRefresh) btnRefresh.classList.add('loading');

    const authCard = document.getElementById('authBannerCard');
    const token = getAdminAuthToken();
    const headers = {};
    if (token) {
        headers['Authorization'] = 'Basic ' + token;
    }

    try {
        // Collect filter values if present
        const filterSource = document.getElementById('filterSource')?.value || '';
        const filterL1 = document.getElementById('filterL1')?.value || '';
        const filterL2 = document.getElementById('filterL2')?.value || '';
        const filterLimit = document.getElementById('filterLimit')?.value || '50';

        const params = new URLSearchParams();
        if (filterSource) params.append('source', filterSource);
        if (filterL1) params.append('l1_decision', filterL1);
        if (filterL2) params.append('l2_decision', filterL2);
        if (filterLimit) params.append('limit', filterLimit);

        const incidentsUrl = '/api/incidents' + (params.toString() ? ('?' + params.toString()) : '');

        // 1. Fetch Stats & Incidents in parallel
        const [statsRes, incidentsRes] = await Promise.all([
            fetch('/api/stats', { headers }),
            fetch(incidentsUrl, { headers })
        ]);

        // Check if either returned 401 Unauthorized
        if (statsRes.status === 401 || incidentsRes.status === 401) {
            if (authCard) authCard.style.display = 'block';
            document.getElementById('statTotal').textContent = '🔒';
            document.getElementById('statBlocked').textContent = '🔒';
            document.getElementById('statHighCritical').textContent = '🔒';
            document.getElementById('statLayer2').textContent = '🔒';

            const tbody = document.getElementById('incidentsTableBody');
            if (tbody) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="10" style="text-align: center; color: var(--text-muted); padding: 2.5rem 1rem;">
                            <div style="font-size: 1.25rem; margin-bottom: 0.5rem;">🔒</div>
                            <div style="font-weight: 600; color: var(--text-main); margin-bottom: 0.25rem;">Administrator Authentication Required</div>
                            <div style="font-size: 0.8rem; color: var(--text-subtle);">Please enter administrator credentials in the challenge card above to unlock live incident telemetry.</div>
                        </td>
                    </tr>
                `;
            }
            return;
        }

        // Hide auth banner if authorized
        if (authCard) authCard.style.display = 'none';

        if (statsRes.ok) {
            const stats = await statsRes.json();
            document.getElementById('statTotal').textContent = Number(stats.total_requests || 0).toLocaleString();
            document.getElementById('statBlocked').textContent = Number(stats.blocked_requests || 0).toLocaleString();
            document.getElementById('statHighCritical').textContent = Number(stats.high_critical_threats || 0).toLocaleString();
            document.getElementById('statLayer2').textContent = Number(stats.layer2_actions || 0).toLocaleString();
        }

        if (incidentsRes.ok) {
            const incidents = await incidentsRes.json();
            renderIncidentsTable(incidents);
        }

    } catch (err) {
        console.error('Failed to load dashboard data:', err);
    } finally {
        isFetching = false;
        if (btnRefresh) btnRefresh.classList.remove('loading');
    }
}

function renderIncidentsTable(incidents) {
    const tbody = document.getElementById('incidentsTableBody');
    const countBadge = document.getElementById('incidentCountBadge');
    if (!tbody) return;

    if (!Array.isArray(incidents) || incidents.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="10" style="text-align: center; color: var(--text-muted); padding: 2.5rem 1rem;">
                    <div style="font-size: 1.25rem; margin-bottom: 0.5rem;">📋</div>
                    <div style="font-weight: 600; color: var(--text-main); margin-bottom: 0.25rem;">No Incidents Recorded Yet</div>
                    <div style="font-size: 0.8rem; color: var(--text-subtle);">Analyzed prompts submitted via the AI Assistant, External Demo, or Gateway API will appear here in real time.</div>
                </td>
            </tr>
        `;
        if (countBadge) countBadge.textContent = '0 incidents recorded';
        return;
    }

    if (countBadge) {
        countBadge.textContent = `${incidents.length} incident${incidents.length === 1 ? '' : 's'} recorded`;
    }

    tbody.innerHTML = incidents.map(inc => {
        const reqId = String(inc.request_id || 'REQ-');
        let channelBadge = '<span class="source-badge badge-app" title="Application Security Event">System</span>';
        if (reqId.startsWith('GW-')) {
            channelBadge = '<span class="source-badge badge-gw" title="External OpenAI-compatible Gateway API (/api/v1/chat/completions)">Gateway API</span>';
        } else if (reqId.startsWith('EXT-')) {
            channelBadge = '<span class="source-badge badge-ext" title="Interactive Secure AI Playground Demo (/external-demo)">Playground</span>';
        } else if (reqId.startsWith('REQ-')) {
            channelBadge = '<span class="source-badge badge-req" title="Internal Prompt Security Analyzer (/secure-prompt)">Internal Analyzer</span>';
        }

        const isBlock = inc.final_decision === 'BLOCK';
        const isMask = inc.final_decision === 'MASK';
        const finalTagClass = isBlock ? 'tag-badge tag-block' : (isMask ? 'tag-badge tag-mask' : 'tag-badge tag-allow');

        const l1TagClass = inc.layer1_decision === 'BLOCK' ? 'tag-badge tag-block' : 'tag-badge tag-allow';
        const l2Decision = inc.layer2_decision || 'N/A';
        const l2TagClass = l2Decision === 'BLOCK' ? 'tag-badge tag-block' : (l2Decision === 'MASK' ? 'tag-badge tag-mask' : 'tag-badge tag-allow');

        const score = inc.risk_score !== undefined ? parseFloat(inc.risk_score) : 0;
        let riskColor = '#10b981';
        if (score >= 61) riskColor = '#ef4444';
        else if (score >= 38) riskColor = '#f59e0b';

        let timeStr = 'Recent';
        if (inc.timestamp) {
            try {
                timeStr = new Date(inc.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            } catch (e) {
                timeStr = inc.timestamp;
            }
        }

        const snippet = inc.prompt_snippet || inc.prompt || 'No content';
        const displaySnippet = snippet.length > 50 ? (snippet.substring(0, 50) + '…') : snippet;

        const alertStatus = inc.alert_status || 'NONE';
        const alertColor = alertStatus === 'DISPATCHED' ? '#ef4444' : 'var(--text-subtle)';

        return `
            <tr>
                <td><code style="font-family: 'JetBrains Mono', monospace; font-size: 0.76rem; background: var(--bg-surface-subtle); padding: 0.15rem 0.4rem; border-radius: 4px; border: 1px solid var(--border-subtle);">${escapeHTML(reqId)}</code></td>
                <td>${channelBadge}</td>
                <td style="white-space: nowrap; font-size: 0.78rem; color: var(--text-muted);">${escapeHTML(timeStr)}</td>
                <td title="${escapeHTML(snippet)}" style="max-width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHTML(displaySnippet)}</td>
                <td style="font-weight: 800; font-family: 'JetBrains Mono', monospace; color: ${riskColor}; white-space: nowrap;">${Math.round(score)}%</td>
                <td style="font-weight: 600; font-size: 0.78rem;">${escapeHTML(inc.attack_type || 'General')}</td>
                <td><span class="${l1TagClass}">${escapeHTML(inc.layer1_decision || 'ALLOW')}</span></td>
                <td><span class="${l2TagClass}">${escapeHTML(l2Decision)}</span></td>
                <td><span class="${finalTagClass}">${escapeHTML(inc.final_decision || 'ALLOW')}</span></td>
                <td style="font-size: 0.72rem; font-weight: 700; color: ${alertColor}; white-space: nowrap;">${escapeHTML(alertStatus)}</td>
            </tr>
        `;
    }).join('');
}

async function handleDashboardAuth(e) {
    if (e) e.preventDefault();
    const userField = document.getElementById('dashUsername');
    const passField = document.getElementById('dashPassword');
    const errorEl = document.getElementById('dashAuthError');

    const username = userField ? userField.value.trim() : '';
    const password = passField ? passField.value.trim() : '';

    if (!username || !password) return;

    if (errorEl) errorEl.style.display = 'none';

    try {
        const res = await fetch('/api/reauth', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await res.json();
        if (res.ok && data.success) {
            const token = btoa(username + ':' + password);
            setAdminAuthToken(token);
            if (passField) passField.value = '';
            const authCard = document.getElementById('authBannerCard');
            if (authCard) authCard.style.display = 'none';
            fetchDashboardData();
        } else {
            if (errorEl) {
                errorEl.textContent = data.error || 'Authentication failed: Invalid credentials provided.';
                errorEl.style.display = 'block';
            }
        }
    } catch (err) {
        if (errorEl) {
            errorEl.textContent = 'Authentication service temporarily unavailable.';
            errorEl.style.display = 'block';
        }
    }
}

function escapeHTML(str) {
    if (!str) return '';
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

document.addEventListener('DOMContentLoaded', () => {
    fetchDashboardData();
    // Auto-refresh every 10 seconds if page remains open
    setInterval(fetchDashboardData, 10000);
});
