const fallbackVoiceCatalog = {
  orpheus: ["tara", "leah", "jess", "leo", "dan", "mia", "zac", "zoe"],
  kokoro: [
    "af_heart",
    "af_bella",
    "af_nicole",
    "af_sarah",
    "af_aoede",
    "af_kore",
    "af_nova",
    "af_sky",
    "am_puck",
    "am_fenrir",
    "am_michael",
    "am_liam",
    "bf_emma",
    "bf_isabella",
    "bm_george",
    "bm_fable",
  ],
  piper: [
    "en_US-lessac-medium",
    "en_GB-alba-medium",
    "de_DE-thorsten-medium",
    "fr_FR-siwis-medium",
    "es_ES-sharvard-medium",
    "zh_CN-huayan-medium",
  ],
  mlx: ["default"],
};
const fallbackDefaultVoice = {
  orpheus: "tara",
  kokoro: "af_heart",
  piper: "en_US-lessac-medium",
  mlx: "default",
};
const defaultSpeakerMaps = {
  orpheus: { A: "tara", B: "leo", C: "mia", D: "leah", E: "dan", F: "zoe" },
  kokoro: {
    A: "af_heart",
    B: "am_puck",
    C: "bf_emma",
    D: "af_bella",
    E: "am_michael",
    F: "bf_isabella",
  },
  piper: {
    A: "en_US-lessac-medium",
    B: "en_GB-alba-medium",
    C: "de_DE-thorsten-medium",
    D: "fr_FR-siwis-medium",
    E: "es_ES-sharvard-medium",
    F: "zh_CN-huayan-medium",
  },
  mlx: {
    A: "default",
    B: "default",
    C: "default",
    D: "default",
    E: "default",
    F: "default",
  },
};
const speakers = ["A", "B", "C", "D", "E", "F"];
const backends = [
  { id: "orpheus", label: "Orpheus" },
  { id: "chatterbox", label: "Chatterbox Multilingual" },
  { id: "kokoro", label: "Kokoro (英語推奨)" },
  { id: "piper", label: "Piper" },
  { id: "mlx", label: "MLX-Audio (Mac)" },
  { id: "dia", label: "Dia (実験)" },
];
const fallbackLanguages = {
  ar: "Arabic",
  da: "Danish",
  de: "German",
  el: "Greek",
  en: "English",
  es: "Spanish",
  fi: "Finnish",
  fr: "French",
  he: "Hebrew",
  hi: "Hindi",
  it: "Italian",
  ja: "Japanese",
  ko: "Korean",
  ms: "Malay",
  nl: "Dutch",
  no: "Norwegian",
  pl: "Polish",
  pt: "Portuguese",
  ru: "Russian",
  sv: "Swedish",
  sw: "Swahili",
  tr: "Turkish",
  zh: "Chinese",
};
const mlxSettingProfiles = {
  "mlx-chatterbox": {
    visible: ["model", "language", "maxTokens", "temperature", "topP", "repetitionPenalty", "exaggeration", "cfgWeight", "minP", "seed", "refAudio"],
    defaults: { maxTokens: 1000, temperature: 0.65, topP: 1, repetitionPenalty: 1.2, exaggeration: 0.5, cfgWeight: 0.5, minP: 0.05, seed: 0 },
    hint: "Chatterbox MLX: 日本語/英語を含む多言語と参照音声向け。Top-kや指示文はこのモデルでは使いません。",
    placeholders: {
      refAudio: "任意: path/to/voice.wav",
    },
  },
  "mlx-qwen3-tts": {
    visible: ["model", "language", "speed", "maxTokens", "temperature", "topP", "topK", "repetitionPenalty", "seed", "refAudio", "refText"],
    defaults: { speed: 1, maxTokens: 1200, temperature: 0.35, topP: 0.85, topK: 20, repetitionPenalty: 1.2, seed: 42 },
    hint: "Qwen3-TTS Base: プリセット声ではなく参照音声で声を固定するモデルです。参照音声を使わない場合は声が揺れやすいので、キャラ別の声にはCustomVoiceを使ってください。",
    placeholders: {
      refAudio: "任意: path/to/reference.wav",
      refText: "参照音声で読まれている文章",
    },
  },
  "mlx-qwen3-custom": {
    visible: ["model", "language", "speed", "maxTokens", "temperature", "topP", "topK", "repetitionPenalty", "seed", "instruct"],
    defaults: { speed: 1, maxTokens: 1200, temperature: 0.35, topP: 0.85, topK: 20, repetitionPenalty: 1.2, seed: 42 },
    hint: "Qwen3 CustomVoice: プリセット声に感情や話し方の指示を足すモデル。声の一貫性を優先するため既定値は安定寄りです。",
    placeholders: {
      instruct: "例: cheerful, calm, clear Japanese narration",
    },
  },
  "mlx-qwen3-voice-design": {
    visible: ["model", "language", "speed", "maxTokens", "temperature", "topP", "topK", "repetitionPenalty", "seed", "instruct"],
    defaults: { speed: 1, maxTokens: 1200, temperature: 0.3, topP: 0.85, topK: 20, repetitionPenalty: 1.2, seed: 42 },
    hint: "Qwen3 VoiceDesign: 声質説明が必須のモデル。行ごとに揺れやすいので、固定seedと低めの温度で使います。",
    placeholders: {
      instruct: "例: a warm adult Japanese teacher voice, calm pace, clear pronunciation",
    },
  },
  "mlx-kokoro": {
    visible: ["model", "language", "speed", "seed"],
    defaults: { speed: 1, seed: 0 },
    hint: "Kokoro MLX: 軽量高速な日本語/英語TTS。参照音声やLLM系サンプリング設定は使いません。",
  },
  "mlx-dia": {
    visible: ["model", "maxTokens", "temperature", "topP", "topK", "seed", "refAudio"],
    defaults: { maxTokens: 1280, temperature: 1.3, topP: 0.95, topK: 50, seed: 0 },
    hint: "Dia MLX: 英語の[S1]/[S2]台本専用。単発と長文は無効化します。",
    placeholders: {
      refAudio: "任意: 英語会話の参照音声",
    },
  },
  default: {
    visible: ["model", "language", "speed", "maxTokens", "temperature", "topP", "topK", "repetitionPenalty", "seed"],
    defaults: { speed: 1, maxTokens: 1200, temperature: 0.7, topP: 0.9, topK: 50, repetitionPenalty: 1.1, seed: 0 },
    hint: "モデルを選ぶと、使える設定だけ表示します。",
  },
};
const mlxSettingInputSelectors = {
  speed: "#mlxSpeed",
  maxTokens: "#mlxMaxTokens",
  temperature: "#mlxTemperature",
  topP: "#mlxTopP",
  topK: "#mlxTopK",
  repetitionPenalty: "#mlxRepetitionPenalty",
  exaggeration: "#mlxExaggeration",
  cfgWeight: "#mlxCfgWeight",
  minP: "#mlxMinP",
  seed: "#mlxSeed",
};
const mlxTextInputSelectors = {
  refAudio: "#mlxRefAudioPath",
  refText: "#mlxRefText",
  instruct: "#mlxInstruct",
};
const defaultSingleText = "Hello, this is a local Ultra-TTS test.";
const diaSingleSample =
  "[S1] Dia is an open weights text to dialogue model. [S2] It works best with English conversation and alternating speakers. [S1] For regular English TTS, Kokoro is the safer choice.";
