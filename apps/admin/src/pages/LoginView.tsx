import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { AuraBackground, NoiseTexture, TopbarBrand } from '@vistaflow/ui';
import './LoginView.css';

export default function LoginView() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login({ username, password });
      navigate('/', { replace: true });
    } catch (err: any) {
      const message = err.response?.data?.message || '登录失败，请检查用户名和密码';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <AuraBackground enableMouseTracking />
      <NoiseTexture opacity={0.03} />
      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <div className="text-eyebrow-sm" style={{ marginBottom: '8px' }}>ADMIN PORTAL</div>
            <TopbarBrand type="button" style={{ color: 'var(--color-starlight)' }}>
              VistaFlow
            </TopbarBrand>
          </div>

          <form className="login-form" onSubmit={handleSubmit}>
            {error && (
              <div className="login-error" role="alert">
                {error}
              </div>
            )}

            <div className="form-group">
              <label htmlFor="username" className="text-label-md">
                用户名
              </label>
              <input
                id="username"
                type="text"
                className="input-box"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="请输入用户名"
                required
                autoFocus
                disabled={isLoading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="password" className="text-label-md">
                密码
              </label>
              <input
                id="password"
                type="password"
                className="input-box"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="请输入密码"
                required
                disabled={isLoading}
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={isLoading || !username || !password}
              style={{ marginTop: '8px' }}
            >
              {isLoading ? '登录中...' : '登录'}
            </button>
          </form>
        </div>
      </div>
    </>
  );
}
