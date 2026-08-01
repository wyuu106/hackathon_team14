import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import axios from "axios";

import { API_URL } from "../../utils/api";
import { getErrorMessage } from "../../utils/error";

import "./inboxUser.css";

function InboxUser() {
  const navigate = useNavigate();
  const { userId } = useParams();

  const [messageData, setMessageData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const token = localStorage.getItem("token");

  useEffect(() => {
    const fetchMessageData = async () => {
      try {
        const response = await axios.get(
          `${API_URL}/messages/${userId}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        setMessageData(response.data);
      } catch (error) {
        console.error(error);
        alert(getErrorMessage(error));
      } finally {
        setIsLoading(false);
      }
    };

    fetchMessageData();
  }, [userId, token]);

  if (isLoading) {
    return <p>読み込み中...</p>;
  }

  if (!messageData) {
    return <p>メッセージを取得できませんでした。</p>;
  }

  return (
    <div className="message-page">
      <header className="message-header">
        <button
          type="button"
          className="back-button"
          onClick={() => navigate("/inbox")}
        >
          戻る
        </button>

        <h1>{messageData.username}</h1>
      </header>

      <div className="message-list">
        {messageData.messages.length === 0 ? (
          <p className="message-empty">メッセージはありません。</p>
        ) : (
          messageData.messages.map((message) => ( 
            <div
              key={message.message_id}
              className="message-item"
            >
              <p className="message-content">{message.content}</p>

              <time className="message-time">
                {new Date(message.created_at).toLocaleString("ja-JP", {
                  month: "numeric",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </time>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default InboxUser;