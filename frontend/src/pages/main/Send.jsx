import { useEffect, useState } from "react";
import { api } from "../../utils/api";
import { getErrorMessage } from "../../utils/error";

import "./send.css"

function Send() {
  const [templates, setTemplates] = useState([]);
  const [sendingId, setSendingId] = useState(null);
  const [freeMessage, setFreeMessage] = useState("");

  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const response = await api.get("/templates");

        setTemplates(response.data);

      } catch (error) {
        console.error(error);
        alert(getErrorMessage(error));
      }
    };

    fetchTemplates();
  }, []);

  const handleSendMessage = async (message) => {
    if (sendingId !== null) {
      return;
    }

    setSendingId(message.id);

    try {
      await api.post("/messages", { content: message.content });

      alert("送信完了！");

    } catch (error) {
      console.error(error);
      alert(getErrorMessage(error));

    } finally {
      setSendingId(null);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const content = freeMessage.trim();
    if (!content) return;
    await handleSendMessage({ id: "free", content });
    setFreeMessage("");
  };

  return (
    <div className="send-page">
      <header className="page-heading">
        <h1>クイックチャット</h1>
      </header>

      <div className="template-list">
        {templates.length === 0 && <p className="template-empty">設定画面から定型文を登録できます。</p>}
        {templates.map((template) => (
          <button
            key={template.id}
            type="button"
            className="template-card"
            onClick={() => handleSendMessage(template)}
            disabled={sendingId !== null}
          >
            {sendingId === template.id
              ? "送信中..."
              : template.content}
          </button>
        ))}
      </div>

      <form className="free-message-form" onSubmit={handleSubmit}>
        <div><input id="free-message" aria-label="メッセージ" value={freeMessage} onChange={(event) => setFreeMessage(event.target.value)} maxLength={1000} placeholder="メッセージを入力" />
        <button type="submit" disabled={!freeMessage.trim() || sendingId !== null}>送信</button></div>
      </form>
    </div>
  );
}

export default Send;
