// ==========================================================================
// NovelEngineCore - Universe Studio v4.0 Application Logic
// ==========================================================================

let storyState = null;
let currentDraft = null;

// Switch Active Galaxy View
function switchGalaxy(viewName) {
  const views = ['world', 'characters', 'novel', 'comic', 'plugins'];
  views.forEach(v => {
    const navBtn = document.getElementById(`nav-${v}`);
    const viewPane = document.getElementById(`galaxy-view-${v}`);
    if (v === viewName) {
      navBtn.classList.add('active');
      viewPane.classList.add('active');
    } else {
      navBtn.classList.remove('active');
      viewPane.classList.remove('active');
    }
  });
}

// Initial Fetch on Page Load
document.addEventListener('DOMContentLoaded', async () => {
  await fetchState();
});

async function fetchState() {
  try {
    const res = await fetch('/api/state');
    if (res.ok) {
      storyState = await res.json();
      renderAll();
    }
  } catch (err) {
    console.warn("Could not fetch initial state, using local defaults.", err);
  }
}

function renderAll() {
  if (!storyState) return;
  renderWorldView(storyState.world_bible);
  renderCharactersView(storyState.characters);
  updateCharacterBadge();
}

// ----------------------------------------------------------------------
// 1. World Genesis Galaxy Rendering & Actions
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
  btn.disabled = true;
  btn.innerText = '⏳ AI Đang Xây Dựng Thế Giới...';

  try {
    const res = await fetch('/api/world/auto-generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: document.getElementById('world-title').value,
        genre: document.getElementById('world-genre').value,
        logline: document.getElementById('world-logline').value,
        provider_model: document.getElementById('model-select').value
      })
    });
    if (res.ok) {
      const worldBible = await res.json();
      if (storyState) storyState.world_bible = worldBible;
      renderWorldView(worldBible);
      alert('✓ Đã khởi tạo hoàn tất toàn bộ Thế Giới Quan!');
    }
  } catch (err) {
    alert('Lỗi khởi tạo thế giới: ' + err.message);
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
// 2. Character Matrix Galaxy Rendering & Actions
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
// 3. Novel Drafting Galaxy (Viết Truyện & Lưu File Tự Động)
// ----------------------------------------------------------------------

async function generateScene() {
  const btn = document.getElementById('btn-generate-scene');
  const indicator = document.getElementById('status-indicator');
  const proseOutput = document.getElementById('prose-output');
  const auditBadge = document.getElementById('audit-badge');
  const wordCountBadge = document.getElementById('word-count-badge');

  btn.disabled = true;
  indicator.classList.remove('hidden');
  auditBadge.classList.add('hidden');
  proseOutput.innerHTML = '<p class="placeholder-text">⏳ Đang tổng hợp ngữ cảnh vi mô và kích hoạt Universe Gravitational Pipeline...</p>';

  const payload = {
    contract: {
      scene_id: "VOL01_CH01_SC01",
      chapter_id: "CH01",
      scene_index: 1,
      location: "Lâm Gia - Hội Nghị Đường",
      time_of_day: "Hoàng hôn",
      pov_character_id: "char_lin_feng",
      present_characters: ["char_lin_feng"],
      target_word_count: 1200,
      narrative_goal: document.getElementById('contract-goal').innerText,
      conflict_dynamic: document.getElementById('contract-conflict').innerText,
      scene_resolution: "Lâm Phong dằn mặt trưởng lão bằng cách ném đủ linh thạch.",
      cliffhanger_hook: document.getElementById('contract-hook').innerText,
      hard_constraints: [
        "Lâm Phong chưa đạt Trúc Cơ, TUYỆT ĐỐI KHÔNG được giết Trưởng Lão trong cảnh này.",
        "Không được để lộ danh tính linh hồn trong chiếc nhẫn.",
        "Văn phong sắc sảo, dồn dập (Show, don't tell)."
      ]
    },
    provider_model: document.getElementById('model-select').value,
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
    } else {
      renderMockDraft();
    }
  } catch (err) {
    console.warn("Direct draft failed, fallback mock draft", err);
    renderMockDraft();
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

  proseOutput.innerText = data.prose_content;
  auditBadge.classList.remove('hidden');
  const words = data.prose_content.trim().split(/\s+/).length;
  wordCountBadge.innerText = `${words} từ`;

  // Render Comic Storyboard
  if (data.comic_storyboard && data.comic_storyboard.panels) {
    renderComicPanels(data.comic_storyboard.panels);
  }
}

function renderMockDraft() {
  const mockProse = `Hoàng hôn đỏ quạch như máu nhuộm đỏ cả khoảng sân của Lâm Gia. Lâm Phong đứng thẳng người giữa sảnh Nghị Sự, bờ vai phải vẫn còn rỉ máu từ vết thương cũ, nhưng đôi mắt đen nhánh của chàng lại phẳng lặng như mặt hồ ngàn năm.

"Năm trăm linh thạch hạ phẩm, một viên không thiếu!" – Giọng nói của Lâm Phong vang lên đanh gọn. Chàng giơ tay, một túi gấm nặng trịch rơi xuống bàn gỗ lim phát ra tiếng 'bộp' giòn giã.

Phía trên chủ vị, Đại Trưởng Lão Triệu nheo cặp mắt ưng, khóe môi khẽ nhếch lên nụ cười mỉa mai: "Lâm Phong, ngươi đùa với lão phu sao? Giá của Vân Hà Ngọc Bội hôm nay... là một ngàn linh thạch!"

Sát khí vô hình bỗng chốc tràn ngập cả gian phòng. Lâm Phong không lùi nửa bước, bàn tay trái giấu trong tay áo khẽ chạm vào chiếc nhẫn hắc thiết, ánh mắt lạnh băng khóa chặt vào gã trưởng lão tham lam.`;

  const mockPanels = [
    {
      panel_index: 1,
      camera_angle: "Wide Shot (Toàn cảnh)",
      visual_composition: "Góc rộng từ trên cao nhìn xuống sảnh đường Lâm Gia, hoàng hôn đỏ rực chiếu qua ô cửa sổ gỗ, Lâm Phong đứng cô độc đối diện hàng trưởng lão.",
      dialogue: [{ "Lâm Phong": "Năm trăm linh thạch, một viên không thiếu!" }],
      sound_effects_sfx: "BỘP!",
      image_prompt_for_ai: "Wide cinematic shot, ancient chinese xianxia martial hall, sunset crimson light, young cultivator with black ponytail and ragged blue robes facing intimidating elders on thrones, dynamic lighting, 8k anime artstyle"
    },
    {
      panel_index: 2,
      camera_angle: "Close-up (Cận cảnh)",
      visual_composition: "Cận cảnh nụ cười đểu cáng của Đại Trưởng Lão Triệu, ánh mắt thâm độc, tay vuốt chòm râu dê.",
      dialogue: [{ "Đại Trưởng Lão": "Hôm nay giá là một ngàn linh thạch!" }],
      sound_effects_sfx: "HẮC HẮC...",
      image_prompt_for_ai: "Close up shot of cunning old elder with long grey goatee, sinister smirk, luxurious embroidered silk robes, glowing jade ornaments, intense dramatic rim light, webtoon illustration"
    },
    {
      panel_index: 3,
      camera_angle: "Dutch Angle (Góc nghiêng căng thẳng)",
      visual_composition: "Góc nghiêng kịch tính đặc tả đôi mắt sắc lẹm của Lâm Phong, tay nắm chặt lại, luồng linh khí mờ ảo bắt đầu dao động quanh ngón tay.",
      dialogue: [{ "Lâm Phong": "..." }],
      sound_effects_sfx: "RẮC!",
      image_prompt_for_ai: "Dutch angle extreme focus on protagonist cold sharp eyes, black hair fluttering, subtle dark spiritual aura rising from iron ring on finger, high tension, manhwa action style"
    }
  ];

  renderDraft({
    prose_content: mockProse,
    comic_storyboard: { panels: mockPanels }
  });
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
