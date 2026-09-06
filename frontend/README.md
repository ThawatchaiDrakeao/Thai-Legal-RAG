# Thai Legal RAG Demo UI

React + Vite single-page demo for the Thai Legal RAG API.

## Run development server

From the `frontend/` directory:

```powershell
npm install
npm run dev
```

Open `http://localhost:5173`. The UI calls the backend at `http://127.0.0.1:8000` by default. To use another URL, copy `.env.example` to `.env` and set:

```text
VITE_API_URL=http://127.0.0.1:8000
```

## Build for production

```powershell
npm run build
npm run preview
```

The UI does not use `localStorage` or `sessionStorage`.
