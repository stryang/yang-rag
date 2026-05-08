import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Users as UsersIcon,
  Plus,
  Search,
  Edit2,
  Trash2,
  Shield,
  User as UserIcon,
  X,
  Loader2,
  AlertCircle,
  UserPlus,
  KeyRound,
  CheckCircle2,
} from 'lucide-react'
import Modal from '@/components/Modal'
import ConfirmDialog from '@/components/ConfirmDialog'
import { usersApi, User, UserCreate, UserUpdate } from '@/lib/api'
import { useAuthStore } from '@/stores/authStore'
import { cn } from '@/lib/utils'

type UserFormData = UserCreate & {
  is_active: boolean
}

type FeedbackState = {
  tone: 'success' | 'error'
  message: string
} | null

const DEFAULT_FORM: UserFormData = {
  username: '',
  email: '',
  password: '',
  role: 'user',
  is_active: true,
}

const UsersPage: React.FC = () => {
  const { user: currentUser } = useAuthStore()
  const navigate = useNavigate()

  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [modalLoading, setModalLoading] = useState(false)
  const [modalError, setModalError] = useState('')
  const [feedback, setFeedback] = useState<FeedbackState>(null)
  const [deleteTarget, setDeleteTarget] = useState<User | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [resetTarget, setResetTarget] = useState<User | null>(null)
  const [resetPassword, setResetPassword] = useState('')
  const [resetError, setResetError] = useState('')
  const [resetLoading, setResetLoading] = useState(false)
  const [formData, setFormData] = useState<UserFormData>(DEFAULT_FORM)

  useEffect(() => {
    if (currentUser?.role !== 'admin') {
      navigate('/admin')
      return
    }
    void fetchUsers()
  }, [currentUser, navigate])

  const fetchUsers = async () => {
    try {
      setLoading(true)
      const data = await usersApi.list(0, 100)
      setUsers(data.users)
    } catch (err) {
      console.error('Failed to fetch users:', err)
      setFeedback({ tone: 'error', message: '加载用户失败' })
    } finally {
      setLoading(false)
    }
  }

  const handleOpenModal = (user?: User) => {
    if (user) {
      setEditingUser(user)
      setFormData({
        username: user.username,
        email: user.email,
        password: '',
        role: user.role,
        is_active: user.is_active,
      })
    } else {
      setEditingUser(null)
      setFormData(DEFAULT_FORM)
    }
    setModalError('')
    setShowModal(true)
  }

  const handleCloseModal = () => {
    setShowModal(false)
    setEditingUser(null)
    setFormData(DEFAULT_FORM)
    setModalError('')
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setModalError('')

    if (!editingUser && !formData.password.trim()) {
      setModalError('密码不能为空')
      return
    }

    if (editingUser?.id === currentUser?.id && !formData.is_active) {
      setModalError('不能禁用当前登录中的管理员账户')
      return
    }

    try {
      setModalLoading(true)
      if (editingUser) {
        const updateData: UserUpdate = {
          username: formData.username,
          email: formData.email,
          role: formData.role,
          is_active: formData.is_active,
        }
        await usersApi.update(editingUser.id, updateData)
        setFeedback({ tone: 'success', message: `用户 ${formData.username} 已更新` })
      } else {
        await usersApi.create(formData)
        setFeedback({ tone: 'success', message: `用户 ${formData.username} 已创建` })
      }
      await fetchUsers()
      handleCloseModal()
    } catch (err: unknown) {
      const errorMessage =
        err && typeof err === 'object' && 'response' in err
          ? ((err as { response?: { data?: { detail?: string } } }).response?.data?.detail || '操作失败')
          : '操作失败'
      setModalError(errorMessage)
    } finally {
      setModalLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!deleteTarget) {
      return
    }

    try {
      setDeleting(true)
      await usersApi.delete(deleteTarget.id)
      await fetchUsers()
      setFeedback({ tone: 'success', message: `用户 ${deleteTarget.username} 已删除` })
      setDeleteTarget(null)
    } catch (err: unknown) {
      console.error('Failed to delete user:', err)
      const errorMessage =
        err && typeof err === 'object' && 'response' in err
          ? ((err as { response?: { data?: { detail?: string } } }).response?.data?.detail || '删除失败')
          : '删除失败'
      setFeedback({ tone: 'error', message: errorMessage })
    } finally {
      setDeleting(false)
    }
  }

  const openResetPasswordModal = (user: User) => {
    setResetTarget(user)
    setResetPassword('')
    setResetError('')
  }

  const closeResetPasswordModal = () => {
    setResetTarget(null)
    setResetPassword('')
    setResetError('')
  }

  const handleResetPassword = async (event: React.FormEvent) => {
    event.preventDefault()

    if (!resetTarget) {
      return
    }

    if (resetPassword.trim().length < 6) {
      setResetError('密码长度至少为 6 位')
      return
    }

    try {
      setResetLoading(true)
      await usersApi.resetPassword(resetTarget.id, resetPassword.trim())
      setFeedback({ tone: 'success', message: `用户 ${resetTarget.username} 的密码已更新` })
      closeResetPasswordModal()
    } catch (err: unknown) {
      console.error('Failed to reset password:', err)
      const errorMessage =
        err && typeof err === 'object' && 'response' in err
          ? ((err as { response?: { data?: { detail?: string } } }).response?.data?.detail || '密码重置失败')
          : '密码重置失败'
      setResetError(errorMessage)
    } finally {
      setResetLoading(false)
    }
  }

  const filteredUsers = users.filter(
    (user) =>
      user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.email.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="space-y-6 page-enter">
      {feedback && (
        <div className={cn(
          'flex items-center gap-3 rounded-2xl border p-4',
          feedback.tone === 'success'
            ? 'border-primary-200 bg-primary-50 text-primary-700'
            : 'border-red-200 bg-red-50 text-red-700'
        )}>
          {feedback.tone === 'success' ? (
            <CheckCircle2 className="h-5 w-5 flex-shrink-0" />
          ) : (
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
          )}
          <span className="flex-1">{feedback.message}</span>
          <button onClick={() => setFeedback(null)} className="rounded-xl p-1 transition-colors hover:bg-black/5">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">用户管理</h1>
          <p className="mt-1 text-gray-500">管理系统用户、角色和账户状态</p>
        </div>
        <button
          type="button"
          onClick={() => handleOpenModal()}
          className="inline-flex items-center gap-2 rounded-[1.1rem] bg-primary-600 px-5 py-2.5 font-semibold text-white shadow-md shadow-primary-600/15 transition-all duration-200 hover:-translate-y-0.5 hover:bg-primary-700 hover:shadow-lg"
        >
          <UserPlus className="h-5 w-5" />
          添加用户
        </button>
      </div>

      <div className="relative">
        <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="搜索用户..."
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
          className="w-full rounded-2xl border border-gray-200 bg-white py-3.5 pl-12 pr-4 text-gray-800 shadow-sm outline-none transition-all placeholder-gray-400 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
        />
      </div>

      <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm animate-rise-in" style={{ animationDelay: '120ms' }}>
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="relative">
              <div className="h-16 w-16 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600"></div>
              <UsersIcon className="absolute inset-0 m-auto h-6 w-6 animate-pulse text-primary-600" />
            </div>
            <p className="mt-4 text-gray-500">加载中...</p>
          </div>
        ) : filteredUsers.length === 0 ? (
          <div className="px-4 py-16 text-center">
            <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-gray-100">
              <UsersIcon className="h-10 w-10 text-gray-400" />
            </div>
            <h3 className="mb-2 text-lg font-semibold text-gray-900">没有找到用户</h3>
            <p className="mb-6 text-gray-500">尝试调整搜索条件或添加新用户</p>
            <button
              type="button"
              onClick={() => handleOpenModal()}
              className="inline-flex items-center gap-2 rounded-[1.1rem] bg-primary-600 px-5 py-2.5 font-semibold text-white shadow-md transition-all duration-200 hover:bg-primary-700"
            >
              <Plus className="h-4 w-4" />
              添加用户
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50">
                  <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-500">用户</th>
                  <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-500">角色</th>
                  <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-500">状态</th>
                  <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-500">创建时间</th>
                  <th className="px-6 py-4 text-right text-xs font-bold uppercase tracking-wider text-gray-500">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredUsers.map((user, index) => (
                  <tr key={user.id} className="animate-rise-in transition-colors hover:bg-gray-50" style={{ animationDelay: `${index * 40}ms` }}>
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="flex items-center gap-4">
                        <div className={cn(
                          'flex h-11 w-11 items-center justify-center rounded-xl shadow-md',
                          user.role === 'admin' ? 'bg-dark' : 'bg-primary-600'
                        )}>
                          {user.role === 'admin' ? (
                            <Shield className="h-5 w-5 text-primary-400" />
                          ) : (
                            <UserIcon className="h-5 w-5 text-white" />
                          )}
                        </div>
                        <div>
                          <p className="font-semibold text-gray-900">{user.username}</p>
                          <p className="text-sm text-gray-500">{user.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <span className={cn(
                        'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold',
                        user.role === 'admin' ? 'bg-gray-100 text-gray-800' : 'bg-primary-50 text-primary-700'
                      )}>
                        {user.role === 'admin' ? (
                          <><Shield className="h-3 w-3" /> 管理员</>
                        ) : (
                          <><UserIcon className="h-3 w-3" /> 用户</>
                        )}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <span className={cn(
                        'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold',
                        user.is_active ? 'bg-primary-50 text-primary-700' : 'bg-red-50 text-red-700'
                      )}>
                        <span className={cn(
                          'h-1.5 w-1.5 rounded-full',
                          user.is_active ? 'bg-primary-500' : 'bg-red-500'
                        )}></span>
                        {user.is_active ? '活跃' : '禁用'}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                      {new Date(user.created_at).toLocaleDateString('zh-CN')}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => handleOpenModal(user)}
                          className="rounded-2xl p-2.5 text-gray-400 transition-all duration-200 hover:bg-primary-50 hover:text-primary-600"
                          title="编辑"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => openResetPasswordModal(user)}
                          className="rounded-2xl p-2.5 text-gray-400 transition-all duration-200 hover:bg-amber-50 hover:text-amber-600"
                          title="重置密码"
                        >
                          <KeyRound className="h-4 w-4" />
                        </button>
                        {user.id !== currentUser?.id && (
                          <button
                            type="button"
                            onClick={() => setDeleteTarget(user)}
                            className="rounded-2xl p-2.5 text-gray-400 transition-all duration-200 hover:bg-red-50 hover:text-red-600"
                            title="删除"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showModal && (
        <Modal onClose={handleCloseModal} panelClassName="max-w-md">
          <div className="relative max-h-[inherit] overflow-y-auto rounded-[1.75rem] bg-white p-6 shadow-2xl">
            <div className="absolute left-0 right-0 top-0 h-1 rounded-t-[1.75rem] bg-gradient-to-r from-primary-500 via-primary-600 to-dark"></div>

            <div className="mb-6 mt-2 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary-600">
                  {editingUser ? <Edit2 className="h-5 w-5 text-white" /> : <UserPlus className="h-5 w-5 text-white" />}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">{editingUser ? '编辑用户' : '添加新用户'}</h3>
                  <p className="text-sm text-gray-500">{editingUser ? '更新角色、邮箱和状态' : '创建新的管理台账户'}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={handleCloseModal}
                className="rounded-2xl p-2 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {modalError && (
                <div className="flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-600">
                  <AlertCircle className="h-4 w-4 flex-shrink-0" />
                  {modalError}
                </div>
              )}

              <div>
                <label className="mb-2 block text-sm font-semibold text-gray-700">用户名</label>
                <input
                  type="text"
                  value={formData.username}
                  onChange={(event) => setFormData({ ...formData, username: event.target.value })}
                  className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                  required
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-semibold text-gray-700">邮箱</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(event) => setFormData({ ...formData, email: event.target.value })}
                  className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                  required
                />
              </div>

              {!editingUser && (
                <div>
                  <label className="mb-2 block text-sm font-semibold text-gray-700">初始密码</label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(event) => setFormData({ ...formData, password: event.target.value })}
                    className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                    required
                    minLength={6}
                  />
                </div>
              )}

              <div>
                <label className="mb-2 block text-sm font-semibold text-gray-700">角色</label>
                <select
                  value={formData.role}
                  onChange={(event) => setFormData({ ...formData, role: event.target.value as 'admin' | 'user' })}
                  className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                >
                  <option value="user">普通用户</option>
                  <option value="admin">管理员</option>
                </select>
              </div>

              {editingUser && (
                <div>
                  <label className="mb-2 block text-sm font-semibold text-gray-700">账户状态</label>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { value: true, label: '活跃', description: '允许登录和使用系统' },
                      { value: false, label: '禁用', description: '禁止登录但保留账户' },
                    ].map((option) => (
                      <button
                        key={String(option.value)}
                        type="button"
                        onClick={() => setFormData({ ...formData, is_active: option.value })}
                        className={cn(
                          'rounded-[1.15rem] border-2 p-4 text-left transition-all duration-200',
                          formData.is_active === option.value
                            ? 'border-primary-500 bg-primary-50'
                            : 'border-gray-200 bg-gray-50 hover:border-gray-300'
                        )}
                      >
                        <p className="font-semibold text-gray-900">{option.label}</p>
                        <p className="mt-1 text-sm text-gray-500">{option.description}</p>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="flex-1 rounded-[1.1rem] border border-gray-200 px-4 py-3 font-medium text-gray-700 transition-colors hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={modalLoading}
                  className="flex-1 rounded-[1.1rem] bg-primary-600 px-4 py-3 font-semibold text-white shadow-md shadow-primary-600/15 transition-all hover:bg-primary-700 disabled:opacity-50"
                >
                  {modalLoading ? (
                    <Loader2 className="mx-auto h-5 w-5 animate-spin" />
                  ) : editingUser ? (
                    '保存更改'
                  ) : (
                    '创建用户'
                  )}
                </button>
              </div>
            </form>
          </div>
        </Modal>
      )}

      {deleteTarget && (
        <ConfirmDialog
          title="删除用户"
          description={`确定要删除用户 “${deleteTarget.username}” 吗？此操作不可撤销。`}
          confirmText="确认删除"
          loading={deleting}
          tone="danger"
          onClose={() => setDeleteTarget(null)}
          onConfirm={handleDelete}
        />
      )}

      {resetTarget && (
        <Modal onClose={!resetLoading ? closeResetPasswordModal : undefined} closeOnBackdropClick={!resetLoading} panelClassName="max-w-md">
          <div className="relative max-h-[inherit] overflow-y-auto rounded-[1.75rem] bg-white p-6 shadow-2xl">
            <div className="absolute left-0 right-0 top-0 h-1 rounded-t-[1.75rem] bg-gradient-to-r from-amber-500 via-orange-500 to-red-500"></div>

            <div className="mb-6 mt-2 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-50 text-amber-600">
                  <KeyRound className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">重置密码</h3>
                  <p className="text-sm text-gray-500">为 {resetTarget.username} 设置一个新的登录密码</p>
                </div>
              </div>
              <button
                type="button"
                onClick={closeResetPasswordModal}
                disabled={resetLoading}
                className="rounded-2xl p-2 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 disabled:opacity-50"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleResetPassword} className="space-y-4">
              {resetError && (
                <div className="flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-600">
                  <AlertCircle className="h-4 w-4 flex-shrink-0" />
                  {resetError}
                </div>
              )}

              <div>
                <label className="mb-2 block text-sm font-semibold text-gray-700">新密码</label>
                <input
                  type="password"
                  value={resetPassword}
                  onChange={(event) => setResetPassword(event.target.value)}
                  className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                  minLength={6}
                  required
                  autoFocus
                />
                <p className="mt-2 text-xs text-gray-500">密码至少 6 位，提交后立即生效。</p>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={closeResetPasswordModal}
                  disabled={resetLoading}
                  className="flex-1 rounded-[1.1rem] border border-gray-200 px-4 py-3 font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:opacity-50"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={resetLoading}
                  className="flex-1 rounded-[1.1rem] bg-amber-600 px-4 py-3 font-semibold text-white shadow-md shadow-amber-600/15 transition-all hover:bg-amber-700 disabled:opacity-50"
                >
                  {resetLoading ? <Loader2 className="mx-auto h-5 w-5 animate-spin" /> : '确认重置'}
                </button>
              </div>
            </form>
          </div>
        </Modal>
      )}
    </div>
  )
}

export default UsersPage
