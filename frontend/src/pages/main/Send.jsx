import { useEffect, useState } from "react";
import axios from "axios";

import { API_URL } from "../../utils/api";
import { getErrorMessage } from "../../utils/error";

import "./send.css"

function Send() {
  const [templates, setTemplates] = useState([]);
  const [sendingId, setSendingId] = useState(null);

  const token = localStorage.getItem("token");

  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const response = await axios.get(
          `${API_URL}/templates`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        setTemplates(response.data);

      } catch (error) {
        console.error(error);
        alert(getErrorMessage(error));
      }
    };

    fetchTemplates();
  }, [token]);

  const handleSendMessage = async (message) => {
    if (sendingId !== null) {
      return;
    }

    setSendingId(message.id);

    try {
      await axios.post(
        `${API_URL}/messages`,
        {
          content: message.content,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      alert("送信完了！");

    } catch (error) {
      console.error(error);
      alert(getErrorMessage(error));

    } finally {
      setSendingId(null);
    }
  };

  return (
    <div>
      <h2>クイックチャット</h2>

      <div className="template-list">
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
    </div>
  );
}

export default Send;