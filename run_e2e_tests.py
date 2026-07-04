import os
import sys
import builtins
from fastapi.testclient import TestClient

def safe_print(*args, **kwargs):
    encoding = sys.stdout.encoding or "utf-8"
    new_args = []
    for arg in args:
        if isinstance(arg, str):
            s = arg.replace("🚀", "[RUN]").replace("✅", "[OK]").replace("❌", "[ERROR]").replace("🎉", "[SUCCESS]")
            s = s.encode(encoding, errors="replace").decode(encoding)
            new_args.append(s)
        else:
            new_args.append(arg)
    builtins.print(*new_args, **kwargs)

print = safe_print

TEST_DB_FILE = "./test_temp.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_FILE}"
os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://localhost:8000"

if os.path.exists(TEST_DB_FILE):
    try:
        os.remove(TEST_DB_FILE)
    except Exception:
        pass

from app.main import app
from app.database.session import SessionLocal, engine, Base
from app.models.models import Invitation

Base.metadata.create_all(bind=engine)

client = TestClient(app)

def print_banner(msg: str):
    print("\n" + "=" * 80)
    print(f"🚀 {msg}")
    print("=" * 80)

def get_invitation_token(email: str) -> str:
    db = SessionLocal()
    try:
        invitation = db.query(Invitation).filter(Invitation.email == email.lower()).first()
        assert invitation is not None, f"No invitation found for {email}"
        return invitation.invitation_token
    finally:
        db.close()

def main():
    try:
        print_banner("Step 1: Bootstrap Admin Registration")
        reg_payload = {
            "email": "admin@focusguard.ai",
            "full_name": "Chief Architect",
            "password": "secure_admin_password_123",
        }
        res = client.post("/auth/register", json=reg_payload)
        print(f"Response: {res.status_code} | {res.json()}")
        assert res.status_code == 201
        assert res.json()["email"] == "admin@focusguard.ai"
        assert res.json()["role"] == "ADMIN"
        assert res.json()["organization_id"] is None
        print("✅ Bootstrap admin registration succeeded.")

        print_banner("Step 2: Block Second Admin Registration")
        second_admin_payload = {
            "email": "other-admin@focusguard.ai",
            "full_name": "Another Admin",
            "password": "secure_admin_password_999",
        }
        res = client.post("/auth/register", json=second_admin_payload)
        print(f"Response (Expected Error): {res.status_code} | {res.json()}")
        assert res.status_code == 403
        assert "Admin registration is closed" in res.json()["detail"]
        print("✅ Second admin registration correctly blocked.")

        print_banner("Step 3: Admin Authentication (Login)")
        login_data = {
            "username": "admin@focusguard.ai",
            "password": "secure_admin_password_123",
        }
        res = client.post("/auth/login", data=login_data)
        print(f"Response: {res.status_code} | {res.json()}")
        assert res.status_code == 200
        token = res.json()["access_token"]
        assert token is not None
        assert "refresh_token" not in res.json()
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Admin login completed. Access token generated.")

        print_banner("Step 4: Retrieve Admin Profile via /me")
        res = client.get("/auth/me", headers=headers)
        print(f"Response: {res.status_code} | {res.json()}")
        assert res.status_code == 200
        assert res.json()["email"] == "admin@focusguard.ai"
        admin_id = res.json()["id"]
        print("✅ /me profile matches authenticated Admin.")

        print_banner("Step 5: Create Organization and Auto-link Admin")
        org_payload = {"organization_name": "FocusGuard Corp"}
        res = client.post("/organizations/create", json=org_payload, headers=headers)
        print(f"Response: {res.status_code} | {res.json()}")
        assert res.status_code == 201
        org_id = res.json()["id"]

        res = client.get("/auth/me", headers=headers)
        assert res.json()["organization_id"] == org_id
        print("✅ Organization created. Admin automatically linked.")

        print_banner("Step 6: Generate Invitation (Token Not Exposed in Response)")
        invite_payload = {"email": "employee@focusguard.ai"}
        res = client.post("/admin/invite-user", json=invite_payload, headers=headers)
        print(f"Response: {res.status_code} | {res.json()}")
        assert res.status_code == 201
        assert "invitation_token" not in res.json()
        assert res.json()["email"] == "employee@focusguard.ai"
        assert res.json()["organization_id"] == org_id
        assert res.json()["invited_by"] == admin_id
        invitation_token = get_invitation_token("employee@focusguard.ai")
        print("✅ Invitation created. Token retrieved internally (simulates email delivery).")

        print_banner("Step 7: Block Public Registration for Employees")
        employee_register_payload = {
            "email": "employee@focusguard.ai",
            "full_name": "Rogue Employee",
            "password": "somepassword123",
            "role": "EMPLOYEE",
            "organization_id": org_id,
        }
        res = client.post("/auth/register", json=employee_register_payload)
        print(f"Response (Expected Error): {res.status_code} | {res.json()}")
        assert res.status_code == 403
        print("✅ Public registration cannot create employees or additional admins.")

        print_banner("Step 8: Complete Setup (Employee Onboarding)")
        setup_payload = {
            "token": invitation_token,
            "full_name": "Alex Employee",
            "password": "secure_employee_password_456",
        }
        res = client.post("/auth/complete-setup", json=setup_payload)
        print(f"Response: {res.status_code} | {res.json()}")
        assert res.status_code == 201
        assert res.json()["email"] == "employee@focusguard.ai"
        assert res.json()["role"] == "EMPLOYEE"
        assert res.json()["organization_id"] == org_id
        print("✅ Onboarding setup completed successfully.")

        print_banner("Step 9: Block Double Use of Invitation Token")
        res = client.post("/auth/complete-setup", json=setup_payload)
        print(f"Response (Expected Error): {res.status_code} | {res.json()}")
        assert res.status_code == 400
        assert "already been used" in res.json()["detail"]
        print("✅ Correctly blocked re-using an onboarding token.")

        print_banner("Step 10: Block Invalid Invitation Tokens")
        malformed_payload = {
            "token": "fake_token_123",
            "full_name": "Fake Name",
            "password": "securepassword123",
        }
        res = client.post("/auth/complete-setup", json=malformed_payload)
        print(f"Response (Expected Error): {res.status_code} | {res.json()}")
        assert res.status_code == 404
        print("✅ Correctly rejected invalid tokens.")

        print_banner("Step 11: Role-Based Authorization Enforcement")
        employee_login_data = {
            "username": "employee@focusguard.ai",
            "password": "secure_employee_password_456",
        }
        res = client.post("/auth/login", data=employee_login_data)
        assert res.status_code == 200
        employee_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}

        res = client.post("/admin/invite-user", json={"email": "other@focusguard.ai"}, headers=employee_headers)
        print(f"Response (Expected Error): {res.status_code} | {res.json()}")
        assert res.status_code == 403
        print("✅ RBAC enforced. Employee forbidden from admin routes.")

        print_banner("🎉 ALL TESTS PASSED SUCCESSFULLY! 🎉")
    except AssertionError:
        print("\n❌ TEST FAILURE DETECTED!")
        sys.exit(1)
    finally:
        try:
            engine.dispose()
        except Exception:
            pass
        if os.path.exists(TEST_DB_FILE):
            try:
                os.remove(TEST_DB_FILE)
            except Exception as e:
                print(f"Warning: Could not remove test DB file: {e}")

if __name__ == "__main__":
    main()
