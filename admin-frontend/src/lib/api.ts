import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Separate client for RAG API
export const ragApi = axios.create({
  baseURL: '/rag-api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token for admin API
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Request interceptor to add API key for RAG API
ragApi.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const apiKey = localStorage.getItem('rag_api_key') || 'rag-secret-key'
    if (config.headers) {
      config.headers['X-API-Key'] = apiKey
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for admin API
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Types
export interface User {
  id: number
  username: string
  email: string
  role: 'admin' | 'user'
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface UserCreate {
  username: string
  email: string
  password: string
  role: 'admin' | 'user'
}

export interface UserUpdate {
  username?: string
  email?: string
  role?: 'admin' | 'user'
  is_active?: boolean
}

export interface UserListResponse {
  users: User[]
  total: number
}

export type VectorStoreType = 'chroma' | 'faiss' | 'milvus'
export type VectorDatabaseStatus = 'online' | 'warning' | 'offline' | 'unknown'

export interface VectorDatabaseProfile {
  id: number
  name: string
  store_type: VectorStoreType
  description: string
  persist_path: string | null
  host: string | null
  port: number | null
  collection_prefix: string | null
  is_default: boolean
  is_enabled: boolean
  last_status: VectorDatabaseStatus
  last_checked_at: string | null
  last_error: string | null
  created_at: string
  updated_at: string
  target: string
}

export interface VectorDatabaseRuntimeCollection {
  id: string
  name: string
  description: string
  document_count: number
  chunk_count: number
  embedding_model: string
  updated_at: string
}

export interface VectorDatabaseRuntimeOverview {
  store_type: VectorStoreType
  status: VectorDatabaseStatus
  target: string
  persist_path: string | null
  host: string | null
  port: number | null
  message: string
  collection_count: number
  total_documents: number
  total_chunks: number
  storage_usage_bytes: number
  storage_usage_label: string
  managed_profiles: number
  collections: VectorDatabaseRuntimeCollection[]
}

export interface VectorDatabaseTestResponse {
  success: boolean
  status: VectorDatabaseStatus
  message: string
  checked_at: string
  resolved_target: string
}

export interface VectorDatabaseProfileInput {
  name: string
  store_type: VectorStoreType
  description: string
  persist_path?: string | null
  host?: string | null
  port?: number | null
  collection_prefix?: string | null
  is_default: boolean
  is_enabled: boolean
}

export type RuntimeLlmProvider = 'openai' | 'ollama' | 'siliconflow' | 'qwen'
export type RuntimeEmbeddingProvider = 'openai' | 'ollama' | 'siliconflow' | 'local' | 'huggingface'

export interface RuntimeSettings {
  llm_provider: RuntimeLlmProvider
  llm_model: string
  llm_api_key: string
  llm_base_url: string | null
  llm_temperature: number
  llm_max_tokens: number
  embedding_provider: RuntimeEmbeddingProvider
  embedding_model: string
  embedding_api_key: string
  embedding_base_url: string | null
  embedding_dimension: number
  vector_store_type: VectorStoreType
  vector_store_persist_dir: string
  milvus_host: string
  milvus_port: number
  milvus_collection: string
  api_endpoint: string
  uses_placeholder_llm_key: boolean
  uses_placeholder_embedding_key: boolean
}

export interface RuntimeSettingsUpdate {
  llm_provider: RuntimeLlmProvider
  llm_model: string
  llm_api_key: string
  llm_base_url: string | null
  llm_temperature: number
  llm_max_tokens: number
  embedding_provider: RuntimeEmbeddingProvider
  embedding_model: string
  embedding_api_key: string
  embedding_base_url: string | null
  embedding_dimension: number
  vector_store_type: VectorStoreType
  vector_store_persist_dir: string
  milvus_host: string
  milvus_port: number
  milvus_collection: string
  api_endpoint: string
}

// Knowledge Base types
export interface KnowledgeBase {
  id: string
  name: string
  description: string
  document_count: number
  chunk_count: number
  embedding_model: string
  created_at: string
  updated_at: string
}

export interface SearchResult {
  content: string
  metadata: Record<string, unknown>
  score: number
}

export interface KnowledgeSearchOptions {
  query: string
  top_k?: number
  retrieval_mode?: 'vector' | 'hybrid'
  retrieval_top_k?: number
  use_reranker?: boolean
  reranker_type?: 'simple' | 'cross-encoder' | 'llm'
  rerank_top_k?: number
  filter_dict?: Record<string, unknown>
}

export interface RuntimeReloadResponse {
  status: string
  llm_provider: string
  llm_model: string
  embedding_provider: string
  embedding_model: string
  vector_store_type: string
}

export interface SystemServiceStatus {
  key: string
  name: string
  status: 'online' | 'warning' | 'offline'
  detail: string
}

export interface SystemOverviewStats {
  total_users: number
  total_knowledge_bases: number
  total_documents: number
  total_chunks: number
  vector_profiles: number
}

export interface SystemOverview {
  generated_at: string
  stats: SystemOverviewStats
  services: SystemServiceStatus[]
  recent_knowledge_bases: KnowledgeBase[]
  vector_runtime: VectorDatabaseRuntimeOverview
}

// API functions - Auth
export const authApi = {
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/v1/auth/login', data)
    return response.data
  },

  register: async (data: UserCreate): Promise<User> => {
    const response = await api.post<User>('/v1/auth/register', data)
    return response.data
  },

  getMe: async (): Promise<User> => {
    const response = await api.get<User>('/v1/auth/me')
    return response.data
  },

  logout: async (): Promise<void> => {
    await api.post('/v1/auth/logout')
  },
}

// API functions - Users
export const usersApi = {
  list: async (skip = 0, limit = 100): Promise<UserListResponse> => {
    const response = await api.get<UserListResponse>('/v1/users', {
      params: { skip, limit },
    })
    return response.data
  },

  get: async (id: number): Promise<User> => {
    const response = await api.get<User>(`/v1/users/${id}`)
    return response.data
  },

  create: async (data: UserCreate): Promise<User> => {
    const response = await api.post<User>('/v1/users', data)
    return response.data
  },

  update: async (id: number, data: UserUpdate): Promise<User> => {
    const response = await api.put<User>(`/v1/users/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/v1/users/${id}`)
  },

  resetPassword: async (id: number, newPassword: string): Promise<User> => {
    const response = await api.put<User>(`/v1/users/${id}/password`, {
      new_password: newPassword,
    })
    return response.data
  },
}

// API functions - Vector Databases
export const vectorDatabasesApi = {
  getRuntime: async (): Promise<VectorDatabaseRuntimeOverview> => {
    const response = await api.get<VectorDatabaseRuntimeOverview>('/v1/vector-databases/runtime')
    return response.data
  },

  list: async (): Promise<{ items: VectorDatabaseProfile[]; total: number }> => {
    const response = await api.get<{ items: VectorDatabaseProfile[]; total: number }>('/v1/vector-databases')
    return response.data
  },

  get: async (id: number): Promise<VectorDatabaseProfile> => {
    const response = await api.get<VectorDatabaseProfile>(`/v1/vector-databases/${id}`)
    return response.data
  },

  create: async (data: VectorDatabaseProfileInput): Promise<VectorDatabaseProfile> => {
    const response = await api.post<VectorDatabaseProfile>('/v1/vector-databases', data)
    return response.data
  },

  update: async (id: number, data: Partial<VectorDatabaseProfileInput>): Promise<VectorDatabaseProfile> => {
    const response = await api.put<VectorDatabaseProfile>(`/v1/vector-databases/${id}`, data)
    return response.data
  },

  test: async (id: number): Promise<VectorDatabaseTestResponse> => {
    const response = await api.post<VectorDatabaseTestResponse>(`/v1/vector-databases/${id}/test`)
    return response.data
  },

  setDefault: async (id: number): Promise<VectorDatabaseProfile> => {
    const response = await api.post<VectorDatabaseProfile>(`/v1/vector-databases/${id}/default`)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/v1/vector-databases/${id}`)
  },
}

export const runtimeSettingsApi = {
  get: async (): Promise<RuntimeSettings> => {
    const response = await api.get<RuntimeSettings>('/v1/runtime-settings')
    return response.data
  },

  update: async (data: RuntimeSettingsUpdate): Promise<RuntimeSettings> => {
    const response = await api.put<RuntimeSettings>('/v1/runtime-settings', data)
    return response.data
  },

  reload: async (): Promise<RuntimeReloadResponse> => {
    const response = await api.post<RuntimeReloadResponse>('/v1/runtime-settings/reload')
    return response.data
  },
}

export const systemApi = {
  getOverview: async (): Promise<SystemOverview> => {
    const response = await api.get<SystemOverview>('/v1/system/overview')
    return response.data
  },
}

// API functions - Knowledge Bases
export const kbApi = {
  list: async (): Promise<{ knowledge_bases: KnowledgeBase[]; total: number }> => {
    const response = await api.get<{ knowledge_bases: KnowledgeBase[]; total: number }>('/v1/knowledge')
    return response.data
  },

  get: async (id: string): Promise<KnowledgeBase> => {
    const response = await api.get<KnowledgeBase>(`/v1/knowledge/${id}`)
    return response.data
  },

  create: async (data: { name: string; description: string }): Promise<KnowledgeBase> => {
    const response = await api.post<KnowledgeBase>('/v1/knowledge', data)
    return response.data
  },

  update: async (id: string, data: { name?: string; description?: string }): Promise<KnowledgeBase> => {
    const response = await api.patch<KnowledgeBase>(`/v1/knowledge/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/v1/knowledge/${id}`)
  },

  upload: async (kbId: string, file: File): Promise<{ status: string; file_name: string; document_count: number; chunk_count: number }> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post(`/v1/knowledge/${kbId}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  search: async (
    kbId: string,
    options: KnowledgeSearchOptions
  ): Promise<{ query: string; results: SearchResult[]; total: number; retrieval_mode: 'vector' | 'hybrid'; reranked: boolean }> => {
    const response = await api.post(`/v1/knowledge/${kbId}/search`, {
      top_k: 5,
      retrieval_mode: 'vector',
      use_reranker: false,
      reranker_type: 'simple',
      ...options,
    })
    return response.data
  },
}
