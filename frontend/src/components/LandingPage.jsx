function LandingPage({ onGetStarted, onWatchDemo, onLogin }) {
  return (
    <div className="page page-landing">
      {/* Header */}
      <header className="landing-header">
        <a href="#" className="logo">
          <div className="logo-icon">SI</div>
          <span className="logo-text">SchemeIQ</span>
        </a>
        
        <nav>
          <a href="#home">Home</a>
          <a href="#schemes">Schemes</a>
          <a href="#about">About</a>
          <a href="#contact">Contact</a>
        </nav>
        
        <div className="header-actions">
          <button className="btn-secondary" onClick={onLogin}>Sign In</button>
          <button className="btn-primary" onClick={onGetStarted}>Get Started</button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <div className="hero-badge">
            🇮🇳 India's #1 Scheme Platform
          </div>
          
          <h1 className="hero-title">
            Find Every Government Scheme<br />
            Your Business <span className="highlight">Deserves</span>
          </h1>
          
          <p className="hero-subtitle">
            AI-powered scheme matching, document verification, and guided applications 
            for Startups & MSMEs across India.
          </p>
          
          <div className="hero-ctas">
            <button className="btn-primary" onClick={onGetStarted}>
              Discover My Schemes
            </button>
            <button className="btn-secondary" onClick={onWatchDemo}>
              ▶ Watch Demo
            </button>
          </div>
          
          <div className="trust-badges">
            <span>3,000+ Schemes</span>
            <span>Real-Time Updates</span>
            <span>Free to Use</span>
          </div>
        </div>
        
        <div className="hero-visual">
          <div className="dashboard-mockup">
            <div className="mockup-header">
              <div className="mockup-dot red" />
              <div className="mockup-dot yellow" />
              <div className="mockup-dot green" />
            </div>
            
            {/* Scheme Card 1 */}
            <div className="mockup-scheme-card">
              <div className="mockup-scheme-header">
                <span className="mockup-badge">STARTUP</span>
                <span className="match-badge">94% Match</span>
              </div>
              <div className="mockup-scheme-name">Startup India Seed Fund</div>
              <div className="mockup-scheme-ministry">DPIIT, Ministry of Commerce</div>
            </div>
            
            {/* Scheme Card 2 */}
            <div className="mockup-scheme-card">
              <div className="mockup-scheme-header">
                <span className="mockup-badge">MSME</span>
                <span className="match-badge">88% Match</span>
              </div>
              <div className="mockup-scheme-name">CGTMSE Collateral-Free Loan</div>
              <div className="mockup-scheme-ministry">Ministry of MSME, SIDBI</div>
            </div>
            
            {/* Scheme Card 3 */}
            <div className="mockup-scheme-card">
              <div className="mockup-scheme-header">
                <span className="mockup-badge">MSME</span>
                <span className="match-badge">82% Match</span>
              </div>
              <div className="mockup-scheme-name">PMEGP Business Loan</div>
              <div className="mockup-scheme-ministry">Ministry of KVIC</div>
            </div>
            
            {/* AI Chat Bubble */}
            <div className="mockup-chat-bubble">
              🎉 You qualify for ₹52 Lakhs in funding!
            </div>
          </div>
        </div>
      </section>

      {/* Stats Bar */}
      <div className="stats-bar">
        <div className="stat-item">
          <span className="stat-number">3,000+</span>
          <span className="stat-label">Active Schemes</span>
        </div>
        <div className="stat-divider" />
        <div className="stat-item">
          <span className="stat-number">₹50,000 Cr</span>
          <span className="stat-label">Available Funding</span>
        </div>
        <div className="stat-divider" />
        <div className="stat-item">
          <span className="stat-number">28</span>
          <span className="stat-label">States Covered</span>
        </div>
        <div className="stat-divider" />
        <div className="stat-item">
          <span className="stat-number">50+</span>
          <span className="stat-label">Ministries</span>
        </div>
      </div>
    </div>
  );
}

export default LandingPage;
