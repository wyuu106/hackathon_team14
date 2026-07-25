import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";

import { API_URL } from "../../utils/api";
import { getErrorMessage } from "../../utils/error";

import "./auth.css";
import "../../styles/button.css"

function Register() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    id: "",
    username: "",
    password: "",
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleRegister = async () => {
    try {
      await axios.post(
        `${API_URL}/register`,
        formData
      );

      alert("登録が完了しました");
      navigate("/login");

    } catch (error) {
      console.error(error);
      alert(getErrorMessage(error));
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container">

        <h2 className="auth-title">
          新規ユーザー登録
        </h2>

        <div className="auth-form">

          <input
            type="text"
            name="id"
            placeholder="ID"
            value={formData.id}
            onChange={handleChange}
          />

          <input
            type="text"
            name="username"
            placeholder="ユーザーネーム"
            value={formData.username}
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
            className="button-base button-primary"
            onClick={handleRegister}
          >
            登録
          </button>

        </div>

        <Link
          className="auth-link"
          to="/"
        >
          ログイン画面へ戻る
        </Link>
      </div>
    </div>
  );
}

export default Register;