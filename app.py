# app.py
# Kamus Halal Farmasi — Streamlit App (UI/UX Edukasi dengan Tabs)
# --------------------------------------------------------------
# Cara menjalankan:
# 1) pip install streamlit
# 2) streamlit run app.py

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Tuple

import streamlit as st


# =========================
# Konfigurasi & Konstanta
# =========================
APP_TITLE = "Kamus Halal Farmasi"
APP_SUBTITLE = "Solusi Pencarian Status Kehalalan Bahan Baku Farmasi"
DATA_FILE_DEFAULT = "data_halal.json"

STATUS_OPTIONS = ["Halal", "Syubhat", "Haram"]


# =========================
# Utilitas Data
# =========================
@st.cache_data(show_spinner=False)
def load_data(json_path: str) -> List[Dict[str, Any]]:
    """
    Memuat data kamus halal dari file JSON.

    Parameter:
        json_path: path file JSON (contoh: 'data_halal.json')

    Return:
        List of dict: daftar bahan beserta atributnya

    Catatan:
        Menggunakan st.cache_data agar loading cepat (tidak baca file berulang).
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(
            f"File data tidak ditemukan: {json_path}\n"
            f"Pastikan file '{os.path.basename(json_path)}' berada di folder yang sama dengan app.py "
            f"atau sesuaikan path-nya."
        )

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Struktur JSON tidak valid. Root JSON harus berupa list/array.")

    # Validasi minimal key agar tidak error saat render UI
    required_keys = {
        "Nama_Bahan",
        "Kategori",
        "E_Number",
        "Status",
        "Titik_Kritis",
        "Substitusi_Halal",
        "Referensi",
    }
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Item indeks {i} bukan object/dict.")
        missing = required_keys - set(item.keys())
        if missing:
            raise ValueError(f"Item indeks {i} kehilangan key: {sorted(list(missing))}")

    return data


def normalize(text: str) -> str:
    """
    Normalisasi string untuk pencarian:
    - Lowercase
    - Strip whitespace
    """
    return (text or "").strip().lower()


def build_filters(data: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
    """
    Menghasilkan opsi filter Status dan Kategori dari data.
    """
    statuses = sorted({str(d.get("Status", "")).strip() for d in data if d.get("Status")})
    categories = sorted({str(d.get("Kategori", "")).strip() for d in data if d.get("Kategori")})

    # Pastikan urutan status konsisten (Halal, Syubhat, Haram) bila ada
    statuses_ordered = [s for s in STATUS_OPTIONS if s in statuses] + [s for s in statuses if s not in STATUS_OPTIONS]
    return statuses_ordered, categories


def apply_search_and_filters(
    data: List[Dict[str, Any]],
    query: str,
    status_filter: List[str],
    category_filter: List[str],
) -> List[Dict[str, Any]]:
    """
    Menerapkan pencarian (Nama_Bahan / E_Number) dan filter (Status, Kategori).

    Parameter:
        data: data bahan
        query: input search bar
        status_filter: list status yang dipilih
        category_filter: list kategori yang dipilih

    Return:
        list data hasil filter
    """
    q = normalize(query)

    def match_query(item: Dict[str, Any]) -> bool:
        if not q:
            return True
        nama = normalize(str(item.get("Nama_Bahan", "")))
        en = normalize(str(item.get("E_Number", "")))
        return (q in nama) or (q in en)

    def match_status(item: Dict[str, Any]) -> bool:
        if not status_filter:
            return True
        return str(item.get("Status", "")).strip() in status_filter

    def match_category(item: Dict[str, Any]) -> bool:
        if not category_filter:
            return True
        return str(item.get("Kategori", "")).strip() in category_filter

    filtered = [d for d in data if match_query(d) and match_status(d) and match_category(d)]

    # Urutkan agar rapi: Status (Halal->Syubhat->Haram), lalu Nama
    status_rank = {s: i for i, s in enumerate(STATUS_OPTIONS)}
    filtered.sort(
        key=lambda x: (
            status_rank.get(str(x.get("Status", "")).strip(), 999),
            normalize(str(x.get("Nama_Bahan", ""))),
        )
    )
    return filtered


# =========================
# UI Helpers
# =========================
def status_badge(status: str) -> str:
    """
    Membuat badge status dengan warna berbeda menggunakan HTML.
    """
    s = (status or "").strip()
    color = {
        "Halal": "#16a34a",   # hijau
        "Syubhat": "#f59e0b", # kuning
        "Haram": "#dc2626",   # merah
    }.get(s, "#64748b")      # abu-abu default

    return f"""
        <span style="
            display:inline-block;
            padding:0.25rem 0.6rem;
            border-radius:999px;
            font-size:0.85rem;
            font-weight:600;
            color:white;
            background:{color};
            vertical-align:middle;">
            {s}
        </span>
    """


def render_item_card(item: Dict[str, Any]) -> None:
    """
    Render satu item bahan dalam bentuk expander agar rapi.
    """
    nama = str(item.get("Nama_Bahan", "")).strip()
    kategori = str(item.get("Kategori", "")).strip()
    e_number = str(item.get("E_Number", "")).strip()
    status = str(item.get("Status", "")).strip()

    meta = []
    if kategori:
        meta.append(f"Kategori: {kategori}")
    if e_number:
        meta.append(f"E-Number: {e_number}")

    header_line = " • ".join(meta) if meta else ""

    with st.expander(f"{nama}", expanded=False):
        # Header ringkas (nama + badge)
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; justify-content:space-between; gap:12px;">
                <div style="font-size:1.05rem; font-weight:700;">{nama}</div>
                <div>{status_badge(status)}</div>
            </div>
            <div style="margin-top:6px; color:#475569; font-size:0.95rem;">
                {header_line}
            </div>
            <hr style="margin: 12px 0;"/>
            """,
            unsafe_allow_html=True,
        )

        # Detail isi
        st.markdown("**Titik Kritis**")
        st.write(item.get("Titik_Kritis", ""))

        st.markdown("**Substitusi Halal**")
        st.write(item.get("Substitusi_Halal", ""))

        st.markdown("**Referensi**")
        st.write(item.get("Referensi", ""))


