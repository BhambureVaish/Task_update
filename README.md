# Task_update
# User Management System

## Overview
This project implements a user management system with "Forgot Password" and "Reset Password" features. It utilizes FastAPI for building the API, SQLAlchemy for database interactions, Passlib for password hashing, Python-Jose for handling JWT tokens, FastAPI-Mail for sending emails, and dotenv for managing environment variables.

- ## Features
- **User Registration**: Allows users to create an account.
- **User Login**: Users can log into their accounts.
- **Forgot Password**: Users can request a password reset link via email.
- **Reset Password**: Users can reset their password using the link sent to their email.


## Implementation Workflow

### 1. Setup Environment
#### Libraries Used:
- **FastAPI**: Framework for building the API.
- **SQLAlchemy**: ORM for database interactions.
- **Passlib**: Library for password hashing.
- **Python-Jose (JWT)**: Library for encoding and decoding JSON Web Tokens.
- **FastAPI-Mail**: To send emails for password reset.
- **dotenv**: To manage environment variables.

### 2. Database Configuration
- Set up a PostgreSQL database using the database URL in the `.env` file.
- Defined a `User` model that includes fields for user information and password reset tokens.

### 3. Password Hashing
- Utilized Passlib to securely hash user passwords.

### 4. Email Configuration
- Configured FastAPI-Mail to use Gmail's SMTP server for sending password reset emails.

## Feature Implementation
### 1. User Registration
- **Endpoint**: `POST /register`
- **Functionality**: Creates a new user account.
- **Request Body**:
  ```json
  {
    "first_name": "Vaish",
    "last_name": "Bhambure",
    "email": "vaishb@gmail.com",
    "phone_number": "1234567890",
    "password": "securepassword"
  }
### 2.Login User
- **Endpoint**: `POST /login`
- **Method**: `POST`

-**Request Body**:
To log in, users need to provide their email and password in the request body. The request should be formatted as JSON:
```json
 {
 "email": "vaishb@gmail.com",
"password": "securepassword"
}
### 3. Forgot Password Feature
- **Endpoint**: `POST /forgot-password`
- **Functionality**:
  - The user provides their email address.
  - The system checks if the email exists in the database.
  - If the email exists, a JWT token is generated with an expiration time (1 hour).
  - An email is sent to the user with a link containing the reset token.
- **Request Body**:
```json
{
  "email": "vaishb@gmail.com"
}

### Reset Password
- **Endpoint**: `POST /reset-password`
- **Method**: `POST`

#### Request Parameters
To reset a password, users must send a token and their new password in the request body.

#### Request Body
```json
{
  "token": "your_reset_token",
  "new_password": "your_new_secure_password"
}
