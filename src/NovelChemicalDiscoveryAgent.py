import pandas as pd
from dotenv import load_dotenv
import os
from google import genai
from typing import Dict, Any, Optional
import joblib 
from rdkit import Chem
from rdkit.Chem import Descriptors, MolToInchi, InchiToInchiKey, Draw, AllChem
import uuid 

load_dotenv()

# --- Konfigurasi Global Path ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
# Model berada di folder yang sama (/src)
MODEL_PATH = os.path.join(BASE_DIR, 'chemical_predictor_model_rf.pkl') 
# Results folder berada di root proyek (naik satu level dari /src)
RESULTS_DIR = os.path.join(os.path.dirname(BASE_DIR), 'results') 

INPUT_FEATURES = ['Solubility', 'Viscosity_cP', 'ThermalStability_Score', 'BoilingPoint_C']
OUTPUT_TARGETS = ['MolWeight', 'ExactMass', 'HBondDonors', 'HBondAcceptors', 'TPSA', 'LogP', 'RotatableBonds']
SMILES_COL = 'SMILES'

os.makedirs(RESULTS_DIR, exist_ok=True)

class NovelChemicalDiscoveryAgent:
    def __init__(self):
        self.OUTPUT_TARGETS = OUTPUT_TARGETS
        self.model_name = 'gemini-2.5-flash'
        self.RESULTS_DIR = RESULTS_DIR 

        self.predictor = self._load_model(MODEL_PATH) 
        self.client = self._init_gemini_client()

    def _load_model(self, path: str) -> Optional[Any]:
        """Memuat model ML untuk fungsi fitness."""
        try:
            model = joblib.load(path)
            print("INFO: Model ML untuk Fitness berhasil dimuat.")
            return model
        except FileNotFoundError:
            print(f"ERROR: Model ML tidak ditemukan di {path}. Pastikan 'model_training.py' sudah dijalankan.")
            return None
    
    def _init_gemini_client(self) -> Optional[genai.Client]:
        """Inisialisasi Gemini Client."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key: return None
        try:
            client = genai.Client(api_key=api_key)
            print("INFO: Gemini Client berhasil diinisialisasi.")
            return client
        except Exception as e:
            print(f"ERROR: Gagal inisialisasi Gemini Client: {e}")
            return None

    def _calculate_rdkit_properties(self, mol: Chem.Mol) -> Dict[str, float]:
        """Menghitung properti numerik RDKit."""
        if mol is None: return {prop: 0.0 for prop in self.OUTPUT_TARGETS}
        properties = {
            'MolWeight': Descriptors.MolWt(mol), 'ExactMass': Descriptors.ExactMolWt(mol),
            'HBondDonors': Descriptors.NumHDonors(mol), 'HBondAcceptors': Descriptors.NumHAcceptors(mol),
            'TPSA': Descriptors.TPSA(mol), 'LogP': Descriptors.MolLogP(mol),
            'RotatableBonds': Descriptors.NumRotatableBonds(mol),
        }
        return properties

    def _run_genetic_algorithm(self, criteria: Dict[str, float]) -> str:
        """[Placeholder GA] Mengembalikan SMILES yang valid."""
        if criteria['Solubility'] > 0.9:
            return "CCOc1ccc(C(=O)NCCS)cc1" 
        else:
            return "CC(=O)c1cc(N)cc(C(F)(F)F)c1"

    def generate_iupac_name(self, smiles: str) -> str:
        """Menggunakan Gemini untuk mendapatkan Nama IUPAC."""
        if self.client is None or smiles in ("N/A", None): return smiles
        prompt = f"Berikan **hanya** Nama IUPAC formal untuk struktur SMILES: {smiles}. Jangan berikan teks lain."
        try:
            response = self.client.models.generate_content(model=self.model_name, contents=prompt)
            return response.text.strip()
        except Exception as e: return smiles 

    def _get_chemical_identifiers(self, smiles: str, iupac_name: str) -> Dict[str, str]:
        """Menghitung InChI/InChIKey dan memetakan Nama IUPAC."""
        identifiers = {"SMILES": smiles, "IUPAC": iupac_name, "InChI": "N/A", "InChIKey": "N/A"}
        if smiles in ("N/A", None): return identifiers
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol:
                inchi = MolToInchi(mol)
                inchikey = InchiToInchiKey(inchi)
                identifiers["InChI"] = inchi
                identifiers["InChIKey"] = inchikey
        except Exception as e: pass
        return identifiers

    def _generate_visualizations(self, mol: Chem.Mol) -> Dict[str, str]:
        """Menghasilkan gambar 2D dan file 3D .mol, mengembalikan path relatif."""
        paths = {"Structure_2D_Path": None, "Structure_3D_Path": None}
        if mol is None: return paths
        file_id = str(uuid.uuid4())
        
        # 1. Gambar 2D
        try:
            path_2d_relative = f"/results/{file_id}_2d.png"
            path_2d_absolute = os.path.join(self.RESULTS_DIR, f"{file_id}_2d.png")
            Draw.MolToFile(mol, path_2d_absolute, size=(300, 300))
            paths["Structure_2D_Path"] = path_2d_relative
        except Exception as e: pass

        # 2. File 3D (.mol)
        try:
            mol_h = Chem.AddHs(mol)
            AllChem.EmbedMolecule(mol_h, AllChem.ETKDG()) 
            path_3d_relative = f"/results/{file_id}_3d.mol"
            path_3d_absolute = os.path.join(self.RESULTS_DIR, f"{file_id}_3d.mol")
            Chem.MolToMolFile(mol_h, path_3d_absolute)
            paths["Structure_3D_Path"] = path_3d_relative
        except Exception as e: pass

        return paths

    def predict_and_lookup(self, user_criteria: Dict[str, float]) -> Dict[str, Any]:
        """Alur Generatif Utama."""
        if self.predictor is None: return {"recommended_compound": {"SMILES": "N/A", "Properties": {}, "Structure_2D_Path": None, "Structure_3D_Path": None}}

        new_smiles = self._run_genetic_algorithm(user_criteria)
        mol = Chem.MolFromSmiles(new_smiles)
        
        if mol is None: return {"recommended_compound": {"SMILES": "N/A", "Properties": {}, "Structure_2D_Path": None, "Structure_3D_Path": None}}
            
        predicted_props = self._calculate_rdkit_properties(mol)
        iupac_name = self.generate_iupac_name(new_smiles)
        chemical_ids = self._get_chemical_identifiers(new_smiles, iupac_name) 
        viz_paths = self._generate_visualizations(mol)

        all_properties = {**predicted_props, **chemical_ids} 
        
        return {
            "recommended_compound": {
                "SMILES": new_smiles,
                "Properties": all_properties,
                "Structure_2D_Path": viz_paths["Structure_2D_Path"],
                "Structure_3D_Path": viz_paths["Structure_3D_Path"],
            }
        }
    
    def get_justification(self, criteria: Dict[str, float], compound_data: Dict[str, Any]) -> str:
        """Menghasilkan justifikasi menggunakan Gemini API."""
        if self.client is None: return "Justifikasi: Layanan AI tidak tersedia."
        
        compound = compound_data['recommended_compound']
        predicted_props = compound['Properties']
        smiles = compound['SMILES']
        iupac_name = predicted_props.get('IUPAC', smiles)

        prompt = (
            f"Berikan justifikasi singkat (maksimal 100 kata) mengapa senyawa: '{iupac_name}' "
            f"adalah kandidat yang direkomendasikan untuk kriteria Petrokimia:\n"
            f"Kriteria Pengguna: {criteria}\n"
            f"Properti Terprediksi Utama: MolWeight={predicted_props.get('MolWeight', 'N/A')}, LogP={predicted_props.get('LogP', 'N/A')}, TPSA={predicted_props.get('TPSA', 'N/A')}"
        )

        try:
            response = self.client.models.generate_content(model=self.model_name, contents=prompt)
            return response.text
        except Exception as e:
            return f"Justifikasi Gagal: {e}"