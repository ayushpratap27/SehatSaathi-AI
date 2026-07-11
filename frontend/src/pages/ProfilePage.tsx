import { useAuth } from '../context/AuthContext'
import Card from '../components/ui/Card'
import { format } from 'date-fns'
import { Shield, User } from 'lucide-react'

export default function ProfilePage() {
  const { user } = useAuth()
  if (!user) return null

  return (
    <div className="max-w-2xl space-y-6 animate-fade-in">
      <h1 className="text-2xl font-bold text-slate-900">Profile</h1>

      <Card>
        <div className="flex items-center gap-5">
          <div className="w-16 h-16 rounded-2xl bg-green-100 flex items-center justify-center flex-shrink-0">
            <span className="text-2xl font-bold text-green-700">{user.username[0].toUpperCase()}</span>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-900">{user.full_name ?? user.username}</h2>
            <p className="text-slate-500 text-sm">{user.email}</p>
            <p className="text-xs text-slate-400 mt-1">Member since {format(new Date(user.created_at), 'MMMM yyyy')}</p>
          </div>
        </div>
      </Card>

      <Card title="Account Details">
        <dl className="space-y-3 text-sm">
          {[
            { label: 'Username',  value: user.username },
            { label: 'Email',     value: user.email },
            { label: 'Full name', value: user.full_name ?? '—' },
            { label: 'Account status', value: user.is_active ? 'Active' : 'Inactive' },
            { label: 'User ID',   value: user.id },
          ].map(({ label, value }) => (
            <div key={label} className="flex items-center justify-between py-2 border-b border-slate-50 last:border-0">
              <dt className="text-slate-500 font-medium">{label}</dt>
              <dd className="text-slate-800 font-mono text-xs">{value}</dd>
            </div>
          ))}
        </dl>
      </Card>

      <Card>
        <div className="flex items-center gap-3 text-slate-500">
          <Shield className="w-5 h-5 text-green-500" />
          <p className="text-sm">Password management and account settings coming in a future update.</p>
        </div>
      </Card>
    </div>
  )
}
