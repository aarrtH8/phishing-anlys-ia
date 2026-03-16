/**
 * PhishHunter GUI — Frontend SPA
 * Elegant white & gold theme with mascots
 */

let scansData = [];
let scanPollingInterval = null;
let _scanOutputOffset = 0;   // tracks how many chars we've already rendered
let _scanCardBuilt = false;  // true once the status card HTML shell is in the DOM

function navigate(hash) { window.location.hash = hash; }

function handleRoute() {
    const hash = window.location.hash || '#dashboard';
    const parts = hash.slice(1).split('/');
    const view = parts[0];

    document.querySelectorAll('.nav-link').forEach(el => {
        el.classList.toggle('active', el.dataset.view === view ||
            (view === 'report' && el.dataset.view === 'dashboard'));
    });

    document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));

    switch (view) {
        case 'report': showReport(parts.slice(1).join('/')); break;
        case 'scan': showScanForm(); break;
        default: showDashboard();
    }
}

// ── Dashboard ──
async function showDashboard() {
    const container = document.getElementById('view-dashboard');
    container.classList.remove('hidden');
    container.innerHTML = `
        <div class="page-header">
            <img class="page-header-mascot" src="/static/mascot_detective.png" alt="">
            <div>
                <h1 class="page-title">Tableau de bord</h1>
                <p class="page-description">Vue d'ensemble de vos analyses forensiques</p>
            </div>
        </div>
        <div class="stats-bar" id="stats-bar">
            ${[1, 2, 3, 4, 5].map(() => '<div class="stat-card skeleton" style="height:72px"></div>').join('')}
        </div>
        <div class="scans-grid" id="scans-grid">
            ${[1, 2, 3, 4].map(() => '<div class="scan-card skeleton" style="height:180px"></div>').join('')}
        </div>
    `;

    try {
        const res = await fetch('/api/scans');
        scansData = await res.json();
        renderStats(scansData);
        renderSearchBar();
        renderScanCards(scansData);
    } catch (err) {
        document.getElementById('scans-grid').innerHTML = `
            <div class="empty-state" style="grid-column:1/-1">
                <img class="empty-state-mascot" src="/static/mascot_shield.png" alt="">
                <h2 class="empty-state-title">Erreur de chargement</h2>
                <p class="empty-state-desc">${err.message}</p>
            </div>`;
    }
}

function renderSearchBar() {
    const grid = document.getElementById('scans-grid');
    const bar = document.createElement('div');
    bar.className = 'search-bar-wrapper';
    bar.innerHTML = `
        <input id="dashboard-search" class="search-bar" type="search" placeholder="Filtrer par URL, domaine…" autocomplete="off" />
        <span class="search-icon">🔍</span>`;
    grid.parentNode.insertBefore(bar, grid);
    document.getElementById('dashboard-search').addEventListener('input', e => {
        const q = e.target.value.toLowerCase().trim();
        const filtered = q
            ? scansData.filter(s => (s.target_url || '').toLowerCase().includes(q) || (s.folder || '').toLowerCase().includes(q))
            : scansData;
        renderScanCards(filtered);
    });
}

function renderStats(scans) {
    const total = scans.length;
    const high = scans.filter(s => s.threat_level === 'high').length;
    const medium = scans.filter(s => s.threat_level === 'medium').length;
    const screenshots = scans.reduce((sum, s) => sum + (s.screenshot_count || 0), 0);
    const avgScore = total ? Math.round(scans.reduce((sum, s) => sum + (s.risk_score || 0), 0) / total) : 0;
    const avgClass = avgScore >= 75 ? 'danger' : avgScore >= 50 ? 'warning' : avgScore >= 25 ? 'accent' : '';

    document.getElementById('stats-bar').innerHTML = `
        <div class="stat-card"><div class="stat-value">${total}</div><div class="stat-label">Scans totaux</div></div>
        <div class="stat-card"><div class="stat-value danger">${high}</div><div class="stat-label">Menaces élevées</div></div>
        <div class="stat-card"><div class="stat-value warning">${medium}</div><div class="stat-label">Menaces moyennes</div></div>
        <div class="stat-card"><div class="stat-value accent">${screenshots}</div><div class="stat-label">Captures</div></div>
        <div class="stat-card"><div class="stat-value ${avgClass}">${avgScore}</div><div class="stat-label">Score moyen /100</div></div>
    `;
}

