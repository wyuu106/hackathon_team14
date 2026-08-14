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
    <header className="sub-header"><button onClick={() => navigate("/account")}>戻る</button><h1>設定</h1></header>
    <Link className="settings-menu-item" to="/setting/templete"><span className="settings-icon" aria-hidden="true">♡</span><span><strong>テンプレート</strong><small>登録・削除・並び替え</small></span><b>›</b></Link>
    <button className="logout-button" onClick={logout}>ログアウト</button>
  </div>;
}

export default Settings;
