import Head from 'next/head';
import Image from 'next/image';
import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/router';
import {
  ComposedChart,
  Scatter,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts';
import styles from '../styles/dashboard.module.css';
import { getUser, signOut } from '../utils/auth';

/* ── Nav items ─── */
const navItems = [
  {
    label: 'Pricing Dashboard',
    active: true,
    icon: (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" />
        <rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" />
      </svg>
    ),
  },
  {
    label: 'Quote History',
    active: false,
    icon: (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" />
      </svg>
    ),
  },
  {
    label: 'Product Catalogue',
    active: false,
    icon: (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="8" y1="6" x2="21" y2="6" /><line x1="8" y1="12" x2="21" y2="12" /><line x1="8" y1="18" x2="21" y2="18" />
        <line x1="3" y1="6" x2="3.01" y2="6" /><line x1="3" y1="12" x2="3.01" y2="12" /><line x1="3" y1="18" x2="3.01" y2="18" />
      </svg>
    ),
  },
  {
    label: 'Market Trends',
    active: false,
    icon: (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" /><polyline points="16 7 22 7 22 13" />
      </svg>
    ),
  },
  {
    label: 'Settings',
    active: false,
    icon: (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
      </svg>
    ),
  },
];

/* ── Custom chart tooltip ─── */
function PriceTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const p = payload[0]?.payload;
  if (!p) return null;
  return (
    <div className={styles.chartTooltip}>
      <p className={styles.chartTooltipTitle}>{payload[0]?.name}</p>
      <p className={styles.chartTooltipRow}>
        Qty: <strong>{p.qty ?? p.x}</strong>
      </p>
      <p className={styles.chartTooltipRow}>
        Price: <strong>RM {parseFloat(p.price ?? p.y ?? 0).toFixed(2)}</strong>
      </p>
    </div>
  );
}

/* ── Helpers ─── */
function fmt(v) {
  return `RM ${parseFloat(v || 0).toFixed(2)}`;
}

function buildContextBlurb(result) {
  if (!result) return '';
  return (
    `Customer: ${result.customer_name} (${result.loyalty_tier || 'Standard'}, ${result.price_sensitivity || 'N/A'} sensitivity)\n` +
    `Item: ${result.item_name}\n` +
    `Recommended Price: ${fmt(result.recommended_price)}\n` +
    `Min Price: ${fmt(result.min_price)}\n` +
    `List Price: ${fmt(result.list_price)}\n` +
    `Max Discount: ${result.discount_ceiling ?? 0}%`
  );
}

