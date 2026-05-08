import React, { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import ProtectedLayout from '@/components/ProtectedLayout'
import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'
import KnowledgePage from '@/pages/KnowledgePage'
import UsersPage from '@/pages/UsersPage'
import SettingsPage from '@/pages/SettingsPage'
import VectorDatabasesPage from '@/pages/VectorDatabasesPage'

const App: React.FC = () => {
  const { checkAuth, isAuthenticated } = useAuthStore()

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route
          path="/login"
          element={
            isAuthenticated ? <Navigate to="/admin" replace /> : <LoginPage />
          }
        />

        {/* Protected routes */}
        <Route element={<ProtectedLayout />}>
          <Route path="/admin" element={<DashboardPage />} />
          <Route path="/admin/knowledge" element={<KnowledgePage />} />
          <Route path="/admin/vector-databases" element={<VectorDatabasesPage />} />
          <Route path="/admin/users" element={<UsersPage />} />
          <Route path="/admin/settings" element={<SettingsPage />} />
        </Route>

        {/* Default redirect */}
        <Route path="/" element={<Navigate to="/admin" replace />} />
        <Route path="*" element={<Navigate to="/admin" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
