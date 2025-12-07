// D:\chem_portal_ui\server.js
const express = require("express");
const path = require("path");
const app = express();
const PORT = 3000;

// Middleware untuk melayani file statis dari folder 'public'
app.use(express.static(path.join(__dirname, "public")));

// Rute utama: melayani index.html
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "public", "index.html"));
});

// Endpoint konfigurasi untuk frontend
app.get("/config", (req, res) => {
  res.json({
    backendUrl: process.env.BACKEND_URL || "http://127.0.0.1:8000",
  });
});

// Mulai server
app.listen(PORT, () => {
  console.log(`Frontend server berjalan di http://localhost:${PORT}`);
  console.log("Pastikan backend FastAPI berjalan di port 8000.");
});
