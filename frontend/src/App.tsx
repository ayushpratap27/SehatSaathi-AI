import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from './components/auth/ProtectedRoute'
import Layout from './components/layout/Layout'
import LoadingSpinner from './components/ui/LoadingSpinner'

// Lazy-loaded pages for code splitting
const LoginPage       = lazy(() => import('./pages/LoginPage'))
const RegisterPage    = lazy(() => import('./pages/RegisterPage'))
const DashboardPage   = lazy(() => import('./pages/DashboardPage'))
const UploadPage      = lazy(() => import('./pages/UploadPage'))
const ReportsPage     = lazy(() => import('./pages/ReportsPage'))
const ReportDetailPage = lazy(() => import('./pages/ReportDetailPage'))
const ChatPage        = lazy(() => import('./pages/ChatPage'))
const ProfilePage     = lazy(() => import('./pages/ProfilePage'))
const NotFoundPage    = lazy(() => import('./pages/NotFoundPage'))

const PageLoader = () => (
  <div className="min-h-screen flex items-center justify-center">
    <LoadingSpinner size="lg" />
  </div>
)

export default function App() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* Public routes */}
        <Route path="/login"    element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Authenticated routes inside shared Layout */}
        <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route index            element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/upload"    element={<UploadPage />} />
          <Route path="/reports"   element={<ReportsPage />} />
          <Route path="/reports/:id"       element={<ReportDetailPage />} />
          <Route path="/reports/:id/chat"  element={<ChatPage />} />
          <Route path="/profile"   element={<ProfilePage />} />
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  )
}
