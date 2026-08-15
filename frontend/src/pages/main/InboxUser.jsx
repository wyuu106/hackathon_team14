import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../../utils/api";
import { getErrorMessage } from "../../utils/error";
import { formatJapanDateTime } from "../../utils/date";

import "./inboxUser.css";

function InboxUser() {
  const navigate = useNavigate();
  const { userId } = useParams();

  const [messageData, setMessageData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [viewers, setViewers] = useState(null);

  useEffect(() => {
    const fetchMessageData = async () => {
      try {
        const response = await api.get(`/messages/${userId}`);

        setMessageData(response.data);
      } catch (error) {
        console.error(error);
        alert(getErrorMessage(error));
      } finally {
        setIsLoading(false);
      }
    };

    fetchMessageData();
  }, [userId]);

  const showViewers = async (messageId) => {
    if (!messageData.is_own) return;
    try {
      const response = await api.get(`/messages/${messageId}/viewers`);
      setViewers(response.data);
    } catch (error) {
      alert(getErrorMessage(error));
    }
  };

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
          onClick={() => navigate("/view")}
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
              onClick={() => showViewers(message.message_id)}
            >
              <p className="message-content">{message.content}</p>

              <time className="message-time">
                {formatJapanDateTime(message.created_at)}
              </time>
            </div>
          ))
        )}
      </div>
      {viewers && <div className="viewer-backdrop" onClick={() => setViewers(null)}>
        <section className="viewer-sheet" onClick={(event) => event.stopPropagation()}>
          <h2>閲覧したユーザー</h2>
          {viewers.length === 0 ? <p>まだ閲覧されていません。</p> : viewers.map((viewer) => <p key={viewer.user_id}>{viewer.username} <small>@{viewer.user_id}</small></p>)}
          <button onClick={() => setViewers(null)}>閉じる</button>
        </section>
      </div>}
    </div>
  );
}

export default InboxUser;
