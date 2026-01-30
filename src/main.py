import os
import pandas as pd
from src.services.ans_client import AnsDataClient
from src.services.zip_processor import ZipProcessor

def main():
    print("--- STARTING ETL PIPELINE ---")
    
    # Download 
    client = AnsDataClient()
    client.download_last_3_quarters()
    
    # Processing
    processor = ZipProcessor()
    
    # Get list of downloaded files (files ending in .zip)
    downloaded_files = [
        os.path.join(client.download_dir, f) 
        for f in os.listdir(client.download_dir) 
        if f.endswith('.zip')
    ]
    
    all_data = []
    
    print(f"\n--- PROCESSING {len(downloaded_files)} FILES ---")
    
    for zip_file in downloaded_files:
        print(f"Processing: {zip_file}")
        
        # The 'process_zip' method finds the CSV inside automatically
        df = processor.process_zip(zip_file)
        
        if df is not None and not df.empty:
            # Add a column to know which file this came from
            df['SOURCE_FILE'] = os.path.basename(zip_file)
            all_data.append(df)
    
    # Aggregation (Merging 3 quarters)
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        print("\n--- FINAL RESULT ---")
        print(f"Total Rows Processed: {len(final_df)}")
        print("Sample Data:")
        print(final_df[['DATA', 'DESCRICAO', 'VL_SALDO_FINAL', 'SOURCE_FILE']].head())
    else:
        print("No data processed.")

if __name__ == "__main__":
    main()