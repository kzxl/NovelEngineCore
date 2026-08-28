// ==========================================================================
// NovelEngineCore - Universe Studio v4.0 Application Logic (Dynamic BE Models)
// ==========================================================================

let storyState = null;
let currentDraft = null;
let selectedFateChoice = null;
let discoveryCodex = null;
let availableModels = [];

// Switch Active Galaxy View
function switchGalaxy(viewName) {
  const views = ['world', 'characters', 'rpg', 'novel', 'comic'];
  views.forEach(v => {
    const navBtn = document.getElementById(`nav-${v}`);
    const viewPane = document.getElementById(`galaxy-view-${v}`);
    if (navBtn && viewPane) {
      if (v === viewName) {
        navBtn.classList.add('active');
        viewPane.classList.add('active');
      } else {
        navBtn.classList.remove('active');
        viewPane.classList.remove('active');
      }
    }
  });

  if (viewName === 'rpg') {
    refreshDiscoveryCodex();
  }
}

// Initial Fetch on Page Load
document.addEventListener('DOMContentLoaded', async () => {
  await fetchModels();
  await fetchState();
  await refreshDiscoveryCodex();
});

// Dynamic Model Discovery from Backend
async function fetchModels() {
  const select = document.getElementById('model-select');
  select.innerHTML = '<option value="">⏳ Đang quét danh sách model từ server...</option>';

  try {
    const res = await fetch('/api/models');
    if (res.ok) {
      availableModels = await res.json();
      renderModelOptions(availableModels);
    }
  } catch (err) {
    console.error("Could not fetch models from backend", err);
    select.innerHTML = '<option value="ollama/qwen2.5-coder:3b">🟢 Local Ollama (qwen2.5-coder:3b)</option>';
  }
}

function renderModelOptions(models) {
  const select = document.getElementById('model-select');
  select.innerHTML = '';

  const groups = {};
  models.forEach(m => {
    if (!groups[m.category]) groups[m.category] = [];
    groups[m.category].push(m);
  });

  for (const [category, items] of Object.entries(groups)) {
    const optgroup = document.createElement('optgroup');
    optgroup.label = category;

    items.forEach((m, idx) => {
      const opt = document.createElement('option');
      opt.value = m.id;
      opt.innerText = m.name;
      if (!m.is_available) opt.disabled = true;
      if (m.id.includes('qwen2.5-coder:3b') || (!select.value && m.is_available && idx === 0)) {
        opt.selected = true;
      }
      optgroup.appendChild(opt);
    });

    select.appendChild(optgroup);
  }
}

async function fetchState() {
  try {
    const res = await fetch('/api/state');
    if (res.ok) {
      storyState = await res.json();
      renderAll();
    }
  } catch (err) {
    console.warn("Could not fetch initial state.", err);
  }
}

function renderAll() {
  if (!storyState) return;
  renderWorldView(storyState.world_bible);
  renderCharactersView(storyState.characters);
  updateCharacterBadge();
}

// ----------------------------------------------------------------------
// 1. World Genesis Galaxy
// ----------------------------------------------------------------------

function renderWorldView(world) {
  if (!world) return;
  document.getElementById('world-title').value = world.title || '';
  document.getElementById('world-genre').value = world.genre || 'Xianxia';
  document.getElementById('world-energy').value = world.energy_source || '';

  // Render Power Tiers
  const tiersContainer = document.getElementById('power-tiers-list');
  tiersContainer.innerHTML = '';
  if (world.power_progression && world.power_progression.length > 0) {
    world.power_progression.forEach(t => {
      const item = document.createElement('div');
      item.className = 'tier-item';
      item.innerHTML = `
        <div class="tier-item-header">
          <span>Rank ${t.rank}: ${t.name}</span>
        </div>
        <p>${t.description}</p>
        <div class="tier-limit">🚫 Giới hạn: ${t.hard_limits}</div>
      `;
      tiersContainer.appendChild(item);
    });
  }

  // Render Canon Rules
  const canonContainer = document.getElementById('canon-rules-container');
  canonContainer.innerHTML = '';
  if (world.canon_rules && world.canon_rules.length > 0) {
    world.canon_rules.forEach(r => {
      const tag = document.createElement('div');
      tag.className = 'canon-tag';
      tag.innerHTML = `⚡ ${r}`;
      canonContainer.appendChild(tag);
    });
  }

  // Render Factions
  const factionsContainer = document.getElementById('factions-container');
  factionsContainer.innerHTML = '';
  if (world.factions && world.factions.length > 0) {
    world.factions.forEach(f => {
      const card = document.createElement('div');
      card.className = 'faction-card-sm';
      card.innerHTML = `
        <div>
          <span class="faction-name">${f.name}</span>
          <span class="faction-align">[${f.alignment}]</span>
        </div>
        <p style="color:#94a3b8; font-size:0.75rem; margin-top:3px;">${f.core_doctrine}</p>
      `;
      factionsContainer.appendChild(card);
    });
  }

  // Render Locations
  const locationsContainer = document.getElementById('locations-container');
  locationsContainer.innerHTML = '';
  if (world.locations && world.locations.length > 0) {
    world.locations.forEach(loc => {
      const card = document.createElement('div');
      card.className = 'location-card-sm';
      card.innerHTML = `
        <div>
          <span class="location-name">📍 ${loc.name}</span>
        </div>
        <p style="color:#94a3b8; font-size:0.75rem; margin-top:3px;">${loc.climate_and_vibe}</p>
        <span class="hazard-badge">⚠️ Hiểm họa: ${loc.key_hazards}</span>
      `;
      locationsContainer.appendChild(card);
    });
  }
}

