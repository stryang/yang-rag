# Yang RAG Admin - 后台管理系统架构设计

## 系统概述

Yang RAG Admin 是一个为 Yang RAG System 设计的后台管理系统，提供知识库管理和用户管理功能。

> 2026-04 更新：Dashboard 统计已改为实时拉取（知识库数、文档数、RAG 服务健康状态），并修复创建知识库入口路由。

## 技术栈

### 后端
- **框架**: FastAPI
- **认证**: JWT (JSON Web Tokens)
- **密码加密**: bcrypt
- **数据库**: SQLite (轻量级，适合中小型部署)

### 前端
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **UI 库**: TailwindCSS + shadcn/ui
- **路由**: React Router v6
- **状态管理**: Zustand
- **HTTP 客户端**: Axios

## 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端 (React)                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐          │
│  │  登录页  │  │ Dashboard│  │ 知识库   │  │  用户    │          │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘          │
│       │              │             │             │                │
│       └──────────────┴─────────────┴─────────────┘                │
│                           │                                       │
│                    React Router + Axios                            │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ HTTP + JWT
┌───────────────────────────┴─────────────────────────────────────────┐
│                         后端 (FastAPI)                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │   认证模块   │  │  用户管理    │  │  知识库 API  │                 │
│  │ (JWT/bcrypt)│  │  (CRUD)     │  │ (已有接口)    │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                     ┌───────┴───────┐
                     │   SQLite     │
                     │  (用户数据)   │
                     └──────────────┘
```

## API 设计

### 认证接口

| 方法 | 路径 | 描述 |
|------|------|------|
| `POST` | `/api/v1/auth/login` | 用户登录 |
| `POST` | `/api/v1/auth/register` | 用户注册 |
| `POST` | `/api/v1/auth/logout` | 用户登出 |
| `GET` | `/api/v1/auth/me` | 获取当前用户信息 |

### 用户管理接口

| 方法 | 路径 | 描述 |
|------|------|------|
| `GET` | `/api/v1/users` | 列出所有用户（仅管理员） |
| `GET` | `/api/v1/users/{id}` | 获取用户详情 |
| `PUT` | `/api/v1/users/{id}` | 更新用户信息 |
| `DELETE` | `/api/v1/users/{id}` | 删除用户 |
| `PUT` | `/api/v1/users/{id}/password` | 修改密码 |

### 知识库接口（RAG 服务提供）

| 方法 | 路径 | 描述 |
|------|------|------|
| `GET` | `/api/v1/knowledge` | 列出知识库 |
| `POST` | `/api/v1/knowledge` | 创建知识库 |
| `GET` | `/api/v1/knowledge/{id}` | 获取知识库详情 |
| `PATCH` | `/api/v1/knowledge/{id}` | 更新知识库名称/描述 |
| `DELETE` | `/api/v1/knowledge/{id}` | 删除知识库 |
| `POST` | `/api/v1/knowledge/{id}/upload` | 上传文档 |
| `POST` | `/api/v1/knowledge/{id}/search` | 搜索（支持 vector/hybrid + reranker 参数） |

## 数据模型

### User 模型

```python
class User:
    id: int
    username: str  # 唯一
    email: str     # 唯一
    hashed_password: str
    role: str  # "admin" | "user"
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

### JWT Token

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin"
  }
}
```

## 页面设计

### 1. 登录页 (`/login`)
- 简洁的登录表单（用户名/邮箱 + 密码）
- 注册链接（可选开启）
- 错误提示

### 2. 管理后台 (`/admin`)

#### 侧边栏导航
- Dashboard
- 知识库管理
- 用户管理
- 设置

#### Dashboard 首页
- 实时知识库统计卡片
- 实时用户统计（管理员可见）
- RAG 服务在线状态与最近活动概览

#### 知识库管理
- 知识库列表（表格）
- 创建知识库
- 上传文档
- 删除知识库

#### 用户管理（仅管理员）
- 用户列表
- 创建用户
- 编辑用户（角色、状态）
- 重置密码

## 权限设计

| 角色 | 知识库 | 用户管理 |
|------|--------|---------|
| admin | 全部操作 | 全部操作 |
| user | 自己的知识库 | 仅查看个人信息 |

## 安全考虑

1. **密码**: 使用 bcrypt 加密
2. **Token**: JWT，24小时过期
3. **CORS**: 配置允许的前端域名
4. **Rate Limiting**: 登录接口限流
5. **输入验证**: Pydantic 模型验证

## 文件结构

```
yang-rag-admin/
├── backend/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI 入口
│   │   ├── auth/             # 认证模块
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── schemas.py
│   │   │   └── utils.py
│   │   ├── users/            # 用户管理
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   └── schemas.py
│   │   ├── database.py       # 数据库配置
│   │   └── models.py         # SQLAlchemy 模型
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── stores/
│   │   ├── api/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
└── README.md
```
