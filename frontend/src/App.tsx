import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Overview from './pages/Overview';
import Recommendations from './pages/Recommendations';
import ClientInsights from './pages/ClientInsights';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/recommendations" element={<Recommendations />} />
            <Route path="/customer/:customerId" element={<ClientInsights />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;


