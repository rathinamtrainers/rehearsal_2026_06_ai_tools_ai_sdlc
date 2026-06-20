import { useState } from 'react';
import { BrandPanel } from './BrandPanel';
import { LoginForm } from './LoginForm';
import { RegisterForm } from './RegisterForm';

type Screen = 'login' | 'register';

/**
 * Split-screen auth layout: brand panel on the left, the active form on the
 * right. Reproduces the LearnFlow Auth design and toggles between the login
 * and register flows.
 */
export function AuthScreen() {
  const [screen, setScreen] = useState<Screen>('login');

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'grid',
        gridTemplateColumns: 'minmax(380px,1fr) minmax(480px,1.05fr)',
        fontFamily: 'Inter,system-ui,sans-serif',
        background: '#f8fafc',
      }}
    >
      <BrandPanel />

      <main
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '48px 24px',
          background: '#ffffff',
        }}
      >
        <div style={{ width: '100%', maxWidth: 440 }}>
          {screen === 'login' ? (
            <LoginForm onGoToRegister={() => setScreen('register')} />
          ) : (
            <RegisterForm onGoToLogin={() => setScreen('login')} />
          )}
        </div>
      </main>
    </div>
  );
}
