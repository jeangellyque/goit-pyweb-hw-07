import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from alembic.config import Config
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from hw7.models import Grade, Group, Student, Subject, Teacher


ROOT_DIR = Path(__file__).resolve().parent.parent
config = Config(str(ROOT_DIR / "alembic.ini"))
DATABASE_URL = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
engine = create_engine(DATABASE_URL)


@contextmanager
def _session_scope(session: Session | None) -> Iterator[Session]:
    if session is not None:
        yield session
    else:
        with Session(engine) as managed_session:
            yield managed_session


def _rows(session: Session, statement) -> list[dict[str, object]]:
    return [dict(row) for row in session.execute(statement).mappings().all()]


def select_1(session: Session | None = None) -> list[dict[str, object]]:
    """Return the five students with the highest overall average grade."""
    average_grade = func.round(func.avg(Grade.grade), 2).label("average_grade")
    statement = (
        select(Student.id, Student.first_name, Student.last_name, average_grade)
        .join(Grade, Grade.student_id == Student.id)
        .group_by(Student.id, Student.first_name, Student.last_name)
        .order_by(average_grade.desc(), Student.last_name, Student.first_name)
        .limit(5)
    )
    with _session_scope(session) as active_session:
        return _rows(active_session, statement)


def select_2(
    subject_name: str | None = None, session: Session | None = None
) -> list[dict[str, object]]:
    """Return the top student by average grade in one subject."""
    with _session_scope(session) as active_session:
        if subject_name is None:
            subject_name = active_session.scalar(
                select(Subject.name).order_by(Subject.id).limit(1)
            )
        if subject_name is None:
            return []

        average_grade = func.round(func.avg(Grade.grade), 2).label("average_grade")
        statement = (
            select(
                Student.id,
                Student.first_name,
                Student.last_name,
                Subject.name.label("subject"),
                average_grade,
            )
            .join(Grade, Grade.student_id == Student.id)
            .join(Subject, Subject.id == Grade.subject_id)
            .where(Subject.name == subject_name)
            .group_by(
                Student.id,
                Student.first_name,
                Student.last_name,
                Subject.name,
            )
            .order_by(average_grade.desc(), Student.last_name, Student.first_name)
            .limit(1)
        )
        return _rows(active_session, statement)


def select_3(
    subject_name: str | None = None, session: Session | None = None
) -> list[dict[str, object]]:
    """Return each group's average grade in one subject."""
    with _session_scope(session) as active_session:
        if subject_name is None:
            subject_name = active_session.scalar(
                select(Subject.name).order_by(Subject.id).limit(1)
            )
        if subject_name is None:
            return []

        average_grade = func.round(func.avg(Grade.grade), 2).label("average_grade")
        statement = (
            select(
                Group.id.label("group_id"),
                Group.name.label("group_name"),
                Subject.name.label("subject"),
                average_grade,
            )
            .join(Student, Student.group_id == Group.id)
            .join(Grade, Grade.student_id == Student.id)
            .join(Subject, Subject.id == Grade.subject_id)
            .where(Subject.name == subject_name)
            .group_by(Group.id, Group.name, Subject.name)
            .order_by(Group.name)
        )
        return _rows(active_session, statement)


def select_4(session: Session | None = None) -> list[dict[str, object]]:
    """Return the average grade across all grades."""
    statement = select(
        func.round(func.avg(Grade.grade), 2).label("overall_average_grade")
    )
    with _session_scope(session) as active_session:
        return _rows(active_session, statement)


def select_5(
    teacher_id: int | None = None, session: Session | None = None
) -> list[dict[str, object]]:
    """Return the subjects taught by one teacher."""
    with _session_scope(session) as active_session:
        if teacher_id is None:
            teacher_id = active_session.scalar(
                select(Subject.teacher_id).order_by(Subject.teacher_id).limit(1)
            )
        if teacher_id is None:
            return []

        statement = (
            select(
                Teacher.id.label("teacher_id"),
                Teacher.first_name,
                Teacher.last_name,
                Subject.id.label("subject_id"),
                Subject.name.label("subject"),
            )
            .join(Subject, Subject.teacher_id == Teacher.id)
            .where(Teacher.id == teacher_id)
            .order_by(Subject.name)
        )
        return _rows(active_session, statement)


