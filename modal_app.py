import modal

app = modal.App("whisper-asr-web")

image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.6.3-runtime-ubuntu22.04",
        add_python="3.10",
    )
    .apt_install("ffmpeg", "git", "libsndfile1")
    .pip_install(
        "torch==2.8.0+cu126",
        "torchaudio==2.8.0+cu126",
        index_url="https://download.pytorch.org/whl/cu126",
    )
    .pip_install(
        "fastapi>=0.115.14",
        "uvicorn[standard]>=0.35.0",
        "python-multipart>=0.0.20",
        "ffmpeg-python>=0.2.0",
        "numpy>=2.2.6",
        "openai-whisper>=20250625",
        "faster-whisper>=1.1.1",
        "whisperx>=3.8.2",
        "tqdm>=4.67.1",
        "llvmlite>=0.44.0",
        "numba>=0.61.2",
    )
    .add_local_dir("app", "/root/app", copy=True)
    .add_local_file("pyproject.toml", "/root/pyproject.toml", copy=True)
    .add_local_file("README.md", "/root/README.md", copy=True)
    .run_commands("cd /root && pip install --no-deps .")
    .env({
        "ASR_MODEL": "large-v2",
        "ASR_ENGINE": "whisperx",
        "ASR_DEVICE": "cpu",
        "HF_TOKEN": "PLACEHOLDER",
    })
    .run_commands(
        "python -c \"import whisper; whisper.load_model('large-v2', download_root='/root/.cache/whisper')\"",
        "python -c \"import whisperx; whisperx.load_align_model(language_code='zh', device='cpu')\"",
        "python -c \"from whisperx.diarize import DiarizationPipeline; import os; DiarizationPipeline(token=os.environ['HF_TOKEN'], device='cpu')\"",
    )
    .env({
        "ASR_MODEL": "large-v2",
        "ASR_ENGINE": "whisperx",
        "ASR_DEVICE": "cuda",
    })
)


@app.function(
    image=image,
    gpu="T4",
    timeout=7200,
    scaledown_window=300,
    secrets=[modal.Secret.from_name("huggingface-token")],
)
@modal.asgi_app()
def web():
    from app.webservice import app as fastapi_app

    return fastapi_app
