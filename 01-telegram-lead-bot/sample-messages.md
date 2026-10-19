# Test messages (send these to your bot during the demo)

1. RU, hot lead:
   «Здравствуйте! Меня зовут Азиз, у меня кофейня в Юнусабаде. Нужно SMM + таргет в Instagram, бюджет около 8 млн сум в месяц, хотим начать на следующей неделе. Мой номер +998 90 123 45 67»
2. UZ, missing info:
   «Assalomu alaykum, internet do'konimiz uchun sayt kerak edi. Narxi qancha bo'ladi?»
3. EN, vague:
   «hi, do you guys do video ads?»

Expected: #1 → score ~8–9, manager alert fires, row in Sheets. #2 → reply in Uzbek asking name/budget/deadline. #3 → reply in English, low score.
