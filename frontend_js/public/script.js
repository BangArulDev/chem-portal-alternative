// D:\chem_portal_ui\public\script.js

// Variabel Global untuk URL Backend (akan diisi dari /config)
let BACKEND_URL = "http://127.0.0.1:8000";

// --- AUTHENTICATION LOGIC ---

function getToken() {
  return localStorage.getItem("access_token");
}

function isLoggedIn() {
  return !!getToken();
}

function logout() {
  localStorage.removeItem("access_token");
  window.location.href = "/login.html";
}

async function login(username, password) {
  const formData = new URLSearchParams();
  formData.append("username", username);
  formData.append("password", password);

  const response = await fetch(`${BACKEND_URL}/token`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: formData,
  });

  if (!response.ok) {
    let errorMsg = "Login failed";
    try {
      const error = await response.json();
      errorMsg = error.detail || errorMsg;
    } catch (e) {
      // Fallback if response is not JSON (e.g. 500 HTML or raw text)
      errorMsg = `Server Error (${response.status}): ${response.statusText}`;
      const text = await response.text();
      if (text) console.error("Raw Error Response:", text);
    }
    throw new Error(errorMsg);
  }

  const data = await response.json();
  localStorage.setItem("access_token", data.access_token);
  return data.access_token;
}

async function register(username, password) {
  const response = await fetch(`${BACKEND_URL}/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Registration failed");
  }

  return true;
}

function checkAuthProtection() {
  // Jika bukan di halaman login atau register, cek token
  const path = window.location.pathname;
  if (!path.includes("login.html") && !path.includes("register.html")) {
    if (!isLoggedIn()) {
      window.location.href = "/login.html";
    }
  }
}

// --- MAIN APP LOGIC ---

async function init() {
  try {
    // 1. Ambil konfigurasi backend URL dari server frontend sendiri
    const configRes = await fetch("/config");
    const config = await configRes.json();
    BACKEND_URL = config.backendUrl;
    console.log("Backend URL set to:", BACKEND_URL);

    // 2. Cek apakah di halaman auth atau main app
    checkAuthProtection();

    // Setup tombol logout jika ada
    const logoutBtn = document.getElementById("btn-logout"); // Nanti bisa ditambahkan di HTML utama
    if (logoutBtn) {
      logoutBtn.addEventListener("click", logout);
    }

    // 3. Setup event listeners untuk Main App (hanya jika elemen ada)
    const btnFind = document.getElementById("btn-find");
    if (btnFind) {
      btnFind.addEventListener("click", handleDiscover);
    }
  } catch (err) {
    console.error("Gagal inisialisasi:", err);
  }
}

async function handleDiscover() {
  const btn = document.getElementById("btn-find");
  const originalText = btn.innerText;

  // UI Loading State
  btn.innerText = "⏳ Sedang Menganalisis...";
  btn.disabled = true;
  document.getElementById("res-name").innerText = "...";
  document.getElementById("res-smiles").innerText = "...";
  document.getElementById("res-props").innerText = "Menghitung...";
  document.getElementById("res-just").innerText = "Meminta pendapat AI...";

  const criteria = {
    Solubility: parseFloat(document.getElementById("solubility").value),
    Viscosity_cP: parseFloat(document.getElementById("viscosity").value),
    ThermalStability_Score: parseFloat(
      document.getElementById("thermal").value
    ),
    BoilingPoint_C: parseFloat(document.getElementById("boiling").value),
  };

  try {
    const token = getToken();
    if (!token) throw new Error("Silakan login kembali.");

    const response = await fetch(`${BACKEND_URL}/discover`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`, // Sertakan Token
      },
      body: JSON.stringify(criteria),
    });

    if (!response.ok) {
      if (response.status === 401) {
        logout(); // Token expired/invalid
        return;
      }
      throw new Error(`API Error: ${response.statusText}`);
    }

    const data = await response.json();
    updateUI(data);
  } catch (error) {
    console.error(error);
    alert("Terjadi kesalahan: " + error.message);
    document.getElementById("res-just").innerText = "Gagal memuat hasil.";
  } finally {
    btn.innerText = originalText;
    btn.disabled = false;
  }
}

function updateUI(data) {
  const cmp = data.recommended_compound;
  const props = cmp.Properties;

  // 1. Info Utama
  document.getElementById("res-name").innerText =
    props.IUPAC || "Tidak diketahui";
  document.getElementById("res-smiles").innerText = cmp.SMILES;
  document.getElementById("res-status").innerText = "✅ Validated by AI";

  // 2. Properti
  const propText = `
MolWeight   : ${props.MolWeight?.toFixed(2)} g/mol
LogP        : ${props.LogP?.toFixed(2)}
TPSA        : ${props.TPSA?.toFixed(2)} Å²
H-Donors    : ${props.HBondDonors}
H-Acceptors : ${props.HBondAcceptors}
Rotatable   : ${props.RotatableBonds}
    `.trim();
  document.getElementById("res-props").innerText = propText;

  // 3. Justifikasi AI
  document.getElementById("res-just").innerText = data.justification_ai;

  // 4. Visualisasi (Gambar)
  const imgEl = document.getElementById("mol-img");
  if (cmp.Structure_2D_Path) {
    // Karena path dari backend relatif ("/results/..."), kita gabung dengan BACKEND_URL
    // Tapi perhatikan di api_service.py returnnya FileResponse, jadi kita bisa akses sebagai URL statis
    // Di sini kita asumsikan api_service melayani path tersebut.
    // Cek endpoint get_results_file di api_service.py: @app.get("/results/{filename}")
    // Path dari backend: "/results/uuid_2d.png" -> kita butuh nama filenya saja
    const filename = cmp.Structure_2D_Path.split("/").pop();
    imgEl.src = `${BACKEND_URL}/results/${filename}`;
  } else {
    imgEl.src = ""; // Placeholder
  }

  // 5. Link Download (.mol)
  const dlLink = document.getElementById("download-mol");
  if (cmp.Structure_3D_Path) {
    const filename3d = cmp.Structure_3D_Path.split("/").pop();
    dlLink.href = `${BACKEND_URL}/results/${filename3d}`;
    dlLink.setAttribute("aria-disabled", "false");
  } else {
    dlLink.setAttribute("aria-disabled", "true");
  }
}

// Jalankan init saat halaman dimuat
document.addEventListener("DOMContentLoaded", init);
