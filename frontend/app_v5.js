document.addEventListener('DOMContentLoaded', () => {

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


    // --- Single Page App Routing System ---
    const navItems = document.querySelectorAll('.nav-item');
    const pageViews = document.querySelectorAll('.page-view');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = item.getAttribute('data-target');
            if (!targetId) return;

            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            pageViews.forEach(view => {
                if (view.id === targetId) {
                    view.classList.remove('hidden');
                    view.classList.add('active-view');
                } else {
                    view.classList.add('hidden');
                    view.classList.remove('active-view');
                }
            });
            
            // Removed tilt features per user request

            // Re-render chart if navigating to analytics
            if (targetId === 'view-analytics') {
                renderChart();
            }
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
            // Removed tilt features
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
    const heroHeader = document.getElementById('hero-header');

    // State
    const validExtensions = ['.txt', '.pdf', '.docx'];
    let stateCvFile = null;
    let stateJobFiles = [];
    let stateResumes = []; // tracks all CVs uploaded this session
    let stateSessionResults = []; // tracks results from current session for analytics

    // Enable/Disable button
    function updateCompareButton() {
        if (stateCvFile && stateJobFiles.length > 0) {
            compareBtn.disabled = false;
        } else {
            compareBtn.disabled = true;
        }
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
            alert("Please upload a .txt, .pdf, or .docx CV file.");
            return;
        }
        stateCvFile = file;

        // Save to resumes list if not already there
        if (!stateResumes.find(r => r.name === file.name && r.size === file.size)) {
            stateResumes.push({
                name: file.name,
                size: file.size,
                addedAt: new Date(),
                isActive: stateResumes.length === 0 // first one is active by default
            });
            renderResumesList();
        }

        renderCvFile();
        updateCompareButton();
    }

    function renderCvFile() {
        if (!stateCvFile) {
            cvFileList.innerHTML = '';
            return;
        }
        cvFileList.innerHTML = `
            <div class="file-item">
                <div class="file-info">
                    <i class="fa-solid ${getFileIcon(stateCvFile.name)} file-icon" style="color:var(--primary-light)"></i>
                    <div class="file-details">
                        <h5>${stateCvFile.name}</h5>
                        <span>${formatBytes(stateCvFile.size)}</span>
                    </div>
                </div>
                <button class="remove-file-btn" id="remove-cv-btn"><i class="fa-solid fa-trash-can"></i></button>
            </div>
        `;
        document.getElementById('remove-cv-btn').addEventListener('click', () => {
            stateCvFile = null;
            cvFileInput.value = '';
            renderCvFile();
            updateCompareButton();
        });
    }

    // --- Jobs Upload Handlers ---
    jobDropZone.addEventListener('dragover', (e) => { e.preventDefault(); jobDropZone.classList.add('dragover'); });
    jobDropZone.addEventListener('dragleave', (e) => { e.preventDefault(); jobDropZone.classList.remove('dragover'); });
    jobDropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        jobDropZone.classList.remove('dragover');
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
            alert("Please upload valid Job Description files (.txt, .pdf, .docx).");
            return;
        }
        if (stateJobFiles.length + validFiles.length > 5) {
            alert("You can only compare up to 5 target domains at a time.");
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
        heroHeader.classList.add('hidden');
        loadingSection.classList.remove('hidden');

        try {
            const formData = new FormData();
            formData.append('cv_file', stateCvFile);
            
            stateJobFiles.forEach(file => {
                formData.append('job_files', file);
            });

            const response = await fetch('http://localhost:8000/compare/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || "Error connecting to the API.");
            }

            const data = await response.json();
            renderResults(data);
        } catch (error) {
            console.error("Comparison Error:", error);
            alert("Failed to analyze: \n" + error.message);
            loadingSection.classList.add('hidden');
            uploadSection.classList.remove('hidden');
            heroHeader.classList.remove('hidden');
        }
    });

    // Reset Form
    uploadAnotherBtn.addEventListener('click', () => {
        resultsSection.classList.add('hidden');
        uploadSection.classList.remove('hidden');
        heroHeader.classList.remove('hidden');
        
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
            currentSessionHistory.push({
                job: jobTitle,
                score: Math.round(percentScore),
                date: new Date().toLocaleDateString()
            });

            // Accumulate missing skills for analytics gap cloud
            if (gap && gap.missing_skills && gap.missing_skills.length > 0) {
                const existingGaps = JSON.parse(localStorage.getItem('matchai-gap-skills')) || [];
                const updatedGaps = [...existingGaps, ...gap.missing_skills];
                localStorage.setItem('matchai-gap-skills', JSON.stringify(updatedGaps));
            }
            
            clone.querySelector('.score-value').textContent = Math.round(percentScore);

            // Populate the new summary sentence dynamically
            clone.querySelector('.summary-job-title').textContent = jobTitle;

            // Animate SVG Ring and Calculate Label
            setTimeout(() => {
                const circle = card.querySelector('.progress-ring__circle');
                const radius = circle.r.baseVal.value; // 30
                const circumference = radius * 2 * Math.PI; // ~188.49
                const offset = circumference - (percentScore / 100) * circumference;
                circle.style.strokeDashoffset = offset;
                
                let fitLabel = match.fit_category || "moderate fit";
                let fitColor = "var(--warning)";

                // Change stroke-color gradient dynamically and set color based on exact backend category
                if (fitLabel === "strong fit") {
                    circle.style.stroke = "url(#gradientStroke)";
                    fitColor = "var(--primary-light)";
                } else if (fitLabel === "moderate fit") {
                    circle.style.stroke = "var(--warning)";
                    fitColor = "var(--warning)";
                } else {
                    circle.style.stroke = "var(--danger)";
                    fitColor = "var(--danger)";
                }

                const labelEl = card.querySelector('.summary-fit-label');
                labelEl.textContent = fitLabel;
                labelEl.style.color = fitColor;

            }, 100);

            // Code removed, handles skill badges natively in details page now.


            // Set up Page Navigation logic instead of accordion
            const readMoreBtn = clone.querySelector('.read-more-btn');
            const summaryText = match.llm_summary || "We analyzed your CV alongside the job description. You are a strong match for this role.";

            // Parse summary blocks
            let strOverall = "Overall match analysis unavailable.";
            let strStrengths = "No specific strengths identified.";
            let strGaps = "No specific gaps identified.";
            let strAdvice = "No targeted advice available.";

            if (summaryText.includes('Overall:')) {
                const matchStrengths = summaryText.match(/Strengths:\s*([\s\S]*?)(?=Gaps:|Advice:|Overall:|$)/i);
                const matchGaps = summaryText.match(/Gaps:\s*([\s\S]*?)(?=Strengths:|Advice:|Overall:|$)/i);
                const matchAdvice = summaryText.match(/Advice:\s*([\s\S]*?)(?=Strengths:|Gaps:|Overall:|$)/i);
                const matchOverall = summaryText.match(/Overall:\s*([\s\S]*?)(?=Strengths:|Gaps:|Advice:|$)/i);

                if (matchStrengths && matchStrengths[1].trim()) strStrengths = matchStrengths[1].trim();
                if (matchGaps && matchGaps[1].trim()) strGaps = matchGaps[1].trim();
                if (matchAdvice && matchAdvice[1].trim()) strAdvice = matchAdvice[1].trim();
                if (matchOverall && matchOverall[1].trim()) strOverall = matchOverall[1].trim();
            } else {
                strOverall = summaryText; // Graceful fallback
            }

            if (readMoreBtn) {
                readMoreBtn.addEventListener('click', () => {
                    // Navigate to details page
                    document.getElementById('view-dashboard').classList.add('hidden');
                    document.getElementById('view-dashboard').classList.remove('active-view');
                    
                    document.getElementById('view-match-details').classList.remove('hidden');
                    document.getElementById('view-match-details').classList.add('active-view');
                    
                    // Reset toggles UI state
                    document.getElementById('details-inline-skills-view').classList.add('hidden');
                    document.getElementById('details-matched-list').classList.add('hidden');
                    document.getElementById('details-missing-list').classList.add('hidden');

                    // Populate AI details
                    document.getElementById('details-job-title').textContent = jobTitle;
                    document.getElementById('details-ai-overall').textContent = strOverall;
                    document.getElementById('details-ai-strengths').textContent = strStrengths;
                    document.getElementById('details-ai-gaps').textContent = strGaps;
                    document.getElementById('details-ai-advice').innerHTML = strAdvice.replace(/(?:\s|^)(\d+\.)/g, '<br><br>$1').replace(/^<br><br>/, '');

                    // Populate the Top Percentage Ring
                    document.getElementById('details-score-value').textContent = Math.round(percentScore);
                    const circle = document.getElementById('details-progress-circle');
                    if (circle) {
                        const r = circle.r.baseVal.value;
                        const c = r * 2 * Math.PI;
                        const offset = c - (percentScore / 100) * c;
                        circle.style.strokeDasharray = c;
                        circle.style.strokeDashoffset = offset;
                        if (percentScore > 75) circle.style.stroke = "url(#gradientStroke)";
                        else if (percentScore > 40) circle.style.stroke = "var(--warning)";
                        else circle.style.stroke = "var(--danger)";
                    }

                    // Populate details tags
                    const matchedSkills = (gap && gap.matched_skills) ? gap.matched_skills : [];
                    const missingSkills = (gap && gap.missing_skills) ? gap.missing_skills : [];
                    const totalSkills = matchedSkills.length + missingSkills.length;
                    
                    document.getElementById('details-matched-count').textContent = totalSkills > 0 ? `${matchedSkills.length} / ${totalSkills}` : "0 / 0";
                    document.getElementById('details-missing-count').textContent = totalSkills > 0 ? `${missingSkills.length} / ${totalSkills}` : "0 / 0";

                    const matchedTagsContainer = document.getElementById('details-matched-tags');
                    matchedTagsContainer.innerHTML = '';
                    if (matchedSkills.length === 0) {
                        matchedTagsContainer.innerHTML = '<span style="color:var(--text-secondary); font-size: 0.9rem;">No specifically matched skills.</span>';
                    } else {
                        matchedSkills.forEach(skill => {
                            const el = document.createElement('span');
                            el.className = 'tag strength';
                            el.textContent = skill;
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
                            el.textContent = skill;
                            missingTagsContainer.appendChild(el);
                        });
                    }
                });
            }

            matchesContainer.appendChild(clone);
        });

        // Persist Data to LocalStorage for Analytics
        const overallHistory = JSON.parse(localStorage.getItem('matchai-history')) || [];
        const combinedHistory = [...overallHistory, ...currentSessionHistory];
        localStorage.setItem('matchai-history', JSON.stringify(combinedHistory));

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

    // --- Chart.js Analytics Implementation ---
    let myChart = null;

    function renderChart() {
        const ctx = document.getElementById('analyticsChart');
        const noDataEl = document.getElementById('analytics-no-data');
        const bestMatchEl = document.getElementById('analytics-best-match');
        const gapsEl = document.getElementById('analytics-gaps-tags');
        if (!ctx) return;

        // Use live session results first, fall back to localStorage
        const sessionData = stateSessionResults.length > 0
            ? stateSessionResults
            : (JSON.parse(localStorage.getItem('matchai-history')) || []).slice(-10);

        if (sessionData.length === 0) {
            ctx.style.display = 'none';
            if (noDataEl) noDataEl.style.display = 'block';
            if (bestMatchEl) bestMatchEl.classList.add('hidden');
            if (gapsEl) gapsEl.innerHTML = '<span style="color: var(--text-secondary); font-size: 0.9rem; opacity: 0.6;">No data yet — run an analysis first.</span>';
            return;
        }

        // Show best match hero
        if (bestMatchEl) {
            const best = sessionData.reduce((a, b) => a.score > b.score ? a : b);
            document.getElementById('analytics-best-title').textContent = best.job;
            document.getElementById('analytics-best-score').textContent = best.score + '%';
            bestMatchEl.classList.remove('hidden');
        }

        // Show skills gap pills
        if (gapsEl) {
            const allGaps = JSON.parse(localStorage.getItem('matchai-gap-skills')) || [];
            if (allGaps.length > 0) {
                const freq = {};
                allGaps.forEach(s => { freq[s] = (freq[s] || 0) + 1; });
                const sorted = Object.entries(freq).sort((a,b) => b[1]-a[1]).slice(0, 8);
                
                gapsEl.innerHTML = sorted.map(([skill, count], i) => {
                    const rankColors = ['var(--warning)', 'var(--accent)', 'var(--primary-light)'];
                    const rankColor = rankColors[Math.min(i, rankColors.length - 1)];
                    const opacity = Math.max(0.45, 1 - (i * 0.07));
                    return `
                    <div style="display:flex; align-items:center; gap:14px; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08); border-radius:14px; padding: 14px 18px; opacity:${opacity}; transition: opacity 0.2s;">
                        <div style="flex-shrink:0; width:28px; height:28px; border-radius:50%; background:${rankColor}22; border:1.5px solid ${rankColor}; display:flex; align-items:center; justify-content:center; font-size:0.75rem; font-weight:800; color:${rankColor};">${i + 1}</div>
                        <div style="flex-grow:1; font-size:0.95rem; font-weight:600; color:var(--text-primary);">${skill}</div>
                        <div style="flex-shrink:0; font-size:0.75rem; font-weight:700; color:${rankColor}; background:${rankColor}18; padding: 3px 10px; border-radius:20px;">${count}×</div>
                    </div>`;
                }).join('');
            } else {
                gapsEl.innerHTML = '<span style="color: var(--text-secondary); font-size: 0.9rem; opacity: 0.6; grid-column: 1/-1;">No gap data yet — run an analysis first.</span>';
            }
        }

        // Render Bubble Chart
        if (noDataEl) noDataEl.style.display = 'none';
        ctx.style.display = 'block';

        const rootStyles = getComputedStyle(document.documentElement);
        const primaryColor = rootStyles.getPropertyValue('--primary-light').trim() || '#60a5fa';
        const accentColor = rootStyles.getPropertyValue('--warning').trim() || '#fbbf24';
        const dangerColor = '#f43f5e';

        if (myChart) myChart.destroy();

        const strongData = [];
        const modData = [];
        const weakData = [];
        
        sessionData.forEach((h, index) => {
            let yPos = 1; // Weak
            let radius = 10 + (h.score / 10);
            
            if (h.score >= 75) yPos = 3; // Strong
            else if (h.score >= 40) yPos = 2; // Moderate
            
            // Add jitter to fan out overlapped bubbles
            const jitterY = (Math.random() - 0.5) * 0.4;
            
            const pt = { x: h.score, y: yPos + jitterY, r: radius, jobTitle: h.job };
            if (yPos === 3) strongData.push(pt);
            else if (yPos === 2) modData.push(pt);
            else weakData.push(pt);
        });

        myChart = new Chart(ctx, {
            type: 'bubble',
            data: {
                datasets: [
                    { label: 'Strong Fit', data: strongData, backgroundColor: primaryColor + 'aa', borderColor: primaryColor, borderWidth: 2, hoverBorderWidth: 4 },
                    { label: 'Moderate Fit', data: modData, backgroundColor: accentColor + 'aa', borderColor: accentColor, borderWidth: 2, hoverBorderWidth: 4 },
                    { label: 'Weak Fit', data: weakData, backgroundColor: dangerColor + 'aa', borderColor: dangerColor, borderWidth: 2, hoverBorderWidth: 4 }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#f8fafc', font: { family: "'Outfit', sans-serif" }, usePointStyle: true } },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        titleFont: { family: "'Outfit', sans-serif", size: 14 },
                        bodyFont: { family: "'Outfit', sans-serif" },
                        padding: 12, cornerRadius: 10,
                        callbacks: {
                            label: function(c) {
                                return ` ${c.raw.jobTitle}: ${Number(c.raw.x).toFixed(0)}% Match`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true, max: 105,
                        title: { display: true, text: 'Match Score (%)', color: '#94a3b8', font: {family: "'Outfit', sans-serif"} },
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#94a3b8', font: {family: "'Outfit', sans-serif"} }
                    },
                    y: {
                        min: 0.5, max: 3.5,
                        title: { display: false },
                        grid: { color: 'rgba(255,255,255,0.1)' },
                        ticks: {
                            color: '#e2e8f0',
                            font: { family: "'Outfit', sans-serif", weight: '600', size: 13 },
                            stepSize: 1,
                            callback: function(value) {
                                if (value === 1) return 'Weak Fit';
                                if (value === 2) return 'Moderate Fit';
                                if (value === 3) return 'Strong Fit';
                                return '';
                            }
                        }
                    }
                }
            }
        });
    }

    const clearBtn = document.getElementById('clear-history-btn');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
             localStorage.removeItem('matchai-history');
             localStorage.removeItem('matchai-gap-skills');
             stateSessionResults = [];
             renderChart();
        });
    }

});
