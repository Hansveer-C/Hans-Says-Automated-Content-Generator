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

        // Global event listener for Add Stream button (if it exists in the view)
        const btnAddStream = document.getElementById('btn-add-stream');
        if (btnAddStream) {
            btnAddStream.onclick = () => handleAddStream();
        }

        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    // Dashboard Logic
    async function renderDashboard(filter = 'all', query = '') {
        const streamsContainer = document.getElementById('feed-grid');
        const filterPills = document.getElementById('filter-pills');
        streamsContainer.innerHTML = '<div class="loading-shimmer" style="width: 350px;"></div>'.repeat(3);

        try {
            // Fetch and render dynamic topic filters (Channels in HootSuite parlance)
            const trendingRes = await fetch('/trending');
            const trends = await trendingRes.json();

            filterPills.innerHTML = `<button class="pill ${filter === 'all' ? 'active' : ''}" data-filter="all">All Channels</button>`;
            Object.entries(trends).forEach(([name, count]) => {
                filterPills.innerHTML += `<button class="pill ${filter === name ? 'active' : ''}" data-filter="${name}">${name} <small>(${count})</small></button>`;
            });

            const streamCategories = filter === 'all' ? Object.keys(trends).slice(0, 3) : [filter];
            streamsContainer.innerHTML = '';

            for (const cat of streamCategories) {
                const streamColumn = document.createElement('div');
                streamColumn.className = 'stream-column';
                streamColumn.innerHTML = `
                    <div class="stream-header">
                        <div class="stream-title">
                            <i data-lucide="hash"></i>
                            <span>${cat.charAt(0).toUpperCase() + cat.slice(1)} Feed</span>
                        </div>
                        <i data-lucide="more-vertical" style="cursor: pointer;"></i>
                    </div>
                    <div class="stream-content" id="stream-${cat}">
                        <div class="loading-shimmer"></div>
                    </div>
                `;
                streamsContainer.appendChild(streamColumn);

                // Fetch items for this stream
                let url = `/items?limit=15&q=${cat}`;
                if (query) url += `&q=${query}`;

                fetch(url).then(res => res.json()).then(items => {
                    const contentDiv = document.getElementById(`stream-${cat}`);
                    contentDiv.innerHTML = '';
                    items.forEach(item => {
                        contentDiv.appendChild(createCard(item));
                    });
                    if (typeof lucide !== 'undefined') lucide.createIcons();
                });
            }
        } catch (error) {
            console.error('Error fetching items/trends:', error);
            streamsContainer.innerHTML = '<p class="error">Failed to load streams. Please try again.</p>';
        }
    }

    // Composer Logic
    const composerModal = document.getElementById('composer-modal');
    const btnOpenComposer = document.getElementById('btn-open-composer');
    const btnCloseComposer = document.getElementById('close-composer');
    const composerText = document.getElementById('composer-text');
    const previewText = document.getElementById('preview-text-content');

    if (btnOpenComposer) {
        btnOpenComposer.onclick = () => composerModal.classList.add('active');
    }

    if (btnCloseComposer) {
        btnCloseComposer.onclick = () => composerModal.classList.remove('active');
    }

    if (composerText) {
        composerText.oninput = (e) => {
            previewText.textContent = e.target.value || "Your post content will appear here...";
        };
    }

    async function handleAddStream() {
        const topic = prompt("Enter a topic or keyword to add as a new stream (e.g., 'Economy', 'Technology', 'Healthcare'):");
        if (!topic) return;

        const streamsContainer = document.getElementById('feed-grid');
        const cat = topic.toLowerCase().trim();

        // Check if stream already exists
        if (document.getElementById(`stream-${cat}`)) {
            alert("This stream is already active!");
            return;
        }

        const streamColumn = document.createElement('div');
        streamColumn.className = 'stream-column';
        streamColumn.innerHTML = `
            <div class="stream-header">
                <div class="stream-title">
                    <i data-lucide="hash"></i>
                    <span>${topic} Feed</span>
                </div>
                <i data-lucide="more-vertical" style="cursor: pointer;"></i>
            </div>
            <div class="stream-content" id="stream-${cat}">
                <div class="loading-shimmer"></div>
            </div>
        `;
        streamsContainer.appendChild(streamColumn);
        if (typeof lucide !== 'undefined') lucide.createIcons();

        // Fetch items for the new stream
        fetch(`/items?limit=15&q=${cat}`).then(res => res.json()).then(items => {
            const contentDiv = document.getElementById(`stream-${cat}`);
            contentDiv.innerHTML = '';
            if (items.length === 0) {
                contentDiv.innerHTML = '<p class="placeholder-text" style="margin-top: 20px;">No recent items found for this topic.</p>';
            } else {
                items.forEach(item => {
                    contentDiv.appendChild(createCard(item));
                });
            }
            if (typeof lucide !== 'undefined') lucide.createIcons();
        }).catch(err => {
            console.error(`Error fetching items for ${cat}:`, err);
            document.getElementById(`stream-${cat}`).innerHTML = '<p class="error">Failed to load items.</p>';
        });
    }

    function createCard(item) {
        const div = document.createElement('div');
        div.className = 'content-card';
        div.style.cursor = 'pointer';

        const typeClass = item.source_type === 'news' ? 'tag-news' : 'tag-reddit';
        const typeLabel = item.source_type === 'news' ? 'News' : 'Reddit';

        const metrics = item.engagement_metrics || {};
        const score = metrics.score !== undefined ? `<div class="metric"><i data-lucide="arrow-big-up"></i>${metrics.score}</div>` : '';
        const comments = metrics.num_comments !== undefined ? `<div class="metric"><i data-lucide="message-square"></i>${metrics.num_comments}</div>` : '';

        const statusTag = item.is_unavailable ?
            '<span class="card-tag tag-unavailable">Unavailable</span>' :
            (item.enrichment_status === 'generated' ? '<span class="card-tag tag-refined">Summary (AI)</span>' : '');

        div.innerHTML = `
            <div class="card-tags">
                <span class="card-tag ${typeClass}">${typeLabel}</span>
                ${statusTag}
            </div>
            <div class="card-title">${item.title}</div>
            <p class="card-summary">${item.summary || 'No summary available.'}</p>
            <div class="card-footer">
                <span class="card-source">${item.source_name}</span>
                <div class="card-metrics">
                    ${score}
                    ${comments}
                    <div class="metric"><i data-lucide="globe"></i>${item.country}</div>
                </div>
            </div>
            <div class="card-promote-overlay">
                <button class="btn-promote-studio-icon" title="Send to Studio">
                    <i data-lucide="zap"></i>
                </button>
            </div>
        `;

        // Ensure Eye icon is ALWAYS present in a consistent container
        const metricsContainer = div.querySelector('.card-metrics');
        const viewBtn = document.createElement('button');
        viewBtn.className = 'btn-icon-sm';
        viewBtn.innerHTML = '<i data-lucide="eye"></i>';
        viewBtn.title = 'View Details';
        viewBtn.onclick = (e) => {
            e.stopPropagation();
            openReadingPane(item);
        };
        metricsContainer.appendChild(viewBtn);

        const promoteItem = async (e) => {
            if (e) e.stopPropagation();

            // Visual feedback
            div.style.opacity = '0.5';
            div.style.pointerEvents = 'none';

            const btnIcon = div.querySelector('.btn-promote-studio-icon');
            if (btnIcon) btnIcon.innerHTML = '<i class="loading-spinner"></i>';

            try {
                const res = await fetch(`/items/${item.id}/promote`, { method: 'POST' });
                const data = await res.json();
                if (data.cluster_id) {
                    window.preSelectedCluster = data.cluster_id;
                    window.preSelectedItem = item.id;
                    navigate('studio');
                }
            } catch (e) {
                console.error('Promotion failed:', e);
                div.style.opacity = '1';
                div.style.pointerEvents = 'all';
                if (btnIcon) btnIcon.innerHTML = '<i data-lucide="zap"></i>';
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }
        };

        const btnPromoteIcon = div.querySelector('.btn-promote-studio-icon');
        if (btnPromoteIcon) {
            btnPromoteIcon.onclick = promoteItem;
        }

        div.onclick = (e) => {
            if (e.target.closest('.btn-promote-studio-icon') || e.target.closest('.btn-icon-sm')) return;
            promoteItem(e);
        };

        div.title = "Click to promote this topic to the Studio";


        return div;
    }

    let currentReadingItem = null;

    function openReadingPane(item) {
        const pane = document.getElementById('reading-pane');
        const content = document.getElementById('reading-pane-content');

        // Toggle behavior: if clicking the SAME item, close it
        if (currentReadingItem === item.id && pane.classList.contains('active')) {
            closeReadingPane();
            return;
        }
        currentReadingItem = item.id;

        const typeLabel = item.source_type === 'news' ? 'News' : 'Reddit';

        content.innerHTML = `
            <div class="reading-pane-meta">
                <span class="badge active">${typeLabel}</span>
                <span>${item.source_name}</span>
                <span>${item.country}</span>
                <span>${new Date(item.timestamp).toLocaleDateString()}</span>
            </div>
            <h2>${item.title}</h2>
            <div class="reading-pane-summary">
                <p>${item.summary || 'No summary available.'}</p>
                ${item.enrichment_status === 'generated' ? '<p class="info-alert" style="font-size: 0.8em; color: var(--clr-info);">Note: This summary was generated by AI due to source restrictions.</p>' : ''}
            </div>
            <div class="reading-pane-footer" style="display: flex; gap: 10px; flex-wrap: wrap;">
                <a href="${item.url}" target="_blank" class="btn-secondary" style="text-decoration: none; font-size: 0.8em; padding: 10px 15px; background: rgba(255,255,255,0.05); border-radius: 8px; color: white;">
                    <i data-lucide="external-link"></i> View Original
                </a>
                <button id="btn-promote-studio" class="btn-primary" style="font-size: 0.8em; padding: 10px 15px;">
                    <i data-lucide="zap"></i> Send to Studio
                </button>
            </div>
        `;

        const btnPromote = document.getElementById('btn-promote-studio');
        if (btnPromote) {
            btnPromote.onclick = async () => {
                btnPromote.disabled = true;
                btnPromote.innerHTML = '<i class="loading-spinner"></i> Processing...';
                try {
                    const res = await fetch(`/items/${item.id}/promote`, { method: 'POST' });
                    const data = await res.json();
                    if (data.cluster_id) {
                        window.preSelectedCluster = data.cluster_id;
                        window.preSelectedItem = item.id;
                        closeReadingPane();
                        navigate('studio');
                    }
                } catch (e) {
                    console.error('Promotion failed:', e);
                    btnPromote.disabled = false;
                    btnPromote.innerHTML = '<i data-lucide="zap"></i> Send to Studio';
                }
            };
        }

        pane.classList.add('active');
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    function closeReadingPane() {
        document.getElementById('reading-pane').classList.remove('active');
    }

    const btnClosePane = document.getElementById('close-reading-pane');
    if (btnClosePane) btnClosePane.onclick = closeReadingPane;

    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeReadingPane();
    });

    // Studio Logic
    let selectedCluster = null;

    async function renderStudio() {
        console.log('Rendering Studio...');
        const btnGenerateCommentary = viewContainer.querySelector('#btn-generate-commentary');
        const btnGeneratePackage = viewContainer.querySelector('#btn-generate-package');
        const banner = viewContainer.querySelector('#active-topic-banner');
        const topicNameDisplay = viewContainer.querySelector('#active-topic-name');
        const referenceContainer = viewContainer.querySelector('#reference-article-source');
        const referenceContent = viewContainer.querySelector('#reference-article-content');

        if (!btnGenerateCommentary || !btnGeneratePackage || !banner) {
            console.warn('Major Studio elements missing from active view. Skipping render logic.');
            return;
        }

        // Handle pre-selection or existing selection
        if (window.preSelectedCluster) {
            selectedCluster = window.preSelectedCluster;
            window.preSelectedCluster = null;
        }

        if (selectedCluster) {
            btnGenerateCommentary.disabled = false;
            btnGeneratePackage.disabled = false;
            banner.style.display = 'flex';
            topicNameDisplay.textContent = selectedCluster.toUpperCase();

            // Handle specific item reference
            if (window.preSelectedItem && referenceContainer && referenceContent) {
                referenceContainer.style.display = 'block';
                referenceContent.innerHTML = '<div class="loading-shimmer" style="height: 100px;"></div>';
                fetch(`/items/${window.preSelectedItem}`).then(res => res.json()).then(item => {
                    if (item.error) {
                        referenceContent.innerHTML = '<p class="error">Reference article not found.</p>';
                        return;
                    }
                    referenceContent.innerHTML = `
                        <h3 style="margin-bottom: 8px;">${item.title}</h3>
                        <p style="font-size: 0.9em; opacity: 0.8; line-height: 1.4;">${item.summary}</p>
                        <div style="margin-top: 10px; font-size: 0.8em; font-weight: bold; color: var(--clr-primary-500);">
                            Source: ${item.source_name}
                        </div>
                    `;
                }).catch(err => {
                    console.error('Error fetching reference item:', err);
                    referenceContent.innerHTML = '<p class="error">Failed to load reference metadata.</p>';
                });
            }

            // Auto-fetch if selected (only if not already generating)
            fetchCommentary(selectedCluster);
            fetchPackage(selectedCluster);
        } else {
            banner.style.display = 'none';
            if (referenceContainer) referenceContainer.style.display = 'none';
        }

        const tabs = viewContainer.querySelectorAll('.tab-btn');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const target = tab.dataset.tab;
                viewContainer.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
                viewContainer.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                tab.classList.add('active');
                const targetView = viewContainer.querySelector(`#${target}-view`);
                if (targetView) targetView.classList.add('active');
            });
        });

        btnGenerateCommentary.onclick = async () => {
            if (!selectedCluster) return;
            btnGenerateCommentary.disabled = true;
            btnGenerateCommentary.innerHTML = '<span><i class="dot pulse"></i> Generating...</span>';

            const display = viewContainer.querySelector('#commentary-display');
            if (display) display.innerHTML = '<div class="loading-shimmer" style="height: 100px;"></div>'.repeat(3);

            try {
                const response = await fetch(`/topics/${selectedCluster}/generate_angles`, { method: 'POST' });
                const data = await response.json();
                btnGenerateCommentary.disabled = false;
                btnGenerateCommentary.innerHTML = '<i data-lucide="sparkles"></i> <span>Refine Angles</span>';
                if (data.angles) renderCommentary(data);
                else alert('Error: ' + (data.error || 'Failed to generate commentary.'));
            } catch (e) {
                console.error('Error in Generate Commentary:', e);
                btnGenerateCommentary.disabled = false;
                btnGenerateCommentary.innerHTML = '<i data-lucide="sparkles"></i> <span>Refine Angles</span>';
            }
        };

        btnGeneratePackage.onclick = async () => {
            if (!selectedCluster) return;
            btnGeneratePackage.disabled = true;
            btnGeneratePackage.innerHTML = '<i data-lucide="loader"></i> <span>Generating Package...</span>';

            const display = viewContainer.querySelector('#package-display');
            if (display) display.innerHTML = '<div class="loading-shimmer" style="height: 150px;"></div>'.repeat(2);

            try {
                const response = await fetch(`/topics/${selectedCluster}/generate_full_package`, { method: 'POST' });
                const data = await response.json();
                btnGeneratePackage.disabled = false;
                btnGeneratePackage.innerHTML = '<i data-lucide="package"></i> <span>Generate Platform Package</span>';
                if (data.safe_article) renderPackage(data);
            } catch (e) {
                btnGeneratePackage.disabled = false;
                btnGeneratePackage.innerHTML = '<i data-lucide="package"></i> <span>Generate Platform Package</span>';
                console.error(e);
            }
        };

        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    async function fetchCommentary(cluster_id) {
        const display = document.getElementById('commentary-display');
        display.innerHTML = '<div class="loading-shimmer" style="height: 100px;"></div>'.repeat(3);
        try {
            const response = await fetch(`/topics/${cluster_id}/angles`);
            const data = await response.json();
            if (data && data.angles) renderCommentary(data);
            else display.innerHTML = '<p class="placeholder-text">No commentary generated yet. Click "Refine Angles" to start.</p>';
        } catch (e) { display.innerHTML = '<p class="placeholder-text">Click "Refine Angles" to start.</p>'; }
    }

    async function fetchPackage(cluster_id) {
        const display = document.getElementById('package-display');
        display.innerHTML = '<div class="loading-shimmer" style="height: 150px;"></div>'.repeat(2);
        try {
            const response = await fetch(`/topics/${cluster_id}/package`);
            const data = await response.json();
            if (data && data.safe_article) renderPackage(data);
            else display.innerHTML = '<p class="placeholder-text">No package generated. Click "Generate Platform Package" to start.</p>';
        } catch (e) { display.innerHTML = '<p class="placeholder-text">Click "Generate Platform Package" to start.</p>'; }
    }

    function renderCommentary(data) {
        const display = document.getElementById('commentary-display');
        if (!display) return;

        const anglesHtml = data.angles.map(angle => `
            <div class="angle-card" style="margin-bottom: 12px; padding: 12px; border-left: 4px solid var(--clr-primary-500); background: rgba(255,255,255,0.03);">
                <div class="angle-type" style="color: var(--clr-primary-500); font-weight: bold; font-size: 0.8em; margin-bottom: 4px;">${angle.type}</div>
                <div class="angle-content" style="font-size: 0.9em;">${angle.content}</div>
            </div>
        `).join('');

        display.innerHTML = `
            ${anglesHtml}
            <div class="facebook-card" style="margin-top: 16px; padding: 16px; background: rgba(59, 130, 246, 0.1); border: 1px solid var(--clr-primary-500); border-radius: 8px;">
                <div class="facebook-header" style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px; font-weight: bold; color: #60a5fa;">
                    <i data-lucide="facebook"></i>
                    <span>Strongest Angle (Facebook Ready)</span>
                </div>
                <div class="facebook-content" style="white-space: pre-wrap; font-size: 0.95em;">${data.strongest_angle_html || 'No preview available.'}</div>
            </div>
        `;
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    function renderPackage(data) {
        const display = document.getElementById('package-display');
        if (!display) return;

        const headlinesHtml = data.safe_headlines.map(h => `<div class="headline-item">${h}</div>`).join('');
        const slidesHtml = data.carousel_slides.map(s => `<div class="beat-card"><div class="beat-number">Slide ${s.slide_number}</div>${s.text}</div>`).join('');
        const directionsHtml = data.visual_directions.map(d => `<div class="beat-card"><div class="beat-number">Visual ${d.slide_number}</div>${d.direction}</div>`).join('');

        display.innerHTML = `
            <div class="view-section">
                <div class="section-label"><i data-lucide="megaphone"></i> Scroll-Stopping Headlines</div>
                ${headlinesHtml}
            </div>
            <div class="view-section">
                <div class="section-label"><i data-lucide="file-text"></i> Safe Article (Revised)</div>
                <div class="article-body">${data.safe_article.replace(/\n/g, '<br>')}</div>
            </div>
            <div class="view-section">
                <div class="section-label"><i data-lucide="message-square"></i> Engagement CTA & Pinned Comment</div>
                <div class="cta-box">${data.safe_cta}</div>
                <p style="margin-top: 10px; font-size: 0.9em; opacity: 0.8;"><b>Pinned:</b> ${data.pinned_comment}</p>
            </div>
            <div class="view-section">
                <div class="section-label"><i data-lucide="layout"></i> Carousel Assets (Visual Media)</div>
                <div class="beats-grid">${slidesHtml}</div>
                <div class="beats-grid" style="margin-top: 10px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 10px;">
                    ${directionsHtml}
                </div>
            </div>
        `;
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    async function renderAdmin() {
        document.getElementById('stat-total-items').textContent = '470+';
        const sourceListUi = document.getElementById('source-list-ui');
        sourceListUi.innerHTML = `
            <li>CBC News - Politics <span class="badge active">Active</span></li>
            <li>The Hindu - National <span class="badge active">Active</span></li>
            <li>r/CanadaPolitics <span class="badge active">Active</span></li>
        `;
    }

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            navigate(item.dataset.view);
        });
    });

    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('pill')) {
            const pills = document.querySelectorAll('.pill');
            pills.forEach(p => p.classList.remove('active'));
            e.target.classList.add('active');
            renderDashboard(e.target.dataset.filter);
        }
    });

    globalSearch.addEventListener('input', debounce((e) => {
        if (document.querySelector('.nav-item[data-view="dashboard"]').classList.contains('active')) {
            renderDashboard('all', e.target.value);
        }
    }, 500));

    function debounce(func, timeout = 300) {
        let timer;
        return (...args) => {
            clearTimeout(timer);
            timer = setTimeout(() => { func.apply(this, args); }, timeout);
        };
    }

    navigate('dashboard');
});
