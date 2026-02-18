"""
Gateway 客户端 - 统一 API 调用接口

通过 WebSocket 连接到统一 Gateway 服务，实现智能路由和 Fallback
不再直接调用各个 API Provider，所有调用通过 Gateway 统一管理
"""
import asyncio
import websockets
import json
import logging
from typing import Optional, AsyncGenerator, Dict, Any
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger(__name__)

class GatewayClient:
    """Gateway 客户端 - 统一 API 调用接口"""
    
    def __init__(self, gateway_url: Optional[str] = None):
        """
        初始化 Gateway 客户端
        
        Args:
            gateway_url: Gateway WebSocket 地址（默认从环境变量读取）
        """
        self.gateway_url = gateway_url or os.getenv("GATEWAY_URL", "ws://127.0.0.1:8001")
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.session_id = "default"
    
    async def connect(self, session_id: str = "default") -> bool:
        """
        连接到 Gateway
        
        Args:
            session_id: 会话 ID
            
        Returns:
            是否连接成功
        """
        try:
            self.session_id = session_id
            ws_url = f"{self.gateway_url}/ws/stream/{session_id}"
            logger.info(f"正在连接到 Gateway: {ws_url}")
            self.websocket = await websockets.connect(ws_url)
            self.connected = True
            logger.info("✅ Gateway 连接成功")
            return True
        except Exception as e:
            logger.error(f"❌ Gateway 连接失败：{e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """断开 Gateway 连接"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            self.connected = False
            logger.info("Gateway 已断开")
    
    async def send_message(self, message: str, provider: str = "nvidia2") -> AsyncGenerator[str, None]:
        """
        发送消息并接收流式响应
        
        Args:
            message: 用户消息
            provider: API 提供者（可选，默认使用 Gateway 的默认配置）
            
        Yields:
            流式响应文本块
        """
        if not self.connected or not self.websocket:
            raise ConnectionError("未连接到 Gateway")
        
        # 发送消息
        payload = {
            "message": message,
            "provider": provider
        }
        logger.info(f"发送消息到 Gateway: {message[:50]}...")
        await self.websocket.send(json.dumps(payload))
        
        # 接收流式响应
        try:
            async for response in self.websocket:
                # 解析响应
                if response.startswith('{'):
                    data = json.loads(response)
                    # 完成信号
                    if data.get('type') == 'done':
                        logger.info("流式响应完成")
                        break
                    # 错误信号
                    elif data.get('type') == 'error':
                        error_msg = data.get('message', '未知错误')
                        logger.error(f"Gateway 错误：{error_msg}")
                        raise Exception(f"Gateway 错误：{error_msg}")
                else:
                    # 文本块
                    yield response
        except websockets.exceptions.ConnectionClosed:
            logger.error("Gateway 连接意外关闭")
            self.connected = False
            raise
    
    async def chat(self, message: str, provider: str = "nvidia2") -> str:
        """
        发送消息并收集完整响应
        
        Args:
            message: 用户消息
            provider: API 提供者
            
        Returns:
            完整响应文本
        """
        full_response = ""
        async for chunk in self.send_message(message, provider):
            full_response += chunk
        return full_response
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            Gateway 状态信息
        """
        try:
            import requests
            http_url = os.getenv("GATEWAY_HTTP_URL", "http://127.0.0.1:8001")
            response = requests.get(f"{http_url}/health", timeout=5)
            return response.json()
        except Exception as e:
            logger.error(f"健康检查失败：{e}")
            return {"status": "error", "error": str(e)}
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()


# 同步包装器（用于非异步代码）
class SyncGatewayClient:
    """Gateway 客户端同步包装器"""
    
    def __init__(self, gateway_url: Optional[str] = None):
        self.client = GatewayClient(gateway_url)
    
    def chat(self, message: str, provider: str = "nvidia2") -> str:
        """同步调用 Gateway"""
        return asyncio.run(self.client.chat(message, provider))
    
    def health_check(self) -> Dict[str, Any]:
        """同步健康检查"""
        return asyncio.run(self.client.health_check())


# 使用示例
async def main():
    """测试 Gateway 客户端"""
    print("=" * 80)
    print("🧪 Gateway 客户端测试")
    print("=" * 80)
    
    # 健康检查
    print("\n1️⃣ 健康检查...")
    client = GatewayClient()
    health = await client.health_check()
    print(f" Gateway 状态：{health.get('status', 'unknown')}")
    if health.get('status') == 'ok':
        print(f" ✅ Gateway 运行中")
        print(f" ✅ API Providers: {health.get('api_providers', [])}")
        print(f" ✅ 默认 Provider: {health.get('default_provider', 'unknown')}")
    else:
        print(f" ❌ Gateway 未运行")
        print(f" 💡 提示：启动 Gateway: python openclaw_async_architecture/streaming-service/src/gateway.py")
        return
    
    # 对话测试
    print("\n2️⃣ 对话测试...")
    async with client:
        response = await client.chat("你好，请用一句话介绍你自己")
        print(f" 响应：{response[:100]}...")
        print(" ✅ 对话成功")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
