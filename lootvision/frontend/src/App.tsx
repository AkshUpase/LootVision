import { HashRouter, Route, Routes } from "react-router-dom";
import { BottomNav } from "./components/BottomNav";
import Scanner from "./pages/Scanner";
import History from "./pages/History";
import Settings from "./pages/Settings";

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<Scanner />} />
        <Route path="/history" element={<History />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
      <BottomNav />
    </HashRouter>
  );
}