async function autoGenerateWorld() {
  const btn = document.getElementById('btn-auto-world');
  const selectedModel = document.getElementById('model-select').value;
  btn.disabled = true;
  btn.innerText = `⏳ LLM (${selectedModel}) Đang Xây Dựng Thế Giới...`;

  try {
    const res = await fetch('/api/world/auto-generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: document.getElementById('world-title').value,
        genre: document.getElementById('world-genre').value,
        logline: document.getElementById('world-logline').value,
        provider_model: selectedModel
      })
    });
    if (res.ok) {
      const worldBible = await res.json();
      if (storyState) storyState.world_bible = worldBible;
      renderWorldView(worldBible);
      alert('✓ LLM đã tạo hoàn tất toàn bộ Thế Giới Quan!');
    } else {
      const errData = await res.json();
      alert('Lỗi từ AI Model: ' + JSON.stringify(errData));
    }
  } catch (err) {
    alert('Lỗi kết nối tới AI Model: ' + err.message);
  } finally {
    btn.disabled = false;
    btn.innerText = '⚡ AI Tự Động Sinh Toàn Bộ Thế Giới';
  }
}

async function autoEvolveWorld() {
  const btn = document.getElementById('btn-evolve-world');
  btn.disabled = true;
  btn.innerText = '⏳ AI Đang Mở Rộng Lore...';

  try {
    const res = await fetch('/api/world/evolve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ focus_topic: 'Tông môn cổ xưa & Cấm địa ngàn năm' })
    });
    if (res.ok) {
      await fetchState();
      alert('✓ Đã mở rộng thêm Môn Phái, Cấm Địa và Luật Lệ vào Thế Giới!');
    }
  } catch (err) {
    alert('Lỗi mở rộng thế giới: ' + err.message);
  } finally {
    btn.disabled = false;
    btn.innerText = '🌌 AI Tự Mở Rộng Lore & Cấm Địa';
  }
}

// ----------------------------------------------------------------------
// 2. Character Matrix Galaxy
// ----------------------------------------------------------------------

