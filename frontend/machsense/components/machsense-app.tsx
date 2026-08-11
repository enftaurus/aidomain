'use client'

import { useEffect, useMemo, useState } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { Activity, AlertTriangle, ArrowLeft, Bell, CheckCircle2, ChevronRight, CircleStop, Cpu, Factory, LineChart, LogOut, Menu, Plus, Radar, Search, Settings, Siren, Sparkles, Trash2, User, UserPlus, Wrench, X, Zap } from 'lucide-react'
import { LiveTimeSeries } from '@/components/live-time-series'
import { assess, appendEvent, createAlert, getNow, scheduleMaintenance, seedState, shutdownMachine, startMachine, stepTelemetry, updateMachineMode, type Machine, type MockState, type Role, type SimMode } from '@/lib/mock-service'
import { authApi } from '@/lib/api/auth'
import { alertsApi } from '@/lib/api/alerts'
import { machinesApi } from '@/lib/api/machines'
import { maintenanceApi } from '@/lib/api/maintenance'
import { engineersApi } from '@/lib/api/engineers'

type Props = { initialRole?: Role }

const nav = (role: Role) => role === 'admin'
  ? [['Dashboard', '/admin', Factory], ['Machines', '/admin/machines', Cpu], ['Engineers', '/admin/engineers', User], ['Alerts', '/admin/alerts', Siren], ['Maintenance', '/admin/maintenance', Wrench], ['Reports', '/admin/reports', LineChart]] as const
  : [['Dashboard', '/engineer', Factory], ['My Machines', '/engineer/machines', Cpu], ['Alerts', '/engineer/alerts', Siren], ['Maintenance', '/engineer/maintenance', Wrench], ['Reports', '/engineer/reports', LineChart]] as const

// Configured System Accounts
const DEMO_ACCOUNTS = {
  admin: { email: '1602-24-733-160@vce.ac.in', pass: 'admin123', name: 'Plant Admin Manager' },
  engineer: { email: '1602-24-748-062@vce.ac.in', pass: 'engineer123', name: 'Lead Reliability Engineer' },
}

// Default Engineer Assignments
type Assignment = { machineId: string; engineerName: string; engineerEmail: string }
const initialAssignments: Assignment[] = [
  { machineId: 'M-001', engineerName: 'Lead Reliability Engineer', engineerEmail: '1602-24-748-062@vce.ac.in' },
  { machineId: 'M-002', engineerName: 'Lead Reliability Engineer', engineerEmail: '1602-24-748-062@vce.ac.in' },
  { machineId: 'M-003', engineerName: 'Lead Reliability Engineer', engineerEmail: '1602-24-748-062@vce.ac.in' },
  { machineId: 'M-004', engineerName: 'Lead Reliability Engineer', engineerEmail: '1602-24-748-062@vce.ac.in' },
]

const ENGINEER_LIST = [
  { id: 'eng-1', name: 'Lead Reliability Engineer', email: '1602-24-748-062@vce.ac.in', role: 'Lead Reliability Engineer', phone: '+91 98765 43210' },
]

function Logo({ role, onClick }: { role?: Role; onClick?: () => void }) {
  return (
    <button className="flex items-center gap-3" onClick={onClick} aria-label="MachSense home">
      <span className="brand-mark"><Radar className="size-5" /></span>
      <span className="text-lg font-semibold tracking-tight">Mach<span className="text-primary">Sense</span></span>
    </button>
  )
}

function Badge({ status }: { status: string }) {
  return <span className={`status-badge ${status.toLowerCase()}`}><span className="status-dot" />{status}</span>
}

function Modal({ title, children, onClose }: { title: string; children: React.ReactNode; onClose: () => void }) {
  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true">
        <div className="modal-header">
          <h2>{title}</h2>
          <button className="icon-button" onClick={onClose} aria-label="Close dialog"><X /></button>
        </div>
        {children}
      </div>
    </div>
  )
}

function Login() {
  const router = useRouter()
  const [email, setEmail] = useState(DEMO_ACCOUNTS.admin.email)
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState('')

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    const isAdmin = email === DEMO_ACCOUNTS.admin.email && password === 'admin123'
    const isEngineer = email === DEMO_ACCOUNTS.engineer.email && password === 'engineer123'
    const role: Role | null = isAdmin ? 'admin' : isEngineer ? 'engineer' : null
    
    if (!role) return setError('Invalid credentials. Access restricted to 1602-24-733-160@vce.ac.in and 1602-24-748-062@vce.ac.in.')

    // Attempt real backend authentication
    try {
      const res = await authApi.login(email, password)
      if (res?.access_token) {
        authApi.saveToken(res.access_token)
      }
    } catch (err) {
      console.warn('Backend login fallback:', err)
    }

    sessionStorage.setItem('machsense-role', role)
    sessionStorage.setItem('machsense-user-email', email)
    router.push(`/${role}`)
  }

  return (
    <main className="login-page">
      <div className="login-card">
        <Logo onClick={() => router.push('/')} />
        <div className="eyebrow"><span className="pulse-dot" /> MachSense Portal</div>
        <h1>Predict before failure.</h1>
        <p>Decide with confidence.</p>
        <form onSubmit={submit} className="login-form">
          <label className="field-label">
            Email
            <input className="field-input" value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>
          <label className="field-label">
            Password
            <input className="field-input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
          {error && <div className="modal-callout critical"><AlertTriangle className="size-4" />{error}</div>}
          <button className="button primary full" type="submit">Sign In <ChevronRight className="size-4" /></button>
        </form>
        <div className="demo-accounts">
          <strong>Quick Login Accounts</strong>
          <button onClick={() => { setEmail(DEMO_ACCOUNTS.admin.email); setPassword('admin123') }}>
            Admin <span>{DEMO_ACCOUNTS.admin.email}</span>
          </button>
          <button onClick={() => { setEmail(DEMO_ACCOUNTS.engineer.email); setPassword('engineer123') }}>
            Engineer <span>{DEMO_ACCOUNTS.engineer.email}</span>
          </button>
        </div>
      </div>
    </main>
  )
}

