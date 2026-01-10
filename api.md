# API Контракты для TeachHelper

Документация API для связи между backend и frontend частями приложения.

**Базовый URL:** `/api` (или как настроено в приложении)

**Аутентификация:** Большинство эндпоинтов требуют аутентификации через OAuth2. Токен передается в заголовке `Authorization: Bearer <token>` или через cookie `session`.

---

## 1. Аутентификация (`/auth`)

### 1.1 Регистрация пользователя
**POST** `/auth/register`

**Тело запроса:**
```json
{
  "email": "ivan@example.com",
  "first_name": "ivan",
  "last_name": "ivanov",
  "password": "123456",
  "role": "teacher" // или "student"
}
```

**Ответ:** `200 OK`
```json
{
  "id": "uuid",
  "email": "ivan@example.com",
  "first_name": "ivan",
  "last_name": "ivanov",
  "role": "teacher",
  "is_verificated": false
}
```

---

### 1.2 Вход в систему
**POST** `/auth/login`

**Формат:** `application/x-www-form-urlencoded` (OAuth2PasswordRequestForm)

**Параметры:**
- `username`: email пользователя
- `password`: пароль

**Ответ:** `200 OK`
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

**Примечание:** Токен также устанавливается в cookie `session`.

---

### 1.3 Отправка кода подтверждения
**POST** `/auth/send_code`

**Тело запроса:**
```json
{
  "email": "ivan@example.com"
}
```

**Ответ:** `200 OK` (детали зависят от реализации)

---

### 1.4 Подтверждение email
**POST** `/auth/confirm_email`

**Тело запроса:**
```json
{
  "email": "ivan@example.com",
  "code": "123456"
}
```

**Ответ:** `200 OK` (детали зависят от реализации)

---

### 1.5 Забыли пароль
**POST** `/auth/forgot_password`

**Тело запроса:**
```json
{
  "email": "ivan@example.com"
}
```

**Ответ:** `200 OK` (детали зависят от реализации)

---

### 1.6 Подтверждение сброса пароля
**POST** `/auth/confirm_reset`

**Тело запроса:**
```json
{
  "email": "ivan@example.com",
  "code": "123456"
}
```

**Ответ:** `200 OK` (возвращает токен для сброса)

---

### 1.7 Сброс пароля
**POST** `/auth/reset_password`

**Тело запроса:**
```json
{
  "token": "reset_token",
  "password": "new_password"
}
```

**Ответ:** `200 OK` (детали зависят от реализации)

---

### 1.8 Получить текущего пользователя
**GET** `/auth/me`

**Требует аутентификации:** Да

**Ответ:** `200 OK`
```json
{
  "id": "uuid",
  "email": "ivan@example.com",
  "first_name": "ivan",
  "last_name": "ivanov",
  "role": "teacher",
  "is_verificated": true
}
```

---

### 1.9 Удаление аккаунта
**DELETE** `/auth/{id}`

**Требует аутентификации:** Да

**Query параметры:**
- `email`: EmailStr

**Ответ:** `200 OK` (детали зависят от реализации)

---

### 1.10 Выход из системы
**POST** `/auth/logout`

**Требует аутентификации:** Да

**Ответ:** `200 OK`
```json
{
  "detail": "Logged out"
}
```

**Примечание:** Удаляет cookie `session`.

---

## 2. Предметы (`/subjects`)

### 2.1 Создать предмет
**POST** `/subjects`

**Требует аутентификации:** Да

**Query параметры:**
- `name`: string (название предмета)

**Ответ:** `200 OK` (детали зависят от реализации)

---

### 2.2 Получить все предметы
**GET** `/subjects`

**Требует аутентификации:** Да

**Ответ:** `200 OK` (массив предметов)

---

### 2.3 Обновить предмет
**PATCH** `/subjects/{id}`

**Требует аутентификации:** Да

**Path параметры:**
- `id`: UUID

**Ответ:** `200 OK` (детали зависят от реализации)

---

### 2.4 Удалить предмет
**DELETE** `/subjects/{id}`

