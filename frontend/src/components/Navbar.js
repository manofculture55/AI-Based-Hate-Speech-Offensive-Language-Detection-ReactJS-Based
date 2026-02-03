import { Link, useLocation, useNavigate } from "react-router-dom";
import { useContext } from "react";
import { ThemeContext } from "./ThemeContext";
import "../styles/navbar.css";
import {  useEffect, useState } from "react";


export default function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useContext(ThemeContext);

  const isActive = (path) =>
    location.pathname === path ||
    location.pathname.startsWith(path + "/");

  const isAdminPage = location.pathname.startsWith("/admin");
  const [isAdminLoggedIn, setIsAdminLoggedIn] = useState(
    sessionStorage.getItem("admin_auth") === "true"
  );

  useEffect(() => {
    const syncAuth = () => {
      setIsAdminLoggedIn(sessionStorage.getItem("admin_auth") === "true");
    };

    syncAuth(); // run once on mount / route change

    window.addEventListener("admin-auth-change", syncAuth);

    return () => {
      window.removeEventListener("admin-auth-change", syncAuth);
    };
  }, [location.pathname]);



  function adminLogout() {
    sessionStorage.removeItem("admin_auth");
    window.dispatchEvent(new Event("admin-auth-change"));
    setIsAdminLoggedIn(false);
    navigate("/");
  }



  return (
    <nav className="navbar">
      {/* LEFT: Logo */}
      <div className="logo">
        <span
          className="logo-text"
          onClick={() => navigate("/")}
        >
          HateSpeech
        </span>

      </div>

      {/* RIGHT: Navigation + Controls */}
      <div className="nav-right">
        <Link to="/" className={`nav-btn ${isActive("/") ? "active" : ""}`}>
          Home
        </Link>

        <Link
          to="/history"
          className={`nav-btn ${isActive("/history") ? "active" : ""}`}
        >
          History
        </Link>

        <Link
          to="/analytics"
          className={`nav-btn ${isActive("/analytics") ? "active" : ""}`}
        >
          Analytics
        </Link>

        {/* ADMIN LOGOUT — ONLY ON ADMIN PAGE */}
        {isAdminPage && isAdminLoggedIn && (
          <button
            className="nav-admin-logout"
            onClick={adminLogout}
          >
            Logout
          </button>
        )}

        {/* THEME TOGGLE */}
        <label className="theme-switch">
          <input
            type="checkbox"
            className="theme-switch-input"
            checked={theme === "dark"}
            onChange={toggleTheme}
          />
          <span className="theme-switch-slider"></span>
        </label>
      </div>
    </nav>
  );
}
