import { useState } from "react";
import { useNavigate, Link, Navigate } from "react-router-dom";

import { useAuth } from "../../contexts/auth-context";
import { getErrorMessage } from "../../utils/error";

import "./auth.css";

function Login() {
  const navigate = useNavigate();
  const { authStatus, login } = useAuth();

  const [formData, setFormData] = useState({
    id: "",
    password: "",
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleLogin = async (e) => {
    e.preventDefault();

    try {
      await login(formData);
      navigate("/chat");

    } catch (error) {
      console.error(error);
      alert(getErrorMessage(error));
    }
  };

  if (authStatus === "authenticated") return <Navigate to="/chat" replace />;

  return (
    <div className="auth-page">
      <div className="auth-container">

        <h2 className="auth-title">
          ログイン
        </h2>

        <form
          className="auth-form"
          onSubmit={handleLogin}
        >

          <input
            type="text"
            name="id"
            placeholder="ID"
            value={formData.id}
            onChange={handleChange}
          />

          <input
            type="password"
            name="password"
            placeholder="パスワード"
            value={formData.password}
            onChange={handleChange}
          />

          <button
            className="auth-button"
            type="submit"
          >
            ログイン
          </button>

        </form>

        <Link
          className="auth-link"
          to="/register"
        >
          新規ユーザー登録はこちら
        </Link>

      </div>
    </div>
  );
}

export default Login;
