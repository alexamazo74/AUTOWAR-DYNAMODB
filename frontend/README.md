Quick frontend demo for AutoWAR scores

Run the backend locally (from repo root):

```powershell
# from repository root
python -m uvicorn src.app.main:app --host 127.0.0.1 --port 8001 --log-level info
```

Serve the frontend and open it in a browser:

```powershell
# from repository root
cd frontend
python -m http.server 8080
# then open http://127.0.0.1:8080 in your browser
```

The page provides a small UI to POST /scores and to GET /evaluations/:id/scores. Adjust the base URL if your backend runs on a different host/port.
