import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

import { API_URL } from "../../utils/api";
import { getErrorMessage } from "../../utils/error";
import "./templates.css";

const config = () => ({ headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } });

function Templates() {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState([]);
  const [content, setContent] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [draggingId, setDraggingId] = useState(null);
  const holdTimer = useRef(null);
  const latestTemplates = useRef([]);

  useEffect(() => {
    void (async () => {
      try {
        const response = await axios.get(`${API_URL}/templates`, config());
        setTemplates(response.data);
        latestTemplates.current = response.data;
      } catch (error) {
        alert(getErrorMessage(error));
      }
    })();
  }, []);

  const updateTemplates = (next) => {
    latestTemplates.current = next;
    setTemplates(next);
  };

  const register = async (event) => {
    event.preventDefault();
    const value = content.trim();
    if (!value) return;
    setIsSaving(true);
    try {
      const response = await axios.post(`${API_URL}/templates`, { content: value }, config());
      updateTemplates([...latestTemplates.current, response.data]);
      setContent("");
    } catch (error) {
      alert(getErrorMessage(error));
    } finally {
      setIsSaving(false);
    }
  };

  const remove = async (template) => {
    if (!window.confirm("このテンプレートを削除しますか？")) return;
    try {
      await axios.delete(`${API_URL}/templates/${template.id}`, config());
      updateTemplates(latestTemplates.current.filter((item) => item.id !== template.id));
    } catch (error) {
      alert(getErrorMessage(error));
    }
  };

  const persistOrder = async () => {
    try {
      await axios.put(`${API_URL}/templates/order`, {
        template_ids: latestTemplates.current.map((template) => template.id),
      }, config());
    } catch (error) {
      alert(getErrorMessage(error));
    }
  };

  const startHold = (event, id) => {
    event.currentTarget.setPointerCapture(event.pointerId);
    holdTimer.current = window.setTimeout(() => {
      setDraggingId(id);
      if (navigator.vibrate) navigator.vibrate(30);
    }, 350);
  };

  const moveHeldItem = (event, id) => {
    if (draggingId !== id) return;
    const target = document.elementFromPoint(event.clientX, event.clientY)?.closest("[data-template-id]");
    const targetId = Number(target?.dataset.templateId);
    if (!targetId || targetId === id) return;
    const current = latestTemplates.current;
    const from = current.findIndex((item) => item.id === id);
    const to = current.findIndex((item) => item.id === targetId);
    if (from < 0 || to < 0) return;
    const next = [...current];
    const [moved] = next.splice(from, 1);
    next.splice(to, 0, moved);
    updateTemplates(next);
  };

  const finishHold = async (id) => {
    window.clearTimeout(holdTimer.current);
    holdTimer.current = null;
    if (draggingId === id) {
      setDraggingId(null);
      await persistOrder();
    }
  };

  return <div className="templates-page">
    <header className="sub-header"><button onClick={() => navigate("/setting")}>戻る</button><h1>テンプレート</h1></header>
    <form className="template-create-row" onSubmit={register}>
      <input value={content} onChange={(event) => setContent(event.target.value)} maxLength={100} placeholder="テンプレートの内容を入力" aria-label="テンプレートの内容" />
      <button disabled={!content.trim() || isSaving}>{isSaving ? "登録中…" : "登録"}</button>
    </form>
    <p className="template-help">≡ を長押しして上下に動かすと、送信画面の順番も変わります。</p>
    <div className="template-manage-list">
      {templates.length === 0 && <p className="empty-state">登録済みのテンプレートはありません。</p>}
      {templates.map((template) => <article className={`template-manage-row ${draggingId === template.id ? "dragging" : ""}`} key={template.id} data-template-id={template.id}>
        <p>{template.content}</p>
        <button className="template-delete" onClick={() => remove(template)}>削除</button>
        <button
          type="button"
          className="drag-handle"
          aria-label={`${template.content}の順番を変更`}
          onPointerDown={(event) => startHold(event, template.id)}
          onPointerMove={(event) => moveHeldItem(event, template.id)}
          onPointerUp={() => finishHold(template.id)}
          onPointerCancel={() => finishHold(template.id)}
        >≡</button>
      </article>)}
    </div>
  </div>;
}

export default Templates;
