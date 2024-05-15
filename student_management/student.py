"""
Student Management System.

A small, dependency-free system for managing student records and grades.
It demonstrates object-oriented design in pure Python:

* ``Grade``                    - an immutable value object for one grade.
* ``Student``                  - a student's profile and grade history.
* ``StudentManagementSystem``  - stores students and provides CRUD,
                                 ranking and statistics.

Run this file directly to see a full demonstration::

    python student.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from statistics import mean
from typing import Dict, List, Optional


# --------------------------------------------------------------------------
# Exceptions
# --------------------------------------------------------------------------

class StudentManagementError(Exception):
    """Base class for every error raised by this module."""


class ValidationError(StudentManagementError, ValueError):
    """Raised when input data is invalid (bad email, grade out of range...)."""


class StudentNotFoundError(StudentManagementError, KeyError):
    """Raised when a student ID does not exist in the system."""

    def __str__(self) -> str:  # KeyError would otherwise wrap it in quotes
        return str(self.args[0]) if self.args else ""


class DuplicateStudentError(StudentManagementError):
    """Raised when adding a student whose ID is already registered."""


# --------------------------------------------------------------------------
# Validation helpers
# --------------------------------------------------------------------------

_EMAIL_PATTERN = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")

MIN_SCORE = 0.0
MAX_SCORE = 100.0


def _require_text(value: str, field_name: str) -> str:
    """Return ``value`` stripped, or raise if it is empty or not a string."""
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field_name} must be a non-empty string.")
    return value.strip()


def _validate_email(email: str) -> str:
    """Return a normalized (lower-case) email, or raise if it is malformed."""
    email = _require_text(email, "Email").lower()
    if not _EMAIL_PATTERN.match(email):
        raise ValidationError(f"Invalid email address: {email!r}.")
    return email


def _validate_score(score: float) -> float:
    """Return ``score`` as a float, or raise if it is not within 0-100."""
    # bool is a subclass of int, but True/False are never valid grades.
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        raise ValidationError("Score must be a number.")
    if not MIN_SCORE <= score <= MAX_SCORE:
        raise ValidationError(
            f"Score must be between {MIN_SCORE:g} and {MAX_SCORE:g}, "
            f"got {score}."
        )
    return float(score)


def score_to_gpa_points(score: float) -> float:
    """Convert a 0-100 score to points on the common 4.0 GPA scale."""
    if score >= 90:
        return 4.0
    if score >= 80:
        return 3.0
    if score >= 70:
        return 2.0
    if score >= 60:
        return 1.0
    return 0.0


# --------------------------------------------------------------------------
# Domain classes
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Grade:
    """One grade a student earned in one subject (immutable)."""

    subject: str
    score: float

    def __post_init__(self) -> None:
        # frozen dataclasses need object.__setattr__ to normalize fields.
        subject = _require_text(self.subject, "Subject")
        object.__setattr__(self, "subject", subject)
        object.__setattr__(self, "score", _validate_score(self.score))

    @property
    def gpa_points(self) -> float:
        """This grade expressed on the 4.0 scale."""
        return score_to_gpa_points(self.score)


@dataclass
class Student:
    """A student's profile and grade history.

    Responsibility (SRP): hold and validate data about a single student.
    It knows nothing about how students are stored or ranked.
    """

    name: str
    student_id: str
    email: str
    enrollment_date: date = field(default_factory=date.today)
    _grades: List[Grade] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self.name = _require_text(self.name, "Name")
        self.student_id = _require_text(self.student_id, "Student ID")
        self.email = _validate_email(self.email)
        if not isinstance(self.enrollment_date, date):
            raise ValidationError("Enrollment date must be a datetime.date.")
        if self.enrollment_date > date.today():
            raise ValidationError("Enrollment date cannot be in the future.")

    # ----- grades ---------------------------------------------------------

    @property
    def grades(self) -> List[Grade]:
        """A copy of the grade list, so callers cannot modify it directly."""
        return list(self._grades)

    def add_grade(self, subject: str, score: float) -> Grade:
        """Record a grade (0-100) for ``subject`` and return it.

        Raises:
            ValidationError: if the subject is empty or the score is invalid.
        """
        grade = Grade(subject, score)
        self._grades.append(grade)
        return grade

    def calculate_average(self) -> float:
        """Average score across all grades (0.0 if there are none)."""
        if not self._grades:
            return 0.0
        return round(mean(g.score for g in self._grades), 2)

    def calculate_gpa(self) -> float:
        """GPA on the 4.0 scale across all grades (0.0 if there are none)."""
        if not self._grades:
            return 0.0
        return round(mean(g.gpa_points for g in self._grades), 2)

    def subject_averages(self) -> Dict[str, float]:
        """Average score per subject, for students with repeated subjects."""
        by_subject: Dict[str, List[float]] = {}
        for grade in self._grades:
            by_subject.setdefault(grade.subject, []).append(grade.score)
        return {subject: round(mean(scores), 2)
                for subject, scores in by_subject.items()}

    # ----- presentation ---------------------------------------------------

    def get_info(self) -> Dict[str, object]:
        """Return a plain dictionary summary of the student."""
        return {
            "student_id": self.student_id,
            "name": self.name,
            "email": self.email,
            "enrollment_date": self.enrollment_date.isoformat(),
            "grades": {g.subject: g.score for g in self._grades},
            "average": self.calculate_average(),
            "gpa": self.calculate_gpa(),
        }

    def __str__(self) -> str:
        return (f"[{self.student_id}] {self.name:<15} "
                f"avg {self.calculate_average():6.2f}  "
                f"GPA {self.calculate_gpa():.2f}")


class StudentManagementSystem:
    """Stores students and offers CRUD, ranking and statistics.

    Responsibility (SRP): manage the *collection* of students. Per-student
    rules (validation, GPA) stay in ``Student``, so either class can change
    without breaking the other.
    """

    def __init__(self) -> None:
        self._students: Dict[str, Student] = {}

    # ----- CRUD -----------------------------------------------------------

    def add_student(self, name: str, student_id: str, email: str,
                    enrollment_date: Optional[date] = None) -> Student:
        """Create, register and return a new student.

        Raises:
            ValidationError: if any field is invalid.
            DuplicateStudentError: if the ID or email is already used.
        """
        student = Student(name, student_id, email,
                          enrollment_date or date.today())
        if student.student_id in self._students:
            raise DuplicateStudentError(
                f"Student ID {student.student_id!r} already exists.")
        if any(s.email == student.email for s in self._students.values()):
            raise DuplicateStudentError(
                f"Email {student.email!r} is already registered.")
        self._students[student.student_id] = student
        return student

    def get_student(self, student_id: str) -> Student:
        """Return the student with ``student_id``.

        Raises:
            StudentNotFoundError: if no such student exists.
        """
        try:
            return self._students[student_id]
        except KeyError:
            raise StudentNotFoundError(
                f"No student with ID {student_id!r}.") from None

    def update_student(self, student_id: str, *, name: Optional[str] = None,
                       email: Optional[str] = None) -> Student:
        """Update a student's name and/or email and return the student."""
        student = self.get_student(student_id)
        if name is not None:
            student.name = _require_text(name, "Name")
        if email is not None:
            new_email = _validate_email(email)
            if any(s.email == new_email and s is not student
                   for s in self._students.values()):
                raise DuplicateStudentError(
                    f"Email {new_email!r} is already registered.")
            student.email = new_email
        return student

    def remove_student(self, student_id: str) -> Student:
        """Remove and return the student with ``student_id``."""
        student = self.get_student(student_id)
        del self._students[student_id]
        return student

    def add_grade(self, student_id: str, subject: str, score: float) -> Grade:
        """Record a grade for an existing student."""
        return self.get_student(student_id).add_grade(subject, score)

    # ----- queries --------------------------------------------------------

    def __len__(self) -> int:
        return len(self._students)

    def __contains__(self, student_id: object) -> bool:
        return student_id in self._students

    def list_students(self) -> List[Student]:
        """All students, sorted by ID."""
        return sorted(self._students.values(), key=lambda s: s.student_id)

    def get_top_students(self, n: int = 3) -> List[Student]:
        """The ``n`` students with the highest GPA (ties broken by average).

        Students with no grades are not ranked.
        """
        if not isinstance(n, int) or isinstance(n, bool) or n < 1:
            raise ValidationError("n must be a positive integer.")
        graded = [s for s in self._students.values() if s.grades]
        graded.sort(key=lambda s: (s.calculate_gpa(), s.calculate_average()),
                    reverse=True)
        return graded[:n]

    def get_statistics(self) -> Dict[str, object]:
        """System-wide statistics as a dictionary."""
        all_grades = [g for s in self._students.values() for g in s.grades]
        graded = [s for s in self._students.values() if s.grades]

        subjects: Dict[str, List[float]] = {}
        for grade in all_grades:
            subjects.setdefault(grade.subject, []).append(grade.score)

        return {
            "total_students": len(self._students),
            "students_with_grades": len(graded),
            "total_grades": len(all_grades),
            "overall_average": (round(mean(g.score for g in all_grades), 2)
                                if all_grades else 0.0),
            "average_gpa": (round(mean(s.calculate_gpa() for s in graded), 2)
                            if graded else 0.0),
            "highest_score": max((g.score for g in all_grades), default=0.0),
            "lowest_score": min((g.score for g in all_grades), default=0.0),
            "subject_averages": {name: round(mean(scores), 2)
                                 for name, scores in sorted(subjects.items())},
        }

    def display_all_students(self) -> None:
        """Print every student as a formatted table."""
        if not self._students:
            print("No students registered.")
            return
        print(f"{'ID':<6} {'Name':<15} {'Email':<28} {'Avg':>6} {'GPA':>5}")
        print("-" * 64)
        for s in self.list_students():
            print(f"{s.student_id:<6} {s.name:<15} {s.email:<28} "
                  f"{s.calculate_average():>6.2f} {s.calculate_gpa():>5.2f}")


