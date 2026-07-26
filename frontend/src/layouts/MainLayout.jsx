// メイン画面のレイアウト

import { Outlet } from "react-router-dom";
import BottomNav from "../components/BottomNav";

import "./mainLayout.css";

function MainLayout() {
  return (
    <div className="app-layout">
      <main className="app-content">
        <Outlet />
      </main>

      <BottomNav />
    </div>
  );
}

export default MainLayout;