**Требует аутентификации:** Да

**Path параметры:**
- `id`: UUID

**Ответ:** `200 OK` (детали зависят от реализации)

---

## 3. Ученики (`/students`)

### 3.1 Получить всех учеников
**GET** `/students`

**Требует аутентификации:** Да (только для учителя)

**Ответ:** `200 OK`
```json
{
  "students": [
    {
      "id": "uuid",
      "name": "string",
      "classroom": "uuid" // или null
    }
  ],
  "classrooms": [
    {
      "id": "uuid",
      "name": "string"
    }
  ]
}
```

---

### 3.2 Получить фильтры для списка студентов
**GET** `/students/filters`

**Требует аутентификации:** Да (только для учителя)

**Ответ:** `200 OK`
```json
{
  "students": [
    {
      "id": "uuid",
      "name": "string"
    }
  ],
  "classrooms": [
    {
      "id": "uuid",
      "name": "string"
    }
  ]
}
```

**Примечание:** Возвращает доступные варианты для фильтрации списка студентов. Не требует передачи параметров - возвращает все доступные варианты для текущего учителя.

---

### 3.3 Получить данные об успеваемости ученика
**GET** `/students/{id}`

**Требует аутентификации:** Да

**Path параметры:**
- `id`: UUID (ID ученика)

**Ответ:** `200 OK` (данные об успеваемости)

---

### 3.4 Переместить ученика в класс
**PATCH** `/students/{id}/move_to_class`

**Требует аутентификации:** Да

**Path параметры:**
- `id`: UUID (ID ученика)

**Query параметры:**
- `classroom_id`: UUID

**Ответ:** `200 OK` (детали зависят от реализации)

---

### 3.5 Удалить ученика из класса
**PATCH** `/students/{id}/remove_from_class`

**Требует аутентификации:** Да

**Path параметры:**
- `id`: UUID (ID ученика)

**Query параметры:**
- `classroom_id`: UUID

**Ответ:** `200 OK` (детали зависят от реализации)

---

### 3.6 Удалить ученика
**DELETE** `/students/{id}`

**Требует аутентификации:** Да

**Path параметры:**
- `id`: UUID (ID ученика)

**Ответ:** `200 OK` (детали зависят от реализации)

---

## 4. Учителя (`/teachers`)

### 4.1 Получить ссылку-приглашение
**GET** `/teachers/invite_link`

**Требует аутентификации:** Да

**Ответ:** `200 OK`
```json
{
  "link": "https://frontend-url/t/{teacher_id}"
}
```

---

### 4.2 Добавить учителя (для ученика)
**POST** `/teachers/{id}`

**Требует аутентификации:** Да

**Path параметры:**
- `id`: UUID (ID учителя)

**Ответ:** `200 OK` (детали зависят от реализации)

---

## 5. Классы (`/classrooms`)

### 5.1 Создать класс
**POST** `/classrooms`

**Требует аутентификации:** Да

**Query параметры:**
- `name`: string (название класса)

**Ответ:** `200 OK` (детали зависят от реализации)

---

### 5.2 Получить все классы
**GET** `/classrooms`

**Требует аутентификации:** Да

**Ответ:** `200 OK`
```json
[
  {
    "classroom_id": "uuid",
    "name": "string",
    // другие поля
  }
]
```

---

### 5.3 Обновить класс
**PATCH** `/classrooms/{id}`

**Требует аутентификации:** Да

**Path параметры:**
- `id`: UUID

**Query параметры:**
- `name`: string (новое название класса)

**Ответ:** `200 OK` (детали зависят от реализации)

---

### 5.4 Удалить класс
**DELETE** `/classrooms/{id}`

**Требует аутентификации:** Да

**Path параметры:**
- `id`: UUID

**Ответ:** `200 OK` (детали зависят от реализации)

---

## 6. Задания (`/tasks`)

### 6.1 Создать задание
**POST** `/tasks`

**Требует аутентификации:** Да (только для учителя)

