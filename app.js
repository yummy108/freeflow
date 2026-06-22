/* =============== FreeFlow Frontend Logic =============== */

// ---- CONFIG ----
// Replace these with your actual values after forking the repo.
const CONFIG = {
  // GitHub repo where Actions run (e.g. "yourname/freeflow")
  repo: localStorage.getItem('ff_repo') || 'yourname/freeflow',
  // GitHub PAT (Personal Access Token) with 'repo' scope — generated & stored locally only.
  // Get one at https://github.com/settings/tokens (classic, no expiry recommended)
  token: localStorage.getItem('ff_token') || '',
};

// ---- Mode Switch ----
const modeBtns = document.querySelectorAll('.mode-btn');
modeBtns.forEach(btn => btn.addEventListener('click', () => {
  modeBtns.forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.getElementById(`mode-${btn.dataset.mode}`).classList.add('active');
}));

// ---- Drag & Drop .md ----
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('file-input');
const mdPreview = document.getElementById('md-preview');
const mdContent = document.getElementById('md-content');
const mdFilename = document.getElementById('md-filename');
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
    alert('Please upload a .md file');
    return;
  }
  if (file.size > 2 * 1024 * 1024) {
    alert('Max 2 MB');
    return;
  }
  const reader = new FileReader();
  reader.onload = e => {
    currentMd = { name: file.name, content: e.target.result };
    mdFilename.textContent = `📄 ${file.name} (${(file.size/1024).toFixed(1)} KB)`;
    mdContent.textContent = currentMd.content.slice(0, 2000) + (currentMd.content.length > 2000 ? '\n...' : '');
    mdPreview.classList.remove('hidden');
  };
  reader.readAsText(file);
}

// ---- Trigger Pipeline ----
const triggerBtn = document.getElementById('trigger-pipeline');
const mdStatus = document.getElementById('md-status');
const mdResult = document.getElementById('md-result');
const statusText = document.getElementById('status-text');
const resultVideo = document.getElementById('result-video');
const resultDownload = document.getElementById('result-download');
const resultLink = document.getElementById('result-link');

triggerBtn.addEventListener('click', async () => {
  if (!currentMd) { alert('Upload a .md file first!'); return; }

  // Settings
  const settings = {
    voice: document.getElementById('voice-select').value,
    style_prompt: document.getElementById('style-prompt').value || '',
    style: document.getElementById('style-select').value,
    aspect: document.getElementById('aspect-select').value,
    md: currentMd,
    timestamp: Date.now(),
  };

  // Save PAT prompt (only first time)
  if (!CONFIG.token) {
    const token = prompt(
      '🔑 Enter your GitHub Personal Access Token (PAT)\n' +
      'Get one at https://github.com/settings/tokens (classic, repo scope).\n' +
      'Stored in localStorage only — never sent anywhere except GitHub API.'
    );
    if (!token) return;
    CONFIG.token = token;
    localStorage.setItem('ff_token', token);
  }

  // Get repo
  if (CONFIG.repo === 'yourname/freeflow') {
    const repo = prompt('Enter your GitHub repo (e.g. johndoe/freeflow):');
    if (!repo) return;
    CONFIG.repo = repo;
    localStorage.setItem('ff_repo', repo);
  }

  mdResult.classList.add('hidden');
  mdStatus.classList.remove('hidden');
  statusText.textContent = 'Triggering GitHub Action…';

  try {
    // Step 1: Write .md file to repo via Contents API
    statusText.textContent = 'Uploading .md to repo…';
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
    if (!putRes.ok) throw new Error(`Upload failed: ${putRes.status} ${putRes.statusText}`);

    // Step 2: Trigger workflow_dispatch with settings
    statusText.textContent = 'Starting pipeline… (this takes 2–5 min)';
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

    // Step 3: Poll for release
    statusText.textContent = 'Pipeline running… generating script, voice, video. Hang tight.';
    const videoUrl = await pollForRelease(CONFIG, currentMd.name);
    if (!videoUrl) throw new Error('Pipeline finished but no video URL found. Check Actions tab.');

    resultVideo.src = videoUrl;
    resultDownload.href = videoUrl;
    resultDownload.download = currentMd.name.replace('.md', '.mp4');
    resultLink.href = videoUrl;
    mdStatus.classList.add('hidden');
    mdResult.classList.remove('hidden');
  } catch (err) {
    statusText.textContent = '❌ ' + err.message;
  }
});

