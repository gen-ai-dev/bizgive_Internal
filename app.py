from fastapi import FastAPI
from routers.api_routes import router
from mangum import Mangum 
from dotenv import load_dotenv
from middlewares.cors_middlewares import add_cors_middleware
load_dotenv()

app = FastAPI()

# Add CORS middleware
add_cors_middleware(app)


app.include_router(router)

lambda_handler = Mangum(app) 
if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host="0.0.0.0", port=8000,reload=True)