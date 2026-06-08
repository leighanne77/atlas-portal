import { Navigate, Route, Routes } from "react-router-dom";
import AuthSuccess from "./pages/AuthSuccess";
import Home from "./pages/Home";
import Intro from "./pages/Intro";
import Login from "./pages/Login";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/auth/success" element={<AuthSuccess />} />
      <Route path="/intro" element={<Intro />} />
      <Route path="/" element={<Home />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
