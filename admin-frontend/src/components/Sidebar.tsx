import React from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Database,
  HardDrive,
  Users,
  Settings,
  ChevronLeft,
  Sparkles,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useState } from 'react'

const navigation = [
  { name: '仪表盘', href: '/admin', icon: LayoutDashboard },
  { name: '知识库', href: '/admin/knowledge', icon: Database },
  { name: '向量数据库', href: '/admin/vector-databases', icon: HardDrive },
  { name: '用户管理', href: '/admin/users', icon: Users },
  { name: '系统设置', href: '/admin/settings', icon: Settings },
]

const Sidebar: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()

  return (
    <aside
      className={cn(
        'flex flex-col h-full bg-white border-r border-gray-200 transition-all duration-300',
        collapsed ? 'w-20' : 'w-64'
      )}
    >
      {/* Logo */}
      <div className="flex items-center h-20 px-4 border-b border-gray-200">
        <div className={cn(
          'flex items-center gap-3 transition-all duration-300',
          collapsed && 'justify-center w-full'
        )}>
          <div className="relative">
            <div className="w-10 h-10 bg-dark rounded-xl flex items-center justify-center shadow-md animate-drift">
              <Sparkles className="w-5 h-5 text-primary-400" />
            </div>
          </div>
          {!collapsed && (
            <div>
              <span className="font-bold text-lg text-dark">RAG</span>
              <span className="font-bold text-lg text-primary-600 ml-1">Admin</span>
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href ||
            (item.href === '/admin' && location.pathname === '/admin')
          return (
            <NavLink
              key={item.name}
              to={item.href}
              className={cn(
                'group relative flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200',
                isActive
                  ? 'bg-primary-50 text-gray-900'
                  : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'
              )}
            >
              {isActive && (
                <span className="absolute left-1 top-1/2 h-6 w-1 -translate-y-1/2 rounded-full bg-primary-600" />
              )}
              <item.icon className={cn(
                'w-5 h-5 flex-shrink-0 transition-transform duration-200',
                isActive ? 'text-primary-600' : 'group-hover:scale-110'
              )} />
              {!collapsed && <span>{item.name}</span>}
            </NavLink>
          )
        })}
      </nav>

      {/* Collapse Button */}
      <div className="px-3 py-4 border-t border-gray-100">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className={cn(
            'flex items-center justify-center w-full rounded-2xl p-3 text-gray-400 hover:bg-gray-50 hover:text-gray-600 transition-all duration-200',
            collapsed && 'rotate-180'
          )}
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
      </div>
    </aside>
  )
}

export default Sidebar
