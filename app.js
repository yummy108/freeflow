/* =============== FreeFlow Frontend Logic v3 — Better Feedback =============== */

const CONFIG = {
  repo: localStorage.getItem('ff_repo') || 'yummy108/freeflow',
  token: localStorage.getItem('ff_token') || '',
};

// ============ Mode Switch ============
const modeBtns = document.querySelectorAll('.mode-tab');
modeBtns.forEach(btn => btn.addEventListener('click', () => {
  modeBtns.forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  const target = document.getElementById(`mode-${btn.dataset.mode}`);
  if (target) target.classList.add('active');
}));

// ============ Drag & Drop ============
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('file-input');
const mdPreview = document.getElementById('md-preview');
const mdContent = document.getElementById('md-content');
const mdFilename = document.getElementById('md-filename');
const mdFilesize = document.getElementById('md-filesize');
const mdClear = document.getElementById('md-clear');

let currentMd = null;

['dragenter', 'dragover'].forEach(ev =>
  dropzone.addEventListener(ev, e => { e.preventDefault(); dropzone.classList.add('dragover'); })
);
['dragleave', 'drop'].forEach(ev =>
  dropzone.addEventListener(ev, e => { e.preventDefault(); dropzone.classList.remove('dragover'); })
);
dropzone.addEventListener('drop', e => {
  const file = e.dataTransfer.files[0];
  if (file) handleFile(file);
});
dropzone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', e => {
  const file = e.target.files[0];
  if (file) handleFile(file);
});
mdClear.addEventListener('click', () => {
  currentMd = null;
  mdPreview.classList.add('hidden');
  fileInput.value = '';
  showToast('File cleared', 'info');
});

function handleFile(file) {
  if (!file.name.endsWith('.md') && !file.name.endsWith('.markdown')) {
    showToast('❌ Please upload a .md file only', 'error');
    return;
  }
  if (file.size > 2 * 1024 * 1024) {
    showToast('❌ File too large (max 2 MB)', 'error');
    return;
  }
  const reader = new FileReader();
  reader.onload = e => {
    currentMd = { name: file.name, content: e.target.result, size: file.size };
    mdFilename.textContent = file.name;
    mdFilesize.textContent = `${(file.size / 1024).toFixed(1)} KB · ${file.name.endsWith('.md') ? '✅ Valid' : ''}`;
    mdContent.textContent = currentMd.content.slice(0, 2000) + (currentMd.content.length > 2000 ? '\n\n... (truncated for preview)' : '');
    mdPreview.classList.remove('hidden');
    mdPreview.scrollIntoView({ behavior: 'smooth', block: 'start' });
    showToast(`✅ File uploaded: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`, 'success');
  };
  reader.readAsText(file);
}

