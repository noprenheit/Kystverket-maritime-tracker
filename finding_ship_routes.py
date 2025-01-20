import pandas as pd

input_file = 'seilas_cleaned.csv'
output_file = 'ship_routes.csv'

data = pd.read_csv(input_file, delimiter=';')

columns_to_extract = [
    'fartoynavn',
    'avgangshavn_navn',
    'ankomsthavn_navn',
    'etd_estimert_avgangstidspunkt',
    'ankomsttidspunkt'
]

extracted_data = data[columns_to_extract]


extracted_data.to_csv(output_file, index=False)
print(f"Data saved to {output_file}")