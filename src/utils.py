# utils.py

import os
from rdkit import Chem
from rdkit.Chem import Draw
from rdkit.Chem.rdmolfiles import MolToMolFile
from rdkit.Chem import AllChem

# ==============================================================================
# 1. PENANGANAN IMPOR & KONSTANTA
# ==============================================================================

# Menangani impor AllChem di sini agar kesalahan terlihat jelas saat startup
try:
    # AllChem diperlukan untuk EmbedMolecule (3D)
    import rdkit.Chem.AllChem as AllChem
    ALLCHEM_AVAILABLE = True
except ImportError:
    print("WARNING: RDKit AllChem tidak dapat diimpor. Pembuatan file 3D akan dinonaktifkan.")
    ALLCHEM_AVAILABLE = False


def _create_error_placeholder(path: str, message: str):
    """Fungsi helper untuk membuat file placeholder jika rendering gagal."""
    try:
        if os.path.exists(path):
            os.remove(path)
        with open(path, 'w') as f:
            f.write(message)
    except Exception as e:
        print(f"FATAL: Gagal membuat placeholder di {path}. {e}")


# ==============================================================================
# 2. FUNGSI VISUALISASI 2D
# ==============================================================================

def visualize_smiles(smiles: str, output_path: str):
    """
    Menghasilkan visualisasi 2D (PNG) dari SMILES yang dihasilkan.
    Menerapkan penanganan kesalahan yang kuat untuk SMILES yang tidak valid.
    """
    print(f"Mencoba membuat visualisasi 2D untuk: {smiles}")
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            print(f"ERROR: SMILES tidak valid untuk visualisasi 2D.")
            _create_error_placeholder(output_path, "SMILES TIDAK VALID")
            return

        # 2D Rendering
        Draw.MolToFile(mol, output_path, size=(220, 160), imageType='png')
        print(f"SUCCESS: File 2D berhasil dibuat: {output_path}")
        
    except Exception as e:
        print(f"ERROR: Gagal membuat visualisasi 2D untuk {smiles}: {e}")
        _create_error_placeholder(output_path, f"RENDERING GAGAL: {e}")


# ==============================================================================
# 3. FUNGSI GENERASI KOORDINAT 3D
# ==============================================================================

def generate_3d_coords(smiles: str, output_path: str):
    """
    Menghasilkan koordinat 3D dan menyimpan sebagai file .mol.
    Menerapkan penanganan kegagalan konformer yang ketat.
    """
    if not ALLCHEM_AVAILABLE:
        print("ERROR: Pembuatan 3D gagal. AllChem tidak tersedia.")
        _create_error_placeholder(output_path, "3D GAGAL: AllChem tidak termuat.")
        return
        
    print(f"Mencoba membuat konformer 3D untuk: {smiles}")
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            print(f"ERROR: SMILES tidak valid untuk pembuatan 3D.")
            _create_error_placeholder(output_path, "SMILES TIDAK VALID")
            return
            
        # 1. Tambahkan Atom Hidrogen
        mol3d = Chem.AddHs(mol)
        
        # 2. Hasilkan Konformer 3D (ETKDG v2)
        # status 0 = berhasil, selain 0 = gagal.
        status = AllChem.EmbedMolecule(mol3d, AllChem.ETKDG()) 
        
        if status == 0: 
            # Opsional: Optimasi Gaya Medan untuk stabilitas yang lebih baik
            # AllChem.MMFFOptimizeMolecule(mol3d)
            
            # 3. Simpan ke file .mol
            MolToMolFile(mol3d, output_path)
            print(f"SUCCESS: File 3D berhasil dibuat: {output_path}")
        else:
            print(f"WARNING: Gagal membuat konformer 3D stabil untuk {smiles} (Status: {status}).")
            _create_error_placeholder(output_path, f"KONFORMER GAGAL (Status: {status})")
            
    except Exception as e:
        print(f"ERROR: Kegagalan tak terduga saat membuat file 3D untuk {smiles}: {e}")
        # Bersihkan atau buat placeholder jika terjadi error
        _create_error_placeholder(output_path, f"ERROR TAK TERDUGA: {e}")