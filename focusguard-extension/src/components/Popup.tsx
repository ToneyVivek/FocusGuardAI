/**
 * Popup component for FocusGuard Extension
 * Displays extension status and version
 */

import { EXTENSION } from '../constants';

export function Popup() {
  return (
    <div className="popup-container">
      <h1 className="popup-title">{EXTENSION.NAME}</h1>
      <p className="popup-version">Version {EXTENSION.VERSION}</p>
      <p className="popup-status">Status: Extension Loaded Successfully</p>
    </div>
  );
}
