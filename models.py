from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, SmallInteger, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    students: Mapped[list["Student"]] = relationship(back_populates="group")


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    subjects: Mapped[list["Subject"]] = relationship(back_populates="teacher")


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (Index("idx_students_group_id", "group_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="RESTRICT"), nullable=False
    )

    group: Mapped["Group"] = relationship(back_populates="students")
    grades: Mapped[list["Grade"]] = relationship(back_populates="student")


class Subject(Base):
    __tablename__ = "subjects"
    __table_args__ = (Index("idx_subjects_teacher_id", "teacher_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="RESTRICT"), nullable=False
    )

    teacher: Mapped["Teacher"] = relationship(back_populates="subjects")
    grades: Mapped[list["Grade"]] = relationship(back_populates="subject")


class Grade(Base):
    __tablename__ = "grades"
    __table_args__ = (
        CheckConstraint("grade BETWEEN 1 AND 12", name="ck_grades_grade_range"),
        Index("idx_grades_student_id", "student_id"),
        Index("idx_grades_subject_id", "subject_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="RESTRICT"), nullable=False
    )
    grade: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    received_at: Mapped[date] = mapped_column(Date, nullable=False)

    student: Mapped["Student"] = relationship(back_populates="grades")
    subject: Mapped["Subject"] = relationship(back_populates="grades")
