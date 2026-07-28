// メイン画面下部のタブコンポーネント

import { NavLink } from "react-router-dom";

import "./bottomNav.css";

function BottomNav() {
  return (
    <nav className="bottom-nav">
      <NavLink
        to="/send"
        className={({ isActive }) =>
          isActive ? "bottom-nav-item active" : "bottom-nav-item"
        }
      >
        送信
      </NavLink>

      <NavLink
        to="/view"
        className={({ isActive }) =>
          isActive ? "bottom-nav-item active" : "bottom-nav-item"
        }
      >
        閲覧
      </NavLink>

      <NavLink
        to="/search"
        className={({ isActive }) =>
          isActive ? "bottom-nav-item active" : "bottom-nav-item"
        }
      >
        検索
      </NavLink>

      <NavLink
        to="/account"
        className={({ isActive }) =>
          isActive ? "bottom-nav-item active" : "bottom-nav-item"
        }
      >
        アカウント
      </NavLink>
    </nav>
  );
}

export default BottomNav;