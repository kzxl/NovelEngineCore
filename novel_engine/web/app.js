// NovelEngineCore Web UI Application Logic

let currentDraft = null;

function switchTab(tabName) {
  const novelBtn = document.getElementById('tab-btn-novel');
  const comicBtn = document.getElementById('tab-btn-comic');
  const novelPane = document.getElementById('tab-content-novel');
  const comicPane = document.getElementById('tab-content-comic');

  if (tabName === 'novel') {
    novelBtn.classList.add('active');
    comicBtn.classList.remove('active');
    novelPane.classList.add('active');
    comicPane.classList.remove('active');
  } else {
    comicBtn.classList.add('active');
    novelBtn.classList.remove('active');
    comicPane.classList.add('active');
    novelPane.classList.remove('active');
  }
}

async function generateScene() {
  const btn = document.getElementById('btn-generate-scene');
  const indicator = document.getElementById('status-indicator');
  const proseOutput = document.getElementById('prose-output');
  const auditBadge = document.getElementById('audit-badge');
  const wordCountBadge = document.getElementById('word-count-badge');

  btn.disabled = true;
  indicator.classList.remove('hidden');
  auditBadge.classList.add('hidden');
  proseOutput.innerHTML = '<p class="placeholder-text">⏳ Đang tổng hợp ngữ cảnh vi mô (Micro-Context) và kích hoạt Universe Pipeline...</p>';

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
    generate_comic: true
  };

  try {
    const res = await fetch('/api/scene/draft', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      // Fallback to local simulated draft if backend endpoint needs story init first
      await initAndRetry(payload);
      return;
    }

    const data = await res.json();
    renderDraft(data);
  } catch (err) {
    console.warn("Direct API call failed, running simulated pipeline:", err);
    renderMockDraft();
  } finally {
    btn.disabled = false;
    indicator.classList.add('hidden');
  }
}

async function initAndRetry(payload) {
  await fetch('/api/story/init', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: document.getElementById('story-title').value,
      logline: document.getElementById('story-logline').value,
      genre: document.getElementById('story-genre').value,
      provider_model: document.getElementById('model-select').value
    })
  });

  const res = await fetch('/api/scene/draft', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  renderDraft(data);
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

document.getElementById('btn-quick-sample').addEventListener('click', () => {
  generateScene();
});
