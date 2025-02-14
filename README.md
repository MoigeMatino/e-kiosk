# ekiosk

ekiosk is a Django REST Framework (DRF) application for managing an online kiosk. It features authentication via OpenID Connect for customers and Django’s built-in admin for staff users, customer order management, and automated email and SMS notifications. Background tasks are handled efficiently using Celery with Redis as the message broker. The project is fully containerized with Docker and includes a CI/CD pipeline powered by GitHub Actions, with support for deployment to Kubernetes clusters for scalability and reliability.

---

## Features

- **Customer and Order Management**: Manage customers, product categories, products and orders.
- **Authentication**: Secure login and user management using OpenID Connect for customers, while staff users (admins) manage the system through Django’s built-in admin interface.
- **Notifications**:  Email and SMS notifications powered by Google SMTP and Africa's Talking, with logs stored in the Notification model for verification.
- **Permissions**:
  - Customers: Create and view their own orders.
  - Admins: View all orders, update order status (PATCH), but cannot delete or modify other details, create and modify products and categories.
- **Background Tasks**: Asynchronous email and SMS notifications using Celery and Redis.
- **Testing**: Comprehensive tests for serializers, models, views, serializers and tasks using `pytest` with function-based tests and mocking.
- **CI/CD**: GitHub Actions pipeline for building, testing, and deploying the application.
- **Deployment**: Dockerized with Kubernetes support for production deployment.

---

## Architecture Overview

- **Backend**: Django REST Framework
- **Database**: PostgreSQL (via Docker Compose)
- **Task Queue**: Celery with Redis as the message broker(via Docker Compose)
- **Notifications**: Email and SMS with pluggable services
- **Containerization**: Docker for both development and production environments
- **CI/CD**: GitHub Actions pipeline
- **Deployment**: Kubernetes (Minikube for local testing, production-ready configurations available)

---

## Setup Instructions

### Prerequisites

