from allergies_check import check_allergans
ingredients_a = 'Peanut butter, Sugar, Vegtable Oil, Salt'
print('Check menu A...')
result_a = check_allergans(ingredients_a)
print(result_a)

print('\n' + '=' * 40 + '\n')

ingredients_b = 'Apple, Banana, Mango'
print('Check menu B...')
result_b = check_allergans(ingredients_b)
print(result_b)