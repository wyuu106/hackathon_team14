import { BrowserRouter, Routes, Route } from "react-router-dom";

import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";

import MainLayout from "./layouts/MainLayout";
import Send from "./pages/main/Send";
import Inbox from "./pages/main/Inbox";
import InboxUser from "./pages/main/InboxUser";
import Search from "./pages/main/Search";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* ログイン */}
        <Route
          path="login" // URL
          element={<Login />} // page関数
        />

        {/* ログイン */}
        <Route
          path="/register" 
          element={<Register />}
        />

        {/* メイン画面 */}
        <Route element={<MainLayout />}>
          <Route
            path="/send"
            element={<Send />}
          />

          <Route
            path="/inbox"
            element={<Inbox />}
          />

          <Route
            path="/inbox/:userId"
            element={<InboxUser />}
          />

          <Route
            path="/search"
            element={<Search />}
          />
        </Route>

      </Routes>
    </BrowserRouter>
  );
}

export default App;