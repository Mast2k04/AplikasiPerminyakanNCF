import pandas as pd
import numpy as np

def hitung_produksi(cadangan_total, produksi_manual, decline_rate, jangka_waktu):
    # Menghitung produksi dengan kombinasi input manual dan exponetial decline, serta validasi cadangan reservoir
    produksi = []
    kumulatif = 0
    warning_cadangan = False
    
    for i in range(jangka_waktu):
        if i < len(produksi_manual):
            prod_tahun_ini = produksi_manual[i]
        else:
            prod_tahun_ini = produksi[-1] * (1 - decline_rate)
            
        if kumulatif + prod_tahun_ini > cadangan_total:
            prod_tahun_ini = max(0, cadangan_total - kumulatif)
            warning_cadangan = True
            
        produksi.append(round(prod_tahun_ini, 2))
        kumulatif += prod_tahun_ini
        
    return produksi, warning_cadangan, kumulatif

def hitung_opex(opex_dasar, durasi_flat, eskalasi_rate, jangka_waktu):
    #Menghitung biaya Opex dengan periode flat di awal, lalu eskalasi
    arr_opex = []
    opex_berjalan = opex_dasar
    
    for i in range(jangka_waktu):
        if i < durasi_flat:
            arr_opex.append(round(opex_dasar, 2))
        else:
            opex_berjalan = opex_berjalan * (1 + eskalasi_rate)
            arr_opex.append(round(opex_berjalan, 2))
            
    return arr_opex

def hitung_depresiasi(metode, investasi_capital, umur_depresiasi, jangka_waktu):
    #Hanya investasi Capital yang didpresiasikan sesuai metode
    depresiasi = []
    if metode == "Straight Line":
        nilai_dep = investasi_capital / umur_depresiasi
        depresiasi = [round(nilai_dep, 2) if i < umur_depresiasi else 0 for i in range(jangka_waktu)]
        
    elif metode == "Double Declining Balance":
        rate = 2 / umur_depresiasi
        book_value = investasi_capital
        for i in range(jangka_waktu):
            if i < umur_depresiasi:
                dep = book_value * rate
                depresiasi.append(round(dep, 2))
                book_value -= dep
            else:
                depresiasi.append(0)
    return depresiasi

def hitung_cashflow_makro(jangka_waktu, produksi, harga_minyak, capital, non_capital, arr_opex, arr_depresiasi, pajak_persen):
    # Baris Tahun 0 (Arus kas modal keluar)
    # Pemisahan kolom NFC tahunan dan NFC kumulatif (Undiscounted)
    investasi_awal = capital + non_capital
    data_tahun_0 = {
        "Tahun": 0, "Produksi (Mbbl)": 0.0, "Income ($M)": 0.0, 
        "Capital ($M)": capital, "Investasi Non Capital ($M)": non_capital,
        "Opex ($M)": 0.0, "Di ($M)": 0.0, "Taxable Income ($M)": 0.0, 
        "Tax ($M)": 0.0, "NCF ($M)": -float(investasi_awal), "NCF Undiscounted ($M)": -float(investasi_awal)
    }
    
    rows = [data_tahun_0]
    running_total_ncf = -float(investasi_awal)
    
    for i in range(jangka_waktu):
        prod = produksi[i]
        income = prod * harga_minyak
        opex_thn = arr_opex[i]
        di_thn = arr_depresiasi[i]
        
        taxable_income = max(0.0, income - opex_thn - di_thn)
        tax = taxable_income * (pajak_persen / 100)
        
        # NCF per tahun berjalan (Income - Opex - Tax)
        ncf_tahunan = income - opex_thn - tax
        
        # NCF Undiscounted Kumulatif (Running Total akumulatif dari Tahun 0)
        running_total_ncf += ncf_tahunan
        
        rows.append({
            "Tahun": i + 1,
            "Produksi (Mbbl)": round(prod, 2),
            "Income ($M)": round(income, 2),
            "Capital ($M)": 0.0,
            "Investasi Non Capital ($M)": 0.0,
            "Opex ($M)": round(opex_thn, 2),
            "Di ($M)": round(di_thn, 2),
            "Taxable Income ($M)": round(taxable_income, 2),
            "Tax ($M)": round(tax, 2),
            "NCF ($M)": round(ncf_tahunan, 2),
            "NCF Undiscounted ($M)": round(running_total_ncf, 2)
        })
        
    df = pd.DataFrame(rows)
    df.set_index("Tahun", inplace=True)
    return df