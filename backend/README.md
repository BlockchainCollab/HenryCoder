# Backend API Server

This document describes how to set up and run the backend API server for the EVM to Ralph translator.

## Prerequisites

- Python 3.8+
- pip (Python package installer)
- virtualenv (optional, but recommended)

## Configuration

The server can be configured using a `.env` file in the `backend` directory. Create a file named `.env` and add the following variables:

```
HOST=127.0.0.1
PORT=8000
```

- `HOST`: The IP address the server will bind to.
- `PORT`: The port the server will listen on.

If the `.env` file is not present, or these variables are not set, the server will default to `HOST=127.0.0.1` and `PORT=8000`.

## Setup and Running

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Create a Python virtual environment (recommended):**
    ```bash
    python3 -m venv .venv
    ```

3.  **Activate the virtual environment:**

    *   On macOS and Linux:
        ```bash
        source .venv/bin/activate
        ```
    *   On Windows:
        ```bash
        .\.venv\Scripts\activate
        ```

4.  **Install the required dependencies:**
    Make sure to re-run this if you pull new changes that might update `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

5.  **Run the FastAPI server:**
    You can now run the server directly using Python. It will use Uvicorn internally and pick up settings from the `.env` file.
    ```bash
    python main.py
    ```
    For development, if you want auto-reloading when code changes, you can still use Uvicorn directly, but it won't automatically pick up the `.env` for host/port unless Uvicorn itself is configured to do so or you pass them as arguments. The `python main.py` method is now the recommended way to ensure `.env` loading for host/port.
    If you still prefer to use uvicorn directly with auto-reload and custom host/port:
    ```bash
    uvicorn main:app --reload --host <your_host> --port <your_port>
    ```
    (Replace `<your_host>` and `<your_port>` with values from your `.env` or desired settings).

6.  **Access the API:**
    Once the server is running, you can access the API at the configured `HOST` and `PORT` (e.g., `http://127.0.0.1:8000` by default).
    -   The health check endpoint is available at `http://<HOST>:<PORT>/api/health`.
    -   The translation endpoint is `POST http://<HOST>:<PORT>/api/translate`.
    -   Interactive API documentation (Swagger UI) is available at `http://<HOST>:<PORT>/docs`.
    -   Alternative API documentation (ReDoc) is available at `http://<HOST>:<PORT>/redoc`.

## To Deactivate the Virtual Environment (when done):
```bash
deactivate
```
