function AuthScreen({
  mode,
  setMode,
  email,
  setEmail,
  password,
  setPassword,
  phone,
  setPhone,
  userType,
  setUserType,
  showPassword,
  setShowPassword,
  remember,
  setRemember,
  checks,
  strength,
  authLoading,
  canSubmit,
  submitAuth,
  showForgot,
  setShowForgot,
  resetEmail,
  setResetEmail,
  resetToken,
  setResetToken,
  newPassword,
  setNewPassword,
  requestResetToken,
  submitResetPassword,
  message,
  error,
}) {
  const isRegister = mode === 'register';

  return (
    <div className="auth-page">
      {/* Left Panel - Branding */}
      <div className="auth-brand-panel">
        <div className="brand-content">
          <div className="brand-logo">
            <div className="logo-icon">SI</div>
            <span className="logo-text">SchemeIQ</span>
          </div>
          
          <h2>Single Gateway for Onboarding, Compliance, and Scheme Access</h2>
          
          <p>Build a verified business profile once, keep it updated, and receive targeted scheme workflows with document readiness status.</p>

          <div className="brand-features">
            <div className="feature-item">
              <span className="feature-icon">📋</span>
              <div>
                <h4>Standardized onboarding</h4>
                <p>Structured registration for founders, entities, and compliance identifiers.</p>
              </div>
            </div>
            <div className="feature-item">
              <span className="feature-icon">🎯</span>
              <div>
                <h4>Adaptive recommendations</h4>
                <p>Schemes are scored from real profile signals and update as your data changes.</p>
              </div>
            </div>
            <div className="feature-item">
              <span className="feature-icon">📄</span>
              <div>
                <h4>Document readiness</h4>
                <p>Track verification quality and fix blockers before final application.</p>
              </div>
            </div>
          </div>

          <div className="brand-stats">
            <div className="stat-item">
              <span className="stat-value">250+</span>
              <span className="stat-label">Active schemes</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">Live</span>
              <span className="stat-label">Profile-based eligibility</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">Secure</span>
              <span className="stat-label">JWT session model</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Form */}
      <div className="auth-form-panel">
        <div className="form-container">
          <div className="form-header">
            <div className="form-tabs">
              <button 
                type="button"
                className={`tab-item ${mode === 'login' ? 'active' : ''}`}
                onClick={() => setMode('login')}
              >
                Sign In
              </button>
              <button 
                type="button"
                className={`tab-item ${mode === 'register' ? 'active' : ''}`}
                onClick={() => setMode('register')}
              >
                Create Account
              </button>
            </div>
            
            <h1>{isRegister ? 'Create your account' : 'Welcome back'}</h1>
            <p className="form-subtitle">
              {isRegister 
                ? 'Register your account to start your Startup/MSME profile setup.' 
                : 'Sign in to continue your profile, schemes, and document workflows.'}
            </p>
          </div>

          <form className="auth-form" onSubmit={submitAuth}>
            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <input
                id="email"
                type="email"
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            {isRegister && (
              <div className="form-group">
                <label htmlFor="phone">Phone Number</label>
                <input
                  id="phone"
                  type="tel"
                  placeholder="10-digit mobile"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                  required
                />
              </div>
            )}

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <div className="password-input-group">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button 
                  type="button" 
                  className="toggle-password"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
            </div>

            {isRegister && (
              <div className="password-strength">
                <div className="strength-header">
                  <span>Password strength</span>
                  <span className={`strength-level level-${strength}`}>{strength}/5</span>
                </div>
                <div className="strength-bar">
                  <div 
                    className={`strength-fill fill-${strength}`} 
                    style={{ width: `${(strength / 5) * 100}%` }}
                  />
                </div>
                <ul className="strength-requirements">
                  {checks.map((check) => (
                    <li key={check.key} className={check.pass ? 'met' : ''}>
                      <span className="check-icon">{check.pass ? '✓' : '○'}</span>
                      {check.label}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {!isRegister && (
              <div className="form-options">
                <label className="remember-me">
                  <input
                    type="checkbox"
                    checked={remember}
                    onChange={(e) => setRemember(e.target.checked)}
                  />
                  <span>Keep me signed in</span>
                </label>
                <button 
                  type="button" 
                  className="forgot-link"
                  onClick={() => setShowForgot(!showForgot)}
                >
                  Forgot password?
                </button>
              </div>
            )}

            {showForgot && !isRegister && (
              <div className="forgot-panel">
                <form onSubmit={requestResetToken}>
                  <div className="form-group">
                    <label htmlFor="resetEmail">Account Email</label>
                    <input
                      id="resetEmail"
                      type="email"
                      value={resetEmail}
                      onChange={(e) => setResetEmail(e.target.value)}
                      placeholder="Enter your email"
                      required
                    />
                  </div>
                  <button type="submit" className="btn-small">Send Reset Link</button>
                </form>
                
                {resetToken && (
                  <form onSubmit={submitResetPassword} className="reset-form">
                    <div className="form-group">
                      <label htmlFor="resetToken">Reset Token</label>
                      <input
                        id="resetToken"
                        type="text"
                        value={resetToken}
                        onChange={(e) => setResetToken(e.target.value)}
                        placeholder="Enter token"
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label htmlFor="newPassword">New Password</label>
                      <input
                        id="newPassword"
                        type="password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        placeholder="Enter new password"
                        required
                      />
                    </div>
                    <button type="submit" className="btn-small">Reset Password</button>
                  </form>
                )}
              </div>
            )}

            {message && <div className="form-message success">{message}</div>}
            {error && <div className="form-message error">{error}</div>}

            <button type="submit" disabled={authLoading || !canSubmit} className="btn-submit">
              {authLoading ? 'Please wait...' : isRegister ? 'Create Account' : 'Sign In'}
            </button>
          </form>

          <div className="form-footer">
            {!isRegister && (
              <p>Don't have an account? <button type="button" onClick={() => setMode('register')}>Create one</button></p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default AuthScreen;