Ensure you have the following installed:

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Git](https://git-scm.com/)
- Python 3.9 or higher (optional, for local development without Docker)

### Environment Variables

Create a `.env` file in the root directory and add the following variables:

```
DEBUG=
SECRET_KEY=
DJANGO_ALLOWED_HOSTS=
DB_ENGINE=
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=
POSTGRES_PORT=
OIDC_RP_CLIENT_ID=
OIDC_RP_CLIENT_SECRET=
OIDC_RP_SIGN_ALGO=RS256
ATSK_API_KEY=
DEFAULT_FROM_EMAIL=
EMAIL_HOST_PASSWORD=
EMAIL_HOST_USER=
```

### Running Locally

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd ekiosk
   ```

2. Build and run the Docker containers:
   ```bash
   docker-compose up --build
   ```

3. Apply database migrations:
   ```bash
   docker-compose exec api python manage.py migrate
   ```

4. Access the application at `http://localhost:8000/api/v1`.

### Running Tests

Run the tests with:
```bash
docker-compose exec api pytest
```

# 📖  API Notes - User Manual


---
### 🚀 Model Design

This section describes the main models in the application and their relationships.

#### User Model

*   Stores customer information, including OpenID Connect (OIDC) identifiers.
*   Key Fields: `role`, `email`, `phone_number`, `oidc_identifier(openid_sub)`
*   **Note:** Customers must have a phone number to complete their profile.

#### Category Model

*   Represents product categories, supporting up to three levels of nesting.
*   Key Fields: `name`, `parent_category`
*   **Average price calculations** are limited to three levels to maintain performance and relevance.

#### Product Model

*   Stores details about each product.
*   Key Fields: `name`, `price`, `category`, `stock``,discount_price`

#### Discount price field is meant to account for price changes in case of discounts

#### Order Model

*   Tracks customer orders.
*   Key Fields: `customer`, `status`, `created_at`, `total_price`
*   **Status Workflow:**
*   `PENDING` → Stock is not deducted yet, awaiting admin approval.
*   `COMPLETED` → Stock is deducted after admin approval.
*   `CANCELED` → Order is rejected (e.g., due to insufficient stock), and the customer is notified.
*   **Stock is deducted only upon admin order approval.**
*   #### OrderItem Model
    
*   Represents individual items within an order, capturing details like product, quantity, and price at the time of purchase.
*   **Key Fields:** `order`, `product`, `quantity`, `price_at_time_of_order`
*   **Business Logic:**
    *   Ensures `quantity > 0` when saving the record.
    *   The `price_at_time_of_order` is captured to prevent future price changes from affecting past orders.

#### Notification Model

*   Logs all customer and admin notifications (email/SMS).
*   Key Fields: , `message`, `created_at`

--- 

## 📦 Order Processing

Order processing in this application ensures a streamlined workflow from placement to completion while maintaining transparency and efficient communication with both admins and customers.

#### 1\. Customer Places an Order → Status: `PENDING`

*   The system **checks stock availability** for all ordered items.
*   The order status is initially set to `PENDING`.
*   **Stock is NOT deducted yet**—it remains reserved, awaiting admin approval.
*   **Admin is notified** via email about the new order.
*   **Customer is notified** of the order placement via sms.

#### 2\. Admin Reviews & Approves the Order → Status: `COMPLETED`

*   Once the admin approves the order, **stock is deducted** from the inventory.
*   The order status is updated to `COMPLETED`.
*   **Customer is notified** via SMS about the order approval and completion.

#### 3\. (Optional) Order Cancellation → Status: `CANCELED`

*   If the admin rejects the order (e.g., due to insufficient stock or invalid details), the order is **marked as `CANCELED`**.
*   **Customer is notified** of the cancellation via sms.

---

## 🚀 Notifications

### Overview

The notification system is designed to keep stakeholders informed at key points during the order lifecycle. Notifications are sent through **Email** and **SMS** channels to ensure timely communication.

*   **Email Provider**: Google SMTP
*   **SMS Provider**: Africa's Talking

Notifications are logged in the `Notification` model for tracking purposes.

* * *

### Notification Triggers

Below are the scenarios that trigger notifications, the notification type, and the intended recipients:

| Trigger | Notification Type | Recipient |
| --- | --- | --- |
| Order placed | Email | Admin |
| Order placed | SMS | Customer |
| Order approved | SMS | Customer |
| Order cancelled | SMS | Customer |

* * *

### Notification Examples

#### 1\. Order Placed Notification

*   **To Admin (Email)**
    
    *   "A new order (#123) placed for [john@example.com](mailto:john@example.com) requires your attention."
*   **To Customer (SMS)**
    
    *   "Hello +254711223344 your order #123 has been placed successfully."

#### 2\. Order Approved Notification

*   **To Customer (SMS)**
    *   "Good news, +254711223344! Your order #123 has been approved."

#### 3\. Order Cancelled Notification

*   **To Customer (SMS)**
    *   "Sorry, +254711223344. Your order #123 has been cancelled."

* * *

### Note

All notifications are tracked and logged in the `Notification` model, including the message content and timestamp for auditing purposes.




----
## 🚀 API Endpoints

### Overview

This application provides a RESTful API for managing orders, products, and categories. Below is a summary of the available endpoints:

* * *
### 🔹 Authentication

**Root API Endpoint:** `api/v1`

#### Customer Authentication Endpoints

These endpoints manage authentication for customers using **OIDC (OpenID Connect)**.

*   **Login with OIDC:** `POST /api/v1/oidc/authenticate/`  
    _Initiates the OIDC authentication process and redirects to the identity provider._
*   **OIDC Callback:** `GET /api/v1/oidc/callback/`  
    _Handles the callback from the identity provider and processes the authentication response._
*   **Check Profile Completion:** `GET /api/v1/update-profile/`  
    _Redirects the customer to update their profile if any required fields (e.g., phone number) are missing._

#### Admin Authentication Flow

*   Admins use the **Django Admin Interface** for authentication and user management.  
    Access the admin panel at: `/admin/`

### 🔹 Orders

*   **List Orders**: `GET /api/orders/`
*   **Create Order**: `POST /api/orders/`
*   **Retrieve Order**: `GET /api/orders/{id}/`
*   **Update Order Status** (Admin only): `PATCH /api/orders/{id}/`
*   **Delete Order**: Not allowed.

* * *

### 🔹 Products

*   **List Products**: `GET /api/products/`
*   **Create Product**: `POST /api/products/` (Admin only)
*   **Retrieve Product**: `GET /api/products/{id}/`
*   **Update Product**: `PUT /api/products/{id}/` (Admin only)
*   **Bulk Upload Products**: `POST /api/products/bulk-upload/` (Admin only)  
    _See detailed explanation below._

#### 🛍️ Bulk Upload Products

*   **URL:** `/api/products/bulk-upload/`
*   **Method:** `POST`
*   **Description:** Allows admins to upload multiple products at once using a CSV file.

##### Example Request:

    POST /api/products/bulk-upload/
    Content-Type: multipart/form-data
    File: products.csv
    

##### Example CSV Format:

    name,stock,price,category
    Product1,10,100,Category1
    Product2,20,200,Category2
    

##### Example Response:

    {
      "products_created": 2,
      "errors": []
    }
    

##### Notes:

*   Only CSV files are supported for now.
*   Each row in the CSV represents a product with fields: `name`, `stock`, `price`, `category`.
*   If there are errors, the response will indicate which rows failed.

* * *

### 🔹 Categories
*   **List Categories**: `GET /api/categories/`
*   **Calculate Average Price (up to Three Levels)**: `GET /api/categories/<id>/calculate_average_price/`  
    _See detailed explanation below._

#### 📊 Calculate Average Price

*   **URL:** `/api/categories/<id>/calculate_average_price/`
*   **Method:** `GET`
*   **Description:** Calculates and returns the average price of products for the selected category, including products in **immediate subcategories** and **nested subcategories up to three levels deep**.

##### Example Response:
```
    (
        {

         "category": Electronics,
        
          "average_price": 500,
    
          "products_count": 3,
    
          "subcategory_count": 2,  

         },

         status=status.HTTP_200_OK,

    )
```
    
#### Business Logic & Category Structure

*   The calculation includes **main category**, **subcategories**, and their **immediate children** (i.e., up to **three levels deep**).
*   **Why only three levels?** Aiming for a balance between performance and relevance:
    *   Two levels deep captures enough data for accurate calculations without including deeply nested categories that might distort the results.
    *   Ensuring that our queries remain **performant and scalable** while providing **accurate insights** for related categories.
*   **Going beyond three levels** introduces data from potentially unrelated or niche subcategories with significantly different pricing, which can skew the average.

##### Example:
Electronics  
└── Laptops (level 1)  
    ├── Gaming Laptops (level 2)  
    │       └── High-End Gaming Laptops (level 3) ← Included in the calculation  
    └── Ultrabooks (level 2)  
            └── Lightweight Ultrabooks (level 3) ← Included in the calculation  

**Categories beyond level 3** (e.g., `Premium High-End Gaming Laptops`) will not be included in the average calculation.

##### Notes:

*   This endpoint calculates the **average price per subcategory**.
*   Useful for tracking pricing trends and insights at a more specific level.

### 🛠️ Future Enhancements

*   Support for JSON file uploads in bulk product upload.
*   Integrate background tasks for periodic category-level price analysis.

---

## 🚀 Permissions and Authentication

This application enforces strict role-based access control using custom permissions and authentication via **OpenID Connect (OIDC)**, with Google as the provider. The following section explains how authentication is handled and how permissions are enforced for different endpoints.

---

## **Authentication Overview**

The application uses the **mozilla-django-oidc** library for OIDC authentication. This enables users to authenticate via Google. All endpoints are secured with the `IsAuthenticated` permission, ensuring that only authenticated users can access the system beyond basic read-only actions (like viewing products).

### 🔐 Authentication Flow

### Customers: OpenID Connect (OIDC)

Customers are authenticated using OpenID Connect (OIDC) for a seamless and secure login experience. The flow ensures that customer profiles are complete before accessing protected resources.

1.  **Login with OIDC:**  
    Customers are redirected to the OIDC provider for authentication.
    
2.  **Callback and Token Handling:**  
    Upon successful login, the system processes the returned OIDC tokens to authenticate the user.
    
3.  **Profile Validation:**
    
    *   After authentication, the system checks if the customer's profile contains a valid **phone number**.
    *   **If the phone number is missing**, the user is redirected to the **Update Profile** page to complete their details before proceeding. The phone number is important for enabling sms notifications for customers.
4.  **Access Granted:**  
    Once the profile is complete, the customer can access the application’s full set of features.
    

### Admin: Standard Django Authentication

Admins use the default **Django Admin authentication** for login and management tasks. This ensures that admins have full access to manage the system securely.

*   Admins can log in through the `/admin` endpoint.
*   Permissions are set up to restrict access to sensitive resources based on the admin's role.
*   The admin panel provides full control over categories, products, orders, and user management.

#### **Default Authentication Classes**
The following authentication classes are configured in `settings.py`:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'mozilla_django_oidc.contrib.drf.OIDCAuthentication',  # Core OIDC Authentication
        'rest_framework.authentication.SessionAuthentication',  # for web-based sessions
    ),
}
```
- **OIDCAuthentication:** Verifies user identity via Google OpenID Connect.
- **SessionAuthentication:** Supports browser-based sessions for authenticated users.

--- 


## Permissions Overview
Permissions are managed using custom classes to ensure appropriate access based on user roles. Below is a breakdown of permissions for each resource:

#### Orders
- **Customers:**
  - Can create new orders.
  - Can view only their own orders.
  - Cannot update or delete any order.
- **Admins:**
  - Can view all orders.
  - Can update the status of an order using the `PATCH` method.
  - Can approve and cancel orders.
  - Cannot delete or modify other order details.
  

#### Products
- **Customers:** Read-only access to product information.
- **Admins:** Full access to create, update, and delete products. **NB**: can only edit product details like price and stock

#### Categories
For **Admins** only
- Can create and edit categories.


### **Permission Classes**

I have implemented custom permission classes to enforce fine-grained access control. Here’s an overview of the key permission rules:

1. **`IsAdminOrReadOnly`**
   - **Read-Only Access:** Available to all authenticated users.
   - **Modification Access:** Restricted to admin users.

2. **`IsOrderOwnerOrAdminWithLimitedUpdate`**
    - **Customers:** Can create and only access their own orders.
    - **Admins:** Can view all orders and update the status using the `PATCH` method, but cannot delete or full modify order details(`PUT` operations).
    - Used for managing **orders**.

#### Implementation:
    ```python
    from rest_framework.permissions import BasePermission, SAFE_METHODS
    
    class IsAdminOrReadOnly(BasePermission):
    """Allow read-only access for everyone, but only admins can modify resources."""

    def has_permission(self, request, view):
        # Allow read-only access for everyone
        if request.method in SAFE_METHODS:
            return True

        # Only authenticated admins can modify resources
        return (
            request.user.is_authenticated
            and hasattr(request.user, "role")
            and request.user.role == User.ADMIN
        )

    def has_object_permission(self, request, view, obj):
        # Ensure the user is authenticated and has a role attribute before checking
        if (
            request.user.is_authenticated
            and hasattr(request.user, "role")
            and request.user.role == User.ADMIN
        ):
            return True

        # Deny all other modifications
        return False

    ```
### Usage
- The custom permission classes are applied in the corresponding viewsets.

**Example for Orders:**
```python
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related('customer').prefetch_related('order_items__product').all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsOrderOwnerOrAdminWithLimitedUpdate]
```

**Example for Products:**
```python
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
```

---

### **Examples of Permission Enforcement**

#### **Product Endpoints:**
- **GET /products/** – Any authenticated user can view the product list.
- **PATCH /products/{id}/** – Only admin users can modify product details (e.g., price, stock).
- **DELETE /products/{id}/** – Only admin users can delete a product.

#### **Order Endpoints:**
- **GET /orders/** – Admin users can view all orders, while customers can only view their own orders.
- **PATCH /orders/{id}/** – Admin users can modify order status; customers cannot modify any order.

---

### **Common Scenarios and Expected Behavior**
- **Authenticated Customer Viewing Products:** Allowed.
- **Customer Attempting to Modify a Product:** Denied (`403 Forbidden`).
- **Admin Modifying Product Price and Stock:** Allowed (`200 OK`).
- **Unauthenticated User Accessing Any Endpoint (Except Login):** Denied (`401 Unauthorized`).

### **Test Coverage**
The following tests ensure that permissions are correctly enforced:
- **Admin Access:** Ensure admins can modify and delete products.
- **Customer Restrictions:** Ensure customers can only view products and orders they own.
- **Unauthenticated Access:** Ensure unauthenticated users are denied access.

Example Test for Admin Access:
```python
@pytest.mark.django_db
def test_admin_can_update_product(user_admin, product_factory):
    client = APIClient()
    product = product_factory()
    client.force_authenticate(user=user_admin)

    response = client.patch(
        reverse('product-detail', args=[product.id]),
        {'price': 200, 'stock': 50},
        format='json'
    )
    assert response.status_code == status.HTTP_200_OK
    product.refresh_from_db()
    assert product.price == 200
    assert product.stock == 50
```

---

This section covers all relevant aspects of authentication and permission management. For detailed endpoint descriptions and additional examples, see the **API Endpoints** section.

  

---


---

## CI/CD Workflow

The project uses GitHub Actions for continuous integration and deployment. The workflow includes:

1. **Building the Docker image**: Ensures the application can be containerized without errors.
2. **Running Tests**: Executes `pytest` to validate the code.
3. **Pushing to Docker Hub**: Builds and pushes the Docker image to Docker Hub.
4. **Deployment to Kubernetes**: Deploys the latest image to the Kubernetes cluster. An example CD job is defined as deployment was done local environment using `minikube`

---
