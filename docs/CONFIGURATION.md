# Yang RAG 系统配置指南

## 目录

- [快速开始](#快速开始)
- [LLM 模型配置](#llm-模型配置)
- [Embedding 模型配置](#embedding-模型配置)
- [配置方案示例](#配置方案示例)
- [常见问题](#常见问题)

---

## 快速开始

### 1. 复制配置文件

```bash
cp .env.example .env
```

### 2. 编辑配置

根据您选择的方案，修改 `.env` 文件中的相关配置。

### 3. 重启服务

```bash
# 重启 RAG API
pkill -f "python.*src.api.main" && python -m src.api.main &

# 或使用启动脚本
./start-rag.sh
```

---

## LLM 模型配置

### 配置项

| 配置项 | 说明 | 可选值 |
|--------|------|--------|
| `LLM_PROVIDER` | LLM 提供商 | `openai`, `siliconflow`, `qwen`, `ollama` |
| `LLM_MODEL` | 模型名称 | 见下方各提供商列表 |
| `LLM_API_KEY` | API 密钥 | 各提供商的密钥 |
| `LLM_BASE_URL` | API 端点 | 可选，用于代理 |
| `LLM_TEMPERATURE` | 温度参数 | 0.0-2.0，默认 0.7 |
| `LLM_MAX_TOKENS` | 最大 token 数 | 默认 2000 |

### 提供商详情

#### 1. OpenAI (付费)

**优点**: 模型质量最高，支持 GPT-4o、GPT-4-turbo 等顶级模型
**缺点**: 需要付费

```
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
```

**可用模型**:
- `gpt-4o` - 最新最强模型
- `gpt-4o-mini` - 性价比最高 (推荐)
- `gpt-4-turbo` - GPT-4 优化版
- `gpt-3.5-turbo` - 最便宜

**价格参考** (GPT-4o-mini):
- 输入: $0.15 / 1M tokens
- 输出: $0.60 / 1M tokens

---

#### 2. 硅基流动 SiliconFlow (免费额度)

**优点**: 国内可用，有免费额度，支持多种开源模型
**缺点**: 免费额度有限

```bash
# 注册地址: https://www.siliconflow.cn/
LLM_PROVIDER=siliconflow
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
```

**可用模型**:
- `Qwen/Qwen2.5-7B-Instruct` - 通义千问 (推荐)
- `deepseek-ai/DeepSeek-V2.5` - DeepSeek 模型
- `THUDM/glm-4-9b-chat` - 智谱 GLM-4

**价格**: 新用户有免费额度，之后按量计费，价格实惠

---

#### 3. 阿里通义千问 (免费额度)

**优点**: 国内可用，免费额度
**缺点**: 模型选择有限

```bash
# 注册地址: https://dashscope.console.aliyun.com/
LLM_PROVIDER=qwen
LLM_MODEL=qwen-turbo
LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
```

**可用模型**:
- `qwen-turbo` - 快速响应 (推荐)
- `qwen-plus` - 性能更强
- `qwen-max` - 最强性能

---

#### 4. Ollama (本地免费)

**优点**: 完全免费，本地运行，保护隐私
**缺点**: 需要较高配置，首次下载模型较慢

**安装步骤**:

```bash
# 1. 安装 Ollama (macOS)
brew install ollama

# 2. 安装 Ollama (Linux)
curl -fsSL https://ollama.com/install.sh | sh

# 3. 下载模型
ollama pull llama3.2
ollama pull qwen2.5

# 4. 启动服务
ollama serve
```

**配置**:

```bash
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
# LLM_BASE_URL=http://localhost:11434  # 默认值
```

**可用模型**:
- `llama3.2` - Meta 最新开源模型 (推荐)
- `llama3.1` - 8B 参数版本
- `qwen2.5` - 阿里开源模型
- `deepseek-r1` - DeepSeek 推理模型

**硬件要求**:
- 7B 模型: ~4GB RAM
- 13B 模型: ~8GB RAM
- 70B 模型: ~40GB RAM

---

## Embedding 模型配置

### 配置项

| 配置项 | 说明 | 可选值 |
|--------|------|--------|
| `EMBEDDING_PROVIDER` | Embedding 提供商 | `openai`, `siliconflow`, `huggingface`, `ollama` |
| `EMBEDDING_MODEL` | 模型名称 | 见下方各提供商列表 |
| `EMBEDDING_API_KEY` | API 密钥 | 各提供商的密钥 |
| `EMBEDDING_DIMENSION` | 向量维度 | 默认 1536 |

### 提供商详情

#### 1. OpenAI (付费)

```bash
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
EMBEDDING_DIMENSION=1536
```

**可用模型**:
- `text-embedding-3-small` - 最新小型模型 (推荐, 1536 维)
- `text-embedding-3-large` - 大型模型 (3072 维)
- `text-embedding-ada-002` - 旧版模型

**价格**: $0.02 / 1M tokens

---

#### 2. 硅基流动 (免费额度)

```bash
EMBEDDING_PROVIDER=siliconflow
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
EMBEDDING_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
EMBEDDING_DIMENSION=1024
```

**可用模型**:
- `BAAI/bge-large-zh-v1.5` - 中文最优 (推荐)
- `BAAI/bge-small-zh-v1.5` - 小型中文模型

---

#### 3. HuggingFace (本地免费)

**优点**: 完全免费，中文支持好
**缺点**: 需要下载模型，首次较慢

**安装依赖**:

```bash
pip install sentence-transformers
```

```bash
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=bge-large-zh-v1.5
```

**可用模型**:
- `bge-large-zh-v1.5` - 中文最优 (推荐)
- `bge-base-zh-v1.5` - 中型中文模型
- `bge-small-zh-v1.5` - 小型中文模型
- `bge-large-en-v1.5` - 英文大型模型

---

#### 4. Ollama (本地免费)

```bash
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
```

**可用模型**:
- `nomic-embed-text` - Nomic 开源模型 (推荐)

---

## 配置方案示例

### 方案一: 全 OpenAI (最简单)

适合有 OpenAI API Key 的用户，效果最好。

```bash
# LLM
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=sk-your-key

# Embedding
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_API_KEY=sk-your-key
```

**月费用估算**: ~$5-20 (取决于使用量)

---

### 方案二: 全硅基流动 (推荐国内用户)

国内可用，有免费额度，性价比高。

```bash
# LLM
LLM_PROVIDER=siliconflow
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
LLM_API_KEY=sk-your-siliconflow-key

# Embedding
EMBEDDING_PROVIDER=siliconflow
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
EMBEDDING_API_KEY=sk-your-siliconflow-key
```

**费用**: 新用户免费额度，之后按量计费

---

### 方案三: 全 Ollama (完全免费)

适合有较高配置的用户，完全免费。

```bash
# 先安装并启动 Ollama
# ollama pull llama3.2
# ollama pull nomic-embed-text

# LLM
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2

# Embedding
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
```

**费用**: 免费

**硬件要求**: 建议 16GB+ RAM

---

### 方案四: 混合方案

Embedding 用开源本地模型 + LLM 用云服务。

```bash
# Embedding 用 HuggingFace 本地模型
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=bge-large-zh-v1.5

# LLM 用硅基流动
LLM_PROVIDER=siliconflow
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
LLM_API_KEY=sk-your-key
```

---

## 常见问题

### Q: 如何获取 OpenAI API Key?

1. 访问 https://platform.openai.com/api-keys
2. 注册/登录账号
3. 点击 "Create new secret key"
4. 复制密钥

### Q: 如何获取硅基流动 API Key?

1. 访问 https://www.siliconflow.cn/
2. 注册账号
3. 进入控制台 → API 密钥
4. 创建新密钥

### Q: 如何获取阿里云 API Key?

1. 访问 https://dashscope.console.aliyun.com/
2. 开通模型服务
3. 获取 API Key

### Q: Ollama 下载的模型放在哪里?

```bash
# 查看模型位置
ollama show llama3.2 --json | grep location

# 默认位置
~/.ollama/models/
```

### Q: 如何切换模型?

1. 修改 `.env` 文件中的模型配置
2. 重启 RAG API 服务
3. 新创建的知识库会使用新模型
4. **注意**: 已索引的文档需要重新索引才能使用新 Embedding 模型

### Q: 向量维度不匹配怎么办?

不同的 Embedding 模型输出不同维度的向量。如果遇到维度不匹配错误：

1. 检查 `EMBEDDING_DIMENSION` 配置
2. 确保与向量数据库中的向量维度一致
3. 建议重新创建知识库

### Q: API 调用失败怎么办?

1. 检查 API Key 是否正确
2. 检查网络连接
3. 查看日志文件
4. 确认 API 额度是否用完

---

## 技术支持

如有问题，请提交 Issue 或联系开发者。
