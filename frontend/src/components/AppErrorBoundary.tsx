import React from 'react';

type Props = {
  children: React.ReactNode;
};

type State = {
  hasError: boolean;
  message: string;
};

export default class AppErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, message: '' };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error?.message || 'Unknown rendering error' };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // Keep this in console for easier demo-time debugging.
    console.error('App render error:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
          <div className="w-full max-w-xl rounded-xl border border-red-200 bg-white p-6 shadow-sm">
            <h1 className="text-lg font-semibold text-red-700">UI Runtime Error</h1>
            <p className="mt-2 text-sm text-gray-700">
              The app hit a client-side exception and could not render this screen.
            </p>
            <pre className="mt-4 rounded bg-red-50 p-3 text-xs text-red-700 overflow-auto">
              {this.state.message}
            </pre>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="mt-4 inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Reload
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
