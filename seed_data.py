from datetime import date, timedelta
from pathlib import Path
from random import randint, sample

import psycopg
from faker import Faker


DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/app"
SCHEMA_PATH = Path(__file__).parent / "db" / "schema.sql"

GROUPS = ("Група 1", "Група 2", "Група 3")
SUBJECTS = (
    "Математика",
    "Українська мова",
    "Історія України",
    "Англійська мова",
    "Інформатика",
    "Фізика",
    "Біологія",
)


def main():
    fake = Faker("uk_UA")
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    with psycopg.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(schema)
            cursor.execute(
                "TRUNCATE grades, students, subjects, teachers, groups "
                "RESTART IDENTITY CASCADE"
            )

            cursor.executemany(
                "INSERT INTO groups (name) VALUES (%s)", [(name,) for name in GROUPS]
            )
            cursor.executemany(
                "INSERT INTO teachers (first_name, last_name) VALUES (%s, %s)",
                [(fake.first_name(), fake.last_name()) for _ in range(4)],
            )
            cursor.executemany(
                "INSERT INTO subjects (name, teacher_id) VALUES (%s, %s)",
                [(name, randint(1, 4)) for name in SUBJECTS],
            )

            student_count = randint(30, 50)
            students = []
            for index in range(student_count):
                students.append(
                    (
                        fake.first_name(),
                        fake.last_name(),
                        index % len(GROUPS) + 1,
                    )
                )
            cursor.executemany(
                "INSERT INTO students (first_name, last_name, group_id) "
                "VALUES (%s, %s, %s)",
                students,
            )

            grades = []
            for student_id in range(1, student_count + 1):
                subject_ids = sample(range(1, len(SUBJECTS) + 1), len(SUBJECTS))
                grade_count = randint(len(SUBJECTS), 20)
                subject_ids.extend(
                    randint(1, len(SUBJECTS))
                    for _ in range(grade_count - len(SUBJECTS))
                )
                for subject_id in subject_ids:
                    received_at = date.today() - timedelta(days=randint(0, 365))
                    grades.append(
                        (student_id, subject_id, randint(1, 12), received_at)
                    )
            cursor.executemany(
                "INSERT INTO grades (student_id, subject_id, grade, received_at) "
                "VALUES (%s, %s, %s, %s)",
                grades,
            )

    print(
        f"Заповнено базу: {student_count} студентів, "
        f"{len(GROUPS)} групи, {len(SUBJECTS)} предметів, "
        f"{len(grades)} оцінок."
    )


if __name__ == "__main__":
    main()
