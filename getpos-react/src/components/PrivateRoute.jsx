import React from "react";
import { Navigate } from "react-router-dom";
import { useFrappeAuth } from "frappe-react-sdk"; // Import FrappeAuth to get currentUser
import { Spin } from "antd";
const PrivateRoute = ({
  element: Component,
  requiredKeys,
  redirectPath = "/login",
  ...rest
}) => {
  const { currentUser, isLoading } = useFrappeAuth(); // Get currentUser from Frappe auth

  // Function to check if all required keys are in localStorage
  const checkLocalStorageKeys = (keys) => {
    return keys.every((key) => localStorage.getItem(key)); // Ensure all required keys are in localStorage
  };

  const storedUser = JSON.parse(localStorage.getItem("user")); // Get the user from localStorage

  // Check if required localStorage data exists and if the currentUser matches the localStorage user
  const hasRequiredData =
    checkLocalStorageKeys(requiredKeys) &&
    currentUser &&
    storedUser &&
    currentUser === storedUser.email;

  // Redirect to login page if not authorized or if Frappe authentication is still loading
  if (isLoading) {
    return (
      <div className="loading-spin">
        <Spin tip="Loading..." />
      </div>
    ); // Show loading spinner or message while checking
  }

  return hasRequiredData ? (
    <Component {...rest} />
  ) : (
    <Navigate to={redirectPath} />
  );
};

export default PrivateRoute;