// Poll GitHub Releases for a new video
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
    await new Promise(r => setTimeout(r, checkInterval));
  }
  return null;
}

// ============ Mode 2: Auto Topics ============
const TOPICS_KEY = 'ff_topics';
function loadTopics() {
  const stored = localStorage.getItem(TOPICS_KEY);
  return stored ? JSON.parse(stored) : [
    { text: 'Latest AI breakthroughs in 2026', cat: 'tech' },
    { text: 'Mystery of the deep ocean', cat: 'mystery' },
    { text: 'How black holes are formed', cat: 'science' },
  ];
}
function saveTopics(topics) {
  localStorage.setItem(TOPICS_KEY, JSON.stringify(topics));
}

const topicInput = document.getElementById('topic-input');
const categorySelect = document.getElementById('category-select');
const addTopicBtn = document.getElementById('add-topic-btn');
const topicList = document.getElementById('topic-list');

function renderTopics() {
  const topics = loadTopics();
  topicList.innerHTML = '';
  if (topics.length === 0) {
    topicList.innerHTML = '<li class="muted">No topics yet. Add one above!</li>';
    return;
  }
  topics.forEach((t, i) => {
    const li = document.createElement('li');
    li.innerHTML = `
      <div>
        <div class="topic-text">${escapeHtml(t.text)}</div>
      </div>
      <div style="display:flex;gap:8px;align-items:center;">
        <span class="topic-cat">${t.cat}</span>
        <button class="del-btn" data-i="${i}">Delete</button>
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
    })
  );
}

addTopicBtn.addEventListener('click', () => {
  const text = topicInput.value.trim();
  if (!text) { alert('Enter a topic!'); return; }
  const topics = loadTopics();
  topics.push({ text, cat: categorySelect.value });
  saveTopics(topics);
  topicInput.value = '';
  renderTopics();
});

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

renderTopics();

// ---- Trigger Auto One Video ----
const triggerAuto = document.getElementById('trigger-auto');
triggerAuto.addEventListener('click', async () => {
  if (!CONFIG.token) {
    const token = prompt('Enter your GitHub PAT (https://github.com/settings/tokens):');
    if (!token) return;
    CONFIG.token = token;
    localStorage.setItem('ff_token', token);
  }
  if (CONFIG.repo === 'yourname/freeflow') {
    const repo = prompt('Enter your GitHub repo (e.g. johndoe/freeflow):');
    if (!repo) return;
    CONFIG.repo = repo;
    localStorage.setItem('ff_repo', repo);
  }

  // Sync topics.json to repo first
  const topics = loadTopics();
  const topicsJson = JSON.stringify(topics, null, 2);
  const content = btoa(unescape(encodeURIComponent(topicsJson)));

  alert('🚀 Triggering auto-pipeline. Topics will be synced first. Check Actions tab in 2-5 min for video.');

  try {
    // Get current SHA
    const getRes = await fetch(`https://api.github.com/repos/${CONFIG.repo}/contents/pipeline/topics.json`, {
      headers: { 'Authorization': `token ${CONFIG.token}` }
    });
    const current = getRes.ok ? await getRes.json() : null;
    const putRes = await fetch(`https://api.github.com/repos/${CONFIG.repo}/contents/pipeline/topics.json`, {
      method: 'PUT',
      headers: { 'Authorization': `token ${CONFIG.token}`, 'Accept': 'application/vnd.github+json' },
      body: JSON.stringify({
        message: '🤖 Sync topics',
        content,
        sha: current?.sha,
        branch: 'main',
      }),
    });
    if (!putRes.ok) throw new Error('Topic sync failed');

    // Trigger workflow
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
    alert('✅ Pipeline started! Check GitHub Actions tab.');
  } catch (err) {
    alert('❌ ' + err.message);
  }
});

// Initial render
document.getElementById('repo-link').href = `https://github.com/${CONFIG.repo}`;
