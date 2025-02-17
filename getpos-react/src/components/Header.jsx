import React, { useEffect, useState } from "react";
import "./style.css";
import Logo from "../assets/images/logo.png";
import SearchIcon from "../assets/images/Search-icon.png";
import { useLocation } from "react-router-dom";

const Header = ({ onSearch }) => {
  const [user, setUser] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    const userData = localStorage.getItem("user");

    if (userData) {
      setUser(JSON.parse(userData));
    } else {
      console.log("No user data found in localStorage");
    }
  }, []);

  const costCenter = localStorage.getItem("costCenter");
  const Openshift = localStorage.getItem("openingShiftResponse");

  const handleSearch = (e) => {
    setSearchQuery(e.target.value);
    onSearch(e.target.value);
  };

  const toggleMenu = () => {
    setMenuOpen(!menuOpen);
  };

  return (
    <header className="header">
      <div className="header-logo">
        {user && costCenter && Openshift ? (
          <>
            <a href="/getpos-react">
              <img src={Logo} alt="Logo" />
            </a>
            <button
              onClick={() => {
                const origin = window.location.origin;
                window.location.href = `${origin}/app/home`;
              }}
              class="admin-panel-btn"
            >
              Go To Admin Panel
            </button>
          </>
        ) : (
          <>
            <img src={Logo} alt="Logo" />
            <button
              onClick={() => {
                const origin = window.location.origin;
                window.location.href = `${origin}/app/home`;
              }}
              class="admin-panel-btn"
            >
              Go To Admin Panel
            </button>
          </>
        )}
      </div>
      <div className="header-right">
        {user && location.pathname === "/main" ? (
          <>
            <div className="search-container">
              <input
                type="text"
                placeholder="Search"
                value={searchQuery}
                onChange={handleSearch}
              />
              <img id="searchIcon" src={SearchIcon} alt="" />
            </div>
          </>
        ) : (
          []
        )}
        <div
          className={`burger-menu ${menuOpen ? "open" : ""}`}
          onClick={toggleMenu}
        >
          <div className="burger-bar"></div>
          <div className="burger-bar"></div>
          <div className="burger-bar"></div>
        </div>
        <div className={`mobile-menu ${menuOpen ? "open" : ""}`}>
          {user ? (
            <>
              <a href="/profile">Profile</a>
              <a href="/logout">Logout</a>
            </>
          ) : (
            <a href="/">Login</a>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
