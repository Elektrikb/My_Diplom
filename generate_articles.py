# -*- coding: utf-8 -*-
import sqlite3
import json

# Подключение к базе данных
conn = sqlite3.connect(r'd:\Бэкап\Projects\Работа с Claude\data\app.db')
cursor = conn.cursor()

# 50 разнообразных IT-статей
articles = [
    {
        "title": "Основы Git и системы контроля версий",
        "content": "Git - распределенная система контроля версий, созданная Линусом Торвальдсом. Основные команды: git init (инициализация репозитория), git add (добавление файлов в staging), git commit (создание коммита), git push (отправка изменений на сервер), git pull (получение изменений). Ветки позволяют работать над несколькими задачами параллельно. Команда git merge объединяет ветки. Git хранит историю изменений и позволяет откатиться к любой версии кода.",
        "tags": ["git", "version control", "development", "github", "gitlab"]
    },
    {
        "title": "REST API: принципы проектирования",
        "content": "REST (Representational State Transfer) - архитектурный стиль для создания веб-сервисов. Основные принципы: использование HTTP методов (GET для чтения, POST для создания, PUT для обновления, DELETE для удаления), stateless коммуникация, единообразие интерфейса, кэшируемость. URL должны быть понятными и иерархическими (/users/123/orders). Коды ответов: 200 (успех), 201 (создано), 400 (ошибка клиента), 404 (не найдено), 500 (ошибка сервера).",
        "tags": ["rest", "api", "web development", "http", "backend"]
    },
    {
        "title": "Введение в TypeScript",
        "content": "TypeScript - типизированный надмножество JavaScript, разработанное Microsoft. Добавляет статическую типизацию, интерфейсы, enum, generics. Компилируется в чистый JavaScript. Типы данных: string, number, boolean, array, tuple, enum, any, void, never. Интерфейсы описывают структуру объектов. Generics позволяют создавать переиспользуемые компоненты. TypeScript улучшает поддержку IDE, выявляет ошибки на этапе компиляции и делает код более читаемым.",
        "tags": ["typescript", "javascript", "programming", "frontend", "types"]
    },
    {
        "title": "Docker: контейнеризация приложений",
        "content": "Docker - платформа для разработки, доставки и запуска приложений в контейнерах. Контейнер включает приложение и все его зависимости. Dockerfile описывает образ контейнера. Основные команды: docker build (создание образа), docker run (запуск контейнера), docker ps (список контейнеров), docker stop (остановка). Docker Compose позволяет управлять многоконтейнерными приложениями. Преимущества: изоляция, портативность, быстрое развертывание, эффективное использование ресурсов.",
        "tags": ["docker", "containers", "devops", "virtualization", "deployment"]
    },
    {
        "title": "NoSQL базы данных: когда использовать",
        "content": "NoSQL - класс СУБД, отличающихся от реляционных баз данных. Типы: документо-ориентированные (MongoDB), key-value (Redis), колоночные (Cassandra), графовые (Neo4j). Используйте NoSQL когда: нужна горизонтальная масштабируемость, схема данных гибкая и меняется, требуется высокая производительность для чтения/записи, работаете с неструктурированными данными. Реляционные БД лучше для сложных транзакций, строгой консистентности и сложных запросов с JOIN.",
        "tags": ["nosql", "databases", "mongodb", "redis", "scaling"]
    },
    {
        "title": "Микросервисная архитектура",
        "content": "Микросервисы - архитектурный подход, при котором приложение состоит из небольших независимых сервисов. Каждый сервис отвечает за определенную бизнес-функцию, имеет свою базу данных, может быть написан на разных языках. Преимущества: независимое развертывание, масштабируемость, технологическая гибкость, отказоустойчивость. Недостатки: сложность взаимодействия, распределенные транзакции, мониторинг. Требуются: API Gateway, service discovery, централизованное логирование.",
        "tags": ["microservices", "architecture", "scalability", "distributed systems", "design"]
    },
    {
        "title": "Async/Await в JavaScript",
        "content": "Async/await - синтаксический сахар над Promise для работы с асинхронным кодом. Функция с ключевым словом async всегда возвращает Promise. Await приостанавливает выполнение функции до разрешения Promise. Код выглядит синхронным, но выполняется асинхронно. Обработка ошибок через try/catch. Можно использовать Promise.all() для параллельного выполнения. Пример: async function getData() { try { const data = await fetch(url); return data.json(); } catch(error) { console.error(error); } }",
        "tags": ["javascript", "async", "promises", "programming", "es6"]
    },
    {
        "title": "Основы кибербезопасности для разработчиков",
        "content": "Важные принципы безопасности: валидация всех входных данных, использование prepared statements для защиты от SQL injection, экранирование вывода для предотвращения XSS, HTTPS для всех соединений, безопасное хранение паролей (bcrypt, argon2), защита от CSRF токенами. Не храните секреты в коде, используйте переменные окружения. Регулярно обновляйте зависимости. Применяйте принцип наименьших привилегий. Логируйте события безопасности. Проводите code review и тестирование безопасности.",
        "tags": ["security", "cybersecurity", "web security", "encryption", "best practices"]
    },
    {
        "title": "GraphQL vs REST",
        "content": "GraphQL - язык запросов для API, альтернатива REST. Преимущества GraphQL: клиент запрашивает только нужные поля (нет overfetching/underfetching), один endpoint, строгая типизация схемы, introspection. REST преимущества: простота, кэширование HTTP, широкая поддержка. GraphQL лучше для: сложных связанных данных, мобильных приложений (экономия трафика), быстро меняющихся требований. REST лучше для: простых CRUD операций, публичных API, когда важно кэширование.",
        "tags": ["graphql", "rest", "api", "web development", "comparison"]
    },
    {
        "title": "CI/CD: непрерывная интеграция и доставка",
        "content": "CI/CD - практики автоматизации разработки. Continuous Integration: частые коммиты в общую ветку, автоматические сборка и тестирование. Continuous Delivery: код всегда готов к релизу. Continuous Deployment: автоматическое развертывание в production. Этапы pipeline: checkout кода, сборка, тестирование (unit, integration, e2e), статический анализ, деплой. Инструменты: Jenkins, GitLab CI, GitHub Actions, CircleCI. Преимущества: быстрая обратная связь, меньше ошибок, ускорение релизов.",
        "tags": ["ci/cd", "devops", "automation", "testing", "deployment"]
    },
    {
        "title": "Redis: кэширование и хранилище данных",
        "content": "Redis - in-memory хранилище данных типа key-value. Поддерживает структуры: строки, хэши, списки, множества, sorted sets. Используется для: кэширования, очередей сообщений, session storage, real-time analytics, pub/sub. Операции атомарны. Persistence: RDB (снапшоты) и AOF (лог операций). Репликация master-slave для отказоустойчивости. Redis Cluster для горизонтального масштабирования. Очень быстрый благодаря хранению в памяти. Команды: SET, GET, HSET, LPUSH, SADD.",
        "tags": ["redis", "cache", "in-memory", "databases", "performance"]
    },
    {
        "title": "React Hooks: useState и useEffect",
        "content": "Hooks позволяют использовать состояние в функциональных компонентах. useState возвращает значение и функцию для его обновления: const [count, setCount] = useState(0). useEffect выполняет побочные эффекты: запросы к API, подписки, изменение DOM. Вызывается после рендера. Второй аргумент - массив зависимостей, определяет когда эффект перезапускается. Пустой массив [] - только при монтировании. Функция очистки возвращается из эффекта. Другие хуки: useContext, useReducer, useMemo, useCallback.",
        "tags": ["react", "hooks", "frontend", "javascript", "web development"]
    },
    {
        "title": "Kubernetes для начинающих",
        "content": "Kubernetes (K8s) - система оркестрации контейнеров. Автоматизирует развертывание, масштабирование и управление контейнеризированными приложениями. Основные концепции: Pod (группа контейнеров), Service (сетевой доступ к Pods), Deployment (декларативные обновления), ConfigMap и Secret (конфигурация), Ingress (HTTP маршрутизация). Kubectl - CLI для управления. Kubernetes обеспечивает: self-healing, автоскейлинг, service discovery, load balancing. Популярные managed решения: GKE, EKS, AKS.",
        "tags": ["kubernetes", "k8s", "containers", "orchestration", "devops"]
    },
    {
        "title": "SQL оптимизация запросов",
        "content": "Методы оптимизации SQL: создавайте индексы на часто используемых в WHERE, JOIN, ORDER BY колонках. Избегайте SELECT *, выбирайте только нужные поля. Используйте EXPLAIN для анализа плана выполнения. JOIN эффективнее подзапросов. Денормализация может улучшить производительность чтения. Партиционирование таблиц для больших данных. Кэшируйте результаты частых запросов. Избегайте N+1 проблемы, используйте eager loading. Оптимизируйте медленные запросы через индексы и переписывание запросов.",
        "tags": ["sql", "optimization", "databases", "performance", "indexing"]
    },
    {
        "title": "JWT токены аутентификации",
        "content": "JSON Web Token (JWT) - стандарт для создания токенов доступа. Структура: header.payload.signature. Header содержит тип и алгоритм, payload - данные (claims), signature - подпись для проверки целостности. Stateless - сервер не хранит сессии. Используется для: аутентификации API, single sign-on. После логина сервер возвращает JWT, клиент отправляет его в заголовке Authorization: Bearer <token>. Храните токены безопасно, используйте короткое время жизни, refresh tokens для обновления. Не храните чувствительные данные в payload.",
        "tags": ["jwt", "authentication", "security", "api", "tokens"]
    },
    {
        "title": "Node.js Event Loop",
        "content": "Event Loop - механизм, позволяющий Node.js выполнять неблокирующие I/O операции. Фазы: timers (setTimeout, setInterval), pending callbacks, idle/prepare, poll (I/O события), check (setImmediate), close callbacks. Операции выполняются асинхронно, колбэки добавляются в очередь. Микрозадачи (Promise) имеют приоритет над макрозадачами. process.nextTick() выполняется перед следующей фазой. Понимание Event Loop критично для написания эффективного Node.js кода и избежания блокировок.",
        "tags": ["nodejs", "event loop", "javascript", "async", "backend"]
    },
    {
        "title": "Webpack: сборка JavaScript приложений",
        "content": "Webpack - module bundler для JavaScript приложений. Создает граф зависимостей и собирает все модули в один или несколько bundle файлов. Концепции: entry (точка входа), output (куда сохранять), loaders (преобразование файлов), plugins (оптимизация, минификация). Loaders: babel-loader (транспиляция JS), css-loader, file-loader. Plugins: HtmlWebpackPlugin, MiniCssExtractPlugin. Code splitting разбивает код на chunks для lazy loading. Dev server для разработки с hot reload. Webpack 5 улучшил производительность и добавил Module Federation.",
        "tags": ["webpack", "bundler", "javascript", "build tools", "frontend"]
    },
    {
        "title": "Принципы SOLID",
        "content": "SOLID - пять принципов объектно-ориентированного программирования. S (Single Responsibility) - класс должен иметь одну причину для изменения. O (Open/Closed) - открыт для расширения, закрыт для модификации. L (Liskov Substitution) - подклассы должны заменять базовые классы. I (Interface Segregation) - много специализированных интерфейсов лучше одного общего. D (Dependency Inversion) - зависимость от абстракций, а не конкретных реализаций. Соблюдение SOLID делает код более поддерживаемым, тестируемым и расширяемым.",
        "tags": ["solid", "oop", "design principles", "architecture", "best practices"]
    },
    {
        "title": "MongoDB: работа с документами",
        "content": "MongoDB - документо-ориентированная NoSQL база данных. Данные хранятся в формате BSON (Binary JSON). Коллекции содержат документы (аналог таблиц и строк в SQL). Операции: insertOne/insertMany (вставка), find (поиск), updateOne/updateMany (обновление), deleteOne/deleteMany (удаление). Индексы ускоряют запросы. Aggregation framework для сложных запросов и группировок. Репликация через replica sets. Шардирование для горизонтального масштабирования. Схема гибкая, документы в одной коллекции могут иметь разную структуру.",
        "tags": ["mongodb", "nosql", "databases", "documents", "bson"]
    },
    {
        "title": "CSS Grid Layout",
        "content": "CSS Grid - двумерная система раскладки для веб-страниц. Контейнер: display: grid. Определение структуры: grid-template-columns, grid-template-rows. Размещение элементов: grid-column, grid-row. fr единица для гибких размеров. gap для промежутков между элементами. grid-template-areas для именованных областей. repeat() для повторяющихся паттернов. auto-fit и auto-fill для адаптивности. Grid Inspector в DevTools помогает визуализировать сетку. Поддержка всех современных браузеров. Идеален для сложных макетов.",
        "tags": ["css", "grid", "layout", "frontend", "web design"]
    },
    {
        "title": "Тестирование: Unit, Integration, E2E",
        "content": "Типы тестирования: Unit тесты проверяют отдельные функции/методы в изоляции. Быстрые, много unit тестов. Integration тесты проверяют взаимодействие компонентов. E2E (end-to-end) тесты проверяют полный пользовательский сценарий. Пирамида тестирования: много unit, меньше integration, мало E2E. Инструменты: Jest, Mocha (unit/integration), Cypress, Playwright (E2E). TDD (Test-Driven Development): сначала пишется тест, затем код. Code coverage показывает процент покрытия кода тестами.",
        "tags": ["testing", "unit tests", "e2e", "qa", "development"]
    },
    {
        "title": "WebSocket для real-time коммуникации",
        "content": "WebSocket - протокол для двусторонней связи между клиентом и сервером. В отличие от HTTP, соединение постоянное. Handshake через HTTP Upgrade, затем TCP соединение. Используется для: чаты, онлайн игры, live notifications, collaborative editing. JavaScript API: new WebSocket(url), методы send(), close(), события onopen, onmessage, onerror, onclose. Библиотеки: Socket.io (добавляет reconnection, rooms), ws для Node.js. Альтернативы: Server-Sent Events (SSE) для односторонней связи, long polling.",
        "tags": ["websocket", "real-time", "networking", "javascript", "communication"]
    },
    {
        "title": "Linux команды для разработчиков",
        "content": "Полезные Linux команды: ls (список файлов), cd (смена директории), pwd (текущая директория), mkdir (создание папки), rm (удаление), cp (копирование), mv (перемещение). grep (поиск текста), find (поиск файлов), cat (вывод содержимого), less (просмотр), tail -f (мониторинг логов). ps (процессы), top/htop (мониторинг системы), kill (остановка процесса). chmod (права доступа), chown (владелец). curl/wget (HTTP запросы). ssh (удаленное подключение), scp (копирование по сети).",
        "tags": ["linux", "command line", "terminal", "unix", "devops"]
    },
    {
        "title": "OAuth 2.0 авторизация",
        "content": "OAuth 2.0 - протокол авторизации для делегирования доступа. Позволяет приложению получить ограниченный доступ к ресурсам пользователя без передачи пароля. Роли: Resource Owner (пользователь), Client (приложение), Authorization Server, Resource Server. Flows: Authorization Code (для веб-приложений), Implicit (устарел), Client Credentials (сервис-сервис), Resource Owner Password (legacy). Access token - для доступа к ресурсам, Refresh token - для обновления access token. Используется в социальных сетях для 'Login with Google/Facebook'.",
        "tags": ["oauth", "authorization", "security", "api", "authentication"]
    },
    {
        "title": "Алгоритмы сортировки",
        "content": "Основные алгоритмы сортировки: Bubble Sort O(n²) - простой, неэффективный. Selection Sort O(n²) - выбор минимума. Insertion Sort O(n²) - хорош для почти отсортированных. Merge Sort O(n log n) - divide and conquer, стабильная. Quick Sort O(n log n) average, O(n²) worst - часто используется. Heap Sort O(n log n) - использует кучу. Counting Sort O(n+k) - для целых чисел в ограниченном диапазоне. Radix Sort O(nk) - для целых чисел. Выбор зависит от размера данных, распределения, требований к памяти.",
        "tags": ["algorithms", "sorting", "data structures", "complexity", "computer science"]
    },
    {
        "title": "Golang: конкурентность с goroutines",
        "content": "Go предоставляет мощные инструменты для конкурентности. Goroutines - легковесные потоки, запускаются через go func(). Каналы (channels) для коммуникации между goroutines: ch := make(chan int). Отправка: ch <- value, получение: value := <-ch. Буферизованные каналы: make(chan int, 10). select для работы с несколькими каналами. WaitGroup для синхронизации. Mutex для защиты общих данных. Контекст для отмены операций. Go scheduler управляет goroutines эффективно. Конкурентность - одна из сильных сторон Go.",
        "tags": ["golang", "go", "concurrency", "goroutines", "channels"]
    },
    {
        "title": "Progressive Web Apps (PWA)",
        "content": "PWA - веб-приложения с возможностями нативных приложений. Характеристики: работают offline (Service Worker), устанавливаются на устройство, push уведомления, доступ к камере и геолокации. Manifest.json описывает приложение (иконки, имя, цвета). Service Worker - скрипт, работающий в фоне, кэширует ресурсы. Стратегии кэширования: Cache First, Network First, Stale While Revalidate. Lighthouse проверяет PWA критерии. Преимущества: не нужен app store, одна кодовая база, меньше размер, SEO.",
        "tags": ["pwa", "progressive web apps", "service worker", "web development", "mobile"]
    },
    {
        "title": "Design Patterns: Singleton, Factory, Observer",
        "content": "Паттерны проектирования - проверенные решения типичных проблем. Singleton - только один экземпляр класса, глобальный доступ. Factory - создание объектов без указания точного класса. Observer - подписчики получают уведомления об изменениях субъекта. Strategy - семейство алгоритмов, взаимозаменяемых. Decorator - динамическое добавление функциональности. Repository - абстракция для работы с данными. MVC (Model-View-Controller) - разделение логики, представления и управления. Паттерны улучшают архитектуру и переиспользование кода.",
        "tags": ["design patterns", "architecture", "oop", "software design", "best practices"]
    },
    {
        "title": "Elasticsearch для полнотекстового поиска",
        "content": "Elasticsearch - распределенная поисковая система на основе Lucene. Хранит данные в индексах (аналог БД) и документах (JSON). Инвертированный индекс для быстрого полнотекстового поиска. Анализаторы обрабатывают текст: tokenization, lowercase, stemming. Query DSL для построения запросов: match, term, bool, range. Aggregations для аналитики и группировок. Масштабируется горизонтально через шардирование. Используется для: поиск на сайте, логирование (ELK stack), аналитика. Kibana для визуализации данных.",
        "tags": ["elasticsearch", "search", "full-text", "nosql", "analytics"]
    },
    {
        "title": "Python виртуальные окружения",
        "content": "Виртуальные окружения изолируют зависимости проектов. venv - встроенный модуль Python: python -m venv myenv. Активация: Windows - myenv\\Scripts\\activate, Linux/Mac - source myenv/bin/activate. pip install устанавливает пакеты в окружение. requirements.txt список зависимостей: pip freeze > requirements.txt, установка: pip install -r requirements.txt. Альтернативы: virtualenv, conda (для data science), poetry (управление зависимостями и packaging). Всегда используйте виртуальные окружения, чтобы избежать конфликтов версий.",
        "tags": ["python", "venv", "dependencies", "pip", "development"]
    },
    {
        "title": "CORS: Cross-Origin Resource Sharing",
        "content": "CORS - механизм безопасности браузера, контролирующий cross-origin запросы. Same-Origin Policy запрещает запросы к другому домену. CORS разрешает их через заголовки. Сервер отправляет Access-Control-Allow-Origin: * или конкретный домен. Preflight запрос (OPTIONS) проверяет разрешения для сложных запросов. Заголовки: Access-Control-Allow-Methods (GET, POST), Access-Control-Allow-Headers, Access-Control-Allow-Credentials (для cookies). Настраивается на бэкенде. CORS ошибки - частая проблема при разработке фронтенда.",
        "tags": ["cors", "web security", "http", "browsers", "api"]
    },
    {
        "title": "Kafka для обработки событий",
        "content": "Apache Kafka - распределенная платформа потоковой обработки. Producers отправляют сообщения в топики, Consumers читают из топиков. Топики разбиты на партиции для параллелизма. Сообщения хранятся на диске с настраиваемым retention. Consumer Groups для масштабирования потребления. Offset отслеживает позицию чтения. Используется для: event sourcing, логирование, метрики, микросервисы коммуникация, ETL. Высокая пропускная способность, отказоустойчивость. ZooKeeper (или KRaft в новых версиях) для координации.",
        "tags": ["kafka", "streaming", "messaging", "events", "distributed systems"]
    },
    {
        "title": "Vue.js основы реактивности",
        "content": "Vue.js - прогрессивный фронтенд фреймворк. Реактивность - автоматическое обновление DOM при изменении данных. Vue 3 использует Proxy для отслеживания изменений. ref() для примитивов, reactive() для объектов. Computed свойства - кэшируемые вычисления. Watchers - реакция на изменения данных. Template синтаксис: {{ data }}, v-if, v-for, v-bind, v-on. Компоненты - переиспользуемые блоки. Props для передачи данных вниз, emit для событий вверх. Composition API для лучшей организации кода.",
        "tags": ["vuejs", "vue", "frontend", "javascript", "reactivity"]
    },
    {
        "title": "Nginx как reverse proxy",
        "content": "Nginx - веб-сервер и reverse proxy. Reverse proxy принимает запросы клиентов и перенаправляет на бэкенд серверы. Конфигурация в nginx.conf. location блоки определяют маршрутизацию. proxy_pass указывает upstream сервер. Load balancing распределяет нагрузку: round-robin, least connections, ip-hash. Кэширование статических файлов. SSL/TLS терминация. Gzip сжатие. Rate limiting для защиты от DDoS. Используется перед Node.js, Python, PHP приложениями. Высокая производительность и низкое потребление памяти.",
        "tags": ["nginx", "reverse proxy", "web server", "load balancing", "devops"]
    },
    {
        "title": "Rust: безопасность памяти без GC",
        "content": "Rust - системный язык программирования с фокусом на безопасность и производительность. Ownership система управляет памятью без garbage collector. Правила: каждое значение имеет владельца, только один владелец, при выходе из scope память освобождается. Borrowing: immutable (&) и mutable (&mut) ссылки. Lifetime аннотации обеспечивают безопасность ссылок. Компилятор предотвращает data races, null pointer dereference, buffer overflow. Используется для: системное ПО, WebAssembly, embedded, network services. Крутая кривая обучения, но высокая надежность.",
        "tags": ["rust", "programming", "memory safety", "systems programming", "performance"]
    },
    {
        "title": "Serverless архитектура",
        "content": "Serverless - модель выполнения кода без управления инфраструктурой. FaaS (Function as a Service): AWS Lambda, Azure Functions, Google Cloud Functions. Код выполняется в ответ на события: HTTP запросы, изменения в БД, файлы в S3. Оплата за фактическое время выполнения. Автоматическое масштабирование. Stateless функции. Преимущества: нет управления серверами, масштабируемость, снижение затрат. Недостатки: cold start, ограничения времени выполнения, vendor lock-in. Используется для: API, обработка файлов, cron задачи.",
        "tags": ["serverless", "faas", "cloud", "lambda", "architecture"]
    },
    {
        "title": "Terraform для Infrastructure as Code",
        "content": "Terraform - инструмент для декларативного управления инфраструктурой. Описывает желаемое состояние инфраструктуры в .tf файлах (HCL язык). Providers для разных платформ: AWS, Azure, GCP, Kubernetes. Resources - создаваемые компоненты. terraform init инициализирует проект, plan показывает изменения, apply применяет их. State файл отслеживает текущее состояние. Модули для переиспользования конфигураций. Variables и outputs для параметризации. Remote state для команд. Позволяет версионировать инфраструктуру, автоматизировать создание окружений.",
        "tags": ["terraform", "iac", "infrastructure", "devops", "automation"]
    },
    {
        "title": "Функциональное программирование в JavaScript",
        "content": "Функциональное программирование (FP) - парадигма на основе функций. Принципы: immutability (неизменяемость данных), pure functions (без побочных эффектов, детерминированные), функции высшего порядка (принимают или возвращают функции). Array методы: map, filter, reduce, forEach. Композиция функций. Каррирование - преобразование f(a,b) в f(a)(b). Замыкания (closures). Избегайте мутаций, используйте spread/rest операторы. Библиотеки: Lodash/fp, Ramda. FP делает код предсказуемым, тестируемым, легко распараллеливаемым.",
        "tags": ["functional programming", "javascript", "fp", "immutability", "pure functions"]
    },
    {
        "title": "PostgreSQL: продвинутые возможности",
        "content": "PostgreSQL - мощная open-source реляционная СУБД. JSON/JSONB типы для работы с JSON данными, индексы и операторы. Array типы. Full-text search. GIS расширение PostGIS для геоданных. Window functions для аналитики. CTE (Common Table Expressions) для сложных запросов. Triggers и stored procedures. Репликация: streaming replication, logical replication. Партиционирование таблиц. MVCC для конкурентности. Расширения: pg_stat_statements, pg_trgm. Поддержка ACID, надежность, расширяемость.",
        "tags": ["postgresql", "sql", "databases", "relational", "advanced"]
    },
    {
        "title": "CSS Flexbox для раскладки",
        "content": "Flexbox - одномерная система раскладки для строк или столбцов. Контейнер: display: flex. flex-direction: row (по умолчанию), column, row-reverse, column-reverse. justify-content выравнивает по главной оси: flex-start, center, space-between, space-around. align-items выравнивает по перпендикулярной оси. flex-wrap: wrap для переноса элементов. Элементы: flex-grow, flex-shrink, flex-basis определяют размеры. order изменяет порядок. Идеален для навигации, карточек, центрирования. Хорошая поддержка браузеров.",
        "tags": ["css", "flexbox", "layout", "frontend", "responsive"]
    },
    {
        "title": "Prometheus и Grafana для мониторинга",
        "content": "Prometheus - система мониторинга и алертинга. Собирает метрики через HTTP pull модель. Метрики: counter (только растет), gauge (может уменьшаться), histogram, summary. PromQL - язык запросов для метрик. Exporters предоставляют метрики различных систем. Alertmanager для уведомлений. Grafana - платформа визуализации. Создание дашбордов с графиками, таблицами. Интеграция с Prometheus, Elasticsearch, InfluxDB. Используется для мониторинга: серверов, приложений, баз данных. Service discovery для динамических окружений.",
        "tags": ["prometheus", "grafana", "monitoring", "metrics", "devops"]
    },
    {
        "title": "DDD: Domain-Driven Design",
        "content": "Domain-Driven Design - подход к разработке сложных систем. Фокус на бизнес-домене и его логике. Ubiquitous Language - единый язык команды и кода. Bounded Context - границы моделей. Entities (с идентичностью), Value Objects (без идентичности), Aggregates (группа связанных объектов), Repositories (доступ к данным), Services (бизнес-логика без состояния). Domain Events для коммуникации между контекстами. Layered Architecture: domain, application, infrastructure, presentation. DDD помогает справляться со сложностью через правильное моделирование.",
        "tags": ["ddd", "domain-driven design", "architecture", "design", "software engineering"]
    },
    {
        "title": "Async Python: asyncio",
        "content": "asyncio - библиотека для асинхронного программирования в Python. Корутины определяются через async def, вызываются через await. Event loop управляет выполнением. asyncio.run() запускает корутину. asyncio.gather() для параллельного выполнения. Используйте асинхронные библиотеки: aiohttp (HTTP), asyncpg (PostgreSQL), motor (MongoDB). Не блокируйте event loop синхронными операциями. run_in_executor для CPU-интенсивных задач. Async/await делает I/O bound код эффективным. Хорошо подходит для web scraping, API, веб-серверов.",
        "tags": ["python", "asyncio", "async", "concurrency", "programming"]
    },
    {
        "title": "gRPC для межсервисной коммуникации",
        "content": "gRPC - высокопроизводительный RPC фреймворк от Google. Использует Protocol Buffers для сериализации (компактнее JSON). HTTP/2 для транспорта: multiplexing, streaming, header compression. Определение сервисов в .proto файлах. Генерация кода для разных языков. Типы: Unary (запрос-ответ), Server streaming, Client streaming, Bidirectional streaming. Преимущества: производительность, строгая типизация, code generation. Используется в микросервисах. Альтернативы: REST (проще, но медленнее), GraphQL (гибкие запросы).",
        "tags": ["grpc", "rpc", "microservices", "protobuf", "api"]
    },
    {
        "title": "Swift для iOS разработки",
        "content": "Swift - язык программирования от Apple для iOS, macOS, watchOS, tvOS. Современный синтаксис, безопасность типов. Optionals для работы с nil: var name: String?. Guard и if let для unwrapping. Closures - анонимные функции. Protocols для определения интерфейсов. Extensions добавляют функциональность существующим типам. Generics для переиспользуемого кода. ARC (Automatic Reference Counting) управляет памятью. SwiftUI - декларативный фреймворк для UI. Xcode - IDE для разработки. Swift быстрее и безопаснее Objective-C.",
        "tags": ["swift", "ios", "mobile", "apple", "programming"]
    },
    {
        "title": "Memcached для распределенного кэша",
        "content": "Memcached - распределенная система кэширования в памяти. Key-value хранилище, простой интерфейс: set, get, delete. Данные в RAM, очень быстрый доступ. LRU (Least Recently Used) вытеснение при нехватке памяти. Протокол: текстовый или бинарный. Клиент хэширует ключ для выбора сервера (consistent hashing). Не персистентен - перезапуск теряет данные. Используется для: session storage, кэш запросов к БД, результатов API. Сравнение с Redis: Memcached проще, Redis функциональнее (структуры данных, persistence).",
        "tags": ["memcached", "cache", "distributed", "performance", "in-memory"]
    },
    {
        "title": "Angular: компоненты и dependency injection",
        "content": "Angular - полнофункциональный фреймворк от Google. Компоненты - основные блоки: TypeScript класс + HTML template + CSS. Декораторы: @Component, @Injectable, @NgModule. Data binding: {{ }} (интерполяция), [property], (event), [(ngModel)]. Директивы: *ngIf, *ngFor, *ngSwitch. Services для бизнес-логики, инжектируются через DI. RxJS для асинхронности и реактивности. Router для навигации. Forms: template-driven, reactive. HttpClient для HTTP запросов. CLI для генерации кода. Хорошо для крупных enterprise приложений.",
        "tags": ["angular", "frontend", "typescript", "framework", "spa"]
    },
    {
        "title": "Blockchain основы",
        "content": "Blockchain - распределенный реестр транзакций. Блоки связаны криптографически: каждый содержит хэш предыдущего. Консенсус алгоритмы: PoW (Proof of Work), PoS (Proof of Stake). Децентрализация - нет единой точки отказа. Иммутабельность - сложно изменить историю. Smart contracts - код на блокчейне (Ethereum). Криптовалюты: Bitcoin, Ethereum. Use cases: финансы, supply chain, digital identity. Публичные блокчейны открыты всем, приватные - ограниченный доступ. Технология перспективна, но есть проблемы масштабируемости.",
        "tags": ["blockchain", "distributed ledger", "cryptocurrency", "ethereum", "smart contracts"]
    },
    {
        "title": "RabbitMQ: очереди сообщений",
        "content": "RabbitMQ - брокер сообщений, реализует AMQP протокол. Producers отправляют сообщения в exchanges. Exchanges маршрутизируют в queues по routing key. Типы exchanges: direct (точное совпадение), topic (паттерны), fanout (broadcast), headers. Consumers получают сообщения из очередей. Acknowledgments подтверждают обработку. Durability для сохранения при сбоях. Используется для: асинхронная обработка, микросервисы коммуникация, задачи фоном. Dead Letter Exchange для необработанных сообщений. Management UI для мониторинга.",
        "tags": ["rabbitmq", "message queue", "amqp", "messaging", "async"]
    },
    {
        "title": "HTTPS и SSL/TLS",
        "content": "HTTPS - HTTP поверх SSL/TLS для безопасной передачи данных. SSL/TLS шифрует трафик между клиентом и сервером. Handshake: согласование протокола, обмен ключами, проверка сертификата. Сертификат подтверждает идентичность сервера, выдается CA (Certificate Authority). Асимметричное шифрование для обмена ключами (RSA, ECDSA), симметричное для данных (AES). Let's Encrypt - бесплатные SSL сертификаты. HTTPS обязателен для современных сайтов: защита данных, SEO, доверие пользователей. HSTS заставляет использовать HTTPS.",
        "tags": ["https", "ssl", "tls", "security", "encryption"]
    }
]

# Вставка статей в базу данных
for article in articles:
    cursor.execute("""
        INSERT INTO articles (title, content, tags, url)
        VALUES (?, ?, ?, ?)
    """, (article["title"], article["content"], json.dumps(article["tags"], ensure_ascii=False), None))

conn.commit()
print(f"Успешно добавлено {len(articles)} статей в базу данных!")

# Проверка
cursor.execute("SELECT COUNT(*) FROM articles")
total = cursor.fetchone()[0]
print(f"Всего статей в базе: {total}")

conn.close()
