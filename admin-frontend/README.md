# Yang RAG Admin

企业级 RAG 系统的后台管理界面，包含用户认证、知识库管理和用户管理功能。

## 功能特性

### 用户认证
- JWT Token 认证
- 用户注册与登录
- 角色权限控制（Admin / User）
- 密码加密（bcrypt）

### 用户管理（仅管理员）
- 查看所有用户
- 创建新用户
- 编辑用户信息
- 重置用户密码
- 删除用户

### 知识库管理
- 查看知识库列表
- 创建知识库
- 上传文档
- 删除知识库

## 技术栈

### 后端
- **框架**: FastAPI
- **认证**: JWT (python-jose)
- **密码加密**: bcrypt (passlib)
- **数据库**: SQLite (SQLAlchemy + aiosqlite)
- **端口**: 8001

### 前端
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **样式**: TailwindCSS
- **状态管理**: Zustand
- **路由**: React Router v6
- **HTTP**: Axios
- **端口**: 5173

## 快速开始

### 方式一：使用启动脚本

```bash
cd /Users/leo/IdeaProjects/yang/rag
chmod +x start-admin.sh
./start-admin.sh
```

### 方式二：手动启动

**1. 启动后端**

```bash
cd admin-backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

**2. 启动前端（新终端）**

```bash
cd admin-frontend
npm install
npm run dev
```

## 访问地址

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:5173 |
| 后端 API | http://localhost:8001 |
| API 文档 | http://localhost:8001/docs |

## 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |

## API 接口

### 认证接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/auth/login` | 用户登录 |
| POST | `/api/v1/auth/register` | 用户注册 |
| GET | `/api/v1/auth/me` | 获取当前用户 |
| POST | `/api/v1/auth/logout` | 用户登出 |

### 用户管理接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/users` | 列出所有用户 |
| POST | `/api/v1/users` | 创建用户 |
| GET | `/api/v1/users/{id}` | 获取用户详情 |
| PUT | `/api/v1/users/{id}` | 更新用户 |
| DELETE | `/api/v1/users/{id}` | 删除用户 |

## 项目结构

```
yang-rag/
├── admin-backend/           # 后端
│   ├── src/
│   │   ├── main.py         # FastAPI 入口
│   │   ├── database.py     # 数据库配置
│   │   ├── models.py       # 数据模型
│   │   ├── auth/           # 认证模块
│   │   └── users/          # 用户管理
│   ├── requirements.txt
│   └── run.py
├── admin-frontend/          # 前端
│   ├── src/
│   │   ├── components/     # 组件
│   │   ├── pages/         # 页面
│   │   ├── stores/        # 状态管理
│   │   ├── lib/           # 工具函数
│   │   └── App.tsx        # 应用入口
│   ├── package.json
│   └── vite.config.ts
├── start-admin.sh          # 启动脚本
└── docs/
    └── ADMIN_SYSTEM_DESIGN.md
```

## 安全说明

1. **生产环境请修改密钥**: 编辑 `admin-backend/src/auth/utils.py` 中的 `SECRET_KEY`
2. **使用强密码**: 默认密码仅用于演示
3. **CORS 配置**: 根据实际需求调整 `admin-backend/src/main.py` 中的 CORS 配置

## License

MIT
