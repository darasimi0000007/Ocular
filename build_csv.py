import csv
import io
import models

def build_csv(records: list[models.AttendanceRecord]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["person_id", "first_name", "last_name", "recorded_at", "similarity"])

    for r in records:
        writer.writerow([
            str(r.person_id),
            r.attendance_person.first_name,
            r.attendance_person.last_name,
            r.recorded_at.isoformat(),
            r.matched_similarity,
        ])

    return buffer.getvalue().encode("utf-8")