function renderCharactersView(characters) {
  const container = document.getElementById('characters-roster-grid');
  container.innerHTML = '';

  const charList = Object.values(characters || {});
  if (charList.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1/-1; text-align:center; padding: 40px; color:#64748b;">
        Chưa có nhân vật nào. Hãy nhấn nút <strong>"👥 AI Tự Sáng Tạo Dàn Nhân Vật"</strong> ở trên!
      </div>
    `;
    return;
  }

  charList.forEach(c => {
    const card = document.createElement('div');
    card.className = 'char-dossier-card';

    const roleClass = `role-${(c.role || 'npc').toLowerCase()}`;
    const avatarEmoji = c.role === 'Protagonist' ? '🥋' : c.role === 'Antagonist' ? '👹' : c.role === 'Mentor' ? '🧙‍♂️' : '🌸';
    const visualChips = (c.visual_tags || []).map(t => `<span class="visual-chip">${t}</span>`).join('');

    card.innerHTML = `
      <div class="char-card-top">
        <div class="char-card-info">
          <div class="char-avatar-circle">${avatarEmoji}</div>
          <div>
            <div class="char-meta-name">${c.name}</div>
            <span class="role-badge ${roleClass}">${c.role}</span>
          </div>
        </div>
        <button class="char-btn-delete" title="Xóa nhân vật" onclick="deleteCharacter('${c.character_id}')">🗑️</button>
      </div>

      <div class="char-status-line">
        ⚡ <strong>Tu vi:</strong> ${c.status?.power_tier || 'Phàm nhân'} • 🩺 <strong>Trạng thái:</strong> ${c.status?.health_condition || 'Khỏe mạnh'}
      </div>

      <div>
        <div class="char-section-title">Động Cơ & Tính Cách</div>
        <div class="char-traits-list">
          <div>🎯 <strong>Mục tiêu:</strong> ${c.personality?.core_motivation || 'Chưa định'}</div>
          <div>⚠️ <strong>Nhược điểm:</strong> ${c.personality?.fatal_flaw || 'Không'}</div>
          <div>🛡️ <strong>Ranh giới:</strong> ${c.personality?.moral_boundary || 'Không hại kẻ yếu'}</div>
        </div>
      </div>

      ${c.personality?.hidden_secret ? `
        <div class="char-secret-box">
          🤫 <strong>Bí mật ẩn:</strong> ${c.personality.hidden_secret}
        </div>
      ` : ''}

      <div>
        <div class="char-section-title">Visual Identity Tags (Tags vẽ ảnh nhất quán)</div>
        <div class="visual-chips-container">
          ${visualChips || '<span style="font-size:0.75rem; color:#64748b;">Chưa có tags</span>'}
        </div>
      </div>
    `;

    container.appendChild(card);
  });
}

function updateCharacterBadge() {
  const count = Object.keys(storyState?.characters || {}).length;
  document.getElementById('char-count-badge').innerText = count;
}

async function autoGenerateCharacters() {
  const btn = document.getElementById('btn-auto-chars');
  btn.disabled = true;
  btn.innerText = '⏳ AI Đang Sáng Tạo Dàn Nhân Vật...';

  try {
    const res = await fetch('/api/character/auto-generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        count: 4,
        roles_focus: 'Protagonist, Antagonist, Mentor, Sidekick'
      })
    });
    if (res.ok) {
      await fetchState();
      alert('✓ Đã tự động tạo dàn nhân vật hoàn chỉnh kèm Visual Consistency Tags!');
    } else {
      const err = await res.json();
      alert('Lỗi tạo nhân vật từ AI: ' + JSON.stringify(err));
    }
  } catch (err) {
    alert('Lỗi tạo nhân vật: ' + err.message);
  } finally {
    btn.disabled = false;
    btn.innerText = '👥 AI Tự Sáng Tạo Dàn Nhân Vật';
  }
}

async function deleteCharacter(charId) {
  if (!confirm(`Bạn có chắc muốn xóa nhân vật này?`)) return;
  try {
    const res = await fetch(`/api/character/${charId}`, { method: 'DELETE' });
    if (res.ok) {
      await fetchState();
    }
  } catch (err) {
    alert('Lỗi xóa nhân vật: ' + err.message);
  }
}

// Modal Handlers
function openAddCharModal() {
  document.getElementById('add-char-modal').classList.remove('hidden');
}

function closeAddCharModal() {
  document.getElementById('add-char-modal').classList.add('hidden');
}

async function submitAddCharacter() {
  const name = document.getElementById('modal-char-name').value.trim();
  if (!name) {
    alert('Vui lòng nhập tên nhân vật!');
    return;
  }

  const role = document.getElementById('modal-char-role').value;
  const tier = document.getElementById('modal-char-tier').value;
  const motivation = document.getElementById('modal-char-motivation').value;
  const secret = document.getElementById('modal-char-secret').value;
  const tags = document.getElementById('modal-char-tags').value.split(',').map(t => t.trim());

  const newChar = {
    character_id: `char_${name.toLowerCase().replace(/\s+/g, '_')}`,
    name: name,
    role: role,
    visual_tags: tags,
    personality: {
      core_motivation: motivation || "Tu luyện thành tài",
      fatal_flaw: "Cố chấp",
      moral_boundary: "Không làm hại kẻ vô tội",
      hidden_secret: secret
    },
    speech: { vocabulary_level: "Tiêu chuẩn" },
    status: {
      power_tier: tier,
      health_condition: "Khỏe mạnh",
      mental_state: "Bình tĩnh"
    }
  };

  try {
    const res = await fetch('/api/character/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newChar)
    });
    if (res.ok) {
      closeAddCharModal();
      await fetchState();
    }
  } catch (err) {
    alert('Lỗi thêm nhân vật: ' + err.message);
  }
}

// ----------------------------------------------------------------------
// 3. RPG Discovery Codex Dashboard
// ----------------------------------------------------------------------

async function refreshDiscoveryCodex() {
  try {
    const res = await fetch('/api/discovery/codex');
    if (res.ok) {
      discoveryCodex = await res.json();
      renderRPGCodex(discoveryCodex);
      renderFateChoices(discoveryCodex.active_fate_options || []);
    }
  } catch (err) {
    console.warn("Could not fetch discovery codex", err);
  }
}

function renderRPGCodex(codex) {
  if (!codex) return;
  document.getElementById('discovery-count-badge').innerText = codex.total_discoveries || 0;

  // Render Character RPG Stat Cards
  const statsContainer = document.getElementById('rpg-stats-container');
  statsContainer.innerHTML = '';

  const stats = codex.rpg_character_stats || {};
  for (const [charId, stat] of Object.entries(stats)) {
    const charName = charId === 'char_lin_feng' ? 'Lâm Phong' : charId === 'char_elder_zhao' ? 'Đại Trưởng Lão Triệu' : charId;
    const card = document.createElement('div');
    card.className = 'rpg-char-stat-card';
    card.innerHTML = `
      <div class="rpg-stat-header">
        <span class="rpg-char-name">${charName}</span>
        <span class="rpg-level-badge">⚡ ${stat.level}</span>
      </div>
      <div class="rpg-bars">
        <div class="stat-bar-label">
          <span>Sinh Lực (HP)</span>
          <span>${stat.hp_percent}%</span>
        </div>
        <div class="progress-bar-bg">
          <div class="progress-hp" style="width: ${stat.hp_percent}%"></div>
        </div>
      </div>
      <div class="rpg-sub-stats">
        <span>🍀 Khí Vận: <strong>${stat.luck_score}/100</strong></span>
        <span>🎖️ Danh Vọng: <strong>${stat.reputation}</strong></span>
        <span>🏰 Phe: <strong>${stat.faction_alignment}</strong></span>
      </div>
    `;
    statsContainer.appendChild(card);
  }

  // Render Discovery Entries
  const entriesContainer = document.getElementById('discovery-entries-container');
  entriesContainer.innerHTML = '';

  (codex.entries || []).forEach(e => {
    const itemCard = document.createElement('div');
    itemCard.className = 'discovery-card';
    const icon = e.discovery_type === 'ITEM_LOOT' ? '💎' : e.discovery_type === 'NEW_LOCATION' ? '📍' : '🤫';

    itemCard.innerHTML = `
      <div class="discovery-icon-box">${icon}</div>
      <div>
        <div class="discovery-title">${e.title}</div>
        <p class="discovery-desc">${e.description}</p>
        <span style="font-size:0.7rem; color:#64748b;">Khám phá trong: ${e.discovered_in_scene}</span>
      </div>
    `;
    entriesContainer.appendChild(itemCard);
  });
}

function renderFateChoices(choices) {
  const container = document.getElementById('fate-choices-container');
  container.innerHTML = '';

  choices.forEach((fc, idx) => {
    const card = document.createElement('div');
    card.className = `fate-choice-card ${idx === 0 ? 'selected' : ''}`;
    if (idx === 0) selectedFateChoice = fc;

    card.onclick = () => {
      document.querySelectorAll('.fate-choice-card').forEach(el => el.classList.remove('selected'));
      card.classList.add('selected');
      selectedFateChoice = fc;
    };

    card.innerHTML = `
      <div class="fate-header">${fc.title}</div>
      <div class="fate-desc">${fc.description}</div>
      <div class="fate-impact">⚡ Tác động: ${fc.character_trait_impact} | ⚖️ ${fc.risk_reward}</div>
    `;
    container.appendChild(card);
  });
}

// ----------------------------------------------------------------------
// 4. Novel Drafting Galaxy (Viết Truyện & Số Phận)
// ----------------------------------------------------------------------

async function generateScene() {
  const btn = document.getElementById('btn-generate-scene');
  const indicator = document.getElementById('status-indicator');
  const proseOutput = document.getElementById('prose-output');
  const auditBadge = document.getElementById('audit-badge');
  const wordCountBadge = document.getElementById('word-count-badge');
  const savedFileAlert = document.getElementById('file-saved-alert');

  const selectedModel = document.getElementById('model-select').value;

  btn.disabled = true;
  indicator.classList.remove('hidden');
  auditBadge.classList.add('hidden');
  savedFileAlert.classList.add('hidden');
  proseOutput.innerHTML = `<p class="placeholder-text">⏳ Đang gọi model thực tế <strong>[${selectedModel}]</strong> để sinh văn bản tiểu thuyết...</p>`;

  const castSize = parseInt(document.getElementById('cast-size-select').value, 10);
  const spotlightChar = document.getElementById('spotlight-char-select').value;
  const fateDirective = selectedFateChoice ? selectedFateChoice.title + ": " + selectedFateChoice.description : "";

  const payload = {
    contract: {
      scene_id: "VOL01_CH01_SC01",
      chapter_id: "CH01",
      scene_index: 1,
      location: "Lâm Gia - Hội Nghị Đường",
      time_of_day: "Hoàng hôn",
      pov_character_id: spotlightChar,
      present_characters: castSize === 1 ? [spotlightChar] : [spotlightChar, "char_elder_zhao"],
      target_word_count: 800,
      narrative_goal: `[Số lượng nhân vật: ${castSize}] ` + (fateDirective || "Lâm Phong ném linh thạch trả nợ để chuộc lại Vân Hà Ngọc Bội."),
      conflict_dynamic: "Đại Trưởng Lão Triệu ép giá tăng gấp đôi lên 1,000 linh thạch và công khai sỉ nhục.",
      scene_resolution: "Lâm Phong dằn mặt trưởng lão bằng cách ném đủ linh thạch.",
      cliffhanger_hook: "Triệu trưởng lão nhận ra luồng linh khí cổ xưa trên ngọc bội và ra lệnh phong tỏa toàn bộ lối ra.",
      hard_constraints: [
        "Lâm Phong chưa đạt Trúc Cơ, TUYỆT ĐỐI KHÔNG được giết Trưởng Lão trong cảnh này.",
        "Không được để lộ danh tính linh hồn trong chiếc nhẫn.",
        "Văn phong sắc sảo, dồn dập (Show, don't tell)."
      ]
    },
    provider_model: selectedModel,
    generate_comic: true
  };

  try {
    const res = await fetch('/api/scene/draft', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const data = await res.json();
      renderDraft(data);
      await refreshDiscoveryCodex();
    } else {
      const err = await res.json();
      proseOutput.innerHTML = `<p style="color: #f43f5e;">❌ Lỗi khi sinh chương từ model [${selectedModel}]: ${JSON.stringify(err)}</p>`;
    }
  } catch (err) {
    proseOutput.innerHTML = `<p style="color: #f43f5e;">❌ Lỗi kết nối tới AI Engine: ${err.message}</p>`;
  } finally {
    btn.disabled = false;
    indicator.classList.add('hidden');
  }
}

function renderDraft(data) {
  currentDraft = data;
  const proseOutput = document.getElementById('prose-output');
  const auditBadge = document.getElementById('audit-badge');
  const wordCountBadge = document.getElementById('word-count-badge');
  const savedFileAlert = document.getElementById('file-saved-alert');

  proseOutput.innerText = data.prose_content;
  auditBadge.classList.remove('hidden');
  savedFileAlert.classList.remove('hidden');

  const words = data.prose_content.trim().split(/\s+/).length;
  wordCountBadge.innerText = `${words} từ`;

  // Render Comic Storyboard
  if (data.comic_storyboard && data.comic_storyboard.panels) {
    renderComicPanels(data.comic_storyboard.panels);
  }
}

function renderComicPanels(panels) {
  const container = document.getElementById('comic-panels-grid');
  container.innerHTML = '';

  panels.forEach(p => {
    const card = document.createElement('div');
    card.className = 'comic-panel-card';

    let dialogueHtml = '';
    if (p.dialogue && p.dialogue.length > 0) {
      const dialogueText = p.dialogue.map(d => {
        const speaker = Object.keys(d)[0];
        return `<strong>${speaker}:</strong> "${d[speaker]}"`;
      }).join('<br>');
      dialogueHtml = `<div class="bubble-box">${dialogueText}</div>`;
    }

    const sfxHtml = p.sound_effects_sfx 
      ? `<div class="sfx-overlay">${p.sound_effects_sfx}</div>` 
      : '';

    card.innerHTML = `
      <div class="panel-card-header">
        <span class="panel-index">PANEL #${p.panel_index}</span>
        <span class="camera-angle-badge">🎥 ${p.camera_angle}</span>
      </div>
      <div class="panel-visual-canvas">
        <p class="panel-visual-desc">${p.visual_composition}</p>
        ${sfxHtml}
      </div>
      <div class="panel-card-body">
        ${dialogueHtml}
        <div class="prompt-box">
          <span class="label">AI Art Prompt (Flux/Midjourney)</span>
          <code>${p.image_prompt_for_ai}</code>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

function copyProse() {
  if (!currentDraft || !currentDraft.prose_content) return;
  navigator.clipboard.writeText(currentDraft.prose_content);
  alert("Đã sao chép nội dung tiểu thuyết!");
}
