import firebase_admin
from firebase_admin import auth

firebase_admin.initialize_app()

auth.set_custom_user_claims("USER_UID_HERE", {"admin": True})
print("Admin set")