function Landing() {
  const router = useRouter()
  return (
    <main className="landing">
      <div className="landing-nav">
        <Logo />
        <button className="button secondary" onClick={() => router.push('/login')}>Explore Dashboard <ChevronRight className="size-4" /></button>
      </div>
      <div className="landing-grid">
        <section className="landing-copy">
          <div className="eyebrow"><span className="pulse-dot" /> Industrial intelligence, made accountable</div>
          <h1>Know what your machines are telling you.</h1>
          <p>MachSense turns noisy industrial signals into clear, explainable decisions — before downtime becomes a crisis.</p>
          <div className="landing-actions">
            <button className="button primary large" onClick={() => router.push('/login')}>Explore Dashboard <ChevronRight className="size-4" /></button>
            <button className="button ghost large" onClick={() => document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })}>See How It Works</button>
          </div>
        </section>
        <section className="hero-visual">
          <div className="hero-console">
            <div className="console-top"><span>LIVE / NORTHSTAR FACTORY</span><span>4 MACHINES ONLINE</span></div>
            <div className="console-body">
              <div className="eyebrow">Fleet signal map</div>
              <h2>Operational clarity</h2>
              <div className="console-radar">
                <div className="radar-ring one" /><div className="radar-ring two" /><div className="radar-sweep" />
                <div className="radar-node n1" /><div className="radar-node n2" /><div className="radar-node n3" />
              </div>
            </div>
          </div>
        </section>
      </div>
      <section id="how-it-works" className="landing-footer">
        <span>01 · Detect</span><span>02 · Explain</span><span>03 · Decide</span>
        <strong>AI detects. Humans decide.</strong>
      </section>
    </main>
  )
}

