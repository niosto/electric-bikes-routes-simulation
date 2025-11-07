import React from "react";

export default function TopNav({ brand, tabs = [], activeKey }) {
  return (
    <header className="topnav">
      {brand ? <div className="brand">{brand}</div> : <div style={{width:8}} />}
      <nav className="tabs">
        {tabs.map(t => (
          <div key={t.key} className={"tab " + (t.key === activeKey ? "active" : "")}>
            {t.label}
          </div>
        ))}
      </nav>
    </header>
  );
}