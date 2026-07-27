import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";

import { API_URL } from "../../utils/api";
import { getErrorMessage } from "../../utils/error";

import "./auth.css";

function Login() {
  const navigate = useNavigate();

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

  const handleLogin = async () => {
    try {
      const response = await axios.post(
        `${API_URL}/login`,
        formData
      );

      console.log(response.data);

      // ログイン成功後
      navigate("/");

    } catch (error) {
      console.error(error);
      alert(getErrorMessage(error));
    }
  };

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