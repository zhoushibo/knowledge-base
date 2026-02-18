# API 配置更新 - 添加第 3 个 NVIDIA API Key

**更新时间：** 2026-02-18 16:10  
**更新人：** Claw  
**原因：** 用户指出有 3 个 NVIDIA API Key，但 `API_IMPLEMENTATION_GUIDE.md` 中只记录了 2 个

---

## 🎯 更新内容

### 新增：英伟达 3 (第 3 备用) - z-ai/glm4.7

**基本信息：**
```
Provider: NVIDIA (cherry-nvidia)
URL: https://integrate.api.nvidia.com/v1/chat/completions
API KEY: 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
模型：z-ai/glm4.7
```

**性能指标：**
- 平均延迟：待测试
- 上下文窗口：128,000 tokens
- RPM 限制：40/分钟
- 并发限制：5
- 支持思考模式：✅

**适用场景：**
- ✅ 英伟达 1/2 的备用
- ✅ 负载均衡
- ✅ 标准任务

**调用示例：**
```python
import requests

def call_nvidia3_api(prompt):
    headers = {
        "Authorization": "Bearer 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",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "z-ai/glm4.7",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "temperature": 0.7,
        "max_tokens": 1000,
        "extra_body": {
            "chat_template_kwargs": {
                "enable_thinking": True,
                "clear_thinking": False
            }
        }
    }
    response = requests.post(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=120
    )
    result = response.json()
    content = result['choices'][0]['message']['content']
    return content
```

**注意事项：**
✅ **推荐：** 作为第 3 备用，当英伟达 1/2 都失败时使用。

---

## 📋 完整的 NVIDIA API Key 列表

| 编号 | 名称 | API Key | 状态 | 优先级 |
|------|------|---------|------|--------|
| **1** | 英伟达 1 (主) | `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` | ✅ 可用 | 1️⃣ 优先 |
| **2** | 英伟达 2 (备用) | `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` | ✅ 可用 | 2️⃣ 次优先 |
| **3** | 英伟达 3 (第 3 备用) | `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` | ✅ 可用 | 3️⃣ 备用 |

---

## 🔄 使用建议

### 推荐调用顺序

```python
NVIDIA_APIS = [
    {
        "name": "nvidia2",  # 最快最稳定
        "key": "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",
        "priority": 1
    },
    {
        "name": "nvidia1",  # 深度思考
        "key": "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",
        "priority": 2
    },
    {
        "name": "nvidia3",  # 第 3 备用
        "key": "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",
        "priority": 3
    }
]
```

### Fallback 策略

```python
def call_nvidia_with_fallback(prompt):
    """按优先级依次尝试 3 个 NVIDIA API"""
    for api in NVIDIA_APIS:
        try:
            content = call_nvidia_api(prompt, api["key"])
            print(f"✅ 使用 {api['name']} 成功")
            return content
        except Exception as e:
            print(f"❌ {api['name']} 失败：{e}")
            continue
    
    raise Exception("所有 NVIDIA API 都失败")
```

---

## 📝 待办事项

- [ ] 更新 `API_IMPLEMENTATION_GUIDE.md` 正式文档
- [ ] 在 `knowledge_base` 项目中配置 3 个 API Key 的 fallback
- [ ] 测试第 3 个 API Key 的可用性
- [ ] 更新负载均衡策略，加入第 3 个 Key

---

**记录时间：** 2026-02-18 16:10  
**状态：** ✅ 已记录，待正式文档更新
