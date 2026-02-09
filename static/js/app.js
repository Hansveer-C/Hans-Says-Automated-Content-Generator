document.addEventListener('DOMContentLoaded', () => {
    const viewContainer = document.getElementById('view-container');
    const navItems = document.querySelectorAll('.nav-item');
    const globalSearch = document.getElementById('global-search');
    const sidebar = document.getElementById('sidebar');
    const btnToggleSidebar = document.getElementById('btn-toggle-sidebar');

    // Sidebar Toggle & Persistence
    if (sidebar && btnToggleSidebar) {
        // Init from storage
        const isCollapsed = localStorage.getItem('sidebar-collapsed') === 'true';
        if (isCollapsed) sidebar.classList.add('collapsed');

        btnToggleSidebar.onclick = () => {
            const nowCollapsed = sidebar.classList.toggle('collapsed');
            localStorage.setItem('sidebar-collapsed', nowCollapsed);
        };
    }

    // Routing Logic
    const routes = {
        dashboard: () => renderDashboard(),
        studio: () => renderStudio(),
        admin: () => renderAdmin()
    };

    async function navigate(view) {
        navItems.forEach(item => {
            item.classList.remove('active');
            if (item.dataset.view === view) item.classList.add('active');
        });

        const template = document.getElementById(`${view}-template`);
        if (!template) {
            console.error(`Template ${view}-template not found!`);
            return;
        }

        console.log(`Navigating to ${view}`);
        viewContainer.innerHTML = '';
        viewContainer.appendChild(template.content.cloneNode(true));

        if (routes[view]) {
            console.log(`Executing route for ${view}`);
            try {
                await routes[view]();
            } catch (e) {
                console.error(`Error in route ${view}:`, e);
            }
        }

        // Global event listener for Add Stream button
        const btnAddStream = document.getElementById('btn-add-stream');
        if (btnAddStream) {
            btnAddStream.onclick = () => handleAddStream();
        }

        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    /* --- UI Component Registry --- */
    const UI = {
        scoreBadge: (type, value) => `
            <div class="score-badge ${type}">
                <i data-lucide="${type === 'controversy' ? 'alert-circle' : (type === 'final' ? 'award' : 'hash')}"></i>
                <span>${value}</span>
            </div>`,

        statusChip: (status, active = false) => `
            <div class="status-chip ${active ? 'active' : ''}">${status}</div>`,

        copyButton: (text, label = "Copy") => {
            const btn = document.createElement('button');
            btn.className = 'btn-primitive';
            btn.innerHTML = `<i data-lucide="copy"></i><span>${label}</span>`;
            btn.onclick = () => {
                navigator.clipboard.writeText(text);
                btn.innerHTML = `<i data-lucide="check"></i><span>Copied!</span>`;
                setTimeout(() => {
                    btn.innerHTML = `<i data-lucide="copy"></i><span>${label}</span>`;
                    lucide.createIcons();
                }, 2000);
            };
            return btn;
        },

        validationBanner: (results) => {
            if (results.errors.length > 0) {
                return `<div class="validation-banner error"><i data-lucide="x-circle"></i><span>${results.errors[0]}</span></div>`;
            }
            if (results.warnings.length > 0) {
                return `<div class="validation-banner warning"><i data-lucide="alert-triangle"></i><span>${results.warnings[0]}</span></div>`;
            }
            return `<div class="validation-banner success"><i data-lucide="check-circle"></i><span>Ready to Publish</span></div>`;
        },

        inlineEditor: (id, label, value, onUpdate) => {
            const div = document.createElement('div');
            div.className = 'inline-editor-container';
            div.innerHTML = `
                <div class="field-label" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span>${label}</span>
                    <button class="btn-primitive copy-field" style="padding:2px 6px; font-size:10px;"><i data-lucide="copy" style="width:10px;"></i></button>
                </div>
                <textarea id="${id}" class="field-value glass" style="width:100%; min-height:80px; background:rgba(255,255,255,0.03); border:1px solid var(--border-subtle); border-radius:8px; color:white; padding:10px; font-size:13px; font-family:inherit; resize:vertical;">${value || ''}</textarea>
            `;
            const textarea = div.querySelector('textarea');
            textarea.oninput = () => onUpdate(textarea.value);

            div.querySelector('.copy-field').onclick = () => {
                navigator.clipboard.writeText(textarea.value);
            };

            return div;
        }
    };

    /* --- Validation Engine --- */
    const ValidationRules = {
        global: (pkg) => {
            const errors = [];
            const warnings = [];
            if (pkg.used_for_content) warnings.push("Item already marked as used.");
            const age = (new Date() - new Date(pkg.date)) / (1000 * 60 * 60);
            if (age > 72) warnings.push("Content is older than 72 hours.");
            return { errors, warnings };
        },

        facebook: (pkg) => {
            const errors = [];
            const warnings = [];
            if (!pkg.facebook_post_body) errors.push("Post body is required.");
            else {
                const words = pkg.facebook_post_body.split(/\s+/).length;
                if (words < 250) errors.push("Post body is too short (min 250 words).");
                if (words > 500) errors.push("Post body is too long (max 500 words).");
                if (!pkg.facebook_post_body.includes('\n\n')) errors.push("Missing paragraph breaks.");
            }
            if (!pkg.facebook_pinned_comment) errors.push("Pinned comment required.");
            if (!pkg.facebook_headlines || pkg.facebook_headlines.length < 3) errors.push("Missing 3 headlines.");
            return { errors, warnings };
        },

        instagram: (pkg) => {
            const errors = [];
            const warnings = [];
            if (!pkg.ig_on_screen_text || pkg.ig_on_screen_text.length < 6) errors.push("Minimum 6 text beats required.");
            if (pkg.ig_on_screen_text && pkg.ig_on_screen_text.some(t => t.split(' ').length > 10)) errors.push("Beat text exceeds 10 words.");
            if (!pkg.ig_caption) errors.push("Caption required.");
            return { errors, warnings };
        },

        twitter: (pkg) => {
            const errors = [];
            const warnings = [];
            if (!pkg.x_primary_post) errors.push("Primary post required.");
            else if (pkg.x_primary_post.length > 280) errors.push("Post exceeds 280 characters.");
            return { errors, warnings };
        }
    };

    function validatePackage(pkg) {
        const platforms = ['global', 'facebook', 'instagram', 'twitter'];
        const report = {};
        let overallBlocked = false;

        platforms.forEach(p => {
            if (ValidationRules[p]) {
                const res = ValidationRules[p](pkg);
                report[p] = res;
                if (res.errors.length > 0) overallBlocked = true;
            }
        });

        return { report, overallBlocked };
    }

    // Dashboard Logic
    async function renderDashboard(filter = 'all', query = '') {
        const streamsContainer = document.getElementById('feed-grid');
        const filterSidebar = document.getElementById('filter-sidebar');
        if (!streamsContainer || !filterSidebar) return;

        streamsContainer.innerHTML = '<div class="loading-shimmer"></div>';

        // Filter state
        const state = {
            source: filterSidebar.querySelector('[data-source].active')?.dataset.source || 'all',
            signal: filterSidebar.querySelector('[data-signal].active')?.dataset.signal || null,
            minScore: document.getElementById('filter-min-score')?.value || 0,
            used: filterSidebar.querySelector('[data-used].active')?.dataset.used || 'all',
            search: document.getElementById('feed-search')?.value || query
        };

        try {
            let url = `/items?limit=100`;
            if (state.source !== 'all') url += `&source_type=${state.source}`;
            if (state.used === 'unused') url += `&used=false`;
            if (state.search) url += `&q=${encodeURIComponent(state.search)}`;

            const res = await fetch(url);
            let items = await res.json();

            // Client-side filtering
            items = items.filter(item => {
                if (item.final_score < state.minScore) return false;
                if (state.signal) {
                    const signals = calculateSignals(item);
                    if (!signals[state.signal]) return false;
                }
                return true;
            });

            streamsContainer.innerHTML = '';
            if (items.length === 0) {
                streamsContainer.innerHTML = '<div class="placeholder-text">No items match your filters.</div>';
            } else {
                items.forEach(item => {
                    streamsContainer.appendChild(createCard(item));
                });
            }
            if (typeof lucide !== 'undefined') lucide.createIcons();
        } catch (error) {
            console.error('Error fetching items:', error);
            streamsContainer.innerHTML = '<p class="error">Failed to load feed. Please try again.</p>';
        }
    }

    async function handleAddStream() {
        const topic = prompt("Enter a topic to watch:");
        if (!topic) return;
        renderDashboard('all', topic);
    }

    function createCard(item) {
        const div = document.createElement('div');
        div.className = 'content-card glass';

        const signals = calculateSignals(item);
        const signalHtml = `
            <div class="platform-signal-grid" style="display:flex; gap:6px; margin-top:10px;">
                <div class="platform-signal ${signals.fb ? 'active' : ''}" title="Facebook"><i data-lucide="facebook"></i></div>
                <div class="platform-signal ${signals.ig ? 'active' : ''}" title="Instagram"><i data-lucide="instagram"></i></div>
                <div class="platform-signal ${signals.yt ? 'active' : ''}" title="YouTube"><i data-lucide="youtube"></i></div>
                <div class="platform-signal ${signals.x ? 'active' : ''}" title="X"><i data-lucide="twitter"></i></div>
            </div>
        `;

        div.innerHTML = `
            <div class="card-tags">
                <span class="card-tag ${item.source_type === 'news' ? 'tag-news' : 'tag-reddit'}">${item.source_type.toUpperCase()}</span>
                ${item.used_for_content ? '<span class="status-chip active">USED</span>' : ''}
            </div>
            <div class="card-title">${item.title}</div>
            <div style="display:flex; gap:8px; margin-top:8px;">
                ${UI.scoreBadge('hash', item.controversy_score.toFixed(1))}
                ${UI.scoreBadge('final', item.final_score.toFixed(1))}
            </div>
            ${signalHtml}
            <div class="card-footer" style="margin-top:12px; display:flex; justify-content:space-between; align-items:center;">
                <span class="card-source">${item.source_name}</span>
                <span style="font-size:10px; opacity:0.5;">${new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
        `;

        div.onclick = () => openDetailDrawer(item);
        return div;
    }

    function calculateSignals(item) {
        return {
            fb: item.source_type === 'news' || item.summary?.length > 200,
            ig: item.source_type === 'reddit' || item.title?.length < 80,
            yt: item.source_type === 'news' && item.summary?.length > 150,
            x: item.title?.length < 150
        };
    }

    function openDetailDrawer(item) {
        const drawer = document.getElementById('detail-drawer');
        const emptyMsg = document.getElementById('detail-empty');
        const content = document.getElementById('detail-content');
        if (!drawer || !content) return;

        emptyMsg.style.display = 'none';
        content.style.display = 'block';
        drawer.classList.add('active');

        content.innerHTML = `
            <div class="view-header">
                <h2>${item.title}</h2>
            </div>
            <div class="section-label">Summary Intelligence</div>
            <p style="font-size:13px; line-height:1.6; opacity:0.8; margin-bottom:20px;">${item.summary || 'No summary available.'}</p>
            
            <div class="section-label">Actions</div>
            <button class="btn-primary" id="btn-promote-studio-detail" style="width:100%; justify-content:center; margin-bottom:10px;">
                <i data-lucide="zap"></i>
                <span>Send to Studio</span>
            </button>
            <a href="${item.url}" target="_blank" class="btn-secondary" style="width:100%; justify-content:center; text-decoration:none;">
                <i data-lucide="external-link"></i>
                <span>View Original Source</span>
            </a>
        `;

        content.querySelector('#btn-promote-studio-detail').onclick = async () => {
            const btn = document.getElementById('btn-promote-studio-detail');
            btn.disabled = true;
            btn.innerHTML = '<i class="loading-spinner"></i> Promoting...';
            try {
                const res = await fetch(`/items/${item.id}/promote`, { method: 'POST' });
                const data = await res.json();
                if (data.cluster_id) {
                    window.preSelectedCluster = data.cluster_id;
                    navigate('studio');
                }
            } catch (e) {
                console.error('Promotion failed:', e);
                btn.disabled = false;
                btn.innerHTML = '<i data-lucide="zap"></i> Send to Studio';
            }
        };

        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    // Studio Logic
    async function renderStudio() {
        const queueList = document.getElementById('queue-list');
        if (!queueList) return;

        try {
            const res = await fetch('/items?used=true&limit=10');
            const items = await res.json();
            queueList.innerHTML = '';
            if (items.length === 0) {
                queueList.innerHTML = '<div class="placeholder-text">Queue is empty.</div>';
            } else {
                items.forEach(item => {
                    const div = document.createElement('div');
                    div.className = 'queue-card glass';
                    div.style = "padding:10px; border-radius:8px; margin-bottom:10px; cursor:pointer;";
                    div.innerHTML = `
                        <div style="font-size:11px; font-weight:bold; color:var(--clr-primary-400); margin-bottom:20px;">${item.cluster_id}</div>
                        <div style="font-size:12px; opacity:0.8; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${item.title}</div>
                    `;
                    div.onclick = () => loadTopicPackage(item.cluster_id);
                    queueList.appendChild(div);
                });
            }
        } catch (e) {
            console.error('Failed to load queue:', e);
        }

        if (window.preSelectedCluster) {
            loadTopicPackage(window.preSelectedCluster);
            window.preSelectedCluster = null;
        }
    }

    async function loadTopicPackage(clusterId) {
        if (!clusterId) return;
        const studioEmpty = document.getElementById('studio-empty');
        const cockpitContainer = document.getElementById('platform-rows-container');
        if (studioEmpty) studioEmpty.style.display = 'none';
        if (cockpitContainer) {
            cockpitContainer.style.display = 'block';
            cockpitContainer.innerHTML = '<div class="loading-shimmer"></div>';
        }

        try {
            let pkgRes = await fetch(`/topics/${clusterId}/package`);
            let pkg = await pkgRes.json();

            if (pkg.error) {
                renderCockpitHeader(clusterId, null);
                cockpitContainer.innerHTML = `
                    <div style="text-align:center; padding: 40px;">
                        <p style="opacity:0.6; margin-bottom:20px;">No package generated yet.</p>
                        <button class="btn-primary" onclick="generateFullPackage('${clusterId}')">Generate Package</button>
                    </div>
                `;
            } else {
                renderCockpitHeader(clusterId, pkg);
                renderPlatformRows(pkg);
            }
            if (typeof lucide !== 'undefined') lucide.createIcons();
        } catch (e) {
            console.error('Load package failed:', e);
        }
    }
    window.loadTopicPackage = loadTopicPackage;

    async function generateFullPackage(clusterId) {
        if (!clusterId) return;
        const cockpitContainer = document.getElementById('platform-rows-container');
        if (cockpitContainer) cockpitContainer.innerHTML = '<div class="loading-shimmer"></div>';

        try {
            await fetch(`/topics/${clusterId}/generate_full_package`, { method: 'POST' });
            loadTopicPackage(clusterId);
        } catch (e) {
            console.error('Generation Error:', e);
            alert('An error occurred during generation.');
        }
    }
    window.generateFullPackage = generateFullPackage;

    function renderCockpitHeader(clusterId, pkg) {
        const container = document.getElementById('studio-header-container');
        if (!container) return;
        container.innerHTML = `
            <div class="view-header">
                <div>
                    <h1>Publishing Cockpit <span class="score-badge cluster">${clusterId}</span></h1>
                    <p style="font-size:12px; opacity:0.6;">Distributing content across platforms.</p>
                </div>
                <button class="btn-secondary" onclick="generateFullPackage('${clusterId}')">Regenerate All</button>
            </div>
            ${pkg ? `<div class="glass" style="padding:15px; border-radius:12px; margin-bottom:20px; border-left:4px solid var(--clr-primary-500);">
                <div class="section-label">Core Thesis</div>
                <p style="font-size:13px; color:var(--clr-neutral-200);">${pkg.core_thesis}</p>
            </div>` : ''}
        `;
    }

    function renderPlatformRows(pkg) {
        const container = document.getElementById('platform-rows-container');
        if (!container) return;
        container.innerHTML = '';

        const platforms = [
            { id: 'facebook', name: 'Facebook Page', icon: 'facebook' },
            { id: 'instagram', name: 'Instagram Reels', icon: 'instagram' },
            { id: 'twitter', name: 'X (Twitter)', icon: 'twitter' }
        ];

        platforms.forEach(p => {
            const div = document.createElement('div');
            div.className = 'platform-row';
            const res = ValidationRules[p.id](pkg);
            const statusClass = res.errors.length > 0 ? 'blocked' : (res.warnings.length > 0 ? 'warning' : 'ready');

            div.innerHTML = `
                <div class="platform-row-header">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <div class="readiness-badge ${statusClass}"></div>
                        <i data-lucide="${p.icon}"></i>
                        <strong>${p.name}</strong>
                    </div>
                    <button class="btn-primitive" onclick="generateFullPackage('${pkg.cluster_id}')"><i data-lucide="refresh-cw"></i></button>
                </div>
                <div class="platform-row-content">
                    <div class="validation-banner-container">${UI.validationBanner(res)}</div>
                    <div class="composer-grid"></div>
                </div>
            `;
            const grid = div.querySelector('.composer-grid');
            if (p.id === 'facebook') {
                grid.appendChild(UI.inlineEditor('fb-body', 'Post Body', pkg.facebook_post_body, (v) => { pkg.facebook_post_body = v; updateReadiness(pkg); }));
            } else if (p.id === 'instagram') {
                grid.appendChild(UI.inlineEditor('ig-caption', 'Caption', pkg.ig_caption, (v) => { pkg.ig_caption = v; updateReadiness(pkg); }));
            } else if (p.id === 'twitter') {
                grid.appendChild(UI.inlineEditor('x-body', 'Primary Post', pkg.x_primary_post, (v) => { pkg.x_primary_post = v; updateReadiness(pkg); }));
            }
            container.appendChild(div);
        });

        updateReadiness(pkg);
    }

    function updateReadiness(pkg) {
        const readinessPanel = document.getElementById('readiness-panel');
        const btnMarkReady = document.getElementById('btn-mark-ready');
        if (!readinessPanel) return;

        const validation = validatePackage(pkg);
        readinessPanel.innerHTML = '';

        Object.entries(validation.report).forEach(([p, res]) => {
            const statusClass = res.errors.length > 0 ? 'error' : (res.warnings.length > 0 ? 'warning' : 'active');
            const div = document.createElement('div');
            div.style = "display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; font-size:11px;";
            div.innerHTML = `
                <span style="text-transform:capitalize;">${p}</span>
                <span class="status-chip ${statusClass}">${res.errors.length > 0 ? 'Fail' : 'Pass'}</span>
            `;
            readinessPanel.appendChild(div);
        });

        if (btnMarkReady) {
            btnMarkReady.disabled = validation.overallBlocked;
            btnMarkReady.classList.toggle('btn-primary', !validation.overallBlocked);
            btnMarkReady.classList.toggle('btn-secondary', validation.overallBlocked);
        }
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    async function renderAdmin() {
        try {
            const res = await fetch('/sources');
            const sources = await res.json();
            const list = document.getElementById('source-list-ui');
            if (list) {
                list.innerHTML = sources.map(s => `
                    <li style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.05);">
                        <span>${s.name}</span>
                        <span class="badge ${s.is_active ? 'active' : ''}">${s.is_active ? 'Active' : 'Inactive'}</span>
                    </li>
                `).join('');
            }
        } catch (e) {
            console.error('Admin load failed:', e);
        }
    }

    // Global Listeners
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('pill')) {
            const group = e.target.parentElement;
            group.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
            e.target.classList.add('active');
            renderDashboard();
        }
    });

    navItems.forEach(item => {
        item.onclick = (e) => {
            e.preventDefault();
            navigate(item.dataset.view);
        };
    });

    navigate('dashboard');
});
