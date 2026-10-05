import os
from pathlib import Path
from random import choice, randint, sample, shuffle

from alembic.config import Config
from faker import Faker
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from hw7.models import Grade, Group, Student, Subject, Teacher


ROOT_DIR = Path(__file__).resolve().parent.parent
SUBJECT_NAMES = (
    "Математика",
    "Українська мова",
    "Історія України",
    "Англійська мова",
    "Інформатика",
    "Фізика",
    "Біологія",
    "Географія",
)


def main() -> None:
    config = Config(str(ROOT_DIR / "alembic.ini"))
    database_url = os.getenv("DATABASE_URL") or config.get_main_option(
        "sqlalchemy.url"
    )
    engine = create_engine(database_url)
    fake = Faker("uk_UA")

    with Session(engine) as session:
        with session.begin():
            session.execute(delete(Grade))
            session.execute(delete(Student))
            session.execute(delete(Subject))
            session.execute(delete(Teacher))
            session.execute(delete(Group))

            groups = [Group(name=f"Група {number}") for number in range(1, 4)]
            teachers = [
                Teacher(first_name=fake.first_name(), last_name=fake.last_name())
                for _ in range(randint(3, 5))
            ]
            subjects = [
                Subject(name=name, teacher=choice(teachers))
                for name in sample(SUBJECT_NAMES, randint(5, 8))
            ]
            students = [
                Student(
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    group=groups[index % len(groups)],
                )
                for index in range(randint(30, 50))
            ]

            grades = []
            for student in students:
                student_subjects = subjects.copy()
                grade_count = randint(len(subjects), 20)
                student_subjects.extend(
                    choice(subjects) for _ in range(grade_count - len(subjects))
                )
                shuffle(student_subjects)
                grades.extend(
                    Grade(
                        student=student,
                        subject=subject,
                        grade=randint(1, 12),
                        received_at=fake.date_between(
                            start_date="-1y", end_date="today"
                        ),
                    )
                    for subject in student_subjects
                )

            session.add_all(groups + teachers + subjects + students + grades)

    engine.dispose()
    print(
        f"Заповнено базу: {len(students)} студентів, {len(groups)} групи, "
        f"{len(subjects)} предметів, {len(teachers)} викладачів, "
        f"{len(grades)} оцінок."
    )


if __name__ == "__main__":
    main()