// ============ Toast System ============
function showToast(message, type = 'info', duration = 4000) {
  document.querySelectorAll('.toast').forEach(t => t.remove());
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  toast.style.cssText = `
    position: fixed; top: 20px; right: 20px; z-index: 99999;
    background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#06b6d4'};
    color: white; padding: 16px 24px;
    border-radius: 14px; box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    font-weight: 600; font-size: 15px;
    max-width: 360px; min-width: 280px;
    animation: slideInRight 0.3s ease-out;
    border: 1px solid rgba(255,255,255,0.2);
  `;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'slideOutRight 0.3s ease-in';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ============ Pipeline Trigger with LIVE Status ============
const triggerBtn = document.getElementById('trigger-pipeline');
const mdStatus = document.getElementById('md-status');
const mdResult = document.getElementById('md-result');
const statusText = document.getElementById('status-text');
const statusTitle = document.getElementById('status-title');
const resultVideo = document.getElementById('result-video');
const resultDownload = document.getElementById('result-download');
const resultLink = document.getElementById('result-link');
const progressFill = document.getElementById('progress-fill');
const actionLog = document.getElementById('action-log');
const statusPanel = document.getElementById('status-panel');

triggerBtn.addEventListener('click', async () => {
  if (!currentMd) {
    showToast('❌ Upload a .md file first!', 'error');
    return;
  }

  if (!CONFIG.token) {
    const token = prompt(
      '🔑 GitHub Personal Access Token (PAT) chahiye\n\n' +
      '1. Go to: https://github.com/settings/tokens\n' +
      '2. "Generate new token (classic)"\n' +
      '3. Note: FreeFlow · Scope: repo · Generate\n' +
      '4. Copy token (starts with ghp_)\n\n' +
      'Browser me localStorage me save hoga (safe).'
    );
    if (!token) { showToast('❌ Token chahiye', 'error'); return; }
    CONFIG.token = token;
    localStorage.setItem('ff_token', token);
    showToast('✅ PAT saved', 'success');
  }

  if (CONFIG.repo === 'yourname/freeflow') {
    const repo = prompt('GitHub repo name (e.g. yummy108/freeflow):');
    if (!repo) return;
    CONFIG.repo = repo;
    localStorage.setItem('ff_repo', repo);
  }

  // ============ START PIPELINE ============
  mdResult.classList.add('hidden');
  mdStatus.classList.remove('hidden');
  mdStatus.scrollIntoView({ behavior: 'smooth', block: 'start' });
  actionLog.innerHTML = '';
  progressFill.style.width = '0%';

  log('🚀 Pipeline started at ' + new Date().toLocaleTimeString(), 'info');
  log('📂 File: ' + currentMd.name + ' (' + (currentMd.size / 1024).toFixed(1) + ' KB)', 'info');
  log('🎙️ Voice: ' + document.getElementById('voice-select').value, 'info');

  try {
    // ===== Step 1: Upload MD =====
    log('📤 Uploading .md to GitHub...', 'action');
    setActiveStep('upload');
    setProgress(10, 'Uploading .md file...');
    const path = `pipeline/inputs/${Date.now()}-${currentMd.name.replace(/[^a-zA-Z0-9.-]/g, '_')}`;
    const content = btoa(unescape(encodeURIComponent(currentMd.content)));
    const putRes = await fetch(`https://api.github.com/repos/${CONFIG.repo}/contents/${path}`, {
      method: 'PUT',
      headers: { 'Authorization': `token ${CONFIG.token}`, 'Accept': 'application/vnd.github+json' },
      body: JSON.stringify({ message: `📄 ${currentMd.name}`, content, branch: 'main' }),
    });
    if (!putRes.ok) throw new Error(`Upload failed: ${putRes.status} ${(await putRes.text()).slice(0,200)}`);
    log('✅ File uploaded to: ' + path, 'success');

    // ===== Step 2: Trigger workflow =====
    log('⚡ Triggering GitHub Actions workflow...', 'action');
    setActiveStep('research');
    setProgress(25, 'Starting AI pipeline...');
    const wfRes = await fetch(`https://api.github.com/repos/${CONFIG.repo}/actions/workflows/on-demand.yml/dispatches`, {
      method: 'POST',
      headers: { 'Authorization': `token ${CONFIG.token}`, 'Accept': 'application/vnd.github+json' },
      body: JSON.stringify({
        ref: 'main',
        inputs: {
          md_path: path,
          voice: document.getElementById('voice-select').value,
          style_prompt: document.getElementById('style-prompt').value || '',
          style: document.getElementById('style-select').value,
          aspect: document.getElementById('aspect-select').value,
        },
      }),
    });
    if (!wfRes.ok && wfRes.status !== 204) throw new Error(`Workflow trigger failed: ${wfRes.status}`);
    log('✅ Workflow triggered successfully!', 'success');

    log('⏳ AI is now researching your script...', 'info');
    log('📝 Generating voice with Google Gemini TTS...', 'info');
    log('🎨 Fetching stock videos from Pexels + AI images...', 'info');
    log('🎞️ Assembling final video with subtitles...', 'info');

    // ===== Step 3: Poll GitHub Actions for live status =====
    await pollActionsAndRelease(CONFIG, currentMd);

  } catch (err) {
    setProgress(0, '❌ ' + err.message);
    log('❌ ERROR: ' + err.message, 'error');
    showToast('❌ ' + err.message, 'error', 8000);
  }
});

function setProgress(pct, text) {
  if (progressFill) progressFill.style.width = pct + '%';
  if (statusText) statusText.textContent = text;
  if (statusTitle) {
    if (pct === 100) statusTitle.textContent = '✅ Complete!';
    else if (pct === 0) statusTitle.textContent = '❌ Failed';
    else statusTitle.textContent = '⏳ Running... ' + pct + '%';
  }
}

function setActiveStep(step) {
  document.querySelectorAll('.status-step').forEach(s => s.classList.remove('active', 'done'));
  const order = ['upload', 'research', 'script', 'voice', 'visuals', 'assemble'];
  const curIdx = order.indexOf(step);
  order.forEach((s, i) => {
    const el = document.querySelector(`.status-step[data-step="${s}"]`);
    if (!el) return;
    if (i < curIdx) el.classList.add('done');
    if (i === curIdx) el.classList.add('active');
  });
}

function log(msg, type = 'info') {
  if (!actionLog) return;
  const colors = {
    info: '#94a3b8',
    action: '#06b6d4',
    success: '#10b981',
    error: '#ef4444',
    highlight: '#f59e0b'
  };
  const icons = {
    info: 'ℹ️',
    action: '⚡',
    success: '✅',
    error: '❌',
    highlight: '⭐'
  };
  const time = new Date().toLocaleTimeString();
  const div = document.createElement('div');
  div.className = 'log-line log-' + type;
  div.innerHTML = `
    <span class="log-time">${time}</span>
    <span class="log-icon">${icons[type]}</span>
    <span class="log-msg">${msg}</span>
  `;
  actionLog.appendChild(div);
  actionLog.scrollTop = actionLog.scrollHeight;
}

// ============ Poll GitHub Actions + Releases ============
async function pollActionsAndRelease(cfg, mdFile) {
  let startTime = Date.now();
  let lastStep = 'research';
  let videoUrl = null;
  let runId = null;
  let releaseFound = false;

  // First, find the workflow run
  log('🔍 Looking for workflow run...', 'action');
  for (let attempt = 0; attempt < 10; attempt++) {
    try {
      const r = await fetch(`https://api.github.com/repos/${cfg.repo}/actions/runs?per_page=3`, {
        headers: { 'Authorization': `token ${cfg.token}`, 'Accept': 'application/vnd.github+json' }
      });
      if (r.ok) {
        const data = await r.json();
        // Find most recent in_progress or queued run
        const run = data.workflow_runs.find(w => w.status === 'in_progress' || w.status === 'queued')
                  || data.workflow_runs[0];
        if (run && Date.now() - new Date(run.created_at).getTime() < 5 * 60 * 1000) {
          runId = run.id;
          log(`🎬 Workflow run found: #${run.id} (${run.status})`, 'highlight');
          break;
        }
      }
    } catch (e) {}
    await new Promise(r => setTimeout(r, 3000));
  }

  const maxWaitMs = 12 * 60 * 1000;
  let lastStatus = '';

  while (Date.now() - startTime < maxWaitMs) {
    const elapsed = Math.floor((Date.now() - startTime) / 1000);

    // ===== Check workflow run status =====
    if (runId) {
      try {
        const r = await fetch(`https://api.github.com/repos/${cfg.repo}/actions/runs/${runId}`, {
          headers: { 'Authorization': `token ${cfg.token}`, 'Accept': 'application/vnd.github+json' }
        });
        if (r.ok) {
          const run = await r.json();
          if (run.status !== lastStatus) {
            lastStatus = run.status;
            log(`🔄 Workflow status: ${run.status}`, 'info');
            if (run.status === 'completed') {
              if (run.conclusion === 'success') {
                log('✅ Workflow completed successfully!', 'success');
                setProgress(95, 'Workflow done, finding video...');
                setActiveStep('assemble');
              } else {
                throw new Error(`Workflow ${run.conclusion}. Check Actions tab for details.`);
              }
            }
          }
          // Update progress based on time (rough estimate)
          if (run.status === 'in_progress') {
            const pct = Math.min(90, 30 + elapsed / 8);
            const stepNames = ['research', 'script', 'voice', 'visuals', 'assemble'];
            const stepIdx = Math.min(stepNames.length - 1, Math.floor((elapsed / 60) * stepNames.length));
            if (stepIdx >= 0 && stepNames[stepIdx] !== lastStep) {
              lastStep = stepNames[stepIdx];
              setActiveStep(lastStep);
              log('⚙️ Stage: ' + stepNames[stepIdx].toUpperCase(), 'highlight');
            }
            setProgress(pct, `Running... ${elapsed}s elapsed`);
          }
        }
      } catch (e) {}
    } else {
      // Estimate progress without run ID
      const pct = Math.min(85, 30 + elapsed / 10);
      setProgress(pct, `AI working... ${elapsed}s elapsed (open Actions tab to see live logs)`);
    }

    // ===== Check for release with video =====
    try {
      const res = await fetch(`https://api.github.com/repos/${cfg.repo}/releases/latest`, {
        headers: { 'Authorization': `token ${cfg.token}`, 'Accept': 'application/vnd.github+json' }
      });
      if (res.ok) {
        const release = await res.json();
        const baseName = mdFile.name.replace('.md', '');
        const match = release.assets.find(a =>
          a.name.toLowerCase().includes(baseName.toLowerCase()) && a.name.endsWith('.mp4')
        );
        if (match) {
          videoUrl = match.browser_download_url;
          releaseFound = true;
          log(`🎉 VIDEO FOUND in release: ${match.name}`, 'success');
          break;
        }
      }
    } catch (e) {}

    await new Promise(r => setTimeout(r, 10000));
  }

  if (!videoUrl) {
    log('⏰ Timeout! Pipeline still running. Check Actions tab.', 'error');
    log('🔗 https://github.com/' + cfg.repo + '/actions', 'highlight');
    setProgress(0, 'Timeout. Check Actions tab manually.');
    showToast('⏰ Timeout — check Actions tab', 'error', 10000);
    return;
  }

  // ===== Show result =====
  setProgress(100, '✅ Video ready!');
  log(`🎬 Final video URL: ${videoUrl}`, 'success');
  log('🎉 ALL DONE! Total time: ' + Math.floor((Date.now() - startTime) / 60) + ' min', 'highlight');

  resultVideo.src = videoUrl;
  resultDownload.href = videoUrl;
  resultDownload.download = mdFile.name.replace('.md', '.mp4');
  resultLink.href = videoUrl;

  setTimeout(() => {
    mdStatus.classList.add('hidden');
    mdResult.classList.remove('hidden');
    mdResult.scrollIntoView({ behavior: 'smooth', block: 'start' });
    showToast('🎉 Video ready for download!', 'success', 6000);
  }, 1500);
}

// ============ Auto Mode: Topics ============
const TOPICS_KEY = 'ff_topics';
function loadTopics() { const s = localStorage.getItem(TOPICS_KEY); return s ? JSON.parse(s) : []; }
function saveTopics(t) { localStorage.setItem(TOPICS_KEY, JSON.stringify(t)); }

const topicInput = document.getElementById('topic-input');
const categorySelect = document.getElementById('category-select');
const addTopicBtn = document.getElementById('add-topic-btn');
const topicList = document.getElementById('topic-list');
const topicCount = document.getElementById('topic-count');

function renderTopics() {
  const topics = loadTopics();
  topicList.innerHTML = '';
  topicCount.textContent = `(${topics.length})`;
  if (topics.length === 0) {
    topicList.innerHTML = '<li class="muted center" style="background:transparent;border:none;padding:32px;">No topics yet. Add one above 👆</li>';
    return;
  }
  topics.forEach((t, i) => {
    const li = document.createElement('li');
    li.innerHTML = `
      <div class="topic-text">${escapeHtml(t.text)}</div>
      <div style="display:flex;gap:10px;align-items:center;">
        <span class="topic-cat">${escapeHtml(t.cat)}</span>
        <button class="del-btn" data-i="${i}">✕</button>
      </div>
    `;
    topicList.appendChild(li);
  });
  topicList.querySelectorAll('.del-btn').forEach(b =>
    b.addEventListener('click', () => {
      const ts = loadTopics();
      ts.splice(parseInt(b.dataset.i), 1);
      saveTopics(ts);
      renderTopics();
      showToast('Topic deleted', 'info', 2000);
    })
  );
}

addTopicBtn.addEventListener('click', () => {
  const text = topicInput.value.trim();
  if (!text) { showToast('❌ Enter a topic first!', 'error'); return; }
  const topics = loadTopics();
  topics.push({ text, cat: categorySelect.value });
  saveTopics(topics);
  topicInput.value = '';
  renderTopics();
  showToast('✅ Topic added!', 'success');
});

topicInput.addEventListener('keydown', e => { if (e.key === 'Enter') addTopicBtn.click(); });

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

renderTopics();

// ============ Trigger Auto ============
const triggerAuto = document.getElementById('trigger-auto');
triggerAuto.addEventListener('click', async () => {
  if (!CONFIG.token) {
    const token = prompt('GitHub PAT chahiye. https://github.com/settings/tokens');
    if (!token) return;
    CONFIG.token = token;
    localStorage.setItem('ff_token', token);
  }
  if (CONFIG.repo === 'yourname/freeflow') {
    const repo = prompt('GitHub repo name:');
    if (!repo) return;
    CONFIG.repo = repo;
    localStorage.setItem('ff_repo', repo);
  }

  const topics = loadTopics();
  if (topics.length === 0) {
    showToast('❌ Add at least one topic!', 'error');
    return;
  }

  showToast('🚀 Syncing topics & starting pipeline...', 'info');

  try {
    const getRes = await fetch(`https://api.github.com/repos/${CONFIG.repo}/contents/pipeline/topics.json`, {
      headers: { 'Authorization': `token ${CONFIG.token}` }
    });
    const current = getRes.ok ? await getRes.json() : null;
    const content = btoa(unescape(encodeURIComponent(JSON.stringify(topics, null, 2))));
    const putRes = await fetch(`https://api.github.com/repos/${CONFIG.repo}/contents/pipeline/topics.json`, {
      method: 'PUT',
      headers: { 'Authorization': `token ${CONFIG.token}`, 'Accept': 'application/vnd.github+json' },
      body: JSON.stringify({ message: '🤖 Sync topics', content, sha: current?.sha, branch: 'main' }),
    });
    if (!putRes.ok) throw new Error('Topic sync failed');

    const wfRes = await fetch(`https://api.github.com/repos/${CONFIG.repo}/actions/workflows/auto-hourly.yml/dispatches`, {
      method: 'POST',
      headers: { 'Authorization': `token ${CONFIG.token}`, 'Accept': 'application/vnd.github+json' },
      body: JSON.stringify({
        ref: 'main',
        inputs: {
          voice: document.getElementById('auto-voice').value,
          style: document.getElementById('auto-style').value,
          aspect: document.getElementById('auto-aspect').value,
          manual: 'true',
        },
      }),
    });
    if (!wfRes.ok && wfRes.status !== 204) throw new Error('Workflow trigger failed');
    showToast('✅ Pipeline started! Check Actions tab in 2-5 min.', 'success', 6000);
  } catch (err) {
    showToast('❌ ' + err.message, 'error', 8000);
  }
});

// ============ GitHub link in footer ============
const repoLink = document.getElementById('repo-link');
if (repoLink) repoLink.href = `https://github.com/${CONFIG.repo}`;

// ============ Smooth scroll ============
document.querySelectorAll('.nav-links a[href^="#"]').forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    const target = document.querySelector(link.getAttribute('href'));
    if (target) target.scrollIntoView({ behavior: 'smooth' });
  });
});

// ============ Inject toast & log animations CSS ============
const animStyle = document.createElement('style');
animStyle.textContent = `
  @keyframes slideInRight {
    from { transform: translateX(120%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
  }
  @keyframes slideOutRight {
    from { transform: translateX(0); opacity: 1; }
    to { transform: translateX(120%); opacity: 0; }
  }
`;
document.head.appendChild(animStyle);
