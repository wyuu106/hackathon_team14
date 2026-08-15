import { Link, useNavigate } from "react-router-dom";
import "./account.css";

function Settings() {
  const navigate = useNavigate();
  const logout = () => {
    if (!window.confirm("本当にログアウトしますか？")) return;
    localStorage.removeItem("token");
    navigate("/login", { replace: true });
  };
  return <div className="account-page">
    <header className="sub-header settings-header">
      <button onClick={() => navigate("/account")}>
        戻る
      </button>

      <h1>設定</h1>
    </header>
    <Link className="settings-menu-item" to="/setting/templete">
      <span>
        <strong>テンプレート</strong>
      </span>
      <b>›</b>
    </Link>
    <button className="settings-menu-item logout-button" onClick={logout}>
      <strong>ログアウト</strong>
    </button>
  </div>;
}

export default Settings;
