// SIH26188 — Verification & Dashboard Controller
let currentVerificationResult = null;
let webcamStream = null;
let currentRiskFilter = 'ALL';
let historySearchQuery = '';

// Load initial statistics
document.addEventListener("DOMContentLoaded", () => {
    fetchStats();
});

async function fetchStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        const totalEl = document.getElementById('stat-total');
        const lowEl = document.getElementById('stat-low');
        const medEl = document.getElementById('stat-medium');
        const highEl = document.getElementById('stat-high');
        
        if (totalEl) totalEl.textContent = data.total || 0;
        if (lowEl) lowEl.textContent = data.low || 0;
        if (medEl) medEl.textContent = data.medium || 0;
        if (highEl) highEl.textContent = data.high || 0;
    } catch (e) {
        console.warn("Could not fetch stats:", e);
    }
}

// Sample Loader
function loadSample(sampleId) {
    document.getElementById('selected-sample-id').value = sampleId;
    
    const sampleMap = {
        "clean_aadhaar": {
            doc: "/static/samples/sample_clean_aadhaar.jpg",
            selfie: "/static/samples/selfie_person1.jpg",
            name: "sample_clean_aadhaar.jpg",
            selfieName: "selfie_person1.jpg"
        },
        "tampered_pan": {
            doc: "/static/samples/sample_tampered_pan.jpg",
            selfie: "/static/samples/selfie_person2.jpg",
            name: "sample_tampered_pan.jpg",
            selfieName: "selfie_person2.jpg"
        },
        "face_mismatch": {
            doc: "/static/samples/sample_face_mismatch_doc.jpg",
            selfie: "/static/samples/selfie_mismatch.jpg",
            name: "sample_face_mismatch_doc.jpg",
            selfieName: "selfie_mismatch.jpg"
        },
        "poor_quality": {
            doc: "/static/samples/sample_poor_quality_dl.jpg",
            selfie: "/static/samples/selfie_person4.jpg",
            name: "sample_poor_quality_dl.jpg",
            selfieName: "selfie_person4.jpg"
        }
    };
    
    const sample = sampleMap[sampleId];
    if (!sample) return;
    
    // Set Doc Preview
    document.getElementById('doc-preview-img').src = sample.doc;
    document.getElementById('doc-file-name').textContent = sample.name;
    document.getElementById('doc-placeholder').classList.add('hidden');
    document.getElementById('doc-preview-container').classList.remove('hidden');
    document.getElementById('doc-badge').classList.remove('hidden');
    document.getElementById('doc-clear-btn').classList.remove('hidden');
    
    // Set Selfie Preview
    document.getElementById('selfie-preview-img').src = sample.selfie;
    document.getElementById('selfie-file-name').textContent = sample.selfieName;
    document.getElementById('selfie-placeholder').classList.add('hidden');
    document.getElementById('selfie-preview-container').classList.remove('hidden');
    document.getElementById('selfie-clear-btn').classList.remove('hidden');
    
    // Reset manual uploads
    document.getElementById('doc-file-input').value = '';
    document.getElementById('selfie-file-input').value = '';
    document.getElementById('selfie-base64').value = '';
    
    // Smooth scroll to upload form
    document.getElementById('verify-form').scrollIntoView({ behavior: 'smooth', block: 'center' });
}
// File Input Handlers
function handleDocFileChange(input) {
    if (input.files && input.files[0]) {
        document.getElementById('selected-sample-id').value = '';
        const file = input.files[0];
        const reader = new FileReader();
        reader.onload = (e) => {
            document.getElementById('doc-preview-img').src = e.target.result;
            document.getElementById('doc-file-name').textContent = file.name;
            document.getElementById('doc-placeholder').classList.add('hidden');
            document.getElementById('doc-preview-container').classList.remove('hidden');
            document.getElementById('doc-badge').classList.remove('hidden');
            document.getElementById('doc-clear-btn').classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    }
}

function handleSelfieFileChange(input) {
    if (input.files && input.files[0]) {
        document.getElementById('selected-sample-id').value = '';
        document.getElementById('selfie-base64').value = '';
        const file = input.files[0];
        const reader = new FileReader();
        reader.onload = (e) => {
            document.getElementById('selfie-preview-img').src = e.target.result;
            document.getElementById('selfie-file-name').textContent = file.name;
            document.getElementById('selfie-placeholder').classList.add('hidden');
            document.getElementById('selfie-preview-container').classList.remove('hidden');
            document.getElementById('selfie-clear-btn').classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    }
}

function clearDocFile() {
    document.getElementById('doc-file-input').value = '';
    document.getElementById('selected-sample-id').value = '';
    document.getElementById('doc-preview-img').src = '';
    document.getElementById('doc-placeholder').classList.remove('hidden');
    document.getElementById('doc-preview-container').classList.add('hidden');
    document.getElementById('doc-badge').classList.add('hidden');
    document.getElementById('doc-clear-btn').classList.add('hidden');
}

function clearSelfieFile() {
    document.getElementById('selfie-file-input').value = '';
    document.getElementById('selfie-base64').value = '';
    document.getElementById('selected-sample-id').value = '';
    document.getElementById('selfie-preview-img').src = '';
    document.getElementById('selfie-placeholder').classList.remove('hidden');
    document.getElementById('selfie-preview-container').classList.add('hidden');
    document.getElementById('selfie-clear-btn').classList.add('hidden');
}

// Live Webcam Modal & Capture
async function openWebcamModal() {
    const modal = document.getElementById('webcam-modal');
    modal.classList.remove('hidden');
    try {
        webcamStream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
        const video = document.getElementById('webcam-video');
        video.srcObject = webcamStream;
    } catch (err) {
        alert('Webcam access error: ' + err.message);
        closeWebcamModal();
    }
}

function closeWebcamModal() {
    const modal = document.getElementById('webcam-modal');
    modal.classList.add('hidden');
    if (webcamStream) {
        webcamStream.getTracks().forEach(track => track.stop());
        webcamStream = null;
    }
}

function captureWebcamSnapshot() {
    const video = document.getElementById('webcam-video');
    const canvas = document.getElementById('webcam-canvas');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    const base64Data = canvas.toDataURL('image/jpeg', 0.95);
    document.getElementById('selfie-base64').value = base64Data;
    document.getElementById('selected-sample-id').value = '';
    
    document.getElementById('selfie-preview-img').src = base64Data;
    document.getElementById('selfie-file-name').textContent = 'live_webcam_snapshot.jpg';
    document.getElementById('selfie-placeholder').classList.add('hidden');
    document.getElementById('selfie-preview-container').classList.remove('hidden');
    document.getElementById('selfie-clear-btn').classList.remove('hidden');
    
    closeWebcamModal();
}
// Submit Form Handler & Pipeline Runner
async function handleVerifySubmit(e) {
    e.preventDefault();
    
    const sampleId = document.getElementById('selected-sample-id').value;
    const docInput = document.getElementById('doc-file-input');
    const selfieInput = document.getElementById('selfie-file-input');
    const selfieBase64 = document.getElementById('selfie-base64').value;
    
    if (!sampleId && !docInput.files[0]) {
        alert('Please upload or select an Identity Document.');
        return;
    }
    if (!sampleId && !selfieInput.files[0] && !selfieBase64) {
        alert('Please upload, capture, or select a live Selfie.');
        return;
    }
    
    const formData = new FormData(document.getElementById('verify-form'));
    
    // Show Progress
    const progressSec = document.getElementById('progress-section');
    const progressFill = document.getElementById('progress-bar-fill');
    const progressPct = document.getElementById('progress-percent');
    const progressText = document.getElementById('progress-status-text');
    const resultsDash = document.getElementById('results-dashboard');
    const verifyBtn = document.getElementById('verify-btn');
    
    progressSec.classList.remove('hidden');
    resultsDash.classList.add('hidden');
    verifyBtn.disabled = true;
    
    // Ticker animation
    let pct = 15;
    progressFill.style.width = pct + '%';
    progressPct.textContent = pct + '%';
    progressText.textContent = 'Preprocessing & Initializing RapidOCR...';
    
    const interval = setInterval(() => {
        if (pct < 85) {
            pct += 15;
            progressFill.style.width = pct + '%';
            progressPct.textContent = pct + '%';
            if (pct === 30) progressText.textContent = 'Running Error Level Analysis (ELA) & Forensics...';
            if (pct === 60) progressText.textContent = 'Extracting YuNet Facial Landmarks & SFace Embeddings...';
            if (pct === 75) progressText.textContent = 'Computing Composite Risk & Checksum Verifications...';
        }
    }, 450);
    
    try {
        const response = await fetch('/api/verify', {
            method: 'POST',
            body: formData
        });
        
        clearInterval(interval);
        progressFill.style.width = '100%';
        progressPct.textContent = '100%';
        progressText.textContent = 'Verification Complete!';
        
        const data = await response.json();
        
        setTimeout(() => {
            progressSec.classList.add('hidden');
            verifyBtn.disabled = false;
            
            if (data.status === 'success') {
                currentVerificationResult = data;
                renderResults(data);
                fetchStats();
            } else {
                alert('Verification error: ' + (data.message || 'Unknown error occurred.'));
            }
        }, 500);
        
    } catch (err) {
        clearInterval(interval);
        progressSec.classList.add('hidden');
        verifyBtn.disabled = false;
        alert('Server communication error: ' + err.message);
    }
}

// Render Results Dashboard
function renderResults(data) {
    const resultsDash = document.getElementById('results-dashboard');
    resultsDash.classList.remove('hidden');
    
    const risk = data.risk_assessment || {};
    const ocr = data.ocr || {};
    const tampering = data.tampering || {};
    const face = data.face_verification || {};
    const validation = data.validation || {};
    
    // 1. Master Risk Banner
    const banner = document.getElementById('risk-banner');
    const iconBox = document.getElementById('risk-icon-box');
    const verdictTitle = document.getElementById('risk-verdict-title');
    const riskBadge = document.getElementById('risk-level-badge');
    const riskScoreVal = document.getElementById('risk-score-value');
    const riskCircle = document.getElementById('risk-score-circle');
    const riskGaugePct = document.getElementById('risk-gauge-pct');
    const screeningIdEl = document.getElementById('risk-screening-id');
    
    screeningIdEl.textContent = `Screening ID: ${data.screening_id} | ${data.timestamp}`;
    riskScoreVal.textContent = risk.risk_score.toFixed(1);
    riskGaugePct.textContent = Math.round(risk.risk_score) + '%';
    
    if (risk.risk_level === 'LOW') {
        banner.className = 'rounded-2xl p-6 border shadow-2xl transition-all bg-emerald-950/40 border-emerald-500/40 text-emerald-100';
        iconBox.className = 'w-14 h-14 rounded-2xl flex items-center justify-center text-3xl shadow-inner bg-emerald-500/20 text-emerald-400 border border-emerald-500/30';
        iconBox.innerHTML = '<i data-lucide="shield-check" class="w-8 h-8"></i>';
        verdictTitle.textContent = risk.verdict || 'VERIFIED / APPROVED';
        verdictTitle.className = 'text-2xl font-black tracking-tight text-emerald-400';
        riskBadge.className = 'px-3 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30';
        riskBadge.textContent = 'LOW RISK (SAFE)';
        riskCircle.className = 'w-12 h-12 rounded-full border-4 border-emerald-500 flex items-center justify-center font-bold text-xs text-emerald-400';
    } else if (risk.risk_level === 'MEDIUM') {
        banner.className = 'rounded-2xl p-6 border shadow-2xl transition-all bg-amber-950/40 border-amber-500/40 text-amber-100';
        iconBox.className = 'w-14 h-14 rounded-2xl flex items-center justify-center text-3xl shadow-inner bg-amber-500/20 text-amber-400 border border-amber-500/30';
        iconBox.innerHTML = '<i data-lucide="alert-triangle" class="w-8 h-8"></i>';
        verdictTitle.textContent = risk.verdict || 'MANUAL REVIEW REQUIRED';
        verdictTitle.className = 'text-2xl font-black tracking-tight text-amber-400';
        riskBadge.className = 'px-3 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-amber-500/20 text-amber-400 border border-amber-500/30';
        riskBadge.textContent = 'MEDIUM RISK';
        riskCircle.className = 'w-12 h-12 rounded-full border-4 border-amber-500 flex items-center justify-center font-bold text-xs text-amber-400';
    } else {
        banner.className = 'rounded-2xl p-6 border shadow-2xl transition-all bg-rose-950/40 border-rose-500/40 text-rose-100';
        iconBox.className = 'w-14 h-14 rounded-2xl flex items-center justify-center text-3xl shadow-inner bg-rose-500/20 text-rose-400 border border-rose-500/30';
        iconBox.innerHTML = '<i data-lucide="shield-alert" class="w-8 h-8"></i>';
        verdictTitle.textContent = risk.verdict || 'REJECTED / SUSPECT FRAUD';
        verdictTitle.className = 'text-2xl font-black tracking-tight text-rose-400';
        riskBadge.className = 'px-3 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-rose-500/20 text-rose-400 border border-rose-500/30';
        riskBadge.textContent = 'HIGH RISK (FRAUD)';
        riskCircle.className = 'w-12 h-12 rounded-full border-4 border-rose-500 flex items-center justify-center font-bold text-xs text-rose-400';
    }
    
    // Explainable Reasons List
    const reasonsList = document.getElementById('risk-reasons-list');
    reasonsList.innerHTML = '';
    (risk.reasons || []).forEach(r => {
        const li = document.createElement('li');
        li.className = 'flex items-start space-x-2';
        const isBad = r.includes('CRITICAL') || r.includes('Tampering') || r.includes('Mismatch') || r.includes('Failure');
        const dotColor = isBad ? 'text-rose-400' : 'text-emerald-400';
        li.innerHTML = `<span class="${dotColor} font-bold">&bull;</span><span>${r}</span>`;
        reasonsList.appendChild(li);
    });
    
    // 2. Face Verification
    const faceMatchBadge = document.getElementById('face-match-badge');
    if (face.is_match) {
        faceMatchBadge.className = 'px-2.5 py-1 rounded text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30';
        faceMatchBadge.textContent = 'MATCH';
    } else {
        faceMatchBadge.className = 'px-2.5 py-1 rounded text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30';
        faceMatchBadge.textContent = 'MISMATCH';
    }
    
    if (face.doc_face_crop) {
        document.getElementById('face-doc-crop').src = '/uploads/' + face.doc_face_crop;
    }
    if (face.selfie_face_crop) {
        document.getElementById('face-selfie-crop').src = '/uploads/' + face.selfie_face_crop;
    }
    document.getElementById('face-similarity-text').textContent = (face.similarity_score || 0).toFixed(1) + '%';
    document.getElementById('face-l2-text').textContent = (face.l2_distance || 0).toFixed(3);
    document.getElementById('face-status-msg').textContent = face.message || '';
    
    // 3. Tampering Forensics
    const tamperBadge = document.getElementById('tamper-badge');
    const tScore = tampering.tampering_score || 0;
    if (tampering.classification === 'Normal') {
        tamperBadge.className = 'px-2.5 py-1 rounded text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30';
        tamperBadge.textContent = 'NORMAL';
    } else if (tampering.classification === 'Review') {
        tamperBadge.className = 'px-2.5 py-1 rounded text-xs font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30';
        tamperBadge.textContent = 'REVIEW';
    } else {
        tamperBadge.className = 'px-2.5 py-1 rounded text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30';
        tamperBadge.textContent = 'SUSPICIOUS';
    }
    
    if (tampering.forensic_heatmap) {
        document.getElementById('tamper-heatmap-img').src = '/uploads/' + tampering.forensic_heatmap;
    }
    document.getElementById('tamper-score-text').textContent = tScore.toFixed(1);
    document.getElementById('tamper-ela-text').textContent = (tampering.metrics?.anomalous_pixel_percentage || 0).toFixed(1) + '%';
    document.getElementById('tamper-noise-text').textContent = (tampering.metrics?.noise_inconsistency_ratio || 0).toFixed(1);
    
    // 4. OCR
    document.getElementById('ocr-conf-badge').textContent = (ocr.overall_confidence || 0).toFixed(1) + '% Conf';
    document.getElementById('ocr-doc-type').textContent = ocr.document_type || 'Unknown';
    
    const fields = ocr.extracted_fields || {};
    document.getElementById('ocr-name').textContent = fields.name?.value || 'N/A';
    document.getElementById('ocr-number').textContent = fields.document_number?.value || 'N/A';
    document.getElementById('ocr-dob').textContent = fields.dob?.value || 'N/A';
    document.getElementById('ocr-expiry').textContent = fields.expiry_date?.value || 'Lifetime / Not Applicable';
    document.getElementById('ocr-gender').textContent = fields.gender?.value || 'N/A';
    
    // 5. Validation Card
    const valBadge = document.getElementById('val-status-badge');
    const failures = validation.validation_failures || [];
    if (failures.length === 0) {
        valBadge.className = 'px-2.5 py-1 rounded text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30';
        valBadge.textContent = 'PASSED';
    } else {
        valBadge.className = 'px-2.5 py-1 rounded text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30';
        valBadge.textContent = `${failures.length} ISSUE(S)`;
    }
    
    document.getElementById('val-doc-num-status').textContent = validation.doc_number_valid ? 'Valid Checksum' : 'Invalid Format';
    document.getElementById('val-doc-num-status').className = validation.doc_number_valid ? 'font-semibold text-emerald-400' : 'font-semibold text-rose-400';
    
    const ageText = validation.age_years ? `Valid (${validation.age_years} yrs)` : (validation.dob_valid ? 'Valid' : 'Invalid');
    document.getElementById('val-age-status').textContent = ageText;
    document.getElementById('val-age-status').className = validation.age_valid ? 'font-semibold text-emerald-400' : 'font-semibold text-rose-400';
    
    document.getElementById('val-expiry-status').textContent = validation.is_expired ? 'Expired' : 'Active / Valid';
    document.getElementById('val-expiry-status').className = validation.is_expired ? 'font-semibold text-rose-400' : 'font-semibold text-emerald-400';
    
    document.getElementById('val-name-status').textContent = validation.name_valid ? 'Extracted' : 'Missing';
    document.getElementById('val-name-status').className = validation.name_valid ? 'font-semibold text-emerald-400' : 'font-semibold text-rose-400';
    
    lucide.createIcons();
    resultsDash.scrollIntoView({ behavior: 'smooth' });
}
// History Management
async function fetchHistory() {
    const tableBody = document.getElementById('history-table-body');
    if (!tableBody) return;
    
    let url = `/api/screenings?risk=${currentRiskFilter}`;
    if (historySearchQuery) {
        url += `&search=${encodeURIComponent(historySearchQuery)}`;
    }
    
    try {
        const res = await fetch(url);
        const records = await res.json();
        
        if (!records || records.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="8" class="py-12 text-center text-slate-500">No screening records found matching current filters.</td></tr>`;
            return;
        }
        
        tableBody.innerHTML = records.map(r => {
            let riskBadgeClass = 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
            if (r.risk_level === 'MEDIUM') riskBadgeClass = 'bg-amber-500/20 text-amber-400 border-amber-500/30';
            if (r.risk_level === 'HIGH') riskBadgeClass = 'bg-rose-500/20 text-rose-400 border-rose-500/30';
            
            const faceBadge = r.face_match 
                ? '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">MATCH</span>' 
                : '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">MISMATCH</span>';
                
            const tamperBadge = r.tampering_classification === 'Suspicious'
                ? '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">TAMPERED</span>'
                : '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">CLEAN</span>';

            return `
                <tr class="hover:bg-slate-800/40 transition-colors">
                    <td class="py-3 px-4">
                        <span class="font-mono font-bold text-slate-200">${r.screening_id}</span>
                        <div class="text-[10px] text-slate-500 mt-0.5">${r.timestamp}</div>
                    </td>
                    <td class="py-3 px-4 font-medium text-emerald-400">${r.document_type || 'Unknown'}</td>
                    <td class="py-3 px-4 font-medium text-white">${r.extracted_name || 'N/A'}</td>
                    <td class="py-3 px-4 font-mono text-slate-300">${r.extracted_doc_number || 'N/A'}</td>
                    <td class="py-3 px-4 text-center">${faceBadge}</td>
                    <td class="py-3 px-4 text-center">${tamperBadge}</td>
                    <td class="py-3 px-4 text-center">
                        <span class="px-2.5 py-1 rounded-full text-[10px] font-bold border ${riskBadgeClass}">${r.risk_level} (${(r.composite_risk_score || 0).toFixed(0)})</span>
                    </td>
                    <td class="py-3 px-4 text-right space-x-2">
                        <button onclick="viewScreeningDetail('${r.screening_id}')" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-medium border border-slate-700">View</button>
                        <button onclick="deleteRecord('${r.screening_id}')" class="px-2 py-1 rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 text-[11px] border border-rose-500/30">Delete</button>
                    </td>
                </tr>
            `;
        }).join('');
        
        lucide.createIcons();
    } catch (e) {
        console.error("Error fetching history:", e);
    }
}

function setRiskFilter(filter) {
    currentRiskFilter = filter;
    document.querySelectorAll('.risk-tab').forEach(btn => {
        btn.className = 'risk-tab px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-slate-400 hover:text-white';
    });
    const activeBtn = document.getElementById(`filter-${filter.toLowerCase()}`);
    if (activeBtn) {
        activeBtn.className = 'risk-tab px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30';
    }
    fetchHistory();
}

let searchTimeout;
function handleHistorySearch(query) {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        historySearchQuery = query.trim();
        fetchHistory();
    }, 300);
}

async function viewScreeningDetail(screeningId) {
    try {
        const res = await fetch(`/api/screening/${screeningId}`);
        const data = await res.json();
        if (data.status !== 'success') return;
        
        const item = data.data;
        document.getElementById('modal-screening-id').textContent = item.screening_id;
        document.getElementById('modal-timestamp').textContent = `Screened on: ${item.timestamp}`;
        
        const modalBody = document.getElementById('modal-body-content');
        modalBody.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                <div class="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                    <p class="text-slate-400 text-[10px]">Risk Assessment</p>
                    <p class="text-lg font-black text-white mt-1">${item.risk_level} (${item.composite_risk_score})</p>
                    <p class="text-slate-400 mt-1">${item.verdict}</p>
                </div>
                <div class="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                    <p class="text-slate-400 text-[10px]">Facial Biometrics</p>
                    <p class="text-lg font-black ${item.face_match ? 'text-emerald-400' : 'text-rose-400'} mt-1">${item.face_match ? 'Matched' : 'Mismatch'} (${item.face_similarity}%)</p>
                </div>
                <div class="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                    <p class="text-slate-400 text-[10px]">Tampering Forensics</p>
                    <p class="text-lg font-black ${item.tampering_classification === 'Suspicious' ? 'text-rose-400' : 'text-emerald-400'} mt-1">${item.tampering_classification} (${item.tampering_score})</p>
                </div>
            </div>

            <div class="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs space-y-2">
                <h4 class="font-bold text-slate-300 uppercase tracking-wider text-[11px]">Extracted Identity Details</h4>
                <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                    <div><span class="text-slate-500 block">Name:</span> <span class="text-white font-medium">${item.extracted_name || 'N/A'}</span></div>
                    <div><span class="text-slate-500 block">Doc Number:</span> <span class="text-cyan-400 font-mono font-medium">${item.extracted_doc_number || 'N/A'}</span></div>
                    <div><span class="text-slate-500 block">DOB:</span> <span class="text-slate-300 font-mono">${item.extracted_dob || 'N/A'}</span></div>
                    <div><span class="text-slate-500 block">Expiry:</span> <span class="text-slate-300">${item.extracted_expiry || 'N/A'}</span></div>
                </div>
            </div>

            ${item.forensic_heatmap_filename ? `
                <div class="bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <p class="text-xs font-bold text-slate-300 mb-2">Forensic ELA Heatmap Overlay</p>
                    <div class="max-h-48 rounded-lg overflow-hidden flex items-center justify-center bg-black">
                        <img src="/uploads/${item.forensic_heatmap_filename}" class="max-h-48 object-contain">
                    </div>
                </div>
            ` : ''}
        `;
        
        document.getElementById('history-modal').classList.remove('hidden');
        lucide.createIcons();
    } catch (e) {
        alert('Could not load screening details.');
    }
}

function closeHistoryModal() {
    document.getElementById('history-modal').classList.add('hidden');
}

async function deleteRecord(screeningId) {
    if (!confirm(`Are you sure you want to delete screening ${screeningId}?`)) return;
    try {
        const res = await fetch(`/api/screening/${screeningId}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.status === 'success') {
            fetchHistory();
            fetchStats();
        }
    } catch (e) {
        alert('Error deleting record.');
    }
}

function downloadJsonReport() {
    if (!currentVerificationResult) return;
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentVerificationResult, null, 2));
    const dlAnchorElem = document.createElement('a');
    dlAnchorElem.setAttribute("href", dataStr);
    dlAnchorElem.setAttribute("download", `verification_audit_${currentVerificationResult.screening_id}.json`);
    dlAnchorElem.click();
}
