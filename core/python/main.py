"""
PrizmAgent 主入口文件
"""
import uvicorn
from fastapi import FastAPI
from agent_core.orchestrator import Orchestrator
from config.settings import settings

app = FastAPI(
    title="PrizmAgent",
    description="A modular, extensible AI agent framework",
    version="0.1.0"
)

# 初始化核心组件
orchestrator = Orchestrator()

@app.on_event("startup")
async def startup_event():
    """启动时初始化所有模块"""
    orchestrator.initialize_all()

@app.get("/")
async def root():
    return {"message": "Welcome to PrizmAgent"}

def main():
    """主函数"""
    uvicorn.run(
        "main:app",
        host=settings.get('api.host', '0.0.0.0'),
        port=settings.get('api.port', 8000),
        reload=settings.get('api.debug', True)
    )

if __name__ == "__main__":
    main()
