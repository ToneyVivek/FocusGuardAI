/**
 * Options page component for FocusGuard Extension
 * Displays settings placeholder
 */

import { EXTENSION } from '../../constants';

export function Options() {
  return (
    <div className="options-container">
      <h1 className="options-title">{EXTENSION.NAME} Settings</h1>
      <p className="options-message">This page will be expanded later.</p>
    </div>
  );
}
