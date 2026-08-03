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
        `${API_URL}/follow/${user.user_id}`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      await fetchUser(user.user_id); // ユーザー情報再取得

    } catch (error) {
      console.error(error);
      alert(getErrorMessage(error));
    }
  };

  // フォロー解除処理
  const handleUnfollow = async () => {
    if (!window.confirm("フォロー解除しますか？")) {
      return;
    }
    try {
      await axios.delete(
        `${API_URL}/follow/${user.user_id}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      await fetchUser(user.user_id); // ユーザー情報再取得
      
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

            <input
              id="userId"
              className="search-input"
              type="text"
              value={userId}
              onChange={handleChange}
              placeholder="IDを入力"
              autoComplete="off"
              maxLength={30}
            />

            <button
              className="search-button"
              type="submit"
              disabled={isLoading}
            >
              {isLoading ? "検索中..." : "検索"}
            </button>
          </div>

          <p className="search-description">
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

            <div className="user-card-information">
              <h2>{user.id}</h2>
              <p>{user.username}</p>
            </div>

            {user.follow_status === "not_following" && (
              <button
                className="follow-button follow"
                onClick={handleFollow}
              >
                フォロー
              </button>
            )}

            {user.follow_status === "following" && (
              <button
                className="follow-button unfollow"
                onClick={handleUnfollow}
              >
                フォローを外す
              </button>
            )}

            {/* リクエスト機能はいったん保留 */}
            {user.follow_status === "requested" && (
              <button
                className="follow-button requested"
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