**Тело запроса:**
```json
{
  "subject_id": "uuid",
  "name": "Задача по математике",
  "description": "Решить 10 уравнений",
  "deadline": "2025-12-31T23:59:59", // опционально
  "exercises": [
    {
      "name": "Посчитай 10",
      "description": "Очень важно",
      "order_index": 1,
      "criterions": [
        {
          "name": "Посчитал до 10",
          "score": 1
        }
      ]
    }
  ]
}
```

**Ответ:** `200 OK`
```json
{
  "id": "uuid",
  "name": "Задача по математике",
  "description": "Решить 10 уравнений",
  "deadline": "2025-12-31T23:59:59",
  "subject_id": "uuid",
  "teacher_id": "uuid",
  "updated_at": "datetime",
  "created_at": "datetime",
  "exercises": [
    {
      "id": "uuid",
      "name": "Посчитай 10",
      "description": "Очень важно",
      "order_index": 1,
      "task_id": "uuid",
      "updated_at": "datetime",
      "created_at": "datetime",
      "file_keys": ["string"] | null, // опционально, ключи файлов из хранилища
      "criterions": [
        {
          "id": "uuid",
          "name": "Посчитал до 10",
          "score": 1,
          "exercise_id": "uuid",
          "updated_at": "datetime",
          "created_at": "datetime"
        }
      ]
    }
  ]
}
```

---

### 6.2 Получить фильтры для списка задач
**GET** `/tasks/filters`

**Требует аутентификации:** Да (только для учителя)

**Ответ:** `200 OK`
```json
{
  "subjects": [
    {
      "id": "uuid",
      "name": "string"
    }
  ],
  "tasks": [
    {
      "id": "uuid",
      "name": "string"
    }
  ]
}
```

**Примечание:** Возвращает доступные варианты для фильтрации списка задач. Не требует передачи параметров - возвращает все доступные варианты для текущего учителя.

---

### 6.3 Получить все задания
**GET** `/tasks`

**Требует аутентификации:** Да (только для учителя)

**Query параметры (фильтры):**
- `task_id`: UUID (опционально, фильтр по ID задачи)
- `subject_id`: UUID (опционально, фильтр по ID предмета)

**Ответ:** `200 OK`
```json
[
  {
    "id": "uuid",
    "name": "string",
    "subject_id": "uuid",
    "subject": "string",
    "updated_at": "datetime"
  }
]
```

**Типы данных:**
- `id`: UUID - идентификатор задачи
- `name`: string - название задачи
- `subject_id`: UUID - идентификатор предмета
- `subject`: string - название предмета
- `updated_at`: datetime - дата и время последнего обновления

---

### 6.4 Получить задание по ID
**GET** `/tasks/{id}`

**Требует аутентификации:** Да (только для учителя)

**Path параметры:**
- `id`: UUID

**Ответ:** `200 OK`
```json
{
  "id": "uuid",
  "name": "Задача по математике",
  "description": "Решить 10 уравнений",
  "deadline": "2025-12-31T23:59:59",
  "subject_id": "uuid",
  "teacher_id": "uuid",
  "updated_at": "datetime",
  "created_at": "datetime",
  "exercises": [
    {
      "id": "uuid",
      "name": "Посчитай 10",
      "description": "Очень важно",
      "order_index": 1,
      "file_keys": ["string"] | null, // опционально, ключи файлов из хранилища
      "criterions": [
        {
          "id": "uuid",
          "name": "Посчитал до 10",
          "score": 1
        }
      ]
    }
  ]
}
```

---

### 6.5 Создать работы по заданию
**POST** `/tasks/{task_id}/start`

**Требует аутентификации:** Да (только для учителя)

**Path параметры:**
- `task_id`: UUID

**Query параметры:**
- `students_ids`: List[UUID] (опционально, список ID студентов)
- `classrooms_ids`: List[UUID] (опционально, список ID классов)

**Примечание:** Необходимо указать хотя бы один из параметров: `students_ids` или `classrooms_ids`.

**Ответ:** `200 OK`
```json
{
  "status": "ok"
}
```