const defaultScriptText = [
  "A: Hello, how are you?",
  "B: I'm good. Let's generate this as a two-speaker WAV.",
].join("\n");
const diaScriptSample = [
  "[S1] Dia works best when the script starts with speaker one.",
  "[S2] And then speaker two answers in English.",
  "[S1] Short tests can sound unnatural, so this sample gives it a little more context.",
  "[S2] For everyday English narration, Kokoro is usually the simpler model to try first.",
].join("\n");

let mode = "single";
let backend = "kokoro";
let backendMetadata = {};
let selectedVoiceByBackend = { ...fallbackDefaultVoice };
let selectedSpeakerMapByContext = {};
let selectedMlxModelId = "mlx-chatterbox";
let activeSpeaker = "A";
let appControlInProgress = false;

const $ = (selector) => document.querySelector(selector);
const statusText = $("#statusText");
const logBox = $("#log");
const audioPlayer = $("#audioPlayer");
const downloadLink = $("#downloadLink");
const manifestLink = $("#manifestLink");
const resultMeta = $("#resultMeta");
const outputState = $("#outputState");
const outputStateLabel = $("#outputStateLabel");
const outputElapsed = $("#outputElapsed");
const modelSummary = $("#modelSummary");
const modelList = $("#modelList");
let outputTimerId = null;
let outputStartedAt = 0;

function log(message) {
  const time = new Date().toLocaleTimeString();
  logBox.textContent += `[${time}] ${message}\n`;
  logBox.scrollTop = logBox.scrollHeight;
}

