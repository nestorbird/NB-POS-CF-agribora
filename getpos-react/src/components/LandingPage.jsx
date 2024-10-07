import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "./Layout";
import { getUser } from "../modules/LandingPage";
import { Spin } from "antd";
import { useFrappeAuth } from "frappe-react-sdk";

const LandingPage = () => {
  const { currentUser, isLoading, login, logout } = useFrappeAuth();
  const navigate = useNavigate();
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const storedUser = JSON.parse(localStorage.getItem("user") || null);
    const storedCostCenter = localStorage.getItem("costCenter");
    const storedPaymentBalances = JSON.parse(localStorage.getItem("paymentBalances") || "{}");
    const storedOpeningShiftResponse = localStorage.getItem("openingShiftResponse");

    // Check if user is logged out from Frappe (currentUser is null)
    if (!isLoading && !currentUser) {
      // Clear localStorage and redirect to login
      localStorage.clear();
      navigate("/");
      return;
    }

    // Early return if user is an Administrator
    if (currentUser === "Administrator" && !isLoading) {
      localStorage.clear();
      return;
    }

    // Check if all required data is present in localStorage
    const hasValidLocalStorageData =
      storedUser &&
      storedCostCenter &&
      storedOpeningShiftResponse &&
      storedPaymentBalances?.Cash !== undefined &&
      currentUser === storedUser?.email;

    if (hasValidLocalStorageData && !isLoading) {
      navigate("/main");
      return;
    }

    // Fetch user data if not present
    if (currentUser && currentUser !== "Administrator" && !isLoading) {
      handleGetUser();
    }

    // Clear localStorage if conditions are not met
    if (!isLoading && (!currentUser || currentUser !== storedUser?.email)) {
      localStorage.clear();
    }
  }, [currentUser, isLoading, navigate]);

  const handleGetUser = async () => {
    setError(null);
    try {
      const data = await getUser();

      if (data.message?.success_key === 1) {
        const userInfo = {
          name: data.message.username,
          email: data.message.email,
          role: data.message.role,
          profileImage: data.message.profile_image,
        };
        localStorage.setItem("user", JSON.stringify(userInfo));

        navigate("/location", { state: { loginResponse: data } });
      } else {
        setError("Failed to retrieve user data.");
      }
    } catch (error) {
      console.error("Error fetching user data:", error);
      setError("An error occurred while retrieving user data.");
    }
  };

  const handleLoginClick = () => {
    window.location.href = window.location.origin;
  };

  return (
    <div className="login-page">
      <Layout showFooter={false} showDropdown={false}>
        <div className="login-screen">
          {/* Display for Administrators */}
          {currentUser === "Administrator" ? (
            <div className="login-prompt">
              <h2 style={{ textAlign: "center", color: "#FF5733" }}>
                Access Denied for Administrators
              </h2>
              <p style={{ textAlign: "center", fontSize: "16px", color: "#555" }}>
                Administrators cannot log in using the standard method. Please use your email to access your account.
              </p>
              <button className="login-button" onClick={handleLoginClick}>
                Login
              </button>
            </div>
          ) : isLoading ? (
            <div className="loading-spin">
              <Spin tip="Loading..." />
            </div>
          ) : error ? (
            <div className="error-message">
              <h2>{error}</h2>
            </div>
          ) : (
            !currentUser && !localStorage.getItem("user") && (
              <div className="login-prompt">
                <h2>Please log in to continue</h2>
                <button className="login-button" onClick={handleLoginClick}>
                  Login
                </button>
              </div>
            )
          )}
        </div>
      </Layout>
    </div>
  );
};

export default LandingPage;
