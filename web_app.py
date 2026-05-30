import argparse
import json
import mimetypes
import os
import re
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import chatterbox_backend
import dia_backend
import kokoro_backend
from gguf_orpheus import AVAILABLE_VOICES, DEFAULT_VOICE, SAMPLE_RATE, generate_speech_from_api
from multi_speaker_tts import write_combined_wav


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
OUTPUT_DIR = ROOT / "outputs" / "web"
LOG_DIR = ROOT / "logs"
MODEL_KEY = "orpheus-3b-0.1-ft"
LMSTUDIO_BASE_URL = "http://127.0.0.1:1234"
BACKEND_ORPHEUS = "orpheus"
BACKEND_CHATTERBOX = "chatterbox"
BACKEND_KOKORO = "kokoro"
BACKEND_DIA = "dia"
BACKENDS = {BACKEND_ORPHEUS, BACKEND_CHATTERBOX, BACKEND_KOKORO, BACKEND_DIA}
SPEAKER_PATTERN = re.compile(r"^\s*(?P<label>[A-Za-z0-9_-]+)\s*[:：]\s*(?P<text>.+?)\s*$")
generation_lock = threading.Lock()


def ensure_stdio():
    if sys.stdout is not None and sys.stderr is not None:
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = open(LOG_DIR / "web_app.log", "a", encoding="utf-8", buffering=1)
    if sys.stdout is None:
        sys.stdout = log_file
    if sys.stderr is None:
        sys.stderr = log_file


def hidden_subprocess_kwargs():
    if os.name != "nt":
        return {}

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return {
        "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0),
        "startupinfo": startupinfo,
    }


