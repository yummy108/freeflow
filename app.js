/* =============== FreeFlow Frontend Logic v2 =============== */

const CONFIG = {
  repo: localStorage.getItem('ff_repo') || 'yummy108/freeflow',
  token: localStorage.getItem('ff_token') || '',
};

// ============== Mode Switch ==============
const modeBtns = document.querySelectorAll('.mode-tab');
modeBtns.forEach(btn => btn.addEventListener('click', () => {
  modeBtns.forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  const mode = btn.dataset.mode;
  const target = document.getElementById(`mode-${mode}`);
  if (target) target.classList.add('active');
}));

// ============== Drag & Drop ==============
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
});

function handleFile(file) {
  if (!file.name.endsWith('.md') && !file.name.endsWith('.markdown')) {
    showToast('Please upload a .md file', 'error');
    return;
  }
  if (file.size > 2 * 1024 * 1024) {
    showToast('Max 2 MB file size', 'error');
    return;
  }
  const reader = new FileReader();
  reader.onload = e => {
    currentMd = { name: file.name, content: e.target.result, size: file.size };
    mdFilename.textContent = file.name;
    mdFilesize.textContent = `${(file.size / 1024).toFixed(1)} KB`;
    mdContent.textContent = currentMd.content.slice(0, 2000) + (currentMd.content.length > 2000 ? '\n...' : '');
    mdPreview.classList.remove('hidden');
    mdPreview.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };
  reader.readAsText(file);
}

// ============== Toast Notification ==============
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  toast.style.cssText = `
    position: fixed; top: 20px; right: 20px;
    background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#06b6d4'};
    color: white; padding: 14px 22px;
    border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    font-weight: 600; font-size: 14px;
    z-index: 9999; animation: fadeInUp 0.3s;
    max-width: 320px;
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

// ============== Pipeline Trigger ==============
const triggerBtn = document.getElementById('trigger-pipeline');
const mdStatus = document.getElementById('md-status');
const mdResult = document.getElementById('md-result');
const statusText = document.getElementById('status-text');
const statusTitle = document.getElementById('status-title');
const resultVideo = document.getElementById('result-video');
const resultDownload = document.getElementById('result-download');
const resultLink = document.getElementById('result-link');
const progressFill = document.getElementById('progress-fill');

triggerBtn.addEventListener('click', async () => {
  if (!currentMd) {
    showToast('Upload a .md file first!', 'error');
    return;
  }

  const settings = {
    voice: document.getElementById('voice-select').value,
    style_prompt: document.getElementById('style-prompt').value || '',
    style: document.getElementById('style-select').value,
    aspect: document.getElementById('aspect-select').value,
    md: currentMd,
  };

  if (!CONFIG.token) {
    const token = prompt(
      '🔑 Enter your GitHub Personal Access Token (PAT)\n\n' +
      'Get one at https://github.com/settings/tokens\n' +
      '(Classic · repo scope · No expiration recommended)\n\n' +
      '⚠️ Stored in browser localStorage only.'
    );
    if (!token) return;
    CONFIG.token = token;
    localStorage.setItem('ff_token', token);
    showToast('✅ PAT saved', 'success');
  }

  if (CONFIG.repo === 'yourname/freeflow') {
    const repo = prompt('Enter your GitHub repo (e.g. yummy108/freeflow):');
    if (!repo) return;
    CONFIG.repo = repo;
    localStorage.setItem('ff_repo', repo);
  }

  mdResult.classList.add('hidden');
  mdStatus.classList.remove('hidden');
  mdStatus.scrollIntoView({ behavior: 'smooth', block: 'start' });
  animateProgress();

  try {
    // Step 1: Upload MD
    setStatus('Uploading .md to GitHub...', '📤 Uploading file', 10);
    setActiveStep('upload');
    const path = `pipeline/inputs/${Date.now()}-${currentMd.name}`;
    const content = btoa(unescape(encodeURIComponent(currentMd.content)));
    const putRes = await fetch(`https://api.github.com/repos/${CONFIG.repo}/contents/${path}`, {
      method: 'PUT',
      headers: {
        'Authorization': `token ${CONFIG.token}`,
        'Accept': 'application/vnd.github+json',
      },
      body: JSON.stringify({
        message: `📄 New MD upload: ${currentMd.name}`,
        content,
        branch: 'main',
      }),
    });
    if (!putRes.ok) throw new Error(`Upload failed: ${putRes.status} ${await putRes.text()}`);

    // Step 2: Trigger workflow
    setStatus('Triggering GitHub Actions pipeline...', '⚡ Starting workflow', 25);
    setActiveStep('research');
    const wfRes = await fetch(`https://api.github.com/repos/${CONFIG.repo}/actions/workflows/on-demand.yml/dispatches`, {
      method: 'POST',
      headers: {
        'Authorization': `token ${CONFIG.token}`,
        'Accept': 'application/vnd.github+json',
      },
      body: JSON.stringify({
        ref: 'main',
        inputs: {
          md_path: path,
          voice: settings.voice,
          style_prompt: settings.style_prompt,
          style: settings.style,
          aspect: settings.aspect,
        },
      }),
    });
    if (!wfRes.ok && wfRes.status !== 204) throw new Error(`Workflow trigger failed: ${wfRes.status}`);

    setStatus('Pipeline running... Research → Script → Voice → Visuals → Assemble', '🔬 AI working hard', 50);

    // Animate progress steps
    const steps = ['script', 'voice', 'visuals', 'assemble'];
    let i = 0;
    const stepInterval = setInterval(() => {
      if (i < steps.length) {
        setActiveStep(steps[i]);
        i++;
      }
    }, 30000); // each step ~30s

    // Step 3: Poll for release
    const videoUrl = await pollForRelease(CONFIG, currentMd.name);
    clearInterval(stepInterval);
    if (!videoUrl) throw new Error('Pipeline finished but no video found. Check Actions tab.');

    setStatus('Video ready! 🎉', '✅ Complete', 100);
    setActiveStep('assemble');

    resultVideo.src = videoUrl;
    resultDownload.href = videoUrl;
    resultDownload.download = currentMd.name.replace('.md', '.mp4');
    resultLink.href = videoUrl;

    setTimeout(() => {
      mdStatus.classList.add('hidden');
      mdResult.classList.remove('hidden');
      mdResult.scrollIntoView({ behavior: 'smooth', block: 'start' });
      showToast('🎉 Video ready for download!', 'success');
    }, 800);

  } catch (err) {
    setStatus('❌ ' + err.message, 'Failed', 0);
    showToast(err.message, 'error');
  }
});

