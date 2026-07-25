import { BrowserRouter, Routes, Route } from "react-router-dom";

import Login from "./pages/auth/Login"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* ログイン */}
        <Route
          path="/" // URL
          element={<Login />} // page関数
        />

      </Routes>
    </BrowserRouter>
  );
}

export default App
