import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";

import { API_URL } from "../../utils/api";
import { getErrorMessage } from "../../utils/error";
import "./account.css";

const config = () => ({ headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } });

function Account() {
  const [account, setAccount] = useState(null);
  const [friends, setFriends] = useState([]);
  const [hasPendingRequests, setHasPendingRequests] = useState(false);

  const load = async () => {
    try {
      const [accountResponse, friendsResponse, requestsResponse] = await Promise.all([
        axios.get(`${API_URL}/account`, config()),
        axios.get(`${API_URL}/friends`, config()),
        axios.get(`${API_URL}/friend-requests`, config()),
      ]);
      setAccount(accountResponse.data);
      setFriends(friendsResponse.data);
      setHasPendingRequests(requestsResponse.data.length > 0);
    } catch (error) {
      alert(getErrorMessage(error));
    }
  };

  useEffect(() => {
    void (async () => {
      await load();
    })();
  }, []);

  const removeFriend = async (friend) => {
    if (!window.confirm(`${friend.username}さんとの友だち関係を解除しますか？`)) return;
    try {
      await axios.delete(`${API_URL}/friends/${friend.user_id}`, config());
      await load();
    } catch (error) {
      alert(getErrorMessage(error));
    }
  };

  return (
    <div className="account-page">
      <header className="account-header">
        <div className="account-title-row"><div><h1>アカウント</h1>{account && <p>@{account.user_id} · {account.username}</p>}</div><Link className="settings-link" to="/setting" aria-label="設定">⚙</Link></div>
        <div className="account-menu">
          <Link className="account-request-link" to="/account/requests">
            <span>フォローリクエスト</span>
            <span className="account-request-status">
              {hasPendingRequests && <span className="request-unread-dot" aria-label="未確認のフォローリクエストあり" />}
              <b>›</b>
            </span>
          </Link>
        </div>
      </header>
      <h2 className="section-title">友だち {account?.friend_count ?? 0}人</h2>
      <div className="friend-list">
        {friends.length === 0 && <p className="empty-state">友だちはまだいません。</p>}
        {friends.map((friend) => (
          <div className="friend-row" key={friend.user_id}>
            <div><strong>{friend.username}</strong><small>@{friend.user_id}</small></div>
            <button className="danger-outline" onClick={() => removeFriend(friend)}>解除</button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Account;
