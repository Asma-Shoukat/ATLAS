/* =====================================================================
   ATLAS — ADAPTIVE TRUSTWORTHY LANGUAGE-AUGMENTED SEARCH
   Frontend Controller (7-Pillar Pipeline Visualization)
   ===================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    const API_BASE_URL = "http://127.0.0.1:5000";

    // Conversation history array
    let chatHistory = [];
    let currentDomain = "GLOBAL";
    let bootPollingInterval = null;
    let isSystemReady = false;  // Boot guard: prevents chat until pipeline is fully loaded

    // --- DOM ELEMENT REFERENCES ---
    // 1. Center Desktop Chat viewport elements
    const mainChatForm = document.getElementById("main-chat-form");
    const mainChatInputField = document.getElementById("main-chat-input-field");
    const mainChatMessagesContainer = document.getElementById("main-chat-messages-container");
    // 2. Floating Command Center elements
    const chatToggleBtn = document.getElementById("chat-toggle-btn");
    const chatCloseBtn = document.getElementById("chat-close-btn");
    const chatboxPopup = document.getElementById("chatbox-popup");
    const cmdPipelineStatus = document.getElementById("cmd-pipeline-status");
    const cmdStatusIcon = document.getElementById("cmd-status-icon");
    const cmdStatusText = document.getElementById("cmd-status-text");
    const cmdStatusDetail = document.getElementById("cmd-status-detail");
    const cmdRecentList = document.getElementById("cmd-recent-list");
    const cmdRecentEmpty = document.getElementById("cmd-recent-empty");
    const cmdNotifications = document.getElementById("cmd-notifications");

    // 3. System Telemetry & Controls
    const systemStatusText = document.getElementById("system-status-text");
    const statusDot = document.querySelector(".indicator-status-dot");
    const hardwareEngine = document.getElementById("hardware-engine");
    const statTotalDocs = document.getElementById("stat-total-docs");
    const statFaissStatus = document.getElementById("stat-faiss-status");
    const activeDomainTelemetry = document.getElementById("active-domain-telemetry");

    // 4. Trial Buttons (Sidebar scenario thread cards!)
    const trialTopicSwitch = document.getElementById("trial-topic-switch");
    const trialIntentAttack = document.getElementById("trial-intent-attack");
    const trialPolicySpec = document.getElementById("trial-policy-spec");

    // 5. Diagnostics trace elements
    const pipelineEmptyState = document.getElementById("pipeline-empty-state");
    const stepCoref = document.getElementById("step-coref");
    const stepRetrieval = document.getElementById("step-retrieval");
    const stepRerank = document.getElementById("step-rerank");
    const stepGuards = document.getElementById("step-guards");
    const stepProvenance = document.getElementById("step-provenance");
    const stepExplainability = document.getElementById("step-explainability");

    const traceTime = document.getElementById("trace-time");
    const originalQueryText = document.getElementById("original-query-text");
    const rewrittenQueryText = document.getElementById("rewritten-query-text");
    const contextResolutionMeta = document.getElementById("context-resolution-meta");
    const retrievalStatsBar = document.getElementById("retrieval-stats-bar");
    const faissCandidatesList = document.getElementById("faiss-candidates-list");
    const peakLogitBar = document.getElementById("peak-logit-bar");
    const logitValueIndicator = document.getElementById("logit-value-indicator");
    const matchedDomainTag = document.getElementById("matched-domain-tag");
    const matchedThresholdVal = document.getElementById("matched-threshold-val");

    // Decision Agent elements
    const decisionVerdictCard = document.getElementById("decision-verdict-card");
    const verdictIconWrap = document.getElementById("verdict-icon-wrap");
    const verdictLabel = document.getElementById("verdict-label");
    const verdictReason = document.getElementById("verdict-reason");
    const shieldThreshold = document.getElementById("shield-threshold");
    const shieldOverlap = document.getElementById("shield-overlap");

    // Provenance elements
    const provenanceId = document.getElementById("provenance-id");
    const provenanceMethod = document.getElementById("provenance-method");
    const provenanceText = document.getElementById("provenance-text");

    // Explainability elements
    const explainWhyRetrieved = document.getElementById("explain-why-retrieved");
    const explainDecision = document.getElementById("explain-decision");
    const explainMatchedTokens = document.getElementById("explain-matched-tokens");

    // Create Tooltip DOM Element
    const tooltip = document.createElement("div");
    tooltip.className = "metadata-tooltip-panel hide";
    document.body.appendChild(tooltip);

    // Helper to escape HTML tags
    function escapeHtml(text) {
        if (!text) return "";
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // --- INTERACTIVE METADATA HOVER TOOLTIP SYSTEM ---
    function bindTooltip(element, citationData) {
        element.addEventListener("mouseenter", (e) => {
            const escapedText = escapeHtml(citationData.full_text);
            tooltip.innerHTML = `
                <div style="font-weight: 700; color: var(--warning); margin-bottom: 6px; font-family: var(--font-heading); display: flex; align-items: center; gap: 6px;">
                    <i class="fa-solid fa-fingerprint"></i> GROUNDING PROVENANCE METADATA
                </div>
                <div style="margin-bottom: 4px; color: rgba(255,255,255,0.6); font-size: 10px;">
                    <strong>Document ID:</strong> <span style="font-family: monospace; font-size: 9px; color: var(--primary);">${citationData.passage_id}</span>
                </div>
                <div style="margin-bottom: 4px; color: rgba(255,255,255,0.6); font-size: 10px;">
                    <strong>Domain:</strong> <span class="cand-domain" style="background: rgba(217, 119, 6, 0.12); color: var(--warning); border: 1px solid rgba(217, 119, 6, 0.25);">${citationData.domain}</span>
                </div>
                <div style="margin-bottom: 4px; color: rgba(255,255,255,0.6); font-size: 10px;">
                    <strong>Retrieved Via:</strong> <span style="color: var(--success); font-weight: 700;">${citationData.retrieval_method || 'HYBRID'}</span>
                </div>
                <div style="margin-bottom: 6px; color: rgba(255,255,255,0.6); font-size: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                    <strong>Title:</strong> <span style="color: #FFF; font-weight: 600;">${escapeHtml(citationData.title)}</span>
                </div>
                <div style="margin-top: 6px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 6px; font-style: italic; max-height: 120px; overflow-y: auto; color: rgba(255,255,255,0.9); line-height: 1.4; scrollbar-width: none;">
                    "${escapedText}"
                </div>
            `;
            tooltip.classList.remove("hide");
        });

        element.addEventListener("mousemove", (e) => {
            const offset = 15;
            let left = e.pageX + offset;
            let top = e.pageY + offset;
            if (left + 260 > window.innerWidth) {
                left = e.pageX - 270;
            }
            if (top + 200 > window.innerHeight) {
                top = e.pageY - 210;
            }
            tooltip.style.left = `${left}px`;
            tooltip.style.top = `${top}px`;
        });

        element.addEventListener("mouseleave", () => {
            tooltip.classList.add("hide");
        });
    }

    // --- ANIMATED PARTICLE BACKGROUND GRID ---
    const canvas = document.getElementById("background-particles");
    const ctx = canvas.getContext("2d");

    let particles = [];
    const maxParticles = 65;

    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    window.addEventListener("resize", resizeCanvas);
    resizeCanvas();

    class Particle {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.vx = (Math.random() - 0.5) * 0.4;
            this.vy = (Math.random() - 0.5) * 0.4;
            this.radius = Math.random() * 2 + 1;
            this.color = Math.random() > 0.5 ? "rgba(179, 142, 91, 0.15)" : "rgba(139, 92, 246, 0.1)";
        }

        update() {
            this.x += this.vx;
            this.y += this.vy;
            if (this.x < 0 || this.x > canvas.width) this.vx *= -1;
            if (this.y < 0 || this.y > canvas.height) this.vy *= -1;
        }

        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
            ctx.fillStyle = this.color;
            ctx.fill();
        }
    }

    for (let i = 0; i < maxParticles; i++) {
        particles.push(new Particle());
    }

    function animateParticles() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => {
            p.update();
            p.draw();
        });

        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dist = Math.hypot(particles[i].x - particles[j].x, particles[i].y - particles[j].y);
                if (dist < 100) {
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = `rgba(179, 142, 91, ${0.06 * (1 - dist / 100)})`;
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(animateParticles);
    }
    animateParticles();

    // --- DOMAIN SELECTION HANDLERS ---
    const domainTabs = document.querySelectorAll(".domain-tab");
    domainTabs.forEach(tab => {
        tab.addEventListener("click", () => {
            domainTabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            currentDomain = tab.getAttribute("data-domain");
            activeDomainTelemetry.innerText = `${currentDomain} ACTIVE`;
            console.log(`[ATLAS] Domain locked: [${currentDomain}]`);
        });
    });

    // --- FLOATING COMMAND CENTER TOGGLE ACTIONS ---
    chatToggleBtn.addEventListener("click", () => {
        chatboxPopup.classList.toggle("hide");
    });

    chatCloseBtn.addEventListener("click", () => {
        chatboxPopup.classList.add("hide");
    });

    // --- RECENT QUERIES TRACKING ---
    let recentQueries = [];
    const MAX_RECENT = 5;

    function addRecentQuery(text, domain) {
        // Remove duplicate if exists
        recentQueries = recentQueries.filter(q => q.text !== text);
        // Add to front
        recentQueries.unshift({ text, domain, time: new Date() });
        // Limit size
        if (recentQueries.length > MAX_RECENT) recentQueries.pop();
        renderRecentQueries();
    }

    function renderRecentQueries() {
        if (!cmdRecentList) return;
        // Clear existing items (except empty state)
        const existingItems = cmdRecentList.querySelectorAll(".cmd-recent-item");
        existingItems.forEach(item => item.remove());

        if (recentQueries.length === 0) {
            if (cmdRecentEmpty) cmdRecentEmpty.style.display = "flex";
            return;
        }
        if (cmdRecentEmpty) cmdRecentEmpty.style.display = "none";

        recentQueries.forEach(q => {
            const item = document.createElement("div");
            item.className = "cmd-recent-item";
            item.innerHTML = `
                <i class="fa-solid fa-clock-rotate-left cmd-recent-icon"></i>
                <span class="cmd-recent-text">${escapeHtml(q.text)}</span>
                <span class="cmd-recent-domain ${q.domain}">${q.domain}</span>
            `;
            item.addEventListener("click", () => {
                // Switch domain tab
                const targetTab = document.querySelector(`.domain-tab[data-domain="${q.domain}"]`);
                if (targetTab) targetTab.click();
                sendUserQuery(q.text);
            });
            cmdRecentList.appendChild(item);
        });
    }

    // --- COMMAND CENTER NOTIFICATION SYSTEM ---
    function addNotification(text, type = "info") {
        if (!cmdNotifications) return;
        const notif = document.createElement("div");
        notif.className = `cmd-notif-item ${type}`;
        const iconClass = type === "success" ? "fa-circle-check" : type === "warning" ? "fa-triangle-exclamation" : "fa-circle-info";
        const now = new Date();
        const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        notif.innerHTML = `
            <i class="fa-solid ${iconClass} cmd-notif-icon"></i>
            <div class="cmd-notif-content">
                <span class="cmd-notif-text">${escapeHtml(text)}</span>
                <span class="cmd-notif-time">${timeStr}</span>
            </div>
        `;
        // Insert at top
        cmdNotifications.insertBefore(notif, cmdNotifications.firstChild);
        // Keep max 6 notifications
        while (cmdNotifications.children.length > 6) {
            cmdNotifications.removeChild(cmdNotifications.lastChild);
        }
    }

    // --- BOOT SYSTEM MONITORING (POLLING STATS API) ---
    function checkSystemBoot() {
        fetch(`${API_BASE_URL}/api/stats`)
            .then(res => {
                if (!res.ok) throw new Error("Server loading");
                return res.json();
            })
            .then(data => {
                const boot = data.boot_status || {};
                const progress = boot.progress || 0;

                systemStatusText.innerText = `${boot.stage} (${progress}%)`;

                // Update Command Center status
                if (cmdStatusText) cmdStatusText.innerText = `${boot.stage} (${progress}%)`;
                if (cmdPipelineStatus) cmdPipelineStatus.innerText = progress === 100 ? "Online" : `${boot.stage}...`;

                if (data.passages_count) {
                    statTotalDocs.innerText = data.passages_count.toLocaleString();
                    if (cmdStatusDetail) cmdStatusDetail.innerHTML = `<i class="fa-solid fa-circle"></i> ${data.passages_count.toLocaleString()} passages loaded`;
                }
                if (data.compute_device) {
                    hardwareEngine.innerHTML = `<i class="fa-solid fa-microchip"></i> Engine: ${data.compute_device.toUpperCase()}`;
                }
                if (boot.faiss_status) {
                    statFaissStatus.innerText = boot.faiss_status;
                }

                if (progress === 100) {
                    isSystemReady = true;  // Unlock chat submissions
                    statusDot.classList.remove("pulsing");
                    statusDot.classList.add("clean");
                    systemStatusText.innerText = "ATLAS PIPELINE ACTIVE";
                    console.log("[ATLAS] System boot complete and ready.");
                    clearInterval(bootPollingInterval);

                    // Update Command Center
                    if (cmdStatusText) cmdStatusText.innerText = "ATLAS Pipeline Active";
                    if (cmdStatusIcon) {
                        cmdStatusIcon.classList.remove("booting");
                        cmdStatusIcon.innerHTML = '<i class="fa-solid fa-circle-check"></i>';
                    }
                    addNotification("ATLAS pipeline fully initialized and ready.", "success");
                }
            })
            .catch(err => {
                systemStatusText.innerText = "ESTABLISHING APIS...";
                console.log("[ATLAS BOOT] Waiting for Flask API service to initialize...");
            });
    }

    bootPollingInterval = setInterval(checkSystemBoot, 2000);
    checkSystemBoot();

    // --- PREMIUM TYPEWRITER EFFECT ENGINE ---
    function typeWrite(element, htmlString, speed = 5, onComplete = null) {
        element.innerHTML = "";
        let isTag = false;
        let text = "";
        let i = 0;

        function next() {
            if (i >= htmlString.length) {
                element.innerHTML = htmlString;
                // Hook tooltip binding if there are citation elements
                const citationBadge = element.querySelector(".citation-badge-ui");
                if (citationBadge && element.dataset.citationInfo) {
                    try {
                        const citationData = JSON.parse(element.dataset.citationInfo);
                        bindTooltip(citationBadge, citationData);
                    } catch (e) {
                        console.error("Failed to parse citation metadata for tooltip hook", e);
                    }
                }
                if (onComplete) onComplete();
                return;
            }
            let char = htmlString.charAt(i);
            if (char === "<") {
                isTag = true;
            }
            text += char;
            if (char === ">") {
                isTag = false;
            }
            element.innerHTML = text;
            i++;
            if (isTag) {
                next();
            } else {
                setTimeout(next, speed);
            }
        }
        next();
    }

    // --- CHAT MESSAGE UI FUNCTIONS (DUALLY SYNCHRONIZED) ---
    function createMessageBubble(sender, text, isHtml = false, citationData = null, isMain = true) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("chat-message", sender);

        const avatar = document.createElement("div");
        avatar.classList.add("msg-avatar");
        avatar.innerHTML = sender === "user" ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';

        const bubble = document.createElement("div");
        bubble.classList.add("msg-card");

        const titleSpan = document.createElement("span");
        titleSpan.className = "avatar-title";
        titleSpan.innerText = sender === "user" ? "SYSTEM OPERATOR" : "ATLAS SEARCH SERVICE";
        bubble.appendChild(titleSpan);

        const contentWrapper = document.createElement("div");
        bubble.appendChild(contentWrapper);

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(bubble);

        if (sender === "assistant") {
            if (citationData) {
                bubble.dataset.citationInfo = JSON.stringify(citationData);
            }
            typeWrite(contentWrapper, text, 4, () => {
                if (isMain) {
                    mainChatMessagesContainer.scrollTop = mainChatMessagesContainer.scrollHeight;
                } else {
                    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
                }
            });
        } else {
            if (isHtml) {
                contentWrapper.innerHTML = text;
            } else {
                const p = document.createElement("p");
                p.innerText = text;
                contentWrapper.appendChild(p);
            }
        }

        return messageDiv;
    }

    function appendMessage(sender, text, isHtml = false, citationData = null) {
        // Render only in Desktop Main view (popup is now Command Center, not chat)
        const mainBubble = createMessageBubble(sender, text, isHtml, citationData, true);
        mainChatMessagesContainer.appendChild(mainBubble);
        mainChatMessagesContainer.scrollTop = mainChatMessagesContainer.scrollHeight;
    }

    function showTypingIndicator() {
        const mainIndicator = document.createElement("div");
        mainIndicator.classList.add("chat-message", "assistant", "typing-indicator-wrapper");
        mainIndicator.innerHTML = `
            <div class="msg-avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="msg-card typing-bubble">
                <span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>
            </div>
        `;
        mainChatMessagesContainer.appendChild(mainIndicator);
        mainChatMessagesContainer.scrollTop = mainChatMessagesContainer.scrollHeight;

        return { main: mainIndicator };
    }

    // --- Helper: retrieval method color ---
    function getMethodColor(method) {
        if (method === "HYBRID") return { bg: "rgba(16, 185, 129, 0.1)", color: "#10B981", border: "rgba(16, 185, 129, 0.2)" };
        if (method === "DENSE") return { bg: "rgba(59, 130, 246, 0.1)", color: "#3B82F6", border: "rgba(59, 130, 246, 0.2)" };
        return { bg: "rgba(217, 119, 6, 0.1)", color: "#D97706", border: "rgba(217, 119, 6, 0.2)" };
    }

    // --- ATLAS 7-PILLAR PIPELINE TRACE RENDERER ---
    function renderPipelineTrace(trace) {
        // Remove empty state
        pipelineEmptyState.classList.add("hide");

        // Display latency
        traceTime.innerText = `${trace.time_ms}ms`;

        const explainability = trace.explainability || {};
        const queryUnderstanding = explainability.query_understanding || {};
        const retrievalReasoning = explainability.retrieval_reasoning || {};
        const decisionReasoning = explainability.decision_reasoning || {};

        // ============================================================
        // STEP 1: Conversational Context + Query Rewriting (Pillars 1+2)
        // ============================================================
        originalQueryText.innerText = `"${trace.original_query}"`;
        rewrittenQueryText.innerText = `"${trace.rewritten_query}"`;

        // Show context resolution metadata
        let metaHtml = '';
        if (queryUnderstanding.resolved) {
            metaHtml += `<div class="context-meta-item resolved">
                <i class="fa-solid fa-link"></i>
                <span>Pronoun resolved: <strong>"${queryUnderstanding.pronouns_detected?.join(', ') || '—'}"</strong> → <strong>${queryUnderstanding.referent || '—'}</strong></span>
            </div>`;
        } else {
            metaHtml += `<div class="context-meta-item standalone">
                <i class="fa-solid fa-check-circle"></i>
                <span>Query is already standalone — no resolution needed</span>
            </div>`;
        }
        if (queryUnderstanding.entities_found && queryUnderstanding.entities_found.length > 0) {
            metaHtml += `<div class="context-meta-item entities">
                <i class="fa-solid fa-tags"></i>
                <span>Context entities: ${queryUnderstanding.entities_found.map(e => `<strong>${escapeHtml(e)}</strong>`).join(', ')}</span>
            </div>`;
        }
        contextResolutionMeta.innerHTML = metaHtml;

        stepCoref.classList.remove("hide");
        stepCoref.classList.add("active");

        // ============================================================
        // STEP 2: Hybrid Retrieval (Pillar 3)
        // ============================================================
        // Retrieval stats bar
        const bm25Count = retrievalReasoning.bm25_candidates || 0;
        const denseCount = retrievalReasoning.dense_candidates || 0;
        const fusedTotal = retrievalReasoning.fused_total || 0;
        retrievalStatsBar.innerHTML = `
            <div class="retrieval-stat">
                <span class="retrieval-method-tag bm25">BM25</span>
                <span class="retrieval-stat-val">${bm25Count} hits</span>
            </div>
            <div class="retrieval-stat">
                <span class="retrieval-method-tag dense">DENSE</span>
                <span class="retrieval-stat-val">${denseCount} hits</span>
            </div>
            <div class="retrieval-stat">
                <span class="retrieval-method-tag hybrid">FUSED</span>
                <span class="retrieval-stat-val">${fusedTotal} candidates</span>
            </div>
        `;

        // Candidate list
        faissCandidatesList.innerHTML = "";
        const candidates = trace.coarse_candidates || [];
        candidates.slice(0, 5).forEach((cand, idx) => {
            const li = document.createElement("li");
            const methodStyle = getMethodColor(cand.retrieval_method || "BM25");
            li.innerHTML = `
                <div class="cand-meta">
                    <span class="retrieval-method-tag" style="background: ${methodStyle.bg}; color: ${methodStyle.color}; border: 1px solid ${methodStyle.border};">${cand.retrieval_method || '—'}</span>
                    <span class="cand-title">${escapeHtml(cand.title.slice(0, 32))}${cand.title.length > 32 ? '...' : ''}</span>
                </div>
                <span class="cand-score">RRF: ${cand.fused_score ? cand.fused_score.toFixed(5) : '—'}</span>
            `;
            faissCandidatesList.appendChild(li);
        });
        stepRetrieval.classList.remove("hide");
        stepRetrieval.classList.add("active");

        // ============================================================
        // STEP 3: Cross-Encoder Reranking
        // ============================================================
        const verdict = trace.verdict || {};
        const logit = verdict.highest_logit || 0;
        const threshold = verdict.threshold || -2.0;

        let progressPercent = ((logit + 10) / 20) * 100;
        progressPercent = Math.max(0, Math.min(100, progressPercent));
        peakLogitBar.style.width = `${progressPercent}%`;

        logitValueIndicator.innerText = `Score: ${logit.toFixed(4)}`;
        matchedDomainTag.innerText = `[${trace.citation ? trace.citation.domain : trace.target_domain}]`;
        matchedThresholdVal.innerText = `${threshold.toFixed(3)}`;

        if (verdict.status === "INTERCEPTED" && verdict.below_threshold) {
            peakLogitBar.style.background = "linear-gradient(90deg, #F87171 0%, var(--danger) 100%)";
            logitValueIndicator.style.color = "var(--danger)";
        } else {
            peakLogitBar.style.background = "linear-gradient(90deg, var(--primary) 0%, var(--success) 100%)";
            logitValueIndicator.style.color = "var(--primary)";
        }
        stepRerank.classList.remove("hide");
        stepRerank.classList.add("active");

        // ============================================================
        // STEP 4: Decision Agent (Pillar 4)
        // ============================================================
        if (verdict.status === "INTERCEPTED") {
            decisionVerdictCard.className = "decision-verdict-card intercepted";
            verdictIconWrap.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i>';
            verdictLabel.innerText = "INTERCEPTED";
            verdictLabel.style.color = "var(--danger)";
            verdictReason.innerText = verdict.reason || "Insufficient evidence detected.";
        } else {
            decisionVerdictCard.className = "decision-verdict-card approved";
            verdictIconWrap.innerHTML = '<i class="fa-solid fa-circle-check"></i>';
            verdictLabel.innerText = "APPROVED";
            verdictLabel.style.color = "var(--success)";
            verdictReason.innerText = verdict.reason || "Sufficient evidence found.";
        }

        // Threshold shield
        if (verdict.below_threshold) {
            shieldThreshold.className = "luxe-shield intercepted";
            shieldThreshold.querySelector(".status-icon").className = "fa-solid fa-triangle-exclamation status-icon";
            shieldThreshold.querySelector(".status-msg").innerText = "BELOW THRESHOLD";
        } else {
            shieldThreshold.className = "luxe-shield clean";
            shieldThreshold.querySelector(".status-icon").className = "fa-solid fa-chart-line status-icon";
            shieldThreshold.querySelector(".status-msg").innerText = "PASSED";
        }

        // Overlap shield
        if (verdict.low_overlap) {
            shieldOverlap.className = "luxe-shield intercepted";
            shieldOverlap.querySelector(".status-icon").className = "fa-solid fa-triangle-exclamation status-icon";
            shieldOverlap.querySelector(".status-msg").innerText = `LOW OVERLAP (${verdict.overlap_count || 0})`;
        } else {
            shieldOverlap.className = "luxe-shield clean";
            shieldOverlap.querySelector(".status-icon").className = "fa-solid fa-magnifying-glass-chart status-icon";
            shieldOverlap.querySelector(".status-msg").innerText = `PASSED (${verdict.overlap_count || 0} terms)`;
        }

        stepGuards.classList.remove("hide");
        stepGuards.classList.add("active");

        // ============================================================
        // STEP 5: Evidence-Grounded Citation (Pillars 5+6)
        // ============================================================
        if (verdict.status === "INTERCEPTED") {
            stepProvenance.classList.add("hide");
            stepProvenance.classList.remove("active");
        } else {
            const citation = trace.citation || {};
            provenanceId.innerText = citation.passage_id || "—";
            provenanceMethod.innerText = citation.retrieval_method || "HYBRID";

            // Color the method tag
            const mStyle = getMethodColor(citation.retrieval_method || "HYBRID");
            provenanceMethod.style.color = mStyle.color;

            provenanceText.innerText = `"${citation.sentence || '—'}"`;
            stepProvenance.classList.remove("hide");
            stepProvenance.classList.add("active");
        }

        // ============================================================
        // STEP 6: Explainability Report (Pillar 7)
        // ============================================================
        explainWhyRetrieved.innerText = retrievalReasoning.why_retrieved || "No retrieval reasoning available.";

        const decReason = decisionReasoning.reason || verdict.reason || "—";
        const decScore = decisionReasoning.confidence_score != null ? decisionReasoning.confidence_score.toFixed(3) : "—";
        const decThresh = decisionReasoning.threshold != null ? decisionReasoning.threshold.toFixed(1) : "—";
        explainDecision.innerText = `${decReason} (Score: ${decScore}, Threshold: ${decThresh})`;

        // Matched tokens display
        const matchedTokens = retrievalReasoning.matched_query_tokens || [];
        if (matchedTokens.length > 0) {
            explainMatchedTokens.innerHTML = matchedTokens.map(t =>
                `<span class="matched-token-pill">${escapeHtml(t)}</span>`
            ).join('');
        } else {
            explainMatchedTokens.innerHTML = '<span class="no-tokens">No specific tokens matched</span>';
        }

        stepExplainability.classList.remove("hide");
        stepExplainability.classList.add("active");
    }

    // --- API POST CHAT CALL ---
    function sendUserQuery(text) {
        if (!text) return;

        // Boot guard: block chat submission if pipeline hasn't finished loading
        if (!isSystemReady) {
            appendMessage("assistant",
                '<p style="line-height: 1.5;"><i class="fa-solid fa-hourglass-half" style="color: var(--warning); margin-right: 6px;"></i>' +
                '<strong>System is still loading.</strong> The ATLAS pipeline is initializing ML models and building search indices. ' +
                'Please wait for the status indicator to show <strong>"ATLAS PIPELINE ACTIVE"</strong> before submitting queries.</p>', true);
            addNotification("Query blocked — system still booting.", "warning");
            return;
        }

        // Track in recent queries for command center
        addRecentQuery(text, currentDomain);

        appendMessage("user", text);
        mainChatInputField.value = "";

        const typingIndicators = showTypingIndicator();

        fetch(`${API_BASE_URL}/api/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: text,
                history: chatHistory,
                domain: currentDomain
            })
        })
            .then(res => {
                if (!res.ok) throw new Error("API call error");
                return res.json();
            })
            .then(data => {
                // Remove typing bubble
                typingIndicators.main.remove();

                // Format answer with rich citation + explainability if approved
                let formattedAnswer = data.answer;
                const explain = data.explainability || {};
                const retReason = explain.retrieval_reasoning || {};
                const decReason = explain.decision_reasoning || {};
                const qUnderstanding = explain.query_understanding || {};

                // Fix 9: Declare rewriteNote BEFORE the if/else branching
                // so it's available in both the approved and intercepted code paths
                let rewriteNote = '';
                if (qUnderstanding.resolved) {
                    rewriteNote = `
                    <div class="inline-explain-row">
                        <i class="fa-solid fa-spell-check"></i>
                        <span><strong>Query Rewritten:</strong> "${escapeHtml(qUnderstanding.original)}" → "${escapeHtml(qUnderstanding.rewritten)}" (resolved "<em>${qUnderstanding.pronouns_detected?.join(', ') || '—'}</em>" → <strong>${escapeHtml(qUnderstanding.referent || '')}</strong>)</span>
                    </div>`;
                }

                if (data.citation) {
                    const cite = data.citation;
                    const escapedTitle = escapeHtml(cite.title);
                    const methodStyle = getMethodColor(cite.retrieval_method || "HYBRID");

                    // Build matched tokens pills
                    const matchedTokens = retReason.matched_query_tokens || [];
                    const tokenPillsHtml = matchedTokens.length > 0
                        ? matchedTokens.map(t => `<span class="inline-matched-token">${escapeHtml(t)}</span>`).join(' ')
                        : '<span class="inline-no-tokens">No specific keyword matches</span>';

                    // Generate human-readable English explanation based on retrieval method
                    let englishExplanation = "";
                    const mthd = cite.retrieval_method || "HYBRID";
                    if (mthd === "HYBRID") {
                        englishExplanation = "This information was fetched because it contains the exact keywords you searched for AND its underlying meaning perfectly aligns with your question's context. Because both keyword and meaning match so well, it was selected as the most reliable source to answer your query.";
                    } else if (mthd === "BM25") {
                        englishExplanation = "This information was fetched because it directly contains the specific keywords from your query.";
                    } else {
                        englishExplanation = "This information was fetched because its overall meaning and context strongly align with your question, even if the exact words differ.";
                    }

                    formattedAnswer = `
                    <div class="assistant-lead-in">
                        <i class="fa-solid fa-bookmark" style="color: var(--primary);"></i>
                        VERIFIED REFERENCE IN [${cite.domain}]: ${escapedTitle.slice(0, 36)}${escapedTitle.length > 36 ? '...' : ''}
                    </div>
                    <p style="font-style: normal; line-height: 1.6; margin-bottom: 10px; border-left: 2.5px solid var(--primary); padding: 6px 12px; background: rgba(179, 142, 91, 0.05); border-radius: 0 var(--radius-sm) var(--radius-sm) 0; font-size: 13.5px;">
                        "${cite.sentence}"
                    </p>
                    <div class="citation-badge-ui">
                        <i class="fa-solid fa-circle-check"></i>
                        <span>Citation: <strong>${cite.passage_id.slice(0, 16)}...</strong></span>
                        <span class="retrieval-method-tag" style="background: ${methodStyle.bg}; color: ${methodStyle.color}; border: 1px solid ${methodStyle.border}; font-size: 8px; margin-left: 4px;">${cite.retrieval_method || 'HYBRID'}</span>
                    </div>

                    <!-- EXPLAINABILITY SECTION: WHY this document was retrieved -->
                    <div class="inline-explainability-block">
                        <div class="inline-explain-header">
                            <i class="fa-solid fa-lightbulb"></i> WHY THIS DOCUMENT WAS RETRIEVED
                        </div>
                        ${rewriteNote}
                        <div class="inline-explain-row">
                            <i class="fa-solid fa-magnifying-glass"></i>
                            <span><strong>Retrieval Reasoning:</strong> ${escapeHtml(englishExplanation)}</span>
                        </div>
                        <div class="inline-explain-row">
                            <i class="fa-solid fa-shield-halved"></i>
                            <span><strong>Decision:</strong> ${escapeHtml(decReason.reason || 'Approved')} (Confidence: <strong>${decReason.confidence_score != null ? decReason.confidence_score.toFixed(3) : '—'}</strong>, Threshold: <strong>${decReason.threshold != null ? decReason.threshold.toFixed(1) : '—'}</strong>)</span>
                        </div>
                        <div class="inline-explain-row">
                            <i class="fa-solid fa-tags"></i>
                            <span><strong>Matched Query Terms:</strong> ${tokenPillsHtml}</span>
                        </div>
                        <div class="inline-explain-row">
                            <i class="fa-solid fa-file-lines"></i>
                            <span><strong>Source:</strong> ${escapeHtml(explain.answer_source || 'Evidence extracted from document')}</span>
                        </div>
                    </div>
                `;
                } else {
                    // Intercepted — show WHY it was refused
                    let refusalExplain = '';
                    if (decReason.reason) {
                        refusalExplain = `
                        <div class="inline-explainability-block intercepted">
                            <div class="inline-explain-header intercepted-header">
                                <i class="fa-solid fa-triangle-exclamation"></i> WHY THIS QUERY WAS INTERCEPTED
                            </div>
                            ${rewriteNote}
                            <div class="inline-explain-row">
                                <i class="fa-solid fa-shield"></i>
                                <span><strong>Reason:</strong> ${escapeHtml(decReason.reason || 'Confidence below threshold')}</span>
                            </div>
                            <div class="inline-explain-row">
                                <i class="fa-solid fa-chart-line"></i>
                                <span><strong>Confidence Score:</strong> ${decReason.confidence_score != null ? decReason.confidence_score.toFixed(3) : '—'} (Threshold: ${decReason.threshold != null ? decReason.threshold.toFixed(1) : '—'})</span>
                            </div>
                        </div>`;
                    }
                    formattedAnswer = `<p style="line-height: 1.5;">${data.answer}</p>${refusalExplain}`;
                }

                appendMessage("assistant", formattedAnswer, true, data.citation);

                // Update conversational history turns
                chatHistory.push(text);
                chatHistory.push(data.citation ? data.citation.sentence : data.answer);
                if (chatHistory.length > 6) {
                    chatHistory.shift();
                    chatHistory.shift();
                }

                // Render ATLAS 7-pillar pipeline trace
                renderPipelineTrace(data);
            })
            .catch(err => {
                typingIndicators.main.remove();

                // Distinguish between "server booting" (503) and "server unreachable" (network error)
                const errMsg = err.message || '';
                if (errMsg.includes('API call error')) {
                    // Server responded but with an error (likely 503 still booting)
                    appendMessage("assistant",
                        '<p style="line-height: 1.5;"><i class="fa-solid fa-hourglass-half" style="color: var(--warning); margin-right: 6px;"></i>' +
                        '<strong>Pipeline is still initializing.</strong> The ML models and search indices are loading. ' +
                        'Please wait for the boot progress to reach 100% and try again.</p>', true);
                    addNotification("Pipeline still loading. Please wait.", "warning");
                } else {
                    // Server is completely unreachable
                    appendMessage("assistant",
                        '<p style="line-height: 1.5;"><i class="fa-solid fa-triangle-exclamation" style="color: var(--danger); margin-right: 6px;"></i>' +
                        '<strong>Backend server is not running.</strong> Please launch the backend first:<br>' +
                        '<code style="background: rgba(255,255,255,0.06); padding: 4px 8px; border-radius: 4px; font-size: 11px;">run.bat</code> ' +
                        'or manually run <code style="background: rgba(255,255,255,0.06); padding: 4px 8px; border-radius: 4px; font-size: 11px;">venv\\Scripts\\python.exe backend\\app.py</code></p>', true);
                    addNotification("Backend unreachable. Run run.bat to start services.", "warning");
                }
                console.error(err);
            });
    }

    // --- FORM SUBMISSION (MAIN CHAT CONSOLE) ---
    mainChatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const text = mainChatInputField.value.trim();
        if (text) {
            sendUserQuery(text);
        }
    });

    // --- BENCHMARK TRIAL ACTION SHORTCUTS ---
    trialTopicSwitch.addEventListener("click", () => {
        const govtTab = document.querySelector('[data-domain="GOVT"]');
        if (govtTab) govtTab.click();

        chatHistory = [
            "What are the sheltered rooms designated for use?",
            "A safe room, as defined by FEMA, is designed to provide shelter from tornadoes."
        ];

        sendUserQuery("Which state has more wildfires?");
    });

    trialIntentAttack.addEventListener("click", () => {
        const govtTab = document.querySelector('[data-domain="GOVT"]');
        if (govtTab) govtTab.click();

        chatHistory = [];

        sendUserQuery("How do you bake a vanilla wedding cake with buttercream frosting?");
    });

    trialPolicySpec.addEventListener("click", () => {
        const govtTab = document.querySelector('[data-domain="GOVT"]');
        if (govtTab) govtTab.click();

        chatHistory = [];

        sendUserQuery("Why doesn't the government prevent people from living in areas prone to flooding?");
    });

    // --- Search Filter on Stress Test Threads ---
    const dialogueSearch = document.getElementById("dialogue-search");
    if (dialogueSearch) {
        dialogueSearch.addEventListener("input", (e) => {
            const query = e.target.value.toLowerCase();
            const threads = document.querySelectorAll(".thread-item-card");
            threads.forEach(thread => {
                const title = thread.querySelector(".thread-title").innerText.toLowerCase();
                const scenario = thread.querySelector(".scenario-name").innerText.toLowerCase();
                const snippet = thread.querySelector(".thread-snippet").innerText.toLowerCase();
                
                if (title.includes(query) || scenario.includes(query) || snippet.includes(query)) {
                    thread.style.display = "flex";
                } else {
                    thread.style.display = "none";
                }
            });
        });
    }

    // --- DRAGGABLE COMMAND CENTER POP-UP ENGINE ---
    const popHeader = document.querySelector(".pop-header");
    let isDragging = false;
    let startX, startY, initialLeft, initialTop;

    if (popHeader) {
        popHeader.style.cursor = "move";

        popHeader.addEventListener("mousedown", dragStart);
        document.addEventListener("mousemove", dragMove);
        document.addEventListener("mouseup", dragEnd);

        popHeader.addEventListener("touchstart", dragStart, { passive: true });
        document.addEventListener("touchmove", dragMove, { passive: false });
        document.addEventListener("touchend", dragEnd);
    }

    function dragStart(e) {
        if (e.target.closest(".pop-header-actions") || e.target.closest(".chat-close-btn")) {
            return;
        }

        isDragging = true;
        
        const clientX = e.type.startsWith("touch") ? e.touches[0].clientX : e.clientX;
        const clientY = e.type.startsWith("touch") ? e.touches[0].clientY : e.clientY;

        const rect = chatboxPopup.getBoundingClientRect();
        
        initialLeft = rect.left;
        initialTop = rect.top;
        startX = clientX;
        startY = clientY;

        chatboxPopup.style.bottom = "auto";
        chatboxPopup.style.right = "auto";
        chatboxPopup.style.left = `${initialLeft}px`;
        chatboxPopup.style.top = `${initialTop}px`;
        
        chatboxPopup.style.transition = "none";
    }

    function dragMove(e) {
        if (!isDragging) return;

        if (e.cancelable) e.preventDefault();

        const clientX = e.type.startsWith("touch") ? e.touches[0].clientX : e.clientX;
        const clientY = e.type.startsWith("touch") ? e.touches[0].clientY : e.clientY;

        const deltaX = clientX - startX;
        const deltaY = clientY - startY;

        let newLeft = initialLeft + deltaX;
        let newTop = initialTop + deltaY;

        const maxLeft = window.innerWidth - chatboxPopup.offsetWidth - 10;
        const maxTop = window.innerHeight - chatboxPopup.offsetHeight - 10;
        newLeft = Math.max(10, Math.min(newLeft, maxLeft));
        newTop = Math.max(10, Math.min(newTop, maxTop));

        chatboxPopup.style.left = `${newLeft}px`;
        chatboxPopup.style.top = `${newTop}px`;
    }

    function dragEnd() {
        if (!isDragging) return;
        isDragging = false;
        chatboxPopup.style.transition = "all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275)";
    }

    // --- QUICK DATASET BENCHMARK TOKENS BINDINGS (center panel) ---
    const tokenPills = document.querySelectorAll(".token-pill");
    tokenPills.forEach(pill => {
        pill.addEventListener("click", () => {
            const targetDom = pill.getAttribute("data-domain");
            const queryText = pill.getAttribute("data-query");
            
            const targetTab = document.querySelector(`.domain-tab[data-domain="${targetDom}"]`);
            if (targetTab) {
                targetTab.click();
            }
            
            sendUserQuery(queryText);
        });
    });

    // --- COMMAND CENTER QUICK BENCHMARK ACTION CARDS ---
    const cmdActionCards = document.querySelectorAll(".cmd-action-card");
    cmdActionCards.forEach(card => {
        card.addEventListener("click", () => {
            const targetDom = card.getAttribute("data-domain");
            const queryText = card.getAttribute("data-query");
            
            // Switch domain
            const targetTab = document.querySelector(`.domain-tab[data-domain="${targetDom}"]`);
            if (targetTab) targetTab.click();
            
            sendUserQuery(queryText);
            addNotification(`Benchmark launched: "${queryText.slice(0, 40)}..."`, "info");
        });
    });
});
