import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Activity, Eye, EyeOff, Loader2 } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const schema = z.object({
  email:     z.string().email('Enter a valid email'),
  username:  z.string().min(3, 'At least 3 characters').max(50).regex(/^[a-zA-Z0-9_.-]+$/, 'Letters, digits, _ . - only'),
  full_name: z.string().max(255).optional(),
  password:  z.string().min(8, 'At least 8 characters')
    .regex(/[A-Z]/, 'Must contain an uppercase letter')
    .regex(/\d/, 'Must contain a digit'),
  confirm: z.string(),
}).refine((d) => d.password === d.confirm, { message: 'Passwords do not match', path: ['confirm'] })

type Form = z.infer<typeof schema>

export default function RegisterPage() {
  const { register: authRegister } = useAuth()
  const [showPw, setShowPw]           = useState<Record<string, boolean>>({})
  const [serverError, setServerError] = useState('')
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<Form>({
    resolver: zodResolver(schema),
  })

  const togglePw = (name: string) => setShowPw((prev) => ({ ...prev, [name]: !prev[name] }))

  const onSubmit = async ({ confirm: _c, ...data }: Form) => {
    setServerError('')
    try {
      await authRegister(data)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message
      setServerError(msg ?? 'Registration failed. Please try again.')
    }
  }

  return (
    <div className="min-h-screen flex" style={{ backgroundColor: '#001e2b' }}>

      {/* Left brand panel */}
      <div className="hidden lg:flex lg:w-1/2 flex-col items-start justify-center px-16">
        <div className="w-14 h-14 rounded-[12px] bg-[#00ed64] flex items-center justify-center mb-8">
          <Activity className="w-8 h-8 text-[#001e2b]" />
        </div>
        <h1 className="text-5xl font-medium text-white leading-tight mb-4">
          Join<br />
          <span style={{ color: '#00ed64' }}>SehatSaathi-AI</span>
        </h1>
        <p className="text-[#a8b3bc] text-lg leading-relaxed max-w-md">
          Upload your lab reports and get instant, AI-powered explanations — no medical jargon.
        </p>
      </div>

      {/* Right form panel */}
      <div className="flex-1 flex items-center justify-center px-4 sm:px-8 py-12">
        <div className="w-full max-w-md">

          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-[8px] bg-[#00ed64] flex items-center justify-center">
              <Activity className="w-6 h-6 text-[#001e2b]" />
            </div>
            <span className="text-lg font-bold text-white">SehatSaathi-AI</span>
          </div>

          <div className="bg-white rounded-[16px] p-8 shadow-[0_8px_32px_rgba(0,0,0,0.24)]">
            <h2 className="text-2xl font-semibold text-[#001e2b] mb-1">Create account</h2>
            <p className="text-[#5c6c7a] text-sm mb-7">Get started for free.</p>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {serverError && (
                <div className="rounded-[8px] px-4 py-3 text-sm font-medium"
                  style={{ backgroundColor: '#fee2e2', color: '#b91c1c' }}>
                  {serverError}
                </div>
              )}
              {([
                { name: 'email',     label: 'Email',                   type: 'email', placeholder: 'you@example.com' },
                { name: 'username',  label: 'Username',                 type: 'text',  placeholder: 'john_doe' },
                { name: 'full_name', label: 'Full name (optional)',      type: 'text',  placeholder: 'John Doe' },
              ] as const).map(({ name, label, type, placeholder }) => (
                <div key={name}>
                  <label className="block text-sm font-medium text-[#001e2b] mb-1.5">{label}</label>
                  <input {...register(name)} type={type} placeholder={placeholder} className="input-field" />
                  {errors[name] && <p className="mt-1.5 text-xs text-red-600">{errors[name]?.message}</p>}
                </div>
              ))}

              {/* Password fields with show/hide toggle */}
              {(['password', 'confirm'] as const).map((name) => (
                <div key={name}>
                  <label className="block text-sm font-medium text-[#001e2b] mb-1.5">
                    {name === 'password' ? 'Password' : 'Confirm password'}
                  </label>
                  <div className="relative">
                    <input
                      {...register(name)}
                      type={showPw[name] ? 'text' : 'password'}
                      placeholder="••••••••"
                      className="input-field pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => togglePw(name)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-[#a8b3bc] hover:text-[#5c6c7a] transition-colors"
                      aria-label={showPw[name] ? 'Hide password' : 'Show password'}
                    >
                      {showPw[name] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {errors[name] && <p className="mt-1.5 text-xs text-red-600">{errors[name]?.message}</p>}
                </div>
              ))}

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full btn-primary py-2.5 flex items-center justify-center gap-2 mt-2"
              >
                {isSubmitting
                  ? <><Loader2 className="w-4 h-4 animate-spin" />Creating account…</>
                  : 'Create account'}
              </button>
            </form>

            <p className="mt-6 text-center text-sm text-[#5c6c7a]">
              Already have an account?{' '}
              <Link to="/login" className="font-semibold" style={{ color: '#00684a' }}>Sign in</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