function setStatus(text, title, progress) {
  statusText.textContent = text;
  if (statusTitle) statusTitle.textContent = title;
  if (progressFill && progress !== undefined) progressFill.style.width = `${progress}%`;
}

function setActiveStep(step) {
  document.querySelectorAll('.status-step').forEach(s => s.classList.remove('active'));
  const el = document.querySelector(`.status-step[data-step="${step}"]`);
  if (el) el.classList.add('active');
}

function animateProgress() {
  let p = 0;
  const interval = setInterval(() => {
    p = Math.min(p + 2, 90);
    if (progressFill) progressFill.style.width = `${p}%`;
    if (p >= 90) clearInterval(interval);
  }, 2000);
}

// Poll GitHub Releases for new video
async function pollForRelease(cfg, name, maxWaitMs = 8 * 60 * 1000) {
  const startTime = Date.now();
  const checkInterval = 15 * 1000;
  while (Date.now() - startTime < maxWaitMs) {
    try {
      const res = await fetch(`https://api.github.com/repos/${cfg.repo}/releases/latest`, {
        headers: { 'Authorization': `token ${cfg.token}`, 'Accept': 'application/vnd.github+json' }
      });
      if (res.ok) {
        const release = await res.json();
        const match = release.assets.find(a => a.name.includes(name.replace('.md', '')) && a.name.endsWith('.mp4'));
        if (match) return match.browser_download_url;
      }
    } catch (e) { /* keep polling */ }
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    setStatus(`Pipeline running... ${elapsed}s elapsed. Research → Script → Voice → Visuals → Assemble`, '🔬 AI working hard', Math.min(90, 30 + elapsed / 4));
    await new Promise(r => setTimeout(r, checkInterval));
  }
  return null;
}

