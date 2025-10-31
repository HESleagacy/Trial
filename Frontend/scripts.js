const API_BASE_URL = 'http://localhost:8000';

const navToggle = document.getElementById('navToggle');
const navMobile = document.getElementById('navMobile');
const menuIcon = document.getElementById('menuIcon');
const closeIcon = document.getElementById('closeIcon');

if (navToggle) {
    navToggle.addEventListener('click', () => {
        navMobile.classList.toggle('hidden');
        menuIcon.classList.toggle('hidden');
        closeIcon.classList.toggle('hidden');
    });
}

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
            if (navMobile && !navMobile.classList.contains('hidden')) {
                navMobile.classList.add('hidden');
                menuIcon.classList.remove('hidden');
                closeIcon.classList.add('hidden');
            }
        }
    });
});

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.className = `toast toast-${type}`;
    toast.classList.remove('hidden');
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

const medForm = document.getElementById('medForm');
const adviceContainer = document.getElementById('adviceContainer');

if (medForm) {
    medForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const medName = document.getElementById('medName').value.trim();
        const medDose = document.getElementById('medDose').value.trim();
        const medFrequency = document.getElementById('medFrequency').value;
        if (!medName || !medDose || !medFrequency) {
            showToast('Please fill in all fields', 'error');
            return;
        }
        showToast('Analyzing your medication...', 'info');
        try {
            const response = await fetch(`${API_BASE_URL}/api/plan`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: medName,
                    dose: medDose,
                    frequency: medFrequency,
                    source: 'manual'
                })
            });
            if (!response.ok) throw new Error('Failed to analyze medication');
            const data = await response.json();
            displayAdvice(medName, medDose, medFrequency, data);
            showToast('Safety plan generated successfully!', 'success');
            adviceContainer && adviceContainer.scrollIntoView({ behavior: 'smooth' });
            setTimeout(() => updateDashboard(), 500);
        } catch (error) {
            console.error('Error:', error);
            showToast('Error connecting to backend. Please ensure the server is running on localhost:8000', 'error');
        }
    });
}

function displayAdvice(medName, medDose, medFrequency, data) {
    const medDisplay = document.getElementById('medDisplay');
    const timingAdvice = document.getElementById('timingAdvice');
    const foodWarnings = document.getElementById('foodWarnings');
    const delayAdvice = document.getElementById('delayAdvice');
    const replacements = document.getElementById('replacements');
    if (medDisplay) medDisplay.textContent = `${medName} ${medDose}, ${medFrequency}`;
    const adviceText = (data && data.advice) || '';
    const adviceLines = adviceText.split('\n').filter(line => line.trim());
    const timingLines = [];
    const warningLines = [];
    const delayLines = [];
    const replacementLines = [];
    adviceLines.forEach(line => {
        const cleanLine = line.replace('•', '').trim();
        if (!cleanLine) return;
        if (cleanLine.toLowerCase().includes('stay safe') || cleanLine.toLowerCase().includes('mvp has your back')) return;
        if (cleanLine.toLowerCase().includes('wait') || cleanLine.toLowerCase().includes('hour') || cleanLine.toLowerCase().includes('before') || cleanLine.toLowerCase().includes('after')) {
            if (cleanLine.toLowerCase().includes('replace')) replacementLines.push(cleanLine);
            else delayLines.push(cleanLine);
        } else if (cleanLine.toLowerCase().includes('avoid') || cleanLine.toLowerCase().includes('limit') || cleanLine.toLowerCase().includes('warning')) {
            warningLines.push(cleanLine);
        } else if (cleanLine.toLowerCase().includes('replace') || cleanLine.toLowerCase().includes('alternative') || cleanLine.toLowerCase().includes('instead')) {
            replacementLines.push(cleanLine);
        } else if (cleanLine.toLowerCase().includes('take') || cleanLine.toLowerCase().includes('timing') || cleanLine.toLowerCase().includes('best time')) {
            timingLines.push(cleanLine);
        } else {
            timingLines.push(cleanLine);
        }
    });
    if (timingAdvice) timingAdvice.textContent = timingLines.length > 0 ? timingLines.join(' ') : 'No specific timing instructions available';
    if (foodWarnings) {
        if (warningLines.length > 0) {
            foodWarnings.innerHTML = warningLines.map(warning =>
                `<div class="warning-item">
                    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="15" y1="9" x2="9" y2="15"></line>
                        <line x1="9" y1="9" x2="15" y2="15"></line>
                    </svg>
                    <span>${warning}</span>
                </div>`
            ).join('');
        } else {
            foodWarnings.innerHTML = '<p class="advice-text">No food warnings identified</p>';
        }
    }
    if (delayAdvice) delayAdvice.textContent = delayLines.length > 0 ? delayLines.join(' ') : 'No specific delay instructions available';
    if (replacements) {
        if (replacementLines.length > 0) {
            replacements.innerHTML = replacementLines.map(replacement =>
                `<div class="replacement-item">
                    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    <span>${replacement}</span>
                </div>`
            ).join('');
        } else {
            replacements.innerHTML = '<p class="advice-text">No replacements needed</p>';
        }
    }
    adviceContainer && adviceContainer.classList.remove('hidden');
    const medObj = {
        med: (data && data.med) || `${medName} ${medDose}`,
        name: medName,
        dose: medDose,
        frequency: medFrequency
    };
    try { sessionStorage.setItem('currentMedication', JSON.stringify(medObj)); } catch (e) {}
}