def render_tab_edukasi() -> None:
    """
    Menampilkan konten edukasi pada Tab 2.
    """
    st.markdown("## 📚 Edukasi Titik Kritis")
    st.caption("Ringkasan edukatif untuk membantu memahami aspek halal pada bahan obat.")

    st.info(
        """
**Apa itu Titik Kritis Bahan Obat?**  
*Titik kritis* adalah bagian/parameter dalam bahan atau proses pembuatan obat yang berpotensi menentukan status halal, 
misalnya karena melibatkan sumber **hewani**, penggunaan **bahan penolong proses** tertentu, atau risiko **kontaminasi silang**.

Contoh titik kritis yang sering muncul:
- **Asal bahan**: hewani (sapi/ikan/babi), nabati, atau sintetis.
- **Penyembelihan**: khusus bahan turunan hewan halal yang harus sesuai syariat.
- **Bahan penolong proses**: enzim, media fermentasi, antifoam, pelarut, karbon aktif, dll.
- **Fasilitas & rantai pasok**: segregasi lini produksi, kebersihan, dan potensi cross-contamination.
        """.strip()
    )

    st.markdown("---")

    st.markdown("### 🧾 Alur Sertifikasi Halal (Ringkas)")
    st.markdown(
        """
Berikut gambaran umum alur sertifikasi halal (disederhanakan untuk edukasi):

1. **Komitmen & Persiapan Internal**
   - Menetapkan kebijakan halal, tim halal, dan prosedur (termasuk kontrol pemasok & bahan).

2. **Pengumpulan Data Bahan dan Proses**
   - Daftar bahan baku/eksipien/zat aditif, dokumen spesifikasi, CoA, serta ketertelusuran sumber.

3. **Analisis Titik Kritis**
   - Identifikasi bahan dan proses yang berisiko (hewani/fermentasi/alkohol proses/oleokimia, dll).

4. **Dokumentasi & Implementasi Sistem Jaminan Produk Halal**
   - SOP penerimaan bahan, penyimpanan, produksi, pembersihan, dan penanganan ketidaksesuaian.

5. **Audit/Verifikasi**
   - Pemeriksaan dokumen dan/atau audit lapangan oleh pihak berwenang/lembaga terkait.

6. **Keputusan & Penerbitan Sertifikat**
   - Jika memenuhi ketentuan, sertifikat halal diterbitkan dan dilakukan pemeliharaan berkelanjutan.
        """.strip()
    )

    st.success("Catatan: Untuk implementasi resmi, gunakan pedoman dan regulasi terbaru dari otoritas terkait (BPJPH/MUI).")