export default function Dashboard() {
  const router = useRouter();

  /* ── Auth ─── */
  const [user, setUser]         = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [signingOut, setSigningOut]   = useState(false);

  /* ── Dropdown data ─── */
  const [customers, setCustomers] = useState([]);
  const [items, setItems]         = useState([]);
  const [dropError, setDropError] = useState('');

  /* ── Selection ─── */
  const [selectedCustomer, setSelectedCustomer] = useState('');
  const [selectedItem,     setSelectedItem]     = useState('');

  /* ── Analysis state ─── */
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError,   setAnalysisError]   = useState('');
  const [pricingResult,   setPricingResult]   = useState(null);

  /* ── Chat ─── */
  const [chatOpen,     setChatOpen]     = useState(false);
  const [chatInput,    setChatInput]    = useState('');
  const [chatLoading,  setChatLoading]  = useState(false);
  const [chatMessages, setChatMessages] = useState([
    { from: 'ai', text: "Hi, I'm your Fiamma AI Pricing Strategist. Ask me anything about pricing, margins, or stock strategy." },
  ]);
  const chatBottomRef = useRef(null);

  /* ── Auth check ─── */
  useEffect(() => {
    async function checkAuth() {
      const currentUser = await getUser();
      if (!currentUser) {
        router.replace('/');
        return;
      }
      setUser(currentUser);
      setAuthLoading(false);
    }
    checkAuth();
  }, [router]);

  /* ── Load dropdowns on mount ─── */
  useEffect(() => {
    async function loadDropdowns() {
      try {
        const [cRes, iRes] = await Promise.all([
          fetch('/api/customers'),
          fetch('/api/items'),
        ]);
        if (!cRes.ok || !iRes.ok) throw new Error('Failed to load customer/item data');
        const [cData, iData] = await Promise.all([cRes.json(), iRes.json()]);
        setCustomers(cData);
        setItems(iData);
      } catch (e) {
        setDropError(e.message);
      }
    }
    if (!authLoading) loadDropdowns();
  }, [authLoading]);

  /* ── Scroll chat to bottom ─── */
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  function handleSignOut() {
    setSigningOut(true);
    signOut();
  }

  /* ── Run pricing analysis ─── */
  async function runAnalysis() {
    if (!selectedCustomer || !selectedItem) {
      setAnalysisError('Please select both a customer and an item.');
      return;
    }
    setAnalysisError('');
    setAnalysisLoading(true);
    setPricingResult(null);

    try {
      const resp = await fetch('/api/pricing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ customer_id: selectedCustomer, item_code: selectedItem }),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ error: resp.statusText }));
        throw new Error(err.error || resp.statusText);
      }

      const reader  = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const raw = line.slice(6).trim();
          if (!raw) continue;
          let event;
          try { event = JSON.parse(raw); } catch { continue; }

          if (event.type === 'result') {
            setPricingResult(event.data);
          } else if (event.type === 'error') {
            throw new Error(event.message);
          }
        }
      }
    } catch (e) {
      setAnalysisError('Error: ' + e.message);
    } finally {
      setAnalysisLoading(false);
    }
  }

  /* ── Chat send ─── */
  async function handleChatSend() {
    if (!chatInput.trim() || chatLoading) return;
    const userText = chatInput.trim();
    setChatInput('');
    setChatMessages((prev) => [...prev, { from: 'user', text: userText }]);
    setChatLoading(true);

    try {
      const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userText,
          context: buildContextBlurb(pricingResult),
        }),
      });

      if (!resp.ok) throw new Error('Chat request failed');

      const reader  = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const raw = line.slice(6).trim();
          if (!raw) continue;
          let event;
          try { event = JSON.parse(raw); } catch { continue; }

          if (event.type === 'message') {
            setChatMessages((prev) => [...prev, { from: 'ai', text: event.text }]);
          } else if (event.type === 'error') {
            setChatMessages((prev) => [...prev, { from: 'ai', text: `⚠️ ${event.message}` }]);
          }
        }
      }
    } catch (e) {
      setChatMessages((prev) => [...prev, { from: 'ai', text: `⚠️ ${e.message}` }]);
    } finally {
      setChatLoading(false);
    }
  }

  /* ── Loading screen ─── */
  if (authLoading) {
    return (
      <div className={styles.loadingPage}>
        <div className={styles.spinner} />
      </div>
    );
  }

  const displayName = user?.userDetails ?? 'User';
  const firstName   = displayName.split(' ')[0].split('@')[0];
  const initials    = displayName.split(' ').map((n) => n[0]).slice(0, 2).join('').toUpperCase();

  /* ── Chart data ─── */
  const actualData  = pricingResult?.actual_points?.map((p) => ({ qty: p.qty, price: p.price })) ?? [];
  const optimalData = pricingResult
    ? [...(pricingResult.optimal_price_points ?? [])]
        .sort((a, b) => a.qty - b.qty)
        .map((p) => ({ qty: p.qty, price: p.price }))
    : [];

  const allQtys  = [...actualData, ...optimalData].map((p) => p.qty);
  const minQty   = allQtys.length ? Math.max(0, Math.min(...allQtys) * 0.8) : 0;
  const maxQty   = allQtys.length ? Math.max(...allQtys) * 1.1 : 100;

  return (
    <>
      <Head>
        <title>Fiamma — AI Pricing Strategist</title>
        <meta name="description" content="Fiamma AI Pricing Strategist Dashboard" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="true" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
      </Head>

      <div className={styles.bg} aria-hidden="true" />

      <div className={styles.shell}>
        {/* ══ SIDEBAR ══ */}
        <aside className={styles.sidebar}>
          <div className={styles.sidebarLogo}>
            <div className={styles.logoMark}>
              <Image
                src="/logos/fiamma_holdings_berhad_logo.jpg"
                alt="Fiamma Logo"
                width={36}
                height={36}
                style={{ objectFit: 'contain', width: '100%', height: '100%', borderRadius: '6px' }}
              />
            </div>
            <div>
              <div className={styles.logoName}>Fiamma</div>
              <div className={styles.logoTagline}>AI Pricing Strategist</div>
            </div>
          </div>

          <nav className={styles.sidebarNav}>
            {navItems.map((item) => (
              <button
                key={item.label}
                className={`${styles.navItem} ${item.active ? styles.navItemActive : ''}`}
              >
                <span className={styles.navIcon}>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            ))}
          </nav>

          {/* Stat cards in sidebar */}
          {pricingResult && (
            <div className={styles.sidebarMetrics}>
              <p className={styles.sidebarMetricsTitle}>Key Metrics</p>
              <div className={styles.statsGrid}>
                <div className={`${styles.statCard} ${styles.statCardGreen}`}>
                  <span className={styles.statLabel}>Recommended</span>
                  <span className={styles.statValue}>{fmt(pricingResult.recommended_price)}</span>
                </div>
                <div className={`${styles.statCard} ${styles.statCardRed}`}>
                  <span className={styles.statLabel}>Min Price</span>
                  <span className={styles.statValue}>{fmt(pricingResult.min_price)}</span>
                </div>
                <div className={`${styles.statCard} ${styles.statCardBlue}`}>
                  <span className={styles.statLabel}>List Price</span>
                  <span className={styles.statValue}>{fmt(pricingResult.list_price)}</span>
                </div>
                <div className={`${styles.statCard} ${styles.statCardAmber}`}>
                  <span className={styles.statLabel}>Max Discount</span>
                  <span className={styles.statValue}>{pricingResult.discount_ceiling ?? 0}%</span>
                </div>
              </div>
            </div>
          )}

          <div className={styles.sidebarUser}>
            <div className={styles.userAvatar}>{initials}</div>
            <div className={styles.userInfo}>
              <span className={styles.userName}>{displayName}</span>
              <span className={styles.userRole}>Sales Manager</span>
            </div>
            <button className={styles.signOutBtn} onClick={handleSignOut} disabled={signingOut} title="Sign out">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
            </button>
          </div>
        </aside>

        {/* ══ MAIN CONTENT ══ */}
        <main className={styles.main}>
          {/* Page header */}
          <div className={styles.pageHeader}>
            <div>
              <h1 className={styles.pageTitle}>Pricing Dashboard</h1>
              <p className={styles.pageSubtitle}>Good morning, {firstName}. Select a customer and item to analyse pricing.</p>
            </div>
            <div className={styles.agentBadge}>Azure AI Foundry</div>
          </div>

          {/* Error banner */}
          {(analysisError || dropError) && (
            <div className={styles.errorBanner}>
              {analysisError || dropError}
            </div>
          )}

          {/* ── ANALYSIS INPUTS ── */}
          <section className={styles.panel}>
            <div className={styles.panelHeader}>
              <div>
                <h2 className={styles.panelTitle}>Analysis Parameters</h2>
                <p className={styles.panelSub}>Select a customer and item, then run the AI pricing analysis</p>
              </div>
            </div>

            <div className={styles.paramsGrid}>
              <div className={styles.paramControl} style={{ gridColumn: 'span 2' }}>
                <label className={styles.paramLabel}>Customer</label>
                <select
                  className={styles.paramInput}
                  value={selectedCustomer}
                  onChange={(e) => setSelectedCustomer(e.target.value)}
                  disabled={customers.length === 0}
                >
                  <option value="">{customers.length === 0 ? 'Loading customers…' : 'Select customer…'}</option>
                  {customers.map((c) => (
                    <option key={c['Customer ID']} value={c['Customer ID']}>
                      {c['Customer Name']}
                    </option>
                  ))}
                </select>
              </div>

              <div className={styles.paramControl} style={{ gridColumn: 'span 2' }}>
                <label className={styles.paramLabel}>Item</label>
                <select
                  className={styles.paramInput}
                  value={selectedItem}
                  onChange={(e) => setSelectedItem(e.target.value)}
                  disabled={items.length === 0}
                >
                  <option value="">{items.length === 0 ? 'Loading items…' : 'Select item…'}</option>
                  {items.map((i) => (
                    <option key={i['Item Code']} value={i['Item Code']}>
                      {i['Item Name']} ({i['Category']})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <button
              className={styles.analyzeBtn}
              onClick={runAnalysis}
              disabled={analysisLoading || !selectedCustomer || !selectedItem}
            >
              {analysisLoading ? (
                <>
                  <span className={styles.spinnerSmall} />
                  Analysing with AI…
                </>
              ) : (
                '⚡ Analyze Pricing'
              )}
            </button>
          </section>

          {/* ── PRICING CHART ── */}
          <section className={styles.panel}>
            <div className={styles.panelHeader}>
              <div>
                <h2 className={styles.panelTitle}>
                  {pricingResult ? `${pricingResult.item_name} — Price vs Quantity` : 'Price vs Quantity Analysis'}
                </h2>
                <p className={styles.panelSub}>
                  {pricingResult
                    ? `${pricingResult.customer_name} · ${pricingResult.loyalty_tier || 'Standard'} tier · Sensitivity: ${pricingResult.price_sensitivity || 'N/A'}`
                    : 'Run an analysis to see the pricing chart'}
                </p>
              </div>
              {pricingResult && <div className={styles.panelBadge}>Live AI Data</div>}
            </div>

            {!pricingResult && !analysisLoading && (
              <div className={styles.emptyState}>
                <span className={styles.emptyIcon}>📊</span>
                <span className={styles.emptyLabel}>Awaiting Analysis</span>
              </div>
            )}

            {analysisLoading && (
              <div className={styles.emptyState}>
                <div className={styles.spinner} />
                <span className={styles.emptyLabel}>Analysing with AI…</span>
              </div>
            )}

            {pricingResult && !analysisLoading && (
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart margin={{ top: 10, right: 20, left: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(39,36,92,0.07)" />
                  <XAxis
                    dataKey="qty"
                    type="number"
                    domain={[minQty, maxQty]}
                    name="Quantity"
                    label={{ value: 'Quantity Ordered', position: 'insideBottom', offset: -5, fill: '#8888aa', fontSize: 11 }}
                    tick={{ fill: '#8888aa', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    dataKey="price"
                    name="Price"
                    tickFormatter={(v) => `RM ${v}`}
                    tick={{ fill: '#8888aa', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip content={<PriceTooltip />} />

                  {/* Min price floor */}
                  <ReferenceLine
                    y={pricingResult.min_price}
                    stroke="#c0392b"
                    strokeDasharray="6 4"
                    strokeWidth={1.5}
                    label={{ value: 'Min Floor', fill: '#c0392b', fontSize: 10, position: 'insideTopRight' }}
                  />
                  {/* List price */}
                  <ReferenceLine
                    y={pricingResult.list_price}
                    stroke="#a09d94"
                    strokeDasharray="3 3"
                    strokeWidth={1.5}
                    label={{ value: 'List Price', fill: '#a09d94', fontSize: 10, position: 'insideTopRight' }}
                  />
                  {/* Recommended price */}
                  <ReferenceLine
                    y={pricingResult.recommended_price}
                    stroke="#2d7a4f"
                    strokeDasharray="4 4"
                    strokeWidth={1.5}
                    label={{ value: 'Recommended', fill: '#2d7a4f', fontSize: 10, position: 'insideTopRight' }}
                  />

                  {/* Optimal price curve */}
                  <Line
                    data={optimalData}
                    dataKey="price"
                    dot={{ fill: '#2d7a4f', r: 4 }}
                    stroke="#2d7a4f"
                    strokeWidth={2.5}
                    type="monotone"
                    name="Optimal Curve"
                    connectNulls
                  />

                  {/* Actual historical scatter */}
                  <Scatter
                    data={actualData}
                    dataKey="price"
                    fill="rgba(35,85,160,0.7)"
                    name="Actual Prices"
                    shape="circle"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            )}
          </section>

          {/* ── AI PRICING RATIONALE ── */}
          <section className={styles.panel}>
            <div className={styles.panelHeader}>
              <div>
                <h2 className={styles.panelTitle}>AI Pricing Rationale</h2>
                <p className={styles.panelSub}>Why the agent recommends this price point</p>
              </div>
              {pricingResult && (
                <div className={styles.recommendBadge}>
                  Recommended: <strong>{fmt(pricingResult.recommended_price)}</strong>
                  <span className={styles.confidencePill}>
                    {pricingResult.discount_ceiling ?? 0}% max discount
                  </span>
                </div>
              )}
            </div>

            {!pricingResult && !analysisLoading && (
              <div className={styles.emptyState}>
                <span className={styles.emptyIcon}>💬</span>
                <span className={styles.emptyLabel}>Run analysis to see reasoning</span>
              </div>
            )}

            {analysisLoading && (
              <div className={styles.emptyState}>
                <div className={styles.spinner} />
                <span className={styles.emptyLabel}>Generating reasoning…</span>
              </div>
            )}

            {pricingResult && !analysisLoading && (
              <div className={styles.reasoningSummary}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C73939" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                <p>{pricingResult.reasoning || 'No reasoning provided.'}</p>
              </div>
            )}
          </section>
        </main>
      </div>

      {/* ══ CHAT FAB ══ */}
      <button
        className={`${styles.chatFab} ${chatOpen ? styles.chatFabOpen : ''}`}
        onClick={() => setChatOpen((o) => !o)}
        aria-label="Open AI Pricing Assistant"
      >
        {chatOpen ? (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        ) : (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        )}
      </button>

      {/* ══ CHAT PANEL ══ */}
      {chatOpen && (
        <div className={styles.chatPanel}>
          <div className={styles.chatHeader}>
            <div className={styles.chatHeaderLeft}>
              <div className={styles.chatAiAvatar}>AI</div>
              <div>
                <div className={styles.chatTitle}>Pricing Assistant</div>
                <div className={styles.chatSubtitle}>Powered by Azure AI Foundry</div>
              </div>
            </div>
            <div className={styles.chatOnline} />
          </div>

          <div className={styles.chatMessages}>
            {chatMessages.map((msg, i) => (
              <div key={i} className={`${styles.chatMsg} ${msg.from === 'user' ? styles.chatMsgUser : styles.chatMsgAi}`}>
                {msg.text}
              </div>
            ))}
            {chatLoading && (
              <div className={`${styles.chatMsg} ${styles.chatMsgAi}`}>
                <span className={styles.chatTyping}>···</span>
              </div>
            )}
            <div ref={chatBottomRef} />
          </div>

          <div className={styles.chatInputRow}>
            <input
              className={styles.chatInput}
              placeholder="Ask about pricing, margins, stock…"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleChatSend()}
              disabled={chatLoading}
            />
            <button className={styles.chatSendBtn} onClick={handleChatSend} disabled={chatLoading}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </>
  );
}
