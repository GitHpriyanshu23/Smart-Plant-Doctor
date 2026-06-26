import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';

const NAV_LINKS = [
  { label: 'Features', href: '#features' },
  { label: 'How it Works', href: '#how-it-works' },
  { label: 'About', href: '#about' },
];

const STATS = [
  { value: '6', label: 'Plants Supported' },
  { value: '29', label: 'Disease Classes' },
  { value: '92.37%', label: 'Accuracy' },
  { value: '24/7', label: 'Real-time Monitoring' },
];

const FEATURES = [
  {
    icon: '📡',
    title: 'Real-time Monitoring',
    description:
      'ESP32-powered sensors stream temperature, humidity, soil moisture, and light data directly to your dashboard.',
  },
  {
    icon: '🔬',
    title: 'AI Disease Detection',
    description:
      'Snap a photo of any leaf and our deep learning model identifies diseases with 92%+ accuracy in seconds.',
  },
  {
    icon: '💬',
    title: 'Smart Chat Assistant',
    description:
      'Ask anything about your plants. Our AI assistant uses live sensor data and history for contextual advice.',
  },
  {
    icon: '📓',
    title: 'Care Journal',
    description:
      'Log watering, fertilizing, and repotting events. Track your care routine and get reminders.',
  },
  {
    icon: '📖',
    title: 'Plant Encyclopedia',
    description:
      'Comprehensive care guides for every supported plant — light needs, watering schedules, and common issues.',
  },
  {
    icon: '🗺️',
    title: 'Disease Map',
    description:
      'See community-reported plant health issues on an interactive map. Stay ahead of outbreaks in your area.',
  },
];

const STEPS = [
  {
    number: '01',
    icon: '📡',
    title: 'Connect Your Sensor',
    description:
      'Plug in your ESP32 device, connect it to Wi-Fi, and it starts streaming environmental data instantly.',
  },
  {
    number: '02',
    icon: '📸',
    title: 'Upload a Photo',
    description:
      'Take a picture of a leaf showing symptoms. Our AI analyzes it and returns a diagnosis within seconds.',
  },
  {
    number: '03',
    icon: '🌱',
    title: 'Get Insights',
    description:
      'Receive actionable treatment plans, care adjustments, and proactive alerts based on your data.',
  },
];

const SUPPORTED_PLANTS = [
  { name: 'Rose', emoji: '🌹', diseases: 8 },
  { name: 'Hibiscus', emoji: '🌺', diseases: 4 },
  { name: 'Aloe Vera', emoji: '🌿', diseases: 5 },
  { name: 'Money Plant', emoji: '🪴', diseases: 4 },
  { name: 'Chrysanthemum', emoji: '🌼', diseases: 3 },
  { name: 'Turmeric', emoji: '🌱', diseases: 5 },
];

