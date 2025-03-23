from fastapi.middleware.cors import CORSMiddleware

def add_cors_middleware(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Replace with specific domains like ["https://example.com"]
        allow_credentials=True,
        allow_methods=["*"],  # Allow all HTTP methods
        allow_headers=["*"],  # Allow all headers
    )
