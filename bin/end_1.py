import random

def make_token(integer):
    letters = [
        'a', 'b', 'c', 'd', 'e', 'f',
        'g', 'h', 'i', 'j', 'k', 'l',
        'm', 'n', 'o', 'p', 'q', 'r',
        's', 't', 'u', 'v', 'w', 'x',
        'y', 'z', 'A', 'B', 'C', 'D',
        'E', 'F', 'G', 'H', 'I', 'J',
        'K', 'L', 'M', 'N', 'O', 'P',
        'Q', 'R', 'S', 'T', 'U', 'V',
        'W', 'X', 'Y', 'Z'
    ]
    token = ''
    for i, l in enumerate(str(integer)):
        if random.randrange(1,4) == 3:
            token += random.choice(letters)+l
        else:
            token += l
    return token

def change_token_for_int(integer_or_token):
    
    token = False
    new_in_integer_str = ''
    for i in range(len(str(integer_or_token))):
        # print(i)
        try:
            x = int(str(integer_or_token)[i])
            new_in_integer_str += f'{str(integer_or_token)[i]}'
        except Exception as e:
            # print(f'Ocurrent Error: {e} dla {i}')
            token = True
    # print(token, new_in_integer_str)
    if token:
        try: export=int(new_in_integer_str)
        except: export= 0
        return export
    else:
        try: 
            integer = integer_or_token
            export=int(integer)
        except: 
            export= 0
        
        return export

def encode_string(s, pin=None, auth_from=None, direct_to=None):

    if pin is None:
        pin = f"{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}"
    if len(str(pin)) != 4:
        return {
        "error": False,
        "EI":0,
        "CS":'0001',
        "TK": 'a0B'
            }
    correct_pin = str(pin)
    if auth_from == None: auth_from = 'unknow Phone Frome'
    if direct_to == None: direct_to = 'unknow Phone To'
    s = f'#{s}-super-tag-xpcs-PIN-footerSepparatorDotter-{correct_pin}-footerSepparatorTag-FROM-footerSepparatorDotter-{auth_from}-footerSepparatorTag-TO-footerSepparatorDotter-{direct_to}-footerSepparatorTag-LOST-footerSepparatorDotter-wtp01234#'
    
    ascii_codes = [ord(char) for char in s]
    
    divider = random.randint(3, 9)
    
    modified_codes = []

    for code in ascii_codes:
        if len(str(code)) == 1:
            code = f'{divider}{divider}{code}'
        elif len(str(code)) == 2:
            code = f'{divider}{code}'
        else:
            code = str(code)
        modified_codes.append(code)

    long_string = ''.join(modified_codes)
    
    int_code = int(long_string) // divider
    
    encoded_string = str(int_code) + str(divider)
    
    encoded_integer = int(encoded_string)
    
    return {
        "succes": True,
        "EI":encoded_integer,
        "CS":correct_pin,
        "TK": make_token(encoded_integer)
            }
def encode_string_old_ver(s, pin=None, phone_from=None, phone_to=None):

    if pin is None:
        pin = f"{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}"
    if len(str(pin)) != 4:
        return {
        "error": False,
        "EI":0,
        "CS":'0001',
        "TK": 'a0B'
            }
    correct_pin = str(pin)
    if phone_from == None: phone_from = 'unknow Phone Frome'
    if phone_to == None: phone_to = 'unknow Phone To'
    s = f'#{s}-super-tag-xpcs-PIN-footerSepparatorDotter-{correct_pin}-footerSepparatorTag-FROM-footerSepparatorDotter-{phone_from}-footerSepparatorTag-TO-footerSepparatorDotter-{phone_to}-footerSepparatorTag-LOST-footerSepparatorDotter-wtp01234#'
    # print(f"String with delimiters: {s}")
    
    ascii_codes = [ord(char) for char in s]
    # print(f"ASCII codes: {ascii_codes}")
    
    divider = random.randint(3, 9)
    # print(f"Divider: {divider}")
    
    modified_codes = []

    for code in ascii_codes:
        if len(str(code)) == 1:
            code = f'{divider}{divider}{code}'
        elif len(str(code)) == 2:
            code = f'{divider}{code}'
        else:
            code = str(code)
        modified_codes.append(code)

    long_string = ''.join(modified_codes)
    # print(f"Long string: {long_string}")
    
    int_code = int(long_string) // divider
    # print(f"Integer code divided: {int_code}")
    
    encoded_string = str(int_code) + str(divider)
    # print(f"Encoded string with divider: {encoded_string}")
    
    encoded_integer = int(encoded_string)
    # print(f"Encoded integer: {encoded_integer}")
    
    return {
        "succes": True,
        "EI":encoded_integer,
        "CS":correct_pin,
        "TK": make_token(encoded_integer)
            }

