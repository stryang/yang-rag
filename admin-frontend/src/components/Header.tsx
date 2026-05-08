import React from 'react'
import { useNavigate } from 'react-router-dom'
import { LogOut, Bell } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import { useEffect, useState } from 'react'
import { DEFAULT_UI_PREFERENCES, getStoredUiPreferences, type AdminUiPreferences } from '@/lib/preferences'
import { systemApi } from '@/lib/api'
import { cn } from '@/lib/utils'

const Header: React.FC = () => {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [showNotifications, setShowNotifications] = useState(false)
  const [preferences, setPreferences] = useState<AdminUiPreferences>(DEFAULT_UI_PREFERENCES)
  const [systemState, setSystemState] = useState<{ label: string; tone: 'online' | 'warning' | 'offline' }>({
    label: '正在同步状态',
    tone: 'warning',
  })

  useEffect(() => {
    const syncPreferences = () => {
      setPreferences(getStoredUiPreferences())
    }

    syncPreferences()
    window.addEventListener('admin-ui-preferences-changed', syncPreferences)

    return () => {
      window.removeEventListener('admin-ui-preferences-changed', syncPreferences)
    }
  }, [])

  useEffect(() => {
    const syncSystemState = async () => {
      try {
        const overview = await systemApi.getOverview()
        const statuses = overview.services.map((item) => item.status)

        if (statuses.includes('offline')) {
          setSystemState({ label: '存在离线服务', tone: 'offline' })
          return
        }
        if (statuses.includes('warning')) {
          setSystemState({ label: '存在待处理告警', tone: 'warning' })
          return
        }
        setSystemState({ label: '系统运行正常', tone: 'online' })
      } catch {
        setSystemState({ label: '状态同步失败', tone: 'offline' })
      }
    }

    void syncSystemState()
  }, [])

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      {/* Left side */}
      <div className="flex items-center gap-4">
        <div className={cn(
          'hidden md:flex items-center gap-2 rounded-full border px-3 py-1.5 animate-fade-in',
          systemState.tone === 'online' && 'border-primary-100 bg-primary-50',
          systemState.tone === 'warning' && 'border-amber-100 bg-amber-50',
          systemState.tone === 'offline' && 'border-red-100 bg-red-50'
        )}>
          <div className={cn(
            'h-2 w-2 rounded-full',
            systemState.tone === 'online' && 'bg-primary-500 animate-pulse',
            systemState.tone === 'warning' && 'bg-amber-500',
            systemState.tone === 'offline' && 'bg-red-500'
          )}></div>
          <span className={cn(
            'text-xs font-medium',
            systemState.tone === 'online' && 'text-primary-700',
            systemState.tone === 'warning' && 'text-amber-700',
            systemState.tone === 'offline' && 'text-red-700'
          )}>
            {systemState.label}
          </span>
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-3">
        {/* Notifications */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative rounded-2xl p-2.5 text-gray-500 hover:bg-gray-50 hover:text-gray-700 transition-all duration-200"
          >
            <Bell className="w-5 h-5" />
            {preferences.notificationsEnabled && (
              <span className="absolute top-2 right-2 w-2 h-2 bg-primary-500 rounded-full border border-white"></span>
            )}
          </button>

          {/* Notification dropdown */}
          {showNotifications && (
            <div className="absolute right-0 top-full mt-2 w-80 bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden z-50 animate-scale-in">
              <div className="px-4 py-3 border-b border-gray-100">
                <h3 className="font-semibold text-gray-800">通知</h3>
              </div>
              <div className="p-4 text-center text-gray-400 text-sm">
                <Bell className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>{preferences.notificationsEnabled ? '暂无新通知' : '通知推送已关闭'}</p>
              </div>
            </div>
          )}
        </div>

        {/* User info */}
        <div className="flex items-center gap-3 pl-3 border-l border-gray-200">
          <div className="hidden sm:block text-right">
            <p className="text-sm font-semibold text-gray-800">{user?.username}</p>
            <p className="text-xs text-gray-500">
              {user?.role === 'admin' ? '管理员' : '普通用户'}
            </p>
          </div>

          <div className="relative">
            <div className="w-10 h-10 bg-dark rounded-xl flex items-center justify-center text-primary-400 font-bold shadow-md">
              {user?.username?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-primary-500 rounded-full border-2 border-white"></div>
          </div>
        </div>

        {/* Logout button */}
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 rounded-2xl px-3 py-2 text-sm text-gray-600 hover:bg-red-50 hover:text-red-600 transition-all duration-200"
        >
          <LogOut className="w-4 h-4" />
          <span className="hidden sm:inline">退出</span>
        </button>
      </div>
    </header>
  )
}

export default Header