---

### 6.6 Обновить задание
**PUT** `/tasks/{id}`

**Требует аутентификации:** Да (только для учителя)

**Path параметры:**
- `id`: UUID

**Тело запроса:**
```json
{
  "id": "uuid",
  "name": "Обновленное название",
  "description": "Обновленное описание",
  "deadline": "2025-12-31T23:59:59",
  "exercises": [
    {
      "id": "uuid",
      "name": "Посчитай 10",
      "description": "Очень важно",
      "order_index": 1,
      "criterions": [
        {
          "id": "uuid",
          "name": "Посчитал до 10",
          "score": 1
        }
      ]
    }
  ],
  "updated_at": "datetime",
  "created_at": "datetime"
}
```

**Ответ:** `200 OK`
```json
{
  "id": "uuid",
  "name": "Обновленное название",
  "description": "Обновленное описание",
  "deadline": "2025-12-31T23:59:59",
  "subject_id": "uuid",
  "teacher_id": "uuid",
  "updated_at": "datetime",
  "created_at": "datetime",
  "exercises": [
    {
      "id": "uuid",
      "name": "Посчитай 10",
      "description": "Очень важно",
      "order_index": 1,
      "task_id": "uuid",
      "updated_at": "datetime",
      "created_at": "datetime",
      "file_keys": ["string"] | null, // опционально, ключи файлов из хранилища
      "criterions": [
        {
          "id": "uuid",
          "name": "Посчитал до 10",
          "score": 1,
          "exercise_id": "uuid",
          "updated_at": "datetime",
          "created_at": "datetime"
        }
      ]
    }
  ]
}
```

---

### 6.7 Удалить задание
**DELETE** `/tasks/{id}`

**Требует аутентификации:** Да (только для учителя)

**Path параметры:**
- `id`: UUID

**Ответ:** `200 OK` (детали зависят от реализации)

**Примечание:** Удаляет задание и все связанные работы.

---

## 7. Работы (`/works`)

### 7.1 Получить фильтры для учителя
**GET** `/works/teacher/filters`

**Требует аутентификации:** Да (только для учителя)

**Query параметры:**
- `students_ids`: List[UUID] (опционально)
- `classrooms_ids`: List[UUID] (опционально)
- `statuses`: List[string] (опционально)
- `tasks_ids`: List[UUID] (опционально)
- `subject_id`: UUID (опционально)
- `min`: datetime (опционально)
- `max`: datetime (опционально)

**Ответ:** `200 OK` (детали зависят от реализации)

---

### 7.2 Получить фильтры для ученика
**GET** `/works/student/filters`

**Требует аутентификации:** Да (только для ученика)

**Query параметры:**
- `teachers_ids`: List[UUID] (опционально)
- `classrooms_ids`: List[UUID] (опционально)
- `statuses`: List[string] (опционально)
- `tasks_ids`: List[UUID] (опционально)
- `subject_id`: UUID (опционально)
- `min`: datetime (опционально)
- `max`: datetime (опционально)

**Ответ:** `200 OK` (детали зависят от реализации)

---

### 7.3 Получить список работ для учителя
**GET** `/works/teacher/list`

**Требует аутентификации:** Да (только для учителя)

**Query параметры:** (те же, что и в `/works/teacher/filters`)

**Ответ:** `200 OK`
```json
[
  {
    "id": "uuid",
    "task_name": "string",
    "subject": "string",
    "student_name": "string",
    "score": 10,
    "max_score": 20,
    "percent": 50,
    "status_work": "pending" // или "in_progress", "completed", "checked"
  }
]
```

---

### 7.4 Получить список работ для ученика
**GET** `/works/student/list`

**Требует аутентификации:** Да (только для ученика)

**Query параметры:** (те же, что и в `/works/student/filters`)

**Ответ:** `200 OK`
```json
[
  {
    "id": "uuid",
    "task_name": "string",
    "subject": "string",
    "student_name": "string",
    "score": 10,
    "max_score": 20,
    "percent": 50,
    "status_work": "pending"
  }
]
```

