import warnings
from datetime import datetime
import io

import msoffcrypto
import openpyxl
from msoffcrypto.exceptions import InvalidKeyError, DecryptionError

warnings.filterwarnings("ignore", category=UserWarning, message="Workbook contains no default style")

def parse_amount(amt):
    """Convert Indonesian currency format (e.g., '3.246.470,00') to float."""
    if not amt or amt.strip() == '':
        return 0.0
    return float(amt.replace('.', '').replace(',', '.'))

def open_excel(filename, password):
    decrypted_buffer = io.BytesIO()
    try:
        with open(filename, "rb") as file:
            office_file = msoffcrypto.OfficeFile(file)
            office_file.load_key(password=password)
            office_file.decrypt(decrypted_buffer)
        print("Password is correct!")
        return decrypted_buffer
    except InvalidKeyError:
        print("Incorrect password provided.")
        return None
    except DecryptionError:
        print("Decryption failed (possibly corrupted file or wrong encryption method).")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def parse_excel_data(decrypted_buffer):
    wb = openpyxl.load_workbook(decrypted_buffer)
    sheet = wb['e-Statement']

    transactions = []

    # Iterate through rows
    for row in sheet.iter_rows(min_row=1):
        # Check if the row contains a transaction number (e.g., "1", "2", etc.)
        # print([cell.value for cell in row])  # Debugging line to check row values
        if row[0].value is not None and isinstance(row[0].value, float):
            # Extract data from columns
            date_str = row[4].value.strip()
            description = row[7].value.strip() if row[7].value else ''  # Column G: Description
            incoming = row[15].value.strip() if row[15].value else ''  # Column O: Incoming
            outgoing = row[18].value.strip() if row[18].value else ''  # Column S: Outgoing
            balance = row[21].value.strip() if row[21].value else ''  # Column V: Balance

            # Extract time from the next row
            next_row = sheet[row[0].row + 1]
            time_str = next_row[4].value.split()[0] if next_row[
                4].value else '00:00:00'  # Column D: Time (e.g., "20:58:58 WIB")

            # Combine date and time into a datetime object
            datetime_str = f"{date_str} {time_str}"
            datetime_obj = datetime.strptime(datetime_str, '%d %b %Y %H:%M:%S')

            # Process amounts
            incoming_amount = parse_amount(incoming)
            outgoing_amount = parse_amount(outgoing)
            balance_amount = parse_amount(balance)

            # Store transaction
            transactions.append({
                'datetime': datetime_obj,
                'description': description,
                'incoming': incoming_amount,
                'outgoing': outgoing_amount,
                'balance': balance_amount
            })

    return {
        "period": sheet.cell(row=6, column=14).value,
        "transactions": transactions
    }