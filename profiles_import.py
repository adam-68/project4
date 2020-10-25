import json
import win32clipboard


def convert_to_dict():

    win32clipboard.OpenClipboard()
    profiles = win32clipboard.GetClipboardData().split("\r\n")
    win32clipboard.CloseClipboard()
    profiles_json = []

    for profile in profiles:
        row = profile.split("\t")
        try:
            curr_profile = {'first_name': row[0].strip(),
                            'last_name': row[1].strip(),
                            'email': row[2].strip(),
                            'phone': row[3].strip(),
                            'street': row[4].strip(),
                            'house_number': row[5].strip(),
                            'post_code': row[6].strip(),
                            'city': row[7].strip(),
                            # "card_holder": row[8].strip(),
                            # "card_number": row[9].strip(),
                            # "exp_month": row[10].strip(),
                            # "exp_year": row[11].strip(),
                            # "cvv": row[12].strip()
                            }
            profiles_json.append(curr_profile)
        except Exception as error:
            print(f"Error with importing profiles {error}")
            return

    with open("USER_INPUT_DATA/profiles.json", "w") as file:
        json.dump(profiles_json, file)


convert_to_dict()
