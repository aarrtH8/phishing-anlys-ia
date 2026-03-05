/**
 * PhishHunter GUI — Frontend SPA
 * Elegant white & gold theme with mascots
 */

let scansData = [];
let scanPollingInterval = null;

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
            ${[1, 2, 3, 4].map(() => '<div class="stat-card skeleton" style="height:72px"></div>').join('')}
        </div>
        <div class="scans-grid" id="scans-grid">
            ${[1, 2, 3, 4].map(() => '<div class="scan-card skeleton" style="height:160px"></div>').join('')}
        </div>
    `;

    try {
        const res = await fetch('/api/scans');
        scansData = await res.json();
        renderStats(scansData);
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

function renderStats(scans) {
    const total = scans.length;
    const high = scans.filter(s => s.threat_level === 'high').length;
    const medium = scans.filter(s => s.threat_level === 'medium').length;
    const screenshots = scans.reduce((sum, s) => sum + (s.screenshot_count || 0), 0);

    document.getElementById('stats-bar').innerHTML = `
        <div class="stat-card"><div class="stat-value">${total}</div><div class="stat-label">Scans totaux</div></div>
        <div class="stat-card"><div class="stat-value danger">${high}</div><div class="stat-label">Menaces élevées</div></div>
        <div class="stat-card"><div class="stat-value warning">${medium}</div><div class="stat-label">Menaces moyennes</div></div>
        <div class="stat-card"><div class="stat-value accent">${screenshots}</div><div class="stat-label">Captures</div></div>
    `;
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

    grid.innerHTML = scans.map(scan => {
        const date = scan.date ? formatDate(scan.date) : '—';
        const domain = extractDomain(scan.target_url || scan.folder);
        const fullUrl = scan.target_url || scan.folder;
        return `
        <div class="scan-card" onclick="navigate('#report/${scan.folder}')">
            <div class="scan-card-header">
                <div>
                    <div class="scan-card-domain">${escapeHtml(domain)}</div>
                    <div class="scan-card-url" title="${escapeHtml(fullUrl)}">${escapeHtml(fullUrl)}</div>
                </div>
                <span class="threat-badge ${scan.threat_level}">${threatLabel(scan.threat_level)}</span>
            </div>
            <div class="scan-card-meta">
                <span class="scan-meta-item">${date}</span>
                <span class="scan-meta-item">&middot;</span>
                <span class="scan-meta-item">${(scan.regions || []).join(', ') || '—'}</span>
                <span class="scan-meta-item">&middot;</span>
                <span class="scan-meta-item">${scan.screenshot_count} captures</span>
            </div>
            <div class="scan-card-footer">
                <span class="scan-status-tag ${scan.has_report ? 'available' : ''}">${scan.has_report ? 'Rapport disponible' : 'Pas de rapport'}</span>
                <div onclick="event.stopPropagation()">
                    <button class="btn-icon danger" onclick="deleteScan('${scan.folder}')" title="Supprimer">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
                    </button>
                </div>
            </div>
        </div>`;
    }).join('');
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

    let infoPanel = '';
    if (data.consolidated_data) {
        const cd = data.consolidated_data;
        const r = cd.regions && cd.regions[0];
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
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:1.5rem;">
            <button class="btn btn-back" onclick="navigate('#dashboard')">← Retour</button>
            <h1 class="page-title" style="margin:0;font-size:1.1rem">${escapeHtml(folder)}</h1>
        </div>
        <div class="report-container">
            <div class="report-sidebar">
                ${infoPanel}
                ${sidebarScreenshots ? `<div class="sidebar-section"><div class="sidebar-section-title">Captures (${data.screenshots.length})</div>${sidebarScreenshots}</div>` : ''}
                ${sidebarDumps ? `<div class="sidebar-section"><div class="sidebar-section-title">Fichiers extraits</div>${sidebarDumps}</div>` : ''}
            </div>
            <div class="report-main">
                <div class="report-content">${reportHtml}</div>
            </div>
        </div>`;

    document.querySelectorAll('.report-content pre code').forEach(block => {
        if (window.hljs) hljs.highlightElement(block);
    });
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
                <div class="form-group" style="display:flex;align-items:center;gap:10px;">
                    <input type="checkbox" id="scan-visible" style="width:18px;height:18px;accent-color:var(--gold);" />
                    <label for="scan-visible" style="font-size:0.82rem;color:var(--text-secondary);cursor:pointer;">Mode visible (navigateur affiché via VNC)</label>
                </div>
                <button class="btn btn-primary" id="btn-launch" onclick="launchScan()" style="width:100%">Lancer l'analyse</button>
            </div>
            <div id="scan-status-area"></div>
        </div>`;

    // Run preflight check
    runPreflight();
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

        panel.innerHTML = `
            <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:var(--gold);margin-bottom:0.5rem;">Environnement</div>
            ${items.map(i => `
                <div style="display:flex;align-items:center;gap:8px;padding:4px 0;font-size:0.8rem;">
                    <span style="width:8px;height:8px;border-radius:50%;background:${i.ok ? 'var(--green)' : 'var(--red)'};flex-shrink:0;"></span>
                    <span style="color:${i.ok ? 'var(--text)' : 'var(--red)'};">${i.label}</span>
                    ${!i.ok ? `<span style="margin-left:auto;font-size:0.7rem;color:var(--text-muted)">${i.hint}</span>` : ''}
                </div>
            `).join('')}
        `;

        // Disable launch if Docker is not available
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

    const btn = document.getElementById('btn-launch');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Lancement...';

    try {
        const res = await fetch('/api/scan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url, regions, visible }) });
        const data = await res.json();
        if (res.ok) { showToast('Scan lancé', 'success'); startScanPolling(); }
        else { showToast(data.error || 'Erreur', 'error'); btn.disabled = false; btn.textContent = 'Lancer l\'analyse'; }
    } catch (err) { showToast('Erreur réseau', 'error'); btn.disabled = false; btn.textContent = 'Lancer l\'analyse'; }
}

function startScanPolling() {
    if (scanPollingInterval) clearInterval(scanPollingInterval);
    scanPollingInterval = setInterval(checkScanStatus, 2000);
    checkScanStatus();
}

async function checkScanStatus() {
    try {
        const res = await fetch('/api/scan/status');
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
    if (!area || (!data.url && !data.output)) { if (area) area.innerHTML = ''; return; }
    const running = data.running;
    area.innerHTML = `
        <div class="form-card" style="margin-top:1.5rem;">
            <div class="terminal-header">
                <div class="terminal-dot ${running ? '' : 'stopped'}"></div>
                <span>${running ? 'En cours...' : (data.return_code === 0 ? 'Terminé' : 'Erreur')}</span>
                ${data.url ? `<span style="margin-left:auto;font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:var(--text-muted)">${escapeHtml(extractDomain(data.url))}</span>` : ''}
            </div>
            <div class="terminal-output">${escapeHtml(data.output || 'En attente...')}</div>
            <div style="display:flex;gap:0.5rem;margin-top:1rem;">
                ${running ? '<button class="btn btn-secondary" onclick="stopScan()" style="flex:1;">Arrêter le scan</button>' : ''}
                ${running ? '<button class="btn btn-secondary" onclick="window.open(\'http://localhost:6080/vnc.html\', \'_blank\')" style="flex:1; border-color: var(--gold); color: var(--gold);">👀 Voir le Navigateur (VNC)</button>' : ''}
                ${!running && data.return_code === 0 ? '<button class="btn btn-primary" style="flex:1;" onclick="navigate(\'#dashboard\')">Voir les résultats</button>' : ''}
                ${!running && data.return_code !== null && data.return_code !== 0 ? '<button class="btn btn-primary" style="flex:1;" onclick="launchScan()">Relancer</button>' : ''}
            </div>
        </div>`;
    const t = area.querySelector('.terminal-output');
    if (t) t.scrollTop = t.scrollHeight;
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

function threatLabel(l) { return { high: 'Élevé', medium: 'Moyen', low: 'Faible', unknown: 'Inconnu' }[l] || 'Inconnu'; }

function escapeHtml(s) { return s ? s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;') : ''; }

window.addEventListener('hashchange', handleRoute);
window.addEventListener('DOMContentLoaded', () => {
    handleRoute();
    document.getElementById('lightbox').addEventListener('click', e => { if (e.target.id === 'lightbox') closeLightbox(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeLightbox(); });
});
