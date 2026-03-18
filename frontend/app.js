document.addEventListener('DOMContentLoaded', () => {
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

        data.matches.forEach((match, index) => {
            const clone = template.content.cloneNode(true);
            const card = clone.querySelector('.match-card');
            card.style.animationDelay = `${index * 0.15}s`;

            clone.querySelector('.job-id').textContent = cleanJobId(match.job_id);
            
            const gap = match.gap_analysis;
            
            // Core FAISS similarity mapping
            let percentScore = Math.max(0, match.similarity_score * 100);
            if (percentScore > 100) percentScore = 100;
            
            clone.querySelector('.score-value').textContent = Math.round(percentScore);

            // Animate SVG Ring
            setTimeout(() => {
                const circle = card.querySelector('.progress-ring__circle');
                const radius = circle.r.baseVal.value; // 42
                const circumference = radius * 2 * Math.PI; // 263.89
                // Correctly calculate offset backwards for a smooth circle fill
                const offset = circumference - (percentScore / 100) * circumference;
                circle.style.strokeDashoffset = offset;
                
                // Change stroke-color gradient dynamically based on score
                if (percentScore > 80) {
                    circle.style.stroke = "url(#gradientStroke)";
                } else if (percentScore > 40) {
                    circle.style.stroke = "var(--warning)";
                } else {
                    circle.style.stroke = "var(--danger)";
                }
            }, 100);

            const strengthsContainer = clone.querySelector('.strengths-tags');
            const oppsContainer = clone.querySelector('.opportunities-tags');

            if (gap && !gap.error) {
                if (!gap.matched_skills || gap.matched_skills.length === 0) {
                    strengthsContainer.innerHTML = '<span class="insight-text">No technical overlap detected.</span>';
                } else {
                    gap.matched_skills.forEach(skill => {
                        const span = document.createElement('span');
                        span.className = 'tag strength';
                        span.textContent = skill;
                        strengthsContainer.appendChild(span);
                    });
                }

                if (!gap.missing_skills || gap.missing_skills.length === 0) {
                    oppsContainer.innerHTML = '<span class="insight-text" style="color:var(--success)">Optimal contextual overlap.</span>';
                } else {
                    gap.missing_skills.slice(0, 10).forEach(skill => {
                        const span = document.createElement('span');
                        span.className = 'tag opportunity';
                        span.textContent = skill;
                        oppsContainer.appendChild(span);
                    });
                    
                    if (gap.missing_skills.length > 10) {
                        const span = document.createElement('span');
                        span.className = 'tag';
                        span.style.background = 'transparent';
                        span.style.border = 'none';
                        span.textContent = `+ ${gap.missing_skills.length - 10} more...`;
                        oppsContainer.appendChild(span);
                    }
                }
            } else {
                strengthsContainer.innerHTML = '<span class="insight-text">Gap telemetry unavailable.</span>';
                oppsContainer.innerHTML = '<span class="insight-text">Gap telemetry unavailable.</span>';
            }

            matchesContainer.appendChild(clone);
        });
    }

    // Set Date visually in top bar
    const dateOpts = { weekday: 'short', month: 'short', day: 'numeric' };
    document.getElementById('current-date').textContent = new Date().toLocaleDateString('en-US', dateOpts);
});