const feedbackForm = document.getElementById('feedbackForm');

if (feedbackForm) {
    feedbackForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const feedbackText = document.getElementById('feedbackText').value.trim();
        if (!feedbackText) {
            showToast('Please enter your feedback', 'error');
            return;
        }
        const currentMed = JSON.parse(sessionStorage.getItem('currentMedication') || '{}');
        if (!currentMed.med) {
            showToast('No medication selected', 'error');
            return;
        }
        try {
            const response = await fetch(`${API_BASE_URL}/api/feedback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ med: currentMed.med, feedback: feedbackText })
            });
            if (!response.ok) throw new Error('Failed to submit feedback');
            const result = await response.json();
            showToast(`Feedback submitted! Sentiment: ${result.sentiment}`, 'success');
            updateDashboard();
            document.getElementById('feedbackText').value = '';
        } catch (error) {
            console.error('Error:', error);
            showToast('Error submitting feedback. Please ensure the server is running.', 'error');
        }
    });
}

async function updateDashboard() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard`);
        if (!response.ok) throw new Error('Failed to fetch dashboard stats');
        const stats = await response.json();
        displayDashboard(stats);
    } catch (error) {
        console.error('Error:', error);
    }
}

function displayDashboard(stats) {
    const dashboardGrid = document.getElementById('dashboardGrid');
    if (!dashboardGrid) return;
    const statsArray = Object.entries(stats || {}).map(([medName, data]) => {
        const totalFeedback = (data.helpful || 0) + (data.confusing || 0) + (data.neutral || 0);
        const helpfulPercentage = totalFeedback > 0 ? Math.round(((data.helpful || 0) / totalFeedback) * 100) : 0;
        const medParts = medName.split(' ');
        const dose = medParts[medParts.length - 1] || '';
        const name = medParts.slice(0, -1).join(' ') || medName;
        return { medication: name, dose: dose, helpful: data.helpful || 0, confusing: data.confusing || 0, neutral: data.neutral || 0, totalFeedback, helpfulPercentage, sources: data.sources || {} };
    });
    if (statsArray.length === 0) {
        dashboardGrid.innerHTML = `
            <div class="dashboard-empty animate-fade-in">
                <svg class="icon-xlarge" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="20" x2="18" y2="10"></line>
                    <line x1="12" y1="20" x2="12" y2="4"></line>
                    <line x1="6" y1="20" x2="6" y2="14"></line>
                </svg>
                <p>Add your first medication to see feedback statistics</p>
            </div>
        `;
        return;
    }
    dashboardGrid.innerHTML = statsArray.map(stat => {
        const totalSources = (stat.sources.ocr || 0) + (stat.sources.manual || 0) + (stat.sources.api || 0);
        const ocrPercent = totalSources > 0 ? Math.round((stat.sources.ocr || 0) / totalSources * 100) : 0;
        const manualPercent = totalSources > 0 ? Math.round((stat.sources.manual || 0) / totalSources * 100) : 0;
        const apiPercent = totalSources > 0 ? Math.round((stat.sources.api || 0) / totalSources * 100) : 0;
        return `
        <div class="dashboard-card animate-slide-up">
            <div class="dashboard-header">
                <h4 class="dashboard-med-name">${stat.medication}</h4>
                <span class="dashboard-dose">${stat.dose}</span>
            </div>
            <div class="dashboard-stat">
                <div class="stat-label">Helpful Rating</div>
                <div class="stat-value">${stat.helpfulPercentage}%</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${stat.helpfulPercentage}%;"></div>
                </div>
            </div>
            <div class="dashboard-breakdown">
                <div class="sentiment-item sentiment-helpful">
                    <span class="sentiment-label">Helpful</span>
                    <span class="sentiment-count">${stat.helpful}</span>
                </div>
                <div class="sentiment-item sentiment-confusing">
                    <span class="sentiment-label">Confusing</span>
                    <span class="sentiment-count">${stat.confusing}</span>
                </div>
                <div class="sentiment-item sentiment-neutral">
                    <span class="sentiment-label">Neutral</span>
                    <span class="sentiment-count">${stat.neutral}</span>
                </div>
            </div>
            ${totalSources > 0 ? `
            <div class="dashboard-sources">
                <div class="sources-title">Source Distribution</div>
                <div class="sources-breakdown">
                    <div class="source-item">
                        <span class="source-label">OCR</span>
                        <span class="source-percent">${ocrPercent}%</span>
                    </div>
                    <div class="source-item">
                        <span class="source-label">Manual</span>
                        <span class="source-percent">${manualPercent}%</span>
                    </div>
                    <div class="source-item">
                        <span class="source-label">API</span>
                        <span class="source-percent">${apiPercent}%</span>
                    </div>
                </div>
            </div>
            ` : ''}
            <div class="dashboard-total">Total Feedback: ${stat.totalFeedback}</div>
        </div>
    `}).join('');
}

