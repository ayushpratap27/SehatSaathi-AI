import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Activity, Eye, EyeOff, Loader2 } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const schema = z.object({
  email:    z.string().email('Enter a valid email'),
  password: z.string().min(1, 'Password is required'),
})
type Form = z.infer<typeof schema>

export default function LoginPage() {
  const { login } = useAuth()
  const [showPw, setShowPw]       = useState(false)
  const [serverError, setServerError] = useState('')
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<Form>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: Form) => {
    setServerError('')
    try {
      await login(data)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message
      setServerError(msg ?? 'Invalid email or password.')
    }
  }

  return (
    /* MongoDB: dark teal hero + bright-green accent */
    <div className="min-h-screen flex" style={{ backgroundColor: '#001e2b' }}>

      {/* ── Left panel: brand hero (hidden on xs) ── */}
      <div className="hidden lg:flex lg:w-1/2 flex-col items-start justify-center px-16">
        <div className="w-14 h-14 rounded-[12px] bg-[#00ed64] flex items-center justify-center mb-8">
          <Activity className="w-8 h-8 text-[#001e2b]" />
        </div>
        <h1 className="text-5xl font-medium text-white leading-tight mb-4">
          Understand your<br />
          <span style={{ color: '#00ed64' }}>medical reports</span><br />
          with AI.
        </h1>
        <p className="text-[#a8b3bc] text-lg leading-relaxed max-w-md">
          SehatSaathi-AI reads your lab results, flags anomalies, and answers your questions — grounded in your own data.
        </p>
      </div>

      {/* ── Right panel: form ─────────────────── */}
      <div className="flex-1 flex items-center justify-center px-4 sm:px-8 py-12">
        <div className="w-full max-w-md">

          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-[8px] bg-[#00ed64] flex items-center justify-center">
              <Activity className="w-6 h-6 text-[#001e2b]" />
            </div>
            <span className="text-lg font-bold text-white">SehatSaathi-AI</span>
          </div>

          {/* Card */}
          <div className="bg-white rounded-[16px] p-8 shadow-[0_8px_32px_rgba(0,0,0,0.24)]">
            <h2 className="text-2xl font-semibold text-[#001e2b] mb-1">Sign in</h2>
            <p className="text-[#5c6c7a] text-sm mb-7">Welcome back. Enter your details.</p>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              {serverError && (
                <div className="rounded-[8px] px-4 py-3 text-sm font-medium"
                  style={{ backgroundColor: '#fee2e2', color: '#b91c1c' }}>
                  {serverError}
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-[#001e2b] mb-1.5">Email address</label>
                <input
                  {...register('email')}
                  type="email"
                  autoComplete="email"
                  placeholder="you@example.com"
                  className="input-field"
                />
                {errors.email && <p className="mt-1.5 text-xs text-red-600">{errors.email.message}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-[#001e2b] mb-1.5">Password</label>
                <div className="relative">
                  <input
                    {...register('password')}
                    type={showPw ? 'text' : 'password'}
                    autoComplete="current-password"
                    placeholder="••••••••"
                    className="input-field pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPw((v) => !v)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[#a8b3bc] hover:text-[#5c6c7a] transition-colors"
                    aria-label={showPw ? 'Hide password' : 'Show password'}
                  >
                    {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {errors.password && <p className="mt-1.5 text-xs text-red-600">{errors.password.message}</p>}
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full btn-primary py-2.5 flex items-center justify-center gap-2"
              >
                {isSubmitting
                  ? <><Loader2 className="w-4 h-4 animate-spin" />Signing in…</>
                  : 'Sign in'}
              </button>
            </form>

            <p className="mt-6 text-center text-sm text-[#5c6c7a]">
              Don&apos;t have an account?{' '}
              <Link to="/register" className="font-semibold" style={{ color: '#00684a' }}>
                Create one
              </Link>
            </p>
          </div>

          <p className="mt-6 text-center text-xs text-[#5c6c7a]">
            For informational purposes only — not a substitute for medical advice.
          </p>
        </div>
      </div>
    </div>
  )
}
