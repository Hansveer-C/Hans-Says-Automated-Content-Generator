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

            const display = viewContainer.querySelector('#package-content-area');
            if (display) display.innerHTML = '<div class="loading-shimmer" style="height: 150px;"></div>'.repeat(3);

            try {
                const response = await fetch(`/topics/${selectedCluster}/generate_full_package`, { method: 'POST' });
                const data = await response.json();
                btnGeneratePackage.disabled = false;
                btnGeneratePackage.innerHTML = '<i data-lucide="package"></i> <span>Generate Platform Package</span>';
                if (data.primary_topic || data.cluster_id) renderPackage(data);
                else alert('Error: ' + (data.error || 'Failed to generate package.'));
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
        const display = document.getElementById('package-content-area');
        if (display) display.innerHTML = '<div class="loading-shimmer" style="height: 150px;"></div>'.repeat(3);
        try {
            const response = await fetch(`/topics/${cluster_id}/package`);
            const data = await response.json();
            if (data && (data.primary_topic || data.cluster_id)) renderPackage(data);
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

    let currentPackageData = null;

    function renderPackage(data) {
        currentPackageData = data;
        const display = document.getElementById('package-display');
        const contentArea = document.getElementById('package-content-area');
        if (!display || !contentArea) return;

        // Initialize sub-tabs
        const subTabs = display.querySelectorAll('.sub-tab-btn');
        subTabs.forEach(tab => {
            tab.onclick = () => {
                subTabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                renderSubTab(tab.dataset.subtab);
            };
        });

        // Initial render
        renderSubTab('canonical');
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    function renderSubTab(tabName) {
        const area = document.getElementById('package-content-area');
        if (!area || !currentPackageData) return;
        const data = currentPackageData;

        let html = '';
        switch (tabName) {
            case 'canonical':
                html = `
                    <div class="view-section">
                        <div class="section-label"><i data-lucide="info"></i> Canonical Source Outputs</div>
                        <div class="headline-item" style="background: rgba(16, 185, 129, 0.1); color: var(--clr-success);">Primary: ${data.primary_topic || 'Not set'}</div>
                        <div class="headline-item">Secondary: ${data.secondary_topic || 'Not set'}</div>
                        <div class="cta-box" style="margin-top: 12px; border-style: solid;">
                            <strong>Core Thesis:</strong><br>${data.core_thesis || 'Not set'}
                        </div>
                        <div class="facebook-card" style="margin-top: 12px; border-color: rgba(255,255,255,0.1); background: rgba(0,0,0,0.2);">
                            <div class="section-label">Editorial Angle</div>
                            <div style="font-size: 0.9em; opacity: 0.9;">${data.editorial_angle || 'Not set'}</div>
                        </div>
                    </div>
                `;
                break;
            case 'facebook':
                html = `
                    <div class="view-section">
                        <div class="section-label"><i data-lucide="facebook"></i> Facebook Page Package</div>
                        <div class="article-body" style="margin-bottom: 20px;">${(data.facebook_post_body || '').replace(/\n/g, '<br>')}</div>
                        
                        <div class="section-label">Distribution Safe Version</div>
                        <div class="article-body" style="font-size: 0.9em; opacity: 0.8; margin-bottom: 20px; border-left: 3px solid var(--clr-success); padding-left: 12px;">
                            ${(data.facebook_distribution_safe_version || 'No safe version generated').replace(/\n/g, '<br>')}
                        </div>

                        <div class="section-label">Headlines (Scroll-Stopping)</div>
                        ${(data.facebook_headlines || []).map(h => `<div class="headline-item">${h}</div>`).join('')}
                        
                        <div class="section-label" style="margin-top: 16px;">Call to Action</div>
                        <div class="cta-box">${data.facebook_cta || 'No CTA generated'}</div>
                        
                        <div class="section-label" style="margin-top: 16px;">Pinned Comment</div>
                        <div class="beat-card" style="padding: 12px; border: 1px solid var(--clr-primary-500);">${data.facebook_pinned_comment || ''}</div>

                        ${data.facebook_metadata ? `
                        <div class="metadata-grid" style="margin-top: 16px; display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; font-size: 0.8em; opacity: 0.7;">
                            <div><strong>Intent:</strong> ${data.facebook_metadata.post_intent}</div>
                            <div><strong>Time:</strong> ${data.facebook_metadata.recommended_post_time}</div>
                        </div>` : ''}
                    </div>

                    <div class="view-section" style="margin-top: 12px;">
                        <div class="section-label"><i data-lucide="users"></i> Facebook Groups (Conversational)</div>
                        <div class="cta-box" style="background: rgba(255,255,255,0.03); border-color: var(--clr-primary-400); color: white;">
                             ${(data.facebook_group_post_body || '').replace(/\n/g, '<br>')}
                        </div>
                        <div style="margin-top: 12px;">
                            <strong>Discussion Prompt:</strong><br>${data.facebook_group_discussion_prompt || 'None'}
                        </div>
                        <div style="margin-top: 10px; font-size: 0.85em; background: rgba(255,165,0,0.1); padding: 8px; border-radius: 4px;">
                            <strong>Safety Notes:</strong> ${data.facebook_group_safety_notes || 'No specific guidance.'}
                        </div>
                        ${data.facebook_group_metadata ? `
                        <div class="metadata-grid" style="margin-top: 10px; display: flex; gap: 15px; font-size: 0.75em; opacity: 0.6;">
                            <span><strong>Safe Score:</strong> ${data.facebook_group_metadata.group_safe_score}</span>
                            <span><strong>Delay:</strong> ${data.facebook_group_metadata.recommended_delay}</span>
                        </div>` : ''}
                    </div>
                `;
                break;
            case 'instagram':
                html = `
                    <div class="view-section">
                        <div class="section-label"><i data-lucide="instagram"></i> Instagram Reels Package</div>
                        <div class="section-label">On-Screen Text Clusters</div>
                        <div class="beats-grid" style="margin-bottom: 16px;">
                            ${(data.ig_on_screen_text || []).map((text, i) => `<div class="beat-card"><div class="beat-number">C${i + 1}</div>${text}</div>`).join('')}
                        </div>

                        <div class="section-label">Full Reel Script</div>
                        <div class="beats-grid">
                            ${(data.ig_reel_script || []).map(b => `<div class="beat-card"><div class="beat-number">${b.beat}</div>${b.text}</div>`).join('')}
                        </div>

                        <div class="section-label" style="margin-top: 16px;">Caption & Hashtags</div>
                        <div class="article-body" style="font-size: 0.9em; padding: 12px; background: rgba(0,0,0,0.2); border-radius: 8px;">
                            ${(data.ig_caption || '').replace(/\n/g, '<br>')}
                            <div style="margin-top: 8px; color: var(--clr-primary-400);">${(data.ig_hashtags || []).join(' ')}</div>
                        </div>

                        <div class="section-label" style="margin-top: 16px;">Engagement</div>
                        <div class="beat-card" style="border-left: 4px solid #e4405f;">
                            <strong>Seed Question:</strong> ${data.ig_seed_comment || 'None'}
                        </div>

                        ${data.ig_metadata ? `
                        <div class="metadata-grid" style="margin-top: 10px; font-size: 0.75em; opacity: 0.6;">
                            <strong>Audio:</strong> ${data.ig_metadata.audio_guidance} | <strong>Post:</strong> ${data.ig_metadata.recommended_post_time}
                        </div>` : ''}
                    </div>
                `;
                break;
            case 'youtube':
                html = `
                    <div class="view-section">
                        <div class="section-label"><i data-lucide="youtube"></i> YouTube Shorts Package</div>
                        <div class="headline-item" style="margin-bottom: 12px; background: #ff000010; border: 1px solid #ff000030;">${data.yt_title || 'No title'}</div>
                        <div class="section-label">Timestamped Script (20-40s)</div>
                        <pre style="white-space: pre-wrap; font-family: inherit; font-size: 0.9em; background: rgba(0,0,0,0.2); padding: 12px; border-radius: 8px;">${data.yt_shorts_script || ''}</pre>
                        
                        <div class="section-label" style="margin-top: 16px;">Description</div>
                        <div style="font-size: 0.85em; opacity: 0.8; margin-bottom: 12px;">${data.yt_description || ''}</div>

                        <div class="section-label">Engagement</div>
                        <div class="beat-card" style="border-left: 4px solid #ff0000;"><strong>Pinned Question:</strong> ${data.yt_pinned_comment || ''}</div>
                        
                        ${data.yt_metadata ? `
                        <div class="metadata-grid" style="margin-top: 10px; font-size: 0.75em; opacity: 0.6;">
                            <strong>Hook Check:</strong> ${data.yt_metadata.retention_hook_used ? '✅ Hooked' : '❌ Missing'} | <strong>Post:</strong> ${data.yt_metadata.recommended_post_time}
                        </div>` : ''}
                    </div>
                `;
                break;
            case 'x':
                html = `
                    <div class="view-section">
                        <div class="section-label"><i data-lucide="twitter"></i> X (Twitter) Package</div>
                        <div class="cta-box" style="background: #000; border-color: #1da1f2; color: #fff; font-size: 1.1em; margin-bottom: 20px;">
                            ${data.x_primary_post || ''}
                        </div>

                        ${(data.x_thread_replies || []).length > 0 ? `
                        <div class="section-label">Thread Replies</div>
                        ${(data.x_thread_replies || []).map((p, i) => `
                            <div class="beat-card" style="margin-bottom: 8px;">
                                <div class="beat-number">Reply ${i + 1}</div>
                                ${p}
                            </div>
                        `).join('')}` : ''}

                        <div class="section-label" style="margin-top: 16px;">Engagement Question</div>
                        <div class="cta-box" style="padding: 10px; border-style: dotted;">${data.x_engagement_question || 'None'}</div>

                        ${data.x_metadata ? `
                        <div class="metadata-grid" style="margin-top: 10px; font-size: 0.75em; opacity: 0.6;">
                            <strong>Type:</strong> ${data.x_metadata.post_type} | <strong>Post:</strong> ${data.x_metadata.recommended_post_time}
                        </div>` : ''}
                    </div>
                `;
                break;
            case 'carousel':
                html = `
                    <div class="view-section">
                        <div class="section-label"><i data-lucide="layers"></i> Carousel / Slide Package</div>
                        <div class="beats-grid" style="grid-template-columns: repeat(2, 1fr);">
                            ${(data.carousel_slides || []).map(s => `
                                <div class="beat-card" style="border: 1px solid rgba(255,255,255,0.05); min-height: 100px;">
                                    <div class="beat-number">Slide ${s.slide || s.slide_number}</div>
                                    <div style="font-weight: bold; margin-bottom: 4px;">${s.text}</div>
                                    <div style="font-size: 0.75em; opacity: 0.6; margin-top: 8px;">
                                        <strong>Visual:</strong> ${s.visual_direction || 'None'}<br>
                                        <strong>Style:</strong> ${s.text_style || 'Default'}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                        <div class="section-label" style="margin-top: 16px;">Carousel Caption</div>
                        <div class="article-body" style="font-size: 0.9em;">${data.carousel_caption || ''}</div>
                    </div>
                `;
                break;
            case 'engagement':
                html = `
                    <div class="view-section">
                        <div class="section-label"><i data-lucide="message-circle"></i> Comment Seeding & Engagement Strategy</div>
                        <div class="beat-card" style="background: rgba(16, 185, 129, 0.05); border: 1px solid var(--clr-success);">
                            <strong>Pin Recommendation:</strong> ${data.seeding_pin_recommendation || ''}
                        </div>
                        <div style="margin-top: 8px; font-size: 0.8em; opacity: 0.7;">
                            <strong>Follow-up Timing:</strong> ${data.seeding_follow_up_timing || 'Not set'}
                        </div>

                        <div class="section-label" style="margin-top: 16px;">Platform Specific Seeds</div>
                        <div class="beats-grid">
                            <div class="beat-card">
                                <div class="beat-number">YouTube</div>
                                <ul style="padding-left: 14px; font-size: 0.85em;">${(data.seeding_yt_comments || []).map(li => `<li>${li}</li>`).join('')}</ul>
                            </div>
                            <div class="beat-card">
                                <div class="beat-number">Instagram</div>
                                <ul style="padding-left: 14px; font-size: 0.85em;">${(data.seeding_ig_comments || []).map(li => `<li>${li}</li>`).join('')}</ul>
                            </div>
                        </div>

                        <div class="section-label" style="margin-top: 16px;">Creator Reply Templates</div>
                        <div class="beats-grid" style="grid-template-columns: repeat(3, 1fr);">
                            ${Object.entries(data.seeding_creator_reply_templates || {}).map(([type, tpl]) => `
                                <div class="beat-card">
                                    <div class="beat-number" style="text-transform: capitalize;">${type}</div>
                                    <div style="font-size: 0.85em;">${tpl}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
                break;
            case 'scheduling':
                html = `
                    <div class="view-section">
                        <div class="section-label"><i data-lucide="calendar"></i> Deployment & Scheduling Plan</div>
                        <div class="cta-box" style="border-style: solid; background: rgba(59, 130, 246, 0.05);">
                            <strong>Ideal Window:</strong> ${data.posting_reason || ''}
                        </div>
                        <div class="section-label" style="margin-top: 16px;">Staggered Platform Launch</div>
                        <div class="beats-grid">
                            ${Object.entries(data.recommended_post_times || {}).map(([p, t]) => `
                                <div class="beat-card">
                                    <div class="beat-number">${p}</div>
                                    <div style="font-weight: bold;">${new Date(t).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                                    <div style="font-size: 0.7em; opacity: 0.5;">${new Date(t).toLocaleDateString()}</div>
                                </div>
                            `).join('')}
                        </div>
                        <div style="margin-top: 16px; display: flex; gap: 10px; align-items: center;">
                            <span class="badge active">Queue Position: ${data.today_queue_position || '1'}</span>
                            <span class="badge" style="background: rgba(255,255,255,0.1);">Next Action: ${data.next_action || 'wait'}</span>
                        </div>
                    </div>
                `;
                break;
        }

        area.innerHTML = html;
        lucide.createIcons();
    }

    async function renderAdmin() {
        try {
            const itemsRes = await fetch('/items?limit=1');
            const totalItems = itemsRes.headers.get('X-Total-Count') || '930+'; // Simple fallback or mock
            document.getElementById('stat-total-items').textContent = totalItems;

            const sourcesRes = await fetch('/sources');
            const sources = await sourcesRes.json();
            const sourceListUi = document.getElementById('source-list-ui');

            sourceListUi.innerHTML = sources.map(s => `
                <li style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <span>${s.name} <small style="opacity: 0.5;">(${s.country})</small></span>
                    <span class="badge ${s.is_active ? 'active' : ''}">${s.is_active ? 'Active' : 'Inactive'}</span>
                </li>
            `).join('');
        } catch (e) {
            console.error('Admin render failed:', e);
        }
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
