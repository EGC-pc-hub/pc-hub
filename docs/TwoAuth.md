# Two-Factor Authentication (TwoAuth)

This feature implements a two-factor authentication (2FA) system using email. It adds an extra layer of security by requiring users to enter a verification code sent to their email address during login and signup.

> [!NOTE]
> **TwoAuth is not implemented on Render** because [Render does not allow mail servers to run on their platform](https://community.render.com/t/mail-server-on-render-com/10529). For deployments on Render, TwoAuth must be disabled by setting `ENABLE_2FA=false`.

## User Experience Overview

- **Login**:
    1. User enters credentials (email/password).
    2. If valid, the user is redirected to the 2FA verification page.
    3. An email with a 6-digit code is sent to the user's registered email.
    4. User enters the code.
    5. If correct, the user is logged in and redirected to the dashboard.

- **Signup**:
    1. User fills out the registration form.
    2. User is redirected to the 2FA verification page.
    3. An email with a 6-digit code is sent to the provided email.
    4. User enters the code.
    5. If correct, the account is created, and the user is logged in.

## Prerequisites

To enable TwoAuth, you need to configure an SMTP server for sending emails. The system is pre-configured to work with Gmail, but requires a specific setup using **App Passwords**.

### Gmail Configuration (App Passwords)

Since Google no longer supports "Less Secure Apps" for personal accounts, you must use an **App Password**.

1.  **Enable 2-Step Verification** on your Google Account:
    - Go to [Google Account Security](https://myaccount.google.com/security).
    - Under "How you sign in to Google", enable **2-Step Verification**.

2.  **Generate an App Password**:
    - Go to the search bar in your Google Account settings and search for "App passwords".
    - Create a new app password (e.g., name it "PC-Hub").
    - Google will generate a 16-character password (e.g., `dhap bzqi fbke fqxe`).

3.  **Configure `.env`**:
    - Use your Gmail address as `MAIL_USERNAME` and `MAIL_DEFAULT_SENDER`.
    - Use the generated 16-character App Password as `MAIL_PASSWORD`.

## Configuration

Configure the following environment variables in your `.env` file:

```env
# Email (SMTP)
EMAIL_BACKEND=smtp
MAIL_SUPPRESS_SEND=false

# SMTP Settings (Gmail Example)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=465
MAIL_USE_TLS=false
MAIL_USE_SSL=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD="your generated app password"  # The 16-char App Password
MAIL_FROM_NAME="PC Hub"
MAIL_DEFAULT_SENDER="your-email@gmail.com"

# Two-factor auth (2AUTH)
ENABLE_2FA=true
TWOAUTH_TTL_MINUTES=10          # Code validity duration
TWOAUTH_RESEND_COOLDOWN_SEC=30  # Time before a new code can be requested
TWOAUTH_EMAIL_SUBJECT="Tu código de verificación (PC Hub)"
```

> [!IMPORTANT]
> Never use your real Google account password. Always use an App Password.

## Technical Details

The TwoAuth system is implemented in the `app/modules/twoauth` module.

### Core Components

-   **`TwoAuthService`**: Handles logic for generating, sending, and verifying codes.
    -   `create_and_send_code(user)`: Generates a code, saves it to the database (`TwoFactorToken`), and sends an email.
    -   `verify_code(user, code)`: Validates the code against the database.
    -   `create_and_send_signup_code(email)`: Handles 2FA for signup (stores state in session since the user doesn't exist yet).

-   **Database Model**:
    -   `TwoFactorToken`: Stores the code, user ID, expiration time, and used status.

-   **Session Management**:
    -   `2fa_user_id`: Stores the user ID temporarily during the login 2FA step.
    -   `pending_signup`: Stores registration data temporarily during the signup 2FA step.

### Security Measures

-   **TTL (Time To Live)**: Codes expire after `TWOAUTH_TTL_MINUTES` (default: 10 minutes).
-   **One-Time Use**: Codes are marked as `used` after successful verification.
-   **Cooldown**: Users must wait `TWOAUTH_RESEND_COOLDOWN_SEC` (default: 30 seconds) before requesting a new code.
-   **Session Cleanup**: Temporary session variables are cleared after successful login/signup or upon failure.

## Troubleshooting

-   **Email not received**:
    -   Check `app.log` for SMTP errors.
    -   Verify `MAIL_USERNAME` and `MAIL_PASSWORD` in `.env`.
    -   Ensure `MAIL_PORT` is 465 and `MAIL_USE_SSL` is `true` for Gmail.
-   **"Invalid or expired code"**:
    -   Ensure the code was entered within `TWOAUTH_TTL_MINUTES`.
    -   Check if the code was already used.
-   **SMTP Authentication Error**:
    -   Verify you are using an **App Password**, not your login password.
    -   Ensure 2-Step Verification is enabled on the Google Account.

## Other documentation

-   [Flask-Mail Documentation](https://flask-mail.readthedocs.io/en/latest/)
-   [Sign in with App Passwords (Google Help)](https://support.google.com/accounts/answer/185833)