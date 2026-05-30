from pathlib import Path

import local_paths


local_paths.configure_local_model_env()


MODEL_DETAILS = {
    "piper": {
        "role": "軽量TTS",
        "summary": "ONNX音声を使う高速・安定枠。長文教材や一括生成に向いています。",
        "languages": ["English", "German", "French", "Spanish", "Chinese"],
        "strengths": ["高速", "CPU向き", "長文向き", "声追加が軽い"],
        "recommendedFor": ["教材読み上げ", "大量生成", "安定運用"],
        "limitations": ["声の表現幅はモデル依存", "日本語voiceは未導入"],
    },
    "orpheus": {
        "role": "TTS LLM",
        "summary": "LM Studio経由で使う音声トークン生成モデル。英語の表現豊かな短文に向いています。",
        "languages": ["English"],
        "strengths": ["表現豊か", "複数プリセット声", "LLM系"],
        "recommendedFor": ["英語セリフ", "短文サンプル", "声の雰囲気確認"],
        "limitations": ["LM Studioが必要", "長文は分割生成推奨"],
    },
    "snac": {
        "role": "音声デコーダ",
        "summary": "Orpheusが生成した音声トークンを24kHz音声へ戻す依存モデルです。",
        "languages": ["Audio codec"],
        "strengths": ["Orpheus用", "24kHz復号"],
        "recommendedFor": ["Orpheus生成"],
        "limitations": ["単体TTSではありません"],
    },
    "kokoro": {
        "role": "軽量ニューラルTTS",
        "summary": "英語向けの軽量モデル。CPUでも扱いやすく、英語長文の安定読み上げに向いています。",
        "languages": ["English US", "English UK"],
        "strengths": ["軽量", "CPU実行", "英語長文", "声が多い"],
        "recommendedFor": ["英語教材", "英語記事", "ナレーション下書き"],
        "limitations": ["日本語は非対応"],
    },
    "chatterbox": {
        "role": "多言語TTS",
        "summary": "日本語・英語を含む多言語生成の実用枠。参照音声で声質を寄せる用途にも使えます。",
        "languages": [
            "Arabic",
            "Danish",
            "German",
            "Greek",
            "English",
            "Spanish",
            "Finnish",
            "French",
            "Hebrew",
            "Hindi",
            "Italian",
            "Japanese",
            "Korean",
            "Malay",
            "Dutch",
            "Norwegian",
            "Polish",
            "Portuguese",
            "Russian",
            "Swedish",
            "Swahili",
            "Turkish",
            "Chinese",
        ],
        "strengths": ["日本語", "英語", "多言語", "参照音声"],
        "recommendedFor": ["日本語短文", "多言語教材", "声質合わせ"],
        "limitations": ["1セグメントは短めに分割", "初回ロードが重い"],
    },
    "dia": {
        "role": "会話TTS",
        "summary": "英語2話者の会話生成向け。台本形式の掛け合いに強い実験枠です。",
        "languages": ["English"],
        "strengths": ["2話者会話", "自然な掛け合い", "英語ダイアログ"],
        "recommendedFor": ["英会話教材", "対話サンプル"],
        "limitations": ["日本語非対応", "長文ナレーション非対応", "初回生成が重い"],
    },
    "dia-dac": {
        "role": "音声トークナイザ",
        "summary": "Diaが音声を復号するためのDAC依存モデルです。",
        "languages": ["Audio codec"],
        "strengths": ["Dia用", "44.1kHz codec"],
        "recommendedFor": ["Dia生成"],
        "limitations": ["単体TTSではありません"],
    },
    "mlx-chatterbox": {
        "role": "MLX多言語TTS",
        "summary": "Apple Silicon向けMLX版Chatterbox。日本語・英語・参照音声の本命候補です。",
        "languages": ["Japanese", "English", "Chinese", "Korean", "French", "German", "Spanish", "Italian", "Portuguese", "Russian", "Arabic"],
        "strengths": ["Mac M4向き", "日本語", "英語", "voice cloning", "約2.6GB"],
        "recommendedFor": ["日本語教材", "多言語短文", "参照音声で声質合わせ"],
        "limitations": ["長文は分割生成", "参照音声は許可済み音声だけ使用"],
    },
    "mlx-qwen3-tts": {
        "role": "MLX TTS LLM",
        "summary": "Qwen3-TTS BaseのMLX 8bit版。日本語・英語のプリセット声と参照音声を試す候補です。",
        "languages": ["Japanese", "English", "Chinese", "Korean", "German", "French", "Russian", "Portuguese", "Spanish", "Italian"],
        "strengths": ["Mac M4向き", "TTS LLM", "プリセット声", "voice cloning"],
        "recommendedFor": ["日本語サンプル", "英語サンプル", "表現違いの比較"],
        "limitations": ["参照音声cloningは参照テキストが必要", "声質指示はCustomVoice/VoiceDesignを使用", "長文は分割生成"],
    },
    "mlx-qwen3-custom": {
        "role": "MLX TTS LLM",
        "summary": "Qwen3-TTS CustomVoiceのMLX 8bit版。プリセット声に感情・スタイル指示を足す候補です。",
        "languages": ["Japanese", "English", "Chinese", "Korean", "German", "French", "Russian", "Portuguese", "Spanish", "Italian"],
        "strengths": ["Mac M4向き", "TTS LLM", "感情指示", "スタイル指示", "複数プリセット声"],
        "recommendedFor": ["声色比較", "感情付きセリフ", "日本語/英語サンプル"],
        "limitations": ["任意の声質設計はVoiceDesignを使用", "長文は分割生成", "初回ロードが重い"],
    },
    "mlx-qwen3-voice-design": {
        "role": "MLX TTS LLM",
        "summary": "Qwen3-TTS VoiceDesignのMLX 8bit版。自然言語で声質を設計する実験候補です。",
        "languages": ["Japanese", "English", "Chinese", "Korean", "German", "French", "Russian", "Portuguese", "Spanish", "Italian"],
        "strengths": ["Mac M4向き", "声質設計", "感情/韻律指示", "TTS LLM"],
        "recommendedFor": ["いろんな声の試作", "キャラ声の方向性確認", "ナレーション声設計"],
        "limitations": ["指示欄が必須", "生成結果は指示文に左右される", "長文は分割生成"],
    },
    "mlx-kokoro": {
        "role": "MLX軽量TTS",
        "summary": "KokoroのMLX 8bit版。軽量高速で、日本語voiceの動作確認にも使えます。",
        "languages": ["Japanese", "English US", "English UK"],
        "strengths": ["高速", "軽量", "日本語voice", "英語voice", "長文向き"],
        "recommendedFor": ["動作確認", "軽量読み上げ", "長文の下書き生成"],
        "limitations": ["voice cloningなし", "表現制御は控えめ"],
    },
    "mlx-dia": {
        "role": "MLX会話TTS",
        "summary": "DiaのMLX版。英語の[S1]/[S2] 2話者会話専用の実験枠です。",
        "languages": ["English"],
        "strengths": ["Mac M4向き", "2話者会話", "英語ダイアログ"],
        "recommendedFor": ["英会話教材", "掛け合いサンプル"],
        "limitations": ["日本語非対応", "長文ナレーション非対応", "台本形式は[S1]/[S2]"],
    },
}


