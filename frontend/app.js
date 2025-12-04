// Frontend JS: Firebase Auth (Google Sign-In) + basic album/photo flows.
// This script requests runtime client config from the backend Cloud Function and initializes Firebase.

async function initFirebaseClient() {
  try {
    let configUrl = '/api/config';
    try {
      let resp = await fetch(configUrl);
      if (!resp.ok) throw new Error('Not found');
      const cfg = await resp.json();
      firebase.initializeApp(cfg);
      return;
    } catch (e1) {
      // Fallback: try via localhost
      configUrl = 'http://localhost:5000/config';
      const resp = await fetch(configUrl);
      if (!resp.ok) throw new Error('Could not load config');
      const cfg = await resp.json();
      firebase.initializeApp(cfg);
      return;
    }
  } catch (err) {
    console.error('Failed to init Firebase client:', err);
    // fall back to placeholder (will fail auth until configured)
    firebase.initializeApp({apiKey: 'REPLACE_ME'});
  }
}

function startApp(){
  const auth = firebase.auth();

  const loginBtn = document.getElementById("login");
const logoutBtn = document.getElementById("logout");
const albumsList = document.getElementById("albums-list");

// views
const viewAlbums = document.getElementById("view-albums");
const viewAlbum = document.getElementById("view-album");
const viewUpload = document.getElementById("view-upload");
const viewPhoto = document.getElementById("view-photo");

const createAlbumBtn = document.getElementById("create-album-btn");
const albumTitle = document.getElementById("album-title");
const albumUploadBtn = document.getElementById("album-upload-btn");
const albumDeleteBtn = document.getElementById("album-delete-btn");
const backToAlbumsBtn = document.getElementById("back-to-albums");
const photosList = document.getElementById("photos-list");

const uploadFiles = document.getElementById("upload-files");
const uploadStartBtn = document.getElementById("upload-start-btn");
const uploadCancelBtn = document.getElementById("upload-cancel-btn");
const uploadStatus = document.getElementById("upload-status");
const uploadAlbumTitle = document.getElementById("upload-album-title");

const photoArea = document.getElementById("photo-area");
const photoDescription = document.getElementById("photo-description");
const photoBackBtn = document.getElementById("photo-back-btn");
const photoEditDescBtn = document.getElementById("photo-edit-desc-btn");
const photoDeleteBtn = document.getElementById("photo-delete-btn");

const dialog = document.getElementById("dialog");

loginBtn.addEventListener("click", async () => {
  const provider = new firebase.auth.GoogleAuthProvider();
  try {
    await auth.signInWithPopup(provider);
  } catch (err) {
    alert(err.message);
  }
});
logoutBtn.addEventListener("click", async () => {
  await auth.signOut();
});

auth.onAuthStateChanged(async (user) => {
  if (user) {
    loginBtn.style.display = "none";
    logoutBtn.style.display = "inline-block";
    await loadAlbums();
  } else {
    loginBtn.style.display = "inline-block";
    logoutBtn.style.display = "none";
    albumsList.innerHTML = "<p>Please sign in to view albums.</p>";
    showView('albums');
  }
});

async function getIdToken() {
  const user = auth.currentUser;
  if (!user) return null;
  return await user.getIdToken();
}

async function isAdmin() {
  const user = auth.currentUser;
  if (!user) return false;
  const idTokenResult = await user.getIdTokenResult();
  return !!(idTokenResult && idTokenResult.claims && idTokenResult.claims.admin);
}

async function apiFetch(path, opts = {}) {
  const token = await getIdToken();
  opts.headers = opts.headers || {};
  opts.headers["Content-Type"] = opts.headers["Content-Type"] || "application/json";
  if (token) opts.headers["Authorization"] = `Bearer ${token}`;
  const resp = await fetch(path, opts);
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`API error: ${resp.status} ${text}`);
  }
  return resp.json();
}

async function loadAlbums() {
  albumsList.innerHTML = "Loading...";
  try {
    const data = await apiFetch("/api/albums");
    if (!data.albums) data.albums = [];
    albumsList.innerHTML = "";
    const admin = await isAdmin();
    if (admin) createAlbumBtn.style.display = 'inline-block'; else createAlbumBtn.style.display = 'none';
    data.albums.forEach(a => {
      const div = document.createElement("div");
      div.className = "album-item";
      const cover = a.cover_url ? `<img src="${escapeHtml(a.cover_url)}" style="width:120px;height:80px;object-fit:cover;display:block;">` : `<div style="width:120px;height:80px;background:rgba(0,0,0,0.04);"></div>`;
      div.innerHTML = `${cover}<strong>${escapeHtml(a.title)}</strong><p>${escapeHtml(a.description||"")}</p>`;
      div.addEventListener("click", () => openAlbum(a));
      albumsList.appendChild(div);
    });
  } catch (err) {
    albumsList.innerHTML = `<p>Error: ${escapeHtml(err.message)}</p>`;
  }
}

function escapeHtml(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }

