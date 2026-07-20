import { Popup } from './components/Popup';
import { AuthProvider } from './contexts/AuthContext';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <Popup />
    </AuthProvider>
  );
}

export default App;