function buildScanCard(scan) {
    const date = scan.date ? formatDate(scan.date) : '—';
    const domain = extractDomain(scan.target_url || scan.folder);
    const fullUrl = scan.target_url || scan.folder;
    const score = scan.risk_score ?? null;
    const level = scan.risk_level || scan.threat_level || 'unknown';

    // Risk bar
    let riskBar = '';
    if (score !== null) {
        const color = score >= 75 ? 'var(--red)' : score >= 50 ? 'var(--orange)' : score >= 25 ? 'var(--gold)' : 'var(--green)';
        riskBar = `
        <div class="risk-score-row">
            <div class="risk-bar-track"><div class="risk-bar-fill" style="width:${score}%;background:${color}"></div></div>
            <span class="risk-score-value" style="color:${color}">${score}/100</span>
        </div>`;
    }

    // TI badges
    let tiBadges = '';
    const ti = scan.ti_summary;
    if (ti) {
        if (ti.is_very_young) {
            tiBadges += `<span class="ti-badge danger" title="Domaine très récent (${ti.domain_age_days}j)">⚡ ${ti.domain_age_days}j</span>`;
        } else if (ti.domain_age_days !== null && ti.domain_age_days !== undefined && ti.domain_age_days < 30) {
            tiBadges += `<span class="ti-badge warning" title="Domaine récent">${ti.domain_age_days}j</span>`;
        }
        if (ti.vt_malicious !== null && ti.vt_malicious !== undefined) {
            if (ti.vt_malicious > 0) {
                tiBadges += `<span class="ti-badge danger" title="VirusTotal">🦠 ${ti.vt_malicious}/${ti.vt_total}</span>`;
            } else {
                tiBadges += `<span class="ti-badge ok" title="VirusTotal propre">✅ VT</span>`;
            }
        }
        if (ti.ssl_valid === false || ti.ssl_self_signed) {
            tiBadges += `<span class="ti-badge danger" title="SSL invalide">🔴 SSL</span>`;
        } else if (ti.ssl_valid) {
            tiBadges += `<span class="ti-badge ok" title="SSL valide">🔒</span>`;
        }
    }

    const badgeLevel = level === 'critical' ? 'critical' : level;

    return `
    <div class="scan-card" onclick="navigate('#report/${scan.folder}')">
        <div class="scan-card-header">
            <div>
                <div class="scan-card-domain">${escapeHtml(domain)}</div>
                <div class="scan-card-url" title="${escapeHtml(fullUrl)}">${escapeHtml(fullUrl)}</div>
            </div>
            <span class="threat-badge ${badgeLevel}">${threatLabel(level)}</span>
        </div>
        ${riskBar}
        <div class="scan-card-meta">
            <span class="scan-meta-item">${date}</span>
            <span class="scan-meta-item">&middot;</span>
            <span class="scan-meta-item">${(scan.regions || []).join(', ') || '—'}</span>
            <span class="scan-meta-item">&middot;</span>
            <span class="scan-meta-item">${scan.screenshot_count} captures</span>
        </div>
        ${tiBadges ? `<div class="ti-badges-row">${tiBadges}</div>` : ''}
        <div class="scan-card-footer">
            <span class="scan-status-tag ${scan.has_report ? 'available' : ''}">${scan.has_report ? 'Rapport disponible' : 'Pas de rapport'}</span>
            <div onclick="event.stopPropagation()">
                <button class="btn-icon danger" onclick="deleteScan('${scan.folder}')" title="Supprimer">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
                </button>
            </div>
        </div>
    </div>`;
}

function renderScanCards(scans) {
    const grid = document.getElementById('scans-grid');

    if (!scans.length) {
        grid.innerHTML = `
            <div class="empty-state" style="grid-column:1/-1">
                <img class="empty-state-mascot" src="/static/mascot_hacker.png" alt="">
                <h2 class="empty-state-title">Aucun scan disponible</h2>
                <p class="empty-state-desc">Lancez votre premier scan pour commencer l'analyse</p>
                <button class="btn btn-primary" onclick="navigate('#scan')">Nouveau scan</button>
            </div>`;
        return;
    }

    grid.innerHTML = scans.map(buildScanCard).join('');
}

// ── Report ──
async function showReport(folder) {
    const container = document.getElementById('view-report');
    container.classList.remove('hidden');
    container.innerHTML = `
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:1.5rem;">
            <button class="btn btn-back" onclick="navigate('#dashboard')">← Retour</button>
            <h1 class="page-title" style="margin:0;font-size:1.1rem">${escapeHtml(folder)}</h1>
        </div>
        <div class="report-container">
            <div class="report-sidebar skeleton" style="min-height:300px"></div>
            <div class="report-main skeleton" style="min-height:500px"></div>
        </div>`;

    try {
        const res = await fetch(`/api/scans/${encodeURIComponent(folder)}`);
        if (!res.ok) throw new Error('Scan introuvable');
        renderReport(folder, await res.json());
    } catch (err) {
        container.innerHTML = `
            <button class="btn btn-back" onclick="navigate('#dashboard')">← Retour</button>
            <div class="empty-state">
                <img class="empty-state-mascot" src="/static/mascot_shield.png" alt="">
                <h2 class="empty-state-title">Erreur</h2>
                <p class="empty-state-desc">${err.message}</p>
            </div>`;
    }
}

