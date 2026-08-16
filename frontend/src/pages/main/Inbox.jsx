import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../utils/api";
import { getErrorMessage } from "../../utils/error";
import { formatJapanDateTime } from "../../utils/date";
import { useRealtime } from "../../contexts/realtime-context";

import "./inbox.css";

function Inbox() {
  const navigate = useNavigate();
  const { lastEvent } = useRealtime();

  const [users, setUsers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchFollowingUsers = useCallback(async () => {
    try {
      const response = await api.get("/inbox");

      setUsers(response.data);

    } catch (error) {
      console.error(error);
      alert(getErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void fetchFollowingUsers(), 0);
    return () => window.clearTimeout(timer);
  }, [fetchFollowingUsers]);

  useEffect(() => {
    if (lastEvent?.type !== "message.created") return undefined;
    const timer = window.setTimeout(() => void fetchFollowingUsers(), 0);
    return () => window.clearTimeout(timer);
  }, [lastEvent, fetchFollowingUsers]);

  if (isLoading) {
    return <p>読み込み中...</p>;
  }

  return (
    <div className="inbox-page">
      <h1 className="inbox-title">
        受信メッセージ一覧
      </h1>

      <div className="inbox-list">
        {users.map((user) => (
          <button
            key={user.user_id}
            type="button"
            className={`inbox-user-row ${
              !user.read_status ? "unread" : ""
            }`}
            onClick={() => navigate(`/view/${user.user_id}`)}
          >
            <div className="user-text">
              <h2>{user.username}</h2>

              <div className="latest-message-row">
                <p className="latest-message">
                  {user.latest_message ?? "受信メッセージはありません"}
                </p>
                {user.latest_message_at && (
                  <time className="latest-message-time" dateTime={user.latest_message_at}>
                    {formatJapanDateTime(user.latest_message_at)}
                  </time>
                )}
              </div>
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
