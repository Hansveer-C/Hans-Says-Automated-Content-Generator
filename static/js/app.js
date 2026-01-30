document.addEventListener('DOMContentLoaded', () => {
    const viewContainer = document.getElementById('view-container');
    const navItems = document.querySelectorAll('.nav-item');
    const globalSearch = document.getElementById('global-search');

    // Routing Logic
    const routes = {
        dashboard: () => renderDashboard(),
        studio: () => renderStudio(),
        admin: () => renderAdmin()
    };

    function navigate(view) {
        // Update UI
        navItems.forEach(item => {
            item.classList.remove('active');
            if (item.dataset.view === view) item.classList.add('active');
        });

        // Run Route
        const template = document.getElementById(`${view}-template`);
        viewContainer.innerHTML = '';
        viewContainer.appendChild(template.content.cloneNode(true));

        if (routes[view]) routes[view]();

        // Refresh icons
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    // Dashboard Logic
    async function renderDashboard(filter = 'all', query = '') {
        const feedGrid = document.getElementById('feed-grid');
        feedGrid.innerHTML = '<div class="loading-shimmer"></div>'.repeat(6);

        try {
            let url = `/items?limit=24`;
            if (filter !== 'all') url += `&q=${filter}`;
            if (query) url += `&q=${query}`;

            const response = await fetch(url);
            const items = await response.json();

            feedGrid.innerHTML = '';
            items.forEach(item => {
                const card = createCard(item);
                feedGrid.appendChild(card);
            });
        } catch (error) {
            console.error('Error fetching items:', error);
            feedGrid.innerHTML = '<p class="error">Failed to load content. Please try again.</p>';
        }
    }

    function createCard(item) {
        const div = document.createElement('div');
        div.className = 'content-card glass';

        const typeClass = item.source_type === 'news' ? 'tag-news' : 'tag-reddit';
        const typeLabel = item.source_type === 'news' ? 'News' : 'Reddit';

        const metrics = item.engagement_metrics || {};
        const score = metrics.score !== undefined ? `<div class="metric"><i data-lucide="arrow-big-up"></i>${metrics.score}</div>` : '';
        const comments = metrics.num_comments !== undefined ? `<div class="metric"><i data-lucide="message-square"></i>${metrics.num_comments}</div>` : '';

        div.innerHTML = `
            <span class="card-tag ${typeClass}">${typeLabel}</span>
            <a href="${item.url}" target="_blank" class="card-title">${item.title}</a>
            <p class="card-summary">${item.summary || 'No summary available.'}</p>
            <div class="card-footer">
                <span class="card-source">${item.source_name}</span>
                <div class="card-metrics">
                    ${score}
                    ${comments}
                    <div class="metric"><i data-lucide="globe"></i>${item.country}</div>
                </div>
            </div>
        `;
        return div;
    }

    // Studio Logic
    let selectedCluster = null;

    async function renderStudio() {
        const response = await fetch('/trending');
        const trends = await response.json();
        const clusterList = document.getElementById('cluster-list');
        const btnGenerateCommentary = document.getElementById('btn-generate-commentary');
        const btnGeneratePackage = document.getElementById('btn-generate-package');

        clusterList.innerHTML = Object.entries(trends).map(([name, count]) => `
            <div class="cluster-item" data-cluster="${name}">
                <span class="cluster-name">${name}</span>
                <span class="cluster-count">${count} items</span>
            </div>
        `).join('');

        // Tab Switching
        const tabs = document.querySelectorAll('.tab-btn');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const target = tab.dataset.tab;
                document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                tab.classList.add('active');
                document.getElementById(`${target}-view`).classList.add('active');
            });
        });

        // Handle cluster selection
        document.querySelectorAll('.cluster-item').forEach(item => {
            item.addEventListener('click', async () => {
                document.querySelectorAll('.cluster-item').forEach(i => i.classList.remove('active'));
                item.classList.add('active');
                selectedCluster = item.dataset.cluster;
                btnGenerateCommentary.disabled = false;
                btnGeneratePackage.disabled = false;

                // Fetch existing commentary & package
                fetchCommentary(selectedCluster);
                fetchPackage(selectedCluster);
            });
        });

        btnGenerateCommentary.onclick = async () => {
            if (!selectedCluster) return;
            btnGenerateCommentary.disabled = true;
            btnGenerateCommentary.innerHTML = '<span>Generating...</span>';

            try {
                const response = await fetch(`/topics/${selectedCluster}/generate_angles`, { method: 'POST' });
                const data = await response.json();
                btnGenerateCommentary.disabled = false;
                btnGenerateCommentary.innerHTML = '<span>Generate Commentary</span>';
                if (data.angles) renderCommentary(data);
            } catch (e) {
                btnGenerateCommentary.disabled = false;
                btnGenerateCommentary.innerHTML = '<span>Generate Commentary</span>';
                console.error(e);
            }
        };

        btnGeneratePackage.onclick = async () => {
            if (!selectedCluster) return;
            btnGeneratePackage.disabled = true;
            btnGeneratePackage.innerHTML = '<span>Generating Package...</span>';

            try {
                const response = await fetch(`/topics/${selectedCluster}/generate_full_package`, { method: 'POST' });
                const data = await response.json();
                btnGeneratePackage.disabled = false;
                btnGeneratePackage.innerHTML = '<span>Generate Full Package</span>';
                if (data.safe_article) renderPackage(data);
            } catch (e) {
                btnGeneratePackage.disabled = false;
                btnGeneratePackage.innerHTML = '<span>Generate Full Package</span>';
                console.error(e);
            }
        };
    }

    async function fetchCommentary(cluster_id) {
        const display = document.getElementById('commentary-display');
        display.innerHTML = '<div class="loading-shimmer" style="height: 100px;"></div>'.repeat(3);
        try {
            const response = await fetch(`/topics/${cluster_id}/angles`);
            const data = await response.json();
            if (data && data.angles) renderCommentary(data);
            else display.innerHTML = '<p class="placeholder-text">No commentary generated yet. Click "Generate" to start.</p>';
        } catch (e) { display.innerHTML = '<p class="placeholder-text">Click "Generate" to start.</p>'; }
    }

    async function fetchPackage(cluster_id) {
        const display = document.getElementById('package-display');
        display.innerHTML = '<div class="loading-shimmer" style="height: 150px;"></div>'.repeat(2);
        try {
            const response = await fetch(`/topics/${cluster_id}/package`);
            const data = await response.json();
            if (data && data.safe_article) renderPackage(data);
            else display.innerHTML = '<p class="placeholder-text">No package generated. Click "Generate Full Package" to start.</p>';
        } catch (e) { display.innerHTML = '<p class="placeholder-text">Click "Generate Full Package" to start.</p>'; }
    }

    function renderCommentary(data) {
        const display = document.getElementById('commentary-display');
        const anglesHtml = data.angles.map(angle => `
            <div class="angle-card">
                <div class="angle-type">${angle.type}</div>
                <div class="angle-content">${angle.content}</div>
            </div>
        `).join('');
        display.innerHTML = `
            ${anglesHtml}
            <div class="facebook-card">
                <div class="facebook-header">
                    <i data-lucide="facebook"></i>
                    <span>Strongest Angle (Facebook Ready)</span>
                </div>
                <div class="facebook-content">${data.strongest_angle_html}</div>
            </div>
        `;
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    function renderPackage(data) {
        const display = document.getElementById('package-display');

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

    // Admin Logic
    async function renderAdmin() {
        const response = await fetch('/items?limit=1'); // Hack to get total from header if we had it, but for now just mock or fetch a count
        document.getElementById('stat-total-items').textContent = '470+'; // Mock for now

        const sourceListUi = document.getElementById('source-list-ui');
        // This would ideally come from an /admin/sources endpoint
        sourceListUi.innerHTML = `
            <li>CBC News - Politics <span class="badge active">Active</span></li>
            <li>The Hindu - National <span class="badge active">Active</span></li>
            <li>r/CanadaPolitics <span class="badge active">Active</span></li>
        `;
    }

    // Event Listeners
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

    // Initialize
    navigate('dashboard');
});