function renderReport(folder, data) {
    const container = document.getElementById('view-report');
    const reportHtml = data.report_md ? renderMarkdown(data.report_md, folder) : '<p style="color:var(--text-muted)">Aucun rapport disponible.</p>';

    let sidebarScreenshots = '';
    if (data.screenshots && data.screenshots.length) {
        sidebarScreenshots = data.screenshots.map(s => `
            <img class="screenshot-thumb"
                 src="/api/scans/${encodeURIComponent(folder)}/files/${encodeURIComponent(s)}"
                 alt="${s}" onclick="openLightbox(this.src)" loading="lazy" />
        `).join('');
    }

    let sidebarDumps = '';
    if (data.dump_files && data.dump_files.length) {
        sidebarDumps = data.dump_files.map(f => `
            <div class="sidebar-nav-item"
                 onclick="window.open('/api/scans/${encodeURIComponent(folder)}/files/dump/${encodeURIComponent(f)}', '_blank')"
                 title="${escapeHtml(f)}">${escapeHtml(f)}</div>
        `).join('');
    }

    let riskPanel = '';
    let infoPanel = '';
    let tiPanel = '';

    if (data.consolidated_data) {
        const cd = data.consolidated_data;
        const r = cd.regions && cd.regions[0];

        // ── Risk Score panel ──
        const risk = cd.risk_score;
        if (risk) {
            const score = risk.score || 0;
            const level = risk.level || 'unknown';
            const color = level === 'critical' ? 'var(--red)' : level === 'high' ? 'var(--orange)' : level === 'medium' ? 'var(--gold)' : 'var(--green)';
            const badgeLevel = level === 'critical' ? 'critical' : level;
            const factors = (risk.factors || []).slice(0, 6);
            riskPanel = `
                <div class="sidebar-section">
                    <div class="sidebar-section-title">Score de risque</div>
                    <div class="risk-gauge-container">
                        <div class="risk-bar-track" style="margin-bottom:8px">
                            <div class="risk-bar-fill" style="width:${score}%;background:${color}"></div>
                        </div>
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                            <span class="risk-gauge-score" style="color:${color}">${score}<span class="risk-gauge-max">/100</span></span>
                            <span class="threat-badge ${badgeLevel}">${threatLabel(level)}</span>
                        </div>
                    </div>
                    ${factors.length ? `<ul class="risk-factors-list">${factors.map(f => `<li class="risk-factor-item">${escapeHtml(f)}</li>`).join('')}</ul>` : ''}
                </div>`;
        }

        // ── Threat Intel panel ──
        const ti = cd.threat_intel;
        if (ti) {
            let tiRows = '';
            const vt = ti.virustotal || {};
            if (vt.skipped) {
                tiRows += `<div class="ti-row"><span class="ti-key">VirusTotal</span><span class="ti-val muted">Non configuré</span></div>`;
            } else if (vt.error) {
                tiRows += `<div class="ti-row"><span class="ti-key">VirusTotal</span><span class="ti-val danger">Erreur</span></div>`;
            } else if (vt.malicious !== undefined) {
                const vtClass = vt.malicious > 0 ? 'danger' : 'ok';
                tiRows += `<div class="ti-row"><span class="ti-key">VirusTotal</span><span class="ti-val ${vtClass}">${vt.malicious} / ${vt.total}</span></div>`;
                if (vt.permalink) tiRows += `<div class="ti-row"><span class="ti-key"></span><a class="ti-link" href="${escapeHtml(vt.permalink)}" target="_blank">Voir rapport VT →</a></div>`;
            }

            const whois = ti.whois || {};
            if (!whois.error) {
                const age = whois.age_days;
                const ageStr = (age !== null && age !== undefined) ? `${age} jours` : 'Inconnu';
                const ageClass = whois.is_very_young ? 'danger' : (whois.is_young ? 'warning' : 'ok');
                tiRows += `<div class="ti-separator"></div>`;
                tiRows += `<div class="ti-row"><span class="ti-key">Âge domaine</span><span class="ti-val ${ageClass}">${ageStr}</span></div>`;
                if (whois.registrar) tiRows += `<div class="ti-row"><span class="ti-key">Registrar</span><span class="ti-val">${escapeHtml(whois.registrar)}</span></div>`;
                if (whois.registration_date) tiRows += `<div class="ti-row"><span class="ti-key">Enregistré</span><span class="ti-val">${whois.registration_date.slice(0, 10)}</span></div>`;
            }

            const ssl = ti.ssl || {};
            if (ssl.issuer !== undefined || ssl.valid !== undefined) {
                const sslClass = ssl.valid ? 'ok' : 'danger';
                const sslLabel = ssl.valid ? '✅ Valide' : (ssl.is_expired ? '❌ Expiré' : '⚠️ Invalide');
                tiRows += `<div class="ti-separator"></div>`;
                tiRows += `<div class="ti-row"><span class="ti-key">SSL</span><span class="ti-val ${sslClass}">${sslLabel}</span></div>`;
                if (ssl.issuer) tiRows += `<div class="ti-row"><span class="ti-key">Émetteur</span><span class="ti-val">${escapeHtml(ssl.issuer)}</span></div>`;
                if (ssl.is_self_signed) tiRows += `<div class="ti-row"><span class="ti-key">Auto-signé</span><span class="ti-val danger">Oui ⚠️</span></div>`;
                if (ssl.days_left !== null && ssl.days_left !== undefined) tiRows += `<div class="ti-row"><span class="ti-key">Jours restants</span><span class="ti-val">${ssl.days_left}</span></div>`;
            }

            if (tiRows) {
                tiPanel = `
                    <div class="sidebar-section">
                        <div class="sidebar-section-title">Threat Intelligence</div>
                        <div class="ti-panel">${tiRows}</div>
                    </div>`;
            }
        }

        // ── Info panel ──
        if (r) {
            infoPanel = `
                <div class="sidebar-section">
                    <div class="sidebar-section-title">Informations</div>
                    <div class="sidebar-info-item"><span>Cible</span><span class="sidebar-info-value">${extractDomain(cd.target_url || '')}</span></div>
                    <div class="sidebar-info-item"><span>Région</span><span class="sidebar-info-value">${r.region}</span></div>
                    <div class="sidebar-info-item"><span>Redirections</span><span class="sidebar-info-value">${(r.redirect_chain || []).length}</span></div>
                    <div class="sidebar-info-item"><span>Inputs</span><span class="sidebar-info-value">${(r.inputs || []).length}</span></div>
                    <div class="sidebar-info-item"><span>Artifacts</span><span class="sidebar-info-value">${(r.files_extracted || []).length}</span></div>
                </div>`;
        }
    }

    container.innerHTML = `
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:1.5rem;flex-wrap:wrap;">
            <button class="btn btn-back" onclick="navigate('#dashboard')">← Retour</button>
            <h1 class="page-title" style="margin:0;font-size:1.1rem;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(folder)}</h1>
            <div style="display:flex;gap:8px;flex-shrink:0;">
                ${data.consolidated_data ? `<a class="btn btn-secondary" href="/api/scans/${encodeURIComponent(folder)}/download/json" download title="Télécharger les données brutes JSON">⬇ JSON</a>` : ''}
                ${data.report_md ? `<a class="btn btn-secondary" href="/api/scans/${encodeURIComponent(folder)}/download/report" download title="Télécharger le rapport Markdown">⬇ Rapport</a>` : ''}
            </div>
        </div>
        <div class="report-tabs" style="display:flex;gap:4px;margin-bottom:1.5rem;border-bottom:2px solid var(--border);padding-bottom:0;">
            <button class="report-tab active" id="tab-btn-report" onclick="switchReportTab('report')" style="padding:8px 18px;border:none;background:none;cursor:pointer;font-weight:600;font-size:0.85rem;color:var(--gold);border-bottom:2px solid var(--gold);margin-bottom:-2px;">📄 Rapport</button>
            <button class="report-tab" id="tab-btn-timeline" onclick="switchReportTab('timeline')" style="padding:8px 18px;border:none;background:none;cursor:pointer;font-size:0.85rem;color:var(--text-muted);border-bottom:2px solid transparent;margin-bottom:-2px;">🎬 Timeline</button>
        </div>
        <div id="tab-content-report" class="report-container">
            <div class="report-sidebar">
                ${riskPanel}
                ${tiPanel}
                ${infoPanel}
                ${sidebarScreenshots ? `<div class="sidebar-section"><div class="sidebar-section-title">Captures (${data.screenshots.length})</div>${sidebarScreenshots}</div>` : ''}
                ${sidebarDumps ? `<div class="sidebar-section"><div class="sidebar-section-title">Fichiers extraits</div>${sidebarDumps}</div>` : ''}
            </div>
            <div class="report-main">
                <div class="report-content">${reportHtml}</div>
            </div>
        </div>
        <div id="tab-content-timeline" class="hidden">
            ${buildTimeline(folder, data)}
        </div>`;

    document.querySelectorAll('.report-content pre code').forEach(block => {
        if (window.hljs) hljs.highlightElement(block);
    });

    document.querySelectorAll('.report-content img').forEach(img => {
        img.addEventListener('click', () => openLightbox(img.src));
    });
}

