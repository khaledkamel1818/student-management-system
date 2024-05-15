# Student Management System

A clean, object-oriented student management system written in **pure Python**
(standard library only). It manages student profiles, records grades per
subject, calculates averages and GPA, ranks the top students and produces
system-wide statistics, with input validation and clear error handling
throughout.

## Features

- **Student profiles**: name, student ID, email and enrollment date.
- **Full CRUD**: add, view, update and remove students.
- **Grades per subject**: scores validated to the 0-100 range.
- **Average and GPA**: average score plus GPA on the 4.0 scale.
- **Top students**: ranking by GPA, ties broken by average score.
- **Statistics**: totals, overall average, average GPA, highest and lowest
  score, and per-subject averages.
- **Validation and errors**: a custom exception hierarchy for invalid data,
  duplicates and unknown students.
- **Zero dependencies**: runs anywhere Python 3.8+ is installed.

## Project structure

```
student_management/
├── student.py         # Classes and a runnable demonstration
├── README.md          # This file
└── requirements.txt   # No external dependencies
```

## Installation

```bash
git clone https://github.com/khaledkamel1818/student-management-system.git
cd student-management-system/student_management
python student.py
```

No `pip install` is needed.

## Usage

```python
from datetime import date
from student import StudentManagementSystem, StudentManagementError

sms = StudentManagementSystem()

# Create students
sms.add_student("Ahmed Hassan", "S001", "ahmed@example.com", date(2024, 9, 1))
sms.add_student("Sara Ali", "S002", "sara@example.com")

# Record grades
sms.add_grade("S001", "Math", 95)
sms.add_grade("S001", "Physics", 88)
sms.add_grade("S002", "Math", 98)

# Query
student = sms.get_student("S001")
print(student.calculate_average())   # 91.5
print(student.calculate_gpa())       # 3.5
print(student.get_info())

for s in sms.get_top_students(3):
    print(s)

print(sms.get_statistics())
sms.display_all_students()

# Update and remove
sms.update_student("S002", email="sara.ali@example.com")
sms.remove_student("S002")

# Errors are explicit and catchable
try:
    sms.add_grade("S001", "Math", 150)
except StudentManagementError as error:
    print(error)   # Score must be between 0 and 100, got 150.
```

## Classes and methods

### `Grade` (immutable value object)

| Member | Description |
|---|---|
| `subject`, `score` | Validated on creation; cannot be changed afterwards. |
| `gpa_points` | The score on the 4.0 scale (90+ = 4.0, 80+ = 3.0, 70+ = 2.0, 60+ = 1.0, else 0.0). |

### `Student`

| Method | Description |
|---|---|
| `Student(name, student_id, email, enrollment_date=today)` | Creates a validated student. |
| `add_grade(subject, score)` | Records a grade (0-100) and returns the `Grade`. |
| `calculate_average()` | Average score across all grades. |
| `calculate_gpa()` | GPA on the 4.0 scale. |
| `subject_averages()` | Average score per subject. |
| `grades` | Read-only copy of the grade list. |
| `get_info()` | A dictionary summary of the student. |

### `StudentManagementSystem`

| Method | Description |
|---|---|
| `add_student(name, student_id, email, enrollment_date=None)` | Registers a new student; rejects duplicate IDs and emails. |
| `get_student(student_id)` | Returns a student or raises `StudentNotFoundError`. |
| `update_student(student_id, name=None, email=None)` | Updates profile fields. |
| `remove_student(student_id)` | Removes and returns a student. |
| `add_grade(student_id, subject, score)` | Records a grade for a student. |
| `list_students()` | All students sorted by ID. |
| `get_top_students(n=3)` | The `n` best students by GPA. |
| `get_statistics()` | A dictionary of system-wide statistics. |
| `display_all_students()` | Prints a formatted table. |
| `len(sms)`, `"S001" in sms` | Number of students, membership test. |

### Exceptions

