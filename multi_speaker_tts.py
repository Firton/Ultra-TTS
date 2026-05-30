import argparse
import os
import re
import time
import wave

from gguf_orpheus import AVAILABLE_VOICES, SAMPLE_RATE, generate_speech_from_api


LINE_PATTERN = re.compile(
    r"^\s*(?P<voice>" + "|".join(re.escape(voice) for voice in AVAILABLE_VOICES) + r")\s*[:：]\s*(?P<text>.+?)\s*$",
    re.IGNORECASE,
)


def parse_script(path):
    utterances = []

    with open(path, "r", encoding="utf-8-sig") as script_file:
        for line_number, line in enumerate(script_file, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            match = LINE_PATTERN.match(line)
            if not match:
                valid_voices = ", ".join(AVAILABLE_VOICES)
                raise ValueError(
                    f"Line {line_number} is invalid. Use '<voice>: <text>'. "
                    f"Valid voices: {valid_voices}"
                )

            utterances.append(
                {
                    "line_number": line_number,
                    "voice": match.group("voice").lower(),
                    "text": match.group("text"),
                }
            )

    return utterances


def write_combined_wav(output_file, audio_chunks, silence_ms):
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    silence_frames = int(SAMPLE_RATE * silence_ms / 1000)
    silence = b"\x00\x00" * silence_frames

    with wave.open(output_file, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)

        for index, chunks in enumerate(audio_chunks):
            for chunk in chunks:
                wav_file.writeframes(chunk)

            if index != len(audio_chunks) - 1 and silence:
                wav_file.writeframes(silence)


def generate_multi_speaker(script_file, output_file, silence_ms):
    utterances = parse_script(script_file)
    if not utterances:
        raise ValueError("Script has no utterances.")

    all_audio = []
    start_time = time.time()

    for index, utterance in enumerate(utterances, start=1):
        print(
            f"[{index}/{len(utterances)}] "
            f"{utterance['voice']} line {utterance['line_number']}: {utterance['text']}"
        )
        chunks = generate_speech_from_api(
            prompt=utterance["text"],
            voice=utterance["voice"],
        )
        if not chunks:
            raise RuntimeError(
                f"No audio generated for line {utterance['line_number']} ({utterance['voice']})."
            )
        all_audio.append(chunks)

    write_combined_wav(output_file, all_audio, silence_ms)

    duration = time.time() - start_time
    print(f"Generated {len(utterances)} utterances in {duration:.2f} seconds")
    print(f"Audio saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Multi-speaker Orpheus TTS using LM Studio API")
    parser.add_argument("--script", required=True, help="UTF-8 script file. Use '<voice>: <text>' per line.")
    parser.add_argument("--output", required=True, help="Output WAV file path")
    parser.add_argument("--silence-ms", type=int, default=250, help="Silence between utterances in milliseconds")
    args = parser.parse_args()

    generate_multi_speaker(
        script_file=args.script,
        output_file=args.output,
        silence_ms=max(0, args.silence_ms),
    )


if __name__ == "__main__":
    main()
