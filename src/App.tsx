import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import Layout from './components/Layout/Layout';
import SchedulerPage from './components/Scheduler/SchedulerPage';
import ConnectionsPage from './components/Connections/ConnectionsPage';
import MigrationDBPage from './components/MigrationDB/MigrationDBPage';
import MigrationCSVPage from './components/MigrationCSV/MigrationCSVPage';

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<SchedulerPage />} />
            <Route path="connections" element={<ConnectionsPage />} />
            <Route path="migration-db" element={<MigrationDBPage />} />
            <Route path="migration-csv" element={<MigrationCSVPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}
