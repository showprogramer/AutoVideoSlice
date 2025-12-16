/**
 * 布局组件
 * 提供页面整体布局结构
 */

import "./Layout.css";

export function Layout({ children }) {
  return (
    <div className="layout">
      <header className="header">
        <div className="container">
          <div className="header-content">
            <a href="/" className="logo">
              <span className="logo-icon">✂️</span>
              <span className="logo-text">AutoVideoSlice</span>
            </a>
            <nav className="nav">
              <a href="/" className="nav-link active">
                首页
              </a>
              <a href="/history" className="nav-link">
                历史
              </a>
              <a href="/settings" className="nav-link">
                设置
              </a>
            </nav>
          </div>
        </div>
      </header>

      <main className="main">
        <div className="container">{children}</div>
      </main>

      <footer className="footer">
        <div className="container">
          <p className="footer-text">
            AutoVideoSlice · 本地优先的智能视频剪辑助手
          </p>
        </div>
      </footer>
    </div>
  );
}

export default Layout;
