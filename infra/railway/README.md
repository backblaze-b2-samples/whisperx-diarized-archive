# Railway Deployment

Deploy both services (web + api) on Railway.

## Setup

1. Create a new Railway project
2. Add two services from the same repo:

### Web Service (`whisperx-diarized-archive-web`)
- **Root Directory**: `apps/web`
- **Build Command**: `pnpm install && pnpm build`
- **Start Command**: `pnpm start`
- **Port**: `3000`

### API Service (`whisperx-diarized-archive-api`)
- **Root Directory**: `services/api`
- **Build Command**: `pip install -r requirements.txt && pip install -r requirements-ml.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

> The API also needs **ffmpeg** on the image (audio/video decoding) and the heavy
> ML stack from `requirements-ml.txt`. A **GPU instance is strongly recommended**
> for production throughput — set `WHISPERX_DEVICE=cuda` and install a
> CUDA-enabled `torch`. CPU works for short clips but is slow at scale.

## Environment Variables

Set these on the API service:

| Variable | Value |
|----------|-------|
| `B2_APPLICATION_KEY_ID` | Your B2 key ID |
| `B2_APPLICATION_KEY` | Your B2 application key |
| `B2_BUCKET_NAME` | Your bucket name |
| `B2_REGION` | Your bucket region (e.g. `us-west-004`) — the S3 endpoint is derived from it |
| `B2_PUBLIC_URL_BASE` | (Optional) public base URL for objects |
| `HF_TOKEN` | (Optional) free HuggingFace token to enable speaker diarization |
| `WHISPERX_DEVICE` | `cuda` on a GPU instance, `cpu` otherwise |
| `API_CORS_ORIGINS` | Your web service URL (e.g., `https://web-production-xxx.up.railway.app`) |

Set this on the Web service:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | Your API service URL (e.g., `https://api-production-xxx.up.railway.app`) |
