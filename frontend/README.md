# Frontend for KYC Fraud Detection

This folder contains a standalone JavaScript frontend for your FastAPI KYC detection backend.

## Features

- **Navigation**: Multi-page interface with Home, Submit KYC, API Docs, and About sections.
- **Dynamic UI**: Click navigation links to switch between pages without reloading.
- **Server Status**: Automatically checks if the backend server is running.
- **Sample Payload**: Pre-loaded sample KYC submission for testing.
- **Real-time Submission**: Submit JSON payloads and view decision results instantly.

## Usage

1. **Start the backend** (in the project root):

```bash
python -m uvicorn app.main:app --reload
```

2. **Serve the frontend** (in this `frontend/` folder):

```bash
python -m http.server 8001
```

3. **Open in browser**:

- `http://127.0.0.1:8001` or `http://localhost:8001`

4. **Navigate and use**:

- **Home**: Overview and quick submission.
- **Submit KYC**: Dedicated submission page.
- **API Docs**: Endpoint documentation with sample payloads.
- **About**: Project details and decision outcomes.

## Server Configuration

The frontend assumes the backend runs on `http://127.0.0.1:8000`. If your backend uses a different host/port, update the `endpoint` variable in `frontend/app.js`.

## Files

- `index.html`: Main HTML structure with navigation and pages.
- `styles.css`: Styling for the UI, including navigation and responsive design.
- `app.js`: JavaScript for navigation, form handling, and API calls.
- `README.md`: This documentation.

## Notes

- The frontend is standalone and does not require any build tools.
- Server status is checked on load and logged to the console.
- All backend files remain unchanged.
