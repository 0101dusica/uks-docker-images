# Superadmin Setup

## How It Works

When the system starts for the first time, a **superadmin** account is automatically created. The initial password is randomly generated and saved to a file inside the backend container.

## Getting the Initial Password

After starting the application, run:

```bash
docker compose exec backend cat superadmin_initial_password.txt
```

This will output something like:

```
Superadmin initial credentials
Username: superadmin
Password: hI#B_Uo}GKvRo[#&

Please change this password on first login.
```

## First Login

1. Go to `http://localhost:8000/login/`
2. Log in using the username and password from the file
3. You will be redirected to the **Change Password** page
4. Enter and confirm a new password (minimum 8 characters)
5. After changing the password, you will be redirected to the superadmin dashboard

> **Note:** You cannot access any part of the system until the initial password is changed.

## Security Notes

- The password file has restricted permissions (`600`) inside the container
- The file is listed in `.gitignore` and will never be committed
- After changing the password, the file can be safely deleted from the container:
  ```bash
  docker compose exec backend rm superadmin_initial_password.txt
  ```