let currentAlbum = null;
async function openAlbum(album) {
  currentAlbum = album;
  showView('album');
  albumTitle.textContent = album.title;
  photosList.innerHTML = "Loading photos...";
  try {
    const data = await apiFetch(`/api/albums/${album.id}/photos`);
    photosList.innerHTML = "";
    const admin = await isAdmin();
    albumUploadBtn.style.display = admin ? 'inline-block' : 'none';
    albumDeleteBtn.style.display = admin ? 'inline-block' : 'none';
    (data.photos||[]).forEach(p => {
      const d = document.createElement("div");
      d.className = "photo-item";
      d.innerHTML = `<img src="${escapeHtml(p.public_url||'')}"><div>${escapeHtml(p.filename||'')}</div>`;
      d.addEventListener('click', () => openPhoto(p));
      photosList.appendChild(d);
    });
  } catch (err) {
    photosList.innerHTML = `<p>Error: ${escapeHtml(err.message)}</p>`;
  }
}

function showView(name){
  viewAlbums.style.display = (name==='albums') ? 'block' : 'none';
  viewAlbum.style.display = (name==='album') ? 'block' : 'none';
  viewUpload.style.display = (name==='upload') ? 'block' : 'none';
  viewPhoto.style.display = (name==='photo') ? 'block' : 'none';
}

// Album page buttons
albumUploadBtn.addEventListener('click', () => {
  uploadAlbumTitle.textContent = currentAlbum.title;
  showView('upload');
});
backToAlbumsBtn.addEventListener('click', () => { showView('albums'); });

createAlbumBtn.addEventListener('click', async () => {
  const title = prompt('Album title');
  if (!title) return;
  try {
    await apiFetch('/api/albums', {method:'POST', body: JSON.stringify({title, description:''})});
    await loadAlbums();
  } catch (e){ alert(e.message); }
});

albumDeleteBtn.addEventListener('click', async () => {
  if (!confirm('Delete album?')) return;
  try{
    const res = await apiFetch(`/api/albums/${currentAlbum.id}`, {method:'DELETE'});
    if (res.error) return alert(res.error);
    alert('Deleted');
    await loadAlbums();
    showView('albums');
  }catch(e){ alert(e.message); }
});

// Upload page
uploadCancelBtn.addEventListener('click', () => { showView('album'); });
uploadStartBtn.addEventListener('click', async () => {
  const files = Array.from(uploadFiles.files || []);
  if (!files.length) return alert('Select files');
  uploadStatus.innerHTML = '';
  try{
    const filenames = files.map(f=>f.name);
    const gen = await apiFetch('/api/generate_upload_urls', {method:'POST', body: JSON.stringify({album_id: currentAlbum.id, filenames})});
    const results = gen.results;
    for (let i=0;i<results.length;i++){
      const r = results[i];
      const f = files.find(x=>x.name===r.filename);
      uploadStatus.innerHTML += `<div>Uploading ${escapeHtml(r.filename)}...</div>`;
      const putResp = await fetch(r.upload_url, {method:'PUT', body: f});
      if (!putResp.ok) throw new Error('Upload failed for '+r.filename);
      // register
      await apiFetch('/api/photos', {method:'POST', body: JSON.stringify({album_id: currentAlbum.id, filename: r.filename, blob_path: r.blob_path, public_url: `https://storage.googleapis.com/${encodeURIComponent(r.blob_path)}`})});
      uploadStatus.innerHTML += `<div>Uploaded ${escapeHtml(r.filename)}</div>`;
    }
    alert('All uploaded');
    await openAlbum(currentAlbum);
  }catch(e){ alert(e.message); }
});

// Photo view
let currentPhoto = null;
async function openPhoto(photo){
  currentPhoto = photo;
  showView('photo');
  photoArea.innerHTML = `<img src="${escapeHtml(photo.public_url||'')}" style="max-width:100%">`;
  photoDescription.textContent = photo.description || '';
  const admin = await isAdmin();
  photoEditDescBtn.style.display = admin ? 'inline-block' : 'none';
  photoDeleteBtn.style.display = admin ? 'inline-block' : 'none';
}

photoBackBtn.addEventListener('click', () => { showView('album'); });

photoEditDescBtn.addEventListener('click', async ()=>{
  const newDesc = prompt('Photo description', currentPhoto.description||'');
  if (newDesc==null) return;
  try{
    await apiFetch(`/api/photos/${currentAlbum.id}/${currentPhoto.id}/description`, {method:'PUT', body: JSON.stringify({description: newDesc})});
    currentPhoto.description = newDesc;
    photoDescription.textContent = newDesc;
    alert('Updated');
  }catch(e){ alert(e.message); }
});

  photoDeleteBtn.addEventListener('click', async ()=>{
    if (!confirm('sure to delete?')) return;
    try{
      await apiFetch(`/api/photos/${currentAlbum.id}/${currentPhoto.id}`, {method:'DELETE'});
      alert('Deleted');
      await openAlbum(currentAlbum);
    }catch(e){ alert(e.message); }
  });
}

initFirebaseClient().then(startApp).catch(err=>{ console.error('Failed to init firebase or start app', err); startApp(); });
