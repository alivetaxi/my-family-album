# My Family Album

This project scaffolds a private family-only digital photo album using:

- GCP Cloud Functions (Python) for backend API
- Firestore for album/photo metadata
- Cloud Storage for image storage
- Firebase Auth (Google Sign-In) for authentication
- Frontend: static site built with HTMX + Vanilla JS
- Firebase Hosting for frontend deployment
- Terraform to manage infrastructure

Files created by this scaffold:

- `backend/` : Cloud Functions code and `requirements.txt`
- `frontend/` : `index.html`, `app.js`, `styles.css`
- `terraform/` : initial Terraform config to create a storage bucket and service account

Next steps

1. Fill in Firebase web app config in `frontend/app.js` (`FIREBASE_CONFIG`).
2. Create or choose a GCP project and enable billing.
3. Update `terraform/variables.tf` values and run `terraform init` and `terraform apply` to create the bucket and service account.
4. Deploy backend Cloud Function (see `backend/README.md`) and set `IMAGES_BUCKET` to the created bucket.
5. Deploy `frontend/` to Firebase Hosting (create a Firebase project and run `firebase init hosting` then `firebase deploy`).

Environment & secrets

- Use `.env.example` as a reference for local env vars. Do NOT commit real credentials.
- For production, store Firebase Admin credentials in Secret Manager and set `FIREBASE_ADMIN_SECRET_NAME` as a Cloud Function environment variable (Terraform can create the secret for you).

If you'd like, I can:

- fill in more backend routes (delete/edit),
- add Firestore rules and an automated deploy pipeline,
- or create a more complete Terraform plan to provision Firestore and Firebase Hosting.
