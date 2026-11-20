import { NavLink } from "react-router-dom";

const TABS = [
  { to: "/", label: "Scanner", icon: "◎" },
  { to: "/history", label: "History", icon: "▤" },
  { to: "/settings", label: "Settings", icon: "⚙" },
];

export function BottomNav() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-panel/95 border-t border-line backdrop-blur z-20">
      <div className="flex justify-around py-2 pb-[calc(env(safe-area-inset-bottom)+0.5rem)]">
        {TABS.map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            end={tab.to === "/"}
            className={({ isActive }) =>
              `flex flex-col items-center gap-0.5 px-4 py-1 text-xs mono ${
                isActive ? "text-scan" : "text-white/40"
              }`
            }
          >
            <span className="text-lg leading-none">{tab.icon}</span>
            {tab.label}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