HF_MODELS = {
    "orpheus": {
        "name": "Orpheus GGUF",
        "backend": "orpheus",
        "path": local_paths.MODELS_DIR
        / "huggingface"
        / "isaiahbjork__orpheus-3b-0.1-ft-Q4_K_M-GGUF",
        "requiredFiles": ["orpheus-3b-0.1-ft-q4_k_m.gguf"],
    },
    "snac": {
        "name": "SNAC 24kHz",
        "backend": "orpheus",
        "path": local_paths.MODELS_DIR / "huggingface" / "hubertsiuzdak__snac_24khz",
        "requiredFiles": ["config.json", "pytorch_model.bin"],
    },
    "kokoro": {
        "name": "Kokoro 82M",
        "backend": "kokoro",
        "path": local_paths.MODELS_DIR / "huggingface" / "hexgrad__Kokoro-82M",
        "requiredFiles": ["config.json", "kokoro-v1_0.pth"],
    },
    "chatterbox": {
        "name": "Chatterbox",
        "backend": "chatterbox",
        "path": local_paths.MODELS_DIR / "huggingface" / "ResembleAI__chatterbox",
        "requiredFiles": [
            "Cangjie5_TC.json",
            "conds.pt",
            "grapheme_mtl_merged_expanded_v1.json",
            "s3gen.pt",
            "t3_mtl23ls_v2.safetensors",
            "ve.pt",
        ],
    },
    "dia": {
        "name": "Dia 1.6B",
        "backend": "dia",
        "path": local_paths.MODELS_DIR / "huggingface" / "nari-labs__Dia-1.6B-0626",
        "requiredFiles": [
            "config.json",
            "model-00001-of-00002.safetensors",
            "model-00002-of-00002.safetensors",
            "preprocessor_config.json",
        ],
    },
    "dia-dac": {
        "name": "Dia DAC Audio Tokenizer",
        "backend": "dia",
        "path": local_paths.MODELS_DIR / "huggingface" / "descript__dac_44khz",
        "requiredFiles": [
            "config.json",
            "model.safetensors",
            "preprocessor_config.json",
        ],
    },
    "mlx-chatterbox": {
        "name": "Chatterbox MLX fp16",
        "backend": "mlx",
        "path": local_paths.MODELS_DIR / "huggingface" / "mlx-community__chatterbox-fp16",
        "requiredFiles": ["config.json", "tokenizer.json", "conds.safetensors"],
        "requiredGlobs": ["*.safetensors"],
    },
    "mlx-qwen3-tts": {
        "name": "Qwen3-TTS MLX Base 8bit (参照音声)",
        "backend": "mlx",
        "path": local_paths.MODELS_DIR
        / "huggingface"
        / "mlx-community__Qwen3-TTS-12Hz-1.7B-Base-8bit",
        "requiredFiles": ["config.json", "tokenizer_config.json", "speech_tokenizer/config.json"],
        "requiredGlobs": ["*.safetensors", "speech_tokenizer/*.safetensors"],
    },
    "mlx-qwen3-custom": {
        "name": "Qwen3-TTS MLX CustomVoice 8bit (プリセット声)",
        "backend": "mlx",
        "path": local_paths.MODELS_DIR
        / "huggingface"
        / "mlx-community__Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit",
        "requiredFiles": ["config.json", "tokenizer_config.json", "speech_tokenizer/config.json"],
        "requiredGlobs": ["*.safetensors", "speech_tokenizer/*.safetensors"],
    },
    "mlx-qwen3-voice-design": {
        "name": "Qwen3-TTS MLX VoiceDesign 8bit",
        "backend": "mlx",
        "path": local_paths.MODELS_DIR
        / "huggingface"
        / "mlx-community__Qwen3-TTS-12Hz-1.7B-VoiceDesign-8bit",
        "requiredFiles": ["config.json", "tokenizer_config.json", "speech_tokenizer/config.json"],
        "requiredGlobs": ["*.safetensors", "speech_tokenizer/*.safetensors"],
    },
    "mlx-kokoro": {
        "name": "Kokoro MLX 82M 8bit",
        "backend": "mlx",
        "path": local_paths.MODELS_DIR / "huggingface" / "mlx-community__Kokoro-82M-8bit",
        "requiredFiles": ["config.json", "kokoro-v1_0.safetensors", "voices/jf_alpha.safetensors"],
        "requiredGlobs": ["voices/*.safetensors"],
    },
    "mlx-dia": {
        "name": "Dia MLX 1.6B fp16",
        "backend": "mlx",
        "path": local_paths.MODELS_DIR / "huggingface" / "mlx-community__Dia-1.6B-fp16",
        "requiredFiles": ["config.json", "model.safetensors"],
        "requiredGlobs": ["*.safetensors"],
    },
}


