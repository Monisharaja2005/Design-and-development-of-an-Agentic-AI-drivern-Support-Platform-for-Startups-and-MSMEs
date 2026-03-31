import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ error, errorInfo });
    console.error('React ErrorBoundary caught:', error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-8">
        <div className="max-w-md w-full bg-white rounded-3xl shadow-2xl border border-slate-200 p-8 text-center space-y-6">
          <div className="w-20 h-20 mx-auto bg-red-100 rounded-2xl flex items-center justify-center">
            <svg className="w-10 h-10 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          
          <div className="space-y-3">
            <h2 className="text-2xl font-black text-slate-900 tracking-tight">
              Something went wrong
            </h2>
            <p className="text-slate-600 font-medium leading-relaxed">
              A component crashed during rendering. Check browser console for details.
            </p>
            {this.state.error && (
              <details className="text-left bg-slate-50 p-4 rounded-xl border border-slate-200 text-sm">
                <summary className="font-bold text-slate-900 cursor-pointer mb-2">Error Details</summary>
                <pre className="mt-2 text-xs text-slate-700 bg-slate-100 p-3 rounded-lg overflow-auto max-h-32 font-mono">
                  {this.state.error?.message || 'Unknown error'}
                </pre>
              </details>
            )}
          </div>

          <div className="flex flex-col sm:flex-row gap-3 pt-4">
            <button
              onClick={this.handleRetry}
              className="flex-1 bg-brand-primary text-white py-3 px-6 rounded-xl font-bold hover:shadow-lg transition-all text-sm"
            >
              Try Again
            </button>
            <button
              onClick={() => window.location.reload()}
              className="flex-1 border border-slate-200 bg-white py-3 px-6 rounded-xl font-semibold text-slate-700 hover:bg-slate-50 transition-all text-sm"
            >
              Reload Page
            </button>
          </div>

          <div className="text-xs text-slate-500 space-y-1">
            <p>💡 Tip: Check browser console (F12) for specific error details</p>
            <p>📄 Missing components? Verify all imports exist.</p>
          </div>
        </div>
      </div>
    );
  }
}