function setBusy(isBusy) {
  document.querySelectorAll("button, textarea, input, select").forEach((element) => {
    if (element.dataset.appControl === "true") {
      element.disabled = appControlInProgress;
      return;
    }
    element.disabled = isBusy;
  });
  if (!isBusy) syncBackendUi();
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function formatElapsed(ms) {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = String(totalSeconds % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

function stopOutputTimer() {
  if (outputTimerId !== null) {
    clearInterval(outputTimerId);
    outputTimerId = null;
  }
}

function updateOutputElapsed() {
  if (!outputStartedAt) return;
  outputElapsed.textContent = formatElapsed(Date.now() - outputStartedAt);
}

function setOutputState(state) {
  const labels = {
    ready: "出力可能",
    running: "出力中",
    done: "出力完了",
  };
  stopOutputTimer();
  outputState.className = `output-state output-${state}`;
  outputStateLabel.textContent = labels[state] || labels.ready;

  if (state === "running") {
    outputStartedAt = Date.now();
    updateOutputElapsed();
    outputTimerId = setInterval(updateOutputElapsed, 1000);
    return;
  }

  if (!outputStartedAt || state === "ready") {
    outputElapsed.textContent = "";
    outputStartedAt = 0;
    return;
  }

  updateOutputElapsed();
}

async function api(path, body = null) {
  const options = body
    ? {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }
    : {};
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok || data.ok === false) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

async function waitForRestart(timeoutMs = 20000) {
  const startedAt = Date.now();
  let sawDisconnect = false;
  await sleep(800);

  while (Date.now() - startedAt < timeoutMs) {
    try {
      const response = await fetch(`/api/status?t=${Date.now()}`, { cache: "no-store" });
      if (response.ok && (sawDisconnect || Date.now() - startedAt > 1800)) return true;
    } catch (_) {
      sawDisconnect = true;
    }
    await sleep(500);
  }

  return false;
}

function backendLabel() {
  return backends.find((item) => item.id === backend)?.label || backend;
}

function backendRuntimeLabel(id) {
  const status = backendMetadata[id];
  if (!status) return "確認中";
  if (status.ready) return "使用可";
  if (status.installed === false) return "未構築";
  if (id === "orpheus" && !status.serverRunning) return "LM Studio待ち";
  if (id === "orpheus" && !status.modelLoaded) return "モデル未ロード";
  return "準備待ち";
}

function formatScriptForBackend(nextBackend, previousBackend) {
  const textarea = $("#scriptText");
  const current = textarea.value;
  const converted = (nextBackend === "dia" || (nextBackend === "mlx" && currentMlxModelId() === "mlx-dia"))
    ? toDiaScript(current)
    : toLetterScript(current);
  if (converted !== current) {
    textarea.value = converted;
    const style = (nextBackend === "dia" || (nextBackend === "mlx" && currentMlxModelId() === "mlx-dia")) ? "[S1]/[S2]" : "A:/B:";
    log(`台本形式を${style}に変換しました`);
  }

  if (nextBackend === "dia" || (nextBackend === "mlx" && currentMlxModelId() === "mlx-dia")) {
    activeSpeaker = "S1";
  } else if (previousBackend === "dia" || (previousBackend === "mlx" && activeSpeaker.startsWith("S"))) {
    activeSpeaker = "A";
  }
}

function toDiaScript(script) {
  const fixedLabels = { A: "S1", B: "S2" };
  const labelMap = {};
  const usedTags = new Set();
  let nextTag = 1;

  return script
    .split(/\r?\n/)
    .map((line) => {
      const diaMatch = line.match(/^\s*\[(S[12])\]\s*(.*?)\s*$/i);
      if (diaMatch) return `[${diaMatch[1].toUpperCase()}] ${diaMatch[2]}`.trim();

      const letterMatch = line.match(/^\s*([A-Za-z0-9_-]+)\s*[:：]\s*(.*?)\s*$/);
      if (!letterMatch) return line;

      const label = letterMatch[1].trim().toUpperCase();
      if (fixedLabels[label]) {
        labelMap[label] = fixedLabels[label];
        usedTags.add(labelMap[label]);
      }
      if (!labelMap[label]) {
        while (usedTags.has(`S${nextTag}`)) nextTag += 1;
        if (nextTag > 2) return line;
        labelMap[label] = `S${nextTag}`;
        usedTags.add(labelMap[label]);
        nextTag += 1;
      }

      return `[${labelMap[label]}] ${letterMatch[2].trim()}`;
    })
    .join("\n");
}

function toLetterScript(script) {
  return script
    .split(/\r?\n/)
    .map((line) => {
      const match = line.match(/^\s*\[(S[12])\]\s*(.*?)\s*$/i);
      if (!match) return line;

      const label = match[1].toUpperCase() === "S1" ? "A" : "B";
      return `${label}: ${match[2].trim()}`;
    })
    .join("\n");
}

function currentMlxCatalog() {
  return backendMetadata.mlx?.modelCatalog || {};
}

function currentMlxModelId() {
  const catalog = currentMlxCatalog();
  if (catalog[selectedMlxModelId]) return selectedMlxModelId;
  const fallback = backendMetadata.mlx?.defaultModelId || selectedMlxModelId;
  selectedMlxModelId = catalog[fallback] ? fallback : Object.keys(catalog)[0] || selectedMlxModelId;
  return selectedMlxModelId;
}

function currentMlxModel() {
  return currentMlxCatalog()[currentMlxModelId()] || null;
}

function currentMlxSettingProfile(modelId = currentMlxModelId()) {
  return mlxSettingProfiles[modelId] || mlxSettingProfiles.default;
}

function currentMlxVisibleSettings(modelId = currentMlxModelId()) {
  return new Set(currentMlxSettingProfile(modelId).visible);
}

function isMlxSettingVisible(setting) {
  return backend === "mlx" && currentMlxVisibleSettings().has(setting);
}

function backendUsesDiaScript(id = backend) {
  return id === "dia" || (id === "mlx" && currentMlxModelId() === "mlx-dia");
}

function isVoiceBackend() {
  return backend === "orpheus" || backend === "kokoro" || backend === "piper" || backend === "mlx";
}

function shouldShowVoiceControls() {
  if (!isVoiceBackend()) return false;
  if (backend !== "mlx") return true;
  if (backendUsesDiaScript()) return false;
  return currentVoices().length > 0;
}

function shouldShowSpeakerMap() {
  if (!shouldShowVoiceControls()) return false;
  if (backend === "mlx") return currentVoices().length > 1;
  return true;
}

function voiceHelpText() {
  if (backend !== "mlx") return "";

  const modelId = currentMlxModelId();
  if (modelId === "mlx-qwen3-tts") {
    return "Qwen3 Baseはプリセット声なし。参照音声と文字起こしで声を固定します。Ryan/Vivianなどを使う場合はQwen3 CustomVoiceを選んでください。";
  }
  if (modelId === "mlx-qwen3-custom") {
    return "Qwen3 CustomVoiceはプリセット声を指定できます。台本のA/B/Cは下の話者割り当てで固定します。";
  }
  if (modelId === "mlx-qwen3-voice-design") {
    return "Qwen3 VoiceDesignはプリセット声ではなく、声・感情の指示欄で声質を設計します。";
  }
  if (modelId === "mlx-chatterbox") {
    return "Chatterboxはプリセット声ではなく、参照音声パスで声質を寄せます。";
  }
  if (modelId === "mlx-kokoro") {
    return "Kokoroはプリセット声を指定できます。";
  }
  return "";
}

function currentVoices() {
  if (backend === "mlx") {
    const voices = currentMlxModel()?.voices;
    if (Array.isArray(voices) && voices.length) return voices;
  }
  const metadataVoices = backendMetadata[backend]?.voices;
  if (Array.isArray(metadataVoices) && metadataVoices.length) return metadataVoices;
  return fallbackVoiceCatalog[backend] || [];
}

function currentDefaultVoice() {
  if (backend === "mlx") {
    return currentMlxModel()?.defaultVoice || currentVoices()[0] || "default";
  }
  const voices = currentVoices();
  return backendMetadata[backend]?.defaultVoice || fallbackDefaultVoice[backend] || voices[0] || "";
}

function currentSingleVoice() {
  const voices = currentVoices();
  const selected = selectedVoiceByBackend[backend];
  if (voices.includes(selected)) return selected;

  selectedVoiceByBackend[backend] = currentDefaultVoice();
  return selectedVoiceByBackend[backend];
}

function speakerMapContextKey() {
  return backend === "mlx" ? `${backend}:${currentMlxModelId()}` : backend;
}

function rememberSpeakerMap() {
  const key = speakerMapContextKey();
  const values = selectedSpeakerMapByContext[key] || {};
  document.querySelectorAll("#speakerMap select").forEach((select) => {
    values[select.dataset.speaker] = select.value;
  });
  selectedSpeakerMapByContext[key] = values;
  return values;
}

function defaultVoiceForSpeaker(voices, speaker, index) {
  const defaults = backend === "mlx" ? {} : defaultSpeakerMaps[backend] || {};
  if (voices.includes(defaults[speaker])) return defaults[speaker];
  if (backend === "mlx" && voices.length > 1) return voices[index % voices.length];
  return currentDefaultVoice();
}

function backendSegmentLimit() {
  if (backend === "mlx") return currentMlxModel()?.maxTextChars || 300;
  if (backend === "chatterbox") return 300;
  if (backend === "kokoro") return 1200;
  if (backend === "piper") return 1000;
  if (backend === "orpheus") return 600;
  return 300;
}

function renderBackendButtons() {
  const container = $("#backendButtons");
  container.innerHTML = "";
  backends.forEach((item) => {
    const runtimeLabel = backendRuntimeLabel(item.id);
    const status = backendMetadata[item.id];
    const button = document.createElement("button");
    button.type = "button";
    button.className = [
      "backend-button",
      item.id === backend ? "active" : "",
      status?.ready ? "backend-ready" : "backend-waiting",
    ]
      .filter(Boolean)
      .join(" ");
    button.innerHTML = `<span>${item.label}</span><small>${runtimeLabel}</small>`;
    button.addEventListener("click", () => {
      const previousBackend = backend;
      formatScriptForBackend(item.id, previousBackend);
      backend = item.id;
      applyBackendSample(previousBackend);
      if (backendUsesDiaScript()) {
        switchMode("script");
      }
      renderBackendButtons();
      renderVoiceButtons();
      renderSpeakerMap();
      renderSpeakerButtons();
      syncBackendUi();
      refreshStatus().catch(() => {});
    });
    container.appendChild(button);
  });
}

function applyBackendSample(previousBackend) {
  if (!backendUsesDiaScript() || previousBackend === "dia") return;

  const singleText = $("#singleText");
  const scriptText = $("#scriptText");
  if (singleText.value.trim() === defaultSingleText) {
    singleText.value = diaSingleSample;
  }
  if (!scriptText.value.trim()) {
    scriptText.value = diaScriptSample;
  }
}

function applyMlxDefaultValues(modelId = currentMlxModelId()) {
  const defaults = currentMlxSettingProfile(modelId).defaults || {};
  Object.entries(defaults).forEach(([setting, value]) => {
    const input = $(mlxSettingInputSelectors[setting]);
    if (input) input.value = String(value);
  });
}

function syncMlxSettingsVisibility({ resetValues = false } = {}) {
  const section = $("#mlxOptions");
  if (!section) return;

  const modelId = currentMlxModelId();
  const profile = currentMlxSettingProfile(modelId);
  const visible = currentMlxVisibleSettings(modelId);
  section.dataset.modelId = modelId;

  if (resetValues) {
    applyMlxDefaultValues(modelId);
  }

  section.querySelectorAll("[data-mlx-setting]").forEach((element) => {
    element.classList.toggle("hidden", !visible.has(element.dataset.mlxSetting));
  });

  const hint = $("#mlxModelHint");
  if (hint) hint.textContent = profile.hint || mlxSettingProfiles.default.hint;

  const placeholders = profile.placeholders || {};
  Object.entries(mlxTextInputSelectors).forEach(([setting, selector]) => {
    const input = $(selector);
    if (!input) return;
    input.placeholder = placeholders[setting] || "";
  });
}

function renderMlxModelOptions() {
  const select = $("#mlxModelId");
  if (!select) return;

  const catalog = currentMlxCatalog();
  const entries = Object.values(catalog);
  const current = currentMlxModelId();
  select.innerHTML = "";
  entries.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.id;
    option.textContent = `${item.name}${item.installed ? "" : " (未DL)"}`;
    if (item.id === current) option.selected = true;
    select.appendChild(option);
  });
  if (!select.value && entries.length) {
    select.value = entries[0].id;
    selectedMlxModelId = entries[0].id;
  }
  renderMlxLanguageOptions();
  syncMlxSettingsVisibility();
}

function renderMlxLanguageOptions(preferDefault = false) {
  const select = $("#mlxLanguageId");
  if (!select) return;

  const model = currentMlxModel();
  const languages = model?.languages || { ja: "Japanese", en: "English" };
  const previous = select.value;
  const fallback = model?.defaultLanguage || Object.keys(languages)[0] || "ja";
  const current = !preferDefault && previous && Object.prototype.hasOwnProperty.call(languages, previous)
    ? previous
    : fallback;
  select.innerHTML = "";
  Object.entries(languages).forEach(([id, name]) => {
    const option = document.createElement("option");
    option.value = id;
    option.textContent = `${name} (${id})`;
    if (id === current) option.selected = true;
    select.appendChild(option);
  });
  if (!select.value) select.value = current;
}

function renderLanguageOptions(languages = fallbackLanguages, defaultLanguage = "ja") {
  const select = $("#languageId");
  const current = select.value || defaultLanguage;
  select.innerHTML = "";
  Object.entries(languages).forEach(([id, name]) => {
    const option = document.createElement("option");
    option.value = id;
    option.textContent = `${name} (${id})`;
    if (id === current) option.selected = true;
    select.appendChild(option);
  });
  if (!select.value) select.value = defaultLanguage;
}

function renderVoiceButtons() {
  const container = $("#singleVoiceButtons");
  container.innerHTML = "";
  const voiceHelp = $("#voiceHelp");
  if (voiceHelp) voiceHelp.textContent = voiceHelpText();
  currentVoices().forEach((voice) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `voice-button ${voice === currentSingleVoice() ? "active" : ""}`;
    button.textContent = voice;
    button.addEventListener("click", () => {
      selectedVoiceByBackend[backend] = voice;
      renderVoiceButtons();
    });
    container.appendChild(button);
  });
}