def dir_size(path):
    path = Path(path)
    if not path.exists():
        return 0
    if path.is_file():
        try:
            return path.stat().st_size
        except OSError:
            return 0

    total = 0
    for item in path.rglob("*"):
        try:
            if item.is_file():
                total += item.stat().st_size
        except OSError:
            continue
    return total


def format_size(size):
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024


def required_files_present(path, files):
    path = Path(path)
    return all((path / filename).exists() for filename in files)


def required_globs_present(path, globs):
    path = Path(path)
    return all(any(path.glob(pattern)) for pattern in globs or [])


def is_installed(model_id):
    meta = HF_MODELS[model_id]
    return (
        meta["path"].exists()
        and required_files_present(meta["path"], meta["requiredFiles"])
        and required_globs_present(meta["path"], meta.get("requiredGlobs"))
    )


def piper_inventory():
    import piper_backend

    voices = []
    for voice_id, entry in piper_backend.VOICE_CATALOG.items():
        model_path = piper_backend.voice_model_path(voice_id)
        config_path = piper_backend.voice_config_path(voice_id)
        installed = model_path.exists() and config_path.exists()
        voices.append(
            {
                "id": voice_id,
                "name": entry["name"],
                "language": entry["language"],
                "installed": installed,
                "path": str(model_path.relative_to(local_paths.ROOT)),
                "size": dir_size(model_path) + dir_size(config_path),
                "sizeLabel": format_size(dir_size(model_path) + dir_size(config_path)),
            }
        )

    return {
        "id": "piper",
        "name": "Piper Voices",
        "backend": "piper",
        **MODEL_DETAILS["piper"],
        "path": str(local_paths.PIPER_MODELS_DIR.relative_to(local_paths.ROOT)),
        "installed": any(voice["installed"] for voice in voices),
        "voiceCount": sum(1 for voice in voices if voice["installed"]),
        "size": dir_size(local_paths.PIPER_MODELS_DIR),
        "sizeLabel": format_size(dir_size(local_paths.PIPER_MODELS_DIR)),
        "voices": voices,
    }