---

### 7.5 Получить работу по ID
**GET** `/works/{id}`

**Требует аутентификации:** Да

**Path параметры:**
- `id`: UUID (ID работы)

**Ответ:** `200 OK`
```json
{
  "task": {
    "id": "uuid",
    "name": "string",
    "description": "string",
    "deadline": "datetime",
    "subject_id": "uuid",
    "teacher_id": "uuid",
    "updated_at": "datetime",
    "created_at": "datetime",
    "exercises": [
      {
        "id": "uuid",
        "name": "string",
        "description": "string",
        "order_index": 0,
        "task_id": "uuid",
        "updated_at": "datetime",
        "created_at": "datetime",
        "file_keys": ["string"] | null, // опционально, ключи файлов из хранилища
        "criterions": [
          {
            "id": "uuid",
            "name": "string",
            "score": 0,
            "exercise_id": "uuid",
            "updated_at": "datetime",
            "created_at": "datetime"
          }
        ]
      }
    ]
  },
  "work": {
    "id": "uuid",
    "task_id": "uuid",
    "student_id": "uuid",
    "finish_date": "datetime",
    "status": "pending",
    "answers": [
      {
        "id": "uuid",
        "work_id": "uuid",
        "exercise_id": "uuid",
        "file_keys": ["string"] | null, // опционально, ключи файлов из хранилища
        "text": "string",
        "assessments": [
          {
            "id": "uuid",
            "points": 0
          }
        ],
        "comments": [
          {
            "id": "uuid",
            "answer_id": "uuid",
            "type_id": "uuid",
            "description": "string",
            "answer_file_key": "string", // ключ файла ответа из хранилища
            "coordinates": [
              {
                "x1": 0.0,
                "y1": 0.0,
                "x2": 0.0,
                "y2": 0.0
              }
            ],
            "file_keys": ["string"] | null // опционально, ключи файлов из хранилища
          }
        ]
      }
    ]
  }
}
```

**Типы данных:**

**task** (SchemaTask):
- `id`: UUID - идентификатор задачи
- `name`: string - название задачи
- `description`: string - описание задачи
- `deadline`: datetime|null - срок выполнения (опционально)
- `subject_id`: UUID - идентификатор предмета
- `teacher_id`: UUID - идентификатор учителя
- `updated_at`: datetime|null - дата последнего обновления
- `created_at`: datetime|null - дата создания
- `exercises`: array[SchemaExercise] - список упражнений
  - `id`: UUID|null - идентификатор упражнения
  - `name`: string - название упражнения
  - `description`: string - описание упражнения
  - `order_index`: int - порядковый номер
  - `task_id`: UUID - идентификатор задачи
  - `updated_at`: datetime|null - дата последнего обновления
  - `created_at`: datetime|null - дата создания
  - `file_keys`: array[string]|null - опционально, ключи файлов из хранилища
  - `criterions`: array[ExerciseCriterionsSchema] - список критериев оценки
    - `id`: UUID|null - идентификатор критерия
    - `name`: string - название критерия
    - `score`: int - максимальный балл
    - `exercise_id`: UUID - идентификатор упражнения
    - `updated_at`: datetime|null - дата последнего обновления
    - `created_at`: datetime|null - дата создания

**work** (WorkRead):
- `id`: UUID - идентификатор работы
- `task_id`: UUID - идентификатор задачи
- `student_id`: UUID - идентификатор ученика
- `finish_date`: datetime|null - дата завершения (опционально)
- `status`: StatusWork - статус работы (enum: "pending", "in_progress", "completed", "checked")
- `answers`: array[AnswerRead] - список ответов
  - `id`: UUID - идентификатор ответа
  - `work_id`: UUID - идентификатор работы
  - `exercise_id`: UUID - идентификатор упражнения
  - `file_keys`: array[string]|null - опционально, ключи файлов из хранилища
  - `text`: string - текст ответа
  - `assessments`: array[AssessmentRead] - список оценок
    - `id`: UUID - идентификатор оценки
    - `points`: int - количество баллов
  - `comments`: array[CommentRead] - список комментариев
    - `id`: UUID - идентификатор комментария
    - `answer_id`: UUID - идентификатор ответа
    - `type_id`: UUID - идентификатор типа комментария
    - `description`: string - описание комментария
    - `answer_file_key`: string - ключ файла ответа из хранилища
    - `coordinates`: array[Coordinates] - координаты на изображении
      - `x1`: float - координата X1
      - `y1`: float - координата Y1
      - `x2`: float - координата X2
      - `y2`: float - координата Y2
    - `file_keys`: array[string]|null - опционально, ключи файлов из хранилища