document.addEventListener('DOMContentLoaded', () => {
    updateDashboard();
    setInterval(() => updateDashboard(), 5000);
});

const observerOptions = { threshold: 0.1, rootMargin: '0px 0px -50px 0px' };

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

document.querySelectorAll('.animate-slide-up, .animate-fade-in').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
    observer.observe(el);
});

const ocrInput = document.getElementById('ocrInput');
const ocrDropzone = document.getElementById('ocrDropzone');
const ocrSelectBtn = document.getElementById('ocrSelectBtn');
const scanBtn = document.getElementById('scanBtn');
const ocrPreview = document.getElementById('ocrPreview');
const autoApplyOCR = document.getElementById('autoApplyOCR');

let selectedOCRFile = null;

if (ocrSelectBtn && ocrInput) {
    ocrSelectBtn.addEventListener('click', () => ocrInput.click());
}

if (ocrInput) {
    ocrInput.addEventListener('change', (e) => {
        const file = e.target.files && e.target.files[0];
        handleSelectedOCRFile(file);
    });
}

if (ocrDropzone) {
    ['dragenter', 'dragover'].forEach(ev => {
        ocrDropzone.addEventListener(ev, (e) => {
            e.preventDefault();
            e.stopPropagation();
            ocrDropzone.classList.add('ocr-dropzone--active');
        });
    });
    ['dragleave', 'dragend', 'drop'].forEach(ev => {
        ocrDropzone.addEventListener(ev, (e) => {
            e.preventDefault();
            e.stopPropagation();
            ocrDropzone.classList.remove('ocr-dropzone--active');
            if (ev === 'drop') {
                const file = e.dataTransfer.files && e.dataTransfer.files[0];
                handleSelectedOCRFile(file);
            }
        });
    });
}