// ============== Auto Mode: Topics ==============
const TOPICS_KEY = 'ff_topics';
function loadTopics() {
  const stored = localStorage.getItem(TOPICS_KEY);
  return stored ? JSON.parse(stored) : [];
}
function saveTopics(topics) {
  localStorage.setItem(TOPICS_KEY, JSON.stringify(topics));
}

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
    topicList.innerHTML = '<li class="muted center" style="background:transparent;border:none;padding:24px;">No topics yet. Add one above! 👆</li>';
    return;
  }
  topics.forEach((t, i) => {
    const li = document.createElement('li');
    li.innerHTML = `
      <div class="topic-text">${escapeHtml(t.text)}</div>
      <div style="display:flex;gap:10px;align-items:center;">
        <span class="topic-cat">${escapeHtml(t.cat)}</span>
        <button class="del-btn" data-i="${i}">✕ Delete</button>
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
      showToast('Topic deleted', 'info');
    })
  );
}

addTopicBtn.addEventListener('click', () => {
  const text = topicInput.value.trim();
  if (!text) {
    showToast('Enter a topic first!', 'error');
    return;
  }
  const topics = loadTopics();
  topics.push({ text, cat: categorySelect.value });
  saveTopics(topics);
  topicInput.value = '';
  renderTopics();
  showToast('✅ Topic added', 'success');
});

topicInput.addEventListener('keydown', e => {
  if (e.key === 'Enter') addTopicBtn.click();
});

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

renderTopics();

// ============== Trigger Auto ==============
const triggerAuto = document.getElementById('trigger-auto');
triggerAuto.addEventListener('click', async () => {
  if (!CONFIG.token) {
    const token = prompt('Enter your GitHub PAT (https://github.com/settings/tokens):');
    if (!token) return;
    CONFIG.token = token;
    localStorage.setItem('ff_token', token);
  }
  if (CONFIG.repo === 'yourname/freeflow') {
    const repo = prompt('Enter your GitHub repo (e.g. yummy108/freeflow):');
    if (!repo) return;
    CONFIG.repo = repo;
    localStorage.setItem('ff_repo', repo);
  }

  const topics = loadTopics();
  if (topics.length === 0) {
    showToast('Add at least one topic first!', 'error');
    return;
  }

  showToast('🚀 Syncing topics & triggering pipeline...', 'info');

  try {
    // Get current SHA
    const getRes = await fetch(`https://api.github.com/repos/${CONFIG.repo}/contents/pipeline/topics.json`, {
      headers: { 'Authorization': `token ${CONFIG.token}` }
    });
    const current = getRes.ok ? await getRes.json() : null;

    const topicsJson = JSON.stringify(topics, null, 2);
    const content = btoa(unescape(encodeURIComponent(topicsJson)));
    const putRes = await fetch(`https://api.github.com/repos/${CONFIG.repo}/contents/pipeline/topics.json`, {
      method: 'PUT',
      headers: { 'Authorization': `token ${CONFIG.token}`, 'Accept': 'application/vnd.github+json' },
      body: JSON.stringify({
        message: '🤖 Sync auto-research topics',
        content,
        sha: current?.sha,
        branch: 'main',
      }),
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
    showToast('✅ Pipeline started! Check Actions tab in 2-5 min.', 'success');
  } catch (err) {
    showToast('❌ ' + err.message, 'error');
  }
});

// ============== GitHub link in footer ==============
const repoLink = document.getElementById('repo-link');
if (repoLink) repoLink.href = `https://github.com/${CONFIG.repo}`;

// ============== Smooth scroll for nav links ==============
document.querySelectorAll('.nav-links a[href^="#"]').forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    const target = document.querySelector(link.getAttribute('href'));
    if (target) target.scrollIntoView({ behavior: 'smooth' });
  });
});