```
StudentManagementError
├── ValidationError         # bad name, email, score, date or argument
├── StudentNotFoundError    # unknown student ID
└── DuplicateStudentError   # ID or email already registered
```

## OOP concepts used

- **Encapsulation**: grades live in a private list (`_grades`) and are only
  exposed as a copy through the `grades` property, so they can only change
  through `add_grade`, which validates them.
- **Abstraction**: callers use simple methods such as `get_top_students()`
  without knowing how ranking or storage works.
- **Composition**: a `StudentManagementSystem` *has* students, and a
  `Student` *has* grades.
- **Inheritance**: the exception hierarchy derives from a common base class,
  so callers can catch one type or all of them.
- **Immutability**: `Grade` is a frozen dataclass, so a recorded grade cannot
  be altered by accident.
- **Dunder methods**: `__str__`, `__len__` and `__contains__` make objects
  behave naturally with `print`, `len()` and `in`.

### SOLID principles

- **Single Responsibility**: `Grade` validates one score, `Student` manages
  one student's data, `StudentManagementSystem` manages the collection.
- **Open/Closed**: the GPA scale lives in one function
  (`score_to_gpa_points`), so new rules can be added without touching the
  classes that use it.
- **Liskov Substitution**: every custom exception can be used wherever its
  base class (`StudentManagementError`, `ValueError` or `KeyError`) is
  expected.
- **Interface Segregation**: each class exposes a small, focused set of
  methods.
- **Dependency Inversion**: validation is done by small helper functions that
  the classes depend on, rather than being duplicated inside each class.

## Expected output

Running `python student.py` prints:

```

================================================================
1. Adding students
================================================================
Registered 5 students.

================================================================
2. Recording grades
================================================================
Grades recorded for S001-S004 (S005 has none yet).

================================================================
3. Student details
================================================================
  student_id      : S002
  name            : Sara Ali
  email           : sara@example.com
  enrollment_date : 2024-09-01
  grades          : {'Math': 98.0, 'Physics': 94.0, 'Programming': 97.0}
  average         : 96.33
  gpa             : 4.0

================================================================
4. All students
================================================================
ID     Name            Email                           Avg   GPA
----------------------------------------------------------------
S001   Ahmed Hassan    ahmed@example.com             91.67  3.67
S002   Sara Ali        sara@example.com              96.33  4.00
S003   Omar Khaled     omar@example.com              72.33  2.00
S004   Mona Youssef    mona@example.com              88.33  3.33
S005   Youssef Adel    youssef@example.com            0.00  0.00

================================================================
5. Top 3 students
================================================================
  #1 [S002] Sara Ali        avg  96.33  GPA 4.00
  #2 [S001] Ahmed Hassan    avg  91.67  GPA 3.67
  #3 [S004] Mona Youssef    avg  88.33  GPA 3.33

================================================================
6. System statistics
================================================================
  total_students        : 5
  students_with_grades  : 4
  total_grades          : 12
  overall_average       : 87.17
  average_gpa           : 3.25
  highest_score         : 98.0
  lowest_score          : 65.0
  subject_averages      : {'Math': 87.5, 'Physics': 84.5, 'Programming': 89.5}

================================================================
7. Updating and removing
================================================================
  Updated email: omar.khaled@example.com
  Removed: Youssef Adel. Students left: 4

================================================================
8. Error handling
================================================================
  Grade above 100  -> ValidationError: Score must be between 0 and 100, got 105.
  Negative grade   -> ValidationError: Score must be between 0 and 100, got -5.
  Invalid email    -> ValidationError: Invalid email address: 'not-an-email'.
  Duplicate ID     -> DuplicateStudentError: Student ID 'S001' already exists.
  Unknown student  -> StudentNotFoundError: No student with ID 'S999'.
  Empty name       -> ValidationError: Name must be a non-empty string.
```

## Author

**Khaled Kamel** · [GitHub](https://github.com/khaledkamel1818)