function modelStateLabel(item) {
  if (!item.installed) return "未DL";
  if (item.runtimeReady) return "使用可";
  if (!item.runtimeInstalled) return "実行環境待ち";
  return "準備待ち";
}

function appendTagGroup(parent, label, values = [], className = "") {
  if (!values.length) return;

  const group = document.createElement("div");
  group.className = `model-tag-group ${className}`.trim();

  const title = document.createElement("span");
  title.className = "model-tag-label";
  title.textContent = label;
  group.appendChild(title);

  values.forEach((value) => {
    const tag = document.createElement("span");
    tag.className = "model-tag";
    tag.textContent = value;
    group.appendChild(tag);
  });

  parent.appendChild(group);
}

function renderModelInventory(data) {
  modelSummary.textContent = `${data.totalSizeLabel} / ${data.modelsDir}`;
  modelList.innerHTML = "";

  data.models.forEach((item) => {
    const row = document.createElement("div");
    row.className = `model-row-item ${item.installed ? "model-installed" : "model-missing"}`;

    const main = document.createElement("div");
    main.className = "model-row-main";

    const title = document.createElement("strong");
    title.textContent = item.role ? `${item.name} · ${item.role}` : item.name;

    const meta = document.createElement("span");
    const count = typeof item.voiceCount === "number" ? ` / ${item.voiceCount} voices` : "";
    meta.textContent = `${item.backend} / ${item.sizeLabel}${count}`;

    const summary = document.createElement("p");
    summary.className = "model-description";
    summary.textContent = item.summary || "";

    const detail = document.createElement("div");
    detail.className = "model-detail";
    appendTagGroup(detail, "言語", item.languages || [], "language-tags");
    appendTagGroup(detail, "特徴", item.strengths || []);
    appendTagGroup(detail, "用途", item.recommendedFor || []);
    appendTagGroup(detail, "注意", item.limitations || [], "limitation-tags");

    const path = document.createElement("code");
    path.textContent = item.path;

    main.append(title, meta);
    if (item.summary) main.appendChild(summary);
    main.appendChild(detail);
    main.appendChild(path);

    const state = document.createElement("span");
    state.className = `model-state ${item.runtimeReady ? "model-ready" : item.installed ? "model-waiting" : "model-not-downloaded"}`;
    state.textContent = modelStateLabel(item);

    row.append(main, state);
    modelList.appendChild(row);
  });
}

