import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error
import joblib 
import numpy as np
import os
from typing import List, Optional 
import time

# ==============================================================================
# 1. ⚙️ KONFIGURASI GLOBAL
# ==============================================================================

# Path relatif terhadap D:\chem_portal (root)
DATA_PATH = "data/dataset.csv" 
# Path relatif terhadap D:\chem_portal (tempat file ini berada)
MODEL_SAVE_PATH = 'src/chemical_predictor_model_rf.pkl'
LOOKUP_DB_PATH = 'src/chemical_database_for_lookup.pkl'

INPUT_FEATURES: List[str] = ['Solubility', 'Viscosity_cP', 'ThermalStability_Score', 'BoilingPoint_C']
OUTPUT_TARGETS: List[str] = ['MolWeight', 'ExactMass', 'HBondDonors', 'HBondAcceptors', 'TPSA', 'LogP', 'RotatableBonds']
SMILES_COL: str = 'SMILES' 
IDENTIFIER_COLS: List[str] = ['IUPAC', 'InChI', 'InChIKey']

# ==============================================================================
# 2. 🧠 FUNGSI UTAMA PELATIHAN
# ==============================================================================

def _load_and_preprocess_data(data_path: str) -> Optional[pd.DataFrame]:
    """Muat data dan lakukan pembersihan."""
    # Menyesuaikan path untuk file data jika skrip dijalankan dari root
    if not os.path.exists(data_path):
        print(f"❌ ERROR: File data tidak ditemukan di {data_path}.")
        return None

    df = pd.read_csv(data_path)
    required_cols_train = INPUT_FEATURES + OUTPUT_TARGETS + [SMILES_COL]
    df_clean = df.dropna(subset=required_cols_train)
    print(f"Data dimuat. Baris bersih: {len(df_clean)} / Total: {len(df)}")
    return df_clean

def _save_lookup_database(df_clean: pd.DataFrame):
    """Menyimpan subset data untuk database lookup (termasuk Identifiers)."""
    required_cols_lookup = [SMILES_COL] + OUTPUT_TARGETS + IDENTIFIER_COLS
    
    try:
        # PENTING: Path penyimpanan harus disesuaikan jika dijalankan dari root
        full_lookup_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), LOOKUP_DB_PATH)
        df_lookup = df_clean[required_cols_lookup]
        joblib.dump(df_lookup, full_lookup_path)
        print(f"✅ Database lookup disimpan: {LOOKUP_DB_PATH}")
    except KeyError as e:
        print(f"⚠️ PERINGATAN: Kolom identitas tidak lengkap. Lookup DB hanya menyimpan SMILES dan OUTPUT_TARGETS.")
        joblib.dump(df_clean[[SMILES_COL] + OUTPUT_TARGETS], LOOKUP_DB_PATH)

def _evaluate_model(model: MultiOutputRegressor, X_test: pd.DataFrame, Y_test: pd.DataFrame):
    """Menghitung dan mencetak metrik R2 dan RMSE."""
    Y_pred = model.predict(X_test)
    print("\n--- Metrik Evaluasi pada Data Uji (20%) ---")
    
    for i, target in enumerate(OUTPUT_TARGETS):
        r2 = r2_score(Y_test.iloc[:, i], Y_pred[:, i])
        rmse = np.sqrt(mean_squared_error(Y_test.iloc[:, i], Y_pred[:, i]))
        print(f"Target {target.ljust(15)}: R2={r2:.4f}, RMSE={rmse:.4f}")

def train_random_forest_predictor():
    """Melaksanakan seluruh alur pelatihan."""
    print("--- Memulai Pelatihan Model Prediktor Kimia ---")

    # Path data relatif terhadap root proyek
    data_path_from_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), DATA_PATH)
    df_clean = _load_and_preprocess_data(data_path_from_root)
    if df_clean is None: return

    X = df_clean[INPUT_FEATURES]
    Y = df_clean[OUTPUT_TARGETS]
    
    _save_lookup_database(df_clean)
    
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)
    
    print("Mulai pelatihan model Random Forest Multi-Output...")
    rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model = MultiOutputRegressor(rf)
    model.fit(X_train, Y_train)
    
    _evaluate_model(model, X_test, Y_test)
    
    # Path penyimpanan model
    full_model_save_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), MODEL_SAVE_PATH)
    os.makedirs(os.path.dirname(full_model_save_path), exist_ok=True)
    joblib.dump(model, full_model_save_path)
    print(f"\n✅ Model ML berhasil disimpan: {MODEL_SAVE_PATH}")

# ==============================================================================
# 3. 🚀 EKSEKUSI
# ==============================================================================

if __name__ == "__main__":
    train_random_forest_predictor()