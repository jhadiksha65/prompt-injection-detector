document.addEventListener('DOMContentLoaded', () => {
    
    const navLinks = document.querySelectorAll('.nav-link');
    const views = document.querySelectorAll('.view-section');

    // -- Routing Logic --
    function handleRoute() {
        // Fallback to analyzer if no hash
        let hash = window.location.hash.substring(1);
        if (!hash || !['analyzer', 'history', 'howItWorks', 'about'].includes(hash)) {
            hash = 'analyzer';
            history.replaceState(null, null, '#analyzer');
        }

        // Update nav links
        navLinks.forEach(l => {
            l.classList.remove('active');
            if (l.getAttribute('href') === '#' + hash) {
                l.classList.add('active');
            }
        });

        // Update views
        views.forEach(v => {
            v.classList.remove('active');
        });

        const targetView = document.getElementById(hash + 'View');
        if (targetView) {
            targetView.classList.add('active');
        }

        // Handle specific route logic
        if (hash === 'history') {
            loadHistory();
        }
    }

    window.addEventListener('hashchange', handleRoute);
    
    // Initial route handling on load
    handleRoute();

    // -- Expander --
    const expanderBtn = document.getElementById('promptExpanderBtn');
    const expanderContent = document.getElementById('promptExpanderContent');
    if (expanderBtn) {
        expanderBtn.addEventListener('click', () => {
            expanderBtn.classList.toggle('open');
            if (expanderBtn.classList.contains('open')) {
                expanderContent.style.display = 'block';
            } else {
                expanderContent.style.display = 'none';
            }
        });
    }

    // -- Textarea & Char Count --
    const promptInput = document.getElementById('promptInput');
    const charCount = document.getElementById('charCount');
    const MAX_CHARS = 5000;

    if (promptInput) {
        promptInput.addEventListener('input', () => {
            const len = promptInput.value.length;
            charCount.textContent = `${len} / ${MAX_CHARS} characters`;
            if (len > MAX_CHARS) {
                charCount.style.color = 'var(--critical)';
            } else {
                charCount.style.color = 'var(--text-secondary)';
            }
        });
    }

    // -- System Status Checking --
    checkSystemStatus();

    // -- Form Handling --
    const analyzeForm = document.getElementById('analyzeForm');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const retryBtn = document.getElementById('retryBtn');

    if (analyzeForm) {
        analyzeForm.addEventListener('submit', (e) => {
            e.preventDefault();
            analyzePrompt();
        });
    }

    if (retryBtn) {
        retryBtn.addEventListener('click', () => {
            analyzePrompt();
        });
    }

    // -- Functions --
    
    async function checkSystemStatus() {
        const hDot = document.getElementById('headerStatusDot');
        const hText = document.getElementById('headerStatusText');
        const stEngine = document.getElementById('stEngine');
        const stAPI = document.getElementById('stAPI');
        const stModel = document.getElementById('stModel');

        try {
            const res = await fetch('/health');
            if (res.ok) {
                const data = await res.json();
                hDot.className = 'status-dot online';
                hText.textContent = '● Online';
                
                if (stAPI) {
                    stAPI.className = 'status-indicator on';
                    stAPI.nextElementSibling.querySelector('.status-val').textContent = 'Active';
                }

                if (stEngine && data.layer1_rule_engine) {
                    stEngine.className = 'status-indicator on';
                    stEngine.nextElementSibling.querySelector('.status-val').textContent = 'Online';
                }

                if (stModel && data.ml_model_loaded) {
                    stModel.className = 'status-indicator on';
                    stModel.nextElementSibling.querySelector('.status-val').textContent = 'Loaded';
                }
            } else {
                throw new Error('Not OK');
            }
        } catch (err) {
            hDot.className = 'status-dot offline';
            hText.textContent = '● Offline';
            
            [stEngine, stAPI, stModel].forEach(el => {
                if (el) {
                    el.className = 'status-indicator';
                    el.nextElementSibling.querySelector('.status-val').textContent = 'Offline';
                }
            });
        }
    }

    async function analyzePrompt() {
        const prompt = promptInput.value.trim();
        if (!prompt) return;

        // UI State -> Loading
        document.getElementById('resultContainer').style.display = 'none';
        document.getElementById('errorState').style.display = 'none';
        document.getElementById('loadingState').style.display = 'block';
        hideBlockDialog();
        analyzeBtn.disabled = true;

        try {
            // Full dual-layer pipeline: Layer 1 -> LLM -> Layer 2 -> final response.
            // (Previously called /detect, which only ran Layer 1 and never
            // invoked the LLM or Layer 2 response validation.)
            const res = await fetch('/secure-prompt', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt })
            });

            if (!res.ok) throw new Error('API Error');

            const data = await res.json();
            renderResult(data, prompt);
        } catch (err) {
            console.error(err);
            document.getElementById('loadingState').style.display = 'none';
            document.getElementById('errorState').style.display = 'block';
        } finally {
            analyzeBtn.disabled = false;
        }
    }

    function renderResult(data, promptText) {
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('resultContainer').style.display = 'block';

        // Expander Reset
        expanderBtn.classList.remove('open');
        expanderContent.style.display = 'none';

        // /secure-prompt nests the Layer 1 verdict/explanation under "layer1"
        // (same schema previously returned flat by /detect). Layer 2 result
        // and the overall pipeline outcome are new, additional fields.
        const layer1 = data.layer1 || data;
        const layer2 = data.layer2 || {};
        const overallDecision = data.final_decision || layer1.decision || 'UNKNOWN';

        const riskLevel = layer1.risk_level || 'UNKNOWN';
        const riskScore = parseFloat(layer1.risk_score || 0);
        const classification = layer1.classification || layer1.attack_type || 'BENIGN';

        const ruleResult = layer1.rule_result || {};
        const mlResult = layer1.ml_result || {};
        const layer2Decision = layer2.decision || 'NOT_EXECUTED';

        // Layer 1 HIGH/CRITICAL block: use only the backend's own decision and
        // risk_level, never a client-side security judgement.
        const HIGH_CRITICAL_LEVELS = ['HIGH', 'CRITICAL'];
        const isLayer1HighCriticalBlock = (
            data.llm_called === false &&
            layer1.decision === 'BLOCK' &&
            HIGH_CRITICAL_LEVELS.includes(riskLevel)
        );

        const analyzedPromptExpander = document.getElementById('analyzedPromptExpander');
        if (isLayer1HighCriticalBlock) {
            // Don't display the blocked prompt unnecessarily: the expander
            // is hidden entirely and the prompt text is never written to the DOM.
            if (analyzedPromptExpander) analyzedPromptExpander.style.display = 'none';
            document.getElementById('analyzedPromptText').textContent = '';
            showBlockDialog(layer1, riskLevel);
        } else {
            if (analyzedPromptExpander) analyzedPromptExpander.style.display = '';
            document.getElementById('analyzedPromptText').textContent = promptText;
            hideBlockDialog();
        }

        // Populate Top Card
        const securityCard = document.getElementById('securityCard');
        const scDecisionBadge = document.getElementById('scDecisionBadge');
        const scIcon = document.getElementById('scIcon');
        const scDecisionText = document.getElementById('scDecisionText');

        securityCard.className = 'security-card';

        if (overallDecision === 'ALLOW') {
            securityCard.classList.add('safe');
            scIcon.textContent = '✓';
            scDecisionText.textContent = 'SAFE';
        } else if (overallDecision === 'WARNING' || riskLevel === 'WARNING' || riskLevel === 'MEDIUM') {
            securityCard.classList.add('warning');
            scIcon.textContent = '!';
            scDecisionText.textContent = 'WARNING';
        } else if (overallDecision === 'MASK') {
            securityCard.classList.add('warning');
            scIcon.textContent = '!';
            scDecisionText.textContent = 'RESPONSE SANITIZED';
        } else if (overallDecision === 'ERROR') {
            securityCard.classList.add('block');
            scIcon.textContent = '✕';
            scDecisionText.textContent = 'PROVIDER ERROR';
        } else {
            securityCard.classList.add('block');
            scIcon.textContent = '✕';
            scDecisionText.textContent = 'THREAT DETECTED';
        }

        // Risk Meter
        document.getElementById('resRiskScoreVal').textContent = riskScore.toFixed(1);
        const riskMeterFill = document.getElementById('riskMeterFill');
        riskMeterFill.style.width = riskScore + '%';

        // Metrics
        document.getElementById('resRiskLevel').textContent = riskLevel;
        document.getElementById('resDecision').textContent = layer1.decision || overallDecision;
        document.getElementById('resClassification').textContent = classification;

        // Breakdown
        document.getElementById('bdRule').textContent = ruleResult.rule_triggered ? 'DETECTED' : 'CLEAN';
        document.getElementById('bdNLP').textContent = mlResult.is_malicious ? 'DETECTED' : 'CLEAN';
        document.getElementById('bdRisk').textContent = riskLevel;
        document.getElementById('bdLayer2').textContent = layer2Decision;
        document.getElementById('bdDecision').textContent = overallDecision;

        // Final system response (post Layer 2 sanitization/blocking)
        const responseSection = document.getElementById('responseSection');
        const resResponseText = document.getElementById('resResponseText');
        if (resResponseText) {
            if (typeof data.response === 'string' && data.response.length > 0) {
                resResponseText.textContent = data.response;
                if (responseSection) responseSection.style.display = '';
            } else if (responseSection) {
                responseSection.style.display = 'none';
            }
        }
    }

    function showBlockDialog(layer1, riskLevel) {
        const overlay = document.getElementById('blockDialogOverlay');
        if (!overlay) return;

        // Populate strictly from the backend's own verdict/explanation data.
        document.getElementById('blockDialogRiskLevel').textContent = riskLevel || 'UNKNOWN';
        document.getElementById('blockDialogAttackType').textContent =
            layer1.attack_type || layer1.classification || 'Prompt Injection';

        const reasonEl = document.getElementById('blockDialogReason');
        reasonEl.textContent = layer1.reason ? layer1.reason : '';

        overlay.style.display = 'flex';
    }

    function hideBlockDialog() {
        const overlay = document.getElementById('blockDialogOverlay');
        if (overlay) overlay.style.display = 'none';
    }

    const blockDialogRetryBtn = document.getElementById('blockDialogRetryBtn');
    if (blockDialogRetryBtn) {
        blockDialogRetryBtn.addEventListener('click', () => {
            // Honest, non-security action: simply clears the way for the user
            // to type a new prompt. No fake authentication or verification step.
            hideBlockDialog();
            if (promptInput) {
                promptInput.value = '';
                promptInput.focus();
                if (charCount) {
                    charCount.textContent = `0 / ${MAX_CHARS} characters`;
                }
            }
            document.getElementById('resultContainer').style.display = 'none';
        });
    }

    function renderEmptyHistory() {
        const tbody = document.getElementById('historyTbody');
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="empty-state">
                    <div class="empty-state-content" style="padding: 3rem 1rem; text-align: center; color: var(--text-secondary);">
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom: 1rem; opacity: 0.5;">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                            <polyline points="12 8 12 12 14 14"></polyline>
                        </svg>
                        <h3 style="color: var(--brand-navy); font-size: 1.1rem; margin-bottom: 0.5rem;">No analyses yet</h3>
                        <p style="margin-bottom: 1.5rem; font-size: 0.9rem;">Your prompt analysis history will appear here.</p>
                        <a href="#analyzer" class="btn btn-outline btn-sm">Analyze a Prompt</a>
                    </div>
                </td>
            </tr>
        `;
    }

    async function loadHistory() {
        const tbody = document.getElementById('historyTbody');
        // keep existing loading state from HTML if it's there
        if (!tbody.innerHTML.includes('empty-state-content')) {
             tbody.innerHTML = '<tr><td colspan="5" class="empty-state">Retrieving incident telemetry...</td></tr>';
        }

        try {
            const res = await fetch('/api/incidents');
            if (!res.ok) throw new Error('API Error');
            const data = await res.json();

            if (!data || data.length === 0) {
                renderEmptyHistory();
                return;
            }

            tbody.innerHTML = '';
            const topData = data.slice(0, 15);

            topData.forEach(inc => {
                const tr = document.createElement('tr');
                
                const time = new Date(inc.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                const promptSnippet = (inc.prompt || inc.attack_type || '').substring(0, 40) + '...';
                const riskLevel = inc.risk_level || 'INFO';
                const score = (inc.risk_score !== undefined) ? inc.risk_score.toFixed(1) + '%' : '--';
                
                let decision = 'ALLOW';
                if (riskLevel === 'CRITICAL' || riskLevel === 'HIGH') decision = 'BLOCK';
                else if (riskLevel === 'WARNING' || riskLevel === 'MEDIUM') decision = 'WARN';

                tr.innerHTML = `
                    <td style="color: var(--text-secondary); font-weight: 500;">${time}</td>
                    <td style="font-family: monospace; color: var(--brand-navy);">${promptSnippet}</td>
                    <td><span class="rtag r-${riskLevel.toLowerCase().substring(0,4)}">${riskLevel}</span></td>
                    <td style="font-weight: 600;">${score}</td>
                    <td style="font-weight: 600;">${decision}</td>
                `;
                tbody.appendChild(tr);
            });

        } catch (err) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty-state">Failed to connect to logging service.</td></tr>';
        }
    }

});