def select_6(
    group_name: str | None = None, session: Session | None = None
) -> list[dict[str, object]]:
    """Return the students in one group."""
    with _session_scope(session) as active_session:
        if group_name is None:
            group_name = active_session.scalar(
                select(Group.name)
                .join(Student, Student.group_id == Group.id)
                .order_by(Group.id)
                .limit(1)
            )
        if group_name is None:
            return []

        statement = (
            select(
                Student.id,
                Student.first_name,
                Student.last_name,
                Group.name.label("group_name"),
            )
            .join(Group, Group.id == Student.group_id)
            .where(Group.name == group_name)
            .order_by(Student.last_name, Student.first_name)
        )
        return _rows(active_session, statement)


def select_7(
    group_name: str | None = None,
    subject_name: str | None = None,
    session: Session | None = None,
) -> list[dict[str, object]]:
    """Return grades in one subject for students in one group."""
    with _session_scope(session) as active_session:
        if group_name is None or subject_name is None:
            defaults_query = (
                select(Group.name, Subject.name)
                .join(Student, Student.group_id == Group.id)
                .join(Grade, Grade.student_id == Student.id)
                .join(Subject, Subject.id == Grade.subject_id)
            )
            if group_name is not None:
                defaults_query = defaults_query.where(Group.name == group_name)
            if subject_name is not None:
                defaults_query = defaults_query.where(Subject.name == subject_name)
            defaults = active_session.execute(
                defaults_query.order_by(Group.id, Subject.id).limit(1)
            ).first()
            if defaults is None:
                return []
            if group_name is None:
                group_name = defaults[0]
            if subject_name is None:
                subject_name = defaults[1]

        statement = (
            select(
                Student.id.label("student_id"),
                Student.first_name,
                Student.last_name,
                Group.name.label("group_name"),
                Subject.name.label("subject"),
                Grade.grade,
                Grade.received_at,
            )
            .join(Group, Group.id == Student.group_id)
            .join(Grade, Grade.student_id == Student.id)
            .join(Subject, Subject.id == Grade.subject_id)
            .where(Group.name == group_name, Subject.name == subject_name)
            .order_by(
                Student.last_name, Student.first_name, Grade.received_at
            )
        )
        return _rows(active_session, statement)


def select_8(
    teacher_id: int | None = None, session: Session | None = None
) -> list[dict[str, object]]:
    """Return the average grade given by one teacher across their subjects."""
    with _session_scope(session) as active_session:
        if teacher_id is None:
            teacher_id = active_session.scalar(
                select(Subject.teacher_id)
                .join(Grade, Grade.subject_id == Subject.id)
                .order_by(Subject.teacher_id)
                .limit(1)
            )
        if teacher_id is None:
            return []

        average_grade = func.round(func.avg(Grade.grade), 2).label("average_grade")
        statement = (
            select(
                Teacher.id.label("teacher_id"),
                Teacher.first_name,
                Teacher.last_name,
                average_grade,
            )
            .join(Subject, Subject.teacher_id == Teacher.id)
            .join(Grade, Grade.subject_id == Subject.id)
            .where(Teacher.id == teacher_id)
            .group_by(Teacher.id, Teacher.first_name, Teacher.last_name)
        )
        return _rows(active_session, statement)


def select_9(
    student_id: int | None = None, session: Session | None = None
) -> list[dict[str, object]]:
    """Return the subjects attended by one student."""
    with _session_scope(session) as active_session:
        if student_id is None:
            student_id = active_session.scalar(
                select(Grade.student_id).order_by(Grade.student_id).limit(1)
            )
        if student_id is None:
            return []

        statement = (
            select(
                Student.id.label("student_id"),
                Student.first_name,
                Student.last_name,
                Subject.id.label("subject_id"),
                Subject.name.label("subject"),
            )
            .join(Grade, Grade.student_id == Student.id)
            .join(Subject, Subject.id == Grade.subject_id)
            .where(Student.id == student_id)
            .distinct()
            .order_by(Subject.name)
        )
        return _rows(active_session, statement)


def select_10(
    student_id: int | None = None,
    teacher_id: int | None = None,
    session: Session | None = None,
) -> list[dict[str, object]]:
    """Return subjects for one student that are taught by one teacher."""
    with _session_scope(session) as active_session:
        defaults_query = (
            select(Student.id, Teacher.id)
            .join(Grade, Grade.student_id == Student.id)
            .join(Subject, Subject.id == Grade.subject_id)
            .join(Teacher, Teacher.id == Subject.teacher_id)
        )
        if student_id is not None:
            defaults_query = defaults_query.where(Student.id == student_id)
        if teacher_id is not None:
            defaults_query = defaults_query.where(Teacher.id == teacher_id)
        defaults = active_session.execute(
            defaults_query.distinct()
            .order_by(Student.id, Teacher.id)
            .limit(1)
        ).first()
        if defaults is None:
            return []
        student_id = student_id if student_id is not None else defaults[0]
        teacher_id = teacher_id if teacher_id is not None else defaults[1]

        statement = (
            select(
                Student.id.label("student_id"),
                Student.first_name.label("student_first_name"),
                Student.last_name.label("student_last_name"),
                Teacher.id.label("teacher_id"),
                Teacher.first_name.label("teacher_first_name"),
                Teacher.last_name.label("teacher_last_name"),
                Subject.id.label("subject_id"),
                Subject.name.label("subject"),
            )
            .join(Grade, Grade.student_id == Student.id)
            .join(Subject, Subject.id == Grade.subject_id)
            .join(Teacher, Teacher.id == Subject.teacher_id)
            .where(Student.id == student_id, Teacher.id == teacher_id)
            .distinct()
            .order_by(Subject.name)
        )
        return _rows(active_session, statement)


