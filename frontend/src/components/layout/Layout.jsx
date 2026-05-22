import TopAppBar from './TopAppBar';
import BottomNavBar from './BottomNavBar';
import Sidebar from './Sidebar';
import { Outlet } from 'react-router-dom';

export default function Layout() {
  return (
    <div className="bg-background text-on-surface font-body-md min-h-screen pb-24">
      <Sidebar />
      <TopAppBar />
      <div className="pt-24 px-6 max-w-7xl mx-auto">
        <Outlet />
      </div>
      <BottomNavBar />
    </div>
  );
}
