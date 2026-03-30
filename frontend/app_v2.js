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
            
            
            // Re-apply tilts if switching back to interactive pages
            applyTiltToCards('.upload-card');
            
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
            
            // Re-apply tilts to match cards since they were in display:none
            applyTiltToCards('.match-card');
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
    const jobUrlInput = document.getElementById('job-url-input');
    const addUrlBtn = document.getElementById('add-url-btn');

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
    let stateJobUrls = [];

    // Enable/Disable button
    function updateCompareButton() {
        if (stateCvFile && (stateJobFiles.length > 0 || stateJobUrls.length > 0)) {
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
        if (stateJobFiles.length + stateJobUrls.length + validFiles.length > 5) {
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

    // --- Web URL Handler ---
    addUrlBtn.addEventListener('click', () => {
        const urlRaw = jobUrlInput.value.trim();
        if (!urlRaw) return;
        
        let formattedUrl = urlRaw;
        if (!formattedUrl.startsWith('http://') && !formattedUrl.startsWith('https://')) {
            formattedUrl = 'https://' + formattedUrl;
        }

        if (!isValidUrl(formattedUrl)) {
            alert("Please enter a valid website URL.");
            return;
        }

        if (stateJobFiles.length + stateJobUrls.length >= 5) {
            alert("You can only compare up to 5 target domains at a time.");
            return;
        }

        if (!stateJobUrls.includes(formattedUrl)) {
            stateJobUrls.push(formattedUrl);
        }
        
        jobUrlInput.value = '';
        renderJobFiles();
        updateCompareButton();
    });

    // Handle 'Enter' key inside URL input
    jobUrlInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            addUrlBtn.click();
        }
    });


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

        // Render URL links
        stateJobUrls.forEach((url, index) => {
            let displayUrl = url;
            try { displayUrl = new URL(url).hostname; } catch(e){}

            const el = document.createElement('div');
            el.className = 'file-item';
            el.innerHTML = `
                <div class="file-info">
                    <i class="fa-solid fa-link file-icon" style="color:var(--primary-light)"></i>
                    <div class="file-details">
                        <h5>${displayUrl}</h5>
                        <span>Web Domain Extraction</span>
                    </div>
                </div>
                <button class="remove-file-btn remove-url-btn" data-index="${index}"><i class="fa-solid fa-trash-can"></i></button>
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

        document.querySelectorAll('.remove-url-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const idx = parseInt(e.currentTarget.getAttribute('data-index'));
                stateJobUrls.splice(idx, 1);
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

            stateJobUrls.forEach(url => {
                formData.append('job_urls', url);
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
        stateJobUrls = [];
        cvFileInput.value = '';
        jobFileInput.value = '';
        jobUrlInput.value = '';
        renderCvFile();
        renderJobFiles();
        updateCompareButton();
    });

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
                
                let fitLabel = "moderate fit";
                let fitColor = "var(--warning)";

                // Change stroke-color gradient dynamically based on score
                if (percentScore > 75) {
                    circle.style.stroke = "url(#gradientStroke)";
                    fitLabel = "strong fit";
                    fitColor = "var(--primary-light)";
                } else if (percentScore > 40) {
                    circle.style.stroke = "var(--warning)";
                } else {
                    circle.style.stroke = "var(--danger)";
                    fitLabel = "weak fit";
                    fitColor = "var(--danger)";
                }

                const labelEl = card.querySelector('.summary-fit-label');
                labelEl.textContent = fitLabel;
                labelEl.style.color = fitColor;

            }, 100);

            // Set up Page Navigation logic instead of accordion
            const readMoreBtn = clone.querySelector('.read-more-btn');
            const summaryText = match.llm_summary || "We analyzed your CV alongside the job description. You are a strong match for this role.";

            if (readMoreBtn) {
                readMoreBtn.addEventListener('click', () => {
                    // Navigate to details page
                    document.getElementById('view-dashboard').classList.add('hidden');
                    document.getElementById('view-dashboard').classList.remove('active-view');
                    
                    document.getElementById('view-match-details').classList.remove('hidden');
                    document.getElementById('view-match-details').classList.add('active-view');
                    
                    // Populate details
                    document.getElementById('details-job-title').textContent = jobTitle;
                    document.getElementById('details-ai-summary').textContent = summaryText;
                });
            }

            matchesContainer.appendChild(clone);
        });

        // Persist Data to LocalStorage for Analytics
        const overallHistory = JSON.parse(localStorage.getItem('matchai-history')) || [];
        const combinedHistory = [...overallHistory, ...currentSessionHistory];
        localStorage.setItem('matchai-history', JSON.stringify(combinedHistory));

        // Apply interactive 3D physics to newly rendered match cards
        applyTiltToCards('.match-card');
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

    // --- Interactive 3D Card Tilt Physics ---
    function applyTiltToCards(selector) {
        const cards = document.querySelectorAll(selector);
        cards.forEach(card => {
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;
                
                const rotateX = ((y - centerY) / centerY) * -12; // Max 12 deg tilt
                const rotateY = ((x - centerX) / centerX) * 12;
                
                card.style.transform = `perspective(1200px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
                card.style.transition = 'transform 0.1s ease-out, box-shadow 0.1s ease-out';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = `perspective(1200px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)`;
                card.style.transition = 'transform 0.4s ease-out, box-shadow 0.4s ease-out';
            });
        });
    }

    // Initialize 3D on static hero cards
    applyTiltToCards('.upload-card');

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
        if (!ctx) return;

        const historyRaw = JSON.parse(localStorage.getItem('matchai-history')) || [];
        
        // Take last 15 points to prevent overcrowding
        const historyData = historyRaw.slice(-15);
        
        const labels = historyData.length ? historyData.map(h => h.job.length > 20 ? h.job.substring(0,20)+'...' : h.job) : ['No Data'];
        const values = historyData.length ? historyData.map(h => h.score) : [0];

        // Fetch dynamic color from active theme engine
        const rootStyles = getComputedStyle(document.documentElement);
        const primaryColor = rootStyles.getPropertyValue('--primary-light').trim() || '#60a5fa';

        if (myChart) {
            myChart.destroy();
        }

        myChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Match Score (%)',
                    data: values,
                    borderColor: primaryColor,
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#fff',
                    pointBorderColor: primaryColor,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#f8fafc', font: { family: "'Outfit', sans-serif", size: 14 } } },
                    tooltip: { backgroundColor: 'rgba(15, 23, 42, 0.9)', titleFont: { family: "'Outfit', sans-serif" }, bodyFont: { family: "'Outfit', sans-serif" }, padding: 12, cornerRadius: 8 }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#94a3b8', font: { family: "'Outfit', sans-serif" } }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#94a3b8', font: { family: "'Outfit', sans-serif" }, maxRotation: 45, minRotation: 45 }
                    }
                }
            }
        });
    }

    const clearBtn = document.getElementById('clear-history-btn');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
             localStorage.removeItem('matchai-history');
             renderChart();
        });
    }

});
