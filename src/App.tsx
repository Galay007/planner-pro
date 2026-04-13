import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import Layout from './components/Layout/Layout';
import SchedulerPage from './components/Scheduler/SchedulerPage';
import ConnectionsPage from './components/Connections/ConnectionsPage';
import MigrationDBPage from './components/MigrationDB/MigrationDBPage';
import MigrationCSVPage from './components/MigrationCSV/MigrationCSVPage';

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <SchedulerPage /> },
      { path: 'connections', element: <ConnectionsPage /> },
      { path: 'migration-db', element: <MigrationDBPage /> },
      { path: 'migration-csv', element: <MigrationCSVPage /> },
    ],
  },
]);

export default function App() {
  return (
    <ThemeProvider>
      <RouterProvider router={router} />
    </ThemeProvider>
  );
}