async function refreshModels() {
  const data = await api("/api/models");
  renderModelInventory(data);
}

function renderSpeakerMap() {
  const map = $("#speakerMap");
  const saved = rememberSpeakerMap();
  map.innerHTML = "";
  const voices = currentVoices();
  speakers.forEach((speaker, index) => {
    const card = document.createElement("label");
    card.className = "speaker-card";

    const label = document.createElement("span");
    label.textContent = speaker;

    const select = document.createElement("select");
    select.dataset.speaker = speaker;
    voices.forEach((voice) => {
      const option = document.createElement("option");
      option.value = voice;
      option.textContent = voice;
      const preferred = voices.includes(saved[speaker])
        ? saved[speaker]
        : defaultVoiceForSpeaker(voices, speaker, index);
      if (voice === preferred) option.selected = true;
      select.appendChild(option);
    });
    select.addEventListener("change", () => {
      const key = speakerMapContextKey();
      selectedSpeakerMapByContext[key] = {
        ...(selectedSpeakerMapByContext[key] || {}),
        [speaker]: select.value,
      };
    });

    card.append(label, select);
    map.appendChild(card);
  });
}

function renderSpeakerButtons() {
  const container = $("#speakerButtons");
  container.innerHTML = "";
  const visibleSpeakers = backendUsesDiaScript() ? ["S1", "S2"] : speakers.slice(0, 3);
  if (!visibleSpeakers.includes(activeSpeaker)) activeSpeaker = visibleSpeakers[0];

  visibleSpeakers.forEach((speaker) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `speaker-button ${speaker === activeSpeaker ? "active" : ""}`;
    button.textContent = speaker;
    button.addEventListener("click", () => {
      activeSpeaker = speaker;
      renderSpeakerButtons();
    });
    container.appendChild(button);
  });
}