export default function LandingPage() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <div className="min-h-screen bg-gray-950 text-white overflow-x-hidden">
      {/* ── Navbar ── */}
      <nav
        className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${
          scrolled
            ? 'bg-gray-950/70 backdrop-blur-xl border-b border-white/10 shadow-lg shadow-black/20'
            : 'bg-transparent'
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 group">
            <span className="text-2xl">🌿</span>
            <span className="text-lg font-bold tracking-tight text-white group-hover:text-leaf-400 transition-colors">
              Smart Plant Doctor
            </span>
          </Link>

          {/* Desktop links */}
          <div className="hidden md:flex items-center gap-8">
            {NAV_LINKS.map((l) => (
              <a
                key={l.label}
                href={l.href}
                className="text-sm text-gray-300 hover:text-white transition-colors"
              >
                {l.label}
              </a>
            ))}
          </div>

          <div className="hidden md:flex items-center gap-3">
            <Link
              to="/login"
              className="text-sm text-gray-300 hover:text-white px-4 py-2 transition-colors"
            >
              Sign in
            </Link>
            <Link
              to="/login"
              className="text-sm font-semibold bg-leaf-600 hover:bg-leaf-500 text-white px-5 py-2 rounded-full transition-colors shadow-lg shadow-leaf-600/25"
            >
              Get started
            </Link>
          </div>

          {/* Mobile hamburger */}
          <button
            className="md:hidden text-gray-300 hover:text-white p-2"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {mobileMenuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile menu dropdown */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-gray-950/90 backdrop-blur-xl border-b border-white/10 px-4 pb-4 space-y-2">
            {NAV_LINKS.map((l) => (
              <a
                key={l.label}
                href={l.href}
                onClick={() => setMobileMenuOpen(false)}
                className="block text-sm text-gray-300 hover:text-white py-2"
              >
                {l.label}
              </a>
            ))}
            <div className="pt-2 flex flex-col gap-2">
              <Link to="/login" className="text-sm text-gray-300 hover:text-white py-2">
                Sign in
              </Link>
              <Link
                to="/login"
                className="text-sm font-semibold bg-leaf-600 hover:bg-leaf-500 text-white px-5 py-2 rounded-full text-center transition-colors"
              >
                Get started
              </Link>
            </div>
          </div>
        )}
      </nav>

      {/* ── Hero Section ── */}
      <section className="relative min-h-screen flex items-center justify-center pt-16">
        {/* Animated gradient background */}
        <div className="absolute inset-0 bg-gradient-to-br from-green-900 via-emerald-800 to-teal-900" />
        <div
          className="absolute inset-0 opacity-30"
          style={{
            backgroundImage:
              'radial-gradient(ellipse at 20% 50%, rgba(16,185,129,0.4) 0%, transparent 50%), radial-gradient(ellipse at 80% 20%, rgba(6,182,212,0.3) 0%, transparent 50%), radial-gradient(ellipse at 50% 80%, rgba(34,197,94,0.3) 0%, transparent 50%)',
          }}
        />
        {/* Subtle grid overlay */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              'linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)',
            backgroundSize: '60px 60px',
          }}
        />

        <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 text-center">
          <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-xl border border-white/20 rounded-full px-4 py-1.5 mb-8">
            <span className="w-2 h-2 bg-leaf-400 rounded-full animate-pulse" />
            <span className="text-sm text-leaf-200 font-medium">AI + IoT Plant Health Platform</span>
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-7xl font-bold leading-[1.1] tracking-tight mb-6">
            Know your plants.
            <br />
            <span className="bg-gradient-to-r from-leaf-400 via-emerald-300 to-teal-300 bg-clip-text text-transparent">
              Before they struggle.
            </span>
          </h1>

          <p className="text-lg sm:text-xl text-gray-300 max-w-2xl mx-auto mb-10 leading-relaxed">
            Live sensor monitoring from ESP32, AI disease detection on leaf photos,
            and personalized care advice — all in one beautiful dashboard.
          </p>

          <div className="flex flex-wrap justify-center gap-4">
            <Link
              to="/login"
              className="bg-leaf-500 hover:bg-leaf-400 text-white font-semibold px-8 py-3.5 rounded-full transition-all shadow-lg shadow-leaf-500/30 hover:shadow-leaf-400/40 hover:-translate-y-0.5"
            >
              Start free →
            </Link>
            <a
              href="#features"
              className="backdrop-blur-xl bg-white/10 border border-white/20 hover:bg-white/20 text-white font-semibold px-8 py-3.5 rounded-full transition-all hover:-translate-y-0.5"
            >
              See features
            </a>
          </div>
        </div>

        {/* Bottom fade into stats */}
        <div className="absolute bottom-0 inset-x-0 h-32 bg-gradient-to-t from-gray-950 to-transparent" />
      </section>

      {/* ── Stats Bar ── */}
      <section className="relative z-10 -mt-16 pb-8">
        <div className="max-w-5xl mx-auto px-4 sm:px-6">
          <div className="backdrop-blur-xl bg-white/[0.07] border border-white/[0.12] rounded-2xl p-6 sm:p-8 grid grid-cols-2 md:grid-cols-4 gap-6 md:gap-4">
            {STATS.map((s) => (
              <div key={s.label} className="text-center">
                <div className="text-2xl sm:text-3xl font-bold text-white mb-1">{s.value}</div>
                <div className="text-xs sm:text-sm text-gray-400">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features Section ── */}
      <section id="features" className="py-24 sm:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <span className="text-leaf-400 font-semibold text-sm tracking-wide uppercase">Features</span>
            <h2 className="mt-3 text-3xl sm:text-4xl font-bold text-white">
              Everything your plants need
            </h2>
            <p className="mt-4 text-gray-400 max-w-2xl mx-auto">
              From hardware sensors to deep learning — a complete ecosystem for plant health.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((f) => (
              <div
                key={f.title}
                className="group backdrop-blur-xl bg-white/[0.04] border border-white/[0.08] rounded-2xl p-6 hover:bg-white/[0.08] hover:border-white/[0.16] transition-all duration-300 hover:-translate-y-1"
              >
                <div className="text-4xl mb-4">{f.icon}</div>
                <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-leaf-400 transition-colors">
                  {f.title}
                </h3>
                <p className="text-sm text-gray-400 leading-relaxed">{f.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How It Works ── */}
      <section id="how-it-works" className="py-24 sm:py-32 bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <span className="text-leaf-400 font-semibold text-sm tracking-wide uppercase">How it works</span>
            <h2 className="mt-3 text-3xl sm:text-4xl font-bold text-white">
              Three steps to healthier plants
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8 relative">
            {/* Connector line (desktop) */}
            <div className="hidden md:block absolute top-16 left-[16.67%] right-[16.67%] h-px bg-gradient-to-r from-leaf-600/0 via-leaf-600/40 to-leaf-600/0" />

            {STEPS.map((s) => (
              <div key={s.number} className="text-center relative">
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-leaf-600/20 border border-leaf-500/30 text-2xl mb-6">
                  {s.icon}
                </div>
                <div className="text-xs font-bold text-leaf-500 tracking-widest mb-2">STEP {s.number}</div>
                <h3 className="text-xl font-semibold text-white mb-3">{s.title}</h3>
                <p className="text-sm text-gray-400 leading-relaxed max-w-xs mx-auto">{s.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Supported Plants ── */}
      <section id="about" className="py-24 sm:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <span className="text-leaf-400 font-semibold text-sm tracking-wide uppercase">Supported Plants</span>
            <h2 className="mt-3 text-3xl sm:text-4xl font-bold text-white">
              Trained on 6 plant species
            </h2>
            <p className="mt-4 text-gray-400 max-w-2xl mx-auto">
              Our model recognizes healthy leaves and 29 disease classes across these crops — with more on the way.
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {SUPPORTED_PLANTS.map((p) => (
              <div
                key={p.name}
                className="backdrop-blur-xl bg-white/[0.04] border border-white/[0.08] rounded-2xl p-6 text-center hover:bg-white/[0.08] hover:border-white/[0.16] transition-all duration-300 hover:-translate-y-1"
              >
                <div className="text-5xl mb-3">{p.emoji}</div>
                <div className="text-sm font-medium text-gray-300">{p.name}</div>
                <div className="text-xs text-gray-500 mt-1">{p.diseases} diseases</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Bottom CTA ── */}
      <section className="py-24 sm:py-32">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
          <div className="backdrop-blur-xl bg-white/[0.05] border border-white/[0.1] rounded-3xl p-10 sm:p-16 relative overflow-hidden">
            {/* Glow accents */}
            <div className="absolute -top-24 -right-24 w-64 h-64 bg-leaf-500/20 rounded-full blur-3xl" />
            <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-teal-500/20 rounded-full blur-3xl" />

            <div className="relative z-10">
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
                Ready to grow smarter?
              </h2>
              <p className="text-gray-400 mb-8 max-w-lg mx-auto">
                Join the community of growers using AI and IoT to keep their plants thriving.
                Free to start, no credit card required.
              </p>
              <Link
                to="/login"
                className="inline-block bg-leaf-500 hover:bg-leaf-400 text-white font-semibold px-10 py-4 rounded-full transition-all shadow-lg shadow-leaf-500/30 hover:shadow-leaf-400/40 hover:-translate-y-0.5"
              >
                Create your free account →
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-white/[0.06] py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8 mb-10">
            {/* Brand */}
            <div>
              <div className="flex items-center gap-2 mb-4">
                <span className="text-xl">🌿</span>
                <span className="font-bold text-white">Smart Plant Doctor</span>
              </div>
              <p className="text-sm text-gray-500 leading-relaxed">
                AI-powered plant health monitoring and disease detection platform.
              </p>
            </div>

            {/* Product */}
            <div>
              <h4 className="text-sm font-semibold text-gray-300 mb-4">Product</h4>
              <ul className="space-y-2 text-sm text-gray-500">
                <li><a href="#features" className="hover:text-gray-300 transition-colors">Features</a></li>
                <li><a href="#how-it-works" className="hover:text-gray-300 transition-colors">How it Works</a></li>
                <li><a href="#about" className="hover:text-gray-300 transition-colors">Supported Plants</a></li>
              </ul>
            </div>

            {/* Resources */}
            <div>
              <h4 className="text-sm font-semibold text-gray-300 mb-4">Resources</h4>
              <ul className="space-y-2 text-sm text-gray-500">
                <li><a href="#" className="hover:text-gray-300 transition-colors">Documentation</a></li>
                <li><a href="#" className="hover:text-gray-300 transition-colors">API Reference</a></li>
                <li><a href="#" className="hover:text-gray-300 transition-colors">Firmware Guide</a></li>
              </ul>
            </div>

            {/* Account */}
            <div>
              <h4 className="text-sm font-semibold text-gray-300 mb-4">Account</h4>
              <ul className="space-y-2 text-sm text-gray-500">
                <li><Link to="/login" className="hover:text-gray-300 transition-colors">Sign in</Link></li>
                <li><Link to="/login" className="hover:text-gray-300 transition-colors">Create account</Link></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-white/[0.06] pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-xs text-gray-600">
              &copy; {new Date().getFullYear()} Smart Plant Doctor. All rights reserved.
            </p>
            <div className="flex gap-6 text-xs text-gray-600">
              <a href="#" className="hover:text-gray-400 transition-colors">Privacy</a>
              <a href="#" className="hover:text-gray-400 transition-colors">Terms</a>
              <a href="#" className="hover:text-gray-400 transition-colors">Contact</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
