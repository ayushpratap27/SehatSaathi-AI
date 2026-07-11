import { useAuth } from '../context/AuthContext'
import Card from '../components/ui/Card'
import { format } from 'date-fns'
import { Shield } from 'lucide-react'

export default function ProfilePage() {
  const { user } = useAuth()
  if (!user) return null

  return (
    <div className="max-w-2xl space-y-6 animate-fade-in">
      <h1 className="text-[28px] font-medium text-[#001e2b]">Profile</h1>

      <Card>
        <div className="p-6 flex items-center gap-5">
          <div
            className="w-16 h-16 rounded-[16px] flex items-center justify-center flex-shrink-0"
            style={{ backgroundColor: '#00ed64' }}
          >
            <span className="text-2xl font-bold text-[#001e2b]">{user.username[0].toUpperCase()}</span>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-[#001e2b]">{user.full_name ?? user.username}</h2>
            <p className="text-[#5c6c7a] text-sm">{user.email}</p>
            <p className="text-xs text-[#a8b3bc] mt-1">Member since {format(new Date(user.created_at), 'MMMM yyyy')}</p>
          </div>
        </div>
      </Card>

      <Card title="Account Details">
        <dl className="space-y-0 p-6">
          {[
            { label: 'Username',       value: user.username },
            { label: 'Email',          value: user.email },
            { label: 'Full name',      value: user.full_name ?? '—' },
            { label: 'Account status', value: user.is_active ? 'Active' : 'Inactive' },
            { label: 'User ID',        value: user.id },
          ].map(({ label, value }) => (
            <div key={label} className="flex items-center justify-between py-3 border-b border-[#f4f7f6] last:border-0">
              <dt className="text-sm text-[#5c6c7a] font-medium">{label}</dt>
              <dd className="text-sm text-[#001e2b] font-mono text-xs">{value}</dd>
            </div>
          ))}
        </dl>
      </Card>

      <Card>
        <div className="p-6 flex items-center gap-3">
          <Shield className="w-5 h-5 flex-shrink-0" style={{ color: '#00684a' }} />
          <p className="text-sm text-[#5c6c7a]">Password management and account settings coming in a future update.</p>
        </div>
      </Card>
    </div>
  )
}
