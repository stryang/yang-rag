# API 接口文档

## 1. 基础信息

- 基础 URL: `http://api.example.com/v1`
- 认证方式: Bearer Token (JWT)
- 数据格式: JSON
- 字符编码: UTF-8

## 2. 认证

### 2.1 登录接口

**请求**
```http
POST /auth/login
Content-Type: application/json

{
    "username": "user@example.com",
    "password": "password123"
}
```

**响应**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600
}
```

### 2.2 Token 刷新

**请求**
```http
POST /auth/refresh
Authorization: Bearer <refresh_token>

{
    "grant_type": "refresh_token"
}
```

## 3. 用户管理

### 3.1 获取用户信息

**请求**
```http
GET /users/{user_id}
Authorization: Bearer <access_token>
```

**响应**
```json
{
    "id": "usr_123456",
    "username": "zhangsan",
    "email": "zhangsan@example.com",
    "phone": "+86-138-0000-0000",
    "status": "active",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}
```

### 3.2 创建用户

**请求**
```http
POST /users
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "username": "lisi",
    "email": "lisi@example.com",
    "password": "SecureP@ss123",
    "phone": "+86-139-0000-0000"
}
```

**响应**
```json
{
    "id": "usr_789012",
    "username": "lisi",
    "email": "lisi@example.com",
    "status": "pending",
    "created_at": "2024-01-15T11:00:00Z"
}
```

### 3.3 更新用户

**请求**
```http
PATCH /users/{user_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "phone": "+86-139-1111-1111",
    "status": "active"
}
```

### 3.4 删除用户

**请求**
```http
DELETE /users/{user_id}
Authorization: Bearer <access_token>
```

**响应**
```json
{
    "message": "User deleted successfully",
    "deleted_at": "2024-01-15T12:00:00Z"
}
```

## 4. 订单管理

### 4.1 订单列表

**请求**
```http
GET /orders
Authorization: Bearer <access_token>
```

**查询参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码，默认1 |
| page_size | int | 每页数量，默认20 |
| status | string | 订单状态筛选 |
| start_date | string | 开始日期 |
| end_date | string | 结束日期 |

**响应**
```json
{
    "items": [
        {
            "id": "ord_123456",
            "user_id": "usr_123456",
            "total_amount": 299.00,
            "status": "completed",
            "items": [
                {
                    "product_id": "prod_001",
                    "name": "商品A",
                    "price": 199.00,
                    "quantity": 1
                },
                {
                    "product_id": "prod_002",
                    "name": "商品B",
                    "price": 100.00,
                    "quantity": 1
                }
            ],
            "created_at": "2024-01-15T10:00:00Z"
        }
    ],
    "pagination": {
        "page": 1,
        "page_size": 20,
        "total_items": 100,
        "total_pages": 5
    }
}
```

### 4.2 创建订单

**请求**
```http
POST /orders
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "items": [
        {"product_id": "prod_001", "quantity": 2},
        {"product_id": "prod_003", "quantity": 1}
    ],
    "shipping_address": {
        "recipient": "张三",
        "phone": "+86-138-0000-0000",
        "address": "北京市朝阳区某某街道123号",
        "postal_code": "100000"
    }
}
```

**响应**
```json
{
    "id": "ord_789012",
    "status": "pending_payment",
    "total_amount": 498.00,
    "payment_deadline": "2024-01-15T12:00:00Z",
    "created_at": "2024-01-15T11:00:00Z"
}
```

## 5. 错误响应

### 5.1 错误格式
```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid request parameters",
        "details": [
            {
                "field": "email",
                "message": "Invalid email format"
            }
        ]
    },
    "request_id": "req_abc123",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### 5.2 错误码对照表

| HTTP状态码 | 错误码 | 说明 |
|------------|--------|------|
| 400 | VALIDATION_ERROR | 参数验证失败 |
| 401 | UNAUTHORIZED | 未认证 |
| 403 | FORBIDDEN | 无权限 |
| 404 | NOT_FOUND | 资源不存在 |
| 409 | CONFLICT | 资源冲突 |
| 429 | RATE_LIMITED | 请求过于频繁 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |

## 6. 速率限制

- 默认限制: 100 请求/分钟
- 认证用户: 1000 请求/分钟
- 超限返回: HTTP 429

### 响应头
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1705312200
```
