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
            const summaryText = match.llm_summary;

            // Parse summary blocks
            let strOverall = "Overall match analysis unavailable.";
            let strStrengths = "No specific strengths identified.";
            let strGaps = "No specific gaps identified.";
            let strAdvice = "No targeted advice available.";

            if (summaryText) {
                const extractMatch = (regex) => {
                    const m = summaryText.match(regex);
                    return m ? m[1].trim() : null;
                };
                strStrengths = extractMatch(/Strengths:\s*([\s\S]*?)(?=Gaps:)/) || strStrengths;
                strGaps = extractMatch(/Gaps:\s*([\s\S]*?)(?=Advice:)/) || strGaps;
                strAdvice = extractMatch(/Advice:\s*([\s\S]*?)(?=Overall:)/) || strAdvice;
                strOverall = extractMatch(/Overall:\s*([\s\S]+)$/) || strOverall;
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

                    // Breakdown Matrix UI removed as requested
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

    // --- Analytics v8 ---
    let myChart = null;
    const CIRCUMFERENCE = 238.76;

    function animateRing(id, pct) {
        const el = document.getElementById(id);
        if (!el) return;
        const offset = CIRCUMFERENCE - (pct / 100) * CIRCUMFERENCE;
        setTimeout(() => { el.style.strokeDashoffset = offset; }, 80);
    }

    function animateBar(id, pct) {
        const el = document.getElementById(id);
        if (!el) return;
        setTimeout(() => { el.style.width = pct + '%'; }, 80);
    }

    function renderChart() {
        const ctx = document.getElementById('analyticsChart');
        const noDataEl  = document.getElementById('analytics-no-data');
        const hasDataEl = document.getElementById('analytics-has-data');
        const gapsEl    = document.getElementById('analytics-gaps-tags');
        if (!ctx) return;

        const sessionData = stateSessionResults.length > 0
            ? stateSessionResults
            : (JSON.parse(localStorage.getItem('matchai-history')) || []).slice(-15);

        if (sessionData.length === 0) {
            if (noDataEl)  noDataEl.classList.remove('hidden');
            if (hasDataEl) hasDataEl.classList.add('hidden');
            return;
        }

        if (noDataEl)  noDataEl.classList.add('hidden');
        if (hasDataEl) hasDataEl.classList.remove('hidden');

        const total    = sessionData.length;
        const nStrong  = sessionData.filter(h => h.score >= 75).length;
        const nMod     = sessionData.filter(h => h.score >= 40 && h.score < 75).length;
        const nWeak    = sessionData.filter(h => h.score < 40).length;

        // Zone counts
        const zS = document.getElementById('zone-strong-count');
        const zM = document.getElementById('zone-moderate-count');
        const zW = document.getElementById('zone-weak-count');
        if (zS) zS.textContent = nStrong;
        if (zM) zM.textContent = nMod;
        if (zW) zW.textContent = nWeak;

        // Percentage labels
        const pS = Math.round((nStrong / total) * 100);
        const pM = Math.round((nMod    / total) * 100);
        const pW = Math.round((nWeak   / total) * 100);
        const elPS = document.getElementById('pct-strong');
        const elPM = document.getElementById('pct-moderate');
        const elPW = document.getElementById('pct-weak');
        if (elPS) elPS.textContent = pS + '% of session';
        if (elPM) elPM.textContent = pM + '% of session';
        if (elPW) elPW.textContent = pW + '% of session';

        // Animate rings and bars
        animateRing('arc-strong',   pS);
        animateRing('arc-moderate', pM);
        animateRing('arc-weak',     pW);
        animateBar('bar-strong',    pS);
        animateBar('bar-moderate',  pM);
        animateBar('bar-weak',      pW);

        // Skills gap tag cloud
        if (gapsEl) {
            const allGaps = JSON.parse(localStorage.getItem('matchai-gap-skills')) || [];
            if (allGaps.length > 0) {
                const freq = {};
                allGaps.forEach(s => { freq[s] = (freq[s] || 0) + 1; });
                const sorted = Object.entries(freq).sort((a,b) => b[1]-a[1]).slice(0, 20);
                gapsEl.innerHTML = sorted.map(([skill, count]) => {
                    const tier = count >= 3 ? 'hot' : count === 2 ? 'warm' : 'cool';
                    return `<span class="an-skill-pill an-skill-pill--${tier}">
                        ${skill}
                        ${count > 1 ? `<span class="an-skill-pill__badge">${count}×</span>` : ''}
                    </span>`;
                }).join('');
            } else {
                gapsEl.innerHTML = '<span class="an-no-skills">No gap data yet.</span>';
            }
        }

        // Area chart — color each point by fit zone
        if (myChart) myChart.destroy();

        const labels = sessionData.map(h => h.job.length > 18 ? h.job.slice(0,18) + '…' : h.job);
        const values = sessionData.map(h => h.score);
        const pointColors = values.map(v =>
            v >= 75 ? '#34d399' : v >= 40 ? '#fbbf24' : '#f87171'
        );
        const pointBorders = values.map(v =>
            v >= 75 ? '#10b981' : v >= 40 ? '#d97706' : '#dc2626'
        );

        myChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: 'Match Score',
                    data: values,
                    borderColor: 'rgba(96,165,250,0.7)',
                    borderWidth: 2.5,
                    tension: 0.42,
                    fill: true,
                    backgroundColor: function(context) {
                        const chart = context.chart;
                        const { ctx: c, chartArea } = chart;
                        if (!chartArea) return 'transparent';
                        const gradient = c.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
                        gradient.addColorStop(0,   'rgba(96,165,250,0.28)');
                        gradient.addColorStop(0.5, 'rgba(6,182,212,0.12)');
                        gradient.addColorStop(1,   'rgba(6,182,212,0)');
                        return gradient;
                    },
                    pointBackgroundColor: pointColors,
                    pointBorderColor:     pointBorders,
                    pointRadius: 7,
                    pointHoverRadius: 10,
                    pointBorderWidth: 2,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(7,12,28,0.97)',
                        titleFont: { family: "'Outfit', sans-serif", size: 13, weight: '700' },
                        bodyFont:  { family: "'Outfit', sans-serif", size: 12 },
                        padding: 14, cornerRadius: 14,
                        displayColors: true,
                        callbacks: {
                            label: c => {
                                const v = c.raw;
                                const zone = v >= 75 ? '🟢 Strong Fit' : v >= 40 ? '🟡 Moderate Fit' : '🔴 Weak Fit';
                                return `  ${v}%  ·  ${zone}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: {
                            color: '#475569',
                            font: { family: "'Outfit', sans-serif", size: 11 },
                            maxRotation: 30, minRotation: 0
                        }
                    },
                    y: {
                        min: 0, max: 105,
                        grid: { color: 'rgba(255,255,255,0.04)' },
                        ticks: {
                            color: '#475569',
                            font: { family: "'Outfit', sans-serif", size: 11 },
                            callback: v => v + '%',
                            stepSize: 25
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
