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
};
const fallbackDefaultVoice = {
  orpheus: "tara",
  kokoro: "af_heart",
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
};
const speakers = ["A", "B", "C", "D", "E", "F"];
const backends = [
  { id: "orpheus", label: "Orpheus" },
  { id: "chatterbox", label: "Chatterbox Multilingual" },
  { id: "kokoro", label: "Kokoro (英語推奨)" },
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
  "[S2] On this GPU, Kokoro is still the safer model for everyday English TTS.",
].join("\n");

let mode = "single";
let backend = "kokoro";
let backendMetadata = {};
let selectedVoiceByBackend = { ...fallbackDefaultVoice };
let activeSpeaker = "A";

const $ = (selector) => document.querySelector(selector);
const statusText = $("#statusText");
const logBox = $("#log");
const audioPlayer = $("#audioPlayer");
const downloadLink = $("#downloadLink");
const resultMeta = $("#resultMeta");
const outputState = $("#outputState");
const outputStateLabel = $("#outputStateLabel");
const outputElapsed = $("#outputElapsed");
let outputTimerId = null;
let outputStartedAt = 0;

function log(message) {
  const time = new Date().toLocaleTimeString();
  logBox.textContent += `[${time}] ${message}\n`;
  logBox.scrollTop = logBox.scrollHeight;
}

function setBusy(isBusy) {
  document.querySelectorAll("button, textarea, input, select").forEach((element) => {
    element.disabled = isBusy;
  });
  if (!isBusy) syncBackendUi();
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

function backendLabel() {
  return backends.find((item) => item.id === backend)?.label || backend;
}

function formatScriptForBackend(nextBackend, previousBackend) {
  const textarea = $("#scriptText");
  const current = textarea.value;
  const converted = nextBackend === "dia" ? toDiaScript(current) : toLetterScript(current);
  if (converted !== current) {
    textarea.value = converted;
    const style = nextBackend === "dia" ? "[S1]/[S2]" : "A:/B:";
    log(`台本形式を${style}に変換しました`);
  }

  if (nextBackend === "dia") {
    activeSpeaker = "S1";
  } else if (previousBackend === "dia") {
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

function isVoiceBackend() {
  return backend === "orpheus" || backend === "kokoro";
}

function currentVoices() {
  const metadataVoices = backendMetadata[backend]?.voices;
  if (Array.isArray(metadataVoices) && metadataVoices.length) return metadataVoices;
  return fallbackVoiceCatalog[backend] || [];
}

function currentDefaultVoice() {
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

function renderBackendButtons() {
  const container = $("#backendButtons");
  container.innerHTML = "";
  backends.forEach((item) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `backend-button ${item.id === backend ? "active" : ""}`;
    button.textContent = item.label;
    button.addEventListener("click", () => {
      const previousBackend = backend;
      formatScriptForBackend(item.id, previousBackend);
      backend = item.id;
      applyBackendSample(previousBackend);
      if (backend === "dia") {
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
  if (backend !== "dia" || previousBackend === "dia") return;

  const singleText = $("#singleText");
  const scriptText = $("#scriptText");
  if (singleText.value.trim() === defaultSingleText) {
    singleText.value = diaSingleSample;
  }
  if (!scriptText.value.trim()) {
    scriptText.value = diaScriptSample;
  }
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

function renderSpeakerMap() {
  const map = $("#speakerMap");
  map.innerHTML = "";
  const voices = currentVoices();
  const defaults = defaultSpeakerMaps[backend] || {};
  speakers.forEach((speaker) => {
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
      if (voice === (defaults[speaker] || currentDefaultVoice())) option.selected = true;
      select.appendChild(option);
    });

    card.append(label, select);
    map.appendChild(card);
  });
}

function renderSpeakerButtons() {
  const container = $("#speakerButtons");
  container.innerHTML = "";
  const visibleSpeakers = backend === "dia" ? ["S1", "S2"] : speakers.slice(0, 3);
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
  const values = {};
  document.querySelectorAll("#speakerMap select").forEach((select) => {
    values[select.dataset.speaker] = select.value;
  });
  return values;
}

function backendOptions() {
  return {
    backend,
    languageId: $("#languageId").value || "ja",
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
  resultMeta.textContent = `${data.fileName} / ${data.duration}s / ${data.utterances.length} lines`;
}

function switchMode(nextMode) {
  mode = nextMode;
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.mode === mode);
  });
  $("#singleMode").classList.toggle("hidden", mode !== "single");
  $("#scriptMode").classList.toggle("hidden", mode !== "script");
  syncBackendUi();
}

function syncBackendUi() {
  const usingChatterbox = backend === "chatterbox";
  const usingKokoro = backend === "kokoro";
  const usingDia = backend === "dia";
  if (usingDia && mode !== "script") {
    switchMode("script");
    return;
  }
  $("#chatterboxOptions").classList.toggle("hidden", !usingChatterbox);
  $("#kokoroOptions").classList.toggle("hidden", !usingKokoro);
  $("#diaOptions").classList.toggle("hidden", !usingDia);
  $("#singleVoiceButtons").closest(".field-row").classList.toggle("hidden", !isVoiceBackend());
  $("#speakerMap").classList.toggle("hidden", !isVoiceBackend());
  $("#silenceMs").closest(".inline-options").classList.toggle("hidden", usingDia);
  document.querySelector('[data-mode="single"]').disabled = usingDia;
}

async function refreshStatus() {
  const data = await api("/api/status");
  backendMetadata = data.backends || {};
  const chatterbox = backendMetadata.chatterbox;
  if (chatterbox?.languages) {
    renderLanguageOptions(chatterbox.languages, chatterbox.defaultLanguage || "ja");
  }
  $("#t3Model").closest("label").classList.toggle("hidden", chatterbox?.supportsT3Model === false);
  renderVoiceButtons();
  renderSpeakerMap();

  if (backend === "chatterbox") {
    if (!chatterbox?.installed) {
      statusText.textContent = "Chatterbox未インストール";
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

  if (backend === "dia") {
    const dia = backendMetadata.dia;
    if (!dia?.installed) {
      statusText.textContent = "Dia未インストール";
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
    log(data.steps?.length ? "起動またはロードを実行しました" : "準備済みです");
  } finally {
    setBusy(false);
  }
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
  }
}

function addLine() {
  const input = $("#lineText");
  const text = input.value.trim();
  if (!text) return;

  const textarea = $("#scriptText");
  const prefix = textarea.value.trim() ? "\n" : "";
  const line = backend === "dia" ? `[${activeSpeaker}] ${text}` : `${activeSpeaker}: ${text}`;
  textarea.value += `${prefix}${line}`;
  input.value = "";
  input.focus();
}

function bindEvents() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => switchMode(tab.dataset.mode));
  });
  $("#ensureButton").addEventListener("click", () => ensureReady().catch((error) => log(`ERROR: ${error.message}`)));
  $("#generateSingleButton").addEventListener("click", generateSingle);
  $("#generateScriptButton").addEventListener("click", generateScript);
  $("#addLineButton").addEventListener("click", addLine);
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