function speakerMap() {
  return { ...rememberSpeakerMap() };
}

function mlxTextOption(setting) {
  if (backend !== "mlx" || !isMlxSettingVisible(setting)) return "";
  const input = $(mlxTextInputSelectors[setting]);
  return input?.value.trim() || "";
}

function mlxNumberOption(setting, fallback) {
  const input = $(mlxSettingInputSelectors[setting]);
  if (backend === "mlx" && !isMlxSettingVisible(setting)) return fallback;
  return Number(input?.value || fallback);
}

function backendOptions() {
  return {
    backend,
    languageId: $("#languageId").value || "ja",
    mlxModelId: $("#mlxModelId")?.value || selectedMlxModelId,
    mlxLanguageId: $("#mlxLanguageId")?.value || currentMlxModel()?.defaultLanguage || "ja",
    mlxRefAudioPath: mlxTextOption("refAudio"),
    mlxRefText: mlxTextOption("refText"),
    mlxInstruct: mlxTextOption("instruct"),
    mlxSpeed: mlxNumberOption("speed", 1),
    mlxMaxTokens: mlxNumberOption("maxTokens", 1200),
    mlxTemperature: mlxNumberOption("temperature", 0.7),
    mlxTopP: mlxNumberOption("topP", 0.9),
    mlxTopK: mlxNumberOption("topK", 50),
    mlxRepetitionPenalty: mlxNumberOption("repetitionPenalty", 1.1),
    mlxExaggeration: mlxNumberOption("exaggeration", 0.5),
    mlxCfgWeight: mlxNumberOption("cfgWeight", 0.5),
    mlxMinP: mlxNumberOption("minP", 0.05),
    mlxSeed: mlxNumberOption("seed", 0),
    t3Model: $("#t3Model").value || "v2",
    audioPromptPath: $("#audioPromptPath").value.trim(),
    exaggeration: Number($("#exaggeration").value || 0.5),
    cfgWeight: Number($("#cfgWeight").value || 0.5),
    temperature: Number($("#temperature").value || 0.65),
    repetitionPenalty: Number($("#repetitionPenalty").value || 2.4),
    topP: Number($("#topP").value || 0.85),
    minP: Number($("#minP").value || 0.05),
    seed: Number($("#seed").value || 0),
    kokoroSpeed: Number($("#kokoroSpeed").value || 1),
    diaMaxNewTokens: Number($("#diaMaxNewTokens").value || 1280),
    diaGuidanceScale: Number($("#diaGuidanceScale").value || 3),
    diaTemperature: Number($("#diaTemperature").value || 1.8),
    diaTopP: Number($("#diaTopP").value || 0.9),
    diaTopK: Number($("#diaTopK").value || 50),
    diaSeed: Number($("#diaSeed").value || 0),
    diaAllowLowVram: $("#diaAllowLowVram").checked,
  };
}

function setResult(data) {
  audioPlayer.src = `${data.url}?t=${Date.now()}`;
  downloadLink.href = data.url;
  downloadLink.classList.remove("hidden");
  if (data.manifestUrl) {
    manifestLink.href = data.manifestUrl;
    manifestLink.classList.remove("hidden");
  } else {
    manifestLink.href = "#";
    manifestLink.classList.add("hidden");
  }
  resultMeta.textContent = `${data.fileName} / ${data.duration}s / ${data.utterances.length} lines`;
}

function switchMode(nextMode) {
  mode = nextMode;
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.mode === mode);
  });
  $("#singleMode").classList.toggle("hidden", mode !== "single");
  $("#scriptMode").classList.toggle("hidden", mode !== "script");
  $("#longformMode").classList.toggle("hidden", mode !== "longform");
  syncBackendUi();
}

function syncBackendUi() {
  const usingChatterbox = backend === "chatterbox";
  const usingKokoro = backend === "kokoro";
  const usingMlx = backend === "mlx";
  const usingDia = backendUsesDiaScript();
  if (usingDia && mode !== "script") {
    switchMode("script");
    return;
  }
  $("#chatterboxOptions").classList.toggle("hidden", !usingChatterbox);
  $("#kokoroOptions").classList.toggle("hidden", !usingKokoro);
  $("#diaOptions").classList.toggle("hidden", backend !== "dia");
  $("#mlxOptions").classList.toggle("hidden", !usingMlx);
  if (usingMlx) syncMlxSettingsVisibility();
  const showVoiceControls = shouldShowVoiceControls();
  const showSpeakerMap = shouldShowSpeakerMap();
  $("#singleVoiceButtons").closest(".field-row").classList.toggle("hidden", !showVoiceControls);
  $("#speakerMap").classList.toggle("hidden", !showSpeakerMap);
  $("#silenceMs").closest(".inline-options").classList.toggle("hidden", usingDia);
  document.querySelector('[data-mode="single"]').disabled = usingDia;
  document.querySelector('[data-mode="longform"]').disabled = usingDia;

  const maxSegmentChars = $("#maxSegmentChars");
  const segmentLimit = backendSegmentLimit();
  maxSegmentChars.max = String(segmentLimit);
  if (Number(maxSegmentChars.value || 0) > segmentLimit) {
    maxSegmentChars.value = String(segmentLimit);
  }
}

