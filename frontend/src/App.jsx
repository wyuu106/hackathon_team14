import { BrowserRouter, Routes, Route } from "react-router-dom";

import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";

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

      </Routes>
    </BrowserRouter>
  );
}

export default App;