import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

import { API_URL } from "../../utils/api";
import { getErrorMessage } from "../../utils/error";

import "./inbox.css";

const dummyUsers = [
  {
    id: 1,
    username: "taro",
    read_status: false,
    latest_message: "今から向かいます",
  },
  {
    id: 2,
    username: "hanako",
    read_status: true,
    latest_message: "了解です",
  },
];

function Inbox() {
  const navigate = useNavigate();

  const [users, setUsers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const token = localStorage.getItem("token");
  
  useEffect(() => {
    const fetchFollowingUsers = async () => {
      try {
        const response = await axios.get(
          `${API_URL}/follows`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        setUsers(response.data);

      } catch (error) {
        console.error(error);
        alert(getErrorMessage(error));
      } finally {
        setIsLoading(false);
      }
    };

    fetchFollowingUsers();
  }, [token]);
  
  const dummyusers = dummyUsers; // 後で消す

  if (isLoading) {
    return <p>読み込み中...</p>;
  }

  return (
    <div className="inbox-page">
      <h1 className="inbox-title">
        受信メッセージ一覧
      </h1>

      <div className="inbox-list">
        {dummyusers.map((user) => ( // ここを後で変える
          <button
            key={user.id}
            type="button"
            className={`inbox-user-row ${
              !user.read_status ? "unread" : ""
            }`}
            onClick={() => navigate(`/inbox/${user.id}`)}
          >
            <div className="user-text">
              <h2>{user.username}</h2>

              <p className="latest-message">
                {user.latest_message ?? "受信メッセージはありません"}
              </p>
            </div>

            {!user.read_status &&
            <span className="unread-dot"></span>}
          </button>
        ))}
      </div>
    </div>
  );
}

export default Inbox;