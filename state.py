startedBookingProcess = False

def set_started_booking_process(value: bool):
    global startedBookingProcess
    startedBookingProcess = value

def is_booking_process_started() -> bool:
    return startedBookingProcess
