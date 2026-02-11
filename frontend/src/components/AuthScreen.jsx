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
    <div className="page auth-page">
      <div className="bg-shape" aria-hidden="true" />
      <div className="bg-grid" aria-hidden="true" />

      <main className="auth-shell auth-entry">
        <section className="portal-panel">
          <p className="portal-kicker">National Startup and MSME Facilitation Portal</p>
          <h2>Single Gateway for Onboarding, Compliance, and Scheme Access</h2>
          <p>
            Build a verified business profile once, keep it updated, and receive targeted scheme workflows with
            document readiness status.
          </p>

          <div className="panel-metrics">
            <article>
              <span>250+</span>
              <small>Active scheme tracks</small>
            </article>
            <article>
              <span>Live</span>
              <small>Profile-based eligibility</small>
            </article>
            <article>
              <span>Role-safe</span>
              <small>Secure JWT session model</small>
            </article>
          </div>

          <div className="auth-feature-grid">
            <div>
              <h4>Standardized onboarding</h4>
              <p>Structured registration for founders, entities, and compliance identifiers.</p>
            </div>
            <div>
              <h4>Adaptive recommendations</h4>
              <p>Schemes are scored from real profile signals and update as your data changes.</p>
            </div>
            <div>
              <h4>Document readiness</h4>
              <p>Track verification quality and fix blockers before final application submission.</p>
            </div>
          </div>
        </section>

        <section className="card auth-card">
          <div className="mode-switch" role="tablist" aria-label="Auth mode">
            <button
              type="button"
              className={mode === 'login' ? 'mode-btn active' : 'mode-btn'}
              onClick={() => {
                setMode('login');
              }}
            >
              Sign In
            </button>
            <button
              type="button"
              className={mode === 'register' ? 'mode-btn active' : 'mode-btn'}
              onClick={() => {
                setMode('register');
              }}
            >
              Create Account
            </button>
          </div>

          <p className="form-kicker">Secure Access</p>
          <h1>{isRegister ? 'Create your portal account' : 'Welcome back'}</h1>
          <p className="subtitle">
            {isRegister
              ? 'Register your account to start your Startup/MSME profile setup.'
              : 'Sign in to continue your profile, schemes, and document workflows.'}
          </p>

          <form className="form" onSubmit={submitAuth}>
            <div className="grid-two compact-grid">
              <div>
                <label htmlFor="email">Email</label>
                <input
                  id="email"
                  type="email"
                  placeholder="you@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              {isRegister ? (
                <div>
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
              ) : (
                <div className="inline-control">
                  <label className="check-row" htmlFor="remember">
                    <input
                      id="remember"
                      type="checkbox"
                      checked={remember}
                      onChange={(e) => setRemember(e.target.checked)}
                    />
                    Keep me signed in
                  </label>
                </div>
              )}
            </div>

            {isRegister ? (
              <div>
                <label htmlFor="userType">Account Type</label>
                <select id="userType" value={userType} onChange={(e) => setUserType(e.target.value)} required>
                  <option value="business">Business</option>
                  <option value="individual">Individual</option>
                </select>
              </div>
            ) : null}

            <label htmlFor="password">Password</label>
            <div className="password-row">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <button type="button" className="ghost-btn" onClick={() => setShowPassword((v) => !v)}>
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>

            {isRegister ? (
              <section className="strength-box" aria-live="polite">
                <div className="strength-head">
                  <p>Password strength</p>
                  <strong>{strength}/5</strong>
                </div>
                <div className="strength-meter">
                  <div className="strength-fill" style={{ width: `${(strength / 5) * 100}%` }} />
                </div>
                <ul>
                  {checks.map((check) => (
                    <li key={check.key} className={check.pass ? 'ok' : 'bad'}>
                      {check.pass ? 'Met' : 'Pending'}: {check.label}
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}

            <button type="submit" disabled={authLoading || !canSubmit}>
              {authLoading ? 'Please wait...' : isRegister ? 'Create Account' : 'Login to Portal'}
            </button>
          </form>

          {!isRegister ? (
            <div className="forgot-wrap">
              <button type="button" className="link-btn" onClick={() => setShowForgot((v) => !v)}>
                {showForgot ? 'Hide password reset' : 'Forgot password?'}
              </button>
              {showForgot ? (
                <div className="forgot-panel">
                  <form className="form" onSubmit={requestResetToken}>
                    <label htmlFor="resetEmail">Account Email</label>
                    <input
                      id="resetEmail"
                      type="email"
                      value={resetEmail}
                      onChange={(e) => setResetEmail(e.target.value)}
                      required
                    />
                    <button type="submit">Generate Reset Token</button>
                  </form>
                  <form className="form" onSubmit={submitResetPassword}>
                    <label htmlFor="resetToken">Reset Token</label>
                    <input
                      id="resetToken"
                      value={resetToken}
                      onChange={(e) => setResetToken(e.target.value)}
                      required
                    />
                    <label htmlFor="newPassword">New Password</label>
                    <input
                      id="newPassword"
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      required
                    />
                    <button type="submit">Reset Password</button>
                  </form>
                </div>
              ) : null}
            </div>
          ) : null}

          {message ? <p className="message">{message}</p> : null}
          {error ? <p className="error">{error}</p> : null}
        </section>
      </main>
    </div>
  );
}

export default AuthScreen;