def render_tab_tentang() -> None:
    """
    Menampilkan konten Tentang Aplikasi pada Tab 3.
    """
    st.markdown("## ℹ️ Tentang Aplikasi")
    st.markdown(
        """
Aplikasi **Kamus Halal Farmasi** adalah aplikasi web sederhana berbasis **Python Streamlit** yang membantu pengguna:
- Mencari **status kehalalan** bahan baku farmasi/eksipien/zat aditif.
- Memahami **titik kritis** (critical points) yang membuat suatu bahan berstatus halal, haram, atau syubhat.
- Mendapat saran **substitusi halal** yang relevan untuk kebutuhan formulasi.

**Pembuat Aplikasi**  
Dosen CPNS Prodi **Manajemen Mutu Halal**.

**Tujuan Aktualisasi**  
Mendukung peningkatan literasi halal di bidang farmasi melalui media digital yang:
- Mudah digunakan (pencarian & filter),
- Informatif (penjelasan titik kritis),
- Praktis (rekomendasi substitusi halal),
- Dapat dikembangkan menjadi basis data internal/edukasi untuk pembelajaran dan layanan publik.
        """.strip()
    )

    st.markdown("---")
    st.caption("Versi: Prototype edukasi • Dibangun dengan Streamlit")


# =========================
# Main App
# =========================
def main() -> None:
    """
    Entry point aplikasi Streamlit.
    Mengatur layout, memuat data, dan menampilkan 3 tab:
    1) Kamus Bahan (pencarian & hasil)
    2) Edukasi Titik Kritis
    3) Tentang Aplikasi
    """
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🧪",
        layout="wide",
    )

    # Header global aplikasi
    st.markdown(f"# 🧪 {APP_TITLE}")
    st.markdown(f"### {APP_SUBTITLE}")
    st.markdown(
        "Aplikasi ini membantu pencarian bahan berdasarkan **Nama Bahan** atau **E-Number**, "
        "serta menyediakan ringkasan edukasi titik kritis dan informasi tujuan aktualisasi."
    )
    st.divider()

    # Sidebar: pemilihan file data + filter (filter dipakai pada Tab 1)
    st.sidebar.header("⚙️ Data & Filter")

    json_path = st.sidebar.text_input(
        "Path file JSON",
        value=DATA_FILE_DEFAULT,
        help="Default: data_halal.json (letakkan di folder yang sama dengan app.py).",
    )

    # Load data (dipakai di Tab 1)
    try:
        data = load_data(json_path)
    except Exception as e:
        st.error("Gagal memuat data JSON.")
        st.exception(e)
        st.stop()

    statuses, categories = build_filters(data)

    st.sidebar.subheader("Filter Status")
    selected_status = st.sidebar.multiselect(
        "Pilih Status",
        options=statuses,
        default=statuses,
    )

    st.sidebar.subheader("Filter Kategori")
    selected_categories = st.sidebar.multiselect(
        "Pilih Kategori",
        options=categories,
        default=categories,
    )

    st.sidebar.divider()
    st.sidebar.caption(f"Total data: **{len(data)}** bahan")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📖 Kamus Bahan", "📚 Edukasi Titik Kritis", "ℹ️ Tentang Aplikasi"])

    # =========================
    # Tab 1: Kamus Bahan
    # =========================
    with tab1:
        st.markdown("## 📖 Kamus Bahan")
        st.caption("Cari bahan berdasarkan Nama Bahan atau E-Number, lalu buka hasil untuk melihat detailnya.")

        # Search bar (dipindahkan ke Tab 1)
        query = st.text_input(
            "🔎 Pencarian (Nama Bahan atau E-Number)",
            placeholder="Contoh: 'Magnesium stearat' atau 'E433'...",
        )

        results = apply_search_and_filters(
            data=data,
            query=query,
            status_filter=selected_status,
            category_filter=selected_categories,
        )

        # Ringkasan hasil
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            st.metric("Hasil ditemukan", len(results))
        with col2:
            st.metric("Total data", len(data))
        with col3:
            if query.strip():
                st.info(f"Menampilkan hasil untuk pencarian: **{query.strip()}**")
            else:
                st.info("Menampilkan hasil berdasarkan filter yang dipilih di sidebar.")

        st.divider()

        if not results:
            st.warning("Tidak ada hasil yang cocok. Coba ubah kata kunci atau filter di sidebar.")
        else:
            # Tampilan hasil dalam expander (cards), 2 kolom agar rapi
            left, right = st.columns(2, gap="large")
            for idx, item in enumerate(results):
                with (left if idx % 2 == 0 else right):
                    render_item_card(item)

        st.divider()
        st.caption("Tips: Untuk audit internal, pastikan data sumber bahan & pemasok terdokumentasi dengan baik.")

    # =========================
    # Tab 2: Edukasi Titik Kritis
    # =========================
    with tab2:
        render_tab_edukasi()

    # =========================
    # Tab 3: Tentang Aplikasi
    # =========================
    with tab3:
        render_tab_tentang()

    st.divider()
    st.caption("© Kamus Halal Farmasi — Prototype Streamlit (CPNS Aktualisasi)")


if __name__ == "__main__":
    main()