function switchReportTab(tab) {
    document.getElementById('tab-content-report').classList.toggle('hidden', tab !== 'report');
    document.getElementById('tab-content-timeline').classList.toggle('hidden', tab !== 'timeline');
    document.querySelectorAll('.report-tab').forEach(btn => {
        const isActive = btn.id === `tab-btn-${tab}`;
        btn.style.color = isActive ? 'var(--gold)' : 'var(--text-muted)';
        btn.style.fontWeight = isActive ? '600' : '400';
        btn.style.borderBottomColor = isActive ? 'var(--gold)' : 'transparent';
    });
}

function buildTimeline(folder, data) {
    const cd = data.consolidated_data;
    if (!cd) return '<p style="color:var(--text-muted);padding:2rem;">Aucune donnée de journey disponible.</p>';
    const regions = cd.regions || [];
    if (!regions.length || !regions[0].interaction_journey || !regions[0].interaction_journey.length) {
        return '<p style="color:var(--text-muted);padding:2rem;">Aucune étape d\'interaction enregistrée.</p>';
    }
    const journey = regions[0].interaction_journey;
    const steps = journey.map((step, i) => {
        const isFirst = i === 0;
        const isLast = i === journey.length - 1;
        const screenshotFile = step.screenshot_path ? step.screenshot_path.split(/[\\/]/).pop() : null;
        const imgHtml = screenshotFile
            ? `<img src="/api/scans/${encodeURIComponent(folder)}/files/${encodeURIComponent(screenshotFile)}" 
               class="timeline-screenshot" onclick="openLightbox(this.src)" loading="lazy"
               style="width:100%;max-width:340px;border-radius:8px;border:1px solid var(--border);cursor:zoom-in;transition:transform 0.2s;"
               onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'" />`
            : '<div style="width:340px;height:120px;background:var(--bg-elevated);border-radius:8px;display:flex;align-items:center;justify-content:center;color:var(--text-muted);font-size:0.8rem;">Capture indisponible</div>';
        const stepDesc = step.description || 'Action';
        const stepColor = stepDesc.toLowerCase().includes('captcha') ? 'var(--orange)'
            : stepDesc.toLowerCase().includes('payment') || stepDesc.toLowerCase().includes('paiement') ? 'var(--red)'
            : stepDesc.toLowerCase().includes('suspicious') ? 'var(--orange)'
            : isFirst ? 'var(--gold)' : isLast ? 'var(--green)' : 'var(--text-muted)';
        return `
        <div style="display:flex;gap:1.5rem;margin-bottom:2rem;align-items:flex-start;">
            <!-- connector -->
            <div style="display:flex;flex-direction:column;align-items:center;flex-shrink:0;">
                <div style="width:32px;height:32px;border-radius:50%;background:var(--bg-elevated);border:2px solid ${stepColor};display:flex;align-items:center;justify-content:center;font-size:0.7rem;font-weight:700;color:${stepColor}">${i + 1}</div>
                ${!isLast ? '<div style="width:2px;flex:1;background:var(--border);margin-top:4px;min-height:60px;"></div>' : ''}
            </div>
            <!-- content -->
            <div style="flex:1;min-width:0;">
                <div style="font-size:0.82rem;font-weight:600;color:${stepColor};margin-bottom:4px;">${escapeHtml(stepDesc)}</div>
                <div style="font-size:0.72rem;color:var(--text-muted);font-family:'JetBrains Mono',monospace;margin-bottom:8px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${escapeHtml(step.url || '—')}</div>
                ${imgHtml}
            </div>
        </div>`;
    }).join('');
    return `<div style="padding:1rem 0.5rem;max-width:900px;">${steps}</div>`;
}

