# Scheduling Service

Purpose: Resource and booking management integrated with MetaTask platform.

Features:
- Schedulable resources (rooms, equipment, teams)
- Booking requests with approval workflow
- Calendar view (FullCalendar) and API endpoints for availability
- Migration from TeamBooking (CFlows) to BookingRequest

Important: scheduling models reference `core.Organization`.

Quick start:
- Migrate: `python manage.py migrate services.scheduling`
- Run tests: `python manage.py test services.scheduling`

API endpoints:
- `/api/calendar-events/`
- `/api/check-availability/`
- `/api/suggest-times/`
