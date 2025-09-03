import { useEffect, useMemo, useState } from 'react'
import './App.css'

type Weekplan = {
  key: string
  name: string
  icon: string
  last_update_iso: string
  img_url: string
  img_url2?: string
  page1_url?: string
  page2_url?: string
}

function useModePolling(intervalMs: number) {
  const [isDashboard, setIsDashboard] = useState(false)
  const [view, setView] = useState<'all' | 'plan1' | 'plan2'>('all')
  useEffect(() => {
    let timer: number | undefined
    const tick = async () => {
      try {
        const res = await fetch('/mode')
        const data = await res.json()
        setIsDashboard(Boolean(data.dashboard))
        if (data.view) setView(data.view)
      } catch (e) {
        // ignore
      } finally {
        timer = window.setTimeout(tick, intervalMs)
      }
    }
    tick()
    return () => { if (timer) window.clearTimeout(timer) }
  }, [intervalMs])
  return { isDashboard, view }
}

function App() {
  const [weekplans, setWeekplans] = useState<Weekplan[]>([])
  const { isDashboard, view } = useModePolling(1000)
  const [screensaverUrl, setScreensaverUrl] = useState('')
  const isPortrait = useIsPortrait(1) // width/height < 1 means portrait/square

  // Keyboard shortcuts: Left = plan1, Right = plan2, Up = all
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      let viewToShow: 'all' | 'plan1' | 'plan2' | null = null
      if (e.key === 'ArrowLeft') viewToShow = 'plan1'
      else if (e.key === 'ArrowRight') viewToShow = 'plan2'
      else if (e.key === 'ArrowUp') viewToShow = 'all'
      if (viewToShow) {
        e.preventDefault()
        e.stopPropagation()
        const form = new FormData()
        form.append('action', 'show_week_plan')
        form.append('current_tab', 'ukeplan')
        form.append('view', viewToShow)
        fetch('/admin', { method: 'POST', body: form })
          .then(() => fetch('/mode').then(r => r.json()).then(() => fetch('/api/weekplans').then(r => r.json()).then(setWeekplans)))
          .catch(() => {})
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  useEffect(() => {
    fetch('/api/weekplans').then(r => r.json()).then(setWeekplans).catch(() => {})
  }, [])

  // Re-fetch weekplans when view changes while dashboard is active, to pick up new page 2
  useEffect(() => {
    if (isDashboard) {
      fetch('/api/weekplans').then(r => r.json()).then(setWeekplans).catch(() => {})
    }
  }, [isDashboard, view])

  // When switching back to screensaver, fetch new image
  const lastIsDashboard = useMemo(() => ({ current: false }), [])
  useEffect(() => {
    if (!isDashboard && lastIsDashboard.current === true) {
      fetch('/screensaver_image').then(r => r.json()).then(d => setScreensaverUrl(d.image_url || '')).catch(() => {})
    }
    lastIsDashboard.current = isDashboard
  }, [isDashboard, lastIsDashboard])

  // Ensure we have a screensaver image when entering or starting in screensaver mode
  useEffect(() => {
    if (!isDashboard && !screensaverUrl) {
      fetch('/screensaver_image').then(r => r.json()).then(d => setScreensaverUrl(d.image_url || '')).catch(() => {})
    }
  }, [isDashboard, screensaverUrl])

  return (
    <div style={{ width: '100vw', height: '100vh', overflow: 'hidden', background: 'black' }}>
      {!isDashboard && (
        <div style={{ position: 'absolute', inset: 0 }}>
          {screensaverUrl && (
            <img src={screensaverUrl} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          )}
        </div>
      )}
      {isDashboard && view === 'all' && (
        <div style={{ position: 'absolute', inset: 0, background: '#f8f9fa', padding: '2rem', boxSizing: 'border-box', overflow: 'hidden', color: '#212529' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', paddingBottom: '1rem', borderBottom: '1px solid rgba(0,0,0,0.1)' }}>
            <DateDisplay />
            <TimeDisplay />
          </div>
          <div style={{
            display: 'flex',
            flexDirection: isPortrait ? 'column' : 'row',
            gap: '2rem',
            height: isPortrait ? 'calc(100vh - 10rem)' : 'calc(100vh - 8rem)',
            alignItems: 'flex-start',
            overflowY: isPortrait ? 'auto' : 'hidden',
            paddingRight: isPortrait ? '1rem' : undefined
          }}>
            {weekplans.map(wp => (
              <PlanCard key={wp.key} plan={wp} />
            ))}
          </div>
        </div>
      )}
      {isDashboard && view !== 'all' && (
        <div style={{ position: 'absolute', inset: 0, background: '#f8f9fa', padding: '2rem', boxSizing: 'border-box', overflow: 'hidden', color: '#212529' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', paddingBottom: '1rem', borderBottom: '1px solid rgba(0,0,0,0.1)' }}>
            <DateDisplay />
            <TimeDisplay />
          </div>
          <SingleUserTwoPage plans={weekplans} view={view} isPortrait={isPortrait} />
        </div>
      )}
    </div>
  )
}

function DateDisplay() {
  const [text, setText] = useState('')
  useEffect(() => {
    const update = () => {
      const now = new Date()
      const opts: Intl.DateTimeFormatOptions = { weekday: 'long', day: 'numeric', month: 'long' }
      const s = now.toLocaleDateString('en-GB', opts)
      setText(s.charAt(0).toUpperCase() + s.slice(1))
    }
    update()
    const id = setInterval(update, 1000)
    return () => clearInterval(id)
  }, [])
  return <div style={{ fontSize: '2.5rem', fontWeight: 500 }}>{text}</div>
}

function TimeDisplay() {
  const [text, setText] = useState('')
  useEffect(() => {
    const update = () => setText(new Date().toLocaleTimeString('en-GB'))
    update()
    const id = setInterval(update, 1000)
    return () => clearInterval(id)
  }, [])
  return <div style={{ fontSize: '3rem', fontWeight: 600, color: '#0d6efd', fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas' }}>{text}</div>
}

function PlanCard({ plan }: { plan: Weekplan }) {
  const lastUpdated = plan.last_update_iso ? new Date(plan.last_update_iso).toLocaleString('en-GB', { hour12: false }) : '—'
  return (
    <div style={{ flex: 1, background: 'white', borderRadius: 12, padding: '1.5rem', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem' }}>
        <span style={{ marginRight: '0.75rem', fontSize: '1.5rem' }}>{plan.icon}</span>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 600, margin: 0 }}>{plan.name}</h2>
      </div>
      <div style={{ width: '100%', aspectRatio: '1.414 / 1', backgroundColor: '#f0f0f0', border: '1px solid #dee2e6', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
        <img src={plan.img_url} alt={`${plan.name} weekplan`} style={{ maxWidth: '100%', maxHeight: '100%', width: 'auto', height: 'auto', objectFit: 'contain' }} />
      </div>
      <div style={{ fontSize: '0.875rem', color: '#6c757d', display: 'flex', alignItems: 'center', marginTop: '1rem' }}>
        <span style={{ marginRight: 8 }}>Last updated: {lastUpdated}</span>
      </div>
    </div>
  )
}

export default App

function SingleUserTwoPage({ plans, view, isPortrait }: { plans: Weekplan[]; view: 'plan1' | 'plan2' | 'all'; isPortrait: boolean }) {
  const planKey = view === 'plan2' ? 'plan2' : 'plan1'
  const plan = plans.find(p => p.key === planKey)
  if (!plan) return null
  const lastUpdated = plan.last_update_iso ? new Date(plan.last_update_iso).toLocaleString('en-GB', { hour12: false }) : '—'
  return (
    <div style={{ width: '100%', height: isPortrait ? 'calc(100vh - 10rem)' : 'calc(100vh - 8rem)', overflowY: isPortrait ? 'auto' : 'hidden', paddingRight: isPortrait ? '1rem' : undefined }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <span style={{ marginRight: '0.75rem', fontSize: '1.5rem' }}>{plan.icon}</span>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 600, margin: 0 }}>{plan.name}</h2>
        </div>
        <div style={{ fontSize: '0.875rem', color: '#6c757d' }}>Last updated: {lastUpdated}</div>
      </div>
      <div style={{ display: 'flex', gap: '2rem', height: '100%', flexDirection: isPortrait ? 'column' : 'row' }}>
        <div style={{ flex: 1 }}>
          <div style={{ width: '100%', height: isPortrait ? '50vh' : '100%', backgroundColor: '#f0f0f0', border: '1px solid #dee2e6', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
            <img src={plan.page1_url || plan.img_url} style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }} />
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ width: '100%', height: isPortrait ? '50vh' : '100%', backgroundColor: '#f0f0f0', border: '1px solid #dee2e6', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
            {(plan.page2_url || plan.img_url2) ? (
              <img src={plan.page2_url || plan.img_url2} style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }} />
            ) : (
              <div style={{ color: '#6c757d' }}>No page 2</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function useIsPortrait(threshold: number) {
  const [isPortrait, setIsPortrait] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false
    const ratio = window.innerWidth / window.innerHeight
    return ratio < threshold
  })
  useEffect(() => {
    const onResize = () => {
      const ratio = window.innerWidth / window.innerHeight
      setIsPortrait(ratio < threshold)
    }
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [threshold])
  return isPortrait
}
