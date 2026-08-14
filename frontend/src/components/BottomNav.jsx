// メイン画面下部のタブコンポーネント

import { NavLink } from "react-router-dom";

import "./bottomNav.css";

function BottomNav() {
  const items = [
    {
      to: "/chat",
      label: "送信",
      icon: (
        <path d="M21.4 2.7 3.2 9.6c-1.2.5-1.1 2.2.2 2.5l7.1 1.7 1.7 7.1c.3 1.3 2 1.4 2.5.2l6.9-18.2c.2-.5-.3-1-1-.8L9.9 13.8m.6 0 4.2-4.2" />
      ),
    },
    {
      to: "/view",
      label: "閲覧",
      icon: <path d="M21 12a8.5 8.5 0 0 1-9 8.5 9.7 9.7 0 0 1-4-.8L3 21l1.4-4.4A8.7 8.7 0 0 1 3 12a8.5 8.5 0 0 1 9-8.5 8.5 8.5 0 0 1 9 8.5Z" />,
    },
    {
      to: "/search",
      label: "検索",
      icon: <><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></>,
    },
    {
      to: "/account",
      label: "アカウント",
      icon: <><circle cx="12" cy="12" r="10" /><circle cx="12" cy="9" r="3" /><path d="M6.5 19c.8-3 2.7-4.5 5.5-4.5s4.7 1.5 5.5 4.5" /></>,
    },
  ];

  return (
    <nav className="bottom-nav" aria-label="メインメニュー">
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          aria-label={item.label}
          title={item.label}
          className={({ isActive }) =>
            isActive ? "bottom-nav-item active" : "bottom-nav-item"
          }
        >
          <svg className="bottom-nav-icon" viewBox="0 0 24 24" aria-hidden="true">
            {item.icon}
          </svg>
        </NavLink>
      ))}
    </nav>
  );
}

export default BottomNav;