function MachineCard({
  machine, engineer, role, onClick, onDelete
}: {
  machine: Machine;
  engineer?: Assignment;
  role: Role;
  onClick: () => void;
  onDelete?: (e: React.MouseEvent) => void;
}) {
  return (
    <div className="panel machine-detail-card relative group cursor-pointer" onClick={onClick}>
      <div className="w-full text-left">
        <div className="flex items-start justify-between gap-3">
          <div className={`machine-icon ${machine.status.toLowerCase()}`}><Cpu className="size-5" /></div>
          <div className="flex items-center gap-2">
            <Badge status={machine.status} />
            {role === 'admin' && onDelete && (
              <button
                type="button"
                onClick={onDelete}
                className="p-1 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 rounded transition-colors"
                title={`Delete machine ${machine.id}`}
              >
                <Trash2 className="size-4" />
              </button>
            )}
          </div>
        </div>

        <div className="machine-detail-main mt-3">
          <strong className="text-sm font-mono text-primary">{machine.id}</strong>
          <h2 className="text-lg font-semibold">{machine.name}</h2>
          <p className="text-xs text-muted-foreground">{machine.line}</p>
          <div className="machine-stats mt-3">
            <span>Health <b>{machine.health}%</b></span>
            <span>RMS <b>{machine.telemetry.at(-1)?.rms.toFixed(2)} mm/s</b></span>
            <span>Temp <b>{machine.telemetry.at(-1)?.temperature.toFixed(1)}°C</b></span>
          </div>
          {engineer && (
            <div className="mt-3 text-xs text-muted-foreground flex items-center gap-1 border-t border-border/40 pt-2">
              <User className="size-3 text-primary" /> Assigned: <span className="text-foreground font-medium">{engineer.engineerName}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function Workspace({ role }: { role: Role }) {
  const router = useRouter()
  const pathname = usePathname()
  const [state, setState] = useState<MockState>(() => seedState())
  const [assignments, setAssignments] = useState<Assignment[]>(initialAssignments)
  const [mockStreamOn, setMockStreamOn] = useState(false)
  const [mobileNav, setMobileNav] = useState(false)
  const [alertOpen, setAlertOpen] = useState(false)
  const [maintenanceOpen, setMaintenanceOpen] = useState(false)
  const [shutdownOpen, setShutdownOpen] = useState(false)
  const [assignModalOpen, setAssignModalOpen] = useState(false)
  const [addMachineModalOpen, setAddMachineModalOpen] = useState(false)
  const [notificationsOpen, setNotificationsOpen] = useState(false)
  const [selectedId, setSelectedId] = useState('M-001')

  const current = state.machines.find((m) => m.id === selectedId) ?? state.machines[0]
  const detailId = pathname.match(/machines\/([^/]+)/)?.[1]
  const detailMachine = state.machines.find((m) => m.id === detailId) ?? current
  const activeMachine = detailMachine

  const pageTitle = pathname.includes('alerts') ? 'Alerts'
    : pathname.includes('maintenance') ? 'Maintenance'
    : pathname.includes('reports') ? 'Reports'
    : pathname.includes('engineers') ? 'Engineers'
    : pathname.includes('machines') ? 'Machines'
    : 'Dashboard'

  // Sync real machine status from FastAPI backend
  useEffect(() => {
    async function syncBackendMachines() {
      try {
        const loginEmail = role === 'admin' ? DEMO_ACCOUNTS.admin.email : DEMO_ACCOUNTS.engineer.email
        const loginPass = role === 'admin' ? DEMO_ACCOUNTS.admin.pass : DEMO_ACCOUNTS.engineer.pass
        try {
          const authRes = await authApi.login(loginEmail, loginPass)
          authApi.saveToken(authRes.access_token)
        } catch (e) {}

        const backendMachines = await machinesApi.list()
        if (backendMachines && backendMachines.length > 0) {
          setState((s) => ({
            ...s,
            machines: s.machines.map((localM) => {
              const remote = backendMachines.find(bm => bm.machine_code === localM.id || bm.id === parseInt(localM.id.replace(/\D/g, '')))
              if (remote) {
                return {
                  ...localM,
                  status: (remote.status as MachineStatus) || localM.status,
                  health: remote.health_score ?? localM.health,
                }
              }
              return localM
            })
          }))
        }
      } catch (err) {
        console.warn('[MachSense] Backend machine sync fallback:', err)
      }
    }
    syncBackendMachines()
  }, [role, pathname])

  useEffect(() => {
    if (!mockStreamOn) return
    const timer = window.setInterval(() => {
      setState((s) => ({
        ...s,
        machines: s.machines.map((m) => {
          if (m.status === 'STOPPED') return m
          const mode = m.id === 'M-001' ? s.mode : 'normal'
          const next = stepTelemetry(m.telemetry.at(-1)!, mode)
          const confidence = assess(next)
          return {
            ...m,
            telemetry: [...m.telemetry.slice(-59), next],
            status: m.id === 'M-001' ? (confidence.level === 'HIGH' ? 'CRITICAL' : confidence.level === 'MEDIUM' ? 'WARNING' : 'RUNNING') : m.status
          }
        })
      }))
    }, 850)
    return () => clearInterval(timer)
  }, [mockStreamOn, state.mode])

  const go = (path: string) => { router.push(path); setMobileNav(false) }
  const machinePath = (id: string) => `/${role}/machines/${id}`
  const logout = () => {
    sessionStorage.removeItem('machsense-role')
    sessionStorage.removeItem('machsense-user-email')
    router.push('/login')
  }

  const setMode = (mode: SimMode) => setState((s) => updateMachineMode(s, mode))
  const selectedTelemetry = activeMachine.telemetry.at(-1)!
  const ai = assess(selectedTelemetry)

  const raiseAlert = async () => {
    setState((s) => createAlert(s, activeMachine.id, `${ai.fault}; RMS ${selectedTelemetry.rms.toFixed(2)} mm/s and kurtosis ${selectedTelemetry.kurtosis.toFixed(1)}.`, role === 'admin' ? 'Admin' : 'Engineer'))
    setAlertOpen(false)

    try {
      const loginEmail = role === 'admin' ? DEMO_ACCOUNTS.admin.email : DEMO_ACCOUNTS.engineer.email
      const loginPass = role === 'admin' ? DEMO_ACCOUNTS.admin.pass : DEMO_ACCOUNTS.engineer.pass
      try {
        const authRes = await authApi.login(loginEmail, loginPass)
        authApi.saveToken(authRes.access_token)
      } catch (e) {}

      const numId = parseInt(activeMachine.id.replace(/\D/g, '')) || 1
      await alertsApi.create({
        machine_id: numId,
        severity: 'HIGH',
        alert_type: 'VIBRATION',
        title: `${role === 'admin' ? 'Admin' : 'Engineer'} Alert — ${activeMachine.id}`,
        description: `Suspicious condition on ${activeMachine.name}: ${ai.fault}. RMS ${selectedTelemetry.rms.toFixed(2)} mm/s, kurtosis ${selectedTelemetry.kurtosis.toFixed(1)}.`,
        confidence: ai.confidence,
        evidence: `RMS ${selectedTelemetry.rms.toFixed(2)} mm/s; Kurtosis ${selectedTelemetry.kurtosis.toFixed(1)}`,
        recommended_action: role === 'admin' ? 'Inspect machine immediately' : 'Review machine telemetry baseline'
      })
      console.log('[MachSense] Backend alert API successfully invoked -> AI PDF report & email sent!')
    } catch (err) {
      console.error('[MachSense] Failed to trigger backend alert API:', err)
    }
  }

  const confirmShutdown = async () => {
    setState((s) => shutdownMachine(s, activeMachine.id, role === 'admin' ? 'Admin' : 'Engineer'))
    setShutdownOpen(false)

    try {
      const loginEmail = role === 'admin' ? DEMO_ACCOUNTS.admin.email : DEMO_ACCOUNTS.engineer.email
      const loginPass = role === 'admin' ? DEMO_ACCOUNTS.admin.pass : DEMO_ACCOUNTS.engineer.pass
      try {
        const authRes = await authApi.login(loginEmail, loginPass)
        authApi.saveToken(authRes.access_token)
      } catch (e) {}

      const numId = parseInt(activeMachine.id.replace(/\D/g, '')) || 1
      await machinesApi.shutdown(numId, {
        reason: `Manual shutdown initiated by ${role === 'admin' ? 'Admin' : 'Engineer'} for ${activeMachine.name}`,
        confirmed: true,
      })
      console.log('[MachSense] Backend shutdown API successfully invoked -> audit log & email sent!')
    } catch (err) {
      console.error('[MachSense] Failed to trigger backend shutdown API:', err)
    }
  }

  const userEmail = typeof window !== 'undefined' ? (sessionStorage.getItem('machsense-user-email') || (role === 'admin' ? DEMO_ACCOUNTS.admin.email : DEMO_ACCOUNTS.engineer.email)) : ''

  const assignEngineerToMachine = (machineId: string, engineerEmail: string) => {
    const eng = ENGINEER_LIST.find(e => e.email === engineerEmail)
    if (!eng) return
    setAssignments(prev => [
      ...prev.filter(a => a.machineId !== machineId),
      { machineId, engineerName: eng.name, engineerEmail: eng.email }
    ])
    setAssignModalOpen(false)
  }

  const handleAddMachine = async (newM: { code: string; name: string; location: string; type: string }) => {
    const createdM: Machine = {
      id: newM.code,
      name: newM.name,
      line: newM.location,
      status: 'RUNNING',
      health: 100,
      baseline: { rms: [1.4, 1.8], temperature: [50, 58], rpm: [1475, 1495], kurtosis: [2.8, 3.4] },
      telemetry: Array.from({ length: 60 }, (_, i) => ({
        timestamp: Date.now() - (59 - i) * 1000,
        rpm: 1485,
        temperature: 54,
        rms: 1.7,
        kurtosis: 3.2,
      }))
    }
    setState(s => ({ ...s, machines: [...s.machines, createdM] }))
    setAddMachineModalOpen(false)

    try {
      const loginEmail = DEMO_ACCOUNTS.admin.email
      const loginPass = DEMO_ACCOUNTS.admin.pass
      try {
        const authRes = await authApi.login(loginEmail, loginPass)
        authApi.saveToken(authRes.access_token)
      } catch (e) {}

      await machinesApi.create({
        machine_code: newM.code,
        name: newM.name,
        location: newM.location,
        machine_type: newM.type,
      })
    } catch (e) {
      console.warn('Backend machine create warning:', e)
    }
  }

  const handleDeleteMachine = async (machineId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!window.confirm(`Delete machine ${machineId}? This action cannot be undone.`)) return
    setState(s => ({ ...s, machines: s.machines.filter(m => m.id !== machineId) }))

    try {
      const numId = parseInt(machineId.replace(/\D/g, '')) || 1
      await machinesApi.delete(numId)
    } catch (err) {
      console.warn('Backend machine delete warning:', err)
    }
  }

  const handleStartMachine = async () => {
    setState((s) => startMachine(s, activeMachine.id, role === 'admin' ? 'Admin' : 'Engineer'))
    try {
      const loginEmail = role === 'admin' ? DEMO_ACCOUNTS.admin.email : DEMO_ACCOUNTS.engineer.email
      const loginPass = role === 'admin' ? DEMO_ACCOUNTS.admin.pass : DEMO_ACCOUNTS.engineer.pass
      try {
        const authRes = await authApi.login(loginEmail, loginPass)
        authApi.saveToken(authRes.access_token)
      } catch (e) {}

      const numId = parseInt(activeMachine.id.replace(/\D/g, '')) || 1
      await machinesApi.start(numId)
      console.log('[MachSense] Backend start machine API successfully invoked!')
    } catch (err) {
      console.error('[MachSense] Failed to trigger backend machine start API:', err)
    }
  }

  const page = detailId ? (
    <MachineDetail
      machine={activeMachine}
      ai={ai}
      assignment={assignments.find(a => a.machineId === activeMachine.id)}
      onBack={() => go(`/${role}/machines`)}
      onAlert={() => setAlertOpen(true)}
      onShutdown={() => setShutdownOpen(true)}
      onStart={handleStartMachine}
    />
  ) : (
    <PageContent
      title={pageTitle}
      role={role}
      state={state}
      current={current}
      assignments={assignments}
      mockStreamOn={mockStreamOn}
      onToggleMockStream={() => setMockStreamOn(!mockStreamOn)}
      onMachine={(id) => go(machinePath(id))}
      onMode={setMode}
      onAlert={() => setAlertOpen(true)}
      onMaintenance={() => setMaintenanceOpen(true)}
      onOpenAssignModal={() => setAssignModalOpen(true)}
      onOpenAddMachineModal={() => setAddMachineModalOpen(true)}
      onDeleteMachine={handleDeleteMachine}
    />
  )

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileNav ? 'mobile-open' : ''}`}>
        <div className="sidebar-top">
          <Logo role={role} onClick={() => go(`/${role}`)} />
          <button className="icon-button mobile-only" onClick={() => setMobileNav(false)} aria-label="Close navigation"><X /></button>
        </div>
        <div className="workspace-switcher">
          <div className="workspace-icon"><Factory className="size-4" /></div>
          <div>
            <div className="eyebrow">Workspace</div>
            <div className="font-medium">Northstar Factory</div>
          </div>
        </div>
        <nav className="nav-list" aria-label="Main navigation">
          {nav(role).map(([label, path, Icon]) => (
            <button key={path} className={`nav-item ${pathname === path ? 'active' : ''}`} onClick={() => go(path)}>
              <Icon className="size-4" />
              <span>{label}</span>
              {label === 'Alerts' && state.alerts.length > 0 && <span className="nav-count">{state.alerts.length}</span>}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <button className="nav-item" onClick={() => setNotificationsOpen(true)}>
            <Bell className="size-4" />
            <span>Notifications</span>
            {state.notifications.filter((n) => !n.read).length > 0 && (
              <span className="nav-count">{state.notifications.filter((n) => !n.read).length}</span>
            )}
          </button>
          <button className="nav-item" onClick={() => window.alert('Settings configured via backend API.')}>
            <Settings className="size-4" />
            <span>Settings</span>
          </button>
          <button className="user-card" onClick={logout}>
            <div className="avatar">{role === 'admin' ? 'AD' : 'EG'}</div>
            <div className="min-w-0 text-left">
              <div className="truncate text-sm font-medium">{role === 'admin' ? 'Plant Admin' : 'Field Engineer'}</div>
              <div className="truncate text-xs text-muted-foreground">{userEmail}</div>
            </div>
            <LogOut className="ml-auto size-4 text-muted-foreground" />
          </button>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <button className="icon-button mobile-only" onClick={() => setMobileNav(true)} aria-label="Open navigation"><Menu /></button>
          <div className="breadcrumb">
            <span>Northstar Factory</span>
            <ChevronRight className="size-3" />
            <strong>{pageTitle}</strong>
            {detailId && <><ChevronRight className="size-3" /><strong>{detailId}</strong></>}
          </div>

          <div className="topbar-actions">
            <div className="simulation-control flex items-center gap-2">
              <button
                className={`button ${mockStreamOn ? 'primary' : 'secondary'} text-xs py-1 px-2.5`}
                onClick={() => setMockStreamOn(!mockStreamOn)}
                title="Turn on/off continuous fake data simulation"
              >
                <span className={`pulse-dot ${mockStreamOn ? 'bg-emerald-400' : 'bg-slate-400'}`} />
                Mock Stream: <strong>{mockStreamOn ? 'ON' : 'OFF'}</strong>
              </button>

              {mockStreamOn && (
                <select value={state.mode} onChange={(e) => setMode(e.target.value as SimMode)} aria-label="Simulation mode" className="text-xs py-1">
                  <option value="normal">Normal</option>
                  <option value="warning">Simulate Warning</option>
                  <option value="critical">Simulate Critical</option>
                </select>
              )}
            </div>

            <button className="icon-button" onClick={() => setNotificationsOpen((v) => !v)} aria-label="Open notifications">
              <Bell className="size-4" />
              {state.notifications.some((n) => !n.read) && <span className="notification-dot" />}
            </button>
          </div>
        </header>

        <div className="content-wrap">
          <div className="page-heading">
            <div>
              <div className="eyebrow">{role === 'admin' ? 'Plant administration' : 'Reliability engineering'} · Updated {getNow()}</div>
              <h1>{detailId ? `${activeMachine.id} · ${activeMachine.name}` : pageTitle}</h1>
              <p>{detailId ? 'Live telemetry and explainable signal analysis' : 'AI detects. AI explains. Humans decide.'}</p>
            </div>
            {!detailId && (
              <div className="heading-actions flex gap-2">
                {role === 'admin' ? (
                  <>
                    <button className="button primary" onClick={() => setAlertOpen(true)}>
                      <Siren className="size-4" /> Send Mail to Engineers
                    </button>
                    <button className="button secondary" onClick={() => setAddMachineModalOpen(true)}>
                      <Plus className="size-4" /> Add Machine
                    </button>
                  </>
                ) : (
                  <button className="button primary" onClick={() => setAlertOpen(true)}>
                    <Siren className="size-4" /> Alert Factory
                  </button>
                )}
                <button className="button secondary" onClick={() => setMaintenanceOpen(true)}>
                  <Wrench className="size-4" /> Schedule Maintenance
                </button>
              </div>
            )}
          </div>
          {page}
        </div>
      </main>

      {alertOpen && <AlertModal role={role} machine={activeMachine} onClose={() => setAlertOpen(false)} onConfirm={raiseAlert} />}
      {maintenanceOpen && (
        <MaintenanceModal
          machine={activeMachine}
          onClose={() => setMaintenanceOpen(false)}
          onConfirm={async (item) => {
            setState((s) => scheduleMaintenance(s, item, role === 'admin' ? 'Admin' : 'Engineer'))
            setMaintenanceOpen(false)
            try {
              const loginEmail = role === 'admin' ? DEMO_ACCOUNTS.admin.email : DEMO_ACCOUNTS.engineer.email
              const loginPass = role === 'admin' ? DEMO_ACCOUNTS.admin.pass : DEMO_ACCOUNTS.engineer.pass
              try {
                const authRes = await authApi.login(loginEmail, loginPass)
                authApi.saveToken(authRes.access_token)
              } catch (e) {}

              const numId = parseInt(item.machineId.replace(/\D/g, '')) || 1
              await maintenanceApi.create({
                machine_id: numId,
                maintenance_type: item.type,
                description: item.notes || `Scheduled maintenance for ${item.machineId}`,
                factory_notes: item.notes,
              })
            } catch (err) {
              console.error('[MachSense] Failed to trigger backend maintenance API:', err)
            }
          }}
        />
      )}
      {shutdownOpen && <ShutdownModal machine={activeMachine} onClose={() => setShutdownOpen(false)} onConfirm={confirmShutdown} />}
      {assignModalOpen && (
        <AssignEngineerModal
          machines={state.machines}
          engineers={ENGINEER_LIST}
          onClose={() => setAssignModalOpen(false)}
          onConfirm={assignEngineerToMachine}
        />
      )}
      {addMachineModalOpen && (
        <AddMachineModal
          onClose={() => setAddMachineModalOpen(false)}
          onConfirm={handleAddMachine}
        />
      )}
      {notificationsOpen && (
        <NotificationPanel
          notifications={state.notifications}
          onClose={() => setNotificationsOpen(false)}
          onOpen={(href) => {
            setState((s) => ({ ...s, notifications: s.notifications.map((n) => ({ ...n, read: true })) }))
            setNotificationsOpen(false)
            go(href)
          }}
        />
      )}
    </div>
  )
}

function PageContent({
  title, role, state, current, assignments, mockStreamOn, onToggleMockStream, onMachine, onMode, onAlert, onMaintenance, onOpenAssignModal, onOpenAddMachineModal, onDeleteMachine
}: {
  title: string;
  role: Role;
  state: MockState;
  current: Machine;
  assignments: Assignment[];
  mockStreamOn: boolean;
  onToggleMockStream: () => void;
  onMachine: (id: string) => void;
  onMode: (mode: SimMode) => void;
  onAlert: () => void;
  onMaintenance: () => void;
  onOpenAssignModal: () => void;
  onOpenAddMachineModal: () => void;
  onDeleteMachine: (id: string, e: React.MouseEvent) => void;
}) {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')

  // ── 1. MACHINES PAGE ────────────────────────────────────────────────────────
  if (title === 'Machines' || title === 'My Machines') {
    const filteredMachines = state.machines.filter(m => {
      const matchesSearch = m.name.toLowerCase().includes(search.toLowerCase()) || m.id.toLowerCase().includes(search.toLowerCase())
      const matchesStatus = statusFilter === 'ALL' || m.status === statusFilter
      return matchesSearch && matchesStatus
    })

    return (
      <div className="space-y-6">
        {/* Machinery Filter & Management Toolbar */}
        <div className="panel p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3 flex-1 max-w-md bg-secondary/50 border border-border px-3 py-1.5 rounded-lg">
            <Search className="size-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search machinery by name or code..."
              className="bg-transparent text-xs w-full focus:outline-none"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs text-muted-foreground">Filter Status:</span>
            {['ALL', 'RUNNING', 'WARNING', 'CRITICAL', 'STOPPED'].map(st => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`text-xs px-2.5 py-1 rounded-full font-medium transition-colors ${statusFilter === st ? 'bg-primary text-primary-foreground' : 'bg-secondary hover:bg-secondary/80 text-secondary-foreground'}`}
              >
                {st}
              </button>
            ))}
          </div>

          {role === 'admin' && (
            <div className="flex items-center gap-2">
              <button className="button primary text-xs" onClick={onOpenAddMachineModal}>
                <Plus className="size-4" /> Add Machine
              </button>
              <button className="button secondary text-xs" onClick={onOpenAssignModal}>
                <UserPlus className="size-4" /> Assign Engineer
              </button>
            </div>
          )}
        </div>

        <section className="panel">
          <div className="panel-header">
            <div>
              <h2>Machinery Fleet Directory ({filteredMachines.length})</h2>
              <p>Comprehensive status, signal thresholds, and assigned engineers</p>
            </div>
          </div>

          {filteredMachines.length === 0 ? (
            <div className="empty-state p-8 text-center text-muted-foreground">
              No machines match your criteria. Try adjusting your search or filters.
            </div>
          ) : (
            <div className="machine-directory p-4">
              {filteredMachines.map((m) => (
                <MachineCard
                  key={m.id}
                  machine={m}
                  role={role}
                  engineer={assignments.find(a => a.machineId === m.id)}
                  onClick={() => onMachine(m.id)}
                  onDelete={(e) => onDeleteMachine(m.id, e)}
                />
              ))}
            </div>
          )}
        </section>
      </div>
    )
  }

  // ── 2. ENGINEERS PAGE ───────────────────────────────────────────────────────
  if (title === 'Engineers') {
    return (
      <div className="space-y-6">
        <div className="metric-grid">
          <Metric label="Active Engineers" value={String(ENGINEER_LIST.length).padStart(2, '0')} trend="on duty" />
          <Metric label="Assigned Machines" value={String(assignments.length).padStart(2, '0')} trend="active" />
          <Metric label="Unassigned Machines" value={String(Math.max(0, state.machines.length - assignments.length)).padStart(2, '0')} trend="unassigned" />
          <Metric label="Primary Support" value="VCE Engineers" trend="verified" />
        </div>

        <div className="panel table-panel">
          <div className="panel-header">
            <div>
              <h2>Engineer Staff & Machinery Assignments</h2>
              <p>Assigned personnel responsible for rotating machinery inspection and decisions</p>
            </div>
            {role === 'admin' && (
              <button className="button primary" onClick={onOpenAssignModal}>
                <UserPlus className="size-4" /> Assign Machine to Engineer
              </button>
            )}
          </div>

          <div className="space-y-4 p-4">
            {ENGINEER_LIST.map((eng) => {
              const engAssignments = assignments.filter(a => a.engineerEmail === eng.email)
              return (
                <div key={eng.id} className="p-4 border border-border/60 rounded-lg bg-card/40 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold text-sm">
                      {eng.name.split(' ').map(n => n[0]).join('')}
                    </div>
                    <div>
                      <h3 className="font-semibold text-base flex items-center gap-2">
                        {eng.name}
                        <span className="text-xs px-2 py-0.5 rounded bg-primary/10 text-primary font-normal">{eng.role}</span>
                      </h3>
                      <p className="text-xs text-muted-foreground font-mono">{eng.email} • {eng.phone}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs text-muted-foreground">Assigned Machines:</span>
                    {engAssignments.length === 0 ? (
                      <span className="text-xs text-amber-500 italic">No machines assigned</span>
                    ) : (
                      engAssignments.map(a => (
                        <button
                          key={a.machineId}
                          onClick={() => onMachine(a.machineId)}
                          className="px-2.5 py-1 rounded bg-secondary hover:bg-secondary/80 text-xs font-semibold flex items-center gap-1 border border-border"
                        >
                          <Cpu className="size-3 text-primary" /> {a.machineId}
                        </button>
                      ))
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    )
  }

  // ── 3. ALERTS PAGE ──────────────────────────────────────────────────────────
  if (title === 'Alerts') {
    return (
      <div className="panel table-panel">
        <div className="panel-header">
          <div>
            <h2>Alert Center</h2>
            <p>Human review is required for every escalation</p>
          </div>
        </div>
        <div className="alert-table">
          {state.alerts.length === 0 ? (
            <div className="empty-state">No alerts created yet. Turn on mock stream or simulate a condition to generate alerts.</div>
          ) : (
            state.alerts.map((a) => (
              <div className="alert-table-row" key={a.id}>
                <div className="alert-icon critical"><Siren className="size-4" /></div>
                <div className="alert-table-copy">
                  <strong>{a.title} · {a.machineId}</strong>
                  <span>{a.detail}</span>
                </div>
                <Badge status={a.level} />
                <button className="button secondary" onClick={onAlert}>
                  {role === 'admin' ? 'Send Mail to Engineers' : 'Alert Factory'}
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    )
  }

  // ── 4. MAINTENANCE PAGE ─────────────────────────────────────────────────────
  if (title === 'Maintenance') {
    return (
      <div className="dashboard-grid">
        <div className="panel table-panel">
          <div className="panel-header">
            <div>
              <h2>Maintenance Schedule</h2>
              <p>Planned work and human decisions</p>
            </div>
            <button className="button primary" onClick={onMaintenance}>Schedule Maintenance</button>
          </div>
          <div className="schedule-list">
            {state.maintenance.length === 0 ? (
              <div className="empty-state">No maintenance records yet.</div>
            ) : (
              state.maintenance.map((m) => (
                <div className="schedule-row" key={m.id}>
                  <div className="machine-icon healthy"><Wrench className="size-4" /></div>
                  <div>
                    <strong>{m.type}</strong>
                    <span>{m.machineId} · {m.date} · {m.time} · {m.engineer}</span>
                  </div>
                  <Badge status={m.priority} />
                </div>
              ))
            )}
          </div>
        </div>
        <div className="panel maintenance-score">
          <div className="eyebrow">Maintenance readiness</div>
          <strong>87%</strong>
          <p>Completing planned inspections reduces projected downtime risk.</p>
        </div>
      </div>
    )
  }

  // ── 5. REPORTS PAGE ─────────────────────────────────────────────────────────
  if (title === 'Reports') {
    return (
      <>
        <section className="metric-grid">
          <Metric label="Availability" value="98.1%" trend="+1.2%" />
          <Metric label="Incidents avoided" value="14" trend="+22%" />
          <Metric label="MTTR" value="3.8h" trend="-0.6h" />
          <Metric label="Work completed" value={`${Math.max(0, 92 - state.maintenance.length)}%`} trend="this month" />
        </section>
        <div className="panel report-panel">
          <div className="panel-header">
            <div>
              <h2>Reliability Performance</h2>
              <p>Rolling operational indicators across the fleet</p>
            </div>
            <button className="button secondary" onClick={() => window.alert('PDF report export requested from backend.')}>Export Report</button>
          </div>
          <div className="report-bars">
            {state.machines.map((m) => (
              <div className="report-bar-row" key={m.id}>
                <span>{m.id}</span>
                <div className="report-bar"><i style={{ width: `${m.health}%` }} /></div>
                <strong>{m.health}%</strong>
                <span>{m.status === 'RUNNING' ? 'On track' : 'Needs intervention'}</span>
              </div>
            ))}
          </div>
        </div>
      </>
    )
  }

  // ── 6. DASHBOARD PAGE (DEFAULT EXECUTIVE OVERVIEW) ──────────────────────────
  return (
    <>
      <section className="metric-grid">
        <Metric label="Fleet health" value={`${Math.round(state.machines.reduce((sum, m) => sum + m.health, 0) / (state.machines.length || 1))}%`} trend="+4.8%" />
        <Metric label="Active alerts" value={String(state.alerts.length).padStart(2, '0')} trend="human review" />
        <Metric label="Predicted uptime" value="98.1%" trend="+1.2%" />
        <Metric label="Maintenance due" value={String(state.maintenance.length).padStart(2, '0')} trend="planned" />
      </section>

      <section className="dashboard-grid lower">
        <div className="panel signal-panel">
          <div className="panel-header">
            <div>
              <h2>Live Plant Signal Monitor — {current.id}</h2>
              <p>Streaming telemetry compared to baseline</p>
            </div>
            <button className="button secondary" onClick={() => onMachine(current.id)}>Open machine command view</button>
          </div>
          <LiveTimeSeries machine={current} mode={current.status === 'CRITICAL' ? 'critical' : current.status === 'WARNING' ? 'warning' : 'normal'} />
        </div>

        <div className="panel ai-panel">
          <div className="ai-heading">
            <div className="ai-icon"><Sparkles className="size-5" /></div>
            <div>
              <div className="eyebrow">MachSense intelligence</div>
              <h2>{assess(current.telemetry.at(-1)!).label}</h2>
            </div>
          </div>
          <p className="ai-copy">AI explains the current signal pattern; a human decides the next step.</p>
          <button className="button primary full" onClick={onAlert}>
            <Siren className="size-4" /> {role === 'admin' ? 'Send Mail to Engineers' : 'Alert Factory'}
          </button>
        </div>
      </section>

      <div className="demo-controls border border-border/50 p-4 rounded-lg bg-card/30 flex flex-col md:flex-row items-center justify-between gap-3">
        <div>
          <strong className="block text-sm font-semibold">SIMULATION STREAM CONTROL</strong>
          <span className="text-xs text-muted-foreground">Mock Data Stream is currently <b>{mockStreamOn ? 'ENABLED (generating fake telemetry loop)' : 'OFF (Paused / Real Data Ready)'}</b></span>
        </div>
        <div className="flex items-center gap-2">
          <button className={`button ${mockStreamOn ? 'primary' : 'secondary'} text-xs`} onClick={onToggleMockStream}>
            {mockStreamOn ? 'Turn OFF Mock Stream' : 'Turn ON Mock Stream'}
          </button>
          {mockStreamOn && (
            <>
              <button className="button secondary text-xs" onClick={() => onMode('normal')}>Normal</button>
              <button className="button secondary text-xs" onClick={() => onMode('warning')}>Simulate Warning</button>
              <button className="button danger text-xs" onClick={() => onMode('critical')}>Simulate Critical</button>
            </>
          )}
        </div>
      </div>
    </>
  )
}

function Metric({ label, value, trend }: { label: string; value: string; trend: string }) {
  return (
    <div className="metric-card">
      <div className="metric-icon blue"><Activity className="size-4" /></div>
      <div className="metric-copy">
        <span>{label}</span>
        <strong>{value}</strong>
        <div><b>{trend}</b> <em>vs baseline</em></div>
      </div>
    </div>
  )
}

function MachineDetail({
  machine, ai, assignment, onBack, onAlert, onShutdown, onStart
}: {
  machine: Machine;
  ai: ReturnType<typeof assess>;
  assignment?: Assignment;
  onBack: () => void;
  onAlert: () => void;
  onShutdown: () => void;
  onStart: () => void;
}) {
  const current = machine.telemetry.at(-1)!
  return (
    <>
      <button className="button ghost" onClick={onBack}><ArrowLeft className="size-4" /> Back to Machines</button>
      <div className="detail-header flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="eyebrow">LIVE TELEMETRY · Updated {getNow()}</div>
          <h2>{machine.id} · {machine.name}</h2>
          <p>{machine.line} {assignment && `• Assigned to ${assignment.engineerName} (${assignment.engineerEmail})`}</p>
        </div>
        <Badge status={machine.status} />
      </div>

      <section className="metric-grid">
        <Metric label="RPM" value={current.rpm.toFixed(0)} trend="live" />
        <Metric label="Temperature" value={`${current.temperature.toFixed(1)}°C`} trend="live" />
        <Metric label="Vibration RMS" value={`${current.rms.toFixed(2)} mm/s`} trend={ai.level} />
        <Metric label="Kurtosis" value={current.kurtosis.toFixed(1)} trend="live" />
      </section>

      <div className="dashboard-grid lower">
        <div className="panel signal-panel">
          <div className="panel-header">
            <div>
              <h2>RPM / Temperature / RMS / Kurtosis</h2>
              <p>Rolling 60-s window · baseline region 1.4–2.0 mm/s</p>
            </div>
            <span className="live-chart-label"><i /> {machine.status === 'STOPPED' ? 'STOPPED · TELEMETRY PAUSED' : 'LIVE'}</span>
          </div>
          <LiveTimeSeries machine={machine} mode={machine.status === 'CRITICAL' ? 'critical' : machine.status === 'WARNING' ? 'warning' : 'normal'} />
          <div className="signal-legend">
            <span><i className="legend-dot blue" /> Actual RMS</span>
            <span><i className="legend-dot amber" /> Baseline</span>
            <span><i className="legend-line" /> Streaming now</span>
          </div>
        </div>

        <div className="panel ai-panel">
          <div className="ai-heading">
            <div className="ai-icon"><Sparkles className="size-5" /></div>
            <div>
              <div className="eyebrow">AI ASSESSMENT</div>
              <h2>{ai.fault}</h2>
            </div>
          </div>
          <p className="ai-copy"><strong>{ai.label}</strong> · {ai.confidence}% confidence. Evidence: RMS above baseline, kurtosis {current.kurtosis.toFixed(1)}, abnormal frequency peak.</p>
          <button className="button primary full" onClick={onAlert}><Siren className="size-4" /> Alert Factory</button>
          <button className="button danger full" onClick={machine.status === 'STOPPED' ? onStart : onShutdown}>
            {machine.status === 'STOPPED' ? <><Zap className="size-4" /> Start Machine</> : <><CircleStop className="size-4" /> Manual Shutdown</>}
          </button>
        </div>
      </div>

      <div className="panel timeline-panel">
        <div className="panel-header">
          <div>
            <h2>Timeline & Audit Log</h2>
            <p>Evidence and human actions on {machine.id}</p>
          </div>
          <span className="text-button">{new Date().toLocaleDateString()}</span>
        </div>
        <div className="timeline">
          {[
            { text: 'Machine running normally', actor: 'System' },
            { text: `AI assessment ${ai.label.toLowerCase()}`, actor: 'MachSense' },
            ...(assignment ? [{ text: `Assigned to ${assignment.engineerName} (${assignment.engineerEmail})`, actor: 'Admin' }] : [])
          ].map((e, i) => (
            <div className="timeline-item" key={i}>
              <span className="timeline-dot" />
              <strong>{e.text}</strong>
              <span>{e.actor} · just now</span>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}

function AlertModal({ role, machine, onClose, onConfirm }: { role: Role; machine: Machine; onClose: () => void; onConfirm: () => void }) {
  const isAdmin = role === 'admin'
  return (
    <Modal title={isAdmin ? 'Send Mail to Engineers' : 'Alert Factory / Admin'} onClose={onClose}>
      <div className="modal-callout warning">
        <AlertTriangle className="size-4" />
        {isAdmin
          ? 'This generates a Technical Engineer PDF Condition Report and emails it directly to the assigned engineer (1602-24-748-062@vce.ac.in).'
          : 'This generates an Operational Factory Admin PDF Report and emails it directly to the plant admin (1602-24-733-160@vce.ac.in).'
        }
      </div>
      <label className="field-label">
        Notification Message
        <textarea className="field-input" defaultValue={`Review ${machine.id}: suspicious vibration pattern detected on ${machine.name}.`} />
      </label>
      <div className="modal-actions">
        <button className="button secondary" onClick={onClose}>Cancel</button>
        <button className="button primary" onClick={onConfirm}>
          {isAdmin ? 'Send Mail to Engineers' : 'Send PDF Report to Factory Admin'}
        </button>
      </div>
    </Modal>
  )
}

function MaintenanceModal({ machine, onClose, onConfirm }: { machine: Machine; onClose: () => void; onConfirm: (item: { machineId: string; engineer: string; date: string; time: string; type: string; priority: string; notes: string }) => void }) {
  const [form, setForm] = useState({ machineId: machine.id, engineer: 'Jordan Diaz (1602-24-748-062@vce.ac.in)', date: '2026-08-15', time: '09:00', type: 'Bearing inspection', priority: 'Scheduled', notes: '' })
  return (
    <Modal title="Schedule Maintenance" onClose={onClose}>
      <div className="form-grid">
        <label className="field-label">Machine<select className="field-input" value={form.machineId} onChange={(e) => setForm({ ...form, machineId: e.target.value })}><option>M-001</option><option>M-002</option><option>M-003</option><option>M-004</option></select></label>
        <label className="field-label">Engineer<input className="field-input" value={form.engineer} onChange={(e) => setForm({ ...form, engineer: e.target.value })} /></label>
        <label className="field-label">Date<input className="field-input" type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} /></label>
        <label className="field-label">Time<input className="field-input" type="time" value={form.time} onChange={(e) => setForm({ ...form, time: e.target.value })} /></label>
        <label className="field-label">Maintenance type<input className="field-input" value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })} /></label>
        <label className="field-label">Priority<select className="field-input" value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}><option>Scheduled</option><option>Urgent</option></select></label>
      </div>
      <label className="field-label">Notes<textarea className="field-input" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} /></label>
      <div className="modal-actions">
        <button className="button secondary" onClick={onClose}>Cancel</button>
        <button className="button primary" onClick={() => onConfirm(form)}>Schedule</button>
      </div>
    </Modal>
  )
}

function ShutdownModal({ machine, onClose, onConfirm }: { machine: Machine; onClose: () => void; onConfirm: () => void }) {
  return (
    <Modal title="Confirm Manual Shutdown" onClose={onClose}>
      <div className="modal-callout critical"><CircleStop className="size-4" /> AI cannot shut down equipment. This human decision will stop {machine.id} and record an audit event.</div>
      <p className="text-sm text-muted-foreground">Reason: suspicious vibration pattern.</p>
      <div className="modal-actions">
        <button className="button secondary" onClick={onClose}>Cancel</button>
        <button className="button danger" onClick={onConfirm}>Confirm Shutdown</button>
      </div>
    </Modal>
  )
}

function AssignEngineerModal({
  machines, engineers, onClose, onConfirm
}: {
  machines: Machine[];
  engineers: typeof ENGINEER_LIST;
  onClose: () => void;
  onConfirm: (machineId: string, engineerEmail: string) => void;
}) {
  const [selectedMachine, setSelectedMachine] = useState(machines[0]?.id || 'M-001')
  const [selectedEngEmail, setSelectedEngEmail] = useState(engineers[0]?.email || '')

  return (
    <Modal title="Assign Engineer to Machine" onClose={onClose}>
      <div className="space-y-4 py-2">
        <label className="field-label">
          Select Machine
          <select className="field-input" value={selectedMachine} onChange={(e) => setSelectedMachine(e.target.value)}>
            {machines.map(m => <option key={m.id} value={m.id}>{m.id} — {m.name}</option>)}
          </select>
        </label>
        <label className="field-label">
          Select Engineer
          <select className="field-input" value={selectedEngEmail} onChange={(e) => setSelectedEngEmail(e.target.value)}>
            {engineers.map(e => <option key={e.id} value={e.email}>{e.name} ({e.email})</option>)}
          </select>
        </label>
      </div>
      <div className="modal-actions">
        <button className="button secondary" onClick={onClose}>Cancel</button>
        <button className="button primary" onClick={() => onConfirm(selectedMachine, selectedEngEmail)}>Save Assignment</button>
      </div>
    </Modal>
  )
}

function AddMachineModal({
  onClose, onConfirm
}: {
  onClose: () => void;
  onConfirm: (m: { code: string; name: string; location: string; type: string }) => void;
}) {
  const [code, setCode] = useState(`M-00${Math.floor(Math.random() * 90 + 10)}`)
  const [name, setName] = useState('')
  const [location, setLocation] = useState('Assembly / Line C')
  const [type, setType] = useState('Electric Motor')

  return (
    <Modal title="Add New Machine" onClose={onClose}>
      <div className="space-y-3 py-2">
        <label className="field-label">Machine Code<input className="field-input" value={code} onChange={e => setCode(e.target.value)} /></label>
        <label className="field-label">Machine Name<input className="field-input" placeholder="e.g. Centrifugal Blower 02" value={name} onChange={e => setName(e.target.value)} /></label>
        <label className="field-label">Location<input className="field-input" value={location} onChange={e => setLocation(e.target.value)} /></label>
        <label className="field-label">Machine Type
          <select className="field-input" value={type} onChange={e => setType(e.target.value)}>
            <option>Electric Motor</option>
            <option>Hydraulic Pump</option>
            <option>CNC Machine</option>
            <option>Air Compressor</option>
            <option>Blower / Fan</option>
          </select>
        </label>
      </div>
      <div className="modal-actions">
        <button className="button secondary" onClick={onClose}>Cancel</button>
        <button className="button primary" disabled={!name} onClick={() => onConfirm({ code, name, location, type })}>Create Machine</button>
      </div>
    </Modal>
  )
}

function NotificationPanel({ notifications, onClose, onOpen }: { notifications: { id: string; text: string; read: boolean; href: string }[]; onClose: () => void; onOpen: (href: string) => void }) {
  return (
    <div className="notification-panel">
      <div className="panel-header">
        <div>
          <h2>Notifications</h2>
          <p>{notifications.filter((n) => !n.read).length} unread</p>
        </div>
        <button className="icon-button" onClick={onClose}><X /></button>
      </div>
      {notifications.length === 0 ? (
        <div className="empty-state">No notifications yet.</div>
      ) : (
        notifications.map((n) => (
          <button className="notification-row" key={n.id} onClick={() => onOpen(n.href)}>
            <span className={`status-dot ${n.read ? '' : 'active'}`} />
            <span>{n.text}</span>
          </button>
        ))
      )}
    </div>
  )
}

export default function MachSenseApp({ initialRole }: Props) {
  const pathname = usePathname()
  const router = useRouter()
  const [role, setRole] = useState<Role | null>(initialRole ?? null)

  useEffect(() => {
    const stored = typeof window !== 'undefined' ? sessionStorage.getItem('machsense-role') as Role | null : null
    if (pathname === '/login' || pathname === '/') return
    const requested = pathname.startsWith('/admin') ? 'admin' : 'engineer'
    if (stored !== requested) router.replace('/login')
    else setRole(stored)
  }, [pathname, router])

  if (pathname === '/') return <Landing />
  if (pathname === '/login') return <Login />
  if (!role) return <main className="login-page"><div className="login-card"><p>Checking demo session…</p></div></main>
  return <Workspace role={role} />
}
