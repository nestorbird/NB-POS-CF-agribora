

const APIs = {
  getGuestCustomer: '/api/method/nbpos.custom_api.v1.master.get_theme_settings',
  login: '/api/method/nbpos.custom_api.v1.nbpos_login.login', 
  getOpeningData : '/api/method/nbpos.custom_api.v1.pos_profile.get_opening_data',
  createOpeningShift:'/api/method/nbpos.custom_api.v1.pos_profile.create_opening_voucher',
  createClosingShift:'/api/method/nbpos.nbpos.doctype.pos_closing_shift.pos_closing_shift.submit_closing_shift',
  getCategoriesAndProducts: '/api/method/nbpos.custom_api.v1.item.get_items',
  getAllCustomers: '/api/method/nbpos.custom_api.v1.customer.get_all_customer',
  getSalesOrderList: '/api/method/nbpos.custom_api.v1.sales_order.get_sales_order_list',
  changePassword: '/api/method/nbpos.custom_api.v1.nbpos_login.change_password',
  getBasicInfo: '/api/method/nbpos.custom_api.v1.hub_manager.get_details_by_hubmanager',
  createCustomer:'/api/method/nbpos.custom_api.v1.customer.create_customer',
  editCustomer: '/api/method/nbpos.custom_api.v1.customer.edit_customer',
  createOrder:'/api/method/nbpos.custom_api.v1.sales_order.create_sales_order_kiosk',
  returnSalesOrder: '/api/method/nbpos.custom_api.v1.sales_order.return_sales_order',
  getCouponCodeList: '/api/method/nbpos.custom_api.v1.coupon_and_giftcard.coupon_code_details',
  validatePromoCode:'/api/method/nbpos.custom_api.v1.coupon_and_giftcard.validate_coupon_code',
  getCustomerDetails:'/api/method/nbpos.custom_api.v1.customer.get_customer',
  getlocation:'/api/method/nbpos.custom_api.v1.location.get_location',

  validateGiftCode:'api/method/nbpos.custom_api.v1.coupon_and_giftcard.validate_gift_card',
  sendMail:"api/method/nbpos.custom_api.v1.sales_invoice.resend_sales_invoice_email",
  getShiftDetails:"/api/method/nbpos.nbpos.doctype.pos_closing_shift.pos_closing_shift.get_shift_details",
  get_user: '/api/method/nbpos.custom_api.v1.nbpos_login.get_user', 
  
};

export default APIs;
