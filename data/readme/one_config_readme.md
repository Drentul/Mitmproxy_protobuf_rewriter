Экран настройки правил для конкретного запроса.

По этому набору параметров определяется, соответствует ли запрос этому набору правил:

is_on - включает и выключает правило. Зеленый соответствует положению включено, а красный - выключено.
authority_expr - задает соответствие для протокола, адреса сервера и порта. Обычно не используется или указывается просто адрес сервера.
path_expr - задает путь для API. Например: /playback-info/.*
Оба этих параметра поддерживают регулярные выражения
method - позволяет отметить флажками используемые методы для запроса

По этим параметрам определяется, что с этим запросом нужно сделать:

status_code - изменяет код ответа. Помните, что при указании кода ошибки хорошо бы еще и содержимое изменить на протобуф с ошибкой.
save_content - сохраняет протобуф в виде json в папку data/saves под указанным именем. Тип протобуфа берется из блока настроек API rules.
rewrite_content - перезаписывает протобуф подготовленным файлом в формате json из папки data/fake_server. Можно сначала сохранить результат запроса через save_content, изменить часть полей, и подложить полученный результат сюда.
headers - изменяет/добавляет заголовки. Если такой заголовок существовал, то он будет перезаписан, если нет - добавлен.