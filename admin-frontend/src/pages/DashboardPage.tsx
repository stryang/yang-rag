import React, { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Activity,
  ArrowRight,
  Database,
  HardDrive,
  Layers3,
  Plus,
  RefreshCw,
  Server,
  Shield,
  Users,
} from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import { cn } from '@/lib/utils'
import { systemApi, type SystemOverview, type SystemServiceStatus } from '@/lib/api'

const formatDateTime = (value: string) =>
  new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))

const STATUS_STYLES: Record<SystemServiceStatus['status'], string> = {
  online: 'border-primary-100 bg-primary-50 text-primary-700',
  warning: 'border-amber-100 bg-amber-50 text-amber-700',
  offline: 'border-red-100 bg-red-50 text-red-700',
}

const STATUS_DOT_STYLES: Record<SystemServiceStatus['status'], string> = {
  online: 'bg-primary-500',
  warning: 'bg-amber-500',
  offline: 'bg-red-500',
}

const DashboardPage: React.FC = () => {
  const { user } = useAuthStore()
  const [overview, setOverview] = useState<SystemOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')

  const fetchOverview = async (silent = false) => {
    try {
      if (silent) {
        setRefreshing(true)
      } else {
        setLoading(true)
      }
      setError('')
      const response = await systemApi.getOverview()
      setOverview(response)
    } catch (err) {
      console.error('Failed to fetch system overview:', err)
      setError('系统概览加载失败，请确认管理后端与 RAG 服务已启动。')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    void fetchOverview()
  }, [])

  const cards = useMemo(() => {
    if (!overview) {
      return []
    }

    return [
      {
        key: 'knowledge',
        name: '知识库',
        value: overview.stats.total_knowledge_bases,
        helper: '已纳入管理的知识库',
        icon: Database,
        tone: 'primary',
        href: '/admin/knowledge',
        visible: true,
      },
      {
        key: 'documents',
        name: '文档总数',
        value: overview.stats.total_documents,
        helper: `${overview.stats.total_chunks} 个切片`,
        icon: Layers3,
        tone: 'neutral',
        href: '/admin/knowledge',
        visible: true,
      },
      {
        key: 'vectors',
        name: '向量配置',
        value: overview.stats.vector_profiles,
        helper: overview.vector_runtime.store_type.toUpperCase(),
        icon: HardDrive,
        tone: 'neutral',
        href: '/admin/vector-databases',
        visible: true,
      },
      {
        key: 'users',
        name: '用户总数',
        value: overview.stats.total_users,
        helper: user?.role === 'admin' ? '当前后台账户数' : '管理员可见',
        icon: Users,
        tone: 'primary',
        href: '/admin/users',
        visible: user?.role === 'admin',
      },
    ].filter((item) => item.visible)
  }, [overview, user?.role])

  if (loading) {
    return (
      <div className="space-y-6 page-enter">
        <div className="flex items-center justify-between">
          <div className="space-y-3">
            <div className="h-8 w-36 rounded-xl bg-gray-200 skeleton" />
            <div className="h-4 w-64 rounded-xl bg-gray-100 skeleton" />
          </div>
          <div className="h-11 w-32 rounded-2xl bg-gray-200 skeleton" />
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="h-36 rounded-2xl bg-white skeleton" />
          ))}
        </div>
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.4fr_0.9fr]">
          <div className="h-[26rem] rounded-2xl bg-white skeleton" />
          <div className="h-[26rem] rounded-2xl bg-white skeleton" />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 page-enter">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">仪表盘</h1>
          <p className="mt-1 text-gray-500">
            欢迎回来，{user?.username}。这里展示当前 RAG 系统的运行视图与管理入口。
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={() => void fetchOverview(true)}
            disabled={refreshing}
            className="btn-secondary"
          >
            <RefreshCw className={cn('h-4 w-4', refreshing && 'animate-spin')} />
            {refreshing ? '刷新中...' : '刷新数据'}
          </button>
          <Link to="/admin/knowledge" className="btn-primary">
            <Plus className="h-4 w-4" />
            新建知识库
          </Link>
        </div>
      </div>

      {error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {overview && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {cards.map((card, index) => (
              <Link
                key={card.key}
                to={card.href}
                className="group relative overflow-hidden rounded-2xl border border-gray-200 bg-white p-5 transition-all duration-300 hover:-translate-y-0.5 hover:border-primary-200 hover:shadow-lg hover:shadow-gray-900/5 animate-rise-in"
                style={{ animationDelay: `${index * 70}ms` }}
              >
                <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-primary-500 via-primary-600 to-dark opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-500">{card.name}</p>
                    <p className="mt-2 text-3xl font-bold text-gray-900">{card.value}</p>
                    <p className="mt-3 text-sm text-gray-500">{card.helper}</p>
                  </div>
                  <div className={cn(
                    'flex h-12 w-12 items-center justify-center rounded-2xl',
                    card.tone === 'primary' ? 'bg-primary-50 text-primary-700' : 'bg-gray-100 text-gray-700'
                  )}>
                    <card.icon className="h-6 w-6" />
                  </div>
                </div>
                <div className="mt-5 flex items-center gap-1 text-sm font-medium text-gray-400 transition-colors group-hover:text-primary-700">
                  查看详情
                  <ArrowRight className="h-4 w-4" />
                </div>
              </Link>
            ))}
          </div>

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.4fr_0.9fr]">
            <div className="space-y-6">
              <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white animate-rise-in">
                <div className="flex flex-col gap-4 border-b border-gray-100 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <h2 className="flex items-center gap-2 text-lg font-bold text-gray-900">
                      <Server className="h-5 w-5 text-primary-600" />
                      服务健康
                    </h2>
                    <p className="mt-1 text-sm text-gray-500">
                      最近一次汇总时间：{formatDateTime(overview.generated_at)}
                    </p>
                  </div>
                  <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-700">
                    当前向量引擎：{overview.vector_runtime.store_type.toUpperCase()}
                  </span>
                </div>
                <div className="grid grid-cols-1 gap-4 p-6 md:grid-cols-3">
                  {overview.services.map((service) => (
                    <div
                      key={service.key}
                      className={cn(
                        'rounded-2xl border p-4 transition-all duration-200 hover:-translate-y-0.5',
                        STATUS_STYLES[service.status]
                      )}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <p className="font-semibold">{service.name}</p>
                        <span className={cn('status-dot', STATUS_DOT_STYLES[service.status])} />
                      </div>
                      <p className="mt-3 text-sm leading-6">{service.detail}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white animate-rise-in">
                <div className="flex items-center justify-between border-b border-gray-100 px-6 py-5">
                  <div>
                    <h2 className="flex items-center gap-2 text-lg font-bold text-gray-900">
                      <Database className="h-5 w-5 text-primary-600" />
                      最近知识库
                    </h2>
                    <p className="mt-1 text-sm text-gray-500">优先关注最近有变更的知识库与文档规模。</p>
                  </div>
                  <Link to="/admin/knowledge" className="text-sm font-semibold text-primary-700 transition-colors hover:text-primary-800">
                    查看全部
                  </Link>
                </div>
                {overview.recent_knowledge_bases.length === 0 ? (
                  <div className="px-6 py-14 text-center text-sm text-gray-500">
                    当前还没有知识库，先创建一个知识库并上传文档。
                  </div>
                ) : (
                  <div className="divide-y divide-gray-100">
                    {overview.recent_knowledge_bases.map((kb) => (
                      <Link
                        key={kb.id}
                        to="/admin/knowledge"
                        className="flex flex-col gap-3 px-6 py-5 transition-colors hover:bg-gray-50 sm:flex-row sm:items-center sm:justify-between"
                      >
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="rounded-full bg-primary-50 px-2.5 py-1 text-xs font-semibold text-primary-700">
                              {kb.embedding_model}
                            </span>
                            <span className="text-xs text-gray-400">
                              更新于 {formatDateTime(kb.updated_at)}
                            </span>
                          </div>
                          <p className="mt-3 truncate text-base font-semibold text-gray-900">{kb.name}</p>
                          <p className="mt-1 truncate text-sm text-gray-500">{kb.description || '暂无描述'}</p>
                        </div>
                        <div className="grid grid-cols-2 gap-3 sm:min-w-[13rem]">
                          <div className="rounded-2xl bg-gray-50 px-4 py-3">
                            <p className="text-xs text-gray-500">文档</p>
                            <p className="mt-1 text-lg font-bold text-gray-900">{kb.document_count}</p>
                          </div>
                          <div className="rounded-2xl bg-gray-50 px-4 py-3">
                            <p className="text-xs text-gray-500">切片</p>
                            <p className="mt-1 text-lg font-bold text-gray-900">{kb.chunk_count}</p>
                          </div>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-6">
              <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white animate-rise-in">
                <div className="border-b border-gray-100 px-6 py-5">
                  <h2 className="flex items-center gap-2 text-lg font-bold text-gray-900">
                    <HardDrive className="h-5 w-5 text-primary-600" />
                    向量运行时
                  </h2>
                  <p className="mt-1 text-sm text-gray-500">{overview.vector_runtime.message}</p>
                </div>
                <div className="space-y-4 p-6">
                  <div className="rounded-2xl bg-primary-50 p-4">
                    <p className="text-sm text-gray-500">目标地址</p>
                    <p className="mt-2 break-all text-base font-semibold text-gray-900">{overview.vector_runtime.target}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-2xl bg-gray-50 p-4">
                      <p className="text-xs text-gray-500">集合数</p>
                      <p className="mt-1 text-xl font-bold text-gray-900">{overview.vector_runtime.collection_count}</p>
                    </div>
                    <div className="rounded-2xl bg-gray-50 p-4">
                      <p className="text-xs text-gray-500">存储体积</p>
                      <p className="mt-1 text-xl font-bold text-gray-900">{overview.vector_runtime.storage_usage_label}</p>
                    </div>
                  </div>
                  <Link to="/admin/vector-databases" className="btn-secondary w-full">
                    管理向量数据库
                  </Link>
                </div>
              </div>

              <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white animate-rise-in">
                <div className="border-b border-gray-100 px-6 py-5">
                  <h2 className="flex items-center gap-2 text-lg font-bold text-gray-900">
                    <Activity className="h-5 w-5 text-primary-600" />
                    常用操作
                  </h2>
                </div>
                <div className="space-y-3 p-6">
                  <Link to="/admin/knowledge" className="flex items-center justify-between rounded-2xl border border-gray-200 px-4 py-4 transition-all hover:border-primary-200 hover:bg-primary-50/60">
                    <div>
                      <p className="font-semibold text-gray-900">上传文档并测试检索</p>
                      <p className="mt-1 text-sm text-gray-500">进入知识库页完成上传、搜索和结果验证。</p>
                    </div>
                    <ArrowRight className="h-4 w-4 text-gray-400" />
                  </Link>
                  <Link to="/admin/settings" className="flex items-center justify-between rounded-2xl border border-gray-200 px-4 py-4 transition-all hover:border-primary-200 hover:bg-primary-50/60">
                    <div>
                      <p className="font-semibold text-gray-900">更新模型与 API 配置</p>
                      <p className="mt-1 text-sm text-gray-500">支持保存到共享 `.env` 并热重载 RAG 服务。</p>
                    </div>
                    <Shield className="h-4 w-4 text-gray-400" />
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default DashboardPage
