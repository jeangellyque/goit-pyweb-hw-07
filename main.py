import json
import os
from datetime import date
from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from hw7.models import Base, Grade, Group, Student, Subject, Teacher


MODELS: dict[str, type[Base]] = {
    "Grade": Grade,
    "Group": Group,
    "Student": Student,
    "Subject": Subject,
    "Teacher": Teacher,
}
REQUIRED_FIELDS: dict[type[Base], tuple[str, ...]] = {
    Grade: ("student_id", "subject_id", "grade", "received_at"),
    Group: ("name",),
    Student: ("first_name", "last_name", "group_id"),
    Subject: ("name", "teacher_id"),
    Teacher: ("first_name", "last_name"),
}
ROOT_DIR = Path(__file__).resolve().parent


def _parser():
    import argparse

    parser = argparse.ArgumentParser(description="Manage the school database.")
    parser.add_argument(
        "-a",
        "--action",
        required=True,
        choices=("create", "list", "update", "remove"),
        help="CRUD operation to perform",
    )
    parser.add_argument(
        "-m",
        "--model",
        required=True,
        choices=tuple(MODELS),
        help="model to operate on",
    )
    parser.add_argument("--id", type=int, help="record ID for update or remove")
    parser.add_argument("-n", "--name", help="record name or person's full name")
    parser.add_argument("--first-name", help="person's first name")
    parser.add_argument("--last-name", help="person's last name")
    parser.add_argument("--group-id", type=int, help="student's group ID")
    parser.add_argument("--teacher-id", type=int, help="subject/grade teacher ID")
    parser.add_argument("--student-id", type=int, help="grade/student ID")
    parser.add_argument("--subject-id", type=int, help="grade subject ID")
    parser.add_argument("--grade", type=int, help="grade value from 1 to 12")
    parser.add_argument(
        "--received-at",
        type=date.fromisoformat,
        help="date the grade was received (YYYY-MM-DD)",
    )
    return parser


def _database_url() -> str:
    if url := os.getenv("DATABASE_URL"):
        return url
    config = Config(str(ROOT_DIR / "alembic.ini"))
    return config.get_main_option("sqlalchemy.url")


def _record_data(record: Base) -> dict[str, object]:
    return {
        column.name: getattr(record, column.name)
        for column in record.__table__.columns
    }


def _person_fields(args, parser, required: bool) -> dict[str, str]:
    fields: dict[str, str] = {}
    if args.name is not None:
        parts = args.name.strip().split(maxsplit=1)
        if len(parts) != 2:
            parser.error("--name for a person must contain first and last names")
        fields["first_name"], fields["last_name"] = parts
    if args.first_name is not None:
        fields["first_name"] = args.first_name.strip()
    if args.last_name is not None:
        fields["last_name"] = args.last_name.strip()

    if required and any(not fields.get(name) for name in ("first_name", "last_name")):
        parser.error("provide --name 'First Last' or both --first-name and --last-name")
    return fields


def _values(args, parser, creating: bool) -> dict[str, object]:
    model = MODELS[args.model]
    if model in (Teacher, Student):
        values = _person_fields(args, parser, required=creating)
    else:
        values = {}

    if model in (Group, Subject) and args.name is not None:
        values["name"] = args.name.strip()
    if model == Student and args.group_id is not None:
        values["group_id"] = args.group_id
    if model == Subject and args.teacher_id is not None:
        values["teacher_id"] = args.teacher_id
    if model == Grade:
        for field in ("student_id", "subject_id", "grade", "received_at"):
            value = getattr(args, field)
            if value is not None:
                values[field] = value

    if creating:
        missing = [
            field
            for field in REQUIRED_FIELDS[model]
            if values.get(field) is None or values.get(field) == ""
        ]
        if missing:
            parser.error(f"{args.model} creation requires: {', '.join(missing)}")
        if model == Grade and not 1 <= values["grade"] <= 12:
            parser.error("--grade must be between 1 and 12")
    elif not values:
        parser.error("provide at least one field to update")
    elif model == Grade and "grade" in values and not 1 <= values["grade"] <= 12:
        parser.error("--grade must be between 1 and 12")

    return values


def _print_json(data) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def _run(args, parser, engine) -> None:
    model = MODELS[args.model]

    if args.action == "list":
        with Session(engine) as session:
            records = session.scalars(select(model).order_by(model.id)).all()
            _print_json([_record_data(record) for record in records])
        return

    if args.action in ("update", "remove") and args.id is None:
        parser.error(f"--id is required for the {args.action} action")

    if args.action == "create":
        values = _values(args, parser, creating=True)
        with Session(engine) as session, session.begin():
            record = model(**values)
            session.add(record)
            session.flush()
            result = _record_data(record)
        _print_json(result)
        return

    if args.action == "update":
        values = _values(args, parser, creating=False)
        with Session(engine) as session, session.begin():
            record = session.get(model, args.id)
            if record is None:
                parser.error(f"{args.model} with id={args.id} was not found")
            for field, value in values.items():
                setattr(record, field, value)
            session.flush()
            result = _record_data(record)
        _print_json(result)
        return

    with Session(engine) as session, session.begin():
        result = session.execute(delete(model).where(model.id == args.id))
        if result.rowcount == 0:
            parser.error(f"{args.model} with id={args.id} was not found")
    print(f"Removed {args.model} id={args.id}")


def main() -> None:
    parser = _parser()
    args = parser.parse_args()
    engine = create_engine(_database_url())
    try:
        _run(args, parser, engine)
    except IntegrityError:
        parser.error(
            "database constraint violation; check unique values, referenced IDs, "
            "and related records"
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
