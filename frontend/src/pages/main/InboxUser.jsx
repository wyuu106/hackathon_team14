import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import axios from "axios";

import { API_URL } from "../../utils/api";
import { getErrorMessage } from "../../utils/error";

import "./inboxUser.css";

const dummyMessageData = {
    user_id: 1,
    username: "わたべ",
    messages: [
      {
        message_id: 1,
        content: "帰宅",
        created_at: "2026-07-31:19:00"
      },
      {
        message_id: 2,
        content: "出発",
        created_at: "2026-08-01:12:00"
      }
    ]
  };

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
          `${API_URL}/message/${userId}`,
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

  /*
  if (!messageData) {
    return <p>メッセージを取得できませんでした。</p>;
  }
    */

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

        <h1>{dummyMessageData.username}</h1> {/* 後で変える */}
      </header>

      <div className="message-list">
        {dummyMessageData.messages.length === 0 ? ( // 後で変える
          <p className="message-empty">メッセージはありません。</p>
        ) : (
          dummyMessageData.messages.map((message) => ( // 後で変える
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