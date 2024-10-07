// App.js
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom'; 
import LoginPage from './pages/LoginPage';
import MainScreen from './components/MainScreen';
import HomePage from './pages/HomePage';
import OrderPage from './pages/OrderPage';
import CustomerPage from './pages/CustomerPage';
import ProfilePage from './pages/ProfilePage';
import OpenShiftScreen from './components/OpenShiftScreen';
import CloseShiftScreen from './components/CloseShiftScreen';
import Location from "./components/getLocation"
import { OpenShiftProvider } from './components/OpenShiftContext';
import Barcode from './components/barcode'
import { ThemeSettingsProvider } from './components/ThemeSettingContext';
import PrivateRoute from './components/PrivateRoute';

const AppRoutes = () => {
  return (
    

    <ThemeSettingsProvider>
    <OpenShiftProvider>

      <Router basename="/getpos-react">
      {/* <Router > */}
          
        <Routes >
     
             <Route path="/" element={<LoginPage />} />
            <Route path="/login" element={<LoginPage />} />

            {/* Private Routes with authentication and data checks */}
            <Route
              path="/Barcode"
              element={<PrivateRoute element={Barcode} requiredKeys={['user']} />}
            />
            <Route
              path="/location"
              element={<PrivateRoute element={Location} requiredKeys={['user']} />}
            />
            <Route
              path="/category"
              element={<PrivateRoute element={MainScreen} requiredKeys={['openShiftData', 'paymentBalances','user','costCenter']} />}
            />
            <Route
              path="/openshift"
              element={<PrivateRoute element={OpenShiftScreen} requiredKeys={['costCenter','user']} />}
            />
            <Route
              path="/closeshift"
              element={<PrivateRoute element={CloseShiftScreen} requiredKeys={['user','openShiftData', 'paymentBalances','costCenter']} />}
            />
            <Route
              path="/main"
              element={<PrivateRoute element={HomePage} requiredKeys={['user','openShiftData', 'paymentBalances','costCenter']} />}
            />
            <Route
              path="/order"
              element={<PrivateRoute element={OrderPage} requiredKeys={['user','openShiftData', 'paymentBalances','costCenter']} />}
            />
            <Route
              path="/customer"
              element={<PrivateRoute element={CustomerPage} requiredKeys={['user','openShiftData', 'paymentBalances','costCenter']} />}
            />
            <Route
              path="/profile"
              element={<PrivateRoute element={ProfilePage} requiredKeys={['user','openShiftData', 'paymentBalances','costCenter']} />}
            />
        </Routes>
      </Router>
    </OpenShiftProvider>
    </ThemeSettingsProvider>
 
  );
};

export default AppRoutes;