function renderMarkdown(md, folder) {
    let processed = md.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (match, alt, src) => {
        if (src.startsWith('http') || src.startsWith('/api/')) return match;
        return `![${alt}](/api/scans/${encodeURIComponent(folder)}/files/${encodeURIComponent(src.replace(/^\.\//, ''))})`;
    });

    if (window.marked) {
        marked.setOptions({
            breaks: true, gfm: true,
            highlight: function (code, lang) {
                if (window.hljs && lang && hljs.getLanguage(lang)) return hljs.highlight(code, { language: lang }).value;
                return code;
            }
        });
        return marked.parse(processed);
    }

    return processed
        .replace(/^### (.*$)/gm, '<h3>$1</h3>')
        .replace(/^## (.*$)/gm, '<h2>$1</h2>')
        .replace(/^# (.*$)/gm, '<h1>$1</h1>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/^> (.*$)/gm, '<blockquote>$1</blockquote>')
        .replace(/^---$/gm, '<hr>')
        .replace(/\n/g, '<br>');
}

// ── Scan Form ──
async function showScanForm() {
    const container = document.getElementById('view-scan');
    container.classList.remove('hidden');
    container.innerHTML = `
        <div class="scan-form-container view">
            <div class="page-header">
                <img class="page-header-mascot" src="/static/mascot_hacker.png" alt="">
                <div>
                    <h1 class="page-title">Nouveau scan</h1>
                    <p class="page-description">Analysez une URL suspecte via Docker</p>
                </div>
            </div>
            <div id="preflight-panel" class="form-card" style="margin-bottom:1rem;"></div>
            <div class="form-card">
                <div class="form-group">
                    <label class="form-label">URL cible</label>
                    <input type="url" id="scan-url" class="form-input" placeholder="https://..." autocomplete="off" />
                    <p class="form-hint">L'URL du site suspect à scanner</p>
                </div>
                <div class="form-group">
                    <label class="form-label">Régions</label>
                    <div class="region-grid">
                        <button class="region-chip selected" data-region="FR" onclick="toggleRegion(this)">France</button>
                        <button class="region-chip" data-region="US" onclick="toggleRegion(this)">USA</button>
                        <button class="region-chip" data-region="DE" onclick="toggleRegion(this)">Allemagne</button>
                        <button class="region-chip" data-region="JP" onclick="toggleRegion(this)">Japon</button>
                    </div>
                    <p class="form-hint">Simuler l'accès depuis ces régions</p>
                </div>
                <div class="form-group">
                    <label class="form-label">VirusTotal</label>
                    <div id="vt-status-panel" class="vt-status-panel">
                        <div style="font-size:0.8rem;color:var(--text-muted)"><span class="spinner" style="margin-right:6px"></span>Vérification...</div>
                    </div>
                    <div style="display:flex;align-items:center;gap:10px;margin-top:10px;">
                        <input type="checkbox" id="scan-use-vt" style="width:18px;height:18px;accent-color:var(--gold);" checked />
                        <label for="scan-use-vt" style="font-size:0.82rem;color:var(--text-secondary);cursor:pointer;">Activer l'analyse VirusTotal</label>
                    </div>
                </div>
                <div class="form-group" style="display:flex;align-items:center;gap:10px;">
                    <input type="checkbox" id="scan-visible" style="width:18px;height:18px;accent-color:var(--gold);" />
                    <label for="scan-visible" style="font-size:0.82rem;color:var(--text-secondary);cursor:pointer;">Mode visible (navigateur affiché via VNC)</label>
                </div>
                <div class="form-group">
                    <label class="form-label">Modèle LLM</label>
                    <select id="scan-model" class="form-input" style="cursor:pointer;">
                        <option value="mistral" selected>mistral (défaut — texte)</option>
                        <option value="llama3">llama3 (meilleure compréhension FR)</option>
                        <option value="llava">llava (vision — plus lent)</option>
                        <option value="phi3">phi3 (léger et rapide)</option>
                        <option value="gemma2">gemma2</option>
                    </select>
                    <p class="form-hint">Modèle Ollama utilisé pour l'analyse forensique</p>
                </div>
                <button class="btn btn-primary" id="btn-launch" onclick="launchScan()" style="width:100%">Lancer l'analyse</button>
            </div>
            <div id="scan-status-area"></div>
        </div>`;

    // Reset incremental terminal state for fresh view
    _scanCardBuilt = false;
    _scanOutputOffset = 0;
    runPreflight();
    loadVtStatus();
    checkScanStatus();
}

async function runPreflight() {
    const panel = document.getElementById('preflight-panel');
    if (!panel) return;
    panel.innerHTML = '<div style="padding:0.5rem 0;font-size:0.8rem;color:var(--text-muted)"><span class="spinner" style="margin-right:8px"></span>Vérification de l\'environnement...</div>';

    try {
        const res = await fetch('/api/preflight');
        const checks = await res.json();

        const items = [
            { label: 'Docker', ok: checks.docker, hint: 'Docker Desktop doit être lancé' },
            { label: 'Ollama', ok: checks.ollama, hint: 'Ollama doit tourner sur le port 11434' },
            { label: 'Image Docker', ok: checks.image_built, hint: 'Exécutez docker compose build' },
        ];

        const models = checks.ollama_models || [];
        const modelsHtml = models.length
            ? `<div style="margin-top:6px;display:flex;flex-wrap:wrap;gap:4px;">
                ${models.map(m => `<span style="font-size:0.68rem;padding:2px 8px;border-radius:99px;background:var(--bg-elevated);color:var(--text-secondary);border:1px solid var(--border);">${escapeHtml(m)}</span>`).join('')}
               </div>`
            : (checks.ollama ? '<div style="font-size:0.7rem;color:var(--text-muted);margin-top:4px;">Aucun modèle installé — <code>ollama pull mistral</code></div>' : '');

        panel.innerHTML = `
            <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:var(--gold);margin-bottom:0.5rem;">Environnement</div>
            ${items.map(i => `
                <div style="display:flex;align-items:center;gap:8px;padding:4px 0;font-size:0.8rem;">
                    <span style="width:8px;height:8px;border-radius:50%;background:${i.ok ? 'var(--green)' : 'var(--red)'};flex-shrink:0;"></span>
                    <span style="color:${i.ok ? 'var(--text)' : 'var(--red)'};">${i.label}</span>
                    ${!i.ok ? `<span style="margin-left:auto;font-size:0.7rem;color:var(--text-muted)">${i.hint}</span>` : ''}
                </div>
            `).join('')}
            ${checks.ollama ? `<div style="font-size:0.72rem;color:var(--text-muted);margin-top:2px;padding-left:16px;">Modèles disponibles${modelsHtml}</div>` : ''}
        `;

        // Populate model select with detected models (keep defaults if empty)
        if (models.length) {
            const sel = document.getElementById('scan-model');
            if (sel) {
                sel.innerHTML = models.map(m =>
                    `<option value="${escapeHtml(m)}" ${m.startsWith('mistral') ? 'selected' : ''}>${escapeHtml(m)}</option>`
                ).join('');
            }
        }

        const btn = document.getElementById('btn-launch');
        if (!checks.docker) {
            btn.disabled = true;
            btn.style.opacity = '0.5';
            btn.title = 'Docker est requis pour lancer un scan';
        }
    } catch (err) {
        panel.innerHTML = '<div style="font-size:0.8rem;color:var(--text-muted)">Impossible de vérifier l\'environnement</div>';
    }
}

async function loadVtStatus() {
    const panel = document.getElementById('vt-status-panel');
    if (!panel) return;
    try {
        const res = await fetch('/api/vt-status');
        const vt = await res.json();

        if (vt.configured) {
            panel.innerHTML = `
                <div class="vt-status-row">
                    <span class="vt-dot ok"></span>
                    <span class="vt-plan">${vt.plan}</span>
                    <span class="vt-key-masked">${vt.key_masked}</span>
                </div>
                <div class="vt-quota-grid">
                    <div class="vt-quota-item">
                        <div class="vt-quota-val">${vt.quota.rate}</div>
                        <div class="vt-quota-lbl">Requêtes</div>
                    </div>
                    <div class="vt-quota-item">
                        <div class="vt-quota-val">${vt.quota.daily}</div>
                        <div class="vt-quota-lbl">Par jour</div>
                    </div>
                    <div class="vt-quota-item">
                        <div class="vt-quota-val">${vt.quota.monthly}</div>
                        <div class="vt-quota-lbl">Par mois</div>
                    </div>
                </div>
                <div class="vt-usage-note">${vt.usage_note}</div>`;
        } else {
            panel.innerHTML = `
                <div class="vt-status-row">
                    <span class="vt-dot off"></span>
                    <span style="font-size:0.8rem;color:var(--text-muted)">Clé API non configurée</span>
                </div>
                <div class="vt-usage-note">Définir <code>VT_API_KEY</code> dans le fichier <code>.env</code> pour activer.
                    <a class="ti-link" href="${vt.upgrade_url}" target="_blank">Obtenir une clé →</a>
                </div>`;
            // Auto-disable the checkbox if not configured
            const cb = document.getElementById('scan-use-vt');
            if (cb) { cb.checked = false; cb.disabled = true; }
        }
    } catch (err) {
        if (panel) panel.innerHTML = '<div style="font-size:0.8rem;color:var(--text-muted)">Impossible de vérifier le statut VT</div>';
    }
}

function toggleRegion(chip) { chip.classList.toggle('selected'); }

function getSelectedRegions() {
    return Array.from(document.querySelectorAll('.region-chip.selected')).map(c => c.dataset.region).join(',');
}

async function launchScan() {
    const url = document.getElementById('scan-url').value.trim();
    if (!url) { document.getElementById('scan-url').focus(); showToast('URL requise', 'error'); return; }
    const regions = getSelectedRegions();
    if (!regions) { showToast('Sélectionnez une région', 'error'); return; }
    const visible = document.getElementById('scan-visible').checked;
    const use_vt = document.getElementById('scan-use-vt')?.checked ?? true;

    const btn = document.getElementById('btn-launch');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Lancement...';
    const model = document.getElementById('scan-model')?.value || 'mistral';

    try {
        const res = await fetch('/api/scan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url, regions, visible, use_vt, model }) });
        const data = await res.json();
        if (res.ok) { showToast('Scan lancé', 'success'); startScanPolling(); }
        else { showToast(data.error || 'Erreur', 'error'); btn.disabled = false; btn.textContent = 'Lancer l\'analyse'; }
    } catch (err) { showToast('Erreur réseau', 'error'); btn.disabled = false; btn.textContent = 'Lancer l\'analyse'; }
}

function startScanPolling() {
    if (scanPollingInterval) clearInterval(scanPollingInterval);
    _scanOutputOffset = 0;
    _scanCardBuilt = false;
    scanPollingInterval = setInterval(checkScanStatus, 2000);
    checkScanStatus();
}

async function checkScanStatus() {
    try {
        const url = `/api/scan/status?offset=${_scanOutputOffset}`;
        const res = await fetch(url);
        const data = await res.json();
        renderScanStatus(data);
        if (!data.running && scanPollingInterval) {
            clearInterval(scanPollingInterval); scanPollingInterval = null;
            const btn = document.getElementById('btn-launch');
            if (btn) { btn.disabled = false; btn.textContent = 'Lancer l\'analyse'; }
            if (data.return_code === 0) showToast('Scan terminé', 'success');
            else if (data.return_code !== null) showToast('Scan terminé avec erreurs', 'error');
        }
    } catch (err) { }
}

async function stopScan() {
    try {
        await fetch('/api/scan/stop', { method: 'POST' });
        showToast('Arrêt demandé', 'success');
    } catch (err) { showToast('Erreur', 'error'); }
}

function renderScanStatus(data) {
    const area = document.getElementById('scan-status-area');
    if (!area) return;

    // Clear area if no scan has ever run
    if (!data.url && !data.output) { area.innerHTML = ''; _scanCardBuilt = false; return; }

    const running = data.running;

    // Build the card shell once — avoid full re-renders which cause flicker
    if (!_scanCardBuilt) {
        area.innerHTML = `
            <div class="form-card" style="margin-top:1.5rem;">
                <div class="terminal-header" id="term-header">
                    <div class="terminal-dot" id="term-dot"></div>
                    <span id="term-status-label"></span>
                    <span id="term-domain" style="margin-left:auto;font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:var(--text-muted)"></span>
                </div>
                <div class="terminal-output" id="term-output"></div>
                <div id="term-actions" style="display:flex;gap:0.5rem;margin-top:1rem;"></div>
            </div>`;
        _scanCardBuilt = true;
        _scanOutputOffset = 0;
    }

    // Update status label + dot
    const dot = document.getElementById('term-dot');
    const label = document.getElementById('term-status-label');
    const domainEl = document.getElementById('term-domain');
    if (dot) dot.className = `terminal-dot${running ? '' : ' stopped'}`;
    if (label) label.textContent = running ? 'En cours...' : (data.return_code === 0 ? 'Terminé ✅' : 'Erreur ❌');
    if (domainEl && data.url) domainEl.textContent = extractDomain(data.url);

    // Append only new output (incremental — no flicker)
    const termEl = document.getElementById('term-output');
    if (termEl && data.output) {
        const newText = data.output; // new chars since last offset
        if (newText.length > 0) {
            const span = document.createElement('span');
            span.innerHTML = colorizeTerminal(newText);
            termEl.appendChild(span);
            termEl.scrollTop = termEl.scrollHeight;
            _scanOutputOffset += newText.length;
        }
    }

    // Update action buttons only when state changes
    const actionsEl = document.getElementById('term-actions');
    if (actionsEl) {
        const newActions = [
            running ? '<button class="btn btn-secondary" onclick="stopScan()" style="flex:1;">Arrêter le scan</button>' : '',
            (running && data.visible) ? '<button class="btn btn-secondary" onclick="window.open(\'http://localhost:6080/vnc_lite.html\', \'_blank\')" style="flex:1; border-color: var(--gold); color: var(--gold);">👀 Voir le Navigateur (VNC)</button>' : '',
            !running && data.return_code === 0 ? '<button class="btn btn-primary" style="flex:1;" onclick="navigate(\'#dashboard\')">Voir les résultats</button>' : '',
            !running && data.return_code !== null && data.return_code !== 0 ? '<button class="btn btn-primary" style="flex:1;" onclick="launchScan()">Relancer</button>' : '',
        ].join('');
        if (actionsEl.innerHTML !== newActions) actionsEl.innerHTML = newActions;
    }

    const btn = document.getElementById('btn-launch');
    if (btn && running) { btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Scan en cours...'; }
}

async function deleteScan(folder) {
    if (!confirm(`Supprimer le scan « ${folder} » ?`)) return;
    try {
        const res = await fetch(`/api/scans/${encodeURIComponent(folder)}`, { method: 'DELETE' });
        if (res.ok) { showToast('Supprimé', 'success'); showDashboard(); }
        else { showToast((await res.json()).error || 'Erreur', 'error'); }
    } catch (err) { showToast('Erreur', 'error'); }
}

function openLightbox(src) { document.getElementById('lightbox-img').src = src; document.getElementById('lightbox').classList.add('active'); }
function closeLightbox() { document.getElementById('lightbox').classList.remove('active'); }

function showToast(msg, type = 'info') {
    const c = document.getElementById('toast-container');
    const t = document.createElement('div');
    t.className = `toast ${type}`;
    t.textContent = msg;
    c.appendChild(t);
    setTimeout(() => { t.style.opacity = '0'; setTimeout(() => t.remove(), 300); }, 3500);
}

function formatDate(s) {
    try { const d = new Date(s); return isNaN(d) ? s : d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }); } catch { return s; }
}

function extractDomain(url) {
    try { return url.startsWith('http') ? new URL(url).hostname : url; } catch { return url; }
}

function threatLabel(l) {
    return { critical: 'Critique', high: 'Élevé', medium: 'Moyen', low: 'Faible', unknown: 'Inconnu' }[l] || 'Inconnu';
}

function escapeHtml(s) { return s ? s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;') : ''; }

function colorizeTerminal(text) {
    return text.split('\n').map(line => {
        const escaped = escapeHtml(line);
        const lower = line.toLowerCase();
        if (lower.includes('[erreur]') || lower.includes('error') || lower.includes('traceback') || lower.includes('exception')) {
            return `<span class="term-line-error">${escaped}</span>`;
        }
        if (lower.includes('warning') || lower.includes('[warn]') || lower.includes('attention')) {
            return `<span class="term-line-warn">${escaped}</span>`;
        }
        if (lower.includes('[gui]') || lower.includes('✅') || lower.includes('success')) {
            return `<span class="term-line-ok">${escaped}</span>`;
        }
        if (lower.includes('🤖') || lower.includes('🛡️') || lower.includes('⚡') || lower.includes('[threatintel]')) {
            return `<span class="term-line-accent">${escaped}</span>`;
        }
        return escaped;
    }).join('\n');
}

window.addEventListener('hashchange', handleRoute);
window.addEventListener('DOMContentLoaded', () => {
    handleRoute();
    document.getElementById('lightbox').addEventListener('click', e => { if (e.target.id === 'lightbox') closeLightbox(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeLightbox(); });
});