---

### 7.6 Обновить работу
**PATCH** `/works/{work_id}`

**Требует аутентификации:** Да

**Path параметры:**
- `work_id`: UUID

**Query параметры:**
- `id`: UUID (ID работы)
- `status`: StatusWork (enum: "pending", "in_progress", "completed", "checked")
- `conclusion`: string (опционально, общий комментарий)

**Ответ:** `200 OK` (детали зависят от реализации)

---

### 7.7 Отправить работу на AI-проверку
**POST** `/works/{work_id}/ai_verification`

**Требует аутентификации:** Да

**Path параметры:**
- `work_id`: UUID

**Ответ:** `200 OK` (детали зависят от реализации)

---

### 7.8 Создать AI-комментарии
**POST** `/works/{work_id}/ai`

**Требует аутентификации:** Да

**Path параметры:**
- `work_id`: UUID

**Тело запроса:**
```json
[
  {
    "answer_id": "uuid",
    "answer_file_key": "string", // ключ файла ответа из хранилища
    "description": "string",
    "type_id": "uuid",
    "coordinates": [
      {
        "x1": 0.0,
        "y1": 0.0,
        "x2": 100.0,
        "y2": 100.0
      }
    ]
  }
]
```

**Ответ:** `200 OK` (детали зависят от реализации)

---

## 8. Комментарии (`/worsk/{work_id}/answers/{answer_id}/comments`)

**Примечание:** В URL есть опечатка "worsk" вместо "works", но это соответствует текущей реализации.

### 8.1 Создать комментарии
**POST** `/worsk/{work_id}/answers/{answer_id}/comments`

**Требует аутентификации:** Да

**Path параметры:**
- `work_id`: UUID
- `answer_id`: UUID

**Тело запроса:**
```json
[
  {
    "answer_file_key": "string", // ключ файла ответа из хранилища
    "description": "string",
    "type_id": "uuid",
    "coordinates": [
      {
        "x1": 0.0,
        "y1": 0.0,
        "x2": 100.0,
        "y2": 100.0
      }
    ]
  }
]
```

**Ответ:** `200 OK` (детали зависят от реализации)

---

### 8.2 Обновить комментарий
**PUT** `/worsk/{work_id}/answers/{answer_id}/comments/{comment_id}`

**Требует аутентификации:** Да

**Path параметры:**
- `work_id`: UUID
- `answer_id`: UUID
- `comment_id`: UUID

**Тело запроса:**
```json
{
  "type_id": "uuid",
  "description": "string"
}
```

**Ответ:** `200 OK` (детали зависят от реализации)

---

### 8.3 Удалить комментарий
**DELETE** `/worsk/{work_id}/answers/{answer_id}/comments/{comment_id}`

**Требует аутентификации:** Да

**Path параметры:**
- `work_id`: UUID
- `answer_id`: UUID
- `comment_id`: UUID

**Ответ:** `200 OK` (детали зависят от реализации)

---

## 9. Оценки (`/worsk/{work_id}/answers/{answer_id}/assessments`)

### 9.1 Обновить оценку
**PUT** `/worsk/{work_id}/answers/{answer_id}/assessments/{id}`

**Требует аутентификации:** Да

**Path параметры:**
- `work_id`: UUID
- `answer_id`: UUID
- `id`: UUID (ID оценки)

**Query параметры:**
- `points`: int (количество баллов)