def select_11(
    student_id: int | None = None,
    teacher_id: int | None = None,
    session: Session | None = None,
) -> list[dict[str, object]]:
    """Return a teacher's average grade for one student."""
    with _session_scope(session) as active_session:
        defaults_query = (
            select(Student.id, Teacher.id)
            .join(Grade, Grade.student_id == Student.id)
            .join(Subject, Subject.id == Grade.subject_id)
            .join(Teacher, Teacher.id == Subject.teacher_id)
        )
        if student_id is not None:
            defaults_query = defaults_query.where(Student.id == student_id)
        if teacher_id is not None:
            defaults_query = defaults_query.where(Teacher.id == teacher_id)
        defaults = active_session.execute(
            defaults_query.distinct()
            .order_by(Student.id, Teacher.id)
            .limit(1)
        ).first()
        if defaults is None:
            return []
        student_id = student_id if student_id is not None else defaults[0]
        teacher_id = teacher_id if teacher_id is not None else defaults[1]

        average_grade = func.round(func.avg(Grade.grade), 2).label("average_grade")
        statement = (
            select(
                Student.id.label("student_id"),
                Student.first_name.label("student_first_name"),
                Student.last_name.label("student_last_name"),
                Teacher.id.label("teacher_id"),
                Teacher.first_name.label("teacher_first_name"),
                Teacher.last_name.label("teacher_last_name"),
                average_grade,
            )
            .join(Grade, Grade.student_id == Student.id)
            .join(Subject, Subject.id == Grade.subject_id)
            .join(Teacher, Teacher.id == Subject.teacher_id)
            .where(Student.id == student_id, Teacher.id == teacher_id)
            .group_by(
                Student.id,
                Student.first_name,
                Student.last_name,
                Teacher.id,
                Teacher.first_name,
                Teacher.last_name,
            )
        )
        return _rows(active_session, statement)


def select_12(
    group_name: str | None = None,
    subject_name: str | None = None,
    session: Session | None = None,
) -> list[dict[str, object]]:
    """Return grades for the latest lesson of a subject in one group."""
    with _session_scope(session) as active_session:
        if group_name is None or subject_name is None:
            defaults_query = (
                select(Group.name, Subject.name)
                .join(Student, Student.group_id == Group.id)
                .join(Grade, Grade.student_id == Student.id)
                .join(Subject, Subject.id == Grade.subject_id)
            )
            if group_name is not None:
                defaults_query = defaults_query.where(Group.name == group_name)
            if subject_name is not None:
                defaults_query = defaults_query.where(Subject.name == subject_name)
            defaults = active_session.execute(
                defaults_query.order_by(Group.id, Subject.id).limit(1)
            ).first()
            if defaults is None:
                return []
            if group_name is None:
                group_name = defaults[0]
            if subject_name is None:
                subject_name = defaults[1]

        latest_lesson = (
            select(func.max(Grade.received_at))
            .join(Student, Student.id == Grade.student_id)
            .join(Group, Group.id == Student.group_id)
            .join(Subject, Subject.id == Grade.subject_id)
            .where(Group.name == group_name, Subject.name == subject_name)
            .scalar_subquery()
        )
        statement = (
            select(
                Student.id.label("student_id"),
                Student.first_name,
                Student.last_name,
                Group.name.label("group_name"),
                Subject.name.label("subject"),
                Grade.grade,
                Grade.received_at,
            )
            .join(Group, Group.id == Student.group_id)
            .join(Grade, Grade.student_id == Student.id)
            .join(Subject, Subject.id == Grade.subject_id)
            .where(
                Group.name == group_name,
                Subject.name == subject_name,
                Grade.received_at == latest_lesson,
            )
            .order_by(Student.last_name, Student.first_name)
        )
        return _rows(active_session, statement)
