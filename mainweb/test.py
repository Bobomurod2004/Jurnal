test = "Hello, my name is [u-1061][u-1072][u-1082][u-1080]"
str_copy = test
e = [i for i in range(len(test)) if test.startswith('[', i)]

for i in e:
    if test.startswith('[u-', i):
        to_replace = test[i:test.find(']', i) + 1]
        char_dec = to_replace[3:-1]

        # Convert the Unicode code point to a character
        char = chr(int(char_dec))
        # Replace the Unicode code point with the character in the string
        str_copy = str_copy.replace(to_replace, char)

print(str_copy)
