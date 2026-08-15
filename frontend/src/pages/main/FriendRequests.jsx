import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../utils/api";
import { getErrorMessage } from "../../utils/error";
import "./account.css";

function FriendRequests() {
  const navigate = useNavigate();
  const [requests, setRequests] = useState([]);
  const load = async () => {
    try { setRequests((await api.get("/friend-requests")).data); }
    catch (error) { alert(getErrorMessage(error)); }
  };
  useEffect(() => {
    void (async () => {
      await load();
    })();
  }, []);

  const accept = async (id) => {
    try { await api.post(`/friend-requests/${id}/accept`); await load(); }
    catch (error) { alert(getErrorMessage(error)); }
  };
  const reject = async (id) => {
    if (!window.confirm("このリクエストを却下しますか？")) return;
    try { await api.delete(`/friend-requests/${id}`); await load(); }
    catch (error) { alert(getErrorMessage(error)); }
  };

  return <div className="account-page">
    <header className="sub-header"><button onClick={() => navigate("/account")}>戻る</button><h1>リクエスト</h1></header>
    {requests.length === 0 && <p className="empty-state">届いているリクエストはありません。</p>}
    {requests.map((request) => <div className="friend-row" key={request.id}>
      <div><strong>{request.sender.username}</strong><small>@{request.sender.user_id}</small></div>
      <div className="request-actions"><button onClick={() => accept(request.id)}>許可</button><button className="danger-outline" onClick={() => reject(request.id)}>却下</button></div>
    </div>)}
  </div>;
}

export default FriendRequests;
