import React from 'react';

const LoginStep = ({ 
  formData, 
  errors, 
  authMode, 
  signUpData, 
  passwordStrength, 
  showPassword, 
  rememberLogin, 
  authLoading, 
  onLoginChange, 
  onSignUpChange, 
  onTogglePassword, 
  onToggleRemember, 
  onAuthModeChange, 
  t, 
  trText 
}) => {
  return (
    <div className="login-wrap">
      <div className="login-hero">
        <span className="pill-status">{t("secure_access", "Secure Access")}</span>
        <h2>{t("welcome_back", "Welcome back to Scheme Intelligence")}</h2>
        <p>{t("sign_in_desc", "Sign in to continue onboarding, discover matching schemes, and use the live scheme assistant.")}</p>
        <ul className="simple-list">
          <li>{t("bullet_structured_discovery", "Structured scheme discovery")}</li>
          <li>{t("bullet_live_assistant", "Live assistant responses")}</li>
          <li>{t("bullet_application_ready", "Application-ready guidance")}</li>
        </ul>
      </div>
      <div className="login-form-card">
        <div className="auth-tabs">
          <button
            type="button"
            className={`auth-tab ${authMode === "signin" ? "active" : ""}`}
            onClick={() => onAuthModeChange("signin")}
          >
            {t("sign_in", "Sign In")}
          </button>
          <button
            type="button"
            className={`auth-tab ${authMode === "signup" ? "active" : ""}`}
            onClick={() => onAuthModeChange("signup")}
          >
            {t("sign_up", "Sign Up")}
          </button>
        </div>

        {authMode === "signin" ? (
          <>
            <div className="field">
              <label htmlFor="email">{t("email", "Email")}</label>
              <input
                id="email"
                name="email"
                type="email"
                value={formData.login.email}
                onChange={onLoginChange}
                placeholder="founder@company.in"
              />
              {errors.email && <span className="error">{trText(errors.email)}</span>}
            </div>
            <div className="field">
              <label htmlFor="password">{t("password", "Password")}</label>
              <div className="password-field">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  value={formData.login.password}
                  onChange={onLoginChange}
                  placeholder={t("enter_password", "Enter your password")}
                />
                <button
                  type="button"
                  className="ghost-btn"
                  onClick={onTogglePassword}
                >
                  {showPassword ? t("hide", "Hide") : t("show", "Show")}
                </button>
              </div>
              {errors.password && (
                <span className="error">{trText(errors.password)}</span>
              )}
              <div className="strength">
                <div className="strength-bar">
                  <span
                    style={{ width: `${(passwordStrength.score / 4) * 100}%` }}
                  />
                </div>
                <span className="strength-label">
                  {t("password_strength", "Password strength")}: {t(
                    `pw_${String(passwordStrength.label || "").toLowerCase()}`,
                    passwordStrength.label
                  )}
                </span>
              </div>
            </div>
          </>
        ) : (
          <>
            <div className="field">
              <label htmlFor="fullName">{t("full_name", "Full name")}</label>
              <input
                id="fullName"
                name="fullName"
                value={signUpData.fullName}
                onChange={onSignUpChange}
                placeholder={t("your_full_name", "Your full name")}
              />
              {errors.fullName && <span className="error">{trText(errors.fullName)}</span>}
            </div>
            <div className="field">
              <label htmlFor="signupEmail">{t("email", "Email")}</label>
              <input
                id="signupEmail"
                name="email"
                type="email"
                value={signUpData.email}
                onChange={onSignUpChange}
                placeholder="founder@company.in"
              />
              {errors.signupEmail && <span className="error">{trText(errors.signupEmail)}</span>}
            </div>
            <div className="field">
              <label htmlFor="signupPassword">{t("create_password", "Create password")}</label>
              <div className="password-field">
                <input
                  id="signupPassword"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  value={signUpData.password}
                  onChange={onSignUpChange}
                  placeholder={t("create_strong_password", "Create a strong password")}
                />
                <button
                  type="button"
                  className="ghost-btn"
                  onClick={onTogglePassword}
                >
                  {showPassword ? t("hide", "Hide") : t("show", "Show")}
                </button>
              </div>
              {errors.signupPassword && <span className="error">{trText(errors.signupPassword)}</span>}
              <div className="strength">
                <div className="strength-bar">
                  <span
                    style={{ width: `${(passwordStrength.score / 4) * 100}%` }}
                  />
                </div>
                <span className="strength-label">
                  {t("password_strength", "Password strength")}: {t(
                    `pw_${String(passwordStrength.label || "").toLowerCase()}`,
                    passwordStrength.label
                  )}
                </span>
              </div>
            </div>
            <div className="field">
              <label htmlFor="confirmPassword">{t("confirm_password", "Confirm password")}</label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type={showPassword ? "text" : "password"}
                value={signUpData.confirmPassword}
                onChange={onSignUpChange}
                placeholder={t("reenter_password", "Re-enter password")}
              />
              {errors.confirmPassword && <span className="error">{trText(errors.confirmPassword)}</span>}
            </div>
          </>
        )}
        <div className="login-row">
          <label className="login-check">
            <input
              type="checkbox"
              checked={rememberLogin}
              onChange={onToggleRemember}
            />
            <span>{t("remember_me", "Remember me")}</span>
          </label>
          <button type="button" className="ghost-btn">
            {t("forgot_password", "Forgot password")}
          </button>
        </div>
        {errors.auth && <div className="error">{trText(errors.auth)}</div>}
        {authSession?.user?.email && (
          <div className="helper">{t("signed_in_as", "Signed in as")} {authSession.user.email}</div>
        )}
      </div>
    </div>
  );
};

export default LoginStep;

