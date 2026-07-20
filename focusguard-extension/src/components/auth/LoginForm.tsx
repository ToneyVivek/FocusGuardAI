/**
 * Login Form Component for FocusGuard Extension
 * Handles user authentication with email and password
 */

import { useState, type FormEvent } from 'react';
import { useAuth } from '../../contexts/AuthContext';

/**
 * Login Form Component
 */
export function LoginForm() {
  const { login, loading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  /**
   * Handle form submission
   */
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    // Basic validation
    if (!email || !password) {
      setError('Please fill in all fields');
      setIsSubmitting(false);
      return;
    }

    if (!email.includes('@')) {
      setError('Please enter a valid email address');
      setIsSubmitting(false);
      return;
    }

    try {
      await login(email, password);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Login failed';
      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="login-form">
      <h2 className="login-title">Login to FocusGuard</h2>
      
      {error && (
        <div className="login-error">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="login-form-element">
        <div className="form-group">
          <label htmlFor="email" className="form-label">
            Email
          </label>
          <input
            id="email"
            type="email"
            className="form-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="your@email.com"
            disabled={loading || isSubmitting}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="password" className="form-label">
            Password
          </label>
          <input
            id="password"
            type="password"
            className="form-input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            disabled={loading || isSubmitting}
            required
          />
        </div>

        <button
          type="submit"
          className="login-button"
          disabled={loading || isSubmitting}
        >
          {isSubmitting ? 'Logging in...' : 'Login'}
        </button>
      </form>
    </div>
  );
}
