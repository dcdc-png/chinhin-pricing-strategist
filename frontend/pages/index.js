import Head from 'next/head';
import Image from 'next/image';import { useEffect, useState, useRef, useCallback } from 'react';
import { useRouter } from 'next/router';
import styles from '../styles/login.module.css';
import { getUser, signIn, isLocalDev } from '../utils/auth';

/* Typewriter strings */
const PHRASES = [
  'Maximize profit margins.',
  'Outsmart competitors.',
  'Price with confidence.',
  'Turn data into decisions.',
];

/* Animated counter hook */
function useCounter(target, duration = 1200, start = false) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    if (!start) return;
    let startTime = null;
    const step = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      setValue(Math.floor(progress * target));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [start, target, duration]);
  return value;
}

export default function LoginPage() {
  const router = useRouter();
  const [authStatus, setAuthStatus] = useState('checking');
  const [signingIn, setSigningIn] = useState(false);
  const localDev = isLocalDev();



  /* ── Typewriter & Counters State ── */
  const [phrase, setPhrase] = useState('');
  const [phraseIndex, setPhraseIndex] = useState(0);
  const [deleting, setDeleting] = useState(false);
  const [countersReady, setCountersReady] = useState(false);
  const typingRef = useRef(null);

  /* ── Auth check ── */
  useEffect(() => {
    async function checkAuth() {
      const user = await getUser();
      if (user) {
        router.replace('/dashboard');
        return;
      }
      setAuthStatus('ready');
      setTimeout(() => setCountersReady(true), 400); // Trigger counters after initial mount
    }
    checkAuth();
  }, [router]);

  /* ── Typewriter effect ── */
  useEffect(() => {
    if (authStatus !== 'ready') return;
    const current = PHRASES[phraseIndex];
    const speed = deleting ? 40 : 70;

    typingRef.current = setTimeout(() => {
      if (!deleting) {
        if (phrase.length < current.length) {
          setPhrase(current.slice(0, phrase.length + 1));
        } else {
          setTimeout(() => setDeleting(true), 1600);
        }
      } else {
        if (phrase.length > 0) {
          setPhrase(phrase.slice(0, -1));
        } else {
          setDeleting(false);
          setPhraseIndex((i) => (i + 1) % PHRASES.length);
        }
      }
    }, speed);

    return () => clearTimeout(typingRef.current);
  }, [phrase, deleting, phraseIndex, authStatus]);

  /* Animated counters */
  const c1 = useCounter(1247, 1400, countersReady);
  const c2 = useCounter(94, 1000, countersReady);
  const c3 = useCounter(18, 1200, countersReady);

  function handleSignIn() {
    setSigningIn(true);
    signIn();
  }

  return (
    <>
      <Head>
        <title>Fiamma AI Pricing Strategist — Sign In</title>
        <meta name="description" content="Sign in to Fiamma AI Pricing Strategist with your company Microsoft account." />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="true" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet" />
      </Head>

      <div className={styles.bg} aria-hidden="true" />

      <main className={styles.page}>
        <div className={styles.splitContainer}>
          
          {/* ── LEFT PANEL (BRAND) ── */}
          <div className={styles.leftPanel}>
            {/* Top Logo */}
            <div className={styles.brandHeader} style={{ animationDelay: '0.1s' }}>
              <div className={styles.brandMark}>
                <Image
                  src="/logos/fiamma_holdings_berhad_logo.jpg"
                  alt="Fiamma Holdings Berhad Logo"
                  width={40}
                  height={40}
                  style={{ objectFit: 'contain', width: '100%', height: '100%', borderRadius: '6px' }}
                />
              </div>
              <span className={styles.brandName}>Fiamma Holdings Berhad</span>
            </div>

            {/* Middle Content */}
            <div className={styles.heroContent}>
              <h1 className={styles.heroTitle} style={{ animationDelay: '0.2s' }}>
                AI Pricing<br/>Strategist
              </h1>
              
              <div className={styles.typewriterRow} style={{ animationDelay: '0.3s' }}>
                <span className={styles.typewriterText}>{phrase}</span>
                <span className={styles.cursor} aria-hidden="true">|</span>
              </div>

              <div className={styles.heroStats} style={{ animationDelay: '0.4s' }}>
                <div className={styles.heroStat}>
                  <span className={styles.heroStatValue}>{c1.toLocaleString()}+</span>
                  <span className={styles.heroStatLabel}>Decisions</span>
                </div>
                <div className={styles.heroStatDivider} />
                <div className={styles.heroStat}>
                  <span className={styles.heroStatValue}>{c2}%</span>
                  <span className={styles.heroStatLabel}>Accuracy</span>
                </div>
                <div className={styles.heroStatDivider} />
                <div className={styles.heroStat}>
                  <span className={styles.heroStatValue}>{c3}s</span>
                  <span className={styles.heroStatLabel}>Speed</span>
                </div>
              </div>
            </div>

            {/* Bottom Footer */}
            <div className={styles.heroFooter} style={{ animationDelay: '0.5s' }}>
              &copy; {new Date().getFullYear()} Fiamma. All rights reserved.
            </div>
            
          </div>

          {/* ── RIGHT PANEL (LOGIN) ── */}
          <div className={styles.rightPanel}>
            <div className={styles.loginContent}>
              
              <div className={styles.mobileLogo}>
                <Image
                  src="/logos/fiamma_holdings_berhad_logo.jpg"
                  alt="Fiamma Logo"
                  width={40}
                  height={40}
                  style={{ borderRadius: '6px' }}
                />
              </div>

              <h2 className={styles.loginTitle} style={{ animationDelay: '0.2s' }}>Welcome Back!</h2>
              <p className={styles.loginPrompt} style={{ animationDelay: '0.3s' }}>
                Sign in to your dashboard to access real-time pricing strategies and automated margin analytics.
              </p>

              <div className={styles.formContainer} style={{ animationDelay: '0.4s' }}>
                {authStatus === 'checking' ? (
                  <div className={styles.loadingState} role="status">
                    <div className={styles.spinner} aria-hidden="true" />
                  </div>
                ) : (
                  <>
                    <button
                      className={styles.btnMicrosoft}
                      onClick={handleSignIn}
                      disabled={signingIn}
                    >
                      {signingIn ? (
                        <>
                          <div className={styles.spinnerSmall} aria-hidden="true" />
                          Redirecting...
                        </>
                      ) : (
                        <>
                          <div className={styles.msIcon} aria-hidden="true">
                            <span className={styles.msRed} />
                            <span className={styles.msGreen} />
                            <span className={styles.msBlue} />
                            <span className={styles.msYellow} />
                          </div>
                          Sign in with Microsoft
                        </>
                      )}
                    </button>

                    {localDev && (
                      <div className={styles.devNotice} role="note" style={{ animationDelay: '0.5s' }}>
                        <p><strong>Local dev:</strong> Auth requires the SWA CLI.</p>
                      </div>
                    )}
                  </>
                )}
              </div>
              
            </div>
          </div>

        </div>
      </main>
    </>
  );
}
