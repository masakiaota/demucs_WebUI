# %%
from __future__ import annotations

print("app is starting...")

import shutil
from multiprocessing import cpu_count
from pathlib import Path

import demucs.separate
import gradio as gr


# %% define configs
DIR_OF_THIS_FILE: Path = Path(__file__).parent.resolve()
OUTPUT_DIR: Path = (DIR_OF_THIS_FILE / "../outputs/").resolve()


class CFG:
    server_port = 9000
    sample_input_file: str = (
        (DIR_OF_THIS_FILE / "../data/shining_star_shortest.mp3").resolve().as_posix()
    )
    model_list: list[str] = [
        "htdemucs",
        "htdemucs_ft",
        "htdemucs_6s",
        "mdx_extra",
        "mdx_extra_q",
    ]
    default_model: str = "htdemucs_ft"
    two_stems_list: list[str] = [
        "False",
        "vocals",
        "drums",
        "bass",
        "piano",
        "guitar",
        "other",
    ]
    default_two_stems: str = "False"
    default_overlap: float = 0.2
    clip_mode_list: list[str] = ["rescale", "clamp"]
    default_clip_mode = "rescale"
    default_shifts = 1
    default_mp3_bitrate = 192


cfg = CFG()


# %% define demucs function
def demucs_separate(
    input_file: str | Path,
    model: str,
    is_two_stems: str,
    overlap: float,
    clip_mode: str,
    shifts: int,
    mp3_bitrate: int,
) -> list[Path]:
    assert model in [
        "htdemucs",
        "htdemucs_ft",
        "htdemucs_6s",
        "mdx_extra",
        "mdx_extra_q",
    ], "model must be htdemucs, htdemucs_ft, htdemucs_6s, mdx_extra or mdx_extra_q"
    assert is_two_stems in [
        "False",
        "vocals",
        "drums",
        "bass",
        "piano",
        "guitar",
        "other",
    ], f'is_two_stems must be "False", "vocals", "drums", "bass", "piano", "guitar" or "other". Not {is_two_stems}'
    assert 0 <= overlap <= 1, "overlap must be between 0 and 1"
    assert clip_mode in ["rescale", "clamp"], "clip_mode must be rescale or clamp"
    assert shifts >= 1, "shifts must be at least 1"
    assert 192 <= mp3_bitrate <= 320, "mp3_bitrate must be between 192 and 320"

    input_file = Path(input_file)
    print("input_file:", input_file)

    cmd = [
        "-j",
        str(cpu_count() // 2),
        "-n",
        model,
        "--overlap",
        str(overlap),
        # "--two-stems","vocals",
        "--clip-mode",
        clip_mode,
        "--shifts",
        str(shifts),
        "--mp3",
        "--mp3-bitrate",
        str(mp3_bitrate),
        "-o",
        OUTPUT_DIR.as_posix(),
        input_file.as_posix(),
    ]
    if is_two_stems != "False":
        cmd.insert(6, "--two-stems")
        cmd.insert(7, is_two_stems)

    demucs.separate.main(opts=cmd)

    song_dir = Path(OUTPUT_DIR) / model / input_file.stem

    audio_preview_path = [
        song_dir / "vocals.mp3",
        song_dir / "drums.mp3",
        song_dir / "bass.mp3",
        song_dir / "piano.mp3",
        song_dir / "guitar.mp3",
        song_dir / "other.mp3",
    ]

    # もし足りなければまずは、othersで代替する
    for i in range(len(audio_preview_path)):
        if not audio_preview_path[i].exists():
            audio_preview_path[i] = song_dir / "other.mp3"

    if is_two_stems != "False":
        # ただし、is_two_stemsがFalseでないときは、
        # no_{is_two_stems}で代替する
        for i in range(len(audio_preview_path)):
            if not audio_preview_path[i].exists():
                audio_preview_path[i] = song_dir / f"no_{is_two_stems}.mp3"

    files = list(song_dir.glob("*.mp3"))
    # TODO : gzに圧縮して返す
    shutil.make_archive(song_dir, "gztar", song_dir)
    files.append(song_dir.with_suffix(".tar.gz"))

    ret = (
        audio_preview_path[0],
        audio_preview_path[1],
        audio_preview_path[2],
        audio_preview_path[3],
        audio_preview_path[4],
        audio_preview_path[5],
        files,
    )

    return ret


# %% gradio interface

demo = gr.Interface(
    fn=demucs_separate,
    inputs=[
        gr.Audio(label="Input Audio", type="filepath"),
        gr.Dropdown(choices=cfg.model_list, value=cfg.default_model, label="Model"),
        gr.Dropdown(
            choices=cfg.two_stems_list,
            value=cfg.default_two_stems,
            label="Make Two Stems",
        ),
        gr.Slider(
            minimum=0.05,
            maximum=1.0,
            step=0.01,
            value=cfg.default_overlap,
            label="Overlap",
        ),
        gr.Dropdown(
            choices=cfg.clip_mode_list,
            value=cfg.default_clip_mode,
            label="Clip Mode",
        ),
        gr.Slider(
            minimum=1,
            maximum=20,
            step=1,
            value=cfg.default_shifts,
            label="Shifts",
        ),
        gr.Slider(
            minimum=192,
            maximum=320,
            step=1,
            value=cfg.default_mp3_bitrate,
            label="MP3 Bitrate",
        ),
    ],
    outputs=[
        gr.Audio(label="Vocals", type="filepath"),
        gr.Audio(label="Drums"),
        gr.Audio(label="Bass"),
        gr.Audio(label="Piano"),
        gr.Audio(label="Guitar"),
        gr.Audio(label="Other"),
        gr.File(label="For Download"),
    ],
    examples=[
        [
            cfg.sample_input_file,
            "htdemucs",
            "False",
            0.1,
            cfg.default_clip_mode,
            cfg.default_shifts,
            cfg.default_mp3_bitrate,
        ],
    ],
)

# %% launch
demo.queue()
demo.launch(server_port=cfg.server_port)
