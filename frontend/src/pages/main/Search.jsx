import { useState } from "react";
import axios from "axios";

import { API_URL } from "../../utils/api";
import { getErrorMessage } from "../../utils/error";

import "./search.css";

function Search() {
  const [userId, setUserId] = useState("");
  const [user, setUser] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const token = localStorage.getItem("token");

  const handleChange = (event) => {
    const value = event.target.value;

    setUserId(value);
    setUser(null);
  };

  // IDからユーザー取得
  const fetchUser = async (targetUserId) => {
    const response = await axios.get(
      `${API_URL}/users/${encodeURIComponent(targetUserId)}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    setUser(response.data);
  };

  // 検索
  const handleSearch = async (event) => {
    event.preventDefault();

    const trimmedUserId = userId.trim();

    setUser(null);

    if (trimmedUserId === "") {
      setError("ユーザーIDを入力してください");
      return;
    }

    if (/\s/.test(trimmedUserId)) {
      setError("ユーザーIDに空白は使用できません");
      return;
    }

    try {
      setIsLoading(true);

      await fetchUser(trimmedUserId);

    } catch (error) {
      console.error(error);
      alert(getErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  };

  // フォロー（リクエスト送信）処理
  const handleFollow = async () => {
    try {
      await axios.post(
        `${API_URL}/follow/${user.id}`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      await fetchUser(user.id); // ユーザー情報再取得

    } catch (error) {
      console.error(error);
      alert(getErrorMessage(error));
    }
  };

  // フォロー解除処理
  const handleUnfollow = async () => {
    try {
      await axios.delete(
        `${API_URL}/follow/${user.id}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      await fetchUser(user.id); // ユーザー情報再取得
      
    } catch (error) {
      console.error(error);
      alert(getErrorMessage(error));
    }
  };

  return (
    <div className="search-page">
      <section className="search-container">
        <div className="search-header">
          <h1>ユーザー検索</h1>
          <p>ユーザーIDを入力して、フォローする相手を探せます。</p>
        </div>

        <form
          className="search-form"
          onSubmit={handleSearch}
        >
          <label
            className="search-label"
            htmlFor="userId"
          >
            ユーザーID
          </label>

          <div className="search-input-group">
            <span className="search-at">@</span>

            <input
              id="userId"
              className="user-search-input"
              type="text"
              value={userId}
              onChange={handleChange}
              placeholder="user123"
              autoComplete="off"
              maxLength={30}
            />

            <button
              className="user-search-button"
              type="submit"
              disabled={isLoading}
            >
              {isLoading ? "検索中..." : "検索"}
            </button>
          </div>

          <p className="user-search-description">
            空白を含まない正確なユーザーIDを入力してください。
          </p>
        </form>

        {error && (
          <div
            className="search-error"
            role="alert"
          >
            {error}
          </div>
        )}

        {user && (
          <article className="user-card">
            <div className="user-card-avatar">
              {user.username?.charAt(0).toUpperCase() || "U"}
            </div>

            <div className="user-card-information">
              <h2>{user.username}</h2>
              <p>@{user.id}</p>
            </div>

            {user.follow_status === "not_following" && (
              <button
                className="follow-button"
                onClick={handleFollow}
              >
                フォロー
              </button>
            )}

            {user.follow_status === "following" && (
              <button
                className="follow-button"
                onClick={handleUnfollow}
              >
                フォローを外す
              </button>
            )}

            {user.follow_status === "request_sent" && (
              <button
                className="follow-button"
                disabled
              >
                リクエスト済み
              </button>
            )}
          </article>
        )}
      </section>
    </div>
  );
}

export default Search;