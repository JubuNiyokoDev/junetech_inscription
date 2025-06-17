import pymysql


def sync_to_php_db(registration):
    conn = pymysql.connect(
        host="php_db_host", user="user", password="pass", db="php_db"
    )
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO registrations (registration_number, event_id, type_id, name, first_name, email, validation, date_registration) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (
                registration.registration_number,
                registration.id_event.id_event,
                registration.id_type.id_type,
                registration.name,
                registration.first_name,
                registration.email,
                registration.validation,
                registration.date_registration,
            ),
        )
    conn.commit()
    conn.close()
