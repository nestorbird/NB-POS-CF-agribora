import { createRoot } from 'react-dom/client'
import './index.css'
import { FrappeProvider } from "frappe-react-sdk";
import App from "./App";
import { StrictMode } from 'react';
import { CartProvider } from "./common/CartContext";

createRoot(document.getElementById('root')).render(
  <StrictMode>

    <FrappeProvider>
    <CartProvider>
      <App />
    </CartProvider>  
    </FrappeProvider> 
  </StrictMode>
  ,
)
