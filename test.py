import pandas as pd

x = pd.read_csv(
                r"C:\Users\Mostafa\Downloads\Telegram Desktop\Bank Melli DB1.csv",
                dtype=str,
                keep_default_na=False,
                encoding_errors='ignore'
            )
print(1)