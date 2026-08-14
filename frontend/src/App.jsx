import { BrowserRouter, Navigate, Routes, Route } from "react-router-dom";

import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";

import MainLayout from "./layouts/MainLayout";
import Send from "./pages/main/Send";
import Inbox from "./pages/main/Inbox";
import InboxUser from "./pages/main/InboxUser";
import Search from "./pages/main/Search";
import Account from "./pages/main/Account";
import FriendRequests from "./pages/main/FriendRequests";
import Settings from "./pages/main/Settings";
import Templates from "./pages/main/Templates";
import RequireAuth from "./components/RequireAuth";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* ログイン */}
        <Route
          path="/login" // URL
          element={<Login />} // page関数
        />

        {/* ログイン */}
        <Route
          path="/register" 
          element={<Register />}
        />

        <Route element={<RequireAuth />}>
        <Route element={<MainLayout />}>
          <Route
            path="/chat"
            element={<Send />}
          />

          <Route
            path="/view"
            element={<Inbox />}
          />

          <Route
            path="/view/:userId"
            element={<InboxUser />}
          />

          <Route
            path="/search"
            element={<Search />}
          />
          <Route path="/account" element={<Account />} />
          <Route path="/account/requests" element={<FriendRequests />} />
          <Route path="/setting" element={<Settings />} />
          <Route path="/setting/templete" element={<Templates />} />
          <Route path="/send" element={<Navigate to="/chat" replace />} />
          <Route path="/inbox" element={<Navigate to="/view" replace />} />
        </Route>
        </Route>

        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />

      </Routes>
    </BrowserRouter>
  );
}

export default App;
