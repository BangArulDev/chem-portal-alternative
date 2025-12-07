(rdkit-env) D:\chem_portal>python src/model_training.py
Mulai pelatihan model Random Forest...

--- Metrik Evaluasi pada Data Uji ---
Target MolWeight: R2=0.8303, RMSE=56.6886
Target ExactMass: R2=0.8332, RMSE=56.1141
Target HBondDonors: R2=0.3126, RMSE=0.9302
Target HBondAcceptors: R2=0.6971, RMSE=1.2701
Target TPSA: R2=0.9970, RMSE=1.9245
Target LogP: R2=0.9961, RMSE=0.1622
Target RotatableBonds: R2=0.9363, RMSE=0.9872

Model ML disimpan: src/chemical_predictor_model_rf.pkl
Database Lookup disimpan: src/chemical_database_for_lookup.pkl

recommended_compound.Properties	Random Forest (ML)	Pastikan nilai MolWeight, LogP, dan TPSA memiliki nilai yang logis (misalnya, LogP harus tinggi jika Solubility input sangat rendah).
recommended_compound.SMILES	KNN Lookup	Pastikan ini adalah string SMILES yang valid dan sesuai dengan properti prediksi.
justification_ai	Gemini API (Agentic AI)	Pastikan ini adalah teks naratif yang masuk akal yang menjelaskan korelasi antara SMILES, properti yang diprediksi, dan kriteria input Anda.
Structure_2D_Path & Structure_3D_Path	RDKit (utils.py)	Cek path ini. File gambar (.png) dan koordinat 3D (.mol) seharusnya telah dibuat di folder results/ proyek Anda.

Method,Endpoint,Fungsi Utama,Output
GET,/,"Root Health Check. Memeriksa apakah server berjalan dan komponen inti (ML Model, Gemini Client) dimuat.",JSON Status (OK atau Service Degraded).
GET,/criteria,"Daftar Kriteria Input. Mengambil daftar fitur yang harus dimasukkan pengguna (Solubility, Viscosity_cP, dll.).",Array JSON berisi string nama kriteria.
GET,/properties,"Daftar Properti Output. Mengambil daftar properti kimia yang diprediksi oleh Model ML (MolWeight, LogP, TPSA, dll.).",Array JSON berisi string nama properti.

MethodEndpointFungsi UtamaInput Body (Contoh)OutputPOST/discoverMulai Penemuan Senyawa. Menerima kriteria pengguna, menjalankan Model ML, mencari SMILES terdekat, dan meminta justifikasi dari Gemini Agent.Kriteria kimia dalam format JSON (misalnya, {"Solubility": 0.05, "Viscosity_cP": 400.0, ...}).JSON kompleks berisi SMILES, Properti Prediksi, Path Visualisasi (2D/3D), dan Justifikasi AI.

backend
uvicorn src.api_service:app --reload

fronend
D:\chem_portal\frontend_js> node server.js
http://localhost:3000/

http://127.0.0.1:8000/docs#/default/get_results_file_results__filename__get