**Ответ:** `200 OK` (детали зависят от реализации)

---

## 10. Ответы (`/teacher/works/{work_id}/answers`)

### 10.1 Обновить общий комментарий к ответу
**PATCH** `/teacher/works/{work_id}/answers/{answer_id}`

**Требует аутентификации:** Да (только для учителя)

**Path параметры:**
- `work_id`: UUID
- `answer_id`: UUID

**Query параметры:**
- `general_comment`: string

**Ответ:** `200 OK` (детали зависят от реализации)

---

## 11. Файлы (`/files`)

### 11.1 Загрузить файлы
**POST** `/files`

**Требует аутентификации:** Да

**Query параметры:**
- `entity`: FileEntity (enum: "work", "answer", "comment", и т.д.)
- `entity_id`: UUID

**Тело запроса:** `multipart/form-data`
- `files`: List[File] (массив файлов для загрузки)

**Ответ:** `200 OK`
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "filename": "string",
    "original_size": 12345,
    "original_mime": "image/jpeg"
  }
]
```

---

### 11.2 Удалить файл
**DELETE** `/files/{id}`

**Требует аутентификации:** Да

**Path параметры:**
- `id`: UUID

**Ответ:** `200 OK` (детали зависят от реализации)

---

## 12. Типы комментариев (`/comment_types`)

### 12.1 Создать тип комментария
**POST** `/comment_types`

**Требует аутентификации:** Да

**Query параметры:**
- `subject_id`: UUID

**Тело запроса:**
```json
{
  // структура зависит от SchemaCommentTypesBase
}
```

**Ответ:** `200 OK` (детали зависят от реализации)

---

### 12.2 Получить типы комментариев
**GET** `/comment_types`

**Требует аутентификации:** Да

**Query параметры:**
- `subject_id`: UUID (ID предмета)

**Ответ:** `200 OK`
```json
[
  {
    "id": "uuid",
    "short_name": "string",
    "name": "string"
  }
]
```

**Типы данных:**
- `id`: UUID - идентификатор типа комментария
- `short_name`: string - краткое название типа комментария
- `name`: string - полное название типа комментария

---

### 12.3 Обновить тип комментария
**PUT** `/comment_types/{id}`

**Требует аутентификации:** Да

**Path параметры:**
- `id`: UUID

**Тело запроса:**
```json
{
  // структура зависит от SchemaCommentTypesBase
}
```

**Ответ:** `200 OK` (детали зависят от реализации)

---

### 12.4 Удалить тип комментария
**DELETE** `/comment_types/{id}`

**Требует аутентификации:** Да

**Path параметры:**
- `id`: UUID

**Ответ:** `200 OK` (детали зависят от реализации)

---

## Статусы работ (StatusWork)

Enum значений для статуса работы:
- `pending` - Ожидает выполнения
- `in_progress` - В процессе выполнения
- `completed` - Завершена
- `checked` - Проверена

---

## Обработка ошибок

Все эндпоинты могут возвращать следующие HTTP статусы:

- `200 OK` - Успешный запрос
- `400 Bad Request` - Неверные параметры запроса
- `401 Unauthorized` - Требуется аутентификация
- `403 Forbidden` - Недостаточно прав доступа
- `404 Not Found` - Ресурс не найден
- `422 Unprocessable Entity` - Ошибка валидации данных
- `500 Internal Server Error` - Внутренняя ошибка сервера

Формат ошибки:
```json
{
  "detail": "Описание ошибки"
}
```

---

## Примечания

1. Все UUID должны быть в формате стандартного UUID v4.
2. Все даты и время должны быть в формате ISO 8601 (например: `2025-12-31T23:59:59`).
3. Для эндпоинтов, требующих аутентификации, токен должен быть передан либо в заголовке `Authorization: Bearer <token>`, либо через cookie `session`.
4. Некоторые эндпоинты доступны только для определенных ролей (учитель или ученик).
5. В URL `/worsk/...` присутствует опечатка, но это соответствует текущей реализации API.


