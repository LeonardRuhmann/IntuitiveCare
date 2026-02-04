import pandas as pd
import os
import zipfile
from src import config

class DataAggregator:
    def __init__(self, output_dir=config.OUTPUT_DIR):
        self.output_dir = output_dir

    def aggregate_data(self, clean_csv_path: str):
        """
        Performs grouping and aggregation on the clean dataset.
        Metrics: Total, Std Dev, Avg per Quarter.
        """
        print(f"   [Aggregator] Loading clean data from {clean_csv_path}...")
        
        # Load data (ensure correct types)
        try:
            df = pd.read_csv(clean_csv_path, sep=config.CSV_SEP, encoding=config.CSV_ENCODING)
        except Exception as e:
            print(f"   [Error] Failed to read file {clean_csv_path}: {e}")
            return None

        # remove columns with '_y'
        cols_to_drop = [col for col in df.columns if str(col).endswith('_y')]
        if cols_to_drop:
            print(f"   [Fix] Dropping redundant columns: {cols_to_drop}")
            df.drop(columns=cols_to_drop, inplace=True)

        # rename columns with '_x'
        cols_to_rename = {col: str(col).replace('_x', '') for col in df.columns if str(col).endswith('_x')}
        if cols_to_rename:
            print(f"   [Fix] Renaming columns back to original: {cols_to_rename}")
            df.rename(columns=cols_to_rename, inplace=True)

        # Convert numeric columns if they are strings
        df['ValorDespesas'] = pd.to_numeric(df['ValorDespesas'], errors='coerce')

        # Convert Date to extract Quarters
        df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
        
        # Create a helper column 'Quarter' (e.g., "2025Q3")
        df['Quarter'] = df['DATA'].dt.to_period('Q').astype(str)

        print("   Calculating metrics by Operator/State...")


        group_keys = ['REG_ANS', 'RazaoSocial', 'UF', 'Modalidade']

        # --- PRIMARY AGGREGATION (Sum & StdDev) ---
        # Group by Company (RazaoSocial) and State (UF)
        grouped = df.groupby(group_keys)
        
        # Calculate Sum, StdDev, and Count
        summary = grouped['ValorDespesas'].agg(['sum', 'std', 'count']).reset_index()
        summary.rename(columns={
            'sum': 'Valor_total_Despesas', 
            'std': 'Desvio_padrao_Despesas',
            'count': 'Qtd_Transacoes'
        }, inplace=True)
        
        # Handle NaN in StdDev (occurs if an operator has only 1 transaction)
        summary['Desvio_padrao_Despesas'] = summary['Desvio_padrao_Despesas'].fillna(0)

        # --- QUARTERLY AVERAGE ---
        # Logic: Total Expenses / Number of Active Quarters
        # We count how many distinct quarters each operator appears in
        unique_quarters = grouped['Quarter'].nunique().reset_index(name='Qtd_Trimestres_Ativos')
        
        # Merge this count back to summary
        summary = pd.merge(summary, unique_quarters, on=group_keys)
        
        # Calculate Average
        summary['Media_Despesas_Por_Trimestre'] = summary['Valor_total_Despesas'] / summary['Qtd_Trimestres_Ativos']

        # ---  SORTING (The Trade-off) ---
        # Strategy: Sort by Total Expenses (Descending) to highlight top spenders.
        # Justification: Using Pandas optimized Quicksort (O(N log N)).
        summary = summary.sort_values(by='Valor_total_Despesas', ascending=False)

        summary.rename(columns={
            'REG_ANS': 'Registro_ANS',
            'RazaoSocial': 'Razao_Social'
        }, inplace=True)

        # Save CSV 
        csv_filename = 'despesas_agregadas.csv'
        output_csv_path = os.path.join(self.output_dir, csv_filename)

        
        # Formatting float to 2 decimal places for readability
        summary.to_csv(output_csv_path, index=False, sep=config.CSV_SEP, float_format='%.2f', encoding=config.CSV_ENCODING)
        print(f"    Saved CSV to {output_csv_path}")

        zip_filename = 'Teste_Leonardo_Ruhmann.zip'
        output_zip_path = os.path.join(self.output_dir, zip_filename)

        print(f"   Zipping to {output_zip_path}...")
        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(output_csv_path, arcname=csv_filename)
        
        print(f"   [Success] Final file created: {output_zip_path}")

        # Show Top 1 result for validation
        if not summary.empty:
            top_one = summary.iloc[0]
            print(f"   -> Top Spender: {top_one['Razao_Social']} ({top_one['UF']})")
            print(f"   -> Total: R$ {top_one['Valor_total_Despesas']:,.2f}")

        return output_zip_path