def decode_integer(encoded_integer, pin):
    encoded_integer = change_token_for_int(encoded_integer)
    pin = str(pin)
    if encoded_integer == 0 or len(pin) != 4:
        return {'error':'Brak autoryzacji!'}
    
    encoded_string = str(encoded_integer)
    # print(f"Encoded string from integer: {encoded_string}")
    
    divider = int(encoded_string[-1])
    encoded_string = encoded_string[:-1]
    # print(f"Divider: {divider}")
    # print(f"Encoded string without divider: {encoded_string}")

    int_code = int(encoded_string) * divider
    # print(f"Integer code multiplied: {int_code}")
    
    long_string = str(int_code)
    # print(f"Long string: {long_string}")
    
    modified_codes = []
    a = 0
    for i in range(len(long_string)):
        if a == 3:
            tree_part_str = long_string[i:i+3]
            if tree_part_str.startswith(str(divider)):
                tree_part_str = tree_part_str[1:]
            # if tree_part_str.startswith(str(divider)) and str(tree_part_str)[1] != str(divider):
            #     tree_part_str = tree_part_str[1:]
            # elif tree_part_str.startswith(str(divider)) and str(tree_part_str)[1] == str(divider):
            #     tree_part_str = tree_part_str[2:]
            modified_codes.append(tree_part_str)
            a = 0
        a += 1
    # print(f"Modified codes: {modified_codes}")
    
    ascii_codes = [int(a) for a in modified_codes]
    # print(f"ASCII codes: {ascii_codes}")
    
    decoded_string_with_pin = ''.join(chr(code) for code in ascii_codes)
    # Poprawne usuwanie delimiterów
    if decoded_string_with_pin[0] == '#' and decoded_string_with_pin[-1] == '#':
        decoded_string_with_pin = decoded_string[1:-1]
    # print(f"Decoded string with pin: {decoded_string_with_pin}")
    # decoded_string = decoded_string_with_pin[:-5]
    # decoded_pin = decoded_string_with_pin[-5:-1]

    try: decoded_string = decoded_string_with_pin[:-1].split('-super-tag-xpcs-')[0]
    except Exception as e: 
        # print(e)
        return {'error':'Brak autoryzacji!'}
    try: decoded_footer_list = decoded_string_with_pin[:-1].split('-super-tag-xpcs-')[1].split('-footerSepparatorTag-')
    except Exception as e: 
        # print(e)
        return {'error':'Brak autoryzacji!'}
    decoded_footer_dict = {}
    for item in decoded_footer_list:
        k, v = item.split('-footerSepparatorDotter-')
        decoded_footer_dict[k] = v
    
    # print(f"Decoded decoded_footer_dict: {decoded_footer_dict}")
    if 'PIN' in decoded_footer_dict:
        decoded_pin = decoded_footer_dict['PIN']
    else:
        return {'error':'Brak autoryzacji!'}
    
    # print(f"Decoded pin: {pin, decoded_pin}")
    if len(pin) != 4:
        return {'error':'Brak autoryzacji!'}
    if pin != decoded_pin:
        return {'error':'Brak autoryzacji!'}
    print(f"PIN: {decoded_footer_dict['PIN']}")
    print(f"FROM: {decoded_footer_dict['FROM']}")
    print(f"TO: {decoded_footer_dict['TO']}")
    return {
        'success': decoded_string,
        'PIN': decoded_footer_dict['PIN'],
        'FROM': decoded_footer_dict['FROM'],
        'TO': decoded_footer_dict['TO']
        }

if __name__ == "__main__":
    while True:
        rout = input('''[e] - encode\n[d] - decode\n\n>>> ''')
        if rout == 'e':
            pin=input('czy chcesz ustawić swój pin? (t/n): ')
            if pin.startswith('t'):
                pin = input('podaj czterocyfrowy pin: ')
                print(f'pin: {pin} został zapisany')
            else:
                pin = None
            phone_from=input('Podaj swój nr whatsApp lub nacisnij <ENTER>: ')
            if phone_from=='':
                phone_from = None
                print(f'Numer telefonu: {phone_from} został zapisany')
            phone_to=input('Podaj nr whatsApp odbiorcy lub nacisnij <ENTER>: ')
            if phone_to=='':
                phone_to = None
                print(f'Numer telefonu: {phone_from} został zapisany')
            encoded = encode_string(
                input("Podaj widomość: "),
                pin=pin, phone_from=phone_from, phone_to=phone_to
                )
            print(f"Encoded:\n\nINT:\n{encoded['EI']}\n\nTOKEN:\n{encoded['TK']}\n\nPIN:\n{encoded['CS']}\n\n")
            # break
        elif rout == 'd':
            decoded = decode_integer(
                input('podaj liczbę lub token: '), input('Podaj pin: '))
            if 'success' in decoded:
                print(f"Decoded: {decoded['success']}")
            elif 'error' in decoded:
                print(f"Decoded: \n{decoded['error']}")
            # break
        else:
            print('Nieznana komenda')
