from utils.locale import init_locale_manager

lm = init_locale_manager()
print(f'Loaded languages: {list(lm.locales.keys())}')
print(f'Total: {len(lm.locales)} locales')

# Test EN
test_en = lm.get_text('main_menu.welcome', 'en', name='Test')
print(f'EN: {test_en[:80]}...')

# Test RU  
test_ru = lm.get_text('main_menu.welcome', 'ru', name='Тест')
print(f'RU: {test_ru[:80]}...')

print('SUCCESS: Locale manager works!')
