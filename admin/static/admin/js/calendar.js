document.addEventListener('DOMContentLoaded', () => {
    const calendarEl = document.getElementById('calendar');

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: eventos,
        eventTimeFormat: {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        },
        eventClick: function(info) {
            window.location.href = `/admin/citas/${info.event.id}/`;
        },
        dateClick: function(info) {
            window.location.href = `/admin/citas/nueva/?fecha=${info.dateStr}`;
        }
    });

    calendar.render();
});