// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Russian (`ru`).
class AppLocalizationsRu extends AppLocalizations {
  AppLocalizationsRu([String locale = 'ru']) : super(locale);

  @override
  String get appName => 'Biletflow Персонал';

  @override
  String get demo => 'Демоданные · симуляция онлайн';

  @override
  String get signIn => 'Войти';

  @override
  String get email => 'Электронная почта';

  @override
  String get password => 'Пароль';

  @override
  String get showPassword => 'Показать пароль';

  @override
  String get hidePassword => 'Скрыть пароль';

  @override
  String get requiredField => 'Заполните это поле.';

  @override
  String get invalidEmail => 'Введите корректный адрес почты.';

  @override
  String get forgotPassword => 'Забыли пароль?';

  @override
  String get resetPassword => 'Сброс пароля';

  @override
  String get sendReset => 'Отправить ссылку';

  @override
  String get resetSent =>
      'Если аккаунт существует, мы отправим ссылку. В деморежиме письма не отправляются.';

  @override
  String get noEvents => 'Пока нет назначенных событий.';

  @override
  String get refresh => 'Обновить';

  @override
  String get retry => 'Повторить';

  @override
  String get back => 'Назад';

  @override
  String get settings => 'Настройки';

  @override
  String get language => 'Язык';

  @override
  String get logout => 'Выйти';

  @override
  String get account => 'Аккаунт';

  @override
  String get overview => 'Обзор события';

  @override
  String get registered => 'Зарегистрировано';

  @override
  String get remaining => 'Ещё не пришли';

  @override
  String get scanTicket => 'Сканировать билет';

  @override
  String get eventCancelled => 'Событие отменено. Вход закрыт.';

  @override
  String get published => 'Опубликовано';

  @override
  String get cancelled => 'Отменён';

  @override
  String get openCamera => 'Открыть камеру';

  @override
  String get closeCamera => 'Закрыть камеру';

  @override
  String get cameraError =>
      'Камера недоступна или доступ запрещён. Разрешите доступ в настройках устройства или введите код ниже.';

  @override
  String get torch => 'Включить/выключить фонарик';

  @override
  String get manualCode => 'ID билета или QR-токен';

  @override
  String get manualCodeHint =>
      'Вставьте UUID билета или 64-символьный QR-токен.';

  @override
  String get verify => 'Проверить билет';

  @override
  String get demoScans => 'Сценарии демосканирования';

  @override
  String get valid => 'Действительный билет';

  @override
  String get invalid => 'Недействительный билет';

  @override
  String get refunded => 'Билет возвращён';

  @override
  String get checked_in => 'Уже использован';

  @override
  String get wrong_event => 'Билет на другое событие';

  @override
  String get campaign_qr => 'Рекламный QR · вход запрещён';

  @override
  String get verification => 'Результат проверки';

  @override
  String get checkIn => 'Пропустить гостя';

  @override
  String get admitted => 'Вход зарегистрирован';

  @override
  String get scanNext => 'Сканировать следующий билет';

  @override
  String get undo => 'Отменить проход';

  @override
  String get undoTitle => 'Отменить этот проход?';

  @override
  String get undoHint => 'Билет снова станет доступен для прохода.';

  @override
  String get undoDone => 'Проход отменён';

  @override
  String get confirm => 'Подтвердить';

  @override
  String get cancel => 'Отмена';

  @override
  String get attendees => 'Участники';

  @override
  String get searchHint => 'Имя, почта или ID билета';

  @override
  String get noResults => 'Участники не найдены.';

  @override
  String get loadMore => 'Загрузить ещё';

  @override
  String get ticket => 'Билет';

  @override
  String get ticketType => 'Тип билета';

  @override
  String get seat => 'Сектор / ряд / место';

  @override
  String get generalAdmission => 'Свободная рассадка';

  @override
  String get checkInTime => 'Время прохода';

  @override
  String get offline => 'Нет соединения. Для прохода нужен ответ сервера.';

  @override
  String get serverError => 'Сервис недоступен. Попробуйте ещё раз.';

  @override
  String get unauthorized => 'Сессия истекла. Войдите снова.';

  @override
  String get forbidden => 'У вас нет прав на это действие.';

  @override
  String get notFound => 'Эта запись недоступна.';

  @override
  String get conflict => 'Статус билета изменился. Обновите данные.';

  @override
  String get badCredentials => 'Неверная почта или пароль.';

  @override
  String get storageError => 'Не удалось получить сохранённую сессию.';

  @override
  String get genericError => 'Что-то пошло не так. Попробуйте ещё раз.';

  @override
  String get demoControls => 'Управление демо';

  @override
  String get normal => 'Обычное соединение';

  @override
  String get offlineMode => 'Имитировать отсутствие сети';

  @override
  String get serverMode => 'Имитировать ошибку сервера';

  @override
  String get emptyAssignments => 'Показать пустые назначения';

  @override
  String get revokeAssignment => 'Отозвать доступ к событию';

  @override
  String get expireSession => 'Завершить сессию';

  @override
  String get resetDemo => 'Сбросить демоданные';

  @override
  String get permissionDenied => 'Отмена прохода запрещена';

  @override
  String get resetHint => 'Укажите почту аккаунта сотрудника.';

  @override
  String get demoShort => 'Демо';

  @override
  String get overviewTab => 'Обзор';

  @override
  String get scanTab => 'Сканер';

  @override
  String get guestsTab => 'Гости';

  @override
  String get welcomeTitle => 'Всё готово\nк вашему событию.';

  @override
  String get welcomeBody =>
      'Войдите, чтобы проверять билеты и встречать гостей.';

  @override
  String get yourEvents => 'Ваши события';

  @override
  String get chooseEvent => 'Выберите событие, на котором вы работаете.';

  @override
  String get attendance => 'Посещаемость';

  @override
  String get admittedLabel => 'Прошли';

  @override
  String ofRegistered(String total) {
    return 'из $total зарегистрированных';
  }

  @override
  String get readyToScan => 'Готовы встретить гостя';

  @override
  String get scanGuide => 'Поместите QR-код билета в рамку.';

  @override
  String get manualEntry => 'Ввести код вручную';

  @override
  String get demoChoose => 'Проверить демобилет';

  @override
  String get checkingTicket => 'Проверяем билет…';

  @override
  String get admissionHint =>
      'Подтвердите вход, чтобы отметить билет использованным.';

  @override
  String get admittedHint =>
      'Проход записан. Можно встречать следующего гостя.';

  @override
  String get usedHint => 'По этому билету уже прошли.';

  @override
  String get blockedHint =>
      'По этому билету вход запрещён. Проверьте данные или обратитесь к организатору.';

  @override
  String get noGuestsHint => 'Попробуйте другое имя, почту или ID билета.';

  @override
  String get preferences => 'Предпочтения';

  @override
  String get demoToolsHint => 'Проверка статусов билетов и ошибок сети.';

  @override
  String get signedInAs => 'Вы вошли как сотрудник события';

  @override
  String get eventDetails => 'Информация о событии';

  @override
  String get logoutConfirm => 'Выйти из аккаунта?';

  @override
  String get logoutHint => 'Для проверки билетов потребуется войти снова.';

  @override
  String get clearSearch => 'Очистить поиск';

  @override
  String get demoLoginHint =>
      'Демоаккаунт уже заполнен. Войдите, чтобы посмотреть приложение.';

  @override
  String get ticketNotFound => 'Билет не найден';

  @override
  String get pending => 'Ожидает оплаты';

  @override
  String get invalidOrder => 'Заказ недействителен';

  @override
  String get validationError =>
      'Проверьте введённые данные и попробуйте снова.';
}