# --------------------------------------------------------------------------
# Demonstration
# --------------------------------------------------------------------------

def _section(title: str) -> None:
    print(f"\n{'=' * 64}\n{title}\n{'=' * 64}")


def main() -> None:
    """Walk through every feature of the system."""
    sms = StudentManagementSystem()

    _section("1. Adding students")
    sms.add_student("Ahmed Hassan", "S001", "ahmed@example.com",
                    date(2024, 9, 1))
    sms.add_student("Sara Ali", "S002", "sara@example.com", date(2024, 9, 1))
    sms.add_student("Omar Khaled", "S003", "omar@example.com",
                    date(2025, 2, 10))
    sms.add_student("Mona Youssef", "S004", "mona@example.com",
                    date(2025, 2, 10))
    sms.add_student("Youssef Adel", "S005", "youssef@example.com")
    print(f"Registered {len(sms)} students.")

    _section("2. Recording grades")
    grades = {
        "S001": {"Math": 95, "Physics": 88, "Programming": 92},
        "S002": {"Math": 98, "Physics": 94, "Programming": 97},
        "S003": {"Math": 72, "Physics": 65, "Programming": 80},
        "S004": {"Math": 85, "Physics": 91, "Programming": 89},
    }
    for student_id, subjects in grades.items():
        for subject, score in subjects.items():
            sms.add_grade(student_id, subject, score)
    print("Grades recorded for S001-S004 (S005 has none yet).")

    _section("3. Student details")
    for key, value in sms.get_student("S002").get_info().items():
        print(f"  {key:<16}: {value}")

    _section("4. All students")
    sms.display_all_students()

    _section("5. Top 3 students")
    for rank, student in enumerate(sms.get_top_students(3), start=1):
        print(f"  #{rank} {student}")

    _section("6. System statistics")
    for key, value in sms.get_statistics().items():
        print(f"  {key:<22}: {value}")

    _section("7. Updating and removing")
    sms.update_student("S003", email="omar.khaled@example.com")
    print(f"  Updated email: {sms.get_student('S003').email}")
    removed = sms.remove_student("S005")
    print(f"  Removed: {removed.name}. Students left: {len(sms)}")

    _section("8. Error handling")
    bad_calls = [
        ("Grade above 100", lambda: sms.add_grade("S001", "Math", 105)),
        ("Negative grade", lambda: sms.add_grade("S001", "Math", -5)),
        ("Invalid email",
         lambda: sms.add_student("Test", "S010", "not-an-email")),
        ("Duplicate ID",
         lambda: sms.add_student("Copy", "S001", "copy@example.com")),
        ("Unknown student", lambda: sms.get_student("S999")),
        ("Empty name", lambda: sms.add_student("  ", "S011", "x@example.com")),
    ]
    for label, call in bad_calls:
        try:
            call()
            print(f"  {label:<16} -> no error (unexpected!)")
        except StudentManagementError as error:
            print(f"  {label:<16} -> {type(error).__name__}: {error}")


if __name__ == "__main__":
    main()