async function refreshStatus() {
  const data = await api("/api/status");
  backendMetadata = data.backends || {};
  if (backendMetadata.mlx?.defaultModelId && currentMlxCatalog()[backendMetadata.mlx.defaultModelId] && !currentMlxCatalog()[selectedMlxModelId]) {
    selectedMlxModelId = backendMetadata.mlx.defaultModelId;
  }
  renderMlxModelOptions();
  const chatterbox = backendMetadata.chatterbox;
  if (chatterbox?.languages) {
    renderLanguageOptions(chatterbox.languages, chatterbox.defaultLanguage || "ja");
  }
  $("#t3Model").closest("label").classList.toggle("hidden", chatterbox?.supportsT3Model === false);
  renderBackendButtons();
  renderVoiceButtons();
  renderSpeakerMap();

  if (backend === "chatterbox") {
    if (!chatterbox?.installed) {
      statusText.textContent = "Chatterbox未インストール";
      statusText.className = "status-warn";
      return;
    }
    if (chatterbox.filesReady === false) {
      statusText.textContent = "Chatterboxモデル未ダウンロード";
      statusText.className = "status-warn";
      return;
    }
    statusText.textContent = chatterbox.loaded
      ? `Chatterbox OK / ${chatterbox.device}`
      : `Chatterbox準備OK / ${chatterbox.device}`;
    statusText.className = "status-ok";
    return;
  }

  if (backend === "kokoro") {
    const kokoro = backendMetadata.kokoro;
    if (!kokoro?.installed) {
      statusText.textContent = "Kokoro未インストール";
      statusText.className = "status-warn";
      return;
    }
    statusText.textContent = `Kokoro OK / ${kokoro.device} / ${kokoro.voices?.length || 0} voices`;
    statusText.className = "status-ok";
    return;
  }

  if (backend === "piper") {
    const piper = backendMetadata.piper;
    if (!piper?.installed) {
      statusText.textContent = "Piper未インストール";
      statusText.className = "status-warn";
      return;
    }
    const count = piper.installedVoices?.length || 0;
    statusText.textContent = count
      ? `Piper OK / ${count} voices`
      : "Piper本体OK / voice未ダウンロード";
    statusText.className = count ? "status-ok" : "status-warn";
    return;
  }

  if (backend === "dia") {
    const dia = backendMetadata.dia;
    if (!dia?.installed) {
      statusText.textContent = "Dia未インストール";
      statusText.className = "status-warn";
      return;
    }
    if (dia.filesReady === false) {
      statusText.textContent = "Diaモデル未ダウンロード";
      statusText.className = "status-warn";
      return;
    }
    if (dia.warning) {
      statusText.textContent = `Dia実験枠 / ${dia.device} / VRAM ${dia.vramGb}GBは非推奨`;
      statusText.className = "status-warn";
      return;
    }
    statusText.textContent = dia.loaded ? `Dia OK / ${dia.device}` : `Dia準備OK / ${dia.device}`;
    statusText.className = dia.device === "cpu" ? "status-warn" : "status-ok";
    return;
  }

  if (backend === "mlx") {
    const mlx = backendMetadata.mlx;
    const model = currentMlxModel();
    if (!mlx?.installed) {
      statusText.textContent = "MLX-Audio未インストール";
      statusText.className = "status-warn";
      return;
    }
    if (!model?.installed) {
      statusText.textContent = `${model?.name || "MLXモデル"} 未ダウンロード`;
      statusText.className = "status-warn";
      return;
    }
    statusText.textContent = `MLX-Audio OK / ${model.name}`;
    statusText.className = "status-ok";
    return;
  }

  const server = data.serverRunning ? "Server OK" : "Server停止中";
  const model = data.modelLoaded ? "Model OK" : "Model未ロード";
  statusText.textContent = `${server} / ${model}`;
  statusText.className = data.serverRunning && data.modelLoaded ? "status-ok" : "status-warn";
}

async function ensureReady() {
  setBusy(true);
  try {
    log(backend === "orpheus" ? "LM StudioとOrpheusモデルを確認中" : `${backendLabel()}モデルを確認中`);
    const data = await api("/api/ensure", backendOptions());
    await refreshStatus();
    await refreshModels();
    log(data.steps?.length ? "起動またはロードを実行しました" : "準備済みです");
  } finally {
    setBusy(false);
  }
}

async function restartApp() {
  if (!window.confirm("アプリを再起動します。実行中の生成は停止します。")) return;

  appControlInProgress = true;
  setBusy(true);
  setOutputState("ready");
  statusText.textContent = "アプリ再起動中";
  statusText.className = "status-warn";
  log("アプリを再起動しています");

  try {
    await api("/api/restart", {});
  } catch (error) {
    log(`再起動要求後に接続が切れました: ${error.message}`);
  }

  if (await waitForRestart()) {
    log("再起動完了。画面を更新します");
    window.location.reload();
    return;
  }

  appControlInProgress = false;
  statusText.textContent = "再起動後の接続確認に失敗";
  statusText.className = "status-error";
  log("ERROR: 再起動後のアプリに接続できませんでした");
  setBusy(false);
}

async function stopApp() {
  if (!window.confirm("アプリを停止します。実行中の生成は停止します。")) return;

  appControlInProgress = true;
  setBusy(true);
  setOutputState("ready");
  statusText.textContent = "アプリ停止中";
  statusText.className = "status-warn";
  log("アプリを停止しています");

  try {
    await api("/api/shutdown", {});
  } catch (error) {
    log(`停止要求後に接続が切れました: ${error.message}`);
  }

  statusText.textContent = "アプリ停止済み";
  statusText.className = "status-warn";
  log("停止しました。再開するにはターミナルや起動スクリプトから起動してください");
}

