import { BrowserRouter, Routes, Route } from "react-router-dom";

import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";

import MainLayout from "./layouts/MainLayout";
import Send from "./pages/main/Send";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* ログイン */}
        <Route
          path="/" // URL
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
        </Route>

      </Routes>
    </BrowserRouter>
  );
}

export default App;