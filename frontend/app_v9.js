document.addEventListener('DOMContentLoaded', () => {

    // --- API Configuration ---
    const API_BASE = 'http://localhost:8000';

    // --- Theme Engine Initialization ---
    const themes = {
        'ocean': { primary: '#3b82f6', secondary: '#8b5cf6', accent: '#06b6d4', light: '#60a5fa' },
        'emerald': { primary: '#10b981', secondary: '#059669', accent: '#34d399', light: '#6ee7b7' },
        'rose': { primary: '#f43f5e', secondary: '#e11d48', accent: '#fb7185', light: '#fda4af' },
        'amber': { primary: '#f59e0b', secondary: '#d97706', accent: '#fbbf24', light: '#fcd34d' },
        'amethyst': { primary: '#8b5cf6', secondary: '#c026d3', accent: '#d946ef', light: '#e879f9' }
    };

    const root = document.documentElement;
    const themeBtns = document.querySelectorAll('.theme-btn');

    function applyTheme(themeName) {
        if (!themes[themeName]) return;
        const palette = themes[themeName];

        root.style.setProperty('--primary', palette.primary);
        root.style.setProperty('--secondary', palette.secondary);
        root.style.setProperty('--accent', palette.accent);
        root.style.setProperty('--primary-light', palette.light);

        themeBtns.forEach(b => b.classList.remove('active'));
        const activeBtn = document.querySelector(`.theme-btn[data-theme="${themeName}"]`);
        if (activeBtn) activeBtn.classList.add('active');

        localStorage.setItem('matchai-theme', themeName);
    }

    themeBtns.forEach(btn => {
        btn.addEventListener('click', (e) => applyTheme(e.currentTarget.getAttribute('data-theme')));
    });

    const savedTheme = localStorage.getItem('matchai-theme');
    if (savedTheme) applyTheme(savedTheme);

    // ═══════════════════════════════════════════
    // MODE SWITCHING: Landing ↔ App
    // ═══════════════════════════════════════════

    const navLandingLinks = document.getElementById('nav-landing-links');
    const navAppLinks = document.getElementById('nav-app-links');
    const topbarLandingActions = document.getElementById('topbar-landing-actions');
    const topbarAppActions = document.getElementById('topbar-app-actions');
    const viewLanding = document.getElementById('view-landing');
    const mainScroll = document.getElementById('main-scroll');

    function switchToApp(targetView) {
        // Switch topbar nav
        navLandingLinks.classList.add('hidden');
        navAppLinks.classList.remove('hidden');
        topbarLandingActions.classList.add('hidden');
        topbarAppActions.classList.remove('hidden');

        // Switch views
        document.querySelectorAll('.page-view').forEach(v => {
            v.classList.add('hidden');
            v.classList.remove('active-view');
        });
        const target = document.getElementById(targetView || 'view-dashboard');
        if (target) {
            target.classList.remove('hidden');
            target.classList.add('active-view');
        }

        // Update app nav active state
        document.querySelectorAll('#nav-app-links .app-nav-item').forEach(n => n.classList.remove('active'));
        const activeNav = document.querySelector(`#nav-app-links [data-target="${targetView || 'view-dashboard'}"]`);
        if (activeNav) activeNav.classList.add('active');

        if ((targetView || 'view-dashboard') === 'view-analytics') renderChart();
        if (targetView === 'view-history') renderHistoryView();
    }

    function switchToLanding() {
        // Switch topbar nav
        navLandingLinks.classList.remove('hidden');
        navAppLinks.classList.add('hidden');
        topbarLandingActions.classList.remove('hidden');
        topbarAppActions.classList.add('hidden');

        // Switch views
        document.querySelectorAll('.page-view').forEach(v => {
            v.classList.add('hidden');
            v.classList.remove('active-view');
        });
        viewLanding.classList.remove('hidden');
        viewLanding.classList.add('active-view');

        // Reset landing nav active state
        document.querySelectorAll('#nav-landing-links .app-nav-item').forEach(n => n.classList.remove('active'));
        const homeLink = document.querySelector('#nav-landing-links [data-scroll="landing-hero"]');
        if (homeLink) homeLink.classList.add('active');

        // Scroll back to top
        if (mainScroll) mainScroll.scrollTop = 0;
    }

    // Wire: all "Try it out" buttons → switchToApp
    document.querySelectorAll('#topbar-try-btn, .hero-try-btn').forEach(btn => {
        btn.addEventListener('click', (e) => { e.preventDefault(); switchToApp('view-dashboard'); });
    });

    // Wire: "Home" in app nav → switchToLanding
    const navHomeBtn = document.getElementById('nav-home-btn');
    if (navHomeBtn) navHomeBtn.addEventListener('click', (e) => { e.preventDefault(); switchToLanding(); });

    // Wire: logo → switchToLanding
    const brandLink = document.getElementById('brand-home-link');
    if (brandLink) brandLink.addEventListener('click', (e) => { e.preventDefault(); switchToLanding(); });

    // Wire: "Learn more" + landing scroll links
    document.querySelectorAll('[data-scroll]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('data-scroll');
            const targetEl = document.getElementById(targetId);
            if (targetEl) targetEl.scrollIntoView({ behavior: 'smooth' });
        });
    });

    // Wire: landing nav items (Home, How It Works, About)
    document.querySelectorAll('#nav-landing-links .app-nav-item').forEach(item => {
        item.addEventListener('click', () => {
            document.querySelectorAll('#nav-landing-links .app-nav-item').forEach(n => n.classList.remove('active'));
            item.classList.add('active');
        });
    });

    // --- Search Functionality ---
    const searchInput = document.getElementById('run-search-input');
    const searchDropdown = document.getElementById('search-dropdown');

    if (searchInput && searchDropdown) {
        const getScoreColor = (score) => score >= 70 ? 'var(--success)' : score >= 40 ? 'var(--warning)' : 'var(--danger)';

        function renderSearchResults(query) {
            const history = JSON.parse(localStorage.getItem('matchai-history')) || [];
            const results = query
                ? history.filter(item => item.job.toLowerCase().includes(query))
                : history.slice(0, 8);

            if (results.length === 0) {
                searchDropdown.innerHTML = query
                    ? '<div style="padding: 12px; color: var(--text-secondary); text-align: center; font-size: 0.9rem;">No saved runs found</div>'
                    : '<div style="padding: 12px; color: var(--text-secondary); text-align: center; font-size: 0.9rem;">No recent runs yet</div>';
                searchDropdown.classList.remove('hidden');
                return;
            }

            const header = !query
                ? '<div style="padding: 8px 12px 4px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: var(--text-secondary); opacity: 0.7;">Recent Runs</div>'
                : '';

            searchDropdown.innerHTML = header + results.slice(0, 10).map(item => `
                <div class="search-result-item" data-run-id="${item.runId || ''}" style="padding: 10px 12px; display: flex; justify-content: space-between; align-items: center; border-radius: 8px; cursor: pointer; transition: background 0.2s ease;">
                    <div style="display: flex; flex-direction: column; gap: 4px; overflow: hidden; padding-right: 10px;">
                        <span style="font-size: 0.95rem; font-weight: 500; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${item.job}</span>
                        <span style="font-size: 0.8rem; color: var(--text-secondary);">${item.date || ''}</span>
                    </div>
                    <span style="background: ${getScoreColor(item.score)}20; color: ${getScoreColor(item.score)}; padding: 3px 8px; border-radius: 99px; font-weight: 700; font-size: 0.8rem; border: 1px solid ${getScoreColor(item.score)}40; flex-shrink: 0;">${item.score}%</span>
                </div>
            `).join('');

            searchDropdown.classList.remove('hidden');

            searchDropdown.querySelectorAll('.search-result-item').forEach(el => {
                el.addEventListener('mouseenter', () => el.style.background = 'rgba(255,255,255,0.05)');
                el.addEventListener('mouseleave', () => el.style.background = 'transparent');
                el.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const runId = el.dataset.runId;
                    searchDropdown.classList.add('hidden');
                    searchInput.value = '';
                    switchToApp('view-history');
                    setTimeout(() => {
                        const target = runId
                            ? document.querySelector(`#history-list [data-run-id="${runId}"]`)
                            : document.querySelector('#history-list .history-run-card');
                        if (target) {
                            target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            // Auto-expand so the user can see the full card
                            target.dataset.expanded = 'true';
                            const preview = target.querySelector('.history-summary-preview');
                            const full = target.querySelector('.history-summary-full');
                            const skillsPrev = target.querySelector('.history-skills-preview');
                            const skillsFull = target.querySelector('.history-skills-full');
                            const chevron = target.querySelector('.history-chevron');
                            if (preview) preview.style.display = 'none';
                            if (full) full.style.display = '';
                            if (skillsPrev) skillsPrev.style.display = 'none';
                            if (skillsFull) skillsFull.style.display = 'flex';
                            if (chevron) chevron.style.transform = 'rotate(180deg)';
                            // Highlight ring
                            target.style.transition = 'box-shadow 0.4s ease';
                            target.style.boxShadow = '0 0 0 2px var(--accent), 0 8px 32px rgba(6,182,212,0.25)';
                            setTimeout(() => { target.style.boxShadow = ''; }, 2500);
                        }
                    }, 150);
                });
            });
        }

        // Show recent runs on focus (before typing)
        searchInput.addEventListener('focus', () => {
            renderSearchResults('');
        });

        // Filter on input
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            renderSearchResults(query);
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
                searchDropdown.classList.add('hidden');
            }
        });
    }

    // ═══════════════════════════════════════════
    // NOTIFICATION SYSTEM
    // ═══════════════════════════════════════════

    const bellBtn = document.getElementById('bell-btn');
    const bellIcon = document.getElementById('bell-icon');
    const notifDot = document.getElementById('notif-dot');
    const notifDropdown = document.getElementById('notif-dropdown');
    const notifList = document.getElementById('notif-list');
    const notifEmpty = document.getElementById('notif-empty');

    function getNotifs() {
        return JSON.parse(localStorage.getItem('matchai-notifications')) || [];
    }

    function saveNotifs(arr) {
        localStorage.setItem('matchai-notifications', JSON.stringify(arr.slice(0, 30)));
    }

    function updateBadge() {
        if (!notifDot) return;
        const unread = getNotifs().filter(n => !n.read).length;
        if (unread > 0) {
            notifDot.classList.remove('hidden');
        } else {
            notifDot.classList.add('hidden');
        }
    }

    function pushNotification(title, body) {
        const notifs = getNotifs();
        notifs.unshift({
            id: Date.now(),
            title,
            body,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            read: false
        });
        saveNotifs(notifs);
        updateBadge();
    }

    function renderNotifDropdown() {
        if (!notifList || !notifEmpty) return;
        const notifs = getNotifs();
        if (notifs.length === 0) {
            notifList.innerHTML = '';
            notifEmpty.style.display = '';
            return;
        }
        notifEmpty.style.display = 'none';
        notifList.innerHTML = notifs.map(n => `
            <div class="notif-item ${n.read ? 'read' : 'unread'}">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:8px; margin-bottom:3px;">
                    <span class="notif-title">${n.title}</span>
                    <span class="notif-time">${n.time}</span>
                </div>
                <p class="notif-body">${n.body}</p>
            </div>
        `).join('');
    }

    if (bellBtn) {
        bellBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isOpen = !notifDropdown.classList.contains('hidden');
            // Close search dropdown if open
            if (searchDropdown) searchDropdown.classList.add('hidden');
            notifDropdown.classList.toggle('hidden', isOpen);
            if (!isOpen) {
                renderNotifDropdown();
                // Mark all as read
                const notifs = getNotifs().map(n => ({ ...n, read: true }));
                saveNotifs(notifs);
                updateBadge();
                // Filled bell while open
                if (bellIcon) {
                    bellIcon.className = 'fa-solid fa-bell';
                }
            } else {
                if (bellIcon) bellIcon.className = 'fa-regular fa-bell';
            }
        });

        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!bellBtn.contains(e.target)) {
                notifDropdown.classList.add('hidden');
                if (bellIcon) bellIcon.className = 'fa-regular fa-bell';
            }
        });
    }

    const notifClearBtn = document.getElementById('notif-clear-btn');
    if (notifClearBtn) {
        notifClearBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            localStorage.removeItem('matchai-notifications');
            renderNotifDropdown();
            updateBadge();
        });
    }

    // Initialise badge from persisted notifs
    updateBadge();

    // --- Light / Dark Mode Toggle ---
    const lightModeToggle = document.getElementById('light-mode-toggle');

    function applyLightMode(isLight) {
        if (isLight) {
            document.body.classList.add('light-mode');
        } else {
            document.body.classList.remove('light-mode');
        }
        if (lightModeToggle) lightModeToggle.checked = isLight;
        localStorage.setItem('matchai-light-mode', isLight ? '1' : '0');
    }

    if (lightModeToggle) {
        lightModeToggle.addEventListener('change', () => applyLightMode(lightModeToggle.checked));
    }

    // Restore saved preference on load
    if (localStorage.getItem('matchai-light-mode') === '1') {
        applyLightMode(true);
    }


    // --- App Nav Item Routing ---
    document.querySelectorAll('#nav-app-links .app-nav-item[data-target]').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            switchToApp(item.getAttribute('data-target'));
        });
    });

    // Match Details Routing (Back Button)
    const backToResultsBtn = document.getElementById('back-to-results-btn');
    if (backToResultsBtn) {
        backToResultsBtn.addEventListener('click', () => {
            document.getElementById('view-match-details').classList.add('hidden');
            document.getElementById('view-match-details').classList.remove('active-view');

            document.getElementById('view-dashboard').classList.remove('hidden');
            document.getElementById('view-dashboard').classList.add('active-view');

            document.querySelectorAll('.app-nav-item').forEach(n => n.classList.remove('active'));
            document.querySelector('.app-nav-item[data-target="view-dashboard"]').classList.add('active');
        });
    }

    // Connect Details Skill Badges
    const detailsInlineView = document.getElementById('details-inline-skills-view');
    const detailsMatchedList = document.getElementById('details-matched-list');
    const detailsMissingList = document.getElementById('details-missing-list');
    const detailsMatchedToggle = document.getElementById('details-matched-toggle');
    const detailsMissingToggle = document.getElementById('details-missing-toggle');

    if (detailsMatchedToggle && detailsMissingToggle) {
        detailsMatchedToggle.addEventListener('click', () => {
            if (detailsInlineView.classList.contains('hidden') || (!detailsInlineView.classList.contains('hidden') && detailsMatchedList.classList.contains('hidden'))) {
                detailsInlineView.classList.remove('hidden');
                detailsMatchedList.classList.remove('hidden');
                detailsMissingList.classList.add('hidden');
            } else {
                detailsInlineView.classList.add('hidden');
            }
        });

        detailsMissingToggle.addEventListener('click', () => {
            if (detailsInlineView.classList.contains('hidden') || (!detailsInlineView.classList.contains('hidden') && detailsMissingList.classList.contains('hidden'))) {
                detailsInlineView.classList.remove('hidden');
                detailsMissingList.classList.remove('hidden');
                detailsMatchedList.classList.add('hidden');
            } else {
                detailsInlineView.classList.add('hidden');
            }
        });
    }

    // CV Elements
    const cvDropZone = document.getElementById('cv-drop-zone');
    const cvFileInput = document.getElementById('cv-file-input');
    const cvBrowseBtn = document.getElementById('cv-browse-btn');
    const cvFileList = document.getElementById('cv-file-list');

    // Jobs Elements
    const jobDropZone = document.getElementById('job-drop-zone');
    const jobFileInput = document.getElementById('job-file-input');
    const jobBrowseBtn = document.getElementById('job-browse-btn');
    const jobFileList = document.getElementById('job-file-list');

    // Flow Elements
    const uploadSection = document.getElementById('upload-section');
    const loadingSection = document.getElementById('loading-section');
    const resultsSection = document.getElementById('results-section');
    const matchesContainer = document.getElementById('matches-container');
    const compareBtn = document.getElementById('compare-btn');
    const uploadAnotherBtn = document.getElementById('upload-another-btn');
    const scrollIndicator = document.getElementById('scroll-to-upload');
    const contentScroll = document.querySelector('.content-scroll');


    // State
    const validExtensions = ['.txt', '.pdf', '.docx'];
    let stateCvFile = null;
    let stateJobFiles = [];
    let stateResumes = []; // tracks all CVs uploaded this session
    let stateSessionResults = []; // tracks results from current session for analytics

    // Input mode: 'file' or 'text'
    let inputMode = 'file';
    let textJobCounter = 1;

    // Analytics domain filter state
    let activeAnalyticsDomain = null;

    // ── Input Mode Toggle ───────────────────────────────────────────────────
    const modeFileBtn = document.getElementById('mode-file-btn');
    const modeTextBtn = document.getElementById('mode-text-btn');
    const fileModeSection = document.getElementById('file-mode-section');
    const pasteModeSection = document.getElementById('paste-mode-section');

    function switchInputMode(mode) {
        inputMode = mode;
        const isFile = mode === 'file';

        modeFileBtn.style.background = isFile ? 'var(--primary)' : 'transparent';
        modeFileBtn.style.color = isFile ? 'white' : 'var(--text-secondary)';
        modeTextBtn.style.background = isFile ? 'transparent' : 'var(--primary)';
        modeTextBtn.style.color = isFile ? 'var(--text-secondary)' : 'white';

        fileModeSection.classList.toggle('hidden', !isFile);
        pasteModeSection.classList.toggle('hidden', isFile);

        if (!isFile && document.getElementById('job-text-items').children.length === 0) {
            addJobTextEntry();
        }
        updateCompareButton();
    }

    if (modeFileBtn) modeFileBtn.addEventListener('click', () => switchInputMode('file'));
    if (modeTextBtn) modeTextBtn.addEventListener('click', () => switchInputMode('text'));

    // ── Paste-mode CV drop zone — shares handleCvUpload() and renderCvFile() with file mode ──
    const cvDropZonePaste = document.getElementById('cv-drop-zone-paste');
    const cvFileInputPaste = document.getElementById('cv-file-input-paste');
    const cvBrowseBtnPaste = document.getElementById('cv-browse-btn-paste');

    if (cvBrowseBtnPaste) cvBrowseBtnPaste.addEventListener('click', () => cvFileInputPaste?.click());
    if (cvFileInputPaste) {
        cvFileInputPaste.addEventListener('change', (e) => {
            if (e.target.files.length) handleCvUpload(e.target.files[0]);
        });
    }
    if (cvDropZonePaste) {
        cvDropZonePaste.addEventListener('dragover', (e) => { e.preventDefault(); cvDropZonePaste.classList.add('dragover'); });
        cvDropZonePaste.addEventListener('dragleave', () => cvDropZonePaste.classList.remove('dragover'));
        cvDropZonePaste.addEventListener('drop', (e) => {
            e.preventDefault();
            cvDropZonePaste.classList.remove('dragover');
            if (e.dataTransfer.files.length) handleCvUpload(e.dataTransfer.files[0]);
        });
    }

    // ── Add/remove JD text entries ──────────────────────────────────────────
    function addJobTextEntry() {
        const items = document.getElementById('job-text-items');
        if (!items || items.children.length >= 5) {
            if (items && items.children.length >= 5) showToast('Maximum 5 job descriptions allowed.', 'warning');
            return;
        }
        const idx = ++textJobCounter;
        const entry = document.createElement('div');
        entry.className = 'job-text-entry';
        entry.style.cssText = 'display:flex; flex-direction:column; gap:8px; background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:12px;';
        entry.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <input class="job-label-input" type="text" value="Job ${idx}" style="background:transparent; border:none; color:var(--text-primary); font-weight:600; font-size:0.95rem; font-family:inherit; outline:none; width:calc(100% - 30px);">
                <button class="remove-text-job-btn" style="background:none; border:none; color:var(--text-secondary); cursor:pointer; font-size:0.85rem; flex-shrink:0;"><i class="fa-solid fa-trash-can"></i></button>
            </div>
            <textarea class="job-text-input" placeholder="Paste job description here..." style="width:100%; min-height:120px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); border-radius:8px; padding:10px; color:var(--text-primary); font-family:inherit; font-size:0.88rem; resize:vertical; outline:none; line-height:1.6; box-sizing:border-box;"></textarea>
        `;
        entry.querySelector('.remove-text-job-btn').addEventListener('click', () => {
            entry.remove();
            updateCompareButton();
        });
        entry.querySelector('.job-text-input').addEventListener('input', updateCompareButton);
        items.appendChild(entry);
        updateCompareButton();
    }

    const addJobTextBtn = document.getElementById('add-job-text-btn');
    if (addJobTextBtn) addJobTextBtn.addEventListener('click', addJobTextEntry);

    
    // Enable/Disable button
    function updateCompareButton() {
        let ready = false;
        if (inputMode === 'file') {
            ready = stateCvFile !== null && stateJobFiles.length > 0;
        } else {
            const hasJob = Array.from(document.querySelectorAll('.job-text-input'))
                .some(t => t.value.trim().length > 50);
            ready = stateCvFile !== null && hasJob;
        }
        compareBtn.disabled = !ready;
    }

    function checkExtension(fileName) {
        return validExtensions.some(ext => fileName.toLowerCase().endsWith(ext));
    }

    function getFileIcon(fileName) {
        if (fileName.toLowerCase().endsWith('.pdf')) return 'fa-file-pdf';
        if (fileName.toLowerCase().endsWith('.docx') || fileName.toLowerCase().endsWith('.doc')) return 'fa-file-word';
        return 'fa-file-lines';
    }

    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    // ── Inline toast notifications (replaces alert) ──
    function showToast(message, type = 'error') {
        const existing = document.getElementById('matchai-toast');
        if (existing) existing.remove();
        const color = type === 'error' ? 'var(--danger)' : type === 'warning' ? 'var(--warning)' : 'var(--success)';
        const icon  = type === 'error' ? 'fa-circle-xmark' : type === 'warning' ? 'fa-triangle-exclamation' : 'fa-circle-check';
        const toast = document.createElement('div');
        toast.id = 'matchai-toast';
        toast.style.cssText = `position:fixed; bottom:32px; left:50%; transform:translateX(-50%) translateY(20px); background:var(--bg-base); border:1px solid ${color}; color:var(--text-primary); padding:13px 22px; border-radius:12px; font-size:0.9rem; font-weight:500; display:flex; align-items:center; gap:10px; z-index:9999; box-shadow:0 8px 30px rgba(0,0,0,0.2); opacity:0; transition:opacity 0.25s ease, transform 0.25s ease; pointer-events:none;`;
        toast.innerHTML = `<i class="fa-solid ${icon}" style="color:${color}; font-size:1rem;"></i> ${message}`;
        document.body.appendChild(toast);
        requestAnimationFrame(() => { toast.style.opacity = '1'; toast.style.transform = 'translateX(-50%) translateY(0)'; });
        setTimeout(() => {
            toast.style.opacity = '0'; toast.style.transform = 'translateX(-50%) translateY(10px)';
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }

    function isValidUrl(string) {
        try {
            new URL(string);
            return true;
        } catch (_) {
            return false;
        }
    }

    // --- CV Upload Handlers ---
    cvDropZone.addEventListener('dragover', (e) => { e.preventDefault(); cvDropZone.classList.add('dragover'); });
    cvDropZone.addEventListener('dragleave', (e) => { e.preventDefault(); cvDropZone.classList.remove('dragover'); });
    cvDropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        cvDropZone.classList.remove('dragover');
        cvDropZone.classList.add('fast-pulse');
        setTimeout(() => cvDropZone.classList.remove('fast-pulse'), 400);
        if (e.dataTransfer.files.length) {
            handleCvUpload(e.dataTransfer.files[0]);
        }
    });
    cvBrowseBtn.addEventListener('click', () => cvFileInput.click());
    cvFileInput.addEventListener('change', (e) => {
        if (e.target.files.length) handleCvUpload(e.target.files[0]);
    });

    function handleCvUpload(file) {
        if (!checkExtension(file.name)) {
            showToast('Please upload a .txt, .pdf, or .docx CV file.', 'error');
            return;
        }
        stateCvFile = file;

        // Enforce strict 1-CV limit
        stateResumes = [{
            name: file.name,
            size: file.size,
            addedAt: new Date(),
            isActive: true
        }];
        renderResumesList();

        renderCvFile();
        updateCompareButton();
    }

    function renderCvFile() {
        const fileHTML = stateCvFile ? `
            <div class="file-item">
                <div class="file-info">
                    <i class="fa-solid ${getFileIcon(stateCvFile.name)} file-icon" style="color:var(--primary-light)"></i>
                    <div class="file-details">
                        <h5>${stateCvFile.name}</h5>
                        <span>${formatBytes(stateCvFile.size)}</span>
                    </div>
                </div>
                <button class="remove-file-btn remove-cv-btn"><i class="fa-solid fa-trash-can"></i></button>
            </div>
        ` : '';

        // Update both panels
        [cvFileList, document.getElementById('cv-file-list-paste')].forEach(el => {
            if (!el) return;
            el.innerHTML = fileHTML;
            if (stateCvFile) {
                el.querySelector('.remove-cv-btn')?.addEventListener('click', () => {
                    stateCvFile = null;
                    cvFileInput.value = '';
                    if (cvFileInputPaste) cvFileInputPaste.value = '';
                    renderCvFile();
                    updateCompareButton();
                });
            }
        });
    }

    // --- Jobs Upload Handlers ---
    jobDropZone.addEventListener('dragover', (e) => { e.preventDefault(); jobDropZone.classList.add('dragover'); });
    jobDropZone.addEventListener('dragleave', (e) => { e.preventDefault(); jobDropZone.classList.remove('dragover'); });
    jobDropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        jobDropZone.classList.remove('dragover');
        jobDropZone.classList.add('fast-pulse');
        setTimeout(() => jobDropZone.classList.remove('fast-pulse'), 400);
        if (e.dataTransfer.files.length) {
            handleJobsUpload(e.dataTransfer.files);
        }
    });
    jobBrowseBtn.addEventListener('click', () => jobFileInput.click());
    jobFileInput.addEventListener('change', (e) => {
        if (e.target.files.length) handleJobsUpload(e.target.files);
    });

    function handleJobsUpload(files) {
        const validFiles = Array.from(files).filter(f => checkExtension(f.name));
        if (validFiles.length === 0) {
            showToast('Please upload valid job description files (.txt, .pdf, .docx).', 'error');
            return;
        }
        if (stateJobFiles.length + validFiles.length > 5) {
            showToast('You can only compare up to 5 target domains at a time.', 'warning');
            return;
        }

        validFiles.forEach(vf => {
            if (!stateJobFiles.find(existing => existing.name === vf.name)) {
                stateJobFiles.push(vf);
            }
        });

        renderJobFiles();
        updateCompareButton();
    }


    function renderJobFiles() {
        jobFileList.innerHTML = '';

        // Render physical files
        stateJobFiles.forEach((file, index) => {
            const el = document.createElement('div');
            el.className = 'file-item';
            el.innerHTML = `
                <div class="file-info">
                    <i class="fa-solid ${getFileIcon(file.name)} file-icon" style="color:var(--accent)"></i>
                    <div class="file-details">
                        <h5>${file.name}</h5>
                        <span>${formatBytes(file.size)}</span>
                    </div>
                </div>
                <button class="remove-file-btn remove-job-btn" data-index="${index}"><i class="fa-solid fa-trash-can"></i></button>
            `;
            jobFileList.appendChild(el);
        });



        document.querySelectorAll('.remove-job-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const idx = parseInt(e.currentTarget.getAttribute('data-index'));
                stateJobFiles.splice(idx, 1);
                jobFileInput.value = '';
                renderJobFiles();
                updateCompareButton();
            });
        });
    }

    // --- Analyze API Call ---
    compareBtn.addEventListener('click', async () => {
        uploadSection.classList.add('hidden');
        loadingSection.classList.remove('hidden');

        try {
            let data;

            if (inputMode === 'file') {
                const formData = new FormData();
                formData.append('cv_file', stateCvFile);
                stateJobFiles.forEach(file => formData.append('job_files', file));

                const response = await fetch(`${API_BASE}/compare/upload`, {
                    method: 'POST',
                    body: formData
                });
                if (!response.ok) {
                    const errData = await response.json();
                    throw new Error(errData.detail || "Error connecting to the API.");
                }
                data = await response.json();

            } else {
                const jobs = Array.from(document.querySelectorAll('.job-text-entry')).map((el, i) => ({
                    job_id: (el.querySelector('.job-label-input')?.value || `Job ${i + 1}`).trim(),
                    description: (el.querySelector('.job-text-input')?.value || '').trim()
                })).filter(j => j.description.length > 0);

                const formData = new FormData();
                formData.append('cv_file', stateCvFile);
                formData.append('jobs_json', JSON.stringify(jobs));

                const response = await fetch(`${API_BASE}/compare/mixed`, {
                    method: 'POST',
                    body: formData
                });
                if (!response.ok) {
                    const errData = await response.json();
                    throw new Error(errData.detail || "Error connecting to the API.");
                }
                data = await response.json();
            }

            renderResults(data);
        } catch (error) {
            console.error("Comparison Error:", error);
            showToast('Failed to analyze: ' + error.message, 'error');
            loadingSection.classList.add('hidden');
            uploadSection.classList.remove('hidden');
        }
    });

    // Reset Form
    uploadAnotherBtn.addEventListener('click', () => {
        resultsSection.classList.add('hidden');
        uploadSection.classList.remove('hidden');

        stateCvFile = null;
        stateJobFiles = [];
        cvFileInput.value = '';
        jobFileInput.value = '';
        renderCvFile();
        renderJobFiles();
        updateCompareButton();
    });

    // --- Resumes List Renderer ---
    function renderResumesList() {
        const emptyEl = document.getElementById('resumes-empty');
        const listEl = document.getElementById('resumes-list');
        if (!emptyEl || !listEl) return;

        if (stateResumes.length === 0) {
            emptyEl.style.display = 'block';
            listEl.innerHTML = '';
            return;
        }

        emptyEl.style.display = 'none';
        listEl.innerHTML = '';

        stateResumes.forEach((resume, idx) => {
            const dateStr = resume.addedAt.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
            const card = document.createElement('div');
            card.className = 'upload-card glass-panel';
            card.style.cssText = `padding: 20px 24px; display:flex; align-items:center; gap:18px; ${resume.isActive ? 'border-left: 3px solid var(--primary-light);' : 'opacity: 0.75;'}`;
            card.innerHTML = `
                <i class="fa-solid ${getFileIcon(resume.name)} file-icon" style="color:${resume.isActive ? 'var(--primary-light)' : 'var(--text-secondary)'}; font-size: 1.6rem; flex-shrink:0;"></i>
                <div style="flex-grow:1; min-width:0;">
                    <h5 style="margin:0 0 3px 0; font-size: 1rem; font-weight: 700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${resume.name}</h5>
                    <span style="font-size: 0.8rem; color: var(--text-secondary);">Added ${dateStr} · ${formatBytes(resume.size)}${resume.isActive ? ' · <span style="color:var(--primary-light); font-weight:600;">Active</span>' : ''}</span>
                </div>
                ${!resume.isActive ? `<button class="secondary-btn btn-sm set-active-resume-btn" data-idx="${idx}" style="flex-shrink:0;"><i class="fa-solid fa-fingerprint"></i> Set Active</button>` : `<span style="font-size:0.75rem; color:var(--primary-light); letter-spacing:1px; text-transform:uppercase; font-weight:700; flex-shrink:0;">✓ In Use</span>`}
            `;
            listEl.appendChild(card);
        });

        document.querySelectorAll('.set-active-resume-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const idx = parseInt(e.currentTarget.getAttribute('data-idx'));
                stateResumes.forEach((r, i) => r.isActive = (i === idx));
                renderResumesList();
            });
        });
    }

    function cleanJobId(jobId) {
        return jobId.split(/[_-]/).map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
    }

    // Converts LLM text with "- " bullets or "1. " numbered lists into styled HTML
    function formatAiText(text) {
        if (!text) return '';
        if (Array.isArray(text)) text = text.join('\n');
        const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
        let html = '';
        let inList = false;
        let listType = null;

        lines.forEach(line => {
            if (/^[-•]\s+/.test(line)) {
                if (!inList || listType !== 'ul') {
                    if (inList) html += `</${listType}>`;
                    html += '<ul style="margin: 0; padding-left: 20px; display:flex; flex-direction:column; gap:6px;">';
                    inList = true; listType = 'ul';
                }
                html += `<li style="color:inherit">${line.replace(/^[-•]\s+/, '')}</li>`;
            } else if (/^\d+\.\s+/.test(line)) {
                if (!inList || listType !== 'ol') {
                    if (inList) html += `</${listType}>`;
                    html += '<ol style="margin: 0; padding-left: 20px; display:flex; flex-direction:column; gap:6px;">';
                    inList = true; listType = 'ol';
                }
                html += `<li style="color:inherit">${line.replace(/^\d+\.\s+/, '')}</li>`;
            } else {
                if (inList) { html += `</${listType}>`; inList = false; listType = null; }
                html += `<p style="margin: 0 0 8px 0;">${line}</p>`;
            }
        });

        if (inList) html += `</${listType}>`;
        return html;
    }

    // Title-cases a skill and expands known acronyms
    const acronymMap = {
        'ehr': 'Electronic Health Records (EHR)',
        'emr': 'Electronic Medical Records (EMR)',
        'gp': 'General Practitioner (GP)',
        'cpr': 'CPR',
        'bls': 'BLS',
        'acls': 'ACLS',
        'hipaa': 'HIPAA',
        'gdpr': 'GDPR',
        'aws': 'AWS',
        'gcp': 'GCP',
        'api': 'API',
        'sql': 'SQL',
        'css': 'CSS',
        'html': 'HTML',
        'crm': 'CRM',
        'erp': 'ERP',
    };

    function formatSkillName(skill) {
        const lower = skill.toLowerCase().trim();
        if (acronymMap[lower]) return acronymMap[lower];
        // Title case
        return lower.replace(/\b\w/g, c => c.toUpperCase());
    }

    function getSkillMeta(skill) {
        const s = skill.toLowerCase();
        if (s.includes('data') || s.includes('excel') || s.includes('sql') || s.includes('analytic') || s.includes('python')) return { cat: 'Data & Analytics', icon: 'fa-database', color: '#3b82f6' };
        if (s.includes('seo') || s.includes('market') || s.includes('ad ') || s.includes('ads') || s.includes('hubspot') || s.includes('mailchimp') || s.includes('content') || s.includes('social')) return { cat: 'Marketing & Growth', icon: 'fa-bullhorn', color: '#10b981' };
        if (s.includes('web') || s.includes('wordpress') || s.includes('shopify') || s.includes('html') || s.includes('css') || s.includes('react') || s.includes('javascript') || s.includes('frontend')) return { cat: 'Web & Frontend', icon: 'fa-window-maximize', color: '#8b5cf6' };
        if (s.includes('node') || s.includes('backend') || s.includes('api') || s.includes('java ') || s.includes('c++')) return { cat: 'Backend & Systems', icon: 'fa-server', color: '#ef4444' };
        if (s.includes('test') || s.includes('optimiz') || s.includes('qa') || s.includes('quality')) return { cat: 'Testing & QA', icon: 'fa-flask', color: '#f59e0b' };
        if (s.includes('manage') || s.includes('lead') || s.includes('agile') || s.includes('scrum') || s.includes('project') || s.includes('strateg')) return { cat: 'Management & Strategy', icon: 'fa-sitemap', color: '#ec4899' };
        if (s.includes('ai ') || s.includes('machine') || s.includes('tensorflow') || s.includes('pytorch')) return { cat: 'AI & Machine Learning', icon: 'fa-microchip', color: '#06b6d4' };
        if (s.includes('git') || s.includes('docker') || s.includes('aws') || s.includes('cloud') || s.includes('azure') || s.includes('ci/cd')) return { cat: 'DevOps & Cloud', icon: 'fa-cloud', color: '#f97316' };
        return { cat: 'Industry Expertise', icon: 'fa-cube', color: '#94a3b8' };
    }

    function renderResults(data) {
        loadingSection.classList.add('hidden');
        resultsSection.classList.remove('hidden');
        matchesContainer.innerHTML = '';

        if (!data.matches || data.matches.length === 0) {
            matchesContainer.innerHTML = '<p class="text-secondary" style="padding: 20px; font-size: 1.2rem;">No optimal job matches constructed.</p>';
            return;
        }

        const template = document.getElementById('match-card-template');
        const currentSessionHistory = [];

        data.matches.forEach((match, index) => {
            const clone = template.content.cloneNode(true);
            const card = clone.querySelector('.match-card');
            card.style.animationDelay = `${index * 0.15}s`;

            const jobTitle = cleanJobId(match.job_id);
            clone.querySelector('.job-id').textContent = jobTitle;

            const gap = match.gap_analysis;

            // Core FAISS similarity mapping
            let percentScore = Math.max(0, match.similarity_score * 100);
            if (percentScore > 100) percentScore = 100;

            // Save to memory tracker
            const runLabel = stateCvFile
                ? (stateCvFile?.name || 'run').replace(/\.[^.]+$/, '').replace(/[_\-]+/g, ' ').replace(/\b\w/g, c => c.toUpperCase()).trim()
                : 'CV Run';
            currentSessionHistory.push({
                runId: `${Date.now()}_${index}`,
                job: jobTitle,
                score: Math.round(percentScore),
                date: new Date().toLocaleDateString(),
                matched: (gap && gap.matched_skills) ? gap.matched_skills : [],
                missing: (gap && gap.missing_skills) ? gap.missing_skills : [],
                skillsClean: (gap && gap.skills_source === 'llm'),
                runLabel,
                summary: match.llm_summary || ''
            });

            // Only save clean LLM skills to analytics — never dirty NLP fallback
            if (gap && gap.skills_source === 'llm' && gap.missing_skills && gap.missing_skills.length > 0) {
                const existingGaps = JSON.parse(localStorage.getItem('matchai-gap-skills')) || [];
                const updatedGaps = [...existingGaps, ...gap.missing_skills];
                localStorage.setItem('matchai-gap-skills', JSON.stringify(updatedGaps));
            }

            clone.querySelectorAll('.score-value').forEach(el => el.textContent = Math.round(percentScore));

            // Populate teaser — first sentence only, strip score % mentions
            let rawTeaser = match.llm_summary || "AI analysis complete. Open View Details for the full breakdown of your strengths and growth areas.";
            // Take only the first sentence
            const firstSentence = rawTeaser.split(/(?<=[.!?])\s/)[0] || rawTeaser;
            // Remove "match percentage of X%" or "X% match" style phrases
            let teaser = firstSentence.replace(/\b(with\s+a\s+match\s+percentage\s+of\s+[\d.]+%|[\d.]+%\s+match)\b/gi, '').replace(/\s{2,}/g, ' ').trim();
            if (teaser.length > 150) teaser = teaser.substring(0, 147) + '…';
            const teaserEl = clone.querySelector('.card-teaser-text');
            if (teaserEl) teaserEl.textContent = teaser;


            // Populate Skills Previews
            const matchedContainer = clone.querySelector('.matched-chips-container');
            const missingContainer = clone.querySelector('.missing-chips-container');
            const matchedSkills = (gap && gap.matched_skills) ? gap.matched_skills : [];
            const missingSkills = (gap && gap.missing_skills) ? gap.missing_skills : [];

            // Helper to render up to 3 chips
            const renderChips = (container, skills, isStrength) => {
                if (!container) return;
                if (skills.length === 0) {
                    container.innerHTML = '<span style="color:var(--text-secondary); font-size: 0.85rem;">None</span>';
                    return;
                }
                const toShow = skills.slice(0, 4);
                toShow.forEach(skill => {
                    const el = document.createElement('span');
                    el.className = isStrength ? 'chip green' : 'chip amber';
                    el.textContent = formatSkillName(skill);
                    container.appendChild(el);
                });
                if (skills.length > 4) {
                    const el = document.createElement('span');
                    el.className = 'chip';
                    el.style.opacity = '0.6';
                    el.textContent = `+${skills.length - 4} more`;
                    container.appendChild(el);
                }
            };

            renderChips(matchedContainer, matchedSkills, true);
            renderChips(missingContainer, missingSkills, false);

            // Animate SVG Ring and Calculate Label
            setTimeout(() => {
                const circle = card.querySelector('.progress-ring__circle');
                // Semi-circle arc radius = 47 (from template path M 8,68 A 47,47...)
                const circumference = Math.PI * 47;
                const offset = circumference - (percentScore / 100) * circumference;
                circle.style.strokeDasharray = circumference;
                circle.style.strokeDashoffset = offset;

                let fitLabel = match.fit_category || "moderate fit";
                let fitColor;

                if (fitLabel === "strong fit") {
                    fitColor = "#34d399";
                } else if (fitLabel === "moderate fit") {
                    fitColor = "#fbbf24";
                } else {
                    fitColor = "#f87171";
                }

                // Arc stroke color + glow
                circle.style.stroke = fitColor;
                circle.style.filter = `drop-shadow(0 0 6px ${fitColor}50)`;

                // Score badge: bg, border, text color
                const badge = card.querySelector('.score-badge');
                if (badge) {
                    badge.style.background = `${fitColor}1a`;
                    badge.style.borderColor = `${fitColor}40`;
                    badge.style.color = fitColor;
                }

                // Status dot & fit label
                const dot = card.querySelector('.fit-status-dot');
                if (dot) dot.style.background = fitColor;
                const labelEl = card.querySelector('.summary-fit-label');
                if (labelEl) {
                    labelEl.textContent = fitLabel;
                    labelEl.style.color = fitColor;
                }

                // Left border accent
                card.style.borderLeftColor = fitColor;

                // Skill counts ("X/Y skills matched", "X/Y to develop")
                const total = matchedSkills.length + missingSkills.length;
                const matchedCountEl = card.querySelector('.skill-matched-count span');
                const gapCountEl = card.querySelector('.skill-gap-count span');
                if (matchedCountEl) matchedCountEl.textContent = `${matchedSkills.length}/${total} skills matched`;
                if (gapCountEl) gapCountEl.textContent = `${missingSkills.length}/${total} to develop`;
            }, 100);


            // Code removed, handles skill badges natively in details page now.


            // Read More logic removed. Only View Details (agents) exists now.

            const runDebateBtn = clone.querySelector('.run-debate-btn');
            if (runDebateBtn) {
                runDebateBtn.addEventListener('click', async () => {
                    // Navigate to details page
                    document.getElementById('view-dashboard').classList.add('hidden');
                    document.getElementById('view-dashboard').classList.remove('active-view');

                    document.getElementById('view-match-details').classList.remove('hidden');
                    document.getElementById('view-match-details').classList.add('active-view');

                    // Reset UI
                    document.getElementById('details-inline-skills-view').classList.add('hidden');
                    document.getElementById('details-job-title').textContent = jobTitle;
                    const rsReset = document.getElementById('roadmap-section');
                    if (rsReset) rsReset.style.display = 'none';

                    // --- Populate Stats and Rings (Copying standard logic) ---
                    document.getElementById('details-score-value').textContent = Math.round(percentScore);
                    const circle = document.getElementById('details-progress-circle');
                    if (circle) {
                        const r = circle.r.baseVal.value;
                        const c = r * 2 * Math.PI;
                        const offset = c - (percentScore / 100) * c;
                        circle.style.strokeDasharray = c;
                        circle.style.strokeDashoffset = offset;
                        if (percentScore > 70) circle.style.stroke = "url(#gradientStroke)";
                        else if (percentScore > 40) circle.style.stroke = "var(--warning)";
                        else circle.style.stroke = "var(--danger)";
                    }

                    const matchedSkills = (gap && gap.matched_skills) ? gap.matched_skills : [];
                    const missingSkills = (gap && gap.missing_skills) ? gap.missing_skills : [];
                    const totalSkills = matchedSkills.length + missingSkills.length;

                    document.getElementById('details-matched-count').textContent = totalSkills > 0 ? `${matchedSkills.length} / ${totalSkills}` : "0 / 0";
                    document.getElementById('details-missing-count').textContent = totalSkills > 0 ? `${missingSkills.length} / ${totalSkills}` : "0 / 0";

                    // Empathetic low-score message
                    const jobTitleEl = document.getElementById('details-job-title');
                    if (percentScore < 50) {
                        let encourageEl = document.getElementById('details-encourage-msg');
                        if (!encourageEl) {
                            encourageEl = document.createElement('p');
                            encourageEl.id = 'details-encourage-msg';
                            encourageEl.style.cssText = 'font-size:0.95rem; color: var(--accent); background: rgba(6,182,212,0.06); border: 1px solid rgba(6,182,212,0.15); border-radius: 10px; padding: 10px 16px; margin-top: 8px;';
                            jobTitleEl.parentNode.insertBefore(encourageEl, jobTitleEl.nextSibling);
                        }
                        encourageEl.textContent = `Don't worry — most students score between 30–55% on their first scan. Focus on the “Your next steps” section below to improve quickly.`;
                    } else {
                        const existing = document.getElementById('details-encourage-msg');
                        if (existing) existing.remove();
                    }

                    const matchedTagsContainer = document.getElementById('details-matched-tags');
                    matchedTagsContainer.innerHTML = '';
                    if (matchedSkills.length === 0) {
                        matchedTagsContainer.innerHTML = '<span style="color:var(--text-secondary); font-size: 0.9rem;">No specifically matched skills.</span>';
                    } else {
                        matchedSkills.forEach(skill => {
                            const el = document.createElement('span');
                            el.className = 'tag strength';
                            el.textContent = formatSkillName(skill);
                            matchedTagsContainer.appendChild(el);
                        });
                    }

                    const missingTagsContainer = document.getElementById('details-missing-tags');
                    missingTagsContainer.innerHTML = '';
                    if (missingSkills.length === 0) {
                        missingTagsContainer.innerHTML = '<span style="color:var(--success); font-size: 0.9rem;">No specifically missing skills!</span>';
                    } else {
                        missingSkills.forEach(skill => {
                            const el = document.createElement('span');
                            el.className = 'tag opportunity';
                            el.textContent = formatSkillName(skill);
                            missingTagsContainer.appendChild(el);
                        });
                    }
                    // --- End Stats Population ---

                    // Set loading text in the 4 standard AI boxes
                    document.getElementById('details-ai-overall').innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Generating formal analysis...';
                    document.getElementById('details-ai-strengths').innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Compiling strengths...';
                    document.getElementById('details-ai-gaps').innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Identifying gaps...';
                    document.getElementById('details-ai-advice').innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Formulating advice...';

                    try {
                        const response = await fetch(`${API_BASE}/compare/debate`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                cv_text: match.cv_text || "",
                                job_text: match.job_text || "",
                                faiss_score: percentScore
                            })
                        });

                        if (!response.ok) throw new Error("Debate failed.");
                        const debateData = await response.json();

                        document.getElementById('details-job-title').textContent = jobTitle;

                        // Render with bullet/numbered list formatting
                        document.getElementById('details-ai-overall').innerHTML = formatAiText(debateData.overall || 'No overall analysis provided.');
                        document.getElementById('details-ai-strengths').innerHTML = formatAiText(debateData.strengths || 'No strengths identified.');
                        document.getElementById('details-ai-gaps').innerHTML = formatAiText(debateData.gaps || 'No gaps identified.');
                        document.getElementById('details-ai-advice').innerHTML = formatAiText(debateData.advice || 'No advice available.');

                        // Render Career Roadmap
                        const roadmapSection = document.getElementById('roadmap-section');
                        const roadmapGrid = document.getElementById('roadmap-grid');
                        if (roadmapSection && roadmapGrid && debateData.roadmap) {
                            roadmapSection.style.display = 'block';
                            const phases = [
                                { key: 'short_term',  icon: 'fa-seedling',   color: '#10b981' },
                                { key: 'medium_term', icon: 'fa-chart-line', color: '#f59e0b' },
                                { key: 'long_term',   icon: 'fa-trophy',     color: 'var(--primary-light)' },
                            ];
                            roadmapGrid.innerHTML = phases.map(({ key, icon, color }) => {
                                const phase = debateData.roadmap[key] || {};
                                const actions = Array.isArray(phase.actions) ? phase.actions : [];
                                return `
                                    <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.08); border-radius:14px; padding:20px; border-top:3px solid ${color};">
                                        <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
                                            <i class="fa-solid ${icon}" style="color:${color}; font-size:1rem;"></i>
                                            <span style="font-size:0.75rem; text-transform:uppercase; letter-spacing:1.5px; font-weight:700; color:${color};">${phase.label || ''}</span>
                                        </div>
                                        <p style="font-size:0.88rem; color:var(--text-secondary); margin:0 0 14px 0; font-style:italic; line-height:1.5;">${phase.focus || ''}</p>
                                        <ul style="margin:0; padding-left:18px; display:flex; flex-direction:column; gap:8px;">
                                            ${actions.map(a => `<li style="font-size:0.87rem; color:var(--text-primary); line-height:1.5;">${a}</li>`).join('')}
                                        </ul>
                                    </div>`;
                            }).join('');
                        }

                    } catch (error) {
                        console.error(error);
                        document.getElementById('details-job-title').textContent = jobTitle;
                        document.getElementById('details-ai-overall').textContent = "Our AI analysis is temporarily unavailable. Your skill match results above are still accurate.";
                        document.getElementById('details-ai-strengths').textContent = "Please try again in a moment.";
                        document.getElementById('details-ai-gaps').textContent = "";
                        document.getElementById('details-ai-advice').textContent = "";
                        const rs = document.getElementById('roadmap-section');
                        if (rs) rs.style.display = 'none';
                    }
                });
            }

            matchesContainer.appendChild(clone);
        });

        // Persist Data to LocalStorage for Analytics
        const overallHistory = JSON.parse(localStorage.getItem('matchai-history')) || [];
        const combinedHistory = [...overallHistory, ...currentSessionHistory];
        localStorage.setItem('matchai-history', JSON.stringify(combinedHistory));

        // Fire notification
        if (currentSessionHistory.length > 0) {
            const best = currentSessionHistory.reduce((a, b) => a.score > b.score ? a : b);
            const count = currentSessionHistory.length;
            const title = `${count} match${count > 1 ? 'es' : ''} complete`;
            const others = count - 1;
            const body = `Best: ${best.job} · ${best.score}%${others > 0 ? ` · +${others} more result${others > 1 ? 's' : ''}` : ''}`;
            pushNotification(title, body);
        }

        // Store session results for live analytics tab
        stateSessionResults = currentSessionHistory;

        // Apply interactive 3D physics to newly rendered match cards
        // applyTiltToCards('.match-card');
    }

    // Set Date visually in top bar
    const dateOpts = { weekday: 'short', month: 'short', day: 'numeric' };
    document.getElementById('current-date').textContent = new Date().toLocaleDateString('en-US', dateOpts);

    // --- Global Glow Cursor & Interactive Dashboard Telemetry ---
    const glow = document.createElement('div');
    glow.className = 'glow-cursor';
    document.body.appendChild(glow);

    document.addEventListener('mousemove', (e) => {
        glow.style.transform = `translate(${e.clientX - 250}px, ${e.clientY - 250}px)`;
    });

    // --- Interactive 3D Card Tilt Physics Removed ---

    // --- Hardware Ripple Effect on Primary Buttons ---
    document.documentElement.addEventListener('click', (e) => {
        const btn = e.target.closest('.primary-btn');
        if (btn && !btn.disabled) {
            const rect = btn.getBoundingClientRect();
            const circle = document.createElement('span');
            const diameter = Math.max(rect.width, rect.height);
            const radius = diameter / 2;

            circle.style.width = circle.style.height = `${diameter}px`;
            circle.style.left = `${e.clientX - rect.left - radius}px`;
            circle.style.top = `${e.clientY - rect.top - radius}px`;
            circle.classList.add('btn-ripple');

            const existing = btn.querySelector('.btn-ripple');
            if (existing) existing.remove();

            btn.appendChild(circle);
            setTimeout(() => circle.remove(), 600);
        }
    });

    function renderHistoryView() {
        const history = JSON.parse(localStorage.getItem('matchai-history')) || [];
        const emptyEl = document.getElementById('history-empty');
        const listEl = document.getElementById('history-list');
        if (!emptyEl || !listEl) return;

        if (history.length === 0) {
            emptyEl.style.display = '';
            listEl.innerHTML = '';
            return;
        }

        emptyEl.style.display = 'none';
        const getScoreColor = (s) => s >= 70 ? 'var(--success)' : s >= 40 ? 'var(--warning)' : 'var(--danger)';
        const getScoreLabel = (s) => s >= 70 ? 'Strong' : s >= 40 ? 'Moderate' : 'Weak';

        listEl.innerHTML = [...history].reverse().map((item, i) => {
            const matched = item.matched || [];
            const missing = item.missing || [];
            const allMatchedHtml = matched.map(s => `<span class="chip green" style="font-size:0.78rem; padding:3px 10px;">${s}</span>`).join('');
            const allMissingHtml = missing.map(s => `<span class="chip amber" style="font-size:0.78rem; padding:3px 10px;">${s}</span>`).join('');
            const previewMatchedHtml = matched.slice(0, 5).map(s => `<span class="chip green" style="font-size:0.78rem; padding:3px 10px;">${s}</span>`).join('')
                + (matched.length > 5 ? `<span class="history-more-tag" style="color:var(--text-secondary); font-size:0.8rem; cursor:pointer;">+${matched.length - 5} more</span>` : '');
            const previewMissingHtml = missing.slice(0, 4).map(s => `<span class="chip amber" style="font-size:0.78rem; padding:3px 10px;">${s}</span>`).join('')
                + (missing.length > 4 ? `<span class="history-more-tag" style="color:var(--text-secondary); font-size:0.8rem; cursor:pointer;">+${missing.length - 4} more</span>` : '');

            const fullSummary = item.summary
                ? item.summary.replace(/\b(with\s+a\s+match\s+percentage\s+of\s+[\d.]+%|[\d.]+%\s+match)\b/gi, '').trim()
                : '';
            const teaser = fullSummary.slice(0, 140);

            const cardId = `hcard-${i}`;
            return `
            <div class="glass-panel history-run-card" id="${cardId}" data-run-id="${item.runId || ''}" data-expanded="false"
                style="padding: 22px 26px; border-left: 4px solid ${getScoreColor(item.score)}60; cursor: pointer; transition: border-color 0.3s, box-shadow 0.3s, background 0.2s;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 10px;">
                    <div>
                        <h3 style="margin: 0 0 4px; font-size: 1.05rem; font-weight: 700;">${item.job}</h3>
                        ${item.runLabel ? `<span style="font-size:0.8rem; color:var(--text-secondary);">${item.runLabel}</span>` : ''}
                    </div>
                    <div style="text-align: right; flex-shrink: 0; display:flex; flex-direction:column; align-items:flex-end; gap:4px;">
                        <span style="background: ${getScoreColor(item.score)}20; color: ${getScoreColor(item.score)}; padding: 4px 12px; border-radius: 99px; font-weight: 700; font-size: 0.85rem; border: 1px solid ${getScoreColor(item.score)}40;">${item.score}% · ${getScoreLabel(item.score)}</span>
                        <span style="font-size: 0.78rem; color: var(--text-secondary);">${item.date || ''}</span>
                        <i class="fa-solid fa-chevron-down history-chevron" style="font-size:0.75rem; color:var(--text-secondary); transition: transform 0.3s;"></i>
                    </div>
                </div>
                <p class="history-summary-preview" style="font-size:0.87rem; color:var(--text-secondary); margin: 0 0 12px; line-height:1.6; font-style:italic;">${teaser}${fullSummary.length > 140 ? '…' : ''}</p>
                <p class="history-summary-full" style="font-size:0.87rem; color:var(--text-secondary); margin: 0 0 12px; line-height:1.6; font-style:italic; display:none;">${fullSummary}</p>
                <div class="history-skills-preview" style="display:flex; flex-direction:column; gap:8px;">
                    ${previewMatchedHtml ? `<div style="display:flex; flex-wrap:wrap; gap:6px; align-items:center;">${previewMatchedHtml}</div>` : ''}
                    ${previewMissingHtml ? `<div style="display:flex; flex-wrap:wrap; gap:6px; align-items:center;">${previewMissingHtml}</div>` : ''}
                </div>
                <div class="history-skills-full" style="display:none; flex-direction:column; gap:8px;">
                    ${allMatchedHtml ? `<div><p style="font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; color:var(--text-secondary); margin:0 0 6px;">Matched (${matched.length})</p><div style="display:flex; flex-wrap:wrap; gap:6px;">${allMatchedHtml}</div></div>` : ''}
                    ${allMissingHtml ? `<div style="margin-top:8px;"><p style="font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; color:var(--text-secondary); margin:0 0 6px;">Missing (${missing.length})</p><div style="display:flex; flex-wrap:wrap; gap:6px;">${allMissingHtml}</div></div>` : ''}
                </div>
            </div>`;
        }).join('');

        // Wire card click to expand/collapse
        listEl.querySelectorAll('.history-run-card').forEach(card => {
            card.addEventListener('mouseenter', () => { card.style.background = 'rgba(255,255,255,0.04)'; });
            card.addEventListener('mouseleave', () => { card.style.background = ''; });
            card.addEventListener('click', () => {
                const expanded = card.dataset.expanded === 'true';
                card.dataset.expanded = expanded ? 'false' : 'true';
                card.querySelector('.history-summary-preview').style.display = expanded ? '' : 'none';
                card.querySelector('.history-summary-full').style.display = expanded ? 'none' : '';
                card.querySelector('.history-skills-preview').style.display = expanded ? 'flex' : 'none';
                card.querySelector('.history-skills-full').style.display = expanded ? 'none' : 'flex';
                const chevron = card.querySelector('.history-chevron');
                if (chevron) chevron.style.transform = expanded ? '' : 'rotate(180deg)';
            });
        });

        // Wire "Clear All" button
        const clearBtn = document.getElementById('clear-history-btn');
        if (clearBtn) {
            clearBtn.onclick = () => {
                if (confirm('Clear all run history? This cannot be undone.')) {
                    localStorage.removeItem('matchai-history');
                    renderHistoryView();
                }
            };
        }
    }

    function renderChart() {
        const noDataEl = document.getElementById('analytics-no-data');
        const hasDataEl = document.getElementById('analytics-has-data');

        // Always (re)bind the clear button so it works even after DOM updates
        const clearBtn = document.getElementById('clear-history-btn');
        if (clearBtn && !clearBtn.hasAttribute('data-bound')) {
            clearBtn.setAttribute('data-bound', 'true');
            clearBtn.addEventListener('click', () => {
                localStorage.removeItem('matchai-history');
                localStorage.removeItem('matchai-gap-skills');
                stateSessionResults = [];
                activeAnalyticsDomain = null;
                renderChart();

                // Visual feedback
                const originalHTML = clearBtn.innerHTML;
                clearBtn.innerHTML = '<i class="fa-solid fa-check"></i> ✓ Cleared';
                clearBtn.style.color = '#10b981';
                clearBtn.style.borderColor = '#10b981';
                setTimeout(() => {
                    clearBtn.innerHTML = originalHTML;
                    clearBtn.style.color = '';
                    clearBtn.style.borderColor = '';
                }, 2000);
            });
        }
        const allHistory = (JSON.parse(localStorage.getItem('matchai-history')) || []).slice(-200);
        const sessionData = activeAnalyticsDomain
            ? allHistory.filter(item => (item.runLabel || '') === activeAnalyticsDomain)
            : allHistory;

        if (sessionData.length === 0) {
            if (noDataEl) noDataEl.classList.remove('hidden');
            if (hasDataEl) hasDataEl.classList.add('hidden');

            // Add click listener to dashboard button if not added
            const backToDashBtn = document.getElementById('an-back-to-dash');
            if (backToDashBtn && !backToDashBtn.hasAttribute('data-bound')) {
                backToDashBtn.setAttribute('data-bound', 'true');
                backToDashBtn.addEventListener('click', () => {
                    switchToApp('view-dashboard');
                });
            }
            return;
        }

        if (noDataEl) noDataEl.classList.add('hidden');
        if (hasDataEl) hasDataEl.classList.remove('hidden');

        // Domain filter pills — built from actual runLabels in history
        const filterEl = document.getElementById('an-domain-filter');
        if (filterEl) {
            const allDomains = [...new Set(allHistory.map(item => item.runLabel || '').filter(Boolean))];
            if (allDomains.length >= 2) {
                const pills = ['All', ...allDomains];
                filterEl.innerHTML = `
                    <span style="font-size:0.78rem; font-weight:700; text-transform:uppercase; letter-spacing:1.2px; color:var(--text-secondary); margin-right:4px; white-space:nowrap;">Filter by CV:</span>
                    ${pills.map(d => {
                        const isActive = d === 'All' ? !activeAnalyticsDomain : d === activeAnalyticsDomain;
                        return `<button class="an-domain-pill" data-domain="${d === 'All' ? '' : d}"
                            style="padding:6px 18px; border-radius:99px; border:1px solid ${isActive ? 'var(--primary)' : 'rgba(255,255,255,0.12)'}; cursor:pointer; font-size:0.85rem; font-weight:600; font-family:inherit; transition:all 0.2s; background:${isActive ? 'var(--primary)' : 'rgba(255,255,255,0.04)'}; color:${isActive ? 'white' : 'var(--text-secondary)'};">${d}</button>`;
                    }).join('')}
                `;
                filterEl.querySelectorAll('.an-domain-pill').forEach(pill => {
                    pill.addEventListener('click', () => {
                        activeAnalyticsDomain = pill.getAttribute('data-domain') || null;
                        renderChart();
                    });
                });
            } else {
                filterEl.innerHTML = '';
            }
        }

        // Best match banner
        const bestMatchEl = document.getElementById('an-best-match');
        if (bestMatchEl && sessionData.length > 0) {
            const best = sessionData.reduce((a, b) => a.score > b.score ? a : b);
            const bestColor = best.score >= 70 ? '#10b981' : best.score >= 40 ? '#f59e0b' : '#ef4444';
            bestMatchEl.style.display = 'flex';
            bestMatchEl.style.alignItems = 'center';
            bestMatchEl.style.gap = '16px';
            bestMatchEl.innerHTML = `
                <div style="width:44px; height:44px; border-radius:12px; background:rgba(251,191,36,0.1); border:1px solid rgba(251,191,36,0.2); display:flex; align-items:center; justify-content:center; flex-shrink:0;">
                    <i class="fa-solid fa-trophy" style="color:#fbbf24; font-size:1.1rem;"></i>
                </div>
                <div style="flex-grow:1; min-width:0;">
                    <div style="font-size:0.7rem; text-transform:uppercase; letter-spacing:1.5px; color:var(--text-secondary); font-weight:700; margin-bottom:2px;">Best Match${activeAnalyticsDomain ? ' · ' + activeAnalyticsDomain : ''}</div>
                    <div style="font-size:1.1rem; font-weight:700; color:var(--text-primary); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${best.job}</div>
                    <div style="font-size:0.78rem; color:var(--text-secondary); margin-top:1px;">${best.runLabel ? best.runLabel + ' · ' : ''}${best.date || ''}</div>
                </div>
                <div style="font-size:2rem; font-weight:800; color:${bestColor}; flex-shrink:0;">${best.score}%</div>
            `;
        } else if (bestMatchEl) {
            bestMatchEl.style.display = 'none';
        }

        // Helpers
        const getColor = (score) => score >= 70 ? 'var(--success)' : score >= 40 ? 'var(--warning)' : 'var(--danger)';

        // New Logic for Executive Metrics
        const totalScans = sessionData.length;
        const avgScore = Math.round(sessionData.reduce((acc, curr) => acc + curr.score, 0) / totalScans) || 0;

        const gapCounts = {};
        sessionData.forEach(item => {
            (item.missing || []).forEach(g => {
                const clean = formatSkillName(g);
                gapCounts[clean] = (gapCounts[clean] || 0) + 1;
            });
        });
        if (Object.keys(gapCounts).length === 0 && !activeAnalyticsDomain) {
            (JSON.parse(localStorage.getItem('matchai-gap-skills')) || []).forEach(g => {
                const clean = formatSkillName(g);
                gapCounts[clean] = (gapCounts[clean] || 0) + 1;
            });
        }
        let topGap = "-";
        const sortedTopGaps = Object.entries(gapCounts).sort((a, b) => b[1] - a[1]);
        if (sortedTopGaps.length > 0) topGap = sortedTopGaps[0][0];

        const metricTotalEl = document.getElementById('an-metric-total');
        const metricAvgEl = document.getElementById('an-metric-avg');
        const metricGapEl = document.getElementById('an-metric-gap');

        if (metricTotalEl) metricTotalEl.textContent = totalScans;
        if (metricAvgEl) {
            metricAvgEl.textContent = avgScore + '%';
            metricAvgEl.style.color = getColor(avgScore);
            metricAvgEl.parentElement.style.borderBottomColor = getColor(avgScore);
        }
        if (metricGapEl) metricGapEl.textContent = topGap;

        // Performance History — grouped by runLabel
        const historyListEl = document.getElementById('an-history-list');
        if (historyListEl) {
            const reversed = sessionData.slice().reverse();
            const groups = {};
            const groupOrder = [];
            reversed.forEach(item => {
                const key = item.runLabel || 'Previous Runs';
                if (!groups[key]) { groups[key] = []; groupOrder.push(key); }
                groups[key].push(item);
            });
            const showHeaders = groupOrder.length > 1;
            historyListEl.innerHTML = groupOrder.map(groupName => `
                <div style="margin-bottom:${showHeaders ? '18px' : '0'};">
                    ${showHeaders ? `<div style="font-size:0.72rem; text-transform:uppercase; letter-spacing:1.5px; color:var(--text-secondary); font-weight:700; margin-bottom:8px; padding-bottom:6px; border-bottom:1px solid rgba(255,255,255,0.06); display:flex; align-items:center; gap:6px;"><i class="fa-solid fa-folder-open" style="opacity:0.5;"></i>&nbsp;${groupName}</div>` : ''}
                    ${groups[groupName].map(item => `
                        <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05); padding:12px 16px; border-radius:10px; display:flex; align-items:center; justify-content:space-between; gap:16px; margin-bottom:8px;">
                            <div style="flex:1; min-width:0;">
                                <h4 style="font-size:0.95rem; font-weight:600; margin:0 0 3px 0; color:var(--text-primary); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${item.job}</h4>
                                <span style="font-size:0.75rem; color:var(--text-secondary);">${item.date || ''}</span>
                            </div>
                            <div style="flex:2; display:flex; align-items:center; gap:12px;">
                                <div style="flex-grow:1; height:6px; background:rgba(255,255,255,0.05); border-radius:99px; overflow:hidden;">
                                    <div style="width:${item.score}%; height:100%; background:${getColor(item.score)};"></div>
                                </div>
                                <span style="font-weight:700; font-size:0.9rem; color:${getColor(item.score)}; min-width:40px; text-align:right;">${item.score}%</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `).join('');
        }

        // Skill Matrix - Strengths
        const strengthsEl = document.getElementById('an-matrix-strengths');
        let sortedStrengths = [];
        if (strengthsEl) {
            const allStrengths = [];
            sessionData.forEach(item => {
                if (item.matched) allStrengths.push(...item.matched);
            });

            const strengthsCounts = {};
            allStrengths.forEach(s => {
                const clean = formatSkillName(s);
                strengthsCounts[clean] = (strengthsCounts[clean] || 0) + 1;
            });

            sortedStrengths = Object.entries(strengthsCounts).sort((a, b) => b[1] - a[1]).filter(item => item[1] > 1).slice(0, 25);

            if (sortedStrengths.length === 0) {
                strengthsEl.innerHTML = '<span style="color:var(--text-secondary); font-size: 0.9rem;">No recurring strengths yet. Scan more jobs.</span>';
            } else {
                const categorized = {};
                sortedStrengths.forEach(([skill, count]) => {
                    const meta = getSkillMeta(skill);
                    if (!categorized[meta.cat]) categorized[meta.cat] = { meta, skills: [] };
                    categorized[meta.cat].skills.push(skill);
                });

                strengthsEl.innerHTML = Object.values(categorized).map(group => `
                    <div style="width: 100%; margin-bottom: 20px;">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                            <i class="fa-solid ${group.meta.icon}" style="color: ${group.meta.color}; font-size: 0.9rem; text-shadow: 0 0 10px ${group.meta.color}60;"></i>
                            <span style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; color: var(--text-secondary);">${group.meta.cat}</span>
                        </div>
                        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                            ${group.skills.map(skill => `
                                <span style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); padding: 6px 12px; border-radius: 6px; font-size: 0.9rem; color: var(--text-primary); box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                    ${skill}
                                </span>
                            `).join('')}
                        </div>
                    </div>
                `).join('');
            }
        }

        // Skill Matrix - Gaps
        const gapsEl = document.getElementById('an-matrix-gaps');
        let sortedGaps = [];
        if (gapsEl) {
            sortedGaps = Object.entries(gapCounts).sort((a, b) => b[1] - a[1]).slice(0, 25);

            if (sortedGaps.length === 0) {
                gapsEl.innerHTML = '<span style="color:var(--text-secondary); font-size: 0.9rem;">No recurring skill gaps found.</span>';
            } else {
                const categorized = {};
                sortedGaps.forEach(([skill, count]) => {
                    const meta = getSkillMeta(skill);
                    if (!categorized[meta.cat]) categorized[meta.cat] = { meta, skills: [] };
                    categorized[meta.cat].skills.push(skill);
                });

                gapsEl.innerHTML = Object.values(categorized).map(group => `
                    <div style="width: 100%; margin-bottom: 20px;">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                            <i class="fa-solid ${group.meta.icon}" style="color: ${group.meta.color}; font-size: 0.9rem; text-shadow: 0 0 10px ${group.meta.color}60;"></i>
                            <span style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; color: var(--text-secondary);">${group.meta.cat}</span>
                        </div>
                        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                            ${group.skills.map(skill => `
                                <span style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); padding: 6px 12px; border-radius: 6px; font-size: 0.9rem; color: var(--text-primary); box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                    ${skill}
                                </span>
                            `).join('')}
                        </div>
                    </div>
                `).join('');
            }
        }

        // Score Distribution Doughnut
        if (window.analyticsDistributionChart) {
            window.analyticsDistributionChart.destroy();
            window.analyticsDistributionChart = null;
        }
        const distCanvas = document.getElementById('distributionChart');
        if (distCanvas && sessionData.length > 0) {
            const strong   = sessionData.filter(d => d.score >= 70).length;
            const moderate = sessionData.filter(d => d.score >= 40 && d.score < 70).length;
            const weak     = sessionData.filter(d => d.score < 40).length;
            window.analyticsDistributionChart = new Chart(distCanvas, {
                type: 'doughnut',
                data: {
                    labels: ['Strong ≥70%', 'Moderate 40–69%', 'Weak <40%'],
                    datasets: [{
                        data: [strong, moderate, weak],
                        backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                        borderColor: 'rgba(15,23,42,0.8)',
                        borderWidth: 2,
                        hoverOffset: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '62%',
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                color: document.body.classList.contains('light-mode') ? 'rgba(15,23,42,0.8)' : 'rgba(255,255,255,0.7)',
                                font: { family: "'Outfit', sans-serif", size: 11 },
                                usePointStyle: true,
                                padding: 12,
                                generateLabels: chart => chart.data.labels.map((lbl, i) => ({
                                    text: `${lbl}  (${chart.data.datasets[0].data[i]})`,
                                    fillStyle: chart.data.datasets[0].backgroundColor[i],
                                    strokeStyle: 'transparent',
                                    lineWidth: 0,
                                    pointStyle: 'circle',
                                    fontColor: document.body.classList.contains('light-mode') ? 'rgba(15,23,42,0.8)' : 'rgba(255,255,255,0.7)',
                                    index: i
                                }))
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(15,23,42,0.9)',
                            titleFont: { family: "'Outfit', sans-serif", size: 12 },
                            bodyFont:  { family: "'Outfit', sans-serif", size: 11 },
                            callbacks: {
                                label: ctx => {
                                    const pct = sessionData.length > 0 ? Math.round(ctx.parsed / sessionData.length * 100) : 0;
                                    return ` ${ctx.parsed} scan${ctx.parsed !== 1 ? 's' : ''} (${pct}%)`;
                                }
                            }
                        }
                    }
                }
            });
        }

        // Radar Chart
        if (window.analyticsRadarChart) {
            window.analyticsRadarChart.destroy();
        }

        const radarContainer = document.getElementById('skillRadarContainer');
        if (radarContainer) {
            // Re-inject canvas to clear out any empty state messages safely
            radarContainer.innerHTML = '<canvas id="skillRadarChart"></canvas>';
            const radarCtx = document.getElementById('skillRadarChart');

            const chartLabels = [];
            const strengthData = [];
            const gapData = [];

            const combined = {};
            sortedStrengths.forEach(([s, c]) => { combined[s] = { s: c, g: 0 }; });
            sortedGaps.forEach(([s, c]) => {
                if (combined[s]) combined[s].g = c;
                else combined[s] = { s: 0, g: c };
            });

            const topSkills = Object.entries(combined)
                .sort((a, b) => (b[1].s + b[1].g) - (a[1].s + a[1].g))
                .slice(0, 6);

            topSkills.forEach(([skill, data]) => {
                chartLabels.push(skill.length > 15 ? skill.substring(0, 15) + '...' : skill);
                strengthData.push(data.s);
                gapData.push(data.g);
            });

            if (topSkills.length >= 3) {
                const primaryColor = getComputedStyle(document.documentElement).getPropertyValue('--primary').trim() || '#3b82f6';
                const warningColor = getComputedStyle(document.documentElement).getPropertyValue('--warning').trim() || '#f59e0b';

                window.analyticsRadarChart = new Chart(radarCtx, {
                    type: 'radar',
                    data: {
                        labels: chartLabels,
                        datasets: [
                            {
                                label: 'Core Strengths',
                                data: strengthData,
                                backgroundColor: primaryColor + '40',
                                borderColor: primaryColor,
                                pointBackgroundColor: primaryColor,
                                borderWidth: 2,
                                pointRadius: 3,
                            },
                            {
                                label: 'Skill Gaps',
                                data: gapData,
                                backgroundColor: warningColor + '40',
                                borderColor: warningColor,
                                pointBackgroundColor: warningColor,
                                borderWidth: 2,
                                pointRadius: 3,
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            r: {
                                angleLines: { color: document.body.classList.contains('light-mode') ? 'rgba(15,23,42,0.15)' : 'rgba(255, 255, 255, 0.1)' },
                                grid: { color: document.body.classList.contains('light-mode') ? 'rgba(15,23,42,0.12)' : 'rgba(255, 255, 255, 0.1)' },
                                pointLabels: {
                                    color: document.body.classList.contains('light-mode') ? 'rgba(15,23,42,0.7)' : 'rgba(255, 255, 255, 0.7)',
                                    font: { family: "'Outfit', sans-serif", size: 10, weight: '500' }
                                },
                                ticks: { display: false, beginAtZero: true }
                            }
                        },
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: {
                                    color: document.body.classList.contains('light-mode') ? 'rgba(15,23,42,0.8)' : 'rgba(255, 255, 255, 0.7)',
                                    font: { family: "'Outfit', sans-serif", size: 12 },
                                    usePointStyle: true,
                                    padding: 20
                                }
                            },
                            tooltip: {
                                backgroundColor: 'rgba(15, 23, 42, 0.9)',
                                titleFont: { family: "'Outfit', sans-serif", size: 13 },
                                bodyFont: { family: "'Outfit', sans-serif", size: 12 },
                                padding: 10,
                                cornerRadius: 8,
                                displayColors: false
                            }
                        }
                    }
                });
            } else {
                radarContainer.innerHTML = '<div style="text-align: center; color:var(--text-secondary); font-size: 0.9rem; padding: 40px; position: absolute; width: 100%; top: 50%; transform: translateY(-50%);">Not enough data.<br>Scan at least 3 skills to generate your radar profile.</div>';
            }
        }

        // Trigger animations
        setTimeout(() => {
            document.querySelectorAll('.an-anim-bar').forEach(bar => {
                bar.style.width = bar.getAttribute('data-width');
            });
        }, 50);
    }

});