async function generateSingle() {
  const text = $("#singleText").value.trim();
  if (!text) return log("単発テキストが空です");

  setBusy(true);
  setOutputState("running");
  try {
    const options = backendOptions();
    const voice = isVoiceBackend() ? currentSingleVoice() : "";
    log(isVoiceBackend() ? `単発生成: ${backendLabel()} ${voice}` : `単発生成: ${backendLabel()}`);
    const data = await api("/api/generate-single", { ...options, text, voice });
    setResult(data);
    setOutputState("done");
    log(`生成完了: ${data.fileName}`);
  } catch (error) {
    setOutputState("ready");
    log(`ERROR: ${error.message}`);
  } finally {
    setBusy(false);
    refreshStatus().catch(() => {});
    refreshModels().catch(() => {});
  }
}

async function generateScript() {
  const script = $("#scriptText").value.trim();
  if (!script) return log("台本が空です");

  setBusy(true);
  setOutputState("running");
  try {
    const options = backendOptions();
    log(`台本生成: ${backendLabel()}`);
    const data = await api("/api/generate-script", {
      ...options,
      script,
      speakerMap: speakerMap(),
      silenceMs: Number($("#silenceMs").value || 250),
    });
    setResult(data);
    setOutputState("done");
    log(`生成完了: ${data.fileName}`);
  } catch (error) {
    setOutputState("ready");
    log(`ERROR: ${error.message}`);
  } finally {
    setBusy(false);
    refreshStatus().catch(() => {});
    refreshModels().catch(() => {});
  }
}

async function generateLongform() {
  const text = $("#longformText").value.trim();
  if (!text) return log("長文テキストが空です");
  if (backendUsesDiaScript()) return log("ERROR: Dia系モデルは長文ナレーションに対応していません");
  if (backend === "mlx" && currentMlxModel()?.supportsLongform === false) {
    return log("ERROR: 選択中のMLXモデルは長文ナレーションに対応していません");
  }

  setBusy(true);
  setOutputState("running");
  try {
    const options = backendOptions();
    const voice = isVoiceBackend() ? currentSingleVoice() : "";
    log(isVoiceBackend() ? `長文生成: ${backendLabel()} ${voice}` : `長文生成: ${backendLabel()}`);
    const data = await api("/api/generate-longform", {
      ...options,
      title: $("#articleTitle").value.trim(),
      text,
      voice,
      speakerMap: speakerMap(),
      maxSegmentChars: Number($("#maxSegmentChars").value || backendSegmentLimit()),
      silenceMs: Number($("#longformSilenceMs").value || 450),
    });
    setResult(data);
    setOutputState("done");
    log(`生成完了: ${data.fileName}`);
    if (data.manifestFileName) log(`manifest作成: ${data.manifestFileName}`);
  } catch (error) {
    setOutputState("ready");
    log(`ERROR: ${error.message}`);
  } finally {
    setBusy(false);
    refreshStatus().catch(() => {});
    refreshModels().catch(() => {});
  }
}

function addLine() {
  const input = $("#lineText");
  const text = input.value.trim();
  if (!text) return;

  const textarea = $("#scriptText");
  const prefix = textarea.value.trim() ? "\n" : "";
  const line = backendUsesDiaScript() ? `[${activeSpeaker}] ${text}` : `${activeSpeaker}: ${text}`;
  textarea.value += `${prefix}${line}`;
  input.value = "";
  input.focus();
}

function bindEvents() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => switchMode(tab.dataset.mode));
  });
  $("#ensureButton").addEventListener("click", () => ensureReady().catch((error) => log(`ERROR: ${error.message}`)));
  $("#restartAppButton").addEventListener("click", () => restartApp().catch((error) => log(`ERROR: ${error.message}`)));
  $("#stopAppButton").addEventListener("click", () => stopApp().catch((error) => log(`ERROR: ${error.message}`)));
  $("#generateSingleButton").addEventListener("click", generateSingle);
  $("#generateScriptButton").addEventListener("click", generateScript);
  $("#generateLongformButton").addEventListener("click", generateLongform);
  $("#addLineButton").addEventListener("click", addLine);
  $("#mlxModelId")?.addEventListener("change", (event) => {
    const wasDiaStyle = backendUsesDiaScript();
    selectedMlxModelId = event.target.value;
    const isDiaStyle = backendUsesDiaScript();
    if (backend === "mlx" && wasDiaStyle !== isDiaStyle) {
      formatScriptForBackend("mlx", wasDiaStyle ? "dia" : "mlx");
    }
    renderMlxLanguageOptions(true);
    syncMlxSettingsVisibility({ resetValues: true });
    renderVoiceButtons();
    renderSpeakerMap();
    renderSpeakerButtons();
    syncBackendUi();
    refreshModels().catch(() => {});
  });
  $("#lineText").addEventListener("keydown", (event) => {
    if (event.key === "Enter") addLine();
  });
}

renderBackendButtons();
renderLanguageOptions();
renderVoiceButtons();
renderSpeakerMap();
renderSpeakerButtons();
bindEvents();
syncBackendUi();
refreshStatus().catch((error) => {
  statusText.textContent = "Status取得失敗";
  statusText.className = "status-error";
  log(`ERROR: ${error.message}`);
});
refreshModels().catch((error) => {
  modelSummary.textContent = "モデル確認失敗";
  log(`ERROR: ${error.message}`);
});