const tabManual = document.getElementById('tab-manual');
const tabOcr = document.getElementById('tab-ocr');
const manualPanel = document.getElementById('manualPanel');
const ocrPanel = document.getElementById('ocrPanel');
const ocrName = document.getElementById('ocrName');
const ocrDose = document.getElementById('ocrDose');
const ocrFrequency = document.getElementById('ocrFrequency');
const applyOcrBtn = document.getElementById('applyOcrBtn');
const fillManualBtn = document.getElementById('fillManualBtn');

function switchToManual() {
    if (tabManual) tabManual.classList.add('tab-active');
    if (tabOcr) tabOcr.classList.remove('tab-active');
    if (manualPanel) manualPanel.classList.remove('hidden');
    if (ocrPanel) ocrPanel.classList.add('hidden');
}
function switchToOcr() {
    if (tabOcr) tabOcr.classList.add('tab-active');
    if (tabManual) tabManual.classList.remove('tab-active');
    if (ocrPanel) ocrPanel.classList.remove('hidden');
    if (manualPanel) manualPanel.classList.add('hidden');
}
if (tabManual) tabManual.addEventListener('click', switchToManual);
if (tabOcr) tabOcr.addEventListener('click', switchToOcr);

function ensureFrequencySync() {
    const manualSel = document.getElementById('medFrequency');
    if (!manualSel || !ocrFrequency) return;
    const manualOptions = Array.from(manualSel.options).map(o => ({ v: o.value, t: o.textContent }));
    ocrFrequency.innerHTML = '';
    manualOptions.forEach(opt => {
        const el = document.createElement('option');
        el.value = opt.v;
        el.textContent = opt.t;
        ocrFrequency.appendChild(el);
    });
    if (!Array.from(ocrFrequency.options).some(o => o.value === 'custom')) {
        const customOpt = document.createElement('option');
        customOpt.value = 'custom';
        customOpt.textContent = 'Other (custom)';
        ocrFrequency.appendChild(customOpt);
    }
}
ensureFrequencySync();

let ocrCustomInput = null;
function showOcrCustomInput(show) {
    if (!ocrFrequency) return;
    if (show) {
        if (!ocrCustomInput) {
            ocrCustomInput = document.createElement('input');
            ocrCustomInput.type = 'text';
            ocrCustomInput.id = 'ocrFrequencyCustom';
            ocrCustomInput.className = 'form-input';
            ocrCustomInput.placeholder = 'Enter custom frequency (e.g., every 6 hours)';
            ocrFrequency.parentNode.appendChild(ocrCustomInput);
        }
        ocrCustomInput.classList.remove('hidden');
    } else {
        if (ocrCustomInput) {
            ocrCustomInput.classList.add('hidden');
            ocrCustomInput.value = '';
        }
    }
}

if (ocrFrequency) {
    ocrFrequency.addEventListener('change', () => {
        if (ocrFrequency.value === 'custom') showOcrCustomInput(true);
        else showOcrCustomInput(false);
    });
}

if (applyOcrBtn) {
    applyOcrBtn.addEventListener('click', async () => {
        const name = (ocrName && ocrName.value.trim()) || '';
        const dose = (ocrDose && ocrDose.value.trim()) || '';
        let freq = (ocrFrequency && ocrFrequency.value) || '';
        if (freq === 'custom' && ocrCustomInput) freq = ocrCustomInput.value.trim();
        if (!name || !dose) {
            showToast('Please ensure name and dose are present (editable after scan).', 'error');
            return;
        }
        if (!freq) {
            showToast('Please select or enter a frequency', 'error');
            return;
        }
        showToast('Generating plan from OCR data...', 'info');
        try {
            const res = await fetch(`${API_BASE_URL}/api/plan`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, dose, frequency: freq || 'as-needed', source: 'ocr' })
            });
            if (!res.ok) throw new Error('Plan generation failed');
            const data = await res.json();
            displayAdvice(name, dose, freq || 'as-needed', data);
            showToast('Safety plan generated!', 'success');
            adviceContainer && adviceContainer.scrollIntoView({ behavior: 'smooth' });
            setTimeout(() => updateDashboard(), 500);
        } catch (err) {
            console.error(err);
            showToast('Error generating plan from OCR data.', 'error');
        }
    });
}