def run_lms(*args):
    try:
        result = subprocess.run(
            ["lms", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            **hidden_subprocess_kwargs(),
        )
    except FileNotFoundError:
        return {"ok": False, "exit_code": 127, "text": "lms command was not found."}

    text = "\n".join(part for part in [result.stdout, result.stderr] if part).strip()
    return {"ok": result.returncode == 0, "exit_code": result.returncode, "text": text}


def get_lmstudio_models_http():
    try:
        with urllib.request.urlopen(f"{LMSTUDIO_BASE_URL}/v1/models", timeout=1.5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {
            "serverRunning": False,
            "modelLoaded": False,
            "serverText": str(exc),
            "modelsText": "",
        }

    model_ids = [
        str(item.get("id", ""))
        for item in payload.get("data", [])
        if isinstance(item, dict)
    ]
    return {
        "serverRunning": True,
        "modelLoaded": MODEL_KEY in model_ids,
        "serverText": f"LM Studio server responded at {LMSTUDIO_BASE_URL}.",
        "modelsText": "\n".join(model_ids),
    }


def get_lmstudio_status():
    status = get_lmstudio_models_http()
    return {
        "serverRunning": status["serverRunning"],
        "modelLoaded": status["modelLoaded"],
        "modelKey": MODEL_KEY,
        "voices": AVAILABLE_VOICES,
        "defaultVoice": DEFAULT_VOICE,
        "serverText": status["serverText"],
        "modelsText": status["modelsText"],
    }


def get_app_status():
    orpheus = get_lmstudio_status()
    chatterbox = chatterbox_backend.dependency_status()
    kokoro = kokoro_backend.dependency_status()
    dia = dia_backend.dependency_status()
    return {
        **orpheus,
        "backends": {
            BACKEND_ORPHEUS: {
                **orpheus,
                "name": "Orpheus",
                "kind": "lmstudio",
                "ready": orpheus["serverRunning"] and orpheus["modelLoaded"],
            },
            BACKEND_CHATTERBOX: {
                **chatterbox,
                "name": "Chatterbox Multilingual",
                "kind": "local",
                "ready": chatterbox["installed"],
            },
            BACKEND_KOKORO: {
                **kokoro,
                "name": "Kokoro",
                "kind": "local-process",
                "ready": kokoro["installed"],
            },
            BACKEND_DIA: {
                **dia,
                "name": "Dia",
                "kind": "local",
                "ready": dia["installed"] and dia["device"] != "cpu" and dia.get("recommended", True),
            },
        },
    }


def ensure_lmstudio():
    steps = []
    status = get_lmstudio_status()

    if not status["serverRunning"]:
        started = run_lms("server", "start", "--port", "1234")
        steps.append({"step": "server start", **started})
        if not started["ok"]:
            return {"ok": False, "steps": steps, "status": get_lmstudio_status()}

    status = get_lmstudio_status()
    if not status["modelLoaded"]:
        loaded = run_lms("load", MODEL_KEY, "--identifier", MODEL_KEY, "-y")
        steps.append({"step": "model load", **loaded})
        if not loaded["ok"]:
            return {"ok": False, "steps": steps, "status": get_lmstudio_status()}

    return {"ok": True, "steps": steps, "status": get_lmstudio_status()}


def safe_backend(value):
    backend = (value or BACKEND_ORPHEUS).strip().lower()
    if backend not in BACKENDS:
        raise ValueError(f"Unknown backend: {backend}")
    return backend


def ensure_backend(payload):
    backend = safe_backend((payload or {}).get("backend"))
    release_inactive_backends(backend)
    if backend == BACKEND_CHATTERBOX:
        return chatterbox_backend.ensure_model(payload or {})
    if backend == BACKEND_KOKORO:
        return kokoro_backend.ensure_model(payload or {})
    if backend == BACKEND_DIA:
        return dia_backend.ensure_model(payload or {})
    return ensure_lmstudio()


def release_inactive_backends(active_backend):
    if active_backend != BACKEND_CHATTERBOX:
        chatterbox_backend.unload_model()
    if active_backend != BACKEND_DIA:
        dia_backend.unload_model()
    if active_backend != BACKEND_KOKORO:
        kokoro_backend.unload_model()


def safe_voice(value):
    voice = (value or DEFAULT_VOICE).strip().lower()
    if voice not in AVAILABLE_VOICES:
        raise ValueError(f"Unknown voice: {voice}")
    return voice


def safe_kokoro_voice(value):
    return kokoro_backend.safe_voice(value)


def output_path(prefix):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    counter = 0
    while True:
        suffix = f"-{counter}" if counter else ""
        path = OUTPUT_DIR / f"{prefix}-{stamp}{suffix}.wav"
        if not path.exists():
            return path
        counter += 1


def write_pcm16_wav(output_file, audio_chunks, sample_rate, silence_ms=0):
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    silence_frames = int(sample_rate * silence_ms / 1000)
    silence = b"\x00\x00" * silence_frames

    with wave.open(str(output_file), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)

        for index, chunk in enumerate(audio_chunks):
            wav_file.writeframes(chunk)
            if index != len(audio_chunks) - 1 and silence:
                wav_file.writeframes(silence)


def audio_duration(path):
    with wave.open(str(path), "rb") as wav_file:
        return wav_file.getnframes() / wav_file.getframerate()


def parse_script(script_text, speaker_map):
    utterances = []
    normalized_map = {
        str(label).strip().upper(): safe_voice(voice)
        for label, voice in (speaker_map or {}).items()
        if str(label).strip()
    }

    for line_number, line in enumerate((script_text or "").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        match = SPEAKER_PATTERN.match(line)
        if not match:
            raise ValueError(f"Line {line_number}: use 'A: text' or 'tara: text'.")

        label = match.group("label").strip()
        voice = normalized_map.get(label.upper())
        if voice is None and label.lower() in AVAILABLE_VOICES:
            voice = label.lower()
        if voice is None:
            raise ValueError(f"Line {line_number}: speaker '{label}' has no assigned voice.")

        utterances.append(
            {
                "label": label,
                "voice": voice,
                "text": match.group("text").strip(),
                "lineNumber": line_number,
            }
        )

    if not utterances:
        raise ValueError("Script has no lines to generate.")

    return utterances


def parse_chatterbox_script(script_text):
    utterances = []

    for line_number, line in enumerate((script_text or "").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        match = SPEAKER_PATTERN.match(line)
        if not match:
            raise ValueError(f"Line {line_number}: use 'A: text'.")

        utterances.append(
            {
                "label": match.group("label").strip(),
                "voice": "chatterbox",
                "text": match.group("text").strip(),
                "lineNumber": line_number,
            }
        )

    if not utterances:
        raise ValueError("Script has no lines to generate.")

    return utterances


def parse_kokoro_script(script_text, speaker_map):
    utterances = []
    normalized_map = {
        str(label).strip().upper(): safe_kokoro_voice(voice)
        for label, voice in (speaker_map or {}).items()
        if str(label).strip()
    }

    for line_number, line in enumerate((script_text or "").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        match = SPEAKER_PATTERN.match(line)
        if not match:
            raise ValueError(f"Line {line_number}: use 'A: text' or a Kokoro voice label.")

        label = match.group("label").strip()
        voice = normalized_map.get(label.upper())
        if voice is None and label.lower() in kokoro_backend.AVAILABLE_VOICES:
            voice = label.lower()
        if voice is None:
            raise ValueError(f"Line {line_number}: speaker '{label}' has no assigned Kokoro voice.")

        utterances.append(
            {
                "label": label,
                "voice": voice,
                "text": match.group("text").strip(),
                "lineNumber": line_number,
            }
        )

    if not utterances:
        raise ValueError("Script has no lines to generate.")

    return utterances


def generate_single(payload):
    backend = safe_backend(payload.get("backend"))
    text = (payload.get("text") or "").strip()
    if not text:
        raise ValueError("Text is empty.")

    if backend == BACKEND_CHATTERBOX:
        language_id = chatterbox_backend.safe_language(payload.get("languageId"))
        out_path = output_path(f"single-chatterbox-{language_id}")
        sample_rate, audio = chatterbox_backend.generate_waveform(text, payload)
        write_pcm16_wav(out_path, [audio], sample_rate)
        return audio_result(
            out_path,
            [{"label": "chatterbox", "voice": "chatterbox", "text": text}],
        )

    if backend == BACKEND_KOKORO:
        voice = safe_kokoro_voice(payload.get("voice"))
        out_path = output_path(f"single-kokoro-{voice}")
        kokoro_backend.generate_to_file([{"voice": voice, "text": text}], out_path, payload)
        return audio_result(out_path, [{"label": voice, "voice": voice, "text": text}])

    if backend == BACKEND_DIA:
        out_path = output_path("single-dia")
        dia_backend.generate_to_file(dia_backend.single_text(text), out_path, payload)
        return audio_result(out_path, [{"label": "S1", "voice": "dia", "text": text}])

    voice = safe_voice(payload.get("voice"))
    out_path = output_path(f"single-{voice}")
    chunks = generate_speech_from_api(text, voice=voice, output_file=str(out_path))
    if not chunks:
        raise RuntimeError("No audio was generated.")

    return audio_result(out_path, [{"label": voice, "voice": voice, "text": text}])


def generate_script(payload):
    backend = safe_backend(payload.get("backend"))
    silence_ms = max(0, min(int(payload.get("silenceMs") or 250), 5000))

    if backend == BACKEND_CHATTERBOX:
        language_id = chatterbox_backend.safe_language(payload.get("languageId"))
        utterances = parse_chatterbox_script(payload.get("script") or "")
        out_path = output_path(f"script-chatterbox-{language_id}")
        all_audio = []
        sample_rate = None

        for utterance in utterances:
            sample_rate, audio = chatterbox_backend.generate_waveform(utterance["text"], payload)
            all_audio.append(audio)

        write_pcm16_wav(str(out_path), all_audio, sample_rate, silence_ms)
        return audio_result(out_path, utterances)

    if backend == BACKEND_KOKORO:
        utterances = parse_kokoro_script(payload.get("script") or "", payload.get("speakerMap") or {})
        out_path = output_path("script-kokoro")
        kokoro_backend.generate_to_file(utterances, out_path, payload, silence_ms)
        return audio_result(out_path, utterances)

    if backend == BACKEND_DIA:
        dia_text = dia_backend.script_to_dialogue(payload.get("script") or "", SPEAKER_PATTERN)
        out_path = output_path("script-dia")
        dia_backend.generate_to_file(dia_text, out_path, payload)
        return audio_result(
            out_path,
            [{"label": "dia", "voice": "dia", "text": dia_text}],
        )

    utterances = parse_script(payload.get("script") or "", payload.get("speakerMap") or {})
    out_path = output_path("script")
    all_audio = []

    for utterance in utterances:
        chunks = generate_speech_from_api(utterance["text"], voice=utterance["voice"])
        if not chunks:
            raise RuntimeError(
                f"No audio generated for line {utterance['lineNumber']} ({utterance['label']})."
            )
        all_audio.append(chunks)

    write_combined_wav(str(out_path), all_audio, silence_ms)
    return audio_result(out_path, utterances)


def audio_result(path, utterances):
    return {
        "fileName": path.name,
        "url": f"/generated/{urllib.parse.quote(path.name)}",
        "duration": round(audio_duration(path), 2),
        "utterances": utterances,
    }


def app_is_running(url):
    try:
        with urllib.request.urlopen(f"{url}/api/status", timeout=1.0) as response:
            return response.status == 200
    except Exception:
        return False


def open_url(url):
    if os.name == "nt":
        subprocess.Popen(
            ["cmd.exe", "/d", "/c", "start", "", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            **hidden_subprocess_kwargs(),
        )
    else:
        webbrowser.open(url)


class AppHandler(BaseHTTPRequestHandler):
    server_version = "UltraTTSWeb/1.0"

    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            self.send_json({"ok": True, **get_app_status()})
            return

        if path.startswith("/generated/"):
            self.send_generated(path.removeprefix("/generated/"))
            return

        if path == "/":
            path = "/index.html"

        self.send_static(path)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        try:
            payload = self.read_json()
            if parsed.path == "/api/ensure":
                result = ensure_backend(payload)
                self.send_json(result, 200 if result["ok"] else 500)
                return

            if parsed.path == "/api/generate-single":
                self.ensure_before_generate(payload)
                with generation_lock:
                    self.send_json({"ok": True, **generate_single(payload)})
                return

            if parsed.path == "/api/generate-script":
                self.ensure_before_generate(payload)
                with generation_lock:
                    self.send_json({"ok": True, **generate_script(payload)})
                return

            self.send_json({"ok": False, "error": "Not found."}, 404)
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, 500)

    def ensure_before_generate(self, payload):
        backend = safe_backend(payload.get("backend"))
        release_inactive_backends(backend)

        if backend == BACKEND_CHATTERBOX:
            status = chatterbox_backend.dependency_status()
            if not status["installed"]:
                raise RuntimeError(f"Chatterbox is not installed: {status['error']}")
            return

        if backend == BACKEND_KOKORO:
            status = kokoro_backend.dependency_status()
            if not status["installed"]:
                raise RuntimeError(f"Kokoro is not installed: {status['error']}")
            return

        if backend == BACKEND_DIA:
            status = dia_backend.dependency_status()
            if not status["installed"]:
                raise RuntimeError(f"Dia is not installed: {status['error']}")
            if status["device"] == "cpu":
                raise RuntimeError("Dia needs a CUDA or MPS GPU for practical local generation.")
            if status.get("recommended") is False and not payload.get("diaAllowLowVram"):
                raise RuntimeError(
                    "Dia needs about 10GB VRAM for practical local use. "
                    f"This GPU has {status.get('vramGb')}GB, so output can become broken audio. "
                    "Use Kokoro for English, or enable the low-VRAM Dia option if you still want to test it."
                )
            return

        result = ensure_lmstudio()
        if not result["ok"]:
            raise RuntimeError("LM Studio server or Orpheus model could not be started.")

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_static(self, request_path):
        relative = request_path.lstrip("/")
        target = (WEB_ROOT / relative).resolve()
        if not str(target).startswith(str(WEB_ROOT.resolve())) or not target.is_file():
            self.send_error(404)
            return

        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_generated(self, encoded_name):
        name = urllib.parse.unquote(encoded_name)
        target = (OUTPUT_DIR / name).resolve()
        if not str(target).startswith(str(OUTPUT_DIR.resolve())) or not target.is_file():
            self.send_error(404)
            return

        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Disposition", f'attachment; filename="{target.name}"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    ensure_stdio()
    parser = argparse.ArgumentParser(description="Local Ultra-TTS web app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true", help="Open the app in the default browser")
    args = parser.parse_args()

    url = f"http://{args.host}:{args.port}"
    if app_is_running(url):
        print(f"Ultra-TTS Web is already running at {url}")
        if args.open:
            open_url(url)
        return 0

    server = ThreadingHTTPServer((args.host, args.port), AppHandler)
    print(f"Ultra-TTS Web is running at {url}")
    print("Close this window to stop the web app.")

    if args.open:
        threading.Timer(0.4, lambda: open_url(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping Ultra-TTS Web.")
    finally:
        server.server_close()


if __name__ == "__main__":
    sys.exit(main())