def hf_inventory_item(model_id, meta):
    path = meta["path"]
    installed = path.exists() and required_files_present(path, meta["requiredFiles"])
    installed = installed and required_globs_present(path, meta.get("requiredGlobs"))
    size = dir_size(path)
    missing_globs = [
        pattern
        for pattern in meta.get("requiredGlobs", [])
        if not any(path.glob(pattern))
    ]
    return {
        "id": model_id,
        "name": meta["name"],
        "backend": meta["backend"],
        **MODEL_DETAILS.get(model_id, {}),
        "path": str(path.relative_to(local_paths.ROOT)),
        "installed": installed,
        "size": size,
        "sizeLabel": format_size(size),
        "missingFiles": [
            filename
            for filename in meta["requiredFiles"]
            if not (path / filename).exists()
        ],
        "missingGlobs": missing_globs,
    }


def model_inventory():
    local_paths.ensure_local_dirs()
    models = [piper_inventory()]
    models.extend(hf_inventory_item(model_id, meta) for model_id, meta in HF_MODELS.items())
    total_size = dir_size(local_paths.MODELS_DIR)

    return {
        "modelsDir": str(local_paths.MODELS_DIR),
        "cacheDir": str(local_paths.CACHE_DIR),
        "totalSize": total_size,
        "totalSizeLabel": format_size(total_size),
        "models": models,
    }