if (fillManualBtn) {
    fillManualBtn.addEventListener('click', () => {
        const name = (ocrName && ocrName.value.trim()) || '';
        const dose = (ocrDose && ocrDose.value.trim()) || '';
        let freq = (ocrFrequency && ocrFrequency.value) || '';
        if (freq === 'custom' && ocrCustomInput) freq = ocrCustomInput.value.trim();
        if (name) {
            const mn = document.getElementById('medName');
            if (mn) mn.value = name;
        }
        if (dose) {
            const md = document.getElementById('medDose');
            if (md) md.value = dose;
        }
        if (freq) {
            const sel = document.getElementById('medFrequency');
            if (sel) {
                const exists = Array.from(sel.options).some(o => o.value === freq);
                if (!exists) {
                    const opt = document.createElement('option');
                    opt.value = freq;
                    opt.textContent = freq;
                    sel.appendChild(opt);
                }
                sel.value = freq;
            }
        }
        switchToManual();
        showToast('Filled manual form with OCR data', 'info');
    });
}

function handleSelectedOCRFile(file) {
    if (!file) return;
    selectedOCRFile = file;
    const url = URL.createObjectURL(file);
    if (ocrPreview) ocrPreview.innerHTML = `<img src="${url}" alt="ocr preview"/><div class="ocr-text">${file.name}</div>`;
    if (ocrPreview) ocrPreview.classList.remove('hidden');
    const ocrFields = document.getElementById('ocrFields');
    if (ocrFields) ocrFields.classList.remove('hidden');
}

if (scanBtn) {
    scanBtn.addEventListener('click', async () => {
        if (!selectedOCRFile) {
            showToast('Please select an image first', 'error');
            return;
        }
        scanBtn.disabled = true;
        scanBtn.textContent = 'Scanning...';
        try {
            const formData = new FormData();
            formData.append('file', selectedOCRFile);
            const res = await fetch(`${API_BASE_URL}/api/ocr`, { method: 'POST', body: formData });
            if (!res.ok) throw new Error('OCR failed');
            const result = await res.json();
            const parsed = result.parsed || {};
            if (ocrName) ocrName.value = parsed.name || parsed.drug || '';
            if (ocrDose) ocrDose.value = parsed.dose || '';
            if (parsed.frequency && ocrFrequency) {
                const optExists = Array.from(ocrFrequency.options).some(o => o.value === parsed.frequency);
                if (!optExists) {
                    const opt = document.createElement('option');
                    opt.value = parsed.frequency;
                    opt.textContent = parsed.frequency;
                    ocrFrequency.appendChild(opt);
                }
                ocrFrequency.value = parsed.frequency;
                showOcrCustomInput(false);
            }
            const ocrFields = document.getElementById('ocrFields');
            if (ocrFields) ocrFields.classList.remove('hidden');
            showToast('OCR succeeded — review detected fields', 'success');
            if (result.plan) {
                const chosenFreq = (ocrFrequency && (ocrFrequency.value === 'custom' && ocrCustomInput ? ocrCustomInput.value.trim() : ocrFrequency.value)) || 'as-needed';
                displayAdvice(ocrName ? ocrName.value : document.getElementById('medName').value, ocrDose ? ocrDose.value : document.getElementById('medDose').value, chosenFreq, result.plan);
            } else if (autoApplyOCR && autoApplyOCR.checked) {
                applyOcrBtn && applyOcrBtn.click();
            }
        } catch (err) {
            console.error(err);
            showToast('OCR error. Ensure backend /api/ocr is available.', 'error');
        } finally {
            scanBtn.disabled = false;
            scanBtn.textContent = 'Scan Image';
        